class VisionFrameBuilder:
    """
    把视觉识别结果整理成统一 frame 格式。

    输入：
        1. 摄像头图像
        2. PaperMapper
        3. MediaPipeHandSource

    输出：
        frame:
        {
            "frame_id": 1,
            "t": 0.033,
            "fingers": [
                {
                    "finger_id": 1,
                    "x": 132.4,
                    "y": 78.6
                }
            ],
            "tap": {
                "candidate": 1
            }
        }

    注意：
        frame 里只保存纸面坐标 x / y。
        image_x / image_y 只作为调试信息，不进入 frame。
    """

    def __init__(self, paper_mapper, hand_source):
        self.paper_mapper = paper_mapper
        self.hand_source = hand_source

    def build_frame(self, image, frame_id, t):
        """
        根据当前摄像头画面生成一帧统一 frame。

        返回：
            frame:
                项目统一 frame 数据。

            debug_data:
                调试用数据，给 visual_overlay 画画面用。
                这些数据不应该保存进 session JSON。
        """
        homography, corners, ids = self.paper_mapper.get_homography(image)
        hand_data, mediapipe_result = self.hand_source.process_image(image)

        fingers = []
        candidate = -1

        if homography is not None:
            fingers = self.build_fingers(hand_data, homography)
            candidate = self.find_candidate(fingers)

        frame = {
            "frame_id": frame_id,
            "t": t,
            "fingers": fingers,
            "tap": {
                "candidate": candidate
            }
        }

        debug_data = {
            "homography": homography,
            "corners": corners,
            "ids": ids,
            "hand_data": hand_data,
            "mediapipe_result": mediapipe_result
        }

        return frame, debug_data

    def build_fingers(self, hand_data, homography):
        """
        把所有 MediaPipe 指尖图像坐标转换成纸面坐标。

        只输出：
            finger_id
            x
            y
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

    def find_candidate(self, fingers):
        """
        当前基础版只把右手食指作为 candidate。

        finger_id = 1 表示右手食指。

        如果这一帧检测到了右手食指：
            candidate = 1

        如果没有检测到：
            candidate = -1
        """
        for finger in fingers:
            if finger["finger_id"] == 1:
                return 1

        return -1


def main():
    import cv2
    import time

    from components.paper_mapper import PaperMapper
    from input_sources.mediapipe_hand_source import MediaPipeHandSource

    layout_path = "data/layouts/keyboard_number_v1.json"

    paper_mapper = PaperMapper(layout_path)
    hand_source = MediaPipeHandSource(swap_hands=True)
    frame_builder = VisionFrameBuilder(paper_mapper, hand_source)

    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("摄像头打开失败")
        return

    start_time = time.time()
    frame_id = 1

    print("VisionFrameBuilder 测试开始")
    print("请把纸面键盘放到摄像头下")
    print("按 q 退出")

    while True:
        success, image = cap.read()

        if not success:
            print("读取摄像头失败")
            break

        t = time.time() - start_time
        frame, debug_data = frame_builder.build_frame(image, frame_id, t)

        print(frame)

        debug_image = paper_mapper.draw_debug(
            image,
            debug_data["corners"],
            debug_data["ids"],
            debug_data["homography"]
        )

        debug_image = hand_source.draw_debug(
            debug_image,
            debug_data["hand_data"],
            debug_data["mediapipe_result"]
        )

        cv2.imshow("Vision Frame Builder Test", debug_image)

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

        frame_id += 1

    hand_source.close()
    cap.release()
    cv2.destroyAllWindows()

    print("VisionFrameBuilder 测试结束")


if __name__ == "__main__":
    main()