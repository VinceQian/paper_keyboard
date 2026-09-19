class FrameBuilder:
    def __init__(self, paper_mapper, hand_source, tap_source=None):
        self.paper_mapper = paper_mapper
        self.hand_source = hand_source
        self.tap_source = tap_source

    def build_frame(self, image, frame_id, t):
        # 1. 根据 ArUco marker 计算图像坐标到纸面坐标的转换关系
        homography, corners, ids = self.paper_mapper.get_homography(image)

        # 2. 用 MediaPipe 识别手和指尖
        hand_data, mediapipe_result = self.hand_source.process_image(image)

        # 3. 默认这一帧没有识别到纸面坐标里的手指
        fingers = {}

        # 4. 只有识别到纸面，才能把图像坐标转换成纸面坐标
        if homography is not None:
            fingers = self.build_fingers(hand_data, homography)

        # 5. 这一步还没有接声音/按钮，所以 candidate 默认是 -1
        candidate = -1

        # 6. 如果以后接了 AudioSource / SerialTapSource，就从 tap_source 读取 candidate
        if self.tap_source is not None:
            candidate = self.tap_source.get_candidate()

        # 7. 生成和线上 replay 一样格式的 frame
        frame = {
            "frame_id": frame_id,
            "t": t,
            "fingers": fingers,
            "tap": {
                "candidate": candidate
            }
        }

        # 8. visual_data 是给调试显示用的，不进入核心输入逻辑
        visual_data = {
            "homography": homography,
            "corners": corners,
            "ids": ids,
            "hand_data": hand_data,
            "mediapipe_result": mediapipe_result
        }

        return frame, visual_data

    def build_fingers(self, hand_data, homography):
        fingers = {}

        for fingertip in hand_data["fingertips"]:
            finger_id = fingertip["finger_id"]

            image_x = fingertip["image_x"]
            image_y = fingertip["image_y"]

            # 把摄像头画面里的指尖坐标转换成纸面 layout 坐标
            paper_x, paper_y = self.paper_mapper.image_to_paper(
                image_x,
                image_y,
                homography
            )

            # 注意：这里的 key 用字符串，是为了和 JSON 读出来的数据格式保持一致
            fingers[str(finger_id)] = {
                "x": float(paper_x),
                "y": float(paper_y)
            }

        return fingers