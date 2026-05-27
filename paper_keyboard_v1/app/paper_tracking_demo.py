from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ============================================================
# User-adjustable settings
# ============================================================

LAYOUT_PATH = PROJECT_ROOT / "data" / "layouts" / "keyboard_full_v1.json"

CAMERA_INDEX = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

MIN_MARKERS_TO_UPDATE = 2
RANSAC_REPROJ_THRESHOLD = 3.0


def load_layout(path: str | Path) -> dict:
    path = Path(path)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_marker_size(marker: dict) -> float:
    if "size_mm" in marker:
        return float(marker["size_mm"])

    if "size" in marker:
        return float(marker["size"])

    raise ValueError(f"Marker {marker.get('id')} is missing size_mm or size.")


def get_marker_board_corners(marker: dict) -> np.ndarray:
    x = float(marker["x"])
    y = float(marker["y"])
    s = get_marker_size(marker)

    return np.array(
        [
            [x, y],
            [x + s, y],
            [x + s, y + s],
            [x, y + s],
        ],
        dtype=np.float32,
    )


def compute_homography_from_markers(
    corners,
    ids,
    layout: dict,
    ransac_reproj_threshold: float,
) -> tuple[np.ndarray | None, int, list[int]]:
    if ids is None:
        return None, 0, []

    marker_map = {
        int(marker["id"]): marker
        for marker in layout.get("markers", [])
    }

    image_points = []
    board_points = []
    used_marker_ids = []

    for i, marker_id in enumerate(ids.flatten()):
        marker_id = int(marker_id)

        if marker_id not in marker_map:
            continue

        image_corners = corners[i][0].astype(np.float32)
        board_corners = get_marker_board_corners(marker_map[marker_id])

        image_points.append(image_corners)
        board_points.append(board_corners)
        used_marker_ids.append(marker_id)

    marker_count = len(used_marker_ids)

    if marker_count == 0:
        return None, 0, []

    image_points = np.concatenate(image_points, axis=0).astype(np.float32)
    board_points = np.concatenate(board_points, axis=0).astype(np.float32)

    if len(image_points) < 4:
        return None, marker_count, used_marker_ids

    H_img_to_board, _ = cv2.findHomography(
        image_points,
        board_points,
        method=cv2.RANSAC,
        ransacReprojThreshold=ransac_reproj_threshold,
    )

    return H_img_to_board, marker_count, used_marker_ids


def transform_points(H: np.ndarray, points: np.ndarray) -> np.ndarray:
    pts = np.array([points], dtype=np.float32)
    result = cv2.perspectiveTransform(pts, H)
    return result[0]


def draw_board_overlay(
    frame: np.ndarray,
    layout: dict,
    H_board_to_img: np.ndarray,
) -> None:
    board_w = float(layout["board_width_mm"])
    board_h = float(layout["board_height_mm"])

    board_corners = np.array(
        [
            [0, 0],
            [board_w, 0],
            [board_w, board_h],
            [0, board_h],
        ],
        dtype=np.float32,
    )

    board_img_corners = transform_points(H_board_to_img, board_corners)
    board_img_corners = board_img_corners.astype(np.int32)

    cv2.polylines(
        frame,
        [board_img_corners],
        isClosed=True,
        color=(255, 255, 255),
        thickness=2,
    )

    for key in layout["keys"]:
        x = float(key["x"])
        y = float(key["y"])
        w = float(key["w"])
        h = float(key["h"])

        key_corners = np.array(
            [
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h],
            ],
            dtype=np.float32,
        )

        key_img_corners = transform_points(H_board_to_img, key_corners)
        key_img_corners = key_img_corners.astype(np.int32)

        cv2.polylines(
            frame,
            [key_img_corners],
            isClosed=True,
            color=(255, 255, 255),
            thickness=2,
        )

        center_board = np.array(
            [
                [x + w / 2.0, y + h / 2.0],
            ],
            dtype=np.float32,
        )

        center_img = transform_points(H_board_to_img, center_board)[0]
        cx, cy = int(center_img[0]), int(center_img[1])

        cv2.putText(
            frame,
            str(key["label"]),
            (cx - 10, cy + 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def create_aruco_detector(layout: dict):
    dictionary_name = (
        layout.get("marker_dictionary")
        or layout.get("aruco_dictionary")
        or "DICT_4X4_50"
    )

    if not hasattr(cv2.aruco, dictionary_name):
        raise ValueError(f"Unknown ArUco dictionary: {dictionary_name}")

    dictionary_id = getattr(cv2.aruco, dictionary_name)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_id)

    parameters = cv2.aruco.DetectorParameters()

    if hasattr(cv2.aruco, "CORNER_REFINE_SUBPIX"):
        parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        return detector, dictionary_name

    return None, dictionary_name


def detect_markers(detector, frame: np.ndarray, layout: dict):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if detector is not None:
        corners, ids, rejected = detector.detectMarkers(gray)
        return corners, ids, rejected

    dictionary_name = (
        layout.get("marker_dictionary")
        or layout.get("aruco_dictionary")
        or "DICT_4X4_50"
    )
    dictionary_id = getattr(cv2.aruco, dictionary_name)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_id)
    parameters = cv2.aruco.DetectorParameters()

    if hasattr(cv2.aruco, "CORNER_REFINE_SUBPIX"):
        parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    return cv2.aruco.detectMarkers(
        gray,
        aruco_dict,
        parameters=parameters,
    )


