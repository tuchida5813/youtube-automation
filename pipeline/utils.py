"""パイプライン共通ユーティリティ。"""
from pathlib import Path
from PIL import ImageFont


# 日本語フォントの候補（優先順位順）
_JP_FONT_CANDIDATES = [
    # Linux: IPA Gothic（このシステムで確認済み）
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",  # symlink alias
    # Linux: Noto CJK
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.ttf",
    # Linux: WenQuanYi
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    # Windows
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
]


def find_japanese_font(size: int) -> ImageFont.FreeTypeFont:
    """
    日本語対応フォントを探してロードする。
    見つからない場合は PIL のデフォルトフォントにフォールバックする。
    """
    for path in _JP_FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError):
                continue
    # フォントが見つからない場合の警告
    print(
        "[utils] ⚠ 日本語フォントが見つかりません。文字化けする可能性があります。\n"
        "  sudo apt install fonts-noto-cjk  などでインストールしてください。"
    )
    return ImageFont.load_default()
