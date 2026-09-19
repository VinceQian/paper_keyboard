# 本节课目标：
# 1. 复习第二节课的知识点
# 2. 学习 dict 的 get 用法
# 3. 理解 class 是什么
# 4. 理解 self 是什么
# 5. 理解 __init__ 什么时候运行
# 6. 理解 json 文件和读取
# 7. 完成 frame_tools, key_finder, session_source, input_decider（部分）, replay_session(部分), app


# ============================================================
# 1. 复习：第二节课知识点
# ============================================================

# 1. dict 字典
#    用来保存“有名字的数据”
#
#    例如：
#    key = {
#        "id": "1",
#        "x": 40,
#        "y": 50,
#        "w": 34,
#        "h": 30
#    }

# 2. list 列表
#    用来保存“一串数据”
#
#    例如：
#    keys = [
#        {"id": "1", "x": 40, "y": 50, "w": 34, "h": 30},
#        {"id": "2", "x": 80, "y": 50, "w": 34, "h": 30}
#    ]

# 3. dict + list 嵌套
#    项目里的 layout、frame、session 都是 dict 和 list 套在一起。
#
#    例如：
#    layout["keys"][0]["id"]

# 4. frame 数据结构
#    frame 表示某一时刻的输入状态。
#
#    例如：
#    frame["tap"]["candidate"]
#    frame["fingers"][0]["x"]

# 5. for 循环
#    用来一个一个处理 list 里的元素。
#
#    例如：
#    for finger in frame["fingers"]:
#        print(finger["finger_id"])

# 6. if 条件判断
#    用来判断一件事情是否成立。
#
#    例如：
#    if candidate == -1:
#        print("没有触发输入")

# 7. def 函数
#    用来把一段代码打包起来，方便重复使用。
#
#    例如：
#    def get_candidate(frame):
#        return frame["tap"]["candidate"]

# 8. return 返回值
#    return 表示把函数结果交回去。
#
#    如果找不到结果，也可以 return None。
#    None 表示“没有结果”。

# 9. 模块化开发
#    把不同功能拆到不同文件里。
#    每个文件只做一件事。


# ============================================================
# 2. dict 的 get 用法
# ============================================================

# 从 dict 里取数据，之前主要用的是 []。
#
# 例如：
#
# student = {
#     "name": "Tom",
#     "age": 15
# }
# #
# print(student["name"])
#
# 这种写法的意思是：
# 我确定这个 key 一定存在。
# 如果 key 不存在，程序会直接报错。

# 现在介绍另一种写法 .get()。
#
# 例如：

# print(student.get("name"))


# .get() 的特点是：
# 如果 key 存在，就返回对应的 value。
# 如果 key 不存在，不会报错，而是返回 None。

# print(student.get("height"))
# print(student["height"])


# 也可以给 .get() 一个默认值。
# 如果 key 不存在，就返回这个默认值。

# print(student.get("height", 0))


# 所以：
#
# dict["key"]
#     表示：这个 key 必须存在，不存在程序就会报错崩溃。
#
# dict.get("key")
#     表示：这个 key 可能不存在，不存在也可以接受，可以继续运行。


# ============================================================
# 3. 复习综合练习
# ============================================================

# 在对程序的优化调试中，我们发现先前的frame结构并没有很好的可访问性和可扩展性，所以对frame的结构做了些小调整。

frame1 = {
    "frame_id": 1,
    "t": 0.0,
    "fingers": {
        "0": {
            "x": 40,
            "y": 65
        },
        "1": {
            "x": 57,
            "y": 65
        },
        "2": {
            "x": 74,
            "y": 65
        }
    },
    "tap": {
        "candidate": 1
    }
}

frame2 = {"frame_id": 2,"t": 0.1,"fingers": {"0": {"x": 40,"y": 65},"1": {"x": 57,"y": 65},"2": {"x": 74,"y": 65}},"tap": {"candidate": 0}}
frame3 = {"frame_id": 3,"t": 0.2,"fingers": {"0": {"x": 40,"y": 65},"1": {"x": 57,"y": 65},"2": {"x": 74,"y": 65}},"tap": {"candidate": -1}}

