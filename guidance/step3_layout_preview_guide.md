# Step 3：纸面键盘 Layout 预览

这一步，我们要设计一张纸面键盘，可以使用实时预览程序来帮助我们设计。

这一步会创建两个新文件：

```text
data/layouts/keyboard_number_v1.json
programs/preview_layout.py
```

这一步对应完整项目中的纸面设计部分：

```text
layout JSON -> keyboard image
```

也就是：我们先用 JSON 描述纸面键盘长什么样，再用程序把它渲染成一张可以显示、保存、打印的键盘图。

---

## 0. 安装 numpy

这一步需要用 numpy 进行矩阵运算。

macOS：

```bash
python3 -m pip install numpy
```

Windows：

```bash
python -m pip install numpy
```

或者：

```bash
py -m pip install numpy
```

---

## 1. 确认 OpenCV 支持 ArUco

这一步需要用 OpenCV 生成 ArUco marker。

ArUco marker 可以理解成一种黑白定位标记。摄像头看到这些标记后，后面的程序就能判断：

```text
这张纸在画面里的位置
这张纸有没有旋转
这张纸的四个角大概在哪里
```

先检查当前 OpenCV 有没有 `aruco` 模块。

macOS：

```bash
python3 -c "import cv2; print(hasattr(cv2, 'aruco'))"
```

Windows：

```bash
python -c "import cv2; print(hasattr(cv2, 'aruco'))"
```

如果输出是：

```text
True
```

可以直接继续。

如果输出是：

```text
False
```

安装 OpenCV contrib 版本。

macOS：

```bash
python3 -m pip install opencv-contrib-python
```

Windows：

```bash
python -m pip install opencv-contrib-python
```

如果 Windows 上 `python` 不可用，可以试：

```bash
py -m pip install opencv-contrib-python
```

---

## 2. 新建 layout 文件夹

在项目目录下新建两个文件夹：

```text
data/layouts
data/generated
```

macOS 可以用：

```bash
mkdir -p data/layouts
mkdir -p data/generated
```

Windows：

```bat
mkdir data
mkdir data\layouts
mkdir data\generated
```

---

## 3. 新建键盘 layout JSON

新建文件：

```text
data/layouts/keyboard_number_v1.json
```

代码：

```json
{
  "layout_id": "keyboard_number_v1",
  "name": "10键数字纸面键盘",
  "unit": "mm",
  "origin": "top_left",

  "board": {
    "w": 297,
    "h": 210
  },

  "markers": [
    {
      "id": 0,
      "x": 5,
      "y": 5,
      "w": 22,
      "h": 22
    },
    {
      "id": 1,
      "x": 270,
      "y": 5,
      "w": 22,
      "h": 22
    },
    {
      "id": 2,
      "x": 270,
      "y": 183,
      "w": 22,
      "h": 22
    },
    {
      "id": 3,
      "x": 5,
      "y": 183,
      "w": 22,
      "h": 22
    }
  ],

  "keys": [
    {
      "id": "1",
      "x": 40,
      "y": 67,
      "w": 34,
      "h": 30
    },
    {
      "id": "2",
      "x": 86,
      "y": 67,
      "w": 34,
      "h": 30
    },
    {
      "id": "3",
      "x": 132,
      "y": 67,
      "w": 34,
      "h": 30
    },
    {
      "id": "4",
      "x": 178,
      "y": 67,
      "w": 34,
      "h": 30
    },
    {
      "id": "5",
      "x": 224,
      "y": 67,
      "w": 34,
      "h": 30
    },
    {
      "id": "6",
      "x": 40,
      "y": 113,
      "w": 34,
      "h": 30
    },
    {
      "id": "7",
      "x": 86,
      "y": 113,
      "w": 34,
      "h": 30
    },
    {
      "id": "8",
      "x": 132,
      "y": 113,
      "w": 34,
      "h": 30
    },
    {
      "id": "9",
      "x": 178,
      "y": 113,
      "w": 34,
      "h": 30
    },
    {
      "id": "0",
      "x": 224,
      "y": 113,
      "w": 34,
      "h": 30
    }
  ]
}
```

---

## 4. 理解 layout JSON

理解这份 JSON 怎么描述键盘。

### `board`

```json
"board": {
  "w": 297,
  "h": 210
}
```

`board` 表示纸面大小。

这里用的是横向 A4：

```text
宽度 297mm
高度 210mm
```

---

### `origin`

```json
"origin": "top_left"
```

表示坐标原点在左上角。

坐标方向是：

```text
x 越大，越往右
y 越大，越往下
```

这和 OpenCV 图像坐标一致。

---

### `markers`

