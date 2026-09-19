# Step 5：生成实时 Frame

这一步，我们要把摄像头、手部识别和纸面定位的结果整理成统一的 `frame`。

这一步会创建两个新文件：

```text
components/frame_builder.py
programs/test_frame_builder.py
```

这一步对应完整项目中的数据整理部分：

```text
image + hand_data + homography -> frame
```

---

## 1. 理解这一节要生成的 frame

线上 replay 版本里，`frame` 是从 JSON 文件里读出来的。

线下实时版本里，`frame` 要由摄像头和识别程序实时生成。

`frame` 的格式会和线上版本一致，也就是：

```python
{
    "frame_id": 1,
    "t": 0.0,
    "fingers": {
        "1": {
            "x": 57.2,
            "y": 83.6
        }
    },
    "tap": {
        "candidate": -1
    }
}
```

字段含义：

```text
frame_id：当前是第几帧
t：从程序开始到现在经过了多少秒
fingers：每根手指在纸面坐标里的位置
tap.candidate：当前有没有输入候选手指
```

这一步还没有接声音或按钮，所以：

```text
candidate = -1
```

---

## 2. 新建 FrameBuilder

新建文件：

```text
components/frame_builder.py
```

代码：

```python
class FrameBuilder:
    def __init__(self, paper_mapper, hand_source, tap_source=None):
        # paper_mapper 负责纸面定位和坐标转换。
        self.paper_mapper = paper_mapper

        # hand_source 负责用 MediaPipe 识别手指位置。
        self.hand_source = hand_source

        # tap_source 负责判断有没有输入触发。
        # 这一步还没有接声音或按钮，所以可以是 None。
        self.tap_source = tap_source

    def build_frame(self, image, frame_id, t):
        # 先根据 ArUco marker 计算 homography。
        # homography 表示：图像坐标 -> 纸面坐标。
        homography, corners, ids = self.paper_mapper.get_homography(image)

        # 用 MediaPipe 识别手和指尖。
        hand_data, mediapipe_result = self.hand_source.process_image(image)

        # 默认没有可用的纸面手指坐标。
        fingers = {}

        # 只有成功识别纸面后，才能把指尖从图像坐标转换成纸面坐标。
        if homography is not None:
            fingers = self.build_fingers(hand_data, homography)

        # 这一步还没有声音或按钮输入，所以默认没有 candidate。
        candidate = -1

        # 接入 AudioSource / SerialTapSource 后，
        # 就从 tap_source 读取 candidate。
        if self.tap_source is not None:
            candidate = self.tap_source.get_candidate()

        # 生成和线上 replay 一样格式的 frame。
        frame = {
            "frame_id": frame_id,
            "t": t,
            "fingers": fingers,
            "tap": {
                "candidate": candidate
            }
        }

        # visual_data 只给调试显示用。
        # 它不会进入后面的输入判断逻辑。
        visual_data = {
            "homography": homography,
            "corners": corners,
            "ids": ids,
            "hand_data": hand_data,
            "mediapipe_result": mediapipe_result
        }

        return frame, visual_data

    def build_fingers(self, hand_data, homography):
        fingers = {}

        for fingertip in hand_data["fingertips"]:
            finger_id = fingertip["finger_id"]

            image_x = fingertip["image_x"]
            image_y = fingertip["image_y"]

            # 把摄像头画面里的指尖坐标转换成纸面 layout 坐标。
            paper_x, paper_y = self.paper_mapper.image_to_paper(
                image_x,
                image_y,
                homography
            )

            # 这里用字符串作为 key，是为了和 JSON 读出来的数据格式保持一致。
            fingers[str(finger_id)] = {
                "x": float(paper_x),
                "y": float(paper_y)
            }

        return fingers
```

---

## 3. 新建 FrameBuilder 测试程序

新建文件：

```text
programs/test_frame_builder.py
```

代码：

```python
import time

import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource
from components.paper_mapper import PaperMapper
from components.frame_builder import FrameBuilder


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    # 打开摄像头。
    camera = CameraSource(camera_id=0)

    # 创建手部识别对象。
    hand_source = MediaPipeHandSource(max_num_hands=1)

    # 创建纸面定位对象。
    paper_mapper = PaperMapper(layout_path)

    # 创建 FrameBuilder。
    # 它会把 hand_source 和 paper_mapper 的结果整理成 frame。
    frame_builder = FrameBuilder(
        paper_mapper,
        hand_source
    )

    frame_id = 0
    start_time = time.time()

    print("FrameBuilder 测试开始")
    print("请把纸面键盘放到摄像头画面里")
    print("按 q 退出")
    print("按 p 打印当前 frame")

    while True:
        # 读取一帧摄像头画面。
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        # 计算当前时间。
        t = time.time() - start_time

        # 根据当前画面生成 frame。
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

        # 画手部骨架。
        image = hand_source.draw_hand(image, mediapipe_result)

        # 画识别到的 ArUco marker。
        image = paper_mapper.draw_detected_markers(image, corners, ids)

        if homography is not None:
            # 画纸面边框。
            image = paper_mapper.draw_board_border(image, homography)

            # 画 layout 里的按键框。
            image = paper_mapper.draw_keys(image, homography)

            cv2.putText(
                image,
                "paper detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
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

        # 画指尖红点和 finger_id。
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - FrameBuilder Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("p"):
            print(frame)

        frame_id = frame_id + 1

    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("FrameBuilder 测试结束")


if __name__ == "__main__":
    main()
```

---

## 4. 修改 app.py 运行测试程序

把 `app.py` 暂时改成：

```python
from programs.test_frame_builder import main


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

运行后，把纸面键盘放到摄像头画面里，再把手伸到纸面键盘上方。

如果一切正常，应该看到：

```text
摄像头画面正常显示
手部骨架能显示
指尖红点和 finger_id 能显示
ArUco marker 被框出来
绿色边框贴合整张纸面
蓝色按键框贴合纸上的按键区域
按 p 可以打印当前 frame
按 q 可以退出
```

按 `p` 时，终端应该打印类似：

```python
{
    "frame_id": 120,
    "t": 4.23,
    "fingers": {
        "0": {"x": 53.1, "y": 120.4},
        "1": {"x": 82.7, "y": 94.2},
        "2": {"x": 103.5, "y": 88.9},
        "3": {"x": 124.6, "y": 91.3},
        "4": {"x": 145.2, "y": 105.7}
    },
    "tap": {
        "candidate": -1
    }
}
```

如果没有识别到纸面，`fingers` 会是空的：

```python
"fingers": {}
```

这是正常的，因为没有 `homography` 时，程序不能把图像坐标转换成纸面坐标。
