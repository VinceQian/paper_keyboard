from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))


BOARD_WIDTH_MM = 297.0
BOARD_HEIGHT_MM = 210.0
DPI = 300
PX_PER_MM = DPI / 25.4

LAYOUT_ID = "keyboard_full_v1"
MARKER_DICTIONARY = "DICT_4X4_50"

MARKER_SIZE_MM = 18.0
MARKER_MARGIN_MM = 6.0

KEY_W_MM = 22.0
KEY_H_MM = 20.0
KEY_GAP_X_MM = 3.0
ROW_GAP_Y_MM = 6.0

ROW_YS_MM = [
    42.0,   # numbers row
    68.0,   # Q row
    94.0,   # A row
    120.0,  # Z row
]

ROW_LABELS = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]


def mm_to_px(value_mm: float) -> int:
    return int(round(value_mm * PX_PER_MM))


def px_canvas_shape() -> tuple[int, int]:
    height_px = mm_to_px(BOARD_HEIGHT_MM)
    width_px = mm_to_px(BOARD_WIDTH_MM)
    return height_px, width_px


def build_marker_specs() -> list[dict]:
    left_x = MARKER_MARGIN_MM
    top_y = MARKER_MARGIN_MM
    right_x = BOARD_WIDTH_MM - MARKER_MARGIN_MM - MARKER_SIZE_MM
    bottom_y = BOARD_HEIGHT_MM - MARKER_MARGIN_MM - MARKER_SIZE_MM

    markers = [
        {
            "id": 0,
            "x": left_x,
            "y": top_y,
            "size_mm": MARKER_SIZE_MM,
            "center_x": left_x + MARKER_SIZE_MM / 2.0,
            "center_y": top_y + MARKER_SIZE_MM / 2.0,
        },
        {
            "id": 1,
            "x": right_x,
            "y": top_y,
            "size_mm": MARKER_SIZE_MM,
            "center_x": right_x + MARKER_SIZE_MM / 2.0,
            "center_y": top_y + MARKER_SIZE_MM / 2.0,
        },
        {
            "id": 2,
            "x": right_x,
            "y": bottom_y,
            "size_mm": MARKER_SIZE_MM,
            "center_x": right_x + MARKER_SIZE_MM / 2.0,
            "center_y": bottom_y + MARKER_SIZE_MM / 2.0,
        },
        {
            "id": 3,
            "x": left_x,
            "y": bottom_y,
            "size_mm": MARKER_SIZE_MM,
            "center_x": left_x + MARKER_SIZE_MM / 2.0,
            "center_y": bottom_y + MARKER_SIZE_MM / 2.0,
        },
    ]

    return markers


def build_key_row(labels: list[str], y_mm: float) -> list[dict]:
    n = len(labels)
    total_width_mm = n * KEY_W_MM + (n - 1) * KEY_GAP_X_MM
    start_x_mm = (BOARD_WIDTH_MM - total_width_mm) / 2.0

    keys = []

    for i, label in enumerate(labels):
        x_mm = start_x_mm + i * (KEY_W_MM + KEY_GAP_X_MM)

        keys.append(
            {
                "id": label,
                "label": label,
                "x": round(x_mm, 3),
                "y": round(y_mm, 3),
                "w": KEY_W_MM,
                "h": KEY_H_MM,
            }
        )

    return keys


def build_layout_data() -> dict:
    all_keys = []

    for labels, row_y in zip(ROW_LABELS, ROW_YS_MM):
        all_keys.extend(build_key_row(labels, row_y))

    markers = build_marker_specs()

    layout_data = {
        "layout_id": LAYOUT_ID,
        "board_width_mm": BOARD_WIDTH_MM,
        "board_height_mm": BOARD_HEIGHT_MM,
        "dpi": DPI,
        "marker_dictionary": MARKER_DICTIONARY,
        "markers": markers,
        "keys": all_keys,
    }

    return layout_data


def create_blank_canvas() -> np.ndarray:
    height_px, width_px = px_canvas_shape()
    canvas = np.full((height_px, width_px, 3), 255, dtype=np.uint8)

    cv2.rectangle(
        canvas,
        (0, 0),
        (width_px - 1, height_px - 1),
        (0, 0, 0),
        2,
    )

    return canvas


def generate_aruco_marker_image(marker_id: int, size_px: int) -> np.ndarray:
    dictionary_id = getattr(cv2.aruco, MARKER_DICTIONARY)
    dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)

    if hasattr(cv2.aruco, "generateImageMarker"):
        marker = cv2.aruco.generateImageMarker(dictionary, marker_id, size_px)
    else:
        marker = np.zeros((size_px, size_px), dtype=np.uint8)
        cv2.aruco.drawMarker(dictionary, marker_id, size_px, marker, 1)

    return marker


def draw_markers(canvas: np.ndarray, markers: list[dict]) -> None:
    for marker in markers:
        x_px = mm_to_px(marker["x"])
        y_px = mm_to_px(marker["y"])
        size_px = mm_to_px(marker["size_mm"])

        marker_img = generate_aruco_marker_image(marker["id"], size_px)

        canvas[y_px:y_px + size_px, x_px:x_px + size_px, 0] = marker_img
        canvas[y_px:y_px + size_px, x_px:x_px + size_px, 1] = marker_img
        canvas[y_px:y_px + size_px, x_px:x_px + size_px, 2] = marker_img


def draw_keys(canvas: np.ndarray, keys: list[dict]) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2.0
    thickness = 4

    for key in keys:
        x1 = mm_to_px(key["x"])
        y1 = mm_to_px(key["y"])
        x2 = mm_to_px(key["x"] + key["w"])
        y2 = mm_to_px(key["y"] + key["h"])

        cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 0), 3)

        label = key["label"]
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        text_x = x1 + (x2 - x1 - text_w) // 2
        text_y = y1 + (y2 - y1 + text_h) // 2

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


def draw_title(canvas: np.ndarray) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = "Paper Keyboard Prototype"
    font_scale = 1.0
    thickness = 2

    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    x = (canvas.shape[1] - text_w) // 2
    y = mm_to_px(30)

    cv2.putText(
        canvas,
        text,
        (x, y),
        font,
        font_scale,
        (0, 0, 0),
        thickness,
        cv2.LINE_AA,
    )


def save_layout_json(layout_data: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(layout_data, file, ensure_ascii=False, indent=2)


def main() -> None:
    layouts_dir = PROJECT_ROOT / "data" / "layouts"
    generated_dir = PROJECT_ROOT / "data" / "generated"

    layouts_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)

    layout_data = build_layout_data()

    canvas = create_blank_canvas()
    draw_title(canvas)
    draw_markers(canvas, layout_data["markers"])
    draw_keys(canvas, layout_data["keys"])

    json_path = layouts_dir / f"{LAYOUT_ID}.json"
    png_path = generated_dir / f"{LAYOUT_ID}.png"

    save_layout_json(layout_data, json_path)
    cv2.imwrite(str(png_path), canvas)

    print("Generated keyboard sheet successfully.")
    print("Layout JSON:", json_path)
    print("Sheet image:", png_path)
    print()
    print("Print suggestion:")
    print("- A4 landscape")
    print("- 100% scale")
    print("- Do not fit to page")


if __name__ == "__main__":
    main()