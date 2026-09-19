# Step 6：单指按键识别与高亮

这一步，我们要判断食指当前落在哪个按键区域里，并在摄像头画面上高亮这个按键。

这一步会修改一个已有文件，并创建一个新文件：

```text
components/paper_mapper.py
programs/test_single_finger_mapping.py
```

这一步对应完整项目中的按键识别部分：

```text
frame + layout JSON -> current_key
```

---

## 1. 理解这一步要做什么

Step 5 里，我们已经可以生成这样的 `frame`：

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

这里的：

```text
fingers["1"]
```

表示食指在纸面坐标里的位置。

这一步要做的事情是：

```text
取出 fingers["1"]
↓
拿到食指的纸面坐标 x, y
↓
交给 KeyFinder
↓
判断当前在哪个 key 里
↓
在画面上高亮这个 key
```

---

## 2. 在 PaperMapper 里加入按键高亮函数

打开文件：

```text
components/paper_mapper.py
```

在 `draw_keys` 后面加入这个函数：

```python
    def draw_key_highlight(self, image, homography, key_id):
        # 如果当前没有 key，就不需要画高亮。
        if key_id is None:
            return image

        # 从 layout 里找到 id 等于 key_id 的按键。
        target_key = None

        for key in self.layout["keys"]:
            if key["id"] == key_id:
                target_key = key
                break

        # 如果 layout 里找不到这个 key，也不画高亮。
        if target_key is None:
            return image

        x = target_key["x"]
        y = target_key["y"]
        w = target_key["w"]
        h = target_key["h"]

        # key 在纸面坐标里的四个角。
        paper_corners = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

        image_corners = []

        # 把 key 的四个角从纸面坐标转换回图像坐标。
        # 这样才能把高亮框画在摄像头画面里。
        for paper_x, paper_y in paper_corners:
            image_x, image_y = self.paper_to_image(
                paper_x,
                paper_y,
                homography
            )

            image_corners.append([int(image_x), int(image_y)])

        points = np.array(
            image_corners,
            dtype=np.int32
        )

        # 用黄色粗线高亮当前 key。
        cv2.polylines(
            image,
            [points],
            True,
            (0, 255, 255),
            5
        )

        return image
```

---

## 3. 新建单指按键识别测试程序

新建文件：

```text
programs/test_single_finger_mapping.py
```

代码：

```python
import time

import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource

from components.paper_mapper import PaperMapper
from components.frame_builder import FrameBuilder
from components.key_finder import KeyFinder
from components.frame_tools import get_finger_position_by_id


def get_current_key(frame, key_finder):
    # 这一步先只看食指。
    # 我们项目里 finger_id = 1 表示食指。
    position = get_finger_position_by_id(frame, 1)

    if position is None:
        return None

    x, y = position

    # KeyFinder 根据纸面坐标判断这个点在哪个 key 里。
    key_id = key_finder.find_key(x, y)

    return key_id


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    # 打开摄像头。
    camera = CameraSource(camera_id=0)

    # 创建手部识别对象。
    hand_source = MediaPipeHandSource(max_num_hands=1)

    # 创建纸面定位对象。
    paper_mapper = PaperMapper(layout_path)

    # 创建 KeyFinder。
    # 它会读取 layout JSON 里的 keys，用来判断坐标落在哪个按键里。
    key_finder = KeyFinder(layout_path)

    # 创建 FrameBuilder。
    frame_builder = FrameBuilder(
        paper_mapper,
        hand_source
    )

    frame_id = 0
    start_time = time.time()

    print("单指按键识别测试开始")
    print("请把纸面键盘放到摄像头画面里")
    print("移动食指，观察当前 key 是否高亮")
    print("按 q 退出")
    print("按 p 打印当前 frame 和 current_key")

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

        # 根据食指当前位置判断当前 key。
        current_key = get_current_key(frame, key_finder)

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

        # 画手部骨架和指尖编号。
        image = hand_source.draw_hand(image, mediapipe_result)
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - Single Finger Mapping Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("p"):
            print(frame)
            print("current_key:", current_key)

        frame_id = frame_id + 1

    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("单指按键识别测试结束")


if __name__ == "__main__":
    main()
```

---

## 4. 修改 app.py 运行测试程序

把 `app.py` 暂时改成：

```python
from programs.test_single_finger_mapping import main


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
按 p 可以打印当前 frame 和 current_key
按 q 可以退出
```

测试时可以重点看：

```text
食指放到 1 上，高亮 1
食指放到 5 上，高亮 5
食指移出按键区域，current key 变成 None
移动或旋转纸张后，高亮框仍然跟着纸面移动
```

这一步完成后，程序已经能判断：

```text
食指当前在哪个按键上
```

后面接入声音输入时，就可以改成：

```text
只有检测到声音触发时，才输入当前 key
```
