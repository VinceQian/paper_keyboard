from __future__ import annotations

import sys
import time
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from core.layout_renderer import LayoutRenderer


# ============================================================
# User-adjustable settings
# ============================================================

LAYOUT_PATH = PROJECT_ROOT / "data" / "layouts" / "keyboard_full_v1.json"

DPI = 300

# 预览窗口最大尺寸，不影响实际导出 PNG 的尺寸。
MAX_PREVIEW_WIDTH = 1200
MAX_PREVIEW_HEIGHT = 850

# 文件检查间隔。
REFRESH_INTERVAL_SECONDS = 0.5

OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"


def make_error_image(message: str) -> np.ndarray:
    width = 1200
    height = 600

    image = np.full((height, width, 3), 245, dtype=np.uint8)

    cv2.putText(
        image,
        "Layout Preview Error",
        (40, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 0, 255),
        3,
        cv2.LINE_AA,
    )

    lines = split_text(message, max_chars=90)

    y = 130
    for line in lines[:12]:
        cv2.putText(
            image,
            line,
            (40, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
        y += 36

    return image


def split_text(text: str, max_chars: int) -> list[str]:
    words = text.replace("\n", " ").split(" ")

    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def get_output_path(layout_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{layout_path.stem}.png"


def main() -> None:
    layout_path = Path(LAYOUT_PATH)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    renderer = LayoutRenderer(dpi=DPI)

    last_mtime = None
    last_preview = None
    last_layout = None

    print("Layout preview started.")
    print("Watching:", layout_path)
    print()
    print("Controls:")
    print("- Edit and save the JSON file to refresh preview")
    print("- Press s in preview window to save PNG")
    print("- Press q in preview window to quit")
    print()

    while True:
        try:
            current_mtime = layout_path.stat().st_mtime

            if last_mtime != current_mtime:
                layout = renderer.load_layout(layout_path)
                image = renderer.render(layout)

                preview = renderer.make_preview_image(
                    image,
                    max_width=MAX_PREVIEW_WIDTH,
                    max_height=MAX_PREVIEW_HEIGHT,
                )

                last_mtime = current_mtime
                last_preview = preview
                last_layout = layout

                print("Preview updated:", time.strftime("%H:%M:%S"))

            if last_preview is not None:
                cv2.imshow("layout_preview", last_preview)

            key = cv2.waitKey(int(REFRESH_INTERVAL_SECONDS * 1000)) & 0xFF

            if key == ord("q"):
                break

            if key == ord("s"):
                if last_layout is not None:
                    output_path = get_output_path(layout_path, output_dir)
                    renderer.save_png(last_layout, output_path)
                    print("Saved PNG:", output_path)

        except Exception as error:
            error_image = make_error_image(str(error))
            cv2.imshow("layout_preview", error_image)

            key = cv2.waitKey(int(REFRESH_INTERVAL_SECONDS * 1000)) & 0xFF

            if key == ord("q"):
                break

    cv2.destroyAllWindows()
    print("Layout preview closed.")


if __name__ == "__main__":
    main()