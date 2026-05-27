from input_sources.session_source import SessionSource
from components.key_finder import KeyFinder
from components.input_decider import InputDecider
from components.text_buffer import TextBuffer


def get_first_finger(frame):
    """
    从 frame 中取出第一个手指。

    当前版本先只处理一个手指。
    如果没有检测到手指，就返回 None。
    """
    fingers = frame.get("fingers", [])

    if len(fingers) == 0:
        return None

    return fingers[0]


def main():
    session_path = "data/sessions/test_number_input_123.json"
    layout_path = "data/layouts/keyboard_number_v1.json"

    source = SessionSource(session_path)
    finder = KeyFinder(layout_path)
    decider = InputDecider()
    text_buffer = TextBuffer()

    frames = source.get_frames()

    print("开始回放 session")
    print("session_id:", source.get_session_id())
    print("layout_id:", source.get_layout_id())
    print()

    for frame in frames:
        frame_id = frame["frame_id"]
        finger = get_first_finger(frame)

        if finger is None:
            current_key_id = None
        else:
            x = finger["x"]
            y = finger["y"]
            current_key_id = finder.find_key(x, y)

        input_key_id = decider.decide_key(frame, current_key_id)

        if input_key_id is not None:
            text_buffer.add_key(input_key_id)
            print(f"frame {frame_id}: 输入 {input_key_id}，当前文本：{text_buffer.get_text()}")
        else:
            print(f"frame {frame_id}: 无输入")

    print()
    print("最终输入结果：", text_buffer.get_text())


if __name__ == "__main__":
    main()