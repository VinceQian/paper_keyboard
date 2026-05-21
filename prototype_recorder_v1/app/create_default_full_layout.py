from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BOARD_WIDTH_MM = 297.0
BOARD_HEIGHT_MM = 210.0

LAYOUT_ID = "keyboard_full_v1"

KEY_W_MM = 22.0
KEY_H_MM = 20.0
KEY_GAP_X_MM = 3.0

ROW_LABELS = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]

ROW_YS_MM = [
    42.0,
    68.0,
    94.0,
    120.0,
]


def build_marker_specs() -> list[dict]:
    marker_size_mm = 18.0
    marker_margin_mm = 6.0

    left_x = marker_margin_mm
    top_y = marker_margin_mm
    right_x = BOARD_WIDTH_MM - marker_margin_mm - marker_size_mm
    bottom_y = BOARD_HEIGHT_MM - marker_margin_mm - marker_size_mm

    return [
        {
            "id": 0,
            "x": left_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        {
            "id": 1,
            "x": right_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        {
            "id": 2,
            "x": right_x,
            "y": bottom_y,
            "size_mm": marker_size_mm,
        },
        {
            "id": 3,
            "x": left_x,
            "y": bottom_y,
            "size_mm": marker_size_mm,
        },
    ]


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


def build_layout() -> dict:
    keys = []

    for labels, y_mm in zip(ROW_LABELS, ROW_YS_MM):
        keys.extend(build_key_row(labels, y_mm))

    return {
        "layout_id": LAYOUT_ID,
        "title": "Paper Keyboard Full V1",
        "board_width_mm": BOARD_WIDTH_MM,
        "board_height_mm": BOARD_HEIGHT_MM,
        "dpi": 300,
        "marker_dictionary": "DICT_4X4_50",
        "markers": build_marker_specs(),
        "keys": keys,
    }


def main() -> None:
    output_dir = PROJECT_ROOT / "data" / "layouts"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{LAYOUT_ID}.json"

    layout = build_layout()

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(layout, file, ensure_ascii=False, indent=2)

    print("Created default full keyboard layout:")
    print(output_path)
    print()
    print("You can now edit this JSON and preview it with:")
    print(f"python app/preview_layout.py data/layouts/{LAYOUT_ID}.json")


if __name__ == "__main__":
    main()