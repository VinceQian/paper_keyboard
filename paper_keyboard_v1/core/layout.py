from __future__ import annotations

import json
from pathlib import Path
from typing import Any


KeyData = dict[str, Any]
MarkerData = dict[str, Any]


class KeyboardLayout:
    """
    Load and query a paper keyboard layout.

    The layout JSON is the source of truth for:
    - board size
    - key positions
    - ArUco marker positions
    """

    REQUIRED_KEY_FIELDS = {"id", "label", "x", "y", "w", "h"}
    REQUIRED_MARKER_FIELDS = {"id", "x", "y", "size_mm"}

    def __init__(
        self,
        board_width_mm: float,
        board_height_mm: float,
        keys: list[KeyData],
        layout_id: str = "keyboard_layout",
        title: str | None = None,
        dpi: int = 300,
        marker_dictionary: str = "DICT_4X4_50",
        markers: list[MarkerData] | None = None,
    ):
        self.layout_id = layout_id
        self.title = title or layout_id
        self.board_width_mm = float(board_width_mm)
        self.board_height_mm = float(board_height_mm)
        self.dpi = int(dpi)
        self.marker_dictionary = marker_dictionary
        self.keys = keys
        self.markers = markers or []

        self._validate()

    @classmethod
    def from_json(cls, path: str | Path) -> "KeyboardLayout":
        path = Path(path)

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return cls(
            layout_id=data.get("layout_id", path.stem),
            title=data.get("title"),
            board_width_mm=data["board_width_mm"],
            board_height_mm=data["board_height_mm"],
            dpi=data.get("dpi", 300),
            marker_dictionary=data.get("marker_dictionary", "DICT_4X4_50"),
            markers=data.get("markers", []),
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

            if float(key["w"]) <= 0 or float(key["h"]) <= 0:
                raise ValueError(f"Key {key['id']} must have positive width and height.")

        if not isinstance(self.markers, list):
            raise TypeError("markers must be a list.")

        for index, marker in enumerate(self.markers):
            missing_fields = self.REQUIRED_MARKER_FIELDS - set(marker.keys())

            if missing_fields:
                raise ValueError(
                    f"Marker at index {index} is missing fields: {missing_fields}"
                )

            if float(marker["size_mm"]) <= 0:
                raise ValueError(f"Marker {marker['id']} must have positive size.")

    def is_inside_key(
        self,
        x: float,
        y: float,
        key: KeyData,
        margin: float = 0.0,
    ) -> bool:
        left = float(key["x"]) - margin
        right = float(key["x"]) + float(key["w"]) + margin
        top = float(key["y"]) - margin
        bottom = float(key["y"]) + float(key["h"]) + margin

        return left <= x <= right and top <= y <= bottom

    def find_key_by_point(
        self,
        x: float,
        y: float,
        margin: float = 0.0,
    ) -> KeyData | None:
        for key in self.keys:
            if self.is_inside_key(x, y, key, margin=margin):
                return key

        return None

    def get_marker_centers_mm(self) -> dict[int, dict[str, float]]:
        """
        Return marker center positions in paper coordinates.

        If center_x / center_y exist in JSON, use them.
        Otherwise compute from x, y, size_mm.
        """
        centers: dict[int, dict[str, float]] = {}

        for marker in self.markers:
            marker_id = int(marker["id"])

            if "center_x" in marker and "center_y" in marker:
                center_x = float(marker["center_x"])
                center_y = float(marker["center_y"])
            else:
                center_x = float(marker["x"]) + float(marker["size_mm"]) / 2.0
                center_y = float(marker["y"]) + float(marker["size_mm"]) / 2.0

            centers[marker_id] = {
                "x": center_x,
                "y": center_y,
            }

        return centers

    def to_dict(self) -> dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "title": self.title,
            "board_width_mm": self.board_width_mm,
            "board_height_mm": self.board_height_mm,
            "dpi": self.dpi,
            "marker_dictionary": self.marker_dictionary,
            "markers": self.markers,
            "keys": self.keys,
        }