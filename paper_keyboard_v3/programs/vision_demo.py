import cv2
import time

from components.paper_mapper import PaperMapper
from components.key_finder import KeyFinder
from components.text_buffer import TextBuffer
from components.vision_frame_builder import VisionFrameBuilder
from components.visual_overlay import VisualOverlay
from input_sources.mediapipe_hand_source import MediaPipeHandSource
from input_sources.audio_source import AudioSource


def find_finger_by_id(frame, target_finger_id):
    """
    从 frame 中找到指定 finger_id 的手指。

    当前基础版主要找：
        finger_id = 1，也就是右手食指。
    """
    for finger in frame["fingers"]:
        if finger["finger_id"] == target_finger_id:
            return finger

    return None


def get_current_key_id(frame, key_finder):
    """
    根据当前 frame 判断候选手指所在的按键。

    当前规则：
        tap.candidate == 1 表示右手食指是候选输入来源。
        如果右手食指存在，就用它的纸面坐标判断 key_id。
    """
    candidate = frame["tap"]["candidate"]

    if candidate == -1:
        return None

    finger = find_finger_by_id(frame, candidate)

    if finger is None:
        return None

    x = finger["x"]
    y = finger["y"]

    key_id = key_finder.find_key(x, y)

    return key_id


def handle_keyboard_input(key, text_buffer):
    """
    处理键盘操作。

    返回：
        should_quit: 是否退出程序
    """
    should_quit = False

    if key == ord("q"):
        should_quit = True

    elif key == ord("c"):
        text_buffer.clear()
        print("已清空文本")

    return should_quit


def handle_audio_tap(audio_source, current_key_id, text_buffer):
    """
    如果检测到敲击，就输入当前按键。

    当前逻辑：
        1. AudioSource 检测到一次 tap
        2. 如果右手食指当前在某个 key 上
        3. 把这个 key 加入 TextBuffer
    """
    if not audio_source.get_tap():
        return

    if current_key_id is None:
        print("检测到敲击，但当前没有可输入的按键")
        return

    text_buffer.add_key(current_key_id)

    print("敲击输入：", current_key_id)
    print("当前文本：", text_buffer.get_text())


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    camera_id = 1

    paper_mapper = PaperMapper(layout_path)
    key_finder = KeyFinder(layout_path)
    text_buffer = TextBuffer()

    hand_source = MediaPipeHandSource(swap_hands=True)
    frame_builder = VisionFrameBuilder(paper_mapper, hand_source)
    overlay = VisualOverlay(layout_path)

    audio_source = AudioSource(
        threshold=0.05,
        cooldown=0.25
    )

    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        print("摄像头打开失败，请检查 camera_id。")
        print("如果你用的是 Mac 自带摄像头，可以把 camera_id 改成 0。")
        return

    audio_source.start()

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
            success, image = cap.read()

            if not success:
                print("读取摄像头失败")
                break

            t = time.time() - start_time

            frame, debug_data = frame_builder.build_frame(
                image,
                frame_id,
                t
            )

            current_key_id = get_current_key_id(frame, key_finder)

            handle_audio_tap(
                audio_source,
                current_key_id,
                text_buffer
            )

            debug_image = overlay.draw_all(
                image,
                frame,
                debug_data,
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
        audio_source.stop()
        hand_source.close()
        cap.release()
        cv2.destroyAllWindows()

    print("Paper Keyboard Vision Demo 结束")
    print("最终文本：", text_buffer.get_text())


if __name__ == "__main__":
    main()