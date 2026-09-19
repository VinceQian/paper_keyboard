import json

import cv2
import numpy as np


class PaperMapper:
    def __init__(self, layout_path):
        # 读取 Step 3 里写好的 layout JSON。
        # 这里面记录了纸张大小、marker 的位置、按键的位置。
        with open(layout_path, "r", encoding="utf-8") as f:
            self.layout = json.load(f)

        # 保存纸张大小。
        # 后面画纸面边框时会用到 board["w"] 和 board["h"]。
        self.board = self.layout["board"]

        # 把 marker 列表整理成 dict，方便根据 marker id 查找。
        # 原来的格式是：
        # [
        #     {"id": 0, "x": 5, ...},
        #     {"id": 1, "x": 270, ...}
        # ]
        #
        # 整理后可以直接：
        # self.marker_map[0]
        # self.marker_map[1]
        self.marker_map = {}

        for marker in self.layout["markers"]:
            self.marker_map[marker["id"]] = marker

        # 选择 ArUco 字典。
        # Step 3 生成 marker 时用的是 DICT_4X4_50，
        # 这里识别时也必须用同一个字典。
        self.dictionary = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_4X4_50
        )

        # 创建 ArUco 检测参数。
        # 不同 OpenCV 版本的写法略有区别，所以这里做了兼容处理。
        if hasattr(cv2.aruco, "DetectorParameters"):
            self.parameters = cv2.aruco.DetectorParameters()
        else:
            self.parameters = cv2.aruco.DetectorParameters_create()

        # 新版 OpenCV 可以创建 ArucoDetector 对象。
        # 旧版 OpenCV 没有 ArucoDetector，就在 detect_markers 里用旧写法。
        if hasattr(cv2.aruco, "ArucoDetector"):
            self.detector = cv2.aruco.ArucoDetector(
                self.dictionary,
                self.parameters
            )
        else:
            self.detector = None

    def detect_markers(self, image):
        # ArUco marker 是黑白图案，转成灰度图就够识别了。
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 检测画面里的 marker。
        # corners：每个 marker 在图像里的四个角点
        # ids：每个 marker 的编号
        if self.detector is not None:
            corners, ids, rejected = self.detector.detectMarkers(gray)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray,
                self.dictionary,
                parameters=self.parameters
            )

        return corners, ids

    def get_marker_paper_corners(self, marker):
        # marker 在 layout JSON 里只有左上角 x, y 和宽高 w, h。
        # 但算 homography 时需要四个角点。
        x = marker["x"]
        y = marker["y"]
        w = marker["w"]
        h = marker["h"]

        # 这里返回的是 marker 在纸面坐标里的四个角。
        # 顺序是：左上、右上、右下、左下。
        return [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

    def get_homography(self, image):
        # 先从摄像头画面里检测 ArUco marker。
        corners, ids = self.detect_markers(image)

        # 如果一个 marker 都没检测到，就没法建立纸面映射。
        if ids is None:
            return None, corners, ids

        # image_points 存 marker 在摄像头画面里的角点。
        # paper_points 存同一个 marker 在纸面 layout 里的角点。
        #
        # 这两个列表是一一对应的：
        # image_points[k] 这个画面点
        # 对应 paper_points[k] 这个纸面点
        image_points = []
        paper_points = []

        for i in range(len(ids)):
            marker_id = int(ids[i][0])

            # 如果摄像头识别到了一个 layout 里没有写的 marker，忽略它。
            if marker_id not in self.marker_map:
                continue

            # 从 layout 里找到这个 marker 在纸上的位置。
            marker = self.marker_map[marker_id]

            # detected_corners 是这个 marker 在摄像头画面里的四个角点。
            detected_corners = corners[i][0]

            # expected_corners 是这个 marker 在纸面 layout 里的四个角点。
            expected_corners = self.get_marker_paper_corners(marker)

            # 把四个角点加入对应列表。
            for j in range(4):
                image_points.append(detected_corners[j])
                paper_points.append(expected_corners[j])

        # 理论上一个 marker 有四个角点，已经够算 homography。
        # 但识别到更多 marker 时会更稳。
        if len(image_points) < 4:
            return None, corners, ids

        # OpenCV 需要 numpy 数组，并且类型用 float32。
        image_points = np.array(image_points, dtype=np.float32)
        paper_points = np.array(paper_points, dtype=np.float32)

        # 计算 homography。
        # 这里得到的是：图像坐标 -> 纸面坐标 的转换关系。
        homography, mask = cv2.findHomography(
            image_points,
            paper_points
        )

        return homography, corners, ids

    def image_to_paper(self, image_x, image_y, homography):
        # 把一个图像坐标点转换成纸面坐标点。
        # 后面 MediaPipe 得到指尖 image_x, image_y 后，就会调用这个函数。
        point = np.array(
            [[[float(image_x), float(image_y)]]],
            dtype=np.float32
        )

        paper_point = cv2.perspectiveTransform(point, homography)

        paper_x = paper_point[0][0][0]
        paper_y = paper_point[0][0][1]

        return paper_x, paper_y

    def paper_to_image(self, paper_x, paper_y, homography):
        # homography 是 图像坐标 -> 纸面坐标。
        # 如果想把纸面上的点画回摄像头画面，就需要反过来转换。
        inverse = np.linalg.inv(homography)

        point = np.array(
            [[[float(paper_x), float(paper_y)]]],
            dtype=np.float32
        )

        image_point = cv2.perspectiveTransform(point, inverse)

        image_x = image_point[0][0][0]
        image_y = image_point[0][0][1]

        return image_x, image_y

    def draw_detected_markers(self, image, corners, ids):
        # 把检测到的 ArUco marker 框出来。
        # 这只是调试显示，不影响后面的判断逻辑。
        if ids is None:
            return image

        cv2.aruco.drawDetectedMarkers(image, corners, ids)
        return image

    def draw_board_border(self, image, homography):
        # 取出纸张在 layout 里的四个角。
        board_w = self.board["w"]
        board_h = self.board["h"]

        paper_corners = [
            [0, 0],
            [board_w, 0],
            [board_w, board_h],
            [0, board_h]
        ]

        image_corners = []

        # 把纸面四个角转换回图像坐标，方便画到摄像头画面上。
        for paper_x, paper_y in paper_corners:
            image_x, image_y = self.paper_to_image(
                paper_x,
                paper_y,
                homography
            )

            image_corners.append([int(image_x), int(image_y)])

        # 用绿色线把纸张边框画出来。
        # 如果绿色边框能正确贴合纸面，说明坐标映射基本是对的。
        for i in range(4):
            p1 = image_corners[i]
            p2 = image_corners[(i + 1) % 4]

            cv2.line(
                image,
                (p1[0], p1[1]),
                (p2[0], p2[1]),
                (0, 255, 0),
                3
            )

        return image

    def draw_keys(self, image, homography):
        # 把 layout JSON 里的每个按键区域画回摄像头画面。
        for key in self.layout["keys"]:
            x = key["x"]
            y = key["y"]
            w = key["w"]
            h = key["h"]

            # 每个 key 在纸面坐标里也是一个矩形。
            paper_corners = [
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h]
            ]

            image_corners = []

            # 把 key 的四个纸面角点转换回图像坐标。
            for paper_x, paper_y in paper_corners:
                image_x, image_y = self.paper_to_image(
                    paper_x,
                    paper_y,
                    homography
                )

                image_corners.append([int(image_x), int(image_y)])

            # cv2.polylines 需要 numpy 数组格式的点。
            points = np.array(
                image_corners,
                dtype=np.int32
            )

            # 用蓝色线画出按键边框。
            cv2.polylines(
                image,
                [points],
                True,
                (255, 0, 0),
                2
            )

            # 在 key 的中心位置写上按键 id。
            center_paper_x = x + w / 2
            center_paper_y = y + h / 2

            center_image_x, center_image_y = self.paper_to_image(
                center_paper_x,
                center_paper_y,
                homography
            )

            cv2.putText(
                image,
                key["id"],
                (int(center_image_x) - 8, int(center_image_y) + 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )

        return image

    def draw_key_highlight(self, image, homography, key_id):
        # 如果当前没有 key，就不画高亮。
        if key_id is None:
            return image

        # 从 layout 里找到对应 id 的 key。
        target_key = None

        for key in self.layout["keys"]:
            if key["id"] == key_id:
                target_key = key
                break

        if target_key is None:
            return image

        x = target_key["x"]
        y = target_key["y"]
        w = target_key["w"]
        h = target_key["h"]

        # key 在纸面坐标里的四个角。
        paper_corners = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

        image_corners = []

        # 把 key 的四个角从纸面坐标转换回图像坐标。
        for paper_x, paper_y in paper_corners:
            image_x, image_y = self.paper_to_image(
                paper_x,
                paper_y,
                homography
            )

            image_corners.append([int(image_x), int(image_y)])

        points = np.array(
            image_corners,
            dtype=np.int32
        )

        # 用更粗的黄色边框高亮当前 key。
        cv2.polylines(
            image,
            [points],
            True,
            (0, 255, 255),
            5
        )

        return image