```json
{
  "id": 0,
  "x": 5,
  "y": 5,
  "w": 22,
  "h": 22
}
```

每一个 marker 都是一个 ArUco 定位标记。

字段含义：

```text
id：marker 的编号
x：marker 左上角的 x 坐标
y：marker 左上角的 y 坐标
w：marker 宽度
h：marker 高度
```

这里的单位都是 `mm`。

注意：

```text
marker 不是按键
marker 是给摄像头定位纸面的标记
```

后面 PaperMapper 会用这些 marker 把摄像头坐标转换成纸面坐标。

---

### `keys`

```json
{
  "id": "1",
  "x": 40,
  "y": 67,
  "w": 34,
  "h": 30
}
```

每一个 key 表示一个按键区域。

字段含义：

```text
id：按键名字
x：按键左上角的 x 坐标
y：按键左上角的 y 坐标
w：按键宽度
h：按键高度
```

比如上面这个 key 表示：

```text
有一个按键叫 1
它左上角在 x=40, y=67
宽度是 34mm
高度是 30mm
```

后面的 `KeyFinder` 会根据这些区域判断：

```text
某个手指坐标现在落在哪个 key 里
```

---

## 5. 新建实时预览程序

新建文件：

```text
programs/preview_layout.py
```

代码：

```python
import json
import os
import time

import cv2
import numpy as np


def load_layout(layout_path):
    with open(layout_path, "r", encoding="utf-8") as f:
        return json.load(f)


def mm_to_px(value, scale):
    return int(round(value * scale))


def create_marker_image(marker_id, size_px):
    if not hasattr(cv2, "aruco"):
        raise RuntimeError(
            "当前 OpenCV 没有 aruco 模块。请安装：python3 -m pip install opencv-contrib-python"
        )

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    if hasattr(cv2.aruco, "generateImageMarker"):
        marker_image = cv2.aruco.generateImageMarker(
            dictionary,
            marker_id,
            size_px
        )
    else:
        marker_image = np.zeros((size_px, size_px), dtype=np.uint8)
        cv2.aruco.drawMarker(
            dictionary,
            marker_id,
            size_px,
            marker_image,
            1
        )

    return marker_image


def draw_marker(canvas, marker, scale):
    marker_id = marker["id"]

    x = mm_to_px(marker["x"], scale)
    y = mm_to_px(marker["y"], scale)
    w = mm_to_px(marker["w"], scale)
    h = mm_to_px(marker["h"], scale)

    marker_image = create_marker_image(marker_id, w)

    if w != h:
        marker_image = cv2.resize(marker_image, (w, h))

    canvas[y:y + h, x:x + w] = marker_image


def draw_key(canvas, key, scale):
    x = mm_to_px(key["x"], scale)
    y = mm_to_px(key["y"], scale)
    w = mm_to_px(key["w"], scale)
    h = mm_to_px(key["h"], scale)

    cv2.rectangle(
        canvas,
        (x, y),
        (x + w, y + h),
        0,
        2,
        lineType=cv2.LINE_AA
    )

    key_id = key["id"]

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2

    text_size, _ = cv2.getTextSize(
        key_id,
        font,
        font_scale,
        thickness
    )

    text_w = text_size[0]
    text_h = text_size[1]

    text_x = x + (w - text_w) // 2
    text_y = y + (h + text_h) // 2

    cv2.putText(
        canvas,
        key_id,
        (text_x, text_y),
        font,
        font_scale,
        0,
        thickness,
        lineType=cv2.LINE_AA
    )


def draw_board_border(canvas):
    height, width = canvas.shape

    cv2.rectangle(
        canvas,
        (0, 0),
        (width - 1, height - 1),
        0,
        2
    )


def draw_layout(layout, scale):
    board = layout["board"]

    board_w_px = mm_to_px(board["w"], scale)
    board_h_px = mm_to_px(board["h"], scale)

    canvas = np.ones((board_h_px, board_w_px), dtype=np.uint8) * 255

    for marker in layout["markers"]:
        draw_marker(canvas, marker, scale)

    for key in layout["keys"]:
        draw_key(canvas, key, scale)

    draw_board_border(canvas)

    return canvas


def save_image(output_path, image):
    output_folder = os.path.dirname(output_path)

    if output_folder != "":
        os.makedirs(output_folder, exist_ok=True)

    cv2.imwrite(output_path, image)


def render_layout(layout_path, scale):
    layout = load_layout(layout_path)
    image = draw_layout(layout, scale)
    return image


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"
    output_path = "data/generated/keyboard_number_v1.png"

    preview_scale = 3
    save_scale = 6

    last_mtime = None
    preview_image = None

    cv2.namedWindow("Paper Keyboard - Layout Preview", cv2.WINDOW_NORMAL)

    print("layout 实时预览开始")
    print("q：退出")
    print("s：保存 PNG")
    print("r：手动重新加载 layout")
    print("+ / -：调整预览大小")
    print()

    while True:
        need_reload = False

        try:
            current_mtime = os.path.getmtime(layout_path)

            if last_mtime is None:
                need_reload = True
            elif current_mtime != last_mtime:
                need_reload = True

            if need_reload:
                preview_image = render_layout(layout_path, preview_scale)
                last_mtime = current_mtime
                print("已重新渲染 layout，preview_scale =", preview_scale)

        except Exception as e:
            print("渲染 layout 失败：", e)
            time.sleep(0.5)

        if preview_image is not None:
            cv2.imshow("Paper Keyboard - Layout Preview", preview_image)

        key = cv2.waitKey(100)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("r"):
            try:
                preview_image = render_layout(layout_path, preview_scale)
                last_mtime = os.path.getmtime(layout_path)
                print("已手动重新加载 layout")
            except Exception as e:
                print("手动重新加载失败：", e)

        if key & 0xFF == ord("s"):
            try:
                save_image_to_save = render_layout(layout_path, save_scale)
                save_image(output_path, save_image_to_save)
                print("已保存：", output_path)
            except Exception as e:
                print("保存失败：", e)

        if key & 0xFF == ord("+") or key & 0xFF == ord("="):
            preview_scale = preview_scale + 1
            preview_image = render_layout(layout_path, preview_scale)
            print("preview_scale =", preview_scale)

        if key & 0xFF == ord("-"):
            preview_scale = max(1, preview_scale - 1)
            preview_image = render_layout(layout_path, preview_scale)
            print("preview_scale =", preview_scale)

    cv2.destroyAllWindows()
    print("layout 实时预览结束")


if __name__ == "__main__":
    main()
```

