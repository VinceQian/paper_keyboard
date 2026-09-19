import time

import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource
from input_sources.serial_tap_source import SerialTapSource

from components.paper_mapper import PaperMapper
from components.frame_builder import FrameBuilder
from components.key_finder import KeyFinder
from components.input_decider import InputDecider
from components.text_buffer import TextBuffer
from components.frame_tools import get_candidate
from components.frame_tools import get_finger_position_by_id

PORT = "/dev/cu.usbmodem1101"

def get_current_key(frame, key_finder):
    # 当前声音版只看食指，继续取 finger_id = 1。
    position = get_finger_position_by_id(frame, 1)

    if position is None:
        return None

    x, y = position

    # KeyFinder 根据纸面坐标判断这个点在哪个 key 里。
    key_id = key_finder.find_key(x, y)

    return key_id


def handle_input(frame, input_decider, key_finder, text_buffer):
    # 从 frame 里读取 candidate。
    # 声音超过阈值时，AudioSource 会让 candidate 变成 1。
    candidate = get_candidate(frame)

    # InputDecider 判断这个 candidate 是不是一次新的触发。
    input_finger_id = input_decider.decide_candidate(candidate)

    if input_finger_id is None:
        return None

    # 声音版目前只支持食指输入。
    if input_finger_id != 1:
        return None

    # 触发输入时，输入食指当前所在的 key。
    input_key_id = get_current_key(frame, key_finder)

    if input_key_id is None:
        return None

    text_buffer.add_char(input_key_id)

    return input_key_id


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    # 打开摄像头。
    camera = CameraSource(camera_id=0)

    # 创建手部识别对象。
    hand_source = MediaPipeHandSource(max_num_hands=1)

    # 创建纸面定位对象。
    paper_mapper = PaperMapper(layout_path)

    # 创建 KeyFinder。
    key_finder = KeyFinder(layout_path)

    # 创建声音输入对象。
    tap_source = SerialTapSource(
        port=PORT,
        baudrate=115200
    )

    # 创建 FrameBuilder。
    # 这次传入 audio_source，所以 frame 里的 candidate 会来自声音输入。
    frame_builder = FrameBuilder(
        paper_mapper,
        hand_source,
        tap_source
    )

    # InputDecider 用来避免同一次声音触发被重复输入。
    input_decider = InputDecider()

    # TextBuffer 保存最终输入出来的文本。
    text_buffer = TextBuffer()

    frame_id = 0
    start_time = time.time()

    print("声音输入纸面键盘开始")
    print("请把纸面键盘放到摄像头画面里")
    print("把食指放到某个 key 上，然后敲击纸面")
    print("按 q 退出")
    print("按 p 打印当前 frame")

    # 开始监听麦克风。

    while True:
        # 读取一帧摄像头画面。
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        # 计算当前时间。
        t = time.time() - start_time

        # 根据当前画面和声音输入生成 frame。
        frame, visual_data = frame_builder.build_frame(
            image,
            frame_id,
            t
        )

        # 从 visual_data 里取出调试显示需要的数据。
        homography = visual_data["homography"]
        corners = visual_data["corners"]
        ids = visual_data["ids"]
        hand_data = visual_data["hand_data"]
        mediapipe_result = visual_data["mediapipe_result"]

        # 根据食指当前位置判断当前 key。
        current_key = get_current_key(frame, key_finder)

        # 如果这一帧有声音触发，就尝试输入当前 key。
        input_key = handle_input(
            frame,
            input_decider,
            key_finder,
            text_buffer
        )

        if input_key is not None:
            print("输入：", input_key)
            print("当前文本：", text_buffer.get_text())

        # 画识别到的 ArUco marker。
        image = paper_mapper.draw_detected_markers(image, corners, ids)

        if homography is not None:
            # 画纸面边框。
            image = paper_mapper.draw_board_border(image, homography)

            # 画 layout 里的按键框。
            image = paper_mapper.draw_keys(image, homography)

            # 高亮食指当前所在的 key。
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

        # 显示当前文本。
        cv2.putText(
            image,
            "text: " + text_buffer.get_text(),
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2
        )

        # 画手部骨架和指尖编号。
        image = hand_source.draw_hand(image, mediapipe_result)
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - Audio Keyboard", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("p"):
            print(frame)

        frame_id = frame_id + 1

    tap_source.close()
    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("声音输入纸面键盘结束")


if __name__ == "__main__":
    main()