#!/usr/bin/env python3
"""
公衆衛生ニュース YouTube ナレーション原稿自動生成ツール

英語の公衆衛生ニュースサイト（WHO・CDC）からRSSで最新情報を取得し、
Claude APIを使って日本語のYouTube音声ナレーション原稿を生成します。

使い方:
    ANTHROPIC_API_KEY=your_key python main.py
"""

import os
import re
import html
import datetime
import feedparser
import anthropic

# ニュースソース（英語公衆衛生RSS）
RSS_FEEDS = [
    {
        "name": "WHO",
        "url": "https://www.who.int/rss-feeds/news-releases.rss",
    },
    {
        "name": "CDC",
        "url": "https://tools.cdc.gov/api/v2/resources/media/132608.rss",
    },
]

# 取得するニュース件数
MAX_ARTICLES = 3


def strip_html(text: str) -> str:
    """HTMLタグと余分な空白を除去する。"""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_news(max_items: int = MAX_ARTICLES) -> list[dict]:
    """
    RSSフィードから最新の公衆衛生ニュースを取得する。

    Returns:
        ニュース記事のリスト（title, summary, source, link を含む辞書）
    """
    articles = []
    for feed_info in RSS_FEEDS:
        if len(articles) >= max_items:
            break
        print(f"  → {feed_info['name']} からニュースを取得中...")
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries:
                if len(articles) >= max_items:
                    break
                title = strip_html(entry.get("title", ""))
                summary = strip_html(
                    entry.get("summary", entry.get("description", ""))
                )
                if not title:
                    continue
                articles.append(
                    {
                        "source": feed_info["name"],
                        "title": title,
                        "summary": summary[:800],  # 長すぎる要約を制限
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                    }
                )
        except Exception as e:
            print(f"  ⚠ {feed_info['name']} の取得に失敗: {e}")
    return articles


def build_prompt(articles: list[dict]) -> str:
    """Claude へ送るプロンプトを組み立てる。"""
    news_block = ""
    for i, a in enumerate(articles, 1):
        news_block += f"""
【ニュース{i}】
ソース : {a['source']}
タイトル: {a['title']}
概要   : {a['summary']}
URL    : {a['link']}
"""

    return f"""あなたは公衆衛生の専門知識を持つYouTubeチャンネルのナレーターです。
以下の英語の最新公衆衛生ニュースをもとに、日本語の音声ナレーション原稿を作成してください。

=== 入力ニュース ===
{news_block}
===================

## 原稿の要件
- **対象視聴者**: 健康や医療に関心を持つ一般の日本人（専門家ではない）
- **トーン**: 落ち着いていて信頼感があり、親しみやすい
- **構成**:
  1. イントロ（チャンネル名「ヘルスニュース最前線」への挨拶と今日の内容紹介）
  2. 各ニュースの解説（タイトル読み上げ → 背景 → 内容 → 日本や私たちの生活への意義）
  3. アウトロ（まとめ・チャンネル登録・高評価の呼びかけ）
- **読み上げ時間**: 約5〜7分（約2000〜2800文字）
- **言語**: 自然な話し言葉の日本語。専門用語は平易に言い換える
- **注意**: 原稿のテキストのみを出力し、見出しや説明コメントは入れないこと

では、原稿を作成してください。"""


def generate_narration(articles: list[dict]) -> str:
    """
    Claude API（ストリーミング）でナレーション原稿を生成する。

    Returns:
        生成された日本語ナレーション原稿の文字列
    """
    client = anthropic.Anthropic()
    prompt = build_prompt(articles)

    full_text = ""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_text += text

    return full_text


def save_script(narration: str, articles: list[dict]) -> str:
    """原稿をテキストファイルに保存する。ファイル名を返す。"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"narration_{timestamp}.txt"

    sources = ", ".join(sorted({a["source"] for a in articles}))
    header = (
        f"# 公衆衛生ニュース ナレーション原稿\n"
        f"# 生成日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n"
        f"# ニュースソース: {sources}\n"
        f"# ニュース件数: {len(articles)} 件\n"
        + "=" * 60
        + "\n\n"
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(narration)

    return filename


def main() -> None:
    # API キーチェック
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("エラー: 環境変数 ANTHROPIC_API_KEY が設定されていません。")
        print("  例: export ANTHROPIC_API_KEY=sk-ant-...")
        raise SystemExit(1)

    print("=" * 56)
    print("  公衆衛生ニュース ナレーション原稿生成ツール")
    print("=" * 56)

    # ステップ 1: ニュース取得
    print("\n[1/3] ニュースを取得中...")
    articles = fetch_news()

    if not articles:
        print("エラー: ニュースを取得できませんでした。ネットワーク接続を確認してください。")
        raise SystemExit(1)

    print(f"\n取得完了: {len(articles)} 件")
    for i, a in enumerate(articles, 1):
        print(f"  {i}. [{a['source']}] {a['title'][:70]}")

    # ステップ 2: 原稿生成
    print("\n[2/3] ナレーション原稿を生成中（Claude claude-opus-4-6）...\n")
    print("-" * 56)
    narration = generate_narration(articles)
    print("\n" + "-" * 56)

    # ステップ 3: 保存
    print("\n[3/3] 原稿をファイルに保存中...")
    filename = save_script(narration, articles)
    print(f"保存完了 → {filename}")
    print("\n完了！")


if __name__ == "__main__":
    main()
