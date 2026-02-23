"""
動画ファイルを作成する。
背景画像 + gTTS音声 + PIL字幕オーバーレイ → MP4

字幕タイミングは「総文字数に対する各チャンクの文字数の割合」で推定する。
"""
from pathlib import Path

import numpy as np
from moviepy.editor import AudioFileClip, VideoClip
from PIL import Image, ImageDraw

import config
from pipeline.utils import find_japanese_font


def _make_subtitle_segments(subtitles: list[dict], duration: float) -> list[dict]:
    """
    字幕チャンクに開始/終了時刻を割り当てる（文字数比例配分）。

    Returns:
        [{"text": str, "start": float, "end": float}, ...]
    """
    texts = [s["text"] for s in subtitles]
    total_chars = sum(len(t) for t in texts)
    if total_chars == 0:
        return []

    segments = []
    t = 0.0
    for text in texts:
        seg_dur = max((len(text) / total_chars) * duration, 0.5)
        segments.append({"text": text, "start": t, "end": t + seg_dur})
        t += seg_dur
    return segments


def _draw_frame(bg_array: np.ndarray, text: str, font) -> np.ndarray:
    """背景 ndarray に字幕テキストを描画して返す。"""
    img = Image.fromarray(bg_array).convert("RGBA")
    w, h = img.size

    # テキストサイズ計測
    tmp_draw = ImageDraw.Draw(img)
    try:
        bbox = tmp_draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except AttributeError:  # PIL < 9.2
        tw, th = tmp_draw.textsize(text, font=font)

    pad = 18
    box_x1 = max((w - tw) // 2 - pad, 0)
    box_y1 = h - th - pad * 3 - 20
    box_x2 = min((w + tw) // 2 + pad, w)
    box_y2 = h - pad - 20

    # 半透明の字幕背景
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0, 0, 0, 155))
    img = Image.alpha_composite(img, overlay)

    # テキスト描画（影 + 本文）
    draw = ImageDraw.Draw(img)
    tx = (w - tw) // 2
    ty = box_y1 + pad
    draw.text((tx + 2, ty + 2), text, font=font, fill=(0, 0, 0, 200))   # 影
    draw.text((tx, ty),         text, font=font, fill=(255, 255, 255))   # 本文

    return np.array(img.convert("RGB"))


def create_video(
    audio_path: Path,
    subtitles: list[dict],
    output_path: Path,
) -> Path:
    """
    背景画像 + TTS音声 + 字幕オーバーレイで動画 (MP4) を作成する。

    Args:
        audio_path:  gTTSが生成したMP3ファイルパス
        subtitles:   [{"text": str}, ...] の字幕リスト
        output_path: 出力MP4パス

    Returns:
        出力ファイルのパス
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_clip = AudioFileClip(str(audio_path))
    duration   = audio_clip.duration

    # 背景画像を読み込み ndarray 化
    bg_img = (
        Image.open(config.BACKGROUND_IMAGE)
        .resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        .convert("RGB")
    )
    bg_array = np.array(bg_img)

    font     = find_japanese_font(40)
    segments = _make_subtitle_segments(subtitles, duration)

    def make_frame(t: float) -> np.ndarray:
        current_text = ""
        for seg in segments:
            if seg["start"] <= t < seg["end"]:
                current_text = seg["text"]
                break
        if current_text:
            return _draw_frame(bg_array.copy(), current_text, font)
        return bg_array.copy()

    video_clip = VideoClip(make_frame, duration=duration)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(
        str(output_path),
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )
    return output_path
