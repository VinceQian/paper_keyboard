import cv2
import mediapipe as mp


class MediaPipeHandSource:
    """
    使用 MediaPipe Hands 识别两只手，并提取十个指尖位置。

    这个类只负责：
    1. 识别手
    2. 提取指尖图像坐标
    3. 给每个指尖分配 finger_id
    4. 画手骨架和指尖调试信息

    它不负责：
    1. 纸面坐标转换
    2. 按键判断
    3. 输入确认
    4. 文本保存

    finger_id 规则：

    右手：
    0 = 拇指
    1 = 食指
    2 = 中指
    3 = 无名指
    4 = 小指

    左手：
    5 = 拇指
    6 = 食指
    7 = 中指
    8 = 无名指
    9 = 小指
    """

    def __init__(self, swap_hands=False):
        """
        参数：
            swap_hands:
                如果发现左右手编号反了，就改成 True。

                单独测试时，如果先用 cv2.flip(image, 1) 镜像画面，
                通常可以设为 False。

                正式主程序中如果不镜像原始画面，
                需要根据实际测试结果决定 True / False。
        """
        self.swap_hands = swap_hands

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

        self.fingertip_landmarks = {
            "thumb": 4,
            "index": 8,
            "middle": 12,
            "ring": 16,
            "pinky": 20
        }

        self.right_hand_ids = {
            "thumb": 0,
            "index": 1,
            "middle": 2,
            "ring": 3,
            "pinky": 4
        }

        self.left_hand_ids = {
            "thumb": 5,
            "index": 6,
            "middle": 7,
            "ring": 8,
            "pinky": 9
        }

    def fix_hand_name(self, hand_name):
        """
        修正 MediaPipe 输出的左右手名称。

        如果 swap_hands=True：
            Left  -> Right
            Right -> Left
        """
        if not self.swap_hands:
            return hand_name

        if hand_name == "Left":
            return "Right"

        if hand_name == "Right":
            return "Left"

        return hand_name

    def get_finger_id(self, hand_name, finger_name):
        """根据手和手指名称返回 finger_id。"""
        if hand_name == "Right":
            return self.right_hand_ids[finger_name]

        if hand_name == "Left":
            return self.left_hand_ids[finger_name]

        return -1

    def process_image(self, image):
        """
        识别一帧图像中的双手和指尖。

        参数：
            image:
                OpenCV 读取到的 BGR 图像。

        返回：
            result_data:
                {
                    "hands": [...],
                    "fingertips": [...]
                }

            mediapipe_result:
                MediaPipe 原始结果，主要用于画手骨架。
        """
        image_height, image_width, channels = image.shape

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mediapipe_result = self.hands.process(rgb_image)

        result_data = {
            "hands": [],
            "fingertips": []
        }

        if not mediapipe_result.multi_hand_landmarks:
            return result_data, mediapipe_result

        hand_landmarks_list = mediapipe_result.multi_hand_landmarks
        handedness_list = mediapipe_result.multi_handedness

        for hand_index, hand_landmarks in enumerate(hand_landmarks_list):
            handedness = handedness_list[hand_index]

            raw_hand_name = handedness.classification[0].label
            hand_name = self.fix_hand_name(raw_hand_name)
            hand_score = handedness.classification[0].score

            hand_data = {
                "hand_index": hand_index,
                "hand": hand_name,
                "raw_hand": raw_hand_name,
                "score": hand_score
            }

            result_data["hands"].append(hand_data)

            for finger_name, landmark_id in self.fingertip_landmarks.items():
                landmark = hand_landmarks.landmark[landmark_id]

                image_x = int(landmark.x * image_width)
                image_y = int(landmark.y * image_height)

                finger_id = self.get_finger_id(hand_name, finger_name)

                fingertip = {
                    "finger_id": finger_id,
                    "hand": hand_name,
                    "raw_hand": raw_hand_name,
                    "finger": finger_name,
                    "landmark_id": landmark_id,
                    "image_x": image_x,
                    "image_y": image_y
                }

                result_data["fingertips"].append(fingertip)

        return result_data, mediapipe_result

    def draw_debug(self, image, result_data, mediapipe_result):
        """
        在图像上画出调试信息。

        显示内容：
        1. MediaPipe 手骨架
        2. 所有指尖点
        3. 每个指尖的 finger_id
        4. 右手食指 finger_id=1 会被特别标记
        """
        debug_image = image.copy()

        if mediapipe_result.multi_hand_landmarks:
            for hand_landmarks in mediapipe_result.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    debug_image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

        for fingertip in result_data["fingertips"]:
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
                debug_image,
                (image_x, image_y),
                radius,
                color,
                -1
            )

            cv2.putText(
                debug_image,
                str(finger_id),
                (image_x + 8, image_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                thickness
            )

        return debug_image

    def close(self):
        """释放 MediaPipe 资源。"""
        self.hands.close()


def main():
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("摄像头打开失败")
        return

    # 单独测试时镜像画面，让它像照镜子一样显示。
    # 如果发现左右手编号反了，可以把 swap_hands 改成 True。
    hand_source = MediaPipeHandSource(swap_hands=False)

    print("MediaPipe 双手识别测试开始")
    print("画面已镜像显示")
    print("finger_id 规则：")
    print("右手 0-4：拇指、食指、中指、无名指、小指")
    print("左手 5-9：拇指、食指、中指、无名指、小指")
    print("绿色点：右手食指 finger_id = 1")
    print("蓝色点：其他指尖")
    print("按 q 退出")

    try:
        while True:
            success, image = cap.read()

            if not success:
                print("读取摄像头失败")
                break

            # 这里只在单独测试 MediaPipe 时镜像画面。
            # 正式主程序里不要随便镜像原始画面，否则会影响 ArUco 坐标映射。
            image = cv2.flip(image, 1)

            result_data, mediapipe_result = hand_source.process_image(image)
            debug_image = hand_source.draw_debug(
                image,
                result_data,
                mediapipe_result
            )

            cv2.imshow("MediaPipe Hand Test", debug_image)

            key = cv2.waitKey(1)

            if key == ord("q"):
                break

    finally:
        hand_source.close()
        cap.release()
        cv2.destroyAllWindows()

    print("MediaPipe 双手识别测试结束")


if __name__ == "__main__":
    main()