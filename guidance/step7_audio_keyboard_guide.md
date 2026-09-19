# Step 7：声音音量输入

这一步，我们要把前面的“当前 key 高亮”升级成真正输入。

这一步会创建两个新文件：

```text
input_sources/audio_source.py
programs/audio_keyboard.py
```

这一步对应完整项目中的输入触发部分：

```text
current_key + audio volume -> text
```

视觉负责判断食指当前在哪个按键上，声音负责判断这一次是否真的触发输入。

---

## 1. 安装 sounddevice

这一步需要用 `sounddevice` 读取麦克风声音。

macOS：

```bash
python3 -m pip install sounddevice
```

Windows：

```bash
python -m pip install sounddevice
```

或者：

```bash
py -m pip install sounddevice
```

---

## 2. 新建 AudioSource

新建文件：

```text
input_sources/audio_source.py
```

代码：

```python
import time

import numpy as np
import sounddevice as sd


class AudioSource:
    def __init__(
        self,
        threshold=0.04,
        cooldown=0.25,
        samplerate=44100,
        blocksize=1024,
        candidate_id=1
    ):
        # threshold 是音量阈值。
        # 声音音量超过这个值时，认为可能发生了一次敲击。
        self.threshold = threshold

        # cooldown 是冷却时间。
        # 一次触发之后，短时间内不要重复触发。
        self.cooldown = cooldown

        # 麦克风采样参数。
        self.samplerate = samplerate
        self.blocksize = blocksize

        # 声音输入暂时只对应食指。
        # candidate_id = 1 表示这次输入由 1 号手指触发。
        self.candidate_id = candidate_id

        # 当前音量，用来显示和调试。
        self.current_rms = 0.0

        # 上一次触发的时间，用来做 cooldown。
        self.last_trigger_time = 0.0

        # 等待主程序读取的 candidate。
        # -1 表示当前没有新的输入触发。
        self.pending_candidate = -1

        # 创建麦克风输入流。
        # audio_callback 会在后台不断收到声音数据。
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=self.audio_callback
        )

    def audio_callback(self, indata, frames, time_info, status):
        # 如果麦克风流有异常状态，打印出来方便调试。
        if status:
            print(status)

        # indata 是这一小段声音数据。
        # channels=1，所以这里只取第 0 个声道。
        audio = indata[:, 0]

        # RMS 可以理解成这一小段声音的音量大小。
        rms = np.sqrt(np.mean(audio * audio))
        self.current_rms = rms

        now = time.time()

        # 如果音量超过阈值，并且距离上一次触发已经过了 cooldown，
        # 就记录一次新的 candidate。
        if rms > self.threshold:
            if now - self.last_trigger_time > self.cooldown:
                self.pending_candidate = self.candidate_id
                self.last_trigger_time = now

    def start(self):
        # 开始监听麦克风。
        self.stream.start()

    def stop(self):
        # 停止并关闭麦克风输入流。
        self.stream.stop()
        self.stream.close()

    def get_candidate(self):
        # 主程序每一帧会调用这个函数读取 candidate。
        # 读完后立刻重置成 -1，避免一次声音被重复使用。
        candidate = self.pending_candidate
        self.pending_candidate = -1
        return candidate

    def get_volume(self):
        # 返回当前音量，方便显示和调参。
        return self.current_rms
```

---

## 3. 新建声音输入纸面键盘程序

新建文件：

```text
programs/audio_keyboard.py
```

代码：

