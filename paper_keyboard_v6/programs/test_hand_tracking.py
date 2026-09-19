import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource


def main():
    camera = CameraSource(camera_id=0)
    hand_source = MediaPipeHandSource(max_num_hands=1)

    print("手部识别测试开始")
    print("按 q 退出")

    while True:
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        hand_data, result = hand_source.process_image(image)

        image = hand_source.draw_hand(image, result)
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - Hand Tracking Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("手部识别测试结束")


if __name__ == "__main__":
    main()