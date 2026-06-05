from input_sources.session_source import SessionSource

from components.key_finder import KeyFinder
from components.input_decider import InputDecider
from components.frame_tools import get_candidate, get_finger_position_by_id


SESSION_PATH = "data/sessions/test_number_input_123.json"
LAYOUT_PATH = "data/layouts/keyboard_number_v1.json"


def main():
    session_source = SessionSource(SESSION_PATH)
    key_finder = KeyFinder(LAYOUT_PATH)
    input_decider = InputDecider()

    frames = session_source.get_frames()

    print("开始测试 replay 数据")
    print("session 文件：", SESSION_PATH)
    print("session_id：", session_source.get_session_id())
    print("layout_id：", session_source.get_layout_id())
    print("frame 数量：", len(frames))
    print()

    for frame in frames:
        frame_id = frame["frame_id"]

        candidate = get_candidate(frame)
        input_finger_id = input_decider.decide_candidate(candidate)

        print("frame", frame_id)
        print("  candidate：", candidate)
        print("  新输入手指：", input_finger_id)

        if input_finger_id is None:
            print("  结果：这一帧没有新的输入")
            print()
            continue

        position = get_finger_position_by_id(frame, input_finger_id)

        if position is None:
            print("  结果：找不到这个手指的位置")
            print()
            continue

        x, y = position
        key_id = key_finder.find_key(x, y)

        print("  手指位置：", position)
        print("  对应按键：", key_id)
        print()

    print("测试结束")


if __name__ == "__main__":
    main()