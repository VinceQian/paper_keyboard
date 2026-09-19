# replay_session.py 是今天最重要的文件。
# 它负责把所有组件组合起来。
#
# replay_session 的核心循环：
# 对每一帧 frame，需要做这些事情：
#
# 1. 读取 candidate
# 2. 判断 candidate 是不是新的输入触发
# 3. 如果不是新的输入，跳过
# 4. 如果是新的输入，根据 finger_id 找手指坐标
# 5. 如果找不到坐标，跳过
# 6. 如果找到坐标，用 KeyFinder 找 key
# 7. 如果没有落在任何 key 上，跳过
# 8. 如果找到 key，加入 TextBuffer


from input_sources.session_source import SessionSource
from components.input_decider import InputDecider
from components.key_finder import KeyFinder
from components.text_buffer import TextBuffer
from components.frame_tools import get_finger_position_by_id,get_candidate
def main():
    session = SessionSource("test_number_input_123.json")
    decider = InputDecider()
    finder = KeyFinder("keyboard_number_v1.json")
    text =TextBuffer()
    frames = session.get_frames()
    for frame in frames:
        candidate=get_candidate(frame)
        finger_id=decider.decide_candidate(candidate)
        if finger_id==None:
            continue
        position=get_finger_position_by_id(frame, finger_id)
        if position is None:
            continue
        x,y = position
        key=finder.find_key(x,y)
        text.add_char(key)
        print(text.get_text())
    
if __name__ == "__main__":
    main()