"""
Claude APIを使ってナレーション原稿・タイトル・YouTube概要・字幕を生成する。
出力は JSON 形式: {title, description, narration, subtitles: [{text}]}
"""
import json
import re
import anthropic
import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _build_prompt(articles: list[dict]) -> str:
    news_block = ""
    for i, a in enumerate(articles, 1):
        news_block += f"""
【ニュース{i}】
ソース  : {a['source']}
タイトル: {a['title']}
概要    : {a['summary']}
URL     : {a['link']}
"""

    return f"""あなたは公衆衛生専門のYouTubeチャンネル「ヘルスニュース最前線」のコンテンツ担当です。
以下の英語ニュースをもとに、YouTube動画用のコンテンツを **JSON のみ** で出力してください。

=== 入力ニュース ==={news_block}
===================

## 出力JSON形式（コードブロック不要、純粋なJSONのみ）
{{
  "title": "動画タイトル（28文字以内、キャッチーで検索されやすいもの）",
  "description": "YouTube概要欄テキスト（200〜350文字）\\n\\n#公衆衛生 #健康ニュース #WHO などハッシュタグ5個を末尾に付ける",
  "narration": "日本語ナレーション原稿（イントロ→各ニュース解説→アウトロ）",
  "subtitles": [
    {{"text": "字幕テキスト（画面表示用の短い文、20〜30文字）"}},
    ...
  ]
}}

## 各フィールドの要件
- **title**: 28文字以内
- **description**: 改行を含めてよい。末尾にハッシュタグ5個
- **narration**: 自然な話し言葉。専門用語は平易に解説。イントロ・各ニュース・アウトロ構成。2200〜2800文字
- **subtitles**: narrationを20〜30文字程度の短いチャンクに分割したもの（合計70〜100個）
"""


def generate_script(articles: list[dict]) -> dict:
    """
    Claude APIでナレーション原稿・タイトル・概要・字幕を生成する。

    Returns:
        {"title": str, "description": str, "narration": str, "subtitles": [{"text": str}]}
    """
    prompt = _build_prompt(articles)
    raw = ""

    with _client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            raw += text

    print()  # 改行

    # コードブロックが含まれている場合は除去
    raw = raw.strip()
    raw = re.sub(r"^```[a-z]*\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)