# 任务1：
#
# 写一个小函数 get_candidate(frame)
#
# 它从 frame 里读取 tap.candidate 并返回。


# def add(a,b,c):
#     t = a+b
#     return t+c

# print(add(3,4,5))

# TODO
def get_candidate(frame):
    x =frame.get("tap")
    return x.get("candidate")

# student.get("name")

print(get_candidate(frame1))




# 任务2：
# 写一个函数 get_finger_position_by_id(frame, finger_id)
#
# 它要做的事情：
# 1. 从 frame 里取出 fingers
# 2. 因为 fingers 改成了 dict 类型，请 .get() 根据 finger_id 找手指
# 3. 注意 JSON 里的 key 是字符串，所以要用 str(finger_id)
# 4. 如果找到手指，返回这个手指的 x, y
# 5. 如果没找到，返回 None

# TODO
def get_finger_position_by_id(frame, finger_id):
    fingers=frame.get("fingers")
    position=fingers.get(str(finger_id))
    if position is None:
        return None

    return position.get("x"),position.get("y")
print(get_finger_position_by_id(frame1,"0"))





# ============================================================
# 4. 为什么需要 class
# ============================================================

# 之前我们写函数时，通常是这样：
#
# def 函数名(数据, 其他参数):
#     使用数据做一些事情
#     return 结果
#
# 这种方式没问题。
# 但是如果一个功能需要长期保存一些数据，每次都传来传去就会有点麻烦。

# 例如 KeyFinder 需要：
# 1. 保存所有 keys
# 2. 反复使用这些 keys 判断坐标在哪个按键上
#
# 如果不用 class，可能每次都要这样：
#
# key_id = find_key(keys, x, y)
#
# 如果用 class，就可以这样：
#
# key_finder = KeyFinder(keys)
# key_id = key_finder.find_key(x, y)
#
# key_finder 对象自己记住了 keys，
# 所以后面调用 find_key() 时，就不用每次都重新传 keys。


# ============================================================
# 5. class 的一个简单例子：Dog
# ============================================================

# class 可以用来描述一类东西。
# 比如 Dog 表示“狗”这一类对象。
#
# 每一只狗都有自己的数据：
# name：名字
# age：年龄
# energy：体力
#
# 每一只狗也可以做一些事情：
# bark()：叫
# eat()：吃饭，补充体力
# play()：玩耍，消耗体力

class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.energy = 50

    def bark(self):
        print(self.name, "说：汪汪！")

    def eat(self):
        self.energy = self.energy + 20
        print(self.name, "吃饭了，现在体力是：", self.energy)

    def play(self):
        self.energy = self.energy - 10
        print(self.name, "玩了一会儿，现在体力是：", self.energy)


dog1 = Dog("小白", 3)
dog2 = Dog("旺财", 5)

dog1.bark()
dog2.bark()

dog1.play()
dog1.eat()

dog2.play()
dog2.play()

# ============================================================
# 6. self 是什么
# ============================================================

# self 可以先简单理解成“这个对象自己”。
#
# 例如：
#
# self.name = name
#
# 意思是：
# 把传进来的 name 保存到这个对象自己身上。
#
# 以后这个对象的其他函数就可以直接使用 self.name。

# 在上面的 Dog 里：
#
# dog1 = Dog("小白", 3)
#
# 创建对象后：
# dog1 自己保存了：
# self.name = 小白
# self.age = 3
# self.energy = 50
#
# 所以后面调用：
# dog1.play()
#
# 它就可以使用自己保存的 name 和 energy


# ============================================================
# 7. __init__ 是什么时候运行的
# ============================================================

# __init__ 会在创建对象时自动运行。
#
# 例如：
#
# dog1 = Dog("小白", 3)
#
# 这一行执行时，Python 会自动调用：
#
# Dog.__init__(dog1, "小白", 3)
#
# 我们不用手动调用 __init__。
# 只要创建对象，它就会自动运行。

# 所以 __init__ 经常用来做初始化：
# 1. 保存路径
# 2. 保存数据
# 3. 读取文件
# 4. 设置初始状态


# ============================================================
# 8. class 版本：SimpleKeyFinder
# ============================================================

# 接下来写一个简化版 KeyFinder。
# 它先不读取 json，直接在代码里保存 keys。

