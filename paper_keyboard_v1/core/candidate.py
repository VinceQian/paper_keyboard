from __future__ import annotations

from typing import Any

from core.layout import KeyboardLayout


FingerData = dict[str, Any]
CandidateData = dict[str, Any]


class CandidateDetector:
    """
    Convert finger positions into candidate key results.

    Supports shrink_x / shrink_y:
    - visual key rectangle can stay large
    - active hitbox can be slightly smaller
    """

    def __init__(
        self,
        layout: KeyboardLayout,
        margin: float = 0.0,
        include_none: bool = False,
        shrink_x: float = 0.0,
        shrink_y: float = 0.0,
    ):
        self.layout = layout
        self.margin = margin
        self.include_none = include_none
        self.shrink_x = shrink_x
        self.shrink_y = shrink_y

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

        key = self._find_key_with_shrink(x, y)

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

    def _find_key_with_shrink(self, x: float, y: float):
        for key in self.layout.keys:
            left = float(key["x"]) + self.shrink_x - self.margin
            right = float(key["x"]) + float(key["w"]) - self.shrink_x + self.margin
            top = float(key["y"]) + self.shrink_y - self.margin
            bottom = float(key["y"]) + float(key["h"]) - self.shrink_y + self.margin

            if left <= x <= right and top <= y <= bottom:
                return key

        return None