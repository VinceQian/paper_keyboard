from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from core.candidate import CandidateDetector
from core.layout import KeyboardLayout
from core.recorder import DemoRecorder


def main() -> None:
    layout_path = PROJECT_ROOT / "data" / "layouts" / "keyboard_small.json"
    output_dir = PROJECT_ROOT / "data" / "recorded"

    layout = KeyboardLayout.from_json(layout_path)
    candidate_detector = CandidateDetector(layout=layout, margin=0.0)

    recorder = DemoRecorder(
        output_dir=output_dir,
        layout_id=layout.layout_id,
        source="synthetic_demo_record",
        notes="Synthetic test before connecting real camera.",
    )

    # This simulates several frames from a top camera.
    # Later, these frames will come from the real vision pipeline.
    sample_frames = [
        {
            "frame_id": 1,
            "timestamp": 0.00,
            "fingers": [
                {"id": "right_index", "x": 10, "y": 10, "confidence": 1.0}
            ],
        },
        {
            "frame_id": 2,
            "timestamp": 0.10,
            "fingers": [
                {"id": "right_index", "x": 55, "y": 110, "confidence": 1.0}
            ],
        },
        {
            "frame_id": 3,
            "timestamp": 0.20,
            "fingers": [
                {"id": "right_index", "x": 115, "y": 115, "confidence": 1.0}
            ],
        },
        {
            "frame_id": 4,
            "timestamp": 0.30,
            "fingers": [
                {"id": "right_index", "x": 145, "y": 150, "confidence": 1.0}
            ],
        },
    ]

    print("Demo recorder started.")
    print("Layout:", layout.layout_id)

    for raw_frame in sample_frames:
        fingers = raw_frame["fingers"]
        candidates = candidate_detector.detect_candidates(fingers)

        recorder.add_frame(
            frame_id=raw_frame["frame_id"],
            timestamp=raw_frame["timestamp"],
            fingers=fingers,
            candidates=candidates,
            debug={
                "mode": "synthetic_test",
            },
        )

        print("-" * 40)
        print("Frame:", raw_frame["frame_id"])
        print("Fingers:", fingers)

        if candidates:
            print("Candidates:", candidates)
        else:
            print("Candidates: none")

    output_path = recorder.save()

    print("-" * 40)
    print("Saved recorded data to:")
    print(output_path)
    print("Demo recorder finished.")


if __name__ == "__main__":
    main()