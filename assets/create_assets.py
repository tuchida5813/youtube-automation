"""
ベースとなる背景画像 (background.png) と
サムネイルテンプレート (thumbnail_base.png) を生成するスクリプト。

使い方:
    python assets/create_assets.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).parent
WIDTH, HEIGHT = 1280, 720


def create_background() -> Path:
    """深緑〜紺グラデーションの背景画像を作成する。"""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # グラデーション（上: 深紺 → 下: ダークティール）
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(8  + ratio * 15)
        g = int(32 + ratio * 45)
        b = int(75 + ratio * 55)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # 装飾: 薄い円弧（医療・健康イメージ）
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for cx, cy, r, alpha in [
        (80,   80,   90, 35),
        (1200, 640,  70, 28),
        (640,  360, 300, 12),
    ]:
        ov_draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=(100, 210, 170, alpha),
            width=3,
        )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    path = ASSETS_DIR / "background.png"
    img.save(str(path))
    print(f"作成: {path}")
    return path


def create_thumbnail_base() -> Path:
    """背景画像に上下バーを追加したサムネイルテンプレートを作成する。"""
    bg = Image.open(ASSETS_DIR / "background.png").copy()
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    # 上部バー（チャンネル名用）
    ov_draw.rectangle([0, 0, WIDTH, 90], fill=(0, 20, 50, 200))
    # 下部バー（日付用）
    ov_draw.rectangle([0, HEIGHT - 70, WIDTH, HEIGHT], fill=(0, 20, 50, 180))

    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    path = ASSETS_DIR / "thumbnail_base.png"
    img.save(str(path))
    print(f"作成: {path}")
    return path


if __name__ == "__main__":
    ASSETS_DIR.mkdir(exist_ok=True)
    create_background()
    create_thumbnail_base()
    print("✅ アセット生成完了")
