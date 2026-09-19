import cv2
import mediapipe as mp


class MediaPipeHandSource:
    def __init__(self, max_num_hands=1):
        self.mp_hands = mp.solutions.hands  # 手部识别模块
        self.mp_draw = mp.solutions.drawing_utils  # 画图工具

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,  # 非静态图片
            max_num_hands=max_num_hands,  # 最多识别数量
            min_detection_confidence=0.6,  # 检测置信度
            min_tracking_confidence=0.6  # 追踪置信度
        )  # 创建 Hands 对象

    def process_image(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # OpenCV 是 BGR，MediaPipe 需要 RGB。
        result = self.hands.process(image_rgb)  # 识别

        hand_data = {
            "fingertips": []
        }

        if result.multi_hand_landmarks is None:
            return hand_data, result

        height, width, _ = image.shape

        hand_landmarks = result.multi_hand_landmarks[0]

        fingertip_ids = {
            0: 4,    # 拇指指尖
            1: 8,    # 食指指尖
            2: 12,   # 中指指尖
            3: 16,   # 无名指指尖
            4: 20    # 小指指尖
        }

        for finger_id, landmark_id in fingertip_ids.items():
            landmark = hand_landmarks.landmark[landmark_id]

            image_x = int(landmark.x * width)
            image_y = int(landmark.y * height)

            fingertip = {
                "finger_id": finger_id,
                "landmark_id": landmark_id,
                "image_x": image_x,
                "image_y": image_y
            }

            hand_data["fingertips"].append(fingertip)

        return hand_data, result

    def draw_hand(self, image, result):
        if result.multi_hand_landmarks is None:
            return image

        for hand_landmarks in result.multi_hand_landmarks:
            self.mp_draw.draw_landmarks(
                image,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS # 关键点间连线
            )

        return image

    def draw_fingertips(self, image, hand_data):
        # 把识别到的指尖画出来。
        for fingertip in hand_data["fingertips"]:
            finger_id = fingertip["finger_id"]
            x = fingertip["image_x"]
            y = fingertip["image_y"]

            cv2.circle(image, (x, y), 8, (0, 0, 255), -1)  # 在指尖画红点。

            cv2.putText(
                image,
                str(finger_id),
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        return image

    def close(self):
        self.hands.close() # 关闭 Hands 对象