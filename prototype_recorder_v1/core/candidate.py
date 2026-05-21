from __future__ import annotations

from typing import Any

from core.layout import KeyboardLayout


FingerData = dict[str, Any]
CandidateData = dict[str, Any]


class CandidateDetector:
    """
    Convert finger positions into candidate key results.

    Input example:
    [
        {"id": "right_index", "x": 55, "y": 110, "confidence": 1.0}
    ]

    Output example:
    [
        {
            "finger_id": "right_index",
            "key_id": "A",
            "label": "A",
            "x": 55,
            "y": 110,
            "score": 1.0
        }
    ]
    """

    def __init__(
        self,
        layout: KeyboardLayout,
        margin: float = 0.0,
        include_none: bool = False,
    ):
        self.layout = layout
        self.margin = margin
        self.include_none = include_none

    def detect_candidates(self, fingers: list[FingerData]) -> list[CandidateData]:
        candidates: list[CandidateData] = []

        for finger in fingers:
            candidate = self._detect_one_finger(finger)

            if candidate is None:
                continue

            candidates.append(candidate)

        return candidates

    def _detect_one_finger(self, finger: FingerData) -> CandidateData | None:
        finger_id = finger.get("id", "unknown_finger")
        x = float(finger["x"])
        y = float(finger["y"])
        confidence = float(finger.get("confidence", 1.0))

        key = self.layout.find_key_by_point(x, y, margin=self.margin)

        if key is None:
            if not self.include_none:
                return None

            return {
                "finger_id": finger_id,
                "key_id": None,
                "label": None,
                "x": x,
                "y": y,
                "score": 0.0,
            }

        return {
            "finger_id": finger_id,
            "key_id": key["id"],
            "label": key["label"],
            "x": x,
            "y": y,
            "score": confidence,
        }