from input_sources.session_source import SessionSource

from components.key_finder import KeyFinder
from components.input_decider import InputDecider
from components.text_buffer import TextBuffer
from components.frame_tools import get_current_key_id


def main():
    session_path = "data/generated/manual_input_12345.json"
    layout_path = "data/layouts/keyboard_number_v1.json"

    source = SessionSource(session_path)
    key_finder = KeyFinder(layout_path)
    input_decider = InputDecider()
    text_buffer = TextBuffer()

    frames = source.get_frames()

    print("开始回放 session")
    print("session_id:", source.get_session_id())
    print("layout_id:", source.get_layout_id())
    print("frame 数量:", len(frames))
    print()

    for frame in frames:
        frame_id = frame["frame_id"]

        current_key_id = get_current_key_id(
            frame,
            key_finder
        )

        input_key_id = input_decider.decide_key(
            frame,
            current_key_id
        )

        if input_key_id is not None:
            text_buffer.add_key(input_key_id)
            print(
                f"frame {frame_id}: "
                f"输入 {input_key_id}，"
                f"当前文本：{text_buffer.get_text()}"
            )
        else:
            print(f"frame {frame_id}: 无输入")

    print()
    print("最终输入结果：", text_buffer.get_text())


if __name__ == "__main__":
    main()