"""英語RSSフィードから最新の公衆衛生ニュースを取得する。"""
import html
import re
import feedparser

RSS_FEEDS = [
    {"name": "WHO", "url": "https://www.who.int/rss-feeds/news-releases.rss"},
    {"name": "CDC", "url": "https://tools.cdc.gov/api/v2/resources/media/132608.rss"},
]


def _strip_html(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_news(max_items: int = 3) -> list[dict]:
    """
    RSSフィードから最新の公衆衛生ニュースを取得する。

    Returns:
        [{"source", "title", "summary", "link", "published"}, ...]
    """
    articles: list[dict] = []
    for feed_info in RSS_FEEDS:
        if len(articles) >= max_items:
            break
        print(f"  → {feed_info['name']} からニュースを取得中...")
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries:
                if len(articles) >= max_items:
                    break
                title = _strip_html(entry.get("title", ""))
                if not title:
                    continue
                articles.append(
                    {
                        "source": feed_info["name"],
                        "title": title,
                        "summary": _strip_html(
                            entry.get("summary", entry.get("description", ""))
                        )[:800],
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                    }
                )
        except Exception as e:
            print(f"  ⚠ {feed_info['name']} の取得失敗: {e}")
    return articles
