from __future__ import annotations

import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from core.layout import KeyboardLayout
from vision.aruco_tracker import ArucoTracker
from vision.camera import CameraSource
from vision.coordinate_mapper import CoordinateMapper


def main() -> None:
    layout_path = PROJECT_ROOT / "data" / "layouts" / "keyboard_small.json"

    layout = KeyboardLayout.from_json(layout_path)

    # For the first prototype:
    # marker 0: top-left
    # marker 1: top-right
    # marker 2: bottom-right
    # marker 3: bottom-left
    #
    # These are marker center positions in paper coordinates.
    # Later we can adjust them based on the actual printed sheet.
    marker_centers_mm = {
        0: {"x": 15.0, "y": 15.0},
        1: {"x": layout.board_width_mm - 15.0, "y": 15.0},
        2: {"x": layout.board_width_mm - 15.0, "y": layout.board_height_mm - 15.0},
        3: {"x": 15.0, "y": layout.board_height_mm - 15.0},
    }

    camera = CameraSource(
        camera_index=0,
        width=1280,
        height=720,
        fps=30,
        flip_horizontal=False,
    )

    aruco_tracker = ArucoTracker(dictionary_name="DICT_4X4_50")
    mapper = CoordinateMapper(marker_centers_mm=marker_centers_mm)

    camera.open()
    print("Camera opened.")
    print("Press q to quit.")

    try:
        while True:
            frame = camera.read()

            if frame is None:
                print("Failed to read frame.")
                break

            aruco_result = aruco_tracker.detect(frame.image)
            homography = mapper.compute_from_markers(aruco_result)

            if homography is None:
                homography = mapper.get_current_result()

            output = aruco_tracker.draw(frame.image, aruco_result)

            if homography is not None:
                output = mapper.draw_paper_axes(
                    output,
                    homography,
                    board_width_mm=layout.board_width_mm,
                    board_height_mm=layout.board_height_mm,
                )

                status = f"H OK markers={homography.used_marker_ids}"
            else:
                status = f"No H markers={aruco_result.marker_ids}"

            cv2.putText(
                output,
                status,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )

            cv2.imshow("paper_tracking_demo", output)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released.")


if __name__ == "__main__":
    main()