"""
サムネイル画像を作成する。
thumbnail_base.png (または background.png) にタイトルテキストを重ねて出力する。
"""
import datetime
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw

import config
from pipeline.utils import find_japanese_font


def create_thumbnail(title: str, output_path: Path) -> Path:
    """
    ベース画像にタイトルテキストを重ねてサムネイル (JPEG) を作成する。

    Args:
        title:       動画タイトル文字列
        output_path: 出力先パス (.jpg)

    Returns:
        出力ファイルのパス
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ベース画像の読み込み
    base_path = config.THUMBNAIL_BASE if config.THUMBNAIL_BASE.exists() else config.BACKGROUND_IMAGE
    img = Image.open(base_path).convert("RGBA").resize((1280, 720))

    draw = ImageDraw.Draw(img)
    font_channel = find_japanese_font(34)
    font_title   = find_japanese_font(62)
    font_date    = find_japanese_font(30)

    # ── チャンネル名（上部バー内）──────────────────────────
    draw.text((30, 22), "ヘルスニュース最前線", font=font_channel, fill=(255, 255, 255, 230))

    # ── タイトル（中央、折り返し）──────────────────────────
    wrapped_lines = textwrap.wrap(title, width=16)
    total_h = 0
    line_heights = []
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        lh = bbox[3] - bbox[1] + 14
        line_heights.append(lh)
        total_h += lh

    y = (720 - total_h) // 2 + 10  # 中央より少し下
    for line, lh in zip(wrapped_lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        lw = bbox[2] - bbox[0]
        x = (1280 - lw) // 2

        # 影（視認性向上）
        draw.text((x + 3, y + 3), line, font=font_title, fill=(0, 0, 0, 180))
        # 本文
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255, 255))
        y += lh

    # ── 日付（下部バー内）──────────────────────────────────
    date_str = datetime.date.today().strftime("%Y年%-m月%-d日")
    draw.text((30, 660), date_str, font=font_date, fill=(200, 200, 200, 200))

    img.convert("RGB").save(str(output_path), "JPEG", quality=95)
    return output_path
