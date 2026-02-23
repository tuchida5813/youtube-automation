"""共有データモデル。循環インポートを避けるため独立したモジュールに定義する。"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class WorkflowState:
    """1回の動画制作ワークフロー全体の状態を保持する。"""
    workflow_id: str
    articles: list[dict]
    script_result: dict                  # {title, description, narration, subtitles}
    audio_path: Optional[Path] = None
    thumbnail_path: Optional[Path] = None
    video_path: Optional[Path] = None
