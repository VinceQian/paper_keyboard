from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from core.layout_renderer import LayoutRenderer


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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "layout_path",
        type=str,
        help="Path to layout JSON file.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for generated printable PNG.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Preview refresh interval in seconds.",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=1200,
        help="Max preview window width.",
    )
    parser.add_argument(
        "--max-height",
        type=int,
        default=850,
        help="Max preview window height.",
    )

    args = parser.parse_args()

    layout_path = Path(args.layout_path)

    if not layout_path.is_absolute():
        layout_path = PROJECT_ROOT / layout_path

    output_dir = PROJECT_ROOT / "data" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    renderer = LayoutRenderer(dpi=args.dpi)

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

    while True:
        try:
            current_mtime = layout_path.stat().st_mtime

            if last_mtime != current_mtime:
                layout = renderer.load_layout(layout_path)
                image = renderer.render(layout)

                preview = renderer.make_preview_image(
                    image,
                    max_width=args.max_width,
                    max_height=args.max_height,
                )

                last_mtime = current_mtime
                last_preview = preview
                last_layout = layout

                print("Preview updated:", time.strftime("%H:%M:%S"))

            if last_preview is not None:
                cv2.imshow("layout_preview", last_preview)

            key = cv2.waitKey(int(args.interval * 1000)) & 0xFF

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

            key = cv2.waitKey(int(args.interval * 1000)) & 0xFF

            if key == ord("q"):
                break

    cv2.destroyAllWindows()
    print("Layout preview closed.")


if __name__ == "__main__":
    main()