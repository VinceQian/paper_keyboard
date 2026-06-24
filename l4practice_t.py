# 本节课目标：
# 1. 接着第三节课，完成 SessionSource
# 2. 完成 InputDecider
# 3. 完成 TextBuffer
# 4. 完成 programs/replay_session.py
# 5. 修改 app.py，用 import 把项目组件组合起来运行


# ============================================================
# 1. 复习：我们现在已经完成了什么
# ============================================================

# 目前已经完成：
#
# components/key_finder.py
#     根据 x, y 判断当前坐标在哪个按键上。
#
# components/frame_tools.py
#     从 frame 里读取 candidate 和手指坐标。
#
# data/layouts/keyboard_number_v1.json
#     保存键盘布局。
#
# data/sessions/test_number_input_123.json
#     保存一段模拟输入过程。
#
# 今天要完成的是：
# 读取 session 文件，然后一帧一帧回放，最后输出输入结果。


# ============================================================
# 2. 今天的完整数据流
# ============================================================

# replay 的意思是：
# 不使用摄像头，不使用麦克风，不使用真实硬件。
# 直接读取已经保存好的 session JSON，模拟整个输入过程。
#
# 完整流程：
#
# SessionSource
#     读取 session JSON
#
# get_candidate(frame)
#     读取当前 frame 的 candidate
#
# InputDecider
#     判断 candidate 是否是一次新的输入触发
#
# get_finger_position_by_id(frame, finger_id)
#     根据 finger_id 找到这个手指的位置
#
# KeyFinder
#     根据 x, y 判断手指在哪个 key 上
#
# TextBuffer
#     保存最终输入出来的文本
#
# replay_session.py
#     把上面所有组件组合起来


# ============================================================
# 3. 完成 input_sources/session_source.py
# ============================================================

# SessionSource 的作用：
# 1. 创建对象时读取 session json
# 2. 把读取到的数据保存到 self.session
# 3. 提供几个函数，让其他程序可以拿到 session 信息
#
# 这个文件写在：
# input_sources/session_source.py
#
# 需要 import：
# import json

# TODO
# 参考代码：

# import json
#
#
# class SessionSource:
#     def __init__(self, session_path):
#         self.session_path = session_path
#         self.session = self.load_session(session_path)
#
#     def load_session(self, session_path):
#         with open(session_path, "r", encoding="utf-8") as f:
#             return json.load(f)
#
#     def get_session_id(self):
#         return self.session["session_id"]
#
#     def get_layout_id(self):
#         return self.session["layout_id"]
#
#     def get_unit(self):
#         return self.session["unit"]
#
#     def get_frames(self):
#         return self.session["frames"]
#
#
# def main():
#     source = SessionSource("data/sessions/test_number_input_123.json")
#     print(source.get_session_id())
#     print(source.get_layout_id())
#     print(source.get_unit())
#     print(len(source.get_frames()))
#
#
# if __name__ == "__main__":
#     main()


# ============================================================
# 4. 完成 components/input_decider.py
# ============================================================

# InputDecider 的作用：
# 判断 candidate 是否是一次新的输入触发。
#
# candidate 的规则：
#
# -1
#     没有触发输入
#
# 0-9
#     某个 finger_id 触发了输入
#
# 为什么不能看到 candidate 就输入？
#
# 因为一次敲击可能会持续好几帧。
# 例如：
#
# -1, 1, 1, 1, -1
#
# 这里 candidate=1 出现了三帧，但这只是一次敲击。
# 所以只能输入一次。
#
# 判断新输入的规则：
#
# 上一帧是 -1
# 当前帧不是 -1
#
# 这时才认为产生了一次新输入。
#
# 这个文件写在：
# components/input_decider.py

# TODO
# 参考代码：

# class InputDecider:
#     def __init__(self):
#         self.last_candidate = -1
#
#     def decide_candidate(self, candidate):
#         is_new_input = (
#             self.last_candidate == -1
#             and candidate != -1
#         )
#
#         self.last_candidate = candidate
#
#         if is_new_input:
#             return candidate
#
#         return None
#
#
# def main():
#     decider = InputDecider()
#     candidates = [-1, 1, 1, -1, 2, 2, -1, 0, 0, -1]
#
#     for candidate in candidates:
#         result = decider.decide_candidate(candidate)
#         print("candidate:", candidate, "-> 新输入:", result)
#
#
# if __name__ == "__main__":
#     main()

# 注意：
# candidate = 0 是合法输入。
# 所以不能写：
#
# if candidate:
#
# 因为 0 会被 Python 当成 False。


# ============================================================
# 5. 完成 components/text_buffer.py
# ============================================================

# TextBuffer 的作用：
# 保存最终输入出来的文本。
#
# 例如依次输入：
#
# 1
# 2
# 3
#
# 最终文本就是：
#
# "123"
#
# 这个文件写在：
# components/text_buffer.py

# TODO
# 参考代码：

# class TextBuffer:
#     def __init__(self):
#         self.text = ""
#
#     def add_key(self, key_id):
#         if key_id == "del":
#           self.text = self.text[:-1]
#         else:
#           self.text = self.text + str(key_id)
#
#     def get_text(self):
#         return self.text
#
#     def clear(self):
#         self.text = ""
#
#
# def main():
#     buffer = TextBuffer()
#
#     buffer.add_key("1")
#     buffer.add_key("2")
#     buffer.add_key("3")
#     buffer.add_key("del")
#
#     print(buffer.get_text())
#
#     buffer.clear()
#     print(buffer.get_text())
#
#
# if __name__ == "__main__":
#     main()


