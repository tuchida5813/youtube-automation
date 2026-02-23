"""
毎日定時に動画制作ワークフローを自動起動するスケジューラー。

DAILY_POST_TIME (HH:MM) に Slack へ通知を送り、
bot/slack_bot.py と同じ原稿生成フローを開始する。

run_bot.py から別スレッドで起動される。
"""
import threading
import time

import schedule
from slack_sdk import WebClient

import config


def _trigger_daily() -> None:
    """毎日定時に呼ばれる: Slack に通知 → ワークフロー開始。"""
    client = WebClient(token=config.SLACK_BOT_TOKEN)

    def say(text: str = "", blocks: list = None, **kwargs) -> None:
        client.chat_postMessage(
            channel=config.SLACK_CHANNEL,
            text=text,
            blocks=blocks or [],
            **kwargs,
        )

    say(text=f"⏰ 毎日定期投稿の時間です（{config.DAILY_POST_TIME}）。ニュースを取得中...")

    # Slack bot の _start_workflow をそのまま再利用する
    from bot.slack_bot import _start_workflow
    threading.Thread(target=_start_workflow, args=(say,), daemon=True).start()


def start_scheduler() -> None:
    """スケジューラーをブロッキングループで実行する（別スレッド推奨）。"""
    schedule.every().day.at(config.DAILY_POST_TIME).do(_trigger_daily)
    print(f"[scheduler] 毎日 {config.DAILY_POST_TIME} に自動実行するスケジュールを設定しました")

    while True:
        schedule.run_pending()
        time.sleep(30)
