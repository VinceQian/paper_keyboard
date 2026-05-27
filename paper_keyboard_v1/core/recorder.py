from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DemoRecorder:
    """
    Record intermediate demo data.

    The recorder does not know how the data is generated.
    It only saves structured frame data into a JSON file.

    This makes it usable for:
    - live prototype demos
    - classroom simulation data
    - debugging
    - later offline replay
    """

    def __init__(
        self,
        output_dir: str | Path,
        session_id: str | None = None,
        layout_id: str | None = None,
        source: str = "prototype_recorder_v1",
        notes: str = "",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = session_id or self._make_session_id()
        self.layout_id = layout_id
        self.source = source
        self.notes = notes

        self.created_at = datetime.now(timezone.utc).isoformat()
        self._start_time = time.perf_counter()
        self.frames: list[dict[str, Any]] = []

    def add_frame(
        self,
        frame_id: int,
        fingers: list[dict[str, Any]],
        candidates: list[dict[str, Any]] | None = None,
        timestamp: float | None = None,
        audio_peak: bool | None = None,
        side_contacts: list[dict[str, Any]] | None = None,
        image_path: str | None = None,
        debug: dict[str, Any] | None = None,
    ) -> None:
        """
        Add one frame of recorded data.

        For Lesson 1, fingers and candidates are enough.
        For later lessons, we can also record audio_peak and side_contacts.
        """
        if timestamp is None:
            timestamp = time.perf_counter() - self._start_time

        frame = {
            "frame_id": frame_id,
            "timestamp": round(timestamp, 6),
            "fingers": fingers,
            "candidates": candidates or [],
            "audio_peak": audio_peak,
            "side_contacts": side_contacts or [],
            "image_path": image_path,
            "debug": debug or {},
        }

        self.frames.append(frame)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": {
                "session_id": self.session_id,
                "created_at": self.created_at,
                "source": self.source,
                "layout_id": self.layout_id,
                "notes": self.notes,
            },
            "frames": self.frames,
        }

    def save(self, filename: str | None = None) -> Path:
        if filename is None:
            filename = f"{self.session_id}.json"

        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)

        return output_path

    @staticmethod
    def _make_session_id() -> str:
        now = datetime.now()
        return now.strftime("session_%Y%m%d_%H%M%S")