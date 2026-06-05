from input_sources.session_source import SessionSource

from components.key_finder import KeyFinder
from components.input_decider import InputDecider
from components.text_buffer import TextBuffer
from components.frame_tools import get_candidate, get_finger_position_by_id


def main():
    session_path = "data/sessions/test_number_input_123.json"
    layout_path = "data/layouts/keyboard_number_v1.json"

    source = SessionSource(session_path)
    key_finder = KeyFinder(layout_path)
    input_decider = InputDecider()
    text_buffer = TextBuffer()

    frames = source.get_frames()

    print("开始回放 session")
    print("session 文件:", session_path)
    print("session_id:", source.get_session_id())
    print("layout_id:", source.get_layout_id())
    print("frame 数量:", len(frames))
    print()

    for frame in frames:
        frame_id = frame["frame_id"]

        candidate = get_candidate(frame)
        input_finger_id = input_decider.decide_candidate(candidate)

        if input_finger_id is None:
            continue

        position = get_finger_position_by_id(frame, input_finger_id)

        if position is None:
            continue

        x, y = position
        input_key_id = key_finder.find_key(x, y)

        if input_key_id is None:
            continue

        text_buffer.add_key(input_key_id)

        print(
            f"frame {frame_id}: "
            f"finger {input_finger_id} 输入 {input_key_id}，"
            f"当前文本：{text_buffer.get_text()}"
        )

    print()
    print("最终输入结果：", text_buffer.get_text())


if __name__ == "__main__":
    main()