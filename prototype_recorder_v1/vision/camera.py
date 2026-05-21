from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass
class CameraFrame:
    frame_id: int
    timestamp: float
    image: np.ndarray


class CameraSource:
    """
    Thin wrapper around cv2.VideoCapture.

    Responsibilities:
    - open camera
    - read frames
    - attach frame_id and timestamp
    - release camera safely
    """

    def __init__(
        self,
        camera_index: int = 0,
        width: int | None = 1280,
        height: int | None = 720,
        fps: int | None = 30,
        flip_horizontal: bool = False,
    ):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.flip_horizontal = flip_horizontal

        self.cap: cv2.VideoCapture | None = None
        self.frame_id = 0
        self.start_time = time.perf_counter()

    def open(self) -> None:
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {self.camera_index}.")

        if self.width is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

        if self.height is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if self.fps is not None:
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        self.frame_id = 0
        self.start_time = time.perf_counter()

    def read(self) -> CameraFrame | None:
        if self.cap is None:
            raise RuntimeError("Camera is not opened. Call open() first.")

        ok, image = self.cap.read()

        if not ok or image is None:
            return None

        if self.flip_horizontal:
            image = cv2.flip(image, 1)

        self.frame_id += 1
        timestamp = time.perf_counter() - self.start_time

        return CameraFrame(
            frame_id=self.frame_id,
            timestamp=timestamp,
            image=image,
        )

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def get_info(self) -> dict[str, Any]:
        if self.cap is None:
            return {
                "camera_index": self.camera_index,
                "opened": False,
            }

        return {
            "camera_index": self.camera_index,
            "opened": self.cap.isOpened(),
            "width": self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            "height": self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
        }