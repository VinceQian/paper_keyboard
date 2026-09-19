import time

import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource

from components.paper_mapper import PaperMapper
from components.frame_builder import FrameBuilder
from components.key_finder import KeyFinder
from components.frame_tools import get_finger_position_by_id


def get_current_key(frame, key_finder):
    # 这里先只看食指。
    # 我们项目里 finger_id = 1 表示食指。
    position = get_finger_position_by_id(frame, 1)

    if position is None:
        return None

    x, y = position

    # KeyFinder 根据纸面坐标判断这个点在哪个 key 里。
    key_id = key_finder.find_key(x, y)

    return key_id


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    camera = CameraSource(camera_id=0)
    hand_source = MediaPipeHandSource(max_num_hands=1)
    paper_mapper = PaperMapper(layout_path)
    key_finder = KeyFinder(layout_path)

    frame_builder = FrameBuilder(
        paper_mapper,
        hand_source
    )

    frame_id = 0
    start_time = time.time()

    print("单指按键识别测试开始")
    print("请把纸面键盘放到摄像头画面里")
    print("移动食指，观察当前 key 是否高亮")
    print("按 q 退出")
    print("按 p 打印当前 frame")

    while True:
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        t = time.time() - start_time

        frame, visual_data = frame_builder.build_frame(
            image,
            frame_id,
            t
        )

        homography = visual_data["homography"]
        corners = visual_data["corners"]
        ids = visual_data["ids"]
        hand_data = visual_data["hand_data"]
        mediapipe_result = visual_data["mediapipe_result"]

        current_key = get_current_key(frame, key_finder)

        image = paper_mapper.draw_detected_markers(image, corners, ids)

        if homography is not None:
            image = paper_mapper.draw_board_border(image, homography)
            image = paper_mapper.draw_keys(image, homography)
            image = paper_mapper.draw_key_highlight(
                image,
                homography,
                current_key
            )

            cv2.putText(
                image,
                "current key: " + str(current_key),
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 255),
                2
            )
        else:
            cv2.putText(
                image,
                "paper not detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2
            )

        image = hand_source.draw_hand(image, mediapipe_result)
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - Single Finger Mapping Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("p"):
            print(frame)
            print("current_key:", current_key)

        frame_id = frame_id + 1

    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("单指按键识别测试结束")


if __name__ == "__main__":
    main()