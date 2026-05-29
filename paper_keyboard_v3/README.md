# Paper Keyboard V3

Paper Keyboard V3 是一个基于纸面键盘、摄像头、手部识别和敲击检测的虚拟键盘项目。

当前版本使用：

* ArUco marker 识别纸面键盘位置
* Homography 将摄像头像素坐标转换成纸面坐标
* MediaPipe 识别双手指尖
* 麦克风音量检测判断敲击
* `FrameBuilder` 生成统一 frame
* `InputDecider` 判断是否产生输入
* `TextBuffer` 保存当前文本
* `SessionWriter` 保存输入过程
* `DirectInput` 可选地把结果直接输入到电脑当前光标位置

项目目标不是做一个商业级键盘，而是做一个结构清晰、方便教学、方便后续替换输入方案的完整 Python 项目。

后续可以把 MediaPipe、AudioSource 替换成彩色贴纸、指套按钮、ESP32、手套或其他传感器方案，只要最终仍然生成统一 frame 格式，后面的输入判断和保存逻辑就可以继续复用。

---

## 1. 当前功能

当前版本支持：

1. 生成纸面数字键盘图片
2. 通过摄像头识别纸面键盘
3. 识别右手食指位置
4. 判断右手食指当前指向哪个数字键
5. 通过敲击纸面触发输入
6. 在窗口中显示当前输入文本
7. 保存输入过程为 session JSON
8. 回放 session 并还原输入结果
9. 可选开启 Direct Input，将输入结果直接打到电脑当前文本框中

---

## 2. 推荐环境

推荐使用：

```bash
Python 3.11
```

不建议使用 Python 3.14。当前项目使用的是 MediaPipe legacy `mp.solutions.hands` 接口，在 Python 3.14 环境中可能出现：

```text
AttributeError: module 'mediapipe' has no attribute 'solutions'
```

因此当前稳定方案是使用 Python 3.11。

---

## 3. 安装依赖

建议使用 conda 创建独立环境：

```bash
conda create -n paper_keyboard python=3.11
conda activate paper_keyboard
```

安装依赖：

```bash
python -m pip install numpy
python -m pip install opencv-contrib-python
python -m pip install mediapipe
python -m pip install sounddevice
python -m pip install pynput
```

依赖说明：

```text
numpy:
    数组和坐标计算

opencv-contrib-python:
    摄像头读取、ArUco marker、图像绘制

mediapipe:
    手部关键点识别

sounddevice:
    麦克风音量检测

pynput:
    Direct Input，直接向电脑当前光标位置输入字符
```

---

## 4. macOS 权限

首次运行时，macOS 可能会要求摄像头和麦克风权限。

Direct Input 还需要辅助功能权限。开启方式：

```text
系统设置
隐私与安全性
辅助功能
给 Terminal / VS Code / Python 打开权限
```

没有辅助功能权限时，程序仍然可以在窗口中显示输入文本，但可能无法直接向其他软件输入字符。

---

## 5. 项目结构

```text
paper_keyboard_v3/
    app.py

    components/
        frame_builder.py
        frame_tools.py
        input_decider.py
        key_finder.py
        paper_mapper.py
        session_writer.py
        text_buffer.py
        visual_overlay.py
        direct_input.py

    input_sources/
        audio_source.py
        camera_source.py
        manual_source.py
        mediapipe_hand_source.py
        session_source.py

    programs/
        main.py
        preview_layout.py
        generate_session.py
        replay_session.py
        test_single_finger_mapping.py

    data/
        layouts/
            keyboard_number_v1.json

        sessions/
            test_number_input_123.json

        generated/
            keyboard_number_v1.png
            manual_input_12345.json
            vision_session_*.json
```

---

## 6. 核心数据格式

项目的核心数据是 frame。

一个 frame 表示某一时刻的输入状态：

```json
{
  "frame_id": 1,
  "t": 0.033,
  "fingers": [
    {
      "finger_id": 1,
      "x": 132.4,
      "y": 78.6
    }
  ],
  "tap": {
    "candidate": 1
  }
}
```

字段含义：

