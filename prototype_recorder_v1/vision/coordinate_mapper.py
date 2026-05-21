from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from vision.aruco_tracker import ArucoDetectionResult


@dataclass
class HomographyResult:
    H_image_to_paper: np.ndarray
    H_paper_to_image: np.ndarray
    used_marker_ids: list[int]
    image_points: np.ndarray
    paper_points: np.ndarray


class CoordinateMapper:
    """
    Compute homography between camera image coordinates and paper coordinates.

    We define paper coordinates in millimeters:
    - paper origin: top-left of the paper
    - x axis: left to right
    - y axis: top to bottom

    Required marker layout example:
    {
        0: {"x": 0, "y": 0},
        1: {"x": 297, "y": 0},
        2: {"x": 297, "y": 210},
        3: {"x": 0, "y": 210}
    }

    Here x, y represent the paper coordinate of each marker's center.
    """

    def __init__(
        self,
        marker_centers_mm: dict[int, dict[str, float]],
        min_markers: int = 4,
    ):
        self.marker_centers_mm = marker_centers_mm
        self.min_markers = min_markers

        self.last_good_result: HomographyResult | None = None

    def compute_from_markers(
        self,
        detection: ArucoDetectionResult,
    ) -> HomographyResult | None:
        image_points: list[list[float]] = []
        paper_points: list[list[float]] = []
        used_marker_ids: list[int] = []

        for marker_id in detection.marker_ids:
            if marker_id not in self.marker_centers_mm:
                continue

            corners = detection.corners_by_id[marker_id]
            center = corners.mean(axis=0)

            paper_center = self.marker_centers_mm[marker_id]

            image_points.append([float(center[0]), float(center[1])])
            paper_points.append([float(paper_center["x"]), float(paper_center["y"])])
            used_marker_ids.append(marker_id)

        if len(used_marker_ids) < self.min_markers:
            return None

        image_points_array = np.array(image_points, dtype=np.float32)
        paper_points_array = np.array(paper_points, dtype=np.float32)

        H_image_to_paper, _ = cv2.findHomography(
            image_points_array,
            paper_points_array,
            method=0,
        )

        if H_image_to_paper is None:
            return None

        H_paper_to_image = np.linalg.inv(H_image_to_paper)

        result = HomographyResult(
            H_image_to_paper=H_image_to_paper,
            H_paper_to_image=H_paper_to_image,
            used_marker_ids=used_marker_ids,
            image_points=image_points_array,
            paper_points=paper_points_array,
        )

        self.last_good_result = result

        return result

    def get_current_result(self) -> HomographyResult | None:
        return self.last_good_result

    @staticmethod
    def image_to_paper_point(
        x: float,
        y: float,
        H_image_to_paper: np.ndarray,
    ) -> tuple[float, float]:
        point = np.array([[[x, y]]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(point, H_image_to_paper)
        return float(mapped[0, 0, 0]), float(mapped[0, 0, 1])

    @staticmethod
    def paper_to_image_point(
        x: float,
        y: float,
        H_paper_to_image: np.ndarray,
    ) -> tuple[float, float]:
        point = np.array([[[x, y]]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(point, H_paper_to_image)
        return float(mapped[0, 0, 0]), float(mapped[0, 0, 1])

    def draw_paper_axes(
        self,
        image: np.ndarray,
        homography: HomographyResult,
        board_width_mm: float,
        board_height_mm: float,
    ) -> np.ndarray:
        output = image.copy()

        paper_corners = [
            (0.0, 0.0),
            (board_width_mm, 0.0),
            (board_width_mm, board_height_mm),
            (0.0, board_height_mm),
        ]

        image_corners = [
            self.paper_to_image_point(x, y, homography.H_paper_to_image)
            for x, y in paper_corners
        ]

        points = np.array(image_corners, dtype=np.int32).reshape(-1, 1, 2)

        cv2.polylines(
            output,
            [points],
            isClosed=True,
            color=(0, 255, 0),
            thickness=2,
        )

        return output

    @staticmethod
    def homography_to_dict(result: HomographyResult | None) -> dict[str, Any]:
        if result is None:
            return {
                "available": False,
            }

        return {
            "available": True,
            "used_marker_ids": result.used_marker_ids,
            "image_points": result.image_points.tolist(),
            "paper_points": result.paper_points.tolist(),
            "H_image_to_paper": result.H_image_to_paper.tolist(),
            "H_paper_to_image": result.H_paper_to_image.tolist(),
        }