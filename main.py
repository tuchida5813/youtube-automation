#!/usr/bin/env python3
"""
公衆衛生ニュース YouTube ナレーション原稿・動画 自動生成ツール（CLIモード）

Slack/YouTube なしで手元で動作確認したい場合に使用します。

使い方:
    # 原稿のみ生成（旧来の動作）
    ANTHROPIC_API_KEY=sk-ant-... python main.py

    # 動画まで生成
    ANTHROPIC_API_KEY=sk-ant-... python main.py --video

    # 動画 + YouTube アップロード
    ANTHROPIC_API_KEY=sk-ant-... python main.py --video --upload
"""
import os
import sys
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="公衆衛生ニュース YouTube 自動生成 (CLIモード)")
    parser.add_argument("--video",  action="store_true", help="動画ファイルも作成する")
    parser.add_argument("--upload", action="store_true", help="YouTube にアップロードする（--video 必須）")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("エラー: 環境変数 ANTHROPIC_API_KEY が設定されていません。")
        sys.exit(1)

    print("=" * 56)
    print("  公衆衛生ニュース 動画制作パイプライン (CLIモード)")
    print("=" * 56)

    # ベースアセットが存在しない場合は自動生成
    import config
    if not config.BACKGROUND_IMAGE.exists():
        print("[setup] アセットを自動生成します...")
        from assets.create_assets import create_background, create_thumbnail_base
        config.ASSETS_DIR.mkdir(exist_ok=True)
        create_background()
        create_thumbnail_base()

    # ニュース取得
    from pipeline.news import fetch_news
    print("\n[1/2] ニュースを取得中...")
    articles = fetch_news()
    if not articles:
        print("エラー: ニュースを取得できませんでした。")
        sys.exit(1)

    print(f"取得完了: {len(articles)} 件")
    for i, a in enumerate(articles, 1):
        print(f"  {i}. [{a['source']}] {a['title'][:70]}")

    if not args.video:
        # 原稿のみ生成（旧来の動作）
        from pipeline.script import generate_script
        import datetime

        print("\n[2/2] ナレーション原稿を生成中...\n" + "-" * 56)
        result = generate_script(articles)
        print("-" * 56)

        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"narration_{ts}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {result['title']}\n\n{result['narration']}\n")
        print(f"\n原稿を保存しました: {filename}")
        return

    # 動画まで生成
    from workflow import run_pipeline
    print("\n[2/2] パイプライン実行中（原稿 → TTS → サムネイル → 動画）...")
    state = run_pipeline(articles)

    print("\n✅ 完了！")
    print(f"  動画       : {state.video_path}")
    print(f"  サムネイル : {state.thumbnail_path}")
    print(f"  音声       : {state.audio_path}")

    if args.upload:
        from pipeline.youtube_upload import upload_video
        print("\n⬆ YouTube にアップロード中...")
        video_id    = upload_video(
            video_path=state.video_path,
            thumbnail_path=state.thumbnail_path,
            title=state.script_result["title"],
            description=state.script_result["description"],
        )
        print(f"🎉 アップロード完了: https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
