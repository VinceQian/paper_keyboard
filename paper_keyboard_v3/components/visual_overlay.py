import json

import cv2
import mediapipe as mp
import numpy as np


class VisualOverlay:
    """
    视觉显示组件。

    这个类只负责把调试信息画到摄像头画面上。

    它不负责：
    1. 识别纸面
    2. 识别手
    3. 生成 frame
    4. 判断输入
    5. 保存文本

    它只读取：
    1. layout
    2. frame
    3. debug_data
    4. current_key_id
    5. 当前 text
    """

    def __init__(self, layout_path):
        self.layout = self.load_layout(layout_path)
        self.board = self.layout["board"]
        self.keys = self.layout["keys"]

        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands

    def load_layout(self, layout_path):
        """读取 layout JSON 文件。"""
        with open(layout_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_marker_ids(self, ids):
        """
        从 OpenCV ArUco 返回的 ids 中整理 marker id 列表。

        ids 可能是 None，也可能是类似 [[0], [1], [2], [3]] 的数组。
        """
        if ids is None:
            return []

        marker_ids = []

        for marker_id in ids.flatten():
            marker_ids.append(int(marker_id))

        return marker_ids

    def paper_points_to_image_points(self, paper_points, homography):
        """
        把纸面坐标转换回图像坐标。

        参数：
            paper_points:
                [
                    [x1, y1],
                    [x2, y2],
                    ...
                ]

            homography:
                图像坐标 -> 纸面坐标 的矩阵

        返回：
            image_points:
                图像坐标点。
        """
        if homography is None:
            return None

        inverse_homography = np.linalg.inv(homography)

        points = np.array(
            [paper_points],
            dtype=np.float32
        )

        image_points = cv2.perspectiveTransform(
            points,
            inverse_homography
        )

        return image_points[0].astype(int)

    def get_key_corners(self, key):
        """得到一个按键在纸面坐标中的四个角点。"""
        x = key["x"]
        y = key["y"]
        w = key["w"]
        h = key["h"]

        corners = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

        return corners

    def draw_markers(self, image, corners, ids):
        """画出检测到的 ArUco marker。"""
        if ids is None:
            return

        cv2.aruco.drawDetectedMarkers(image, corners, ids)

    def draw_paper_border(self, image, homography):
        """画出整张纸面的边框。"""
        if homography is None:
            return

        board_w = self.board["w"]
        board_h = self.board["h"]

        paper_corners = [
            [0, 0],
            [board_w, 0],
            [board_w, board_h],
            [0, board_h]
        ]

        image_corners = self.paper_points_to_image_points(
            paper_corners,
            homography
        )

        if image_corners is None:
            return

        cv2.polylines(
            image,
            [image_corners],
            isClosed=True,
            color=(0, 255, 0),
            thickness=2
        )

    def draw_keys(self, image, homography, current_key_id):
        """
        画出 layout 中的所有按键。

        当前按键会用黄色高亮。
        其他按键用白色线条。
        """
        if homography is None:
            return

        for key in self.keys:
            key_id = key["id"]

            paper_corners = self.get_key_corners(key)

            image_corners = self.paper_points_to_image_points(
                paper_corners,
                homography
            )

            if image_corners is None:
                continue

            if key_id == current_key_id:
                color = (0, 255, 255)
                thickness = 3
            else:
                color = (255, 255, 255)
                thickness = 1

            cv2.polylines(
                image,
                [image_corners],
                isClosed=True,
                color=color,
                thickness=thickness
            )

            center_x = int(np.mean(image_corners[:, 0]))
            center_y = int(np.mean(image_corners[:, 1]))

            cv2.putText(
                image,
                key_id,
                (center_x - 8, center_y + 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )

    def draw_hands(self, image, mediapipe_result):
        """画出 MediaPipe 手部骨架。"""
        if not mediapipe_result.multi_hand_landmarks:
            return

        for hand_landmarks in mediapipe_result.multi_hand_landmarks:
            self.mp_draw.draw_landmarks(
                image,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS
            )

    def draw_fingertips(self, image, hand_data):
        """
        画出所有指尖点和 finger_id。

        finger_id = 1 是当前基础版关注的右手食指，用绿色大点。
        其他手指用蓝色小点。
        """
        fingertips = hand_data["fingertips"]

        for fingertip in fingertips:
            image_x = fingertip["image_x"]
            image_y = fingertip["image_y"]
            finger_id = fingertip["finger_id"]

            if finger_id == 1:
                color = (0, 255, 0)
                radius = 10
                thickness = 2
            else:
                color = (255, 0, 0)
                radius = 6
                thickness = 1

            cv2.circle(
                image,
                (image_x, image_y),
                radius,
                color,
                -1
            )

            cv2.putText(
                image,
                str(finger_id),
                (image_x + 8, image_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                thickness
            )

    def draw_status_background(self, image):
        """给左上角状态栏画一个半透明背景，避免文字看不清。"""
        overlay = image.copy()

        cv2.rectangle(
            overlay,
            (10, 10),
            (780, 170),
            (0, 0, 0),
            -1
        )

        alpha = 0.45

        cv2.addWeighted(
            overlay,
            alpha,
            image,
            1 - alpha,
            0,
            image
        )

    def draw_status_panel(self, image, frame, debug_data, current_key_id, text):
        """
        画左上角状态信息。

        注意：
        marker 数量、手数量、指尖数量都在这里临时计算，
        不要求 debug_data 额外提供这些字段。
        """
        homography = debug_data["homography"]
        ids = debug_data["ids"]
        hand_data = debug_data["hand_data"]

        paper_detected = homography is not None
        marker_ids = self.get_marker_ids(ids)
        hand_count = len(hand_data["hands"])
        fingertip_count = len(hand_data["fingertips"])
        candidate = frame["tap"]["candidate"]

        lines = [
            f"Paper: {paper_detected}   Markers: {marker_ids}",
            f"Hands: {hand_count}   Fingertips: {fingertip_count}",
            f"Candidate finger: {candidate}   Current key: {current_key_id}",
            f"Text: {text}",
            "tap: input    c: clear    q: quit"
        ]

        self.draw_status_background(image)

        x = 20
        y = 38
        line_gap = 30

        for i, line in enumerate(lines):
            cv2.putText(
                image,
                line,
                (x, y + i * line_gap),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

    def draw_all(self, image, frame, debug_data, current_key_id, text):
        """
        画出完整调试画面。

        参数：
            image:
                原始摄像头画面。

            frame:
                项目核心 frame。

            debug_data:
                临时调试数据，只要求包含：
                homography
                corners
                ids
                hand_data
                mediapipe_result

            current_key_id:
                当前候选手指所在的按键 id。

            text:
                当前已经输入的文本。
        """
        debug_image = image.copy()

        self.draw_markers(
            debug_image,
            debug_data["corners"],
            debug_data["ids"]
        )

        self.draw_paper_border(
            debug_image,
            debug_data["homography"]
        )

        self.draw_keys(
            debug_image,
            debug_data["homography"],
            current_key_id
        )

        self.draw_hands(
            debug_image,
            debug_data["mediapipe_result"]
        )

        self.draw_fingertips(
            debug_image,
            debug_data["hand_data"]
        )

        self.draw_status_panel(
            debug_image,
            frame,
            debug_data,
            current_key_id,
            text
        )

        return debug_image


def main():
    print("VisualOverlay 是显示组件，请从 app.py 进入 vision_demo 测试。")


if __name__ == "__main__":
    main()