# Paper Keyboard v2 - Input Engine 教学版

这个版本只关注一件事：

```text
读取 session JSON
逐帧处理数据
判断是否输入了一个按键
输出最终文本
```

它暂时不包含摄像头、麦克风、OpenCV、MediaPipe、ArUco marker。
这些真实传感器部分以后再接回来。

---

## 目录结构

```text
paper_keyboard_v2/
  app/
    replay_session_demo.py
  core/
    input_engine.py
  data/
    layouts/
      keyboard_number_v2.json
    sessions/
      example_tap_only_session.json
      example_continuous_session.json
```

---

## 怎么运行

在 `paper_keyboard_v2` 目录下运行：

```bash
python app/replay_session_demo.py
```

预期输出类似：

```text
Replay started
Layout: keyboard_number_v2
Session: paper_keyboard_session_v1
------------------------
frame 2 time 0.033 pressed 2 output = 2
frame 6 time 0.333 pressed 4 output = 24
frame 9 time 0.633 pressed 0 output = 240
------------------------
Final output: 240
```

---

## InputEngine 的核心逻辑

当前规则非常简单：

```text
1. 找到这一帧的食指坐标
2. 判断食指坐标在哪个按键范围内
3. 如果这一帧 tap.audio == true，就确认输入这个按键
4. 如果连续多帧 tap.audio == true，只输出一次，避免重复输入
```

这个版本故意不做复杂准确率优化。
教学重点是让学生理解：

```text
输入数据 frame
↓
判断当前 key
↓
判断是否 tap
↓
输出字符
```

---

## 第一节课可以怎么讲

第一步：只用 `example_tap_only_session.json`。

学生只需要理解：

```text
每一帧都是一次按下
坐标落在哪个 key 里，就输出哪个 key
```

第二步：切换到 `example_continuous_session.json`。

学生需要理解：

```text
不是每一帧都应该输出
只有 tap.audio == true 时才输出
连续几帧 audio=true 时不能重复输出
```

---

## 学生最适合改哪里

主要改：

```text
core/input_engine.py
```

尤其是：

```python
def update(self, frame):
```

这里就是系统的“判断大脑”。
