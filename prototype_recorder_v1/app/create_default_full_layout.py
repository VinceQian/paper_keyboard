from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BOARD_WIDTH_MM = 297.0
BOARD_HEIGHT_MM = 210.0

LAYOUT_ID = "keyboard_full_v1"

# A4 landscape full keyboard layout.
# Keys are intentionally large, and rows are intentionally far apart
# to reduce errors caused by hand landmark jitter.
KEY_W_MM = 24.0
KEY_H_MM = 24.0
KEY_GAP_X_MM = 5.0

# Row y positions.
# Each key is 24mm tall.
#
# Number row: 36 - 60
# Q row:      78 - 102
# A row:      120 - 144
# Z row:      160 - 184
#
# This creates large vertical gaps between rows.
ROW_YS_MM = [
    36.0,
    78.0,
    120.0,
    160.0,
]

ROW_LABELS = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]


def build_marker_specs() -> list[dict]:
    marker_size_mm = 18.0

    # Top markers stay near top-left and top-right.
    top_y = 6.0
    left_top_x = 6.0
    right_top_x = BOARD_WIDTH_MM - 6.0 - marker_size_mm

    # Bottom markers are moved away from bottom corners.
    # Bottom corners are easy to block when the hand rests near the keyboard.
    #
    # These two markers are still far enough apart to help homography stability.
    bottom_y = BOARD_HEIGHT_MM - 6.0 - marker_size_mm
    bottom_left_x = 87.0
    bottom_right_x = 192.0

    return [
        {
            "id": 0,
            "x": left_top_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        {
            "id": 1,
            "x": right_top_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        {
            "id": 2,
            "x": bottom_right_x,
            "y": bottom_y,
            "size_mm": marker_size_mm,
        },
        {
            "id": 3,
            "x": bottom_left_x,
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
    print("Layout settings:")
    print(f"- Board: {BOARD_WIDTH_MM}mm x {BOARD_HEIGHT_MM}mm")
    print(f"- Key size: {KEY_W_MM}mm x {KEY_H_MM}mm")
    print(f"- Horizontal key gap: {KEY_GAP_X_MM}mm")
    print(f"- Row Y positions: {ROW_YS_MM}")
    print()
    print("Next step:")
    print(f"python app/preview_layout.py data/layouts/{LAYOUT_ID}.json")


if __name__ == "__main__":
    main()