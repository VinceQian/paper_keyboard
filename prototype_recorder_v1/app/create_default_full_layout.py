from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BOARD_WIDTH_MM = 297.0
BOARD_HEIGHT_MM = 210.0

# Keep the same layout id so the rest of the pipeline can still use
# data/layouts/keyboard_full_v1.json by default.
LAYOUT_ID = "keyboard_full_v1"

# New design:
# - key size goes back to around the earlier scale
# - horizontal gaps stay narrow
# - rows are spread out a bit more, but the whole keyboard block is moved upward
#   so the bottom area can be reserved for markers
KEY_W_MM = 20.0
KEY_H_MM = 22.0
KEY_GAP_X_MM = 3.0

ROW_LABELS = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]

# Row ranges:
# 30 - 52
# 62 - 84
# 94 - 116
# 126 - 148
#
# So each row gap is about 10mm, and the bottom area stays relatively open.
ROW_YS_MM = [
    30.0,
    62.0,
    94.0,
    126.0,
]


def build_marker_specs() -> list[dict]:
    marker_size_mm = 18.0

    # Basic anchor coordinates
    left_x = 6.0
    right_x = BOARD_WIDTH_MM - 6.0 - marker_size_mm

    top_y = 6.0
    side_y = 72.0
    bottom_y = BOARD_HEIGHT_MM - 6.0 - marker_size_mm  # 186 for A4 landscape

    # Top middle markers
    top_mid_left_x = 96.0
    top_mid_right_x = 183.0

    # Bottom middle markers
    bottom_mid_left_x = 96.0
    bottom_mid_right_x = 183.0

    return [
        # top left
        {
            "id": 0,
            "x": left_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        # top middle-left
        {
            "id": 1,
            "x": top_mid_left_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        # top middle-right
        {
            "id": 2,
            "x": top_mid_right_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        # top right
        {
            "id": 3,
            "x": right_x,
            "y": top_y,
            "size_mm": marker_size_mm,
        },
        # left side upper
        {
            "id": 4,
            "x": left_x,
            "y": side_y,
            "size_mm": marker_size_mm,
        },
        # right side upper
        {
            "id": 5,
            "x": right_x,
            "y": side_y,
            "size_mm": marker_size_mm,
        },
        # bottom middle-left
        {
            "id": 6,
            "x": bottom_mid_left_x,
            "y": bottom_y,
            "size_mm": marker_size_mm,
        },
        # bottom middle-right
        {
            "id": 7,
            "x": bottom_mid_right_x,
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

    print("Created keyboard layout:")
    print(output_path)
    print()
    print("Layout settings:")
    print(f"- Board: {BOARD_WIDTH_MM}mm x {BOARD_HEIGHT_MM}mm")
    print(f"- Key size: {KEY_W_MM}mm x {KEY_H_MM}mm")
    print(f"- Horizontal gap: {KEY_GAP_X_MM}mm")
    print(f"- Row Y positions: {ROW_YS_MM}")
    print(f"- Marker count: {len(layout['markers'])}")
    print()
    print("Next step:")
    print(f"python app/preview_layout.py data/layouts/{LAYOUT_ID}.json")


if __name__ == "__main__":
    main()