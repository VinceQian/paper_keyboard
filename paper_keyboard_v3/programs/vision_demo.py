import time

import cv2

from components.frame_builder import FrameBuilder
from components.frame_tools import get_current_key_id, get_key_id_for_finger
from components.input_decider import InputDecider
from components.key_finder import KeyFinder
from components.paper_mapper import PaperMapper
from components.session_writer import build_session, save_session
from components.text_buffer import TextBuffer
from components.visual_overlay import VisualOverlay

from input_sources.audio_source import AudioSource
from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource


def save_recorded_session(recorded_frames, layout_id):
    """
    保存当前录制到的 frames。

    使用 session_writer.py 中的 build_session 和 save_session。
    """
    if len(recorded_frames) == 0:
        print("当前没有可保存的 frame")
        return

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    session_id = f"vision_session_{timestamp}"
    output_path = f"data/generated/{session_id}.json"

    session = build_session(
        session_id=session_id,
        layout_id=layout_id,
        frames=recorded_frames
    )

    save_session(output_path, session)

    print("已保存 session：", output_path)
    print("frame 数量：", len(recorded_frames))


def handle_keyboard_input(key, text_buffer, recorded_frames, layout_id):
    """
    处理键盘操作。

    当前支持：
        q: 退出
        c: 清空文本
        s: 保存当前 session
    """
    should_quit = False

    if key == ord("q"):
        should_quit = True

    elif key == ord("c"):
        text_buffer.clear()
        print("已清空文本")

    elif key == ord("s"):
        save_recorded_session(recorded_frames, layout_id)

    return should_quit


def handle_input_decision(input_decider, frame, input_key_id, text_buffer):
    """
    使用 InputDecider 判断当前 frame 是否产生输入。
    """
    confirmed_key_id = input_decider.decide_key(frame, input_key_id)

    if confirmed_key_id is None:
        return

    text_buffer.add_key(confirmed_key_id)

    print("输入：", confirmed_key_id)
    print("当前文本：", text_buffer.get_text())


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"
    layout_id = "keyboard_number_v1"

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

    recorded_frames = []

    tap_source.start()

    start_time = time.time()
    frame_id = 1

    print("Paper Keyboard Vision Demo 开始")
    print("操作说明：")
    print("敲击纸面：输入当前按键")
    print("s：保存当前 session")
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

            # 加入每一帧
            recorded_frames.append(frame)

            # 显示用：
            # 不看 tap.candidate，只看右手食指当前在哪里。
            display_key_id = get_key_id_for_finger(
                frame,
                finger_id=1,
                key_finder=key_finder
            )

            # 输入判断用：
            # 依赖 tap.candidate。
            input_key_id = get_current_key_id(
                frame,
                key_finder
            )

            handle_input_decision(
                input_decider,
                frame,
                input_key_id,
                text_buffer
            )

            debug_image = overlay.draw_all(
                image,
                frame,
                visual_data,
                display_key_id,
                text_buffer.get_text()
            )

            cv2.imshow("Paper Keyboard Vision Demo", debug_image)

            key = cv2.waitKey(1)

            should_quit = handle_keyboard_input(
                key,
                text_buffer,
                recorded_frames,
                layout_id
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
    print("本次记录 frame 数量：", len(recorded_frames))


if __name__ == "__main__":
    main()