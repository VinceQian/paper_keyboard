class FrameBuilder:
    """
    汇总多个输入源，生成项目统一 frame。

    当前依赖组件：
    1. PaperMapper：识别纸面，并提供图像坐标到纸面坐标的转换
    2. MediaPipeHandSource：识别手和指尖
    3. tap_source：提供 tap.candidate

    当前 tap_source 是 AudioSource：
        get_candidate() 返回 -1 或 1

    未来 tap_source 可以换成指套、手套、串口按钮等：
        get_candidate() 可能返回 -1 到 9

    FrameBuilder 不负责：
    1. 判断哪个键被按下
    2. 判断是否产生输入
    3. 保存文本
    4. 显示画面

    它只负责把 source 数据整理成统一 frame。
    """

    def __init__(self, paper_mapper, hand_source, tap_source):
        self.paper_mapper = paper_mapper
        self.hand_source = hand_source
        self.tap_source = tap_source

    def build_frame(self, image, frame_id, t):
        """
        根据当前摄像头画面生成一帧统一 frame。

        返回：
            frame:
                项目核心 frame，格式保持最小化。

            visual_data:
                给显示组件使用的临时视觉数据。
                不保存进 session。
        """
        homography, corners, ids = self.paper_mapper.get_homography(image)
        hand_data, mediapipe_result = self.hand_source.process_image(image)

        fingers = []

        if homography is not None:
            fingers = self.build_fingers(hand_data, homography)

        candidate = self.tap_source.get_candidate()

        frame = {
            "frame_id": frame_id,
            "t": t,
            "fingers": fingers,
            "tap": {
                "candidate": candidate
            }
        }

        visual_data = {
            "homography": homography,
            "corners": corners,
            "ids": ids,
            "hand_data": hand_data,
            "mediapipe_result": mediapipe_result
        }

        return frame, visual_data

    def build_fingers(self, hand_data, homography):
        """
        把 MediaPipe 指尖图像坐标转换成纸面坐标。

        frame 里只保存：
            finger_id
            x
            y

        不保存：
            image_x
            image_y
            hand
            finger
            key_id
        """
        fingers = []

        for fingertip in hand_data["fingertips"]:
            image_x = fingertip["image_x"]
            image_y = fingertip["image_y"]

            paper_x, paper_y = self.paper_mapper.image_to_paper(
                image_x,
                image_y,
                homography
            )

            finger = {
                "finger_id": fingertip["finger_id"],
                "x": float(paper_x),
                "y": float(paper_y)
            }

            fingers.append(finger)

        return fingers


def main():
    print("FrameBuilder 是 main.py 的依赖组件，从 app.py 运行具体程序。")


if __name__ == "__main__":
    main()