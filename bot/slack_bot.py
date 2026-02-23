"""
Slack Bolt (Socket Mode) ボット ─ ヘルスニュース動画作成ワークフロー

ワークフロー:
  /health-news → [ニュース取得 + 原稿生成] → Slack で内容確認
    ↓ 承認
  [TTS + サムネイル + 動画作成] → Slack に動画ファイルを投稿して確認
    ↓ 承認
  [YouTube アップロード] → Slack に動画URLを通知

状態は _states dict (workflow_id → WorkflowState) でメモリ管理する。
"""
import threading
import traceback
import uuid
from typing import Callable

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
from models import WorkflowState

app = App(token=config.SLACK_BOT_TOKEN)

# ワークフロー状態: {workflow_id: WorkflowState}
_states: dict[str, WorkflowState] = {}


# ────────────────────────────────────────────────────────────────
# ユーティリティ
# ────────────────────────────────────────────────────────────────

def _script_review_blocks(state: WorkflowState) -> list[dict]:
    """原稿確認用 Slack Block Kit ブロックを返す。"""
    wid = state.workflow_id
    result = state.script_result
    preview = f"*{result['title']}*\n\n{result['narration'][:600]}..."
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📝 *原稿が完成しました* `{wid}`\n\n{preview}",
            },
        },
        {
            "type": "actions",
            "block_id": f"script_actions_{wid}",
            "elements": [
                _btn("✅ 承認して動画作成", "approve_script",   wid, "primary"),
                _btn("🔄 再生成",           "regenerate_script", wid),
                _btn("❌ キャンセル",        "cancel_workflow",   wid, "danger"),
            ],
        },
    ]


def _upload_review_blocks(state: WorkflowState) -> list[dict]:
    """YouTube アップロード確認用 Slack Block Kit ブロックを返す。"""
    wid = state.workflow_id
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"✅ *動画が完成しました！* `{wid}`\n上の動画ファイルを確認してください。",
            },
        },
        {
            "type": "actions",
            "block_id": f"upload_actions_{wid}",
            "elements": [
                _btn("⬆️ YouTube にアップロード", "approve_upload", wid, "primary"),
                _btn("❌ キャンセル",             "cancel_workflow", wid, "danger"),
            ],
        },
    ]


def _btn(label: str, action_id: str, value: str, style: str = "") -> dict:
    d: dict = {
        "type":      "button",
        "text":      {"type": "plain_text", "text": label},
        "action_id": action_id,
        "value":     value,
    }
    if style:
        d["style"] = style
    return d


def _run_in_thread(fn: Callable, *args) -> None:
    threading.Thread(target=fn, args=args, daemon=True).start()


def _disable_buttons(client, body: dict, new_text: str) -> None:
    """押されたボタンのメッセージをテキストのみに更新してボタンを無効化する。"""
    try:
        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"],
            text=new_text,
            blocks=[],
        )
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────
# Slash Command: /health-news
# ────────────────────────────────────────────────────────────────

@app.command("/health-news")
def handle_slash_command(ack, say, command):
    ack()
    say(text="🔄 最新の公衆衛生ニュースを取得中...")
    _run_in_thread(_start_workflow, say)


def _start_workflow(say: Callable) -> None:
    """ニュース取得 → 原稿生成 → Slack に原稿確認メッセージを投稿する。"""
    from pipeline.news import fetch_news
    from pipeline.script import generate_script

    try:
        articles = fetch_news()
        if not articles:
            say(text="❌ ニュースを取得できませんでした。ネットワーク接続を確認してください。")
            return

        say(text=f"📰 {len(articles)} 件のニュースを取得しました。原稿を生成中...\n（1〜2分かかります）")

        print("\n[script] 原稿生成中...")
        result = generate_script(articles)

        wid   = str(uuid.uuid4())[:8]
        state = WorkflowState(workflow_id=wid, articles=articles, script_result=result)
        _states[wid] = state

        say(
            blocks=_script_review_blocks(state),
            text=f"原稿確認: {result['title']}",
        )

    except Exception as e:
        say(text=f"❌ エラーが発生しました: {e}")
        traceback.print_exc()


# ────────────────────────────────────────────────────────────────
# Action: 原稿承認 → 動画作成
# ────────────────────────────────────────────────────────────────

@app.action("approve_script")
def handle_approve_script(ack, body, say, client):
    ack()
    wid   = body["actions"][0]["value"]
    state = _states.get(wid)
    if not state:
        say(text="❌ ワークフローが見つかりません（タイムアウトした可能性があります）。")
        return

    _disable_buttons(client, body, f"✅ 承認済み — 動画作成中… `{wid}`")
    say(text="🎬 動画を作成しています（5〜10分程度かかります）...")
    _run_in_thread(_create_video_and_notify, say, client, body["channel"]["id"], state)


