"""アプリケーション全体の設定。環境変数 / .env から読み込む。"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv が未インストールでも動作する

# ─── ディレクトリ ───────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / Path(os.getenv("OUTPUT_DIR", "output"))

# ─── Anthropic ─────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = "claude-opus-4-6"

# ─── Slack ─────────────────────────────────────────────────
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")    # xoxb-...
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")    # xapp-... (Socket Mode)
SLACK_CHANNEL   = os.getenv("SLACK_CHANNEL", "#health-news")

# ─── YouTube ───────────────────────────────────────────────
YOUTUBE_CLIENT_SECRETS = BASE_DIR / os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
YOUTUBE_CREDENTIALS    = BASE_DIR / os.getenv("YOUTUBE_CREDENTIALS_FILE", "youtube_credentials.json")
YOUTUBE_CATEGORY_ID    = "25"     # News & Politics
YOUTUBE_PRIVACY        = os.getenv("YOUTUBE_PRIVACY", "private")  # 初回は非公開

# ─── アセット ───────────────────────────────────────────────
BACKGROUND_IMAGE = ASSETS_DIR / "background.png"
THUMBNAIL_BASE   = ASSETS_DIR / "thumbnail_base.png"

# ─── 動画設定 ───────────────────────────────────────────────
VIDEO_WIDTH  = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS    = 24

# ─── 字幕設定 ───────────────────────────────────────────────
# 日本語読み上げ速度の目安（文字/秒）。実際の音声長に合わせて比例配分する
SUBTITLE_CHARS_PER_SEC = 6

# ─── スケジューラ ───────────────────────────────────────────
DAILY_POST_TIME = os.getenv("DAILY_POST_TIME", "09:00")  # HH:MM (ローカル時刻)