```python
import time

import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource
from input_sources.audio_source import AudioSource

from components.paper_mapper import PaperMapper
from components.frame_builder import FrameBuilder
from components.key_finder import KeyFinder
from components.input_decider import InputDecider
from components.text_buffer import TextBuffer
from components.frame_tools import get_candidate
from components.frame_tools import get_finger_position_by_id


def get_current_key(frame, key_finder):
    # 当前声音版只看食指，继续取 finger_id = 1。
    position = get_finger_position_by_id(frame, 1)

    if position is None:
        return None

    x, y = position

    # KeyFinder 根据纸面坐标判断这个点在哪个 key 里。
    key_id = key_finder.find_key(x, y)

    return key_id


def handle_input(frame, input_decider, key_finder, text_buffer):
    # 从 frame 里读取 candidate。
    # 声音超过阈值时，AudioSource 会让 candidate 变成 1。
    candidate = get_candidate(frame)

    # InputDecider 判断这个 candidate 是不是一次新的触发。
    input_finger_id = input_decider.decide_candidate(candidate)

    if input_finger_id is None:
        return None

    # 声音版目前只支持食指输入。
    if input_finger_id != 1:
        return None

    # 触发输入时，输入食指当前所在的 key。
    input_key_id = get_current_key(frame, key_finder)

    if input_key_id is None:
        return None

    text_buffer.add_char(input_key_id)

    return input_key_id


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    # 打开摄像头。
    camera = CameraSource(camera_id=0)

    # 创建手部识别对象。
    hand_source = MediaPipeHandSource(max_num_hands=1)

    # 创建纸面定位对象。
    paper_mapper = PaperMapper(layout_path)

    # 创建 KeyFinder。
    key_finder = KeyFinder(layout_path)

    # 创建声音输入对象。
    audio_source = AudioSource(
        threshold=0.04,
        cooldown=0.25,
        candidate_id=1
    )

    # 创建 FrameBuilder。
    # 这次传入 audio_source，所以 frame 里的 candidate 会来自声音输入。
    frame_builder = FrameBuilder(
        paper_mapper,
        hand_source,
        audio_source
    )

    # InputDecider 用来避免同一次声音触发被重复输入。
    input_decider = InputDecider()

    # TextBuffer 保存最终输入出来的文本。
    text_buffer = TextBuffer()

    frame_id = 0
    start_time = time.time()

    print("声音输入纸面键盘开始")
    print("请把纸面键盘放到摄像头画面里")
    print("把食指放到某个 key 上，然后敲击纸面")
    print("按 q 退出")
    print("按 p 打印当前 frame")

    # 开始监听麦克风。
    audio_source.start()

    while True:
        # 读取一帧摄像头画面。
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        # 计算当前时间。
        t = time.time() - start_time

        # 根据当前画面和声音输入生成 frame。
        frame, visual_data = frame_builder.build_frame(
            image,
            frame_id,
            t
        )

        # 从 visual_data 里取出调试显示需要的数据。
        homography = visual_data["homography"]
        corners = visual_data["corners"]
        ids = visual_data["ids"]
        hand_data = visual_data["hand_data"]
        mediapipe_result = visual_data["mediapipe_result"]

        # 根据食指当前位置判断当前 key。
        current_key = get_current_key(frame, key_finder)

        # 如果这一帧有声音触发，就尝试输入当前 key。
        input_key = handle_input(
            frame,
            input_decider,
            key_finder,
            text_buffer
        )

        if input_key is not None:
            print("输入：", input_key)
            print("当前文本：", text_buffer.get_text())

        # 画识别到的 ArUco marker。
        image = paper_mapper.draw_detected_markers(image, corners, ids)

        if homography is not None:
            # 画纸面边框。
            image = paper_mapper.draw_board_border(image, homography)

            # 画 layout 里的按键框。
            image = paper_mapper.draw_keys(image, homography)

            # 高亮食指当前所在的 key。
            image = paper_mapper.draw_key_highlight(
                image,
                homography,
                current_key
            )

            cv2.putText(
                image,
                "current key: " + str(current_key),
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 255),
                2
            )
        else:
            cv2.putText(
                image,
                "paper not detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2
            )

        # 显示当前文本。
        cv2.putText(
            image,
            "text: " + text_buffer.get_text(),
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2
        )

        # 显示当前音量，方便调整 threshold。
        cv2.putText(
            image,
            "volume: " + str(round(audio_source.get_volume(), 3)),
            (30, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2
        )

        # 画手部骨架和指尖编号。
        image = hand_source.draw_hand(image, mediapipe_result)
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - Audio Keyboard", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("p"):
            print(frame)

        frame_id = frame_id + 1

    audio_source.stop()
    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("声音输入纸面键盘结束")


if __name__ == "__main__":
    main()
```

---

## 4. 修改 app.py 运行测试程序

把 `app.py` 暂时改成：

```python
from programs.audio_keyboard import main


main()
```

然后运行。

macOS：

```bash
python3 app.py
```

Windows：

```bash
python app.py
```

或者：

```bash
py app.py
```

---

## 5. 成功标准

运行后，把纸面键盘放到摄像头画面里，再把食指移动到不同按键上方。

如果一切正常，应该看到：

```text
摄像头画面正常显示
ArUco marker 被框出来
绿色边框贴合整张纸面
蓝色按键框贴合纸上的按键区域
手部骨架能显示
指尖红点和 finger_id 能显示
食指移动到某个按键上方时，这个按键被黄色框高亮
左上角显示 current key
画面上显示当前 text
画面上显示当前 volume
按 p 可以打印当前 frame
按 q 可以退出
```

测试时可以重点看：

```text
食指放到 1 上，敲击纸面，输入 1
食指放到 5 上，敲击纸面，输入 5
食指移出按键区域，敲击纸面，不输入
声音太小时不输入
```

---

## 6. 调整参数

如果太容易误触，可以把阈值调大：

```python
threshold=0.06
```

如果敲击没有反应，可以把阈值调小：

```python
threshold=0.025
```

如果一次敲击输入多次，可以把冷却时间调大：

```python
cooldown=0.4
```

这一步完成后，程序已经能做到：

```text
视觉判断食指当前在哪个 key 上
声音音量判断是否触发输入
TextBuffer 保存输入结果
```
