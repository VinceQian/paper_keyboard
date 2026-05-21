from __future__ import annotations

import json
from pathlib import Path
from typing import Any


KeyData = dict[str, Any]


class KeyboardLayout:
    """
    Load and query a paper keyboard layout.

    A key is represented by:
    {
        "id": "A",
        "label": "A",
        "x": 50,
        "y": 105,
        "w": 24,
        "h": 24
    }

    x, y are the top-left corner of the key in paper coordinates.
    w, h are the width and height of the key.
    """

    REQUIRED_KEY_FIELDS = {"id", "label", "x", "y", "w", "h"}

    def __init__(
        self,
        board_width_mm: float,
        board_height_mm: float,
        keys: list[KeyData],
        layout_id: str = "keyboard_layout",
    ):
        self.layout_id = layout_id
        self.board_width_mm = board_width_mm
        self.board_height_mm = board_height_mm
        self.keys = keys

        self._validate()

    @classmethod
    def from_json(cls, path: str | Path) -> "KeyboardLayout":
        path = Path(path)

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return cls(
            layout_id=data.get("layout_id", path.stem),
            board_width_mm=data["board_width_mm"],
            board_height_mm=data["board_height_mm"],
            keys=data["keys"],
        )

    def _validate(self) -> None:
        if self.board_width_mm <= 0:
            raise ValueError("board_width_mm must be positive.")

        if self.board_height_mm <= 0:
            raise ValueError("board_height_mm must be positive.")

        if not isinstance(self.keys, list):
            raise TypeError("keys must be a list.")

        for index, key in enumerate(self.keys):
            missing_fields = self.REQUIRED_KEY_FIELDS - set(key.keys())
            if missing_fields:
                raise ValueError(
                    f"Key at index {index} is missing fields: {missing_fields}"
                )

            if key["w"] <= 0 or key["h"] <= 0:
                raise ValueError(f"Key {key['id']} must have positive width and height.")

    def is_inside_key(
        self,
        x: float,
        y: float,
        key: KeyData,
        margin: float = 0.0,
    ) -> bool:
        """
        Check whether a point is inside a key rectangle.

        margin can make the key area slightly larger or smaller.
        Positive margin makes detection more forgiving.
        """
        left = key["x"] - margin
        right = key["x"] + key["w"] + margin
        top = key["y"] - margin
        bottom = key["y"] + key["h"] + margin

        return left <= x <= right and top <= y <= bottom

    def find_key_by_point(
        self,
        x: float,
        y: float,
        margin: float = 0.0,
    ) -> KeyData | None:
        """
        Find the first key that contains the point.

        Returns:
            key dict if found
            None if the point is not inside any key
        """
        for key in self.keys:
            if self.is_inside_key(x, y, key, margin=margin):
                return key

        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "board_width_mm": self.board_width_mm,
            "board_height_mm": self.board_height_mm,
            "keys": self.keys,
        }