# class SimpleKeyFinder:
#     def __init__(self):
#         self.keys = [
#             {"id": "1", "x": 40, "y": 50, "w": 34, "h": 30},
#             {"id": "2", "x": 80, "y": 50, "w": 34, "h": 30},
#             {"id": "3", "x": 120, "y": 50, "w": 34, "h": 30}
#         ]

#     def find_key(self, x, y):
#         for key in self.keys:
#             key_x = key["x"]
#             key_y = key["y"]
#             key_w = key["w"]
#             key_h = key["h"]

#             in_x_range = key_x <= x <= key_x + key_w
#             in_y_range = key_y <= y <= key_y + key_h

#             if in_x_range and in_y_range:
#                 return key["id"]

#         return None


# simple_key_finder = SimpleKeyFinder()

# print("57, 65 对应的 key：", simple_key_finder.find_key(57, 65))
# print("97, 65 对应的 key：", simple_key_finder.find_key(97, 65))
# print("10, 10 对应的 key：", simple_key_finder.find_key(10, 10))


# ============================================================
# 9. Why json？
# ============================================================

# 上面的 SimpleKeyFinder 有一个问题：
# keys 直接写死在 Python 代码里。
#
# 如果以后键盘布局变了，就要改 Python 代码。

# 所以我们把键盘布局放到 json 文件里：
#
# data/layouts/keyboard_number_v1.json
#
# Python 程序只负责读取这个 json 文件。
#
# 这样做的好处：
# 1. 代码负责逻辑
# 2. json 文件负责数据
# 3. 以后改键盘布局时，尽量只改 json，不改 Python 代码


# ============================================================
# 10. json 文件读取
# ============================================================

# Python 读取 json 文件需要先 import json。

import json
# a = 1
# file = "路径里的文件"
# 读取 json 的基本写法：
#
# with open("文件路径", "r") as file:
#     data = json.load(file)
#
# 这里：
# open(...) 表示打开文件
# "r" 表示 read，也就是读取
# json.load(file) 表示把 json 文件变成 Python 数据

# 注意：
# json 文件本身不是 Python dict。
# 但是 json.load(file) 之后，读出来的结果通常就是 Python 里的 dict / list。


# ============================================================
# 11. 练习：读取 layout json
# ============================================================
# TODO
def read_layout(path):
    with open(path,"r")as file:
        data =json.load(file)
    return(data)


data = read_layout("keyboard_number_v1.json")
print(data)


# ============================================================
# 12. 练习：读取 session json
# ============================================================

# 上面读取的是 layout json。
# layout 描述键盘长什么样。
#
# 接下来读取 session json。
# session 描述一段输入过程。

# session 大概长这样：
#
# {
#     "session_id": "test_number_input_123",
#     "layout_id": "keyboard_number_v1",
#     "unit": "mm",
#     "frames": [
#         {
#             "frame_id": 1,
#             "t": 0.0,
#             "fingers": {
#                 "1": {
#                     "x": 57,
#                     "y": 65
#                 }
#             }
#             "tap": {
#                 "candidate": -1
#             }
#         }
#     ]
# }

# TODO
def read_session(session_id):
    with open(session_id,"r")as file:
        data=json.load(file)
    return(data)
data = read_layout("test_number_input_123.json")
print(data)





# ============================================================
# 13. 练习：从 session 里读取所有 frame 的 candidate
# ============================================================

# 任务：
# 写一个函数 print_all_candidates(session)
#
# 它要做的事情：
# 1. 从 session 里取出 frames
# 2. 用 for 循环遍历 frames
# 3. 对每一个 frame，打印 frame_id 和 candidate

# TODO
def print_all_candidates(session):
    frames=session.get("frames")
    for frame in frames:
        print(frame["frame_id"])
        print(frame.get("tap").get("candidate"))
    
print_all_candidates(data)








# ============================================================
# 14. 完成 SessionSource
# ============================================================

# 接下来写 SessionSource。
#
# 它的作用：
# 1. 创建对象时读取 session json
# 2. 把整个 session 保存到对象里
# 3. 提供几个函数，让其他模块可以轻松拿到 session 里的数据

# TODO