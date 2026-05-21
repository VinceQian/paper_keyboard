from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from core.layout import KeyboardLayout
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

    This version follows the older stable prototype behavior:

    - Use marker corner points, not marker center points.
    - One marker can mathematically produce a homography.
    - But by default, only update last_good_result when at least 2 markers are visible.
    - If not enough markers are visible, keep using last_good_result.
    """

    def __init__(
        self,
        marker_specs: dict[int, dict[str, float]],
        min_markers_to_update: int = 2,
        ransac_reproj_threshold: float = 3.0,
    ):
        self.marker_specs = marker_specs
        self.min_markers_to_update = min_markers_to_update
        self.ransac_reproj_threshold = ransac_reproj_threshold

        self.last_good_result: HomographyResult | None = None
        self.last_used_marker_count = 0
        self.last_updated = False

    @classmethod
    def from_layout(
        cls,
        layout: KeyboardLayout,
        min_markers_to_update: int = 2,
        ransac_reproj_threshold: float = 3.0,
    ) -> "CoordinateMapper":
        marker_specs: dict[int, dict[str, float]] = {}

        for marker in layout.markers:
            marker_id = int(marker["id"])

            # Support both old layout field "size" and new field "size_mm".
            if "size_mm" in marker:
                size = float(marker["size_mm"])
            elif "size" in marker:
                size = float(marker["size"])
            else:
                raise ValueError(f"Marker {marker_id} is missing size_mm or size.")

            marker_specs[marker_id] = {
                "x": float(marker["x"]),
                "y": float(marker["y"]),
                "size": size,
            }

        if len(marker_specs) == 0:
            raise ValueError(f"Layout {layout.layout_id} has no markers.")

        return cls(
            marker_specs=marker_specs,
            min_markers_to_update=min_markers_to_update,
            ransac_reproj_threshold=ransac_reproj_threshold,
        )

    def compute_candidate_from_markers(
        self,
        detection: ArucoDetectionResult,
    ) -> tuple[HomographyResult | None, int]:
        """
        Compute a candidate homography from currently visible markers.

        This function does not update last_good_result directly.
        It only computes the candidate H and returns how many known markers were used.
        """
        image_points: list[np.ndarray] = []
        paper_points: list[np.ndarray] = []
        used_marker_ids: list[int] = []

        for marker_id in detection.marker_ids:
            if marker_id not in self.marker_specs:
                continue

            image_corners = detection.corners_by_id[marker_id].astype(np.float32)
            paper_corners = self._get_marker_paper_corners(marker_id)

            image_points.append(image_corners)
            paper_points.append(paper_corners)
            used_marker_ids.append(marker_id)

        used_marker_count = len(used_marker_ids)

        if used_marker_count == 0:
            return None, 0

        image_points_array = np.concatenate(image_points, axis=0).astype(np.float32)
        paper_points_array = np.concatenate(paper_points, axis=0).astype(np.float32)

        if len(image_points_array) < 4:
            return None, used_marker_count

        H_image_to_paper, _ = cv2.findHomography(
            image_points_array,
            paper_points_array,
            method=cv2.RANSAC,
            ransacReprojThreshold=self.ransac_reproj_threshold,
        )

        if H_image_to_paper is None:
            return None, used_marker_count

        H_paper_to_image = np.linalg.inv(H_image_to_paper)

        result = HomographyResult(
            H_image_to_paper=H_image_to_paper,
            H_paper_to_image=H_paper_to_image,
            used_marker_ids=used_marker_ids,
            image_points=image_points_array,
            paper_points=paper_points_array,
        )

        return result, used_marker_count

    def update_from_markers(
        self,
        detection: ArucoDetectionResult,
    ) -> tuple[HomographyResult | None, int, bool]:
        """
        Update calibration only when enough markers are visible.

        Returns:
            current_result:
                New result if updated, otherwise last_good_result.
            visible_marker_count:
                How many known markers were visible this frame.
            updated:
                Whether last_good_result was updated this frame.
        """
        candidate_result, marker_count = self.compute_candidate_from_markers(detection)

        self.last_updated = False

        if (
            candidate_result is not None
            and marker_count >= self.min_markers_to_update
        ):
            self.last_good_result = candidate_result
            self.last_used_marker_count = marker_count
            self.last_updated = True

        return self.last_good_result, marker_count, self.last_updated

    def _get_marker_paper_corners(self, marker_id: int) -> np.ndarray:
        marker = self.marker_specs[marker_id]

        x = float(marker["x"])
        y = float(marker["y"])
        size = float(marker["size"])

        # OpenCV ArUco corner order:
        # top-left, top-right, bottom-right, bottom-left
        return np.array(
            [
                [x, y],
                [x + size, y],
                [x + size, y + size],
                [x, y + size],
            ],
            dtype=np.float32,
        )

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

    def draw_paper_border(
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
            color=(255, 255, 255),
            thickness=2,
        )

        return output

    def draw_layout_keys(
        self,
        image: np.ndarray,
        homography: HomographyResult,
        layout: KeyboardLayout,
        current_key_label: str | None = None,
    ) -> np.ndarray:
        output = image.copy()

        for key in layout.keys:
            x = float(key["x"])
            y = float(key["y"])
            w = float(key["w"])
            h = float(key["h"])

            paper_corners = [
                (x, y),
                (x + w, y),
                (x + w, y + h),
                (x, y + h),
            ]

            image_corners = [
                self.paper_to_image_point(px, py, homography.H_paper_to_image)
                for px, py in paper_corners
            ]

            points = np.array(image_corners, dtype=np.int32).reshape(-1, 1, 2)

            if str(key["label"]) == current_key_label:
                color = (0, 255, 0)
                thickness = 4
            else:
                color = (255, 255, 255)
                thickness = 2

            cv2.polylines(
                output,
                [points],
                isClosed=True,
                color=color,
                thickness=thickness,
            )

            center_paper_x = x + w / 2.0
            center_paper_y = y + h / 2.0

            center_img_x, center_img_y = self.paper_to_image_point(
                center_paper_x,
                center_paper_y,
                homography.H_paper_to_image,
            )

            cv2.putText(
                output,
                str(key["label"]),
                (int(center_img_x) - 10, int(center_img_y) + 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
                cv2.LINE_AA,
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