```text
frame_id:
    当前是第几帧

t:
    当前时间，单位是秒

fingers:
    当前识别到的手指列表

finger_id:
    手指编号

x, y:
    手指在纸面坐标系中的位置，单位和 layout 一致

tap.candidate:
    当前触发输入的手指
```

当前 finger_id 规则：

```text
右手：
0 = 拇指
1 = 食指
2 = 中指
3 = 无名指
4 = 小指

左手：
5 = 拇指
6 = 食指
7 = 中指
8 = 无名指
9 = 小指
```

当前基础版中：

```text
tap.candidate = -1:
    没有输入触发

tap.candidate = 1:
    右手食指触发输入
```

未来如果换成指套、手套或硬件按钮，`tap.candidate` 可以扩展成 `-1` 到 `9`。

---

## 7. 生成纸面键盘图片

运行：

```bash
python app.py
```

将 `app.py` 中的入口切换成：

```python
from programs.preview_layout import main as current_program_main
```

运行后会生成：

```text
data/generated/keyboard_number_v1.png
```

将图片打印出来后，放在摄像头下方使用。

注意：

```text
打印时尽量不要缩放图片。
纸面上的 ArUco marker 应该保持清晰、完整、正方形。
```

---

## 8. 运行主程序

将 `app.py` 中的入口切换成：

```python
from programs.main import main as current_program_main
```

运行：

```bash
python app.py
```

主程序会打开摄像头窗口。

操作方式：

```text
敲击纸面：
    输入当前右手食指指向的按键

o：
    开启 / 关闭 Direct Input

s：
    保存当前 session

c：
    清空当前显示文本

q：
    退出程序
```

窗口左上角会显示：

```text
Text: 当前输入文本
Direct Input: ON / OFF
```

Direct Input 关闭时，输入结果只显示在程序窗口中。

Direct Input 开启时，输入结果会同时打到电脑当前光标所在的文本框中。

---

## 9. 测试单指映射

这个程序只测试视觉映射，不测试音频输入。

将 `app.py` 中的入口切换成：

```python
from programs.test_single_finger_mapping import main as current_program_main
```

运行：

```bash
python app.py
```

功能：

```text
识别纸面键盘
识别右手食指
显示右手食指当前指向的按键
```

这个测试适合用于排查：

```text
ArUco 是否识别成功
Homography 是否正确
按键投影是否对齐
MediaPipe 是否正确识别右手食指
KeyFinder 是否能正确找到按键
```

如果这个测试不能正确高亮按键，说明问题在视觉映射链路。

如果这个测试正常，但主程序不能输入，问题更可能在 AudioSource、InputDecider 或 DirectInput。

---

## 10. 生成模拟 session

将 `app.py` 中的入口切换成：

```python
from programs.generate_session import main as current_program_main
```

运行：

```bash
python app.py
```

这个程序不使用摄像头和麦克风，而是通过 `ManualSource` 生成模拟输入。

默认会生成：

```text
data/generated/manual_input_12345.json
```

这个文件可以用于测试 session 回放逻辑。

---

## 11. 回放 session

将 `app.py` 中的入口切换成：

```python
from programs.replay_session import main as current_program_main
```

运行：

```bash
python app.py
```

默认回放路径在 `programs/replay_session.py` 中设置：

```python
session_path = "data/generated/manual_input_12345.json"
```

要回放其他 session，直接手动修改这个路径。

回放流程：

```text
SessionSource 读取 frame
KeyFinder 判断候选手指在哪个按键
InputDecider 判断是否产生输入
TextBuffer 还原最终文本
```

---

## 12. 主要组件说明

### FrameBuilder

位置：

```text
components/frame_builder.py
```

职责：

```text
汇总 PaperMapper、MediaPipeHandSource、tap_source 的结果
生成统一 frame
生成 visual_data 给显示层使用
```

它不负责：

```text
判断按键
判断输入
保存文本
显示画面
```

---

### PaperMapper

位置：

```text
components/paper_mapper.py
```

职责：

```text
读取 layout
识别 ArUco marker
计算 Homography
把图像坐标转换成纸面坐标
```

---

### MediaPipeHandSource

