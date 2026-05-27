from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class HandTrackingResult:
    raw_result: object
    fingers: list[dict]
    index_tip_px: tuple[int, int] | None


class HandTracker:
    """
    MediaPipe hand tracker wrapper.

    Current prototype only uses index fingertip.
    Later we can expand it to multiple fingers.
    """

    def __init__(
        self,
        model_path: str | Path,
        num_hands: int = 1,
        min_hand_detection_confidence: float = 0.6,
        min_hand_presence_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ):
        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Hand landmark model not found: {model_path}"
            )

        base_options = python.BaseOptions(model_asset_path=str(model_path))

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.landmarker = vision.HandLandmarker.create_from_options(options)

    def detect(
        self,
        frame_bgr: np.ndarray,
        timestamp_ms: int,
    ) -> HandTrackingResult:
        height, width, _ = frame_bgr.shape

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb = np.ascontiguousarray(frame_rgb)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb,
        )

        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        fingers: list[dict] = []
        index_tip_px = None

        if not result.hand_landmarks:
            return HandTrackingResult(
                raw_result=result,
                fingers=fingers,
                index_tip_px=index_tip_px,
            )

        hand_landmarks = result.hand_landmarks[0]
        index_tip = hand_landmarks[8]

        tip_x_px = int(index_tip.x * width)
        tip_y_px = int(index_tip.y * height)
        index_tip_px = (tip_x_px, tip_y_px)

        finger_id = "right_index"

        if result.handedness:
            handedness = result.handedness[0][0]
            hand_label = handedness.category_name.lower()
            finger_id = f"{hand_label}_index"

        fingers.append(
            {
                "id": finger_id,
                "image_x": tip_x_px,
                "image_y": tip_y_px,
                "confidence": 1.0,
            }
        )

        return HandTrackingResult(
            raw_result=result,
            fingers=fingers,
            index_tip_px=index_tip_px,
        )

    def draw(
        self,
        frame: np.ndarray,
        result: HandTrackingResult,
    ) -> None:
        raw_result = result.raw_result

        if not raw_result.hand_landmarks:
            return

        height, width, _ = frame.shape
        hand_landmarks = raw_result.hand_landmarks[0]

        for idx, landmark in enumerate(hand_landmarks):
            x = int(landmark.x * width)
            y = int(landmark.y * height)

            if idx == 8:
                cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
            else:
                cv2.circle(frame, (x, y), 3, (255, 0, 0), -1)

        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17),
        ]

        for a, b in connections:
            ax = int(hand_landmarks[a].x * width)
            ay = int(hand_landmarks[a].y * height)
            bx = int(hand_landmarks[b].x * width)
            by = int(hand_landmarks[b].y * height)

            cv2.line(
                frame,
                (ax, ay),
                (bx, by),
                (255, 255, 255),
                2,
            )

    def close(self) -> None:
        self.landmarker.close()