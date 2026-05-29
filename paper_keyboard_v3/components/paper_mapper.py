import json

import cv2
import numpy as np


class PaperMapper:
    """
    纸面坐标转换器。

    它负责：
    1. 从 layout 文件读取 board 和 markers
    2. 在摄像头画面中识别 ArUco marker
    3. 根据 marker 的图像角点和纸面角点计算 Homography
    4. 把图像坐标转换成纸面坐标

    它不负责：
    1. 识别手指
    2. 判断按键
    3. 判断输入
    4. 保存文本
    """

    def __init__(self, layout_path):
        self.layout_path = layout_path
        self.layout = self.load_layout(layout_path)

        self.board = self.layout["board"]
        self.markers = self.layout["markers"]

        self.board_width = self.board["w"]
        self.board_height = self.board["h"]

        self.marker_map = self.build_marker_map()

        self.dictionary = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_4X4_50
        )
        self.parameters = cv2.aruco.DetectorParameters()

    def load_layout(self, layout_path):
        """读取 layout JSON 文件。"""
        with open(layout_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def build_marker_map(self):
        """
        把 markers 列表转换成字典，方便根据 marker_id 查找 marker 信息。
        """
        marker_map = {}

        for marker in self.markers:
            marker_id = marker["id"]
            marker_map[marker_id] = marker

        return marker_map

    def get_marker_paper_corners(self, marker):
        """
        根据 layout 中的 marker 信息，得到它在纸面坐标系中的四个角点。

        顺序需要和 OpenCV ArUco 检测结果一致：
        左上、右上、右下、左下。
        """
        x = marker["x"]
        y = marker["y"]
        w = marker["w"]
        h = marker["h"]

        paper_corners = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

        return paper_corners

    def detect_markers(self, image):
        """
        识别画面中的 ArUco markers。

        返回：
            corners: 检测到的 marker 角点
            ids: 检测到的 marker id
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detector = cv2.aruco.ArucoDetector(
            self.dictionary,
            self.parameters
        )

        corners, ids, rejected = detector.detectMarkers(gray)

        return corners, ids

    def get_homography(self, image):
        """
        根据画面中的 ArUco marker 计算 Homography。

        返回：
            homography: 图像坐标 -> 纸面坐标 的转换矩阵
            corners: OpenCV 检测到的 marker 角点
            ids: OpenCV 检测到的 marker id
        """
        corners, ids = self.detect_markers(image)

        if ids is None:
            return None, corners, ids

        image_points = []
        paper_points = []

        ids = ids.flatten()

        for i, marker_id in enumerate(ids):
            marker_id = int(marker_id)

            if marker_id not in self.marker_map:
                continue

            image_corners = corners[i][0]
            marker = self.marker_map[marker_id]
            paper_corners = self.get_marker_paper_corners(marker)

            for j in range(4):
                image_points.append(image_corners[j])
                paper_points.append(paper_corners[j])

        if len(image_points) < 4:
            return None, corners, ids

        image_points = np.array(image_points, dtype=np.float32)
        paper_points = np.array(paper_points, dtype=np.float32)

        homography, status = cv2.findHomography(
            image_points,
            paper_points
        )

        return homography, corners, ids

    def image_to_paper(self, image_x, image_y, homography):
        """
        把图像坐标转换成纸面坐标。

        参数：
            image_x: 图像中的 x 坐标，单位是像素
            image_y: 图像中的 y 坐标，单位是像素
            homography: 图像坐标到纸面坐标的转换矩阵

        返回：
            paper_x: 纸面上的 x 坐标，单位和 layout 一致
            paper_y: 纸面上的 y 坐标，单位和 layout 一致
        """
        point = np.array([[[image_x, image_y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, homography)

        paper_x = transformed[0][0][0]
        paper_y = transformed[0][0][1]

        return paper_x, paper_y

    def draw_debug(self, image, corners, ids, homography):
        """
        在画面上画出 PaperMapper 的调试信息。

        包括：
        1. 检测到的 ArUco marker
        2. 识别到的纸面边框

        注意：
        正式主程序中的完整显示由 VisualOverlay 负责。
        这个函数主要用于单独测试 PaperMapper。
        """
        debug_image = image.copy()

        if ids is not None:
            cv2.aruco.drawDetectedMarkers(debug_image, corners, ids)

        if homography is not None:
            paper_corners = np.array(
                [
                    [
                        [0, 0],
                        [self.board_width, 0],
                        [self.board_width, self.board_height],
                        [0, self.board_height]
                    ]
                ],
                dtype=np.float32
            )

            inverse_homography = np.linalg.inv(homography)
            image_corners = cv2.perspectiveTransform(
                paper_corners,
                inverse_homography
            )
            image_corners = image_corners.astype(int)

            cv2.polylines(
                debug_image,
                image_corners,
                isClosed=True,
                color=(0, 255, 0),
                thickness=2
            )

        return debug_image


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    mapper = PaperMapper(layout_path)
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("摄像头打开失败")
        return

    print("PaperMapper 测试开始")
    print("请把生成好的纸面键盘放到摄像头下")
    print("按 q 退出")

    try:
        while True:
            success, image = cap.read()

            if not success:
                print("读取摄像头失败")
                break

            homography, corners, ids = mapper.get_homography(image)
            debug_image = mapper.draw_debug(
                image,
                corners,
                ids,
                homography
            )

            if homography is not None:
                cv2.putText(
                    debug_image,
                    "Paper detected",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
            else:
                cv2.putText(
                    debug_image,
                    "Need ArUco markers",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )

            cv2.imshow("Paper Mapper Test", debug_image)

            key = cv2.waitKey(1)

            if key == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print("PaperMapper 测试结束")


if __name__ == "__main__":
    main()