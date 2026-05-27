from __future__ import annotations

import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from vision.camera import CameraSource


def main() -> None:
    camera = CameraSource(
        camera_index=1,
        width=1280,
        height=720,
        fps=30,
        flip_horizontal=False,
    )

    camera.open()
    print("Camera opened.")
    print(camera.get_info())
    print("Press q to quit.")

    try:
        while True:
            frame = camera.read()

            if frame is None:
                print("Failed to read frame.")
                break

            image = frame.image.copy()

            cv2.putText(
                image,
                f"frame={frame.frame_id} time={frame.timestamp:.2f}s",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
            )

            cv2.imshow("camera_smoke_test", image)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released.")


if __name__ == "__main__":
    main()