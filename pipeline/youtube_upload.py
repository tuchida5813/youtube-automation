"""
YouTube Data API v3 を使って動画をアップロードする。

初回実行時にブラウザでOAuth認証が必要。
認証情報は YOUTUBE_CREDENTIALS_FILE に保存され、以降は自動更新される。

前提:
  - Google Cloud Console でプロジェクトを作成し、YouTube Data API v3 を有効化
  - OAuth 2.0 クライアントID (デスクトップアプリ) を作成し、
    JSONファイルをダウンロードして client_secrets.json として配置
"""
import json
from pathlib import Path

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http

import config

SCOPES           = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION      = "v3"


def _get_service():
    """OAuth2認証を行い YouTube API サービスを返す。"""
    creds = None

    if config.YOUTUBE_CREDENTIALS.exists():
        with open(config.YOUTUBE_CREDENTIALS) as f:
            data = json.load(f)
        creds = google.oauth2.credentials.Credentials(
            token         = data.get("token"),
            refresh_token = data.get("refresh_token"),
            token_uri     = data.get("token_uri"),
            client_id     = data.get("client_id"),
            client_secret = data.get("client_secret"),
            scopes        = data.get("scopes"),
        )

    if not creds or not creds.valid:
        if not config.YOUTUBE_CLIENT_SECRETS.exists():
            raise FileNotFoundError(
                f"YouTube client_secrets.json が見つかりません: {config.YOUTUBE_CLIENT_SECRETS}\n"
                "Google Cloud Console から OAuth2.0 クライアントIDをダウンロードしてください。"
            )
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            str(config.YOUTUBE_CLIENT_SECRETS), SCOPES
        )
        creds = flow.run_local_server(port=0)

        # 認証情報を保存
        with open(config.YOUTUBE_CREDENTIALS, "w") as f:
            json.dump(
                {
                    "token":         creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri":     creds.token_uri,
                    "client_id":     creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes":        list(creds.scopes),
                },
                f,
            )

    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)


def upload_video(
    video_path: Path,
    thumbnail_path: Path,
    title: str,
    description: str,
    privacy: str = config.YOUTUBE_PRIVACY,
) -> str:
    """
    動画を YouTube にアップロードし、動画IDを返す。

    Args:
        video_path:     アップロードするMP4ファイル
        thumbnail_path: サムネイル画像ファイル
        title:          動画タイトル
        description:    概要欄テキスト
        privacy:        "private" | "unlisted" | "public"

    Returns:
        YouTube 動画ID（例: "dQw4w9WgXcQ"）
    """
    youtube = _get_service()

    body = {
        "snippet": {
            "title":           title,
            "description":     description,
            "categoryId":      config.YOUTUBE_CATEGORY_ID,
            "tags":            ["公衆衛生", "健康ニュース", "WHO", "CDC", "医療"],
            "defaultLanguage": "ja",
        },
        "status": {
            "privacyStatus":         privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = googleapiclient.http.MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4",
    )

    request  = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    print("  YouTube: 動画アップロード中...")
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response["id"]

    # サムネイル設定
    print("  YouTube: サムネイルを設定中...")
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=googleapiclient.http.MediaFileUpload(str(thumbnail_path)),
    ).execute()

    return video_id