---

## 6. 修改 app.py 运行预览程序

把 `app.py` 暂时改成：

```python
from programs.preview_layout import main


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

## 7. 使用方法

运行后会出现一个 layout 预览窗口。

快捷键：

```text
q：退出
s：保存 PNG
r：手动重新加载 layout
+ / -：调整预览大小
```

如果修改了：

```text
data/layouts/keyboard_number_v1.json
```

保存 JSON 后，预览窗口会自动重新渲染。

可以尝试修改一个按键：

```json
{
  "id": "1",
  "x": 60,
  "y": 67,
  "w": 34,
  "h": 30
}
```

把 `x` 从 `40` 改成 `60`，保存后观察 1 键是否向右移动。

---

## 8. 成功标准

如果一切正常，应该看到一个纸面键盘预览窗口。

```text
能看到白色纸面
四个角附近有 ArUco marker
中间有数字按键
修改 JSON 后窗口会刷新
按 s 可以保存 PNG
按 q 可以退出
```

保存后会生成：

```text
data/generated/keyboard_number_v1.png
```

---

## 9. 注意点

### 这一步的代码主要是工具代码

`preview_layout.py` 的作用是帮我们预览和保存键盘图片。

这一步不需要逐行理解 OpenCV 画图代码，重点是理解：

```text
layout JSON 怎么描述键盘
改 JSON 怎么影响渲染结果
ArUco marker 为什么要放在纸上
```

---

### ArUco marker 不要挡住按键

marker 是给摄像头定位用的，不是给用户按的。

设计 layout 时要注意：

```text
marker 尽量放在纸张边角
marker 周围不要放按键
marker 尽量不要放在使用时手或其他物体会挡住的区域
```

如果摄像头看不到 marker，后面的纸面定位就会失败。

---

### marker 的编号不要重复

这里用了 4 个 marker：

```text
0
1
2
3
```

每个 marker 的图案都不一样。

后面的程序会根据 marker 编号知道：

```text
哪个 marker 在左上
哪个 marker 在右上
哪个 marker 在右下
哪个 marker 在左下
```

所以不要把不同 marker 写成相同的 `id`。

---

### JSON 和图片要保持一致

后面的 `KeyFinder` 会根据 JSON 里的 `keys` 判断按键区域。

所以如果你修改了 JSON，一定要重新保存图片：

```text
按 s 保存 PNG
```

这样纸面上的按键位置和程序里的按键位置才是同一套数据。

---

### 打印时尽量不要裁切

把图片打印到纸上时，尽量选择：

```text
不裁切
完整页面
保持比例
```

不要让打印软件把四个角的 marker 裁掉。

marker 被裁掉或变形后，后面的摄像头定位会更不稳定。
