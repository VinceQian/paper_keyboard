# 本节课目标：
# 1. 复习 dict 和 list 的基本写法
# 2. 理解项目里 frame / layout 这种嵌套数据结构
# 3. 学会用 def 把代码拆成函数
# 4. 初步理解项目目录和模块化开发
# 5. 写项目的 key_finder.py 和 frame_tools.py 组件


# ============================================================
# 1. dict 字典
# ============================================================

# dict 用来保存“有名字的数据”。
#
# 基本形式：
#
# 变量名 = {
#     "key1": value1,
#     "key2": value2,
#     "key3": value3
# }
#
# 注意：
# 1. dict 外面用大括号 {}
# 2. 每一项都是 key: value
# 3. key 和 value 中间用冒号 :
# 4. 不同项之间用逗号 ,
# 5. 最后一项后面可以不写逗号
# 6. 字符串要加引号

# 在 Paper Keyboard 里，一个 key 可以用 dict 表示：
#
# {
#     "id": "1",
#     "x": 40,
#     "y": 50,
#     "w": 34,
#     "h": 30
# }

# a=1
# b=2
# c={"a":a}

# c["a"]

# print(a)

# # 创建一个 dict：
# xuesheng={
#       "name":"李浩宇",
#       "age":15,
#       "height":175
# }
# # 从 dict 中取数据：
# xuesheng["height"]
# print(xuesheng["height"])

# ============================================================
# 2. list 列表
# ============================================================

# list 用来保存“一串数据”。
#
# 基本形式：
#
# 变量名 = [item1, item2, item3]
#
# 注意：
# 1. list 外面用中括号 []
# 2. 不同元素之间用逗号 ,
# 3. list 里的元素可以是数字、字符串、dict，甚至另一个 list
# 4. list 的下标从 0 开始

# 在 Paper Keyboard 里，很多 keys 可以放在一个 list 里：
#
keys = [
    {"id": "1", "x": 40, "y": 50, "w": 34, "h": 30},
    {"id": "2", "x": 80, "y": 50, "w": 34, "h": 30},
    {"id": "3", "x": 120, "y": 50, "w": 34, "h": 30}
]


# key=[1,2,3,"li"]

# # 创建一个 list：

# # 从 list 中取数据：
# print(key[3])
# # list 里如果放的是 dict，可以连续取：
# keys=[
#     {"name":"li","height":175,"age":15},
#     {"name":"qian","height":182,"age":25}
 
# ]
# print(keys[1]["name"])
# ============================================================
# 3. dict + list 嵌套结构
# ============================================================

# 项目里的数据通常不是单独的 dict 或 list，而是 dict 和 list 套在一起。

# layout 的大致结构：
#
layout = {
    "layout_id": "keyboard_number_v1",
    "unit": "mm",
    "keys": [
        {"id": "1", "x": 40, "y": 50, "w": 34, "h": 30},
        {"id": "2", "x": 80, "y": 50, "w": 34, "h": 30}
    ]
}

# 读取 layout 里的 keys：
print(layout["keys"])

# 读取第一个 key：
print(layout["keys"])



# 读取第一个 key 的 id：
print(layout["keys"][0]["id"])


# ============================================================
# 4. frame 数据结构
# ============================================================

# frame 表示某一时刻的输入状态。
#
# 一个 frame 里面包含：
# 1. frame_id：第几帧
# 2. t：当前时间
# 3. fingers：当前有哪些手指，它们在哪里
# 4. tap：当前是否有触发输入的手指

# frame 的结构：
#
frame = {
    "frame_id": 1,
    "t": 0.0,
    "fingers": [
        {
            "finger_id": 0,
            "x": 40,
            "y": 65
        },
        {
            "finger_id": 1,
            "x": 57,
            "y": 65
        },
        {
            "finger_id": 2,
            "x": 74,
            "y": 65
        }
    ],
    "tap": {
        "candidate": 1
    }
}

# 读取 candidate：
print(frame["tap"]["candidate"])

# 读取 fingers：
print(frame["fingers"])
# 读取第一个 finger：
print(frame["fingers"][0])
# 读取第一个 finger 的坐标：
print(frame["fingers"][0]["x"])
print(frame["fingers"][0]["y"])


# ============================================================
# 5. for 循环遍历 list
# ============================================================

# 如果我们有很多 key，就需要一个一个检查。
#
# 基本形式：
#
# for item in items:
#     对当前 item 做一些事情

# 在 KeyFinder 里，我们会这样做：
#
# for key in keys:
#     检查当前坐标是否在这个 key 里面

# 这比手动写：
#
# key1 = keys[0]
# key2 = keys[1]
# key3 = keys[2]
#
# 更适合处理很多按键。

# 循环遍历 keys，输出每个 key 的 id：
for finger in frame["fingers"]:
    print(finger["finger_id"])

# ============================================================
# 6. if 条件判断
# ============================================================

# if 用来判断一件事情是否成立。
#
# 基本形式：
#
# if 条件:
#     条件成立时运行的代码
# else:
#     条件不成立时运行的代码

# 在 KeyFinder 里，我们需要判断：
#

layout = {
    "layout_id": "keyboard_number_v1",
    "unit": "mm",
    "keys": [
        {"id": "1", "x": 40, "y": 50, "w": 34, "h": 30},
        {"id": "2", "x": 80, "y": 50, "w": 34, "h": 30}
    ]
}

x = 55
y = 55

# 这个 x 是否在 key 的左右范围内？
# 这个 y 是否在 key 的上下范围内？

# 判断 x 是否在范围内：
key1=layout["keys"][0]
if x<=key1["x"]+key1["w"] and x>=key1["x"]:
    print("x在范围内")
else:
    print("x不在范围内")
