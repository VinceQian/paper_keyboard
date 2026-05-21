from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass
class ArucoDetectionResult:
    marker_ids: list[int]
    corners_by_id: dict[int, np.ndarray]
    rejected_count: int

    @property
    def count(self) -> int:
        return len(self.marker_ids)


class ArucoTracker:
    """
    Detect ArUco markers from a camera frame.

    This module only detects markers.
    Homography and coordinate mapping are handled by coordinate_mapper.py.
    """

    def __init__(
        self,
        dictionary_name: str = "DICT_4X4_50",
    ):
        self.dictionary_name = dictionary_name
        self.dictionary = self._get_dictionary(dictionary_name)
        self.parameters = cv2.aruco.DetectorParameters()

        # Match the older stable prototype.
        # This improves marker corner accuracy.
        if hasattr(cv2.aruco, "CORNER_REFINE_SUBPIX"):
            self.parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

        if hasattr(cv2.aruco, "ArucoDetector"):
            self.detector = cv2.aruco.ArucoDetector(
                self.dictionary,
                self.parameters,
            )
        else:
            self.detector = None

    def detect(self, image: np.ndarray) -> ArucoDetectionResult:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if self.detector is not None:
            corners, ids, rejected = self.detector.detectMarkers(gray)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray,
                self.dictionary,
                parameters=self.parameters,
            )

        marker_ids: list[int] = []
        corners_by_id: dict[int, np.ndarray] = {}

        if ids is not None:
            flat_ids = ids.flatten()

            for marker_id, marker_corners in zip(flat_ids, corners):
                marker_id_int = int(marker_id)
                marker_ids.append(marker_id_int)

                # marker_corners shape is usually (1, 4, 2).
                corners_by_id[marker_id_int] = marker_corners.reshape(4, 2)

        rejected_count = 0 if rejected is None else len(rejected)

        return ArucoDetectionResult(
            marker_ids=marker_ids,
            corners_by_id=corners_by_id,
            rejected_count=rejected_count,
        )

    def draw(
        self,
        image: np.ndarray,
        result: ArucoDetectionResult,
    ) -> np.ndarray:
        output = image.copy()

        if result.count == 0:
            return output

        corners = []
        ids = []

        for marker_id in result.marker_ids:
            corners.append(result.corners_by_id[marker_id].reshape(1, 4, 2))
            ids.append([marker_id])

        ids_array = np.array(ids, dtype=np.int32)

        cv2.aruco.drawDetectedMarkers(output, corners, ids_array)

        return output

    @staticmethod
    def _get_dictionary(dictionary_name: str):
        if not hasattr(cv2.aruco, dictionary_name):
            available = [
                name
                for name in dir(cv2.aruco)
                if name.startswith("DICT_")
            ]

            raise ValueError(
                f"Unknown ArUco dictionary: {dictionary_name}. "
                f"Available examples: {available[:10]}"
            )

        dictionary_id = getattr(cv2.aruco, dictionary_name)
        return cv2.aruco.getPredefinedDictionary(dictionary_id)

    def to_dict(self, result: ArucoDetectionResult) -> dict[str, Any]:
        return {
            "dictionary_name": self.dictionary_name,
            "marker_ids": result.marker_ids,
            "count": result.count,
            "rejected_count": result.rejected_count,
        }