# ============================================================
# 6. 完成 programs/replay_session.py
# ============================================================

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
#
# 这个文件写在：
# programs/replay_session.py
#
# TODO
# 需要 import：
#
# from input_sources.session_source import SessionSource
# from components.key_finder import KeyFinder
# from components.input_decider import InputDecider
# from components.text_buffer import TextBuffer
# from components.frame_tools import get_candidate, get_finger_position_by_id

# replay_session.py 的 main() 开头：
#
# def main():
#     session_path = "data/sessions/test_number_input_123.json"
#     layout_path = "data/layouts/keyboard_number_v1.json"
#
#     source = SessionSource(session_path)
#     key_finder = KeyFinder(layout_path)
#     input_decider = InputDecider()
#     text_buffer = TextBuffer()
#
#     frames = source.get_frames()
#
#     print("开始回放 session")
#     print("session 文件：", session_path)
#     print("session_id：", source.get_session_id())
#     print("layout_id：", source.get_layout_id())
#     print("frame 数量：", len(frames))
#     print()
# 核心循环代码：
#
#     for frame in frames:
#         frame_id = frame["frame_id"]
#
#         candidate = get_candidate(frame)
#         input_finger_id = input_decider.decide_candidate(candidate)
#
#         if input_finger_id is None:
#             continue
#
#         position = get_finger_position_by_id(frame, input_finger_id)
#
#         if position is None:
#             continue
#
#         x, y = position
#         input_key_id = key_finder.find_key(x, y)
#
#         if input_key_id is None:
#             continue
#
#         text_buffer.add_key(input_key_id)
#
#         print(
#             f"frame {frame_id}: "
#             f"finger {input_finger_id} 输入 {input_key_id}，"
#             f"当前文本：{text_buffer.get_text()}"
#         )
#
#     print()
#     print("最终输入结果：", text_buffer.get_text())
#
#
# if __name__ == "__main__":
#     main()


# ============================================================
# 7. 完成 app.py
# ============================================================

# app.py 是项目总入口。
# 它不负责写项目逻辑，只负责选择运行哪个 program。
# 
# TODO

# from programs.replay_session import main as current_program_main
#
#
# def main():
#     current_program_main()
#
#
# if __name__ == "__main__":
#     main()


# ============================================================
# 8. 运行程序
# ============================================================


# ============================================================
# 9. 我们完成了什么
# ============================================================

# 现在我们已经完成了纸面键盘的逻辑核心。
#
# 现在还没有加入任何传感器，
# 但是程序已经可以处理完整的数据流：
#
# session JSON
#     保存一段输入过程
#
# frame
#     某一时刻的手指位置和 candidate
#
# candidate
#     哪个手指触发输入
#
# InputDecider
#     判断是不是一次新的触发
#
# KeyFinder
#     判断这个手指在哪个按键上
#
# TextBuffer
#     保存最终输入结果
#
# 后面线下课加入摄像头和硬件按钮时，
# 本质上只是把 input_sources 里的 session_source.py 换成传感器的source。
# 所有的核心判断逻辑可以直接继续使用。


# ============================================================
# 10. 后续计划
# ============================================================

# 线下课开始后，课程模式会和线上课不太一样。
#
# 线上课主要是：
#
#     学 Python 基础
#     理解 dict / list / function / class / json / import
#     写出项目的核心逻辑
#
# 线下课会更接近真实项目开发：
#
#     测试摄像头
#     测试手指识别
#     测试纸面定位
#     接入硬件传感器
#     做多指输入测试
#     设计纸面键盘
#     整理最终展示
#     准备报告和答辩
#
# 所以后续不会继续把重点放在“逐行学习 Python 语法”上。
# 代码仍然重要，但更重要的是理解项目流程和模块之间的关系。
# 所以我们会使用 AI 辅助开发，或者可以叫 vibe coding。
#
# 比如后面可能会让 AI 帮忙写：
#
#     摄像头测试程序
#     串口按钮读取程序
#     OpenCV 显示调试信息
#     保存测试结果
#     报告初稿
#     答辩稿
#
# 但是项目的核心数据流（也就是我们写完的这些部分）仍然需要自己理解：
#
#     frame
#     candidate
#     InputDecider
#     KeyFinder
#     TextBuffer


# TODO
# 线下课前建议重新看一遍这些文件：
#
# components/frame_tools.py
# components/key_finder.py
# components/input_decider.py
# components/text_buffer.py
# input_sources/session_source.py
# programs/replay_session.py
#
# 不需要背代码。
# 但是需要能大概说清楚每个文件负责什么。
#
# 建议线下课前重新运行几次代码，也可以尝试自己去修改输入，看看输出会怎么变化：


# TODO
# 线下课会制作真实的纸面键盘。
#
# 可以提前想一想：
#
# 1. 键盘上要有哪些键？
# 2. 只需要数字键，还是需要 delete / space / enter？
# 3. 按键要不要做大一点？
# 4. 按键之间要不要留更大的间隔？
# 5. 最终展示时，希望输入什么内容？
#
# 可以简单画一个草图，不需要很正式，线下课时可以参照着实现。


# TODO
# 可以尝试用 AI 帮忙理解和实现项目，比如：
#
#     我正在做一个 Python 纸面键盘项目。
#     请帮我解释 frame、candidate、InputDecider、KeyFinder 和 TextBuffer
#     之间的关系，要求适合初学者理解。
#
# 重点是练习：
#
#     怎么把问题说清楚
#     怎么判断 AI 的回答对不对
#     怎么把 AI 的回答和自己的项目对应起来
#     如果觉得有趣，甚至可以尝试自己去推进这个项目，或是在 AI 的帮助下完成一些其他自己感兴趣的想法 —— 很多事情往往没有想象的那么难
#     比如可以学习怎么使用 GitHub，怎么用 Git 做项目的版本管理，怎么把我们的这个项目 push 上去等等 —— 如果你想要在相关领域学习，Git 一定是个有用的工具