# 判断 y 是否在范围内：
if y<=key1["y"]+key1["h"] and y>=key1["y"]:
    print("y在范围内")
else:
    print("y不在范围内")
# 如果两个都成立，就说明坐标在这个按键里面：
in_x_range = key1["x"]+key1["w"] >= x >= key1["x"]
in_y_range = key1["y"]+key1["h"] >= y >= key1["y"]

if in_x_range and in_y_range:
    print("手指在按键范围内")
else:
    print("手指不在按键范围内")

# ============================================================
# 7. def 函数
# ============================================================

# def 用来定义一个函数。
# 函数的作用是：把一段可以重复使用的代码打包起来。
#
# 基本形式：
#
# def 函数名(参数1, 参数2):
#     函数里面的代码
#     return 结果

# 例子：
#
def add(a, b):
    result = a + b
    return result

# 使用函数：
#
answer = add(3, 5)
print(answer)

# 在项目里，我们会写很多小函数。
# 比如 frame_tools.py 里会有：
#
# get_fingers(frame)
# get_candidate(frame)
# find_finger_by_id(frame, target_finger_id)
# get_finger_position(finger)

# 这些函数的目的不是让代码变复杂，而是让每一段代码只负责一件小事。

# ============================================================
# 8. return 返回值
# ============================================================

# return 表示“把结果交回去”。
#
# 例如：
#
# def get_candidate(frame):
#     return frame["tap"]["candidate"]

# 使用时：
#
# candidate = get_candidate(frame)

# 这里 candidate 就会得到函数返回的结果。

# 如果函数找不到结果，也可以 return None。
#
# None 表示“没有结果”。

# 在 KeyFinder 里：
#
# 如果坐标落在某个 key 上，return key["id"]
# 如果没有落在任何 key 上，return None

# 定义一个函数，判断a和b相加是否是个两位数，如果是就返回这个两位数，否则返回 None：
def liangweishu(a,b):
    add=a+b
    if 10<=add<100:
        return add
    else:
        return None
    
answer=liangweishu(6,8)
print(answer)
# ============================================================
# 9. 项目目录
# ============================================================

# 一个稍微大一点的项目不会把所有代码都写在一个文件里。
#
# 我们的键盘项目大致分成：
#
# components/
#     放核心功能组件
#     比如 key_finder.py、frame_tools.py、input_decider.py
#
# input_sources/
#     放输入来源
#     比如 manual_source.py、session_source.py
#
# programs/
#     放可以运行的程序入口
#     比如 generate_session.py、replay_session.py
#
# data/
#     放数据文件
#     比如 layout json、session json
#
# app.py
#     总入口，用来选择当前运行哪个 program


# ============================================================
# 10. 模块化开发
# ============================================================

# 模块化的意思是：
# 把不同功能拆到不同文件里。
#
# 例如：
#
# key_finder.py
#     只负责“坐标在哪个按键上”
#
# frame_tools.py
#     只负责“从 frame 里面取数据”
#
# input_decider.py
#     只负责“判断这一次是否真的输入”
#
# text_buffer.py
#     只负责“保存最终文本”

# 这样做的好处：
# 1. 每个文件更短
# 2. 每个文件只做一件事
# 3. 出问题时更容易找到原因
# 4. 后面换输入来源时，核心逻辑可以继续复用


# ============================================================
# 11. class 类
# ============================================================

# class 用来把“数据”和“相关功能”放在一起。
#
# 如果只是写函数，我们通常要把数据传来传去。
# 如果写成 class，就可以让一个对象自己保存数据，并且自己使用这些数据。

# 例如，在项目里我们会写 KeyFinder：
#
# class KeyFinder:
#     def __init__(self, layout_path):
#         self.layout_path = layout_path
#         self.keys = []
#
#     def find_key(self, x, y):
#         检查 x, y 落在哪个 key 上

# 这里：
# KeyFinder 是类名
# __init__ 是创建对象时自动运行的函数
# self.layout_path 是这个对象自己保存的数据
# self.keys 是这个对象自己保存的所有按键信息
# find_key() 是这个对象可以做的事情

# 使用 class 的方式：
#
# key_finder = KeyFinder("data/layouts/keyboard_number_v1.json")
# key_id = key_finder.find_key(57, 65)

# 可以先简单理解为：
# class 是一种更方便的方式，用来管理“同一类功能”。
# 在这个项目里，KeyFinder 只负责找按键，TextBuffer 只负责保存文字。


# ============================================================
# 12. import 从别的文件拿代码
# ============================================================

# import 的作用是使用其他文件里的代码。
#
# 例如：
#
# from components.key_finder import KeyFinder
#
# 意思是：
# 从 components 文件夹里的 key_finder.py 文件中，拿出 KeyFinder 来使用。

# 再比如：
#
# from components.frame_tools import get_candidate
#
# 意思是：
# 从 frame_tools.py 里面拿出 get_candidate 这个函数来使用。


# ============================================================
# 13. app.py 的作用
# ============================================================

# app.py 是整个项目的总入口。
#
# 它的作用不是写所有功能，而是选择当前要运行哪个程序。
#
# 例如：
#
# from programs.test_key_finder import main as current_program_main
#
# def main():
#     current_program_main()
#
# if __name__ == "__main__":
#     main()

# 之后如果要切换程序，只需要改 import：
#
# from programs.generate_session import main as current_program_main
#
# 或者：
#
# from programs.replay_session import main as current_program_main


# ============================================================
# 14. 接下来要进入的项目文件
# ============================================================

# 练习完这个文件后，我们会开始写：
#
# components/key_finder.py
#     根据 x, y 判断当前坐标在哪个按键上
#
# components/frame_tools.py
#     从 frame 里面读取 fingers、candidate、finger position
#
# programs/test_key_finder.py
#     测试 KeyFinder 能不能正常工作