def _create_video_and_notify(say: Callable, client, channel_id: str, state: WorkflowState) -> None:
    """TTS → サムネイル → 動画作成 → Slack にファイル投稿。"""
    from pipeline.tts import text_to_speech
    from pipeline.thumbnail import create_thumbnail
    from pipeline.video import create_video

    try:
        out_dir = config.OUTPUT_DIR / state.workflow_id
        out_dir.mkdir(parents=True, exist_ok=True)

        say(text="🔊 音声（TTS）を生成中...")
        audio_path = text_to_speech(
            state.script_result["narration"],
            out_dir / "narration.mp3",
        )

        say(text="🖼 サムネイルを作成中...")
        thumbnail_path = create_thumbnail(
            state.script_result["title"],
            out_dir / "thumbnail.jpg",
        )

        say(text="🎥 動画を作成中（最も時間がかかります）...")
        video_path = create_video(
            audio_path=audio_path,
            subtitles=state.script_result["subtitles"],
            output_path=out_dir / "video.mp4",
        )

        state.audio_path     = audio_path
        state.thumbnail_path = thumbnail_path
        state.video_path     = video_path

        # Slack に動画ファイルをアップロード
        say(text="📤 確認用動画を Slack にアップロード中...")
        client.files_upload_v2(
            channel=channel_id,
            file=str(video_path),
            filename=f"preview_{state.workflow_id}.mp4",
            title=f"[確認用] {state.script_result['title']}",
        )

        say(
            blocks=_upload_review_blocks(state),
            text="YouTube アップロード確認",
        )

    except Exception as e:
        say(text=f"❌ 動画作成中にエラーが発生しました: {e}")
        traceback.print_exc()


# ────────────────────────────────────────────────────────────────
# Action: YouTube アップロード承認
# ────────────────────────────────────────────────────────────────

@app.action("approve_upload")
def handle_approve_upload(ack, body, say, client):
    ack()
    wid   = body["actions"][0]["value"]
    state = _states.get(wid)
    if not state or not state.video_path:
        say(text="❌ 動画ファイルが見つかりません。")
        return

    _disable_buttons(client, body, f"⬆️ YouTube にアップロード中… `{wid}`")
    _run_in_thread(_upload_to_youtube, say, state)


def _upload_to_youtube(say: Callable, state: WorkflowState) -> None:
    """YouTube にアップロードして Slack に通知する。"""
    from pipeline.youtube_upload import upload_video

    try:
        say(text="⬆️ YouTube にアップロード中... しばらくお待ちください")
        video_id    = upload_video(
            video_path=state.video_path,
            thumbnail_path=state.thumbnail_path,
            title=state.script_result["title"],
            description=state.script_result["description"],
        )
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        say(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"🎉 *YouTube アップロード完了！*\n\n"
                            f"*タイトル*: {state.script_result['title']}\n"
                            f"*URL*: {youtube_url}"
                        ),
                    },
                }
            ],
            text=f"YouTube アップロード完了: {youtube_url}",
        )

        _states.pop(state.workflow_id, None)

    except Exception as e:
        say(text=f"❌ YouTube アップロード中にエラー: {e}")
        traceback.print_exc()


# ────────────────────────────────────────────────────────────────
# Action: 原稿再生成
# ────────────────────────────────────────────────────────────────

@app.action("regenerate_script")
def handle_regenerate(ack, body, say, client):
    ack()
    wid   = body["actions"][0]["value"]
    state = _states.get(wid)
    if not state:
        say(text="❌ ワークフローが見つかりません。")
        return

    _disable_buttons(client, body, f"🔄 原稿を再生成中… `{wid}`")
    _run_in_thread(_regenerate_script, say, state)


def _regenerate_script(say: Callable, state: WorkflowState) -> None:
    from pipeline.script import generate_script
    try:
        say(text="🔄 原稿を再生成中... （1〜2分かかります）")
        result            = generate_script(state.articles)
        state.script_result = result
        say(
            blocks=_script_review_blocks(state),
            text=f"原稿確認 (再生成): {result['title']}",
        )
    except Exception as e:
        say(text=f"❌ 再生成中にエラー: {e}")
        traceback.print_exc()


# ────────────────────────────────────────────────────────────────
# Action: キャンセル
# ────────────────────────────────────────────────────────────────

@app.action("cancel_workflow")
def handle_cancel(ack, body, client):
    ack()
    wid = body["actions"][0]["value"]
    _states.pop(wid, None)
    _disable_buttons(client, body, f"❌ ワークフロー `{wid}` をキャンセルしました。")


# ────────────────────────────────────────────────────────────────
# 起動
# ────────────────────────────────────────────────────────────────

def start() -> None:
    """Slack ボットを Socket Mode で起動する。"""
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    print(f"[slack] ボット起動完了 (チャンネル: {config.SLACK_CHANNEL})")
    handler.start()
