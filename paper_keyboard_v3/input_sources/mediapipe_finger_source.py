import cv2
import mediapipe as mp


class MediaPipeFingerSource:
    """
    使用 MediaPipe Hands 识别食指指尖位置。

    当前基础版只处理：
    1. 单只手
    2. 单个食指指尖
    3. 返回图像坐标 image_x / image_y

    注意：
    这里得到的是摄像头图像坐标，不是纸面坐标。
    """

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

    def get_index_finger_tip(self, image):
        """
        识别食指指尖位置。

        参数：
            image: OpenCV 读取到的 BGR 图像

        返回：
            如果识别到食指指尖，返回：
            {
                "finger_id": 1,
                "image_x": 320,
                "image_y": 240
            }

            如果没有识别到，返回 None。
        """
        image_height, image_width, channels = image.shape

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_image)

        if not result.multi_hand_landmarks:
            return None

        hand_landmarks = result.multi_hand_landmarks[0]

        # MediaPipe Hands 中，8 号点是食指指尖
        index_tip = hand_landmarks.landmark[8]

        image_x = int(index_tip.x * image_width)
        image_y = int(index_tip.y * image_height)

        finger = {
            "finger_id": 1,
            "image_x": image_x,
            "image_y": image_y
        }

        return finger

    def draw_debug(self, image):
        """
        在图像上画出手部关键点和食指指尖。

        返回：
            debug_image: 画好调试信息的图像
            finger: 食指指尖信息，如果没有识别到则是 None
        """
        debug_image = image.copy()

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_image)

        finger = None

        if result.multi_hand_landmarks:
            image_height, image_width, channels = image.shape
            hand_landmarks = result.multi_hand_landmarks[0]

            self.mp_draw.draw_landmarks(
                debug_image,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS
            )

            index_tip = hand_landmarks.landmark[8]

            image_x = int(index_tip.x * image_width)
            image_y = int(index_tip.y * image_height)

            finger = {
                "finger_id": 1,
                "image_x": image_x,
                "image_y": image_y
            }

            cv2.circle(
                debug_image,
                (image_x, image_y),
                10,
                (0, 255, 0),
                -1
            )

            cv2.putText(
                debug_image,
                f"index tip: ({image_x}, {image_y})",
                (image_x + 10, image_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        return debug_image, finger

    def close(self):
        """释放 MediaPipe 资源。"""
        self.hands.close()


def main():
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("摄像头打开失败")
        return

    finger_source = MediaPipeFingerSource()

    print("MediaPipe 食指识别测试开始")
    print("按 q 退出")

    while True:
        success, image = cap.read()

        if not success:
            print("读取摄像头失败")
            break

        debug_image, finger = finger_source.draw_debug(image)

        if finger is not None:
            print(f"食指指尖图像坐标：({finger['image_x']}, {finger['image_y']})")

        cv2.imshow("MediaPipe Finger Test", debug_image)

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

    finger_source.close()
    cap.release()
    cv2.destroyAllWindows()

    print("MediaPipe 食指识别测试结束")


if __name__ == "__main__":
    main()