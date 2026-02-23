"""
ワークフロー・オーケストレーター（Slack 非依存）。
CLIやスケジューラーからパイプライン全体を直接実行する場合に使用する。
"""
import datetime
from pathlib import Path

import config
from models import WorkflowState


def run_pipeline(articles: list[dict]) -> WorkflowState:
    """
    ニュース記事リストから動画作成まで全パイプラインを実行する。

    Slack を介さずに CLI やスケジューラーから呼び出す場合に使う。
    各ステップの進捗は print() で出力する。

    Returns:
        完成した WorkflowState（audio_path / thumbnail_path / video_path が設定済み）
    """
    from pipeline.script import generate_script
    from pipeline.tts import text_to_speech
    from pipeline.thumbnail import create_thumbnail
    from pipeline.video import create_video

    workflow_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir  = config.OUTPUT_DIR / workflow_id
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] 原稿を生成中...")
    result = generate_script(articles)
    print(f"\nタイトル: {result['title']}")

    print("\n[2/4] TTS 音声を生成中...")
    audio_path = text_to_speech(
        result["narration"],
        output_dir / "narration.mp3",
    )
    print(f"音声: {audio_path}")

    print("\n[3/4] サムネイルを作成中...")
    thumbnail_path = create_thumbnail(
        result["title"],
        output_dir / "thumbnail.jpg",
    )
    print(f"サムネイル: {thumbnail_path}")

    print("\n[4/4] 動画を作成中（数分かかります）...")
    video_path = create_video(
        audio_path=audio_path,
        subtitles=result["subtitles"],
        output_path=output_dir / "video.mp4",
    )
    print(f"動画: {video_path}")

    return WorkflowState(
        workflow_id=workflow_id,
        articles=articles,
        script_result=result,
        audio_path=audio_path,
        thumbnail_path=thumbnail_path,
        video_path=video_path,
    )