位置：

```text
input_sources/mediapipe_hand_source.py
```

职责：

```text
识别双手
提取十个指尖的图像坐标
分配 finger_id
```

---

### AudioSource

位置：

```text
input_sources/audio_source.py
```

职责：

```text
监听麦克风音量
检测敲击
输出 candidate
```

当前规则：

```text
没有敲击 -> -1
检测到敲击 -> 1
```

---

### InputDecider

位置：

```text
components/input_decider.py
```

职责：

```text
判断当前 frame 是否产生一次有效输入
```

核心逻辑：

```text
上一帧 candidate = -1
当前帧 candidate != -1
并且候选手指当前在某个按键上
=> 产生一次输入
```

这样可以避免一次敲击持续多帧时重复输入。

---

### TextBuffer

位置：

```text
components/text_buffer.py
```

职责：

```text
保存当前输入文本
支持添加按键
支持删除最后一个字符
支持清空文本
```

---

### SessionWriter

位置：

```text
components/session_writer.py
```

职责：

```text
把 frames 组装成 session
保存成 JSON 文件
```

---

### DirectInput

位置：

```text
components/direct_input.py
```

职责：

```text
将确认后的 key_id 直接输入到电脑当前焦点位置
```

默认应该关闭，避免误触发。

---

### VisualOverlay

位置：

```text
components/visual_overlay.py
```

职责：

```text
把识别结果画到摄像头画面上
```

当前显示：

```text
ArUco marker 框
纸面边框
按键框
当前按键高亮
手骨架
指尖编号
Text
Direct Input 状态
```

---

## 13. 常见问题

### 摄像头打不开

检查 `camera_id`。

常见情况：

```text
0: Mac 自带摄像头
1: 外接摄像头
```

相关文件：

```text
programs/main.py
programs/test_single_finger_mapping.py
input_sources/camera_source.py
```

---

### 画面很暗

部分 USB 摄像头在 macOS 上可能存在兼容性问题。可以尝试：

```text
换 USB Hub
换摄像头
换 Windows 电脑运行
在 Mac 上写代码，在 Windows 上运行测试
```

---

### ArUco marker 识别不到

检查：

```text
纸面是否完整进入画面
marker 是否清晰
marker 是否被手遮挡
打印时是否缩放过
摄像头是否过暗或过曝
opencv-contrib-python 是否安装成功
```

---

### 手指左右识别反了

修改：

```python
MediaPipeHandSource(swap_hands=True)
```

或：

```python
MediaPipeHandSource(swap_hands=False)
```

具体值需要根据摄像头方向和是否镜像显示来测试。

---

### 敲击没有反应

检查 `AudioSource` 的阈值：

```python
threshold=0.04
```

如果检测不到敲击，可以调低：

```python
threshold=0.02
```

如果太容易误触发，可以调高：

```python
threshold=0.06
```

---

### Direct Input 没有真实输入

检查 macOS 辅助功能权限：

```text
系统设置
隐私与安全性
辅助功能
给 Terminal / VS Code / Python 打开权限
```

同时确认程序中 Direct Input 已经打开：

```text
Direct Input: ON
```

---

### Python 3.14 报 MediaPipe 错误

当前项目不推荐 Python 3.14。

推荐使用：

```bash
conda create -n paper_keyboard python=3.11
conda activate paper_keyboard
```

然后重新安装依赖。

---

## 14. 当前建议开发路线

当前版本已经完成基础闭环：

```text
纸面键盘生成
纸面定位
手指识别
敲击触发
输入判断
文本显示
session 保存
session 回放
Direct Input
```

后续可扩展方向：

```text
1. 增加录制开关，而不是从程序启动开始一直记录
2. 增加音频阈值实时调整
3. 增加调试显示开关
4. 替换 MediaPipe 为彩色贴纸识别
5. 替换 AudioSource 为指套按钮或 ESP32 串口输入
6. 扩展到多指输入
7. 扩展到完整字母键盘
```

项目当前最重要的设计原则是：

```text
输入源可以替换
frame 格式保持稳定
InputDecider 和 session 回放逻辑尽量复用
```
