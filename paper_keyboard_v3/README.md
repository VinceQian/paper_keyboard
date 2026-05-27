# Paper Keyboard V3

Paper Keyboard V3 是一个纸面键盘输入系统。

项目目标是：通过摄像头、麦克风或其他传感器采集用户在纸面键盘上的敲击行为，并将其转换为可识别的按键输入。

本版本的核心设计目标是：

```text
传感器方案可以替换，但后续判断逻辑尽量保持稳定。
```

也就是说，无论最终使用顶部摄像头、彩色指甲贴、麦克风、侧面摄像头，还是其他硬件传感器，输入层都需要先把原始数据整理成统一的 `frame` 格式，然后交给后续模块处理。

---

## 项目结构

```text
paper_keyboard_v3/
  README.md
  requirements.txt

  app/
    main.py
    replay_session.py
    record_session.py

  input_sources/
    camera_source.py
    audio_source.py
    color_marker_source.py
    session_source.py
    manual_source.py

  components/
    key_finder.py
    frame_tools.py
    input_decider.py
    text_buffer.py

  data/
    layouts/
    sessions/
    generated/

  docs/

  project_logs/

  practice/
```

---

## 目录说明

### `app/`

`app/` 存放可以直接运行的程序入口。

主要文件：

```text
app/main.py
app/replay_session.py
app/record_session.py
```

说明：

- `main.py`：主程序入口。
- `replay_session.py`：读取已经保存好的 session JSON，并回放输入过程。
- `record_session.py`：接入真实传感器后，用来录制 session JSON。

---

### `input_sources/`

`input_sources/` 存放不同输入来源的代码。

这一层负责把不同输入方案采集到的原始数据转换成统一的 `frame` 格式。

可能包含：

```text
input_sources/camera_source.py
input_sources/audio_source.py
input_sources/color_marker_source.py
input_sources/session_source.py
input_sources/manual_source.py
```

说明：

- `camera_source.py`：摄像头输入。
- `audio_source.py`：麦克风输入。
- `color_marker_source.py`：彩色贴纸或颜色标记输入。
- `session_source.py`：从已有 session JSON 读取输入。
- `manual_source.py`：手动创建测试 frame。

如果后续更换传感器方案，主要应该修改这一层。

---

### `components/`

`components/` 存放和具体传感器无关的功能组件。

这里的代码只处理已经整理好的数据，不直接依赖摄像头、麦克风或具体硬件。

主要文件：

```text
components/key_finder.py
components/frame_tools.py
components/input_decider.py
components/text_buffer.py
```

说明：

- `key_finder.py`：根据手指坐标判断它在哪个按键里。
- `frame_tools.py`：从 frame 中取出常用信息。
- `input_decider.py`：根据 frame 和 layout 判断是否应该输出按键。
- `text_buffer.py`：管理最终输出文本。

---

### `data/`

`data/` 存放项目数据。

```text
data/
  layouts/
  sessions/
  generated/
```

说明：

- `data/layouts/`：存放键盘布局 JSON。
- `data/sessions/`：存放输入过程 session JSON。
- `data/generated/`：存放自动生成的文件，例如录制结果、调试输出等。

---

### `docs/`

`docs/` 存放项目说明、设计笔记和任务文档。

---

### `project_logs/`

`project_logs/` 存放项目日志或开发记录。

这里不是程序自动生成的运行日志，而是人工记录项目进展、问题和总结的地方。

---

### `practice/`

`practice/` 存放练习代码和临时测试代码。

这里的代码不一定是正式项目代码。

---

## layout 数据格式

layout 用来记录纸面键盘上每个按键的位置和大小。

示例：

```json
{
  "layout_id": "keyboard_number_v1",
  "unit": "mm",
  "keys": [
    {
      "label": "1",
      "x": 20,
      "y": 20,
      "w": 20,
      "h": 22
    },
    {
      "label": "2",
      "x": 43,
      "y": 20,
      "w": 20,
      "h": 22
    }
  ]
}
```

字段说明：

- `layout_id`：键盘布局编号。
- `unit`：坐标单位。
- `keys`：按键列表。
- `label`：按键输出字符。
- `x`：按键左上角 x 坐标。
- `y`：按键左上角 y 坐标。
- `w`：按键宽度。
- `h`：按键高度。

每个按键可以看作一个矩形。

判断手指是否在某个按键里，本质上就是判断一个点是否落在这个矩形范围内。

---

## session 数据格式

session 用来记录一次输入过程。

一个 session 由很多 frame 组成。

示例：

```json
{
  "schema_version": "paper_keyboard_session_v1",
  "layout_id": "keyboard_number_v1",
  "time_unit": "seconds",
  "frames": [
    {
      "frame_id": 1,
      "t": 0.000,
      "fingers": [
        {
          "finger_id": 1,
          "x": 50,
          "y": 30
        }
      ],
      "tap": {
        "audio": true
      }
    }
  ]
}
```

字段说明：

- `schema_version`：session 文件格式版本。
- `layout_id`：当前 session 对应的键盘布局。
- `time_unit`：时间单位。
- `frames`：帧列表。
- `frame_id`：帧编号。
- `t`：当前帧时间。
- `fingers`：当前帧中检测到的手指。
- `finger_id`：手指编号。
- `x`：手指在纸面上的 x 坐标。
- `y`：手指在纸面上的 y 坐标。
- `tap.audio`：当前帧是否检测到敲击声音。

后续如果支持多指输入，可以让 `fingers` 中出现多个 finger：

```json
"fingers": [
  {
    "finger_id": 1,
    "x": 50,
    "y": 30
  },
  {
    "finger_id": 2,
    "x": 80,
    "y": 30
  }
]
```

---

## 核心数据流

项目的核心数据流如下：

```text
原始输入
↓
input_sources 整理成统一 frame
↓
components 处理 frame 和 layout
↓
判断是否产生按键输入
↓
更新输出文本
```

更具体地说：

```text
传感器 / session / 手动测试数据
↓
frame
↓
key_finder 判断手指在哪个 key 里
↓
input_decider 判断是否确认输入
↓
text_buffer 更新输出文本
```

---

## 基础判断逻辑

基础版有效输入需要两个条件：

```text
手指在某个按键范围内
并且
tap.audio 为 true
```

也就是说：

```text
手指在按键上，但 audio=false → 不输出
audio=true，但手指不在任何按键上 → 不输出
手指在按键上，并且 audio=true → 输出对应按键
```

---

## 运行方式

运行主程序：

```bash
python -m app.main
```

回放已保存的 session：

```bash
python -m app.replay_session
```

录制新的 session：

```bash
python -m app.record_session
```

如果系统使用 `python3`：

```bash
python3 -m app.main
```

---

## 后续扩展方向

后续可以逐步加入：

- 实时摄像头输入
- 麦克风敲击检测
- session 录制
- session 回放
- layout JSON 读取
- 按键命中判断
- tap 确认输入
- 防重复输入
- 文本输出管理
- 彩色贴纸识别
- 多指输入
- 侧面摄像头辅助
- 其他硬件传感器输入

---

## 设计原则

本项目的设计原则是：

```text
传感器输入和判断逻辑分离。
```

也就是说：

```text
input_sources 可以改变
frame 格式尽量稳定
components 尽量复用
app 负责组织运行流程
```

这样即使后续更换传感器方案，也尽量只需要修改输入层，而不需要重写整个项目。