def open_camera(camera_index: int, width: int, height: int):
    if platform.system() == "Darwin" and hasattr(cv2, "CAP_AVFOUNDATION"):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
    else:
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {camera_index}.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    return cap


def main() -> None:
    layout = load_layout(LAYOUT_PATH)

    print("Paper tracking demo started.")
    print("Loaded layout:", layout.get("layout_id", LAYOUT_PATH.stem))
    print("Board:", layout["board_width_mm"], "x", layout["board_height_mm"], "mm")
    print("Keys:", len(layout.get("keys", [])))
    print("Markers:", len(layout.get("markers", [])))
    print("Min markers to update:", MIN_MARKERS_TO_UPDATE)

    detector, dictionary_name = create_aruco_detector(layout)

    print("Marker dictionary:", dictionary_name)

    cap = open_camera(
        camera_index=CAMERA_INDEX,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
    )

    print("Camera opened.")
    print("Camera index:", CAMERA_INDEX)
    print("Controls:")
    print("- q: quit")
    print("- r: reset calibration")
    print()

    last_good_H_img_to_board = None
    last_good_H_board_to_img = None
    last_marker_count = 0
    last_used_marker_ids: list[int] = []

    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()

            if not ret or frame is None:
                print("Cannot read frame.")
                break

            output = frame.copy()

            corners, ids, rejected = detect_markers(detector, frame, layout)

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(output, corners, ids)

            H_img_to_board, marker_count, used_marker_ids = compute_homography_from_markers(
                corners=corners,
                ids=ids,
                layout=layout,
                ransac_reproj_threshold=RANSAC_REPROJ_THRESHOLD,
            )

            updated = False

            if (
                H_img_to_board is not None
                and marker_count >= MIN_MARKERS_TO_UPDATE
            ):
                H_board_to_img = np.linalg.inv(H_img_to_board)

                last_good_H_img_to_board = H_img_to_board
                last_good_H_board_to_img = H_board_to_img
                last_marker_count = marker_count
                last_used_marker_ids = used_marker_ids
                updated = True

            if last_good_H_board_to_img is not None:
                draw_board_overlay(
                    output,
                    layout,
                    last_good_H_board_to_img,
                )

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            if last_good_H_board_to_img is None:
                calib_text = "Calibration: waiting for markers"
                calib_color = (0, 0, 255)
            elif updated:
                calib_text = (
                    f"Calibration: updated | "
                    f"visible={marker_count} | "
                    f"used={used_marker_ids}"
                )
                calib_color = (0, 255, 0)
            else:
                calib_text = (
                    f"Calibration: using last good H | "
                    f"visible={marker_count} | "
                    f"last={last_marker_count} | "
                    f"used={last_used_marker_ids}"
                )
                calib_color = (0, 255, 255)

            visible_text = (
                f"Visible known markers: {marker_count} "
                f"/ need {MIN_MARKERS_TO_UPDATE}"
            )

            cv2.putText(
                output,
                calib_text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                calib_color,
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                output,
                visible_text,
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 0) if marker_count >= MIN_MARKERS_TO_UPDATE else (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                output,
                f"FPS: {fps:.1f}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 0, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Paper Tracking Demo", output)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("r"):
                last_good_H_img_to_board = None
                last_good_H_board_to_img = None
                last_marker_count = 0
                last_used_marker_ids = []
                print("Calibration reset.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released.")


if __name__ == "__main__":
    main()