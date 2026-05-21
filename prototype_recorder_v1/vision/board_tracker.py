from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from core.layout import KeyboardLayout


@dataclass
class BoardTrackingResult:
    corners: Any
    ids: Any
    visible_marker_count: int
    used_marker_ids: list[int]
    updated: bool
    calibrated: bool
    H_image_to_board: np.ndarray | None
    H_board_to_image: np.ndarray | None


class BoardTracker:
    """
    Stable paper board tracker.

    Behavior:
    - Use all visible known ArUco marker corners.
    - Update calibration only when enough markers are visible.
    - Keep using last good homography when markers are blocked.
    """

    def __init__(
        self,
        layout: KeyboardLayout,
        min_markers_to_update: int = 2,
        ransac_reproj_threshold: float = 3.0,
    ):
        self.layout = layout
        self.min_markers_to_update = min_markers_to_update
        self.ransac_reproj_threshold = ransac_reproj_threshold

        self.marker_map = self._build_marker_map(layout)

        self.detector, self.dictionary_name = self._create_detector(
            layout.marker_dictionary
        )

        self.last_good_H_image_to_board: np.ndarray | None = None
        self.last_good_H_board_to_image: np.ndarray | None = None
        self.last_marker_count = 0
        self.last_used_marker_ids: list[int] = []

    def _build_marker_map(self, layout: KeyboardLayout) -> dict[int, dict[str, float]]:
        marker_map: dict[int, dict[str, float]] = {}

        for marker in layout.markers:
            marker_id = int(marker["id"])

            if "size_mm" in marker:
                size = float(marker["size_mm"])
            elif "size" in marker:
                size = float(marker["size"])
            else:
                raise ValueError(f"Marker {marker_id} is missing size_mm or size.")

            marker_map[marker_id] = {
                "x": float(marker["x"]),
                "y": float(marker["y"]),
                "size": size,
            }

        if not marker_map:
            raise ValueError("Layout has no markers.")

        return marker_map

    def _create_detector(self, dictionary_name: str):
        if not hasattr(cv2.aruco, dictionary_name):
            raise ValueError(f"Unknown ArUco dictionary: {dictionary_name}")

        dictionary_id = getattr(cv2.aruco, dictionary_name)
        aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_id)

        parameters = cv2.aruco.DetectorParameters()

        if hasattr(cv2.aruco, "CORNER_REFINE_SUBPIX"):
            parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

        if hasattr(cv2.aruco, "ArucoDetector"):
            detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        else:
            detector = None

        return detector, dictionary_name

    def reset(self) -> None:
        self.last_good_H_image_to_board = None
        self.last_good_H_board_to_image = None
        self.last_marker_count = 0
        self.last_used_marker_ids = []

    def update(self, frame: np.ndarray) -> BoardTrackingResult:
        corners, ids = self._detect_markers(frame)

        H_candidate, visible_marker_count, used_marker_ids = (
            self._compute_homography_candidate(corners, ids)
        )

        updated = False

        if (
            H_candidate is not None
            and visible_marker_count >= self.min_markers_to_update
        ):
            H_board_to_image = np.linalg.inv(H_candidate)

            self.last_good_H_image_to_board = H_candidate
            self.last_good_H_board_to_image = H_board_to_image
            self.last_marker_count = visible_marker_count
            self.last_used_marker_ids = used_marker_ids
            updated = True

        calibrated = self.last_good_H_image_to_board is not None

        return BoardTrackingResult(
            corners=corners,
            ids=ids,
            visible_marker_count=visible_marker_count,
            used_marker_ids=used_marker_ids,
            updated=updated,
            calibrated=calibrated,
            H_image_to_board=self.last_good_H_image_to_board,
            H_board_to_image=self.last_good_H_board_to_image,
        )

    def _detect_markers(self, frame: np.ndarray):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.detector is not None:
            corners, ids, rejected = self.detector.detectMarkers(gray)
        else:
            dictionary_id = getattr(cv2.aruco, self.dictionary_name)
            aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_id)
            parameters = cv2.aruco.DetectorParameters()

            if hasattr(cv2.aruco, "CORNER_REFINE_SUBPIX"):
                parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray,
                aruco_dict,
                parameters=parameters,
            )

        return corners, ids

    def _compute_homography_candidate(
        self,
        corners,
        ids,
    ) -> tuple[np.ndarray | None, int, list[int]]:
        if ids is None:
            return None, 0, []

        image_points = []
        board_points = []
        used_marker_ids = []

        for i, marker_id in enumerate(ids.flatten()):
            marker_id = int(marker_id)

            if marker_id not in self.marker_map:
                continue

            image_corners = corners[i][0].astype(np.float32)
            board_corners = self._get_marker_board_corners(marker_id)

            image_points.append(image_corners)
            board_points.append(board_corners)
            used_marker_ids.append(marker_id)

        marker_count = len(used_marker_ids)

        if marker_count == 0:
            return None, 0, []

        image_points_array = np.concatenate(image_points, axis=0).astype(np.float32)
        board_points_array = np.concatenate(board_points, axis=0).astype(np.float32)

        if len(image_points_array) < 4:
            return None, marker_count, used_marker_ids

        H_image_to_board, _ = cv2.findHomography(
            image_points_array,
            board_points_array,
            method=cv2.RANSAC,
            ransacReprojThreshold=self.ransac_reproj_threshold,
        )

        return H_image_to_board, marker_count, used_marker_ids

    def _get_marker_board_corners(self, marker_id: int) -> np.ndarray:
        marker = self.marker_map[marker_id]

        x = marker["x"]
        y = marker["y"]
        s = marker["size"]

        return np.array(
            [
                [x, y],
                [x + s, y],
                [x + s, y + s],
                [x, y + s],
            ],
            dtype=np.float32,
        )

    @staticmethod
    def transform_point(
        H: np.ndarray,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        point = np.array([[[x, y]]], dtype=np.float32)
        result = cv2.perspectiveTransform(point, H)
        return float(result[0][0][0]), float(result[0][0][1])

    @staticmethod
    def transform_points(
        H: np.ndarray,
        points: np.ndarray,
    ) -> np.ndarray:
        pts = np.array([points], dtype=np.float32)
        result = cv2.perspectiveTransform(pts, H)
        return result[0]

    def draw_markers(
        self,
        frame: np.ndarray,
        result: BoardTrackingResult,
    ) -> None:
        if result.ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, result.corners, result.ids)

    def draw_board_overlay(
        self,
        frame: np.ndarray,
        result: BoardTrackingResult,
        current_key_label: str | None = None,
    ) -> None:
        if result.H_board_to_image is None:
            return

        H_board_to_image = result.H_board_to_image

        board_w = self.layout.board_width_mm
        board_h = self.layout.board_height_mm

        board_corners = np.array(
            [
                [0, 0],
                [board_w, 0],
                [board_w, board_h],
                [0, board_h],
            ],
            dtype=np.float32,
        )

        board_img_corners = self.transform_points(H_board_to_image, board_corners)
        board_img_corners = board_img_corners.astype(np.int32)

        cv2.polylines(
            frame,
            [board_img_corners],
            isClosed=True,
            color=(255, 255, 255),
            thickness=2,
        )

        for key in self.layout.keys:
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

            key_img_corners = self.transform_points(H_board_to_image, key_corners)
            key_img_corners = key_img_corners.astype(np.int32)

            if str(key["label"]) == current_key_label:
                color = (0, 255, 0)
                thickness = 4
            else:
                color = (255, 255, 255)
                thickness = 2

            cv2.polylines(
                frame,
                [key_img_corners],
                isClosed=True,
                color=color,
                thickness=thickness,
            )

            center_board = np.array(
                [
                    [x + w / 2.0, y + h / 2.0],
                ],
                dtype=np.float32,
            )

            center_img = self.transform_points(H_board_to_image, center_board)[0]
            cx, cy = int(center_img[0]), int(center_img[1])

            cv2.putText(
                frame,
                str(key["label"]),
                (cx - 10, cy + 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
                cv2.LINE_AA,
            )