#!/usr/bin/env python3
"""
Slack ボット + 毎日スケジューラーの起動エントリーポイント。

使い方:
    ANTHROPIC_API_KEY=sk-ant-... \\
    SLACK_BOT_TOKEN=xoxb-...     \\
    SLACK_APP_TOKEN=xapp-...     \\
    python run_bot.py

Slack アプリの設定:
  - Socket Mode を有効化
  - Slash Commands: /health-news
  - Event Subscriptions: 不要（Socket Mode のみ）
  - Bot Token Scopes:
      chat:write, commands, files:write
"""
import os
import sys
import threading


def _check_env() -> None:
    required = {
        "ANTHROPIC_API_KEY": "Anthropic APIキー",
        "SLACK_BOT_TOKEN":   "Slack Bot Token (xoxb-...)",
        "SLACK_APP_TOKEN":   "Slack App Token (xapp-...) ※Socket Mode用",
    }
    missing = [f"  {k}: {desc}" for k, desc in required.items() if not os.environ.get(k)]
    if missing:
        print("エラー: 以下の環境変数が設定されていません。\n" + "\n".join(missing))
        sys.exit(1)


def main() -> None:
    _check_env()

    # ベースアセットが存在しない場合は自動生成
    import config
    if not config.BACKGROUND_IMAGE.exists():
        print("[setup] background.png が見つかりません。自動生成します...")
        from assets.create_assets import create_background, create_thumbnail_base
        config.ASSETS_DIR.mkdir(exist_ok=True)
        create_background()
        create_thumbnail_base()

    # スケジューラーをバックグラウンドスレッドで起動
    from scheduler import start_scheduler
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    # Slack ボットをメインスレッドで起動（ブロッキング）
    print("=" * 56)
    print("  ヘルスニュース YouTube 自動投稿ボット")
    print("=" * 56)
    print(f"  チャンネル: {config.SLACK_CHANNEL}")
    print(f"  毎日自動実行: {config.DAILY_POST_TIME}")
    print("  Slack で /health-news コマンドを実行するか、")
    print(f"  毎日 {config.DAILY_POST_TIME} に自動で処理が始まります。")
    print("=" * 56)

    from bot.slack_bot import start
    start()


if __name__ == "__main__":
    main()
