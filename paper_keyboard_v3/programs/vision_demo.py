import time

import cv2

from components.frame_builder import FrameBuilder
from components.frame_tools import get_current_key_id
from components.input_decider import InputDecider
from components.key_finder import KeyFinder
from components.paper_mapper import PaperMapper
from components.text_buffer import TextBuffer
from components.visual_overlay import VisualOverlay

from input_sources.audio_source import AudioSource
from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource


def handle_keyboard_input(key, text_buffer):
    """
    处理键盘操作。

    当前支持：
        q: 退出
        c: 清空文本
    """
    should_quit = False

    if key == ord("q"):
        should_quit = True

    elif key == ord("c"):
        text_buffer.clear()
        print("已清空文本")

    return should_quit


def handle_input_decision(input_decider, frame, current_key_id, text_buffer):
    """
    使用 InputDecider 判断当前 frame 是否产生输入。

    注意：
        输入判断不直接写在 main 里。
        main 只负责调用组件。
    """
    input_key_id = input_decider.decide_key(frame, current_key_id)

    if input_key_id is None:
        return

    text_buffer.add_key(input_key_id)

    print("输入：", input_key_id)
    print("当前文本：", text_buffer.get_text())


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    camera_id = 1

    camera_source = CameraSource(camera_id=camera_id)

    paper_mapper = PaperMapper(layout_path)
    hand_source = MediaPipeHandSource(swap_hands=True)

    tap_source = AudioSource(
        threshold=0.04,
        cooldown=0.25,
        candidate_id=1
    )

    frame_builder = FrameBuilder(
        paper_mapper=paper_mapper,
        hand_source=hand_source,
        tap_source=tap_source
    )

    key_finder = KeyFinder(layout_path)
    input_decider = InputDecider()
    text_buffer = TextBuffer()
    overlay = VisualOverlay(layout_path)

    tap_source.start()

    start_time = time.time()
    frame_id = 1

    print("Paper Keyboard Vision Demo 开始")
    print("操作说明：")
    print("敲击纸面：输入当前按键")
    print("c：清空文本")
    print("q：退出")
    print()

    try:
        while True:
            success, image = camera_source.read_image()

            if not success:
                print("读取摄像头失败")
                break

            t = time.time() - start_time

            frame, visual_data = frame_builder.build_frame(
                image,
                frame_id,
                t
            )

            current_key_id = get_current_key_id(
                frame,
                key_finder
            )

            handle_input_decision(
                input_decider,
                frame,
                current_key_id,
                text_buffer
            )

            debug_image = overlay.draw_all(
                image,
                frame,
                visual_data,
                current_key_id,
                text_buffer.get_text()
            )

            cv2.imshow("Paper Keyboard Vision Demo", debug_image)

            key = cv2.waitKey(1)

            should_quit = handle_keyboard_input(
                key,
                text_buffer
            )

            if should_quit:
                break

            frame_id += 1

    finally:
        tap_source.stop()
        hand_source.close()
        camera_source.release()
        cv2.destroyAllWindows()

    print("Paper Keyboard Vision Demo 结束")
    print("最终文本：", text_buffer.get_text())


if __name__ == "__main__":
    main()