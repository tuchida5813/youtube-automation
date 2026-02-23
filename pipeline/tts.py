"""テキストを日本語音声ファイルに変換する（gTTS使用）。"""
from pathlib import Path
from gtts import gTTS


def text_to_speech(text: str, output_path: Path) -> Path:
    """
    日本語テキストをMP3音声ファイルに変換する。

    Args:
        text:        読み上げるテキスト
        output_path: 出力MP3ファイルのパス

    Returns:
        出力ファイルのパス
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tts = gTTS(text=text, lang="ja", slow=False)
    tts.save(str(output_path))
    return output_path
