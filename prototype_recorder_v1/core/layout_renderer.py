from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class LayoutRenderer:
    """
    Render a keyboard layout JSON into a printable image.

    The layout JSON is the source of truth.
    Students can edit the JSON and use preview_layout.py to see the result.
    """

    def __init__(self, dpi: int = 300):
        self.dpi = dpi
        self.px_per_mm = dpi / 25.4

    def load_layout(self, path: str | Path) -> dict[str, Any]:
        path = Path(path)

        with open(path, "r", encoding="utf-8") as file:
            layout = json.load(file)

        self.validate_layout(layout)
        return layout

    def validate_layout(self, layout: dict[str, Any]) -> None:
        required_top_fields = [
            "layout_id",
            "board_width_mm",
            "board_height_mm",
            "keys",
        ]

        for field in required_top_fields:
            if field not in layout:
                raise ValueError(f"Missing top-level field: {field}")

        if layout["board_width_mm"] <= 0:
            raise ValueError("board_width_mm must be positive.")

        if layout["board_height_mm"] <= 0:
            raise ValueError("board_height_mm must be positive.")

        if not isinstance(layout["keys"], list):
            raise ValueError("keys must be a list.")

        for index, key in enumerate(layout["keys"]):
            for field in ["id", "label", "x", "y", "w", "h"]:
                if field not in key:
                    raise ValueError(f"Key at index {index} is missing field: {field}")

            if key["w"] <= 0 or key["h"] <= 0:
                raise ValueError(f"Key {key['id']} has invalid size.")

        if "markers" in layout:
            for index, marker in enumerate(layout["markers"]):
                for field in ["id", "x", "y", "size_mm"]:
                    if field not in marker:
                        raise ValueError(
                            f"Marker at index {index} is missing field: {field}"
                        )

    def mm_to_px(self, value_mm: float) -> int:
        return int(round(value_mm * self.px_per_mm))

    def render(self, layout: dict[str, Any]) -> np.ndarray:
        board_width_mm = float(layout["board_width_mm"])
        board_height_mm = float(layout["board_height_mm"])

        width_px = self.mm_to_px(board_width_mm)
        height_px = self.mm_to_px(board_height_mm)

        canvas = np.full((height_px, width_px, 3), 255, dtype=np.uint8)

        self._draw_board_border(canvas)
        self._draw_title(canvas, layout)
        self._draw_markers(canvas, layout)
        self._draw_keys(canvas, layout)

        return canvas

    def save_png(self, layout: dict[str, Any], output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        image = self.render(layout)
        cv2.imwrite(str(output_path), image)

        return output_path

    def make_preview_image(
        self,
        image: np.ndarray,
        max_width: int = 1200,
        max_height: int = 850,
    ) -> np.ndarray:
        height, width = image.shape[:2]

        scale = min(max_width / width, max_height / height, 1.0)

        preview_width = int(width * scale)
        preview_height = int(height * scale)

        return cv2.resize(image, (preview_width, preview_height))

    def _draw_board_border(self, canvas: np.ndarray) -> None:
        height, width = canvas.shape[:2]

        cv2.rectangle(
            canvas,
            (0, 0),
            (width - 1, height - 1),
            (0, 0, 0),
            2,
        )

    def _draw_title(self, canvas: np.ndarray, layout: dict[str, Any]) -> None:
        title = layout.get("title", layout["layout_id"])

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2

        (text_w, text_h), _ = cv2.getTextSize(title, font, font_scale, thickness)

        x = (canvas.shape[1] - text_w) // 2
        y = self.mm_to_px(30)

        cv2.putText(
            canvas,
            title,
            (x, y),
            font,
            font_scale,
            (0, 0, 0),
            thickness,
            cv2.LINE_AA,
        )

    def _draw_keys(self, canvas: np.ndarray, layout: dict[str, Any]) -> None:
        keys = layout["keys"]

        font = cv2.FONT_HERSHEY_SIMPLEX

        for key in keys:
            x1 = self.mm_to_px(float(key["x"]))
            y1 = self.mm_to_px(float(key["y"]))
            x2 = self.mm_to_px(float(key["x"]) + float(key["w"]))
            y2 = self.mm_to_px(float(key["y"]) + float(key["h"]))

            cv2.rectangle(
                canvas,
                (x1, y1),
                (x2, y2),
                (0, 0, 0),
                3,
            )

            label = str(key["label"])

            key_width_px = x2 - x1
            key_height_px = y2 - y1

            font_scale = min(key_width_px / 90, key_height_px / 55)
            font_scale = max(0.7, min(font_scale, 2.0))
            thickness = max(2, int(round(font_scale * 2)))

            (text_w, text_h), _ = cv2.getTextSize(
                label,
                font,
                font_scale,
                thickness,
            )

            text_x = x1 + (key_width_px - text_w) // 2
            text_y = y1 + (key_height_px + text_h) // 2

            cv2.putText(
                canvas,
                label,
                (text_x, text_y),
                font,
                font_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA,
            )

    def _draw_markers(self, canvas: np.ndarray, layout: dict[str, Any]) -> None:
        markers = layout.get("markers", [])

        if not markers:
            return

        dictionary_name = layout.get("marker_dictionary", "DICT_4X4_50")

        if not hasattr(cv2.aruco, dictionary_name):
            raise ValueError(f"Unknown ArUco dictionary: {dictionary_name}")

        dictionary_id = getattr(cv2.aruco, dictionary_name)
        dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)

        for marker in markers:
            marker_id = int(marker["id"])
            x_px = self.mm_to_px(float(marker["x"]))
            y_px = self.mm_to_px(float(marker["y"]))
            size_px = self.mm_to_px(float(marker["size_mm"]))

            marker_image = self._generate_marker(dictionary, marker_id, size_px)

            canvas[y_px:y_px + size_px, x_px:x_px + size_px, 0] = marker_image
            canvas[y_px:y_px + size_px, x_px:x_px + size_px, 1] = marker_image
            canvas[y_px:y_px + size_px, x_px:x_px + size_px, 2] = marker_image

            self._draw_marker_label(canvas, marker_id, x_px, y_px, size_px)

    def _generate_marker(self, dictionary, marker_id: int, size_px: int) -> np.ndarray:
        if hasattr(cv2.aruco, "generateImageMarker"):
            return cv2.aruco.generateImageMarker(dictionary, marker_id, size_px)

        marker = np.zeros((size_px, size_px), dtype=np.uint8)
        cv2.aruco.drawMarker(dictionary, marker_id, size_px, marker, 1)
        return marker

    def _draw_marker_label(
        self,
        canvas: np.ndarray,
        marker_id: int,
        x_px: int,
        y_px: int,
        size_px: int,
    ) -> None:
        label = f"M{marker_id}"

        cv2.putText(
            canvas,
            label,
            (x_px, y_px + size_px + self.mm_to_px(5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )