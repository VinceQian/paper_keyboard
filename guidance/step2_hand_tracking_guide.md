# Step 2：MediaPipe 手部识别测试

这一步，我们要在摄像头画面上识别手，并标出几个指尖位置。

这一步会创建两个新文件：

```text
input_sources/mediapipe_hand_source.py
programs/test_hand_tracking.py
```

这一步对应完整项目中的第二段数据来源：

```text
image -> hand_data
```

也就是：摄像头先给我们一张画面，MediaPipe 再从这张画面里找出手的位置和指尖位置。

---

## 0. 确认当前 Python 环境

如果项目里有 `.venv` 文件夹，但还没有激活，可以先激活。

macOS：

```bash
source .venv/bin/activate
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD：

```bat
.venv\Scripts\activate.bat
```

如果没有虚拟环境，也可以先直接用当前 Python 环境继续做。

---

## 1. 安装 MediaPipe

MediaPipe 是一个常用的人体、手部、姿态识别工具库。这一步我们只用它做一件事：

```text
从摄像头画面里找到手和指尖位置
```

安装命令：

macOS：

```bash
python3 -m pip install mediapipe
```

Windows：

```bash
python -m pip install mediapipe
```

如果 Windows 上 `python` 不可用，可以试：

```bash
py -m pip install mediapipe
```

安装完成后，可以简单检查：

macOS：

```bash
python3 -c "import mediapipe as mp; print(mp.__version__)"
```

Windows：

```bash
python -c "import mediapipe as mp; print(mp.__version__)"
```

如果能打印出版本号，说明 MediaPipe 安装成功。

---

## 2. 新建 MediaPipeHandSource

新建文件：

```text
input_sources/mediapipe_hand_source.py
```

代码：

```python
import cv2
import mediapipe as mp


class MediaPipeHandSource:
    def __init__(self, max_num_hands=1):
        self.mp_hands = mp.solutions.hands  # 手部识别模块
        self.mp_draw = mp.solutions.drawing_utils  # 画图工具

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,  # 非静态图片
            max_num_hands=max_num_hands,  # 最多识别数量
            min_detection_confidence=0.6,  # 检测置信度
            min_tracking_confidence=0.6  # 追踪置信度
        )  # 创建 Hands 对象

    def process_image(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # OpenCV 是 BGR，MediaPipe 需要 RGB。
        result = self.hands.process(image_rgb)  # 识别

        hand_data = {
            "fingertips": []
        }

        if result.multi_hand_landmarks is None:
            return hand_data, result

        height, width, _ = image.shape

        hand_landmarks = result.multi_hand_landmarks[0]

        fingertip_ids = {
            0: 4,    # 拇指指尖
            1: 8,    # 食指指尖
            2: 12,   # 中指指尖
            3: 16,   # 无名指指尖
            4: 20    # 小指指尖
        }

        for finger_id, landmark_id in fingertip_ids.items():
            landmark = hand_landmarks.landmark[landmark_id]

            image_x = int(landmark.x * width)
            image_y = int(landmark.y * height)

            fingertip = {
                "finger_id": finger_id,
                "landmark_id": landmark_id,
                "image_x": image_x,
                "image_y": image_y
            }

            hand_data["fingertips"].append(fingertip)

        return hand_data, result

    def draw_hand(self, image, result):
        if result.multi_hand_landmarks is None:
            return image

        for hand_landmarks in result.multi_hand_landmarks:
            self.mp_draw.draw_landmarks(
                image,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS # 关键点间连线
            )

        return image

    def draw_fingertips(self, image, hand_data):
        # 把识别到的指尖画出来。
        for fingertip in hand_data["fingertips"]:
            finger_id = fingertip["finger_id"]
            x = fingertip["image_x"]
            y = fingertip["image_y"]

            cv2.circle(image, (x, y), 8, (0, 0, 255), -1)  # 在指尖画红点。

            cv2.putText(
                image,
                str(finger_id),
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        return image

    def close(self):
        self.hands.close() # 关闭 Hands 对象
```

这里的 `finger_id` 是我们项目自己定义的编号：

```text
0 = 拇指
1 = 食指
2 = 中指
3 = 无名指
4 = 小指
```

MediaPipe 内部还有自己的 landmark 编号，比如食指指尖是 `8`，中指指尖是 `12`。这里我们把 MediaPipe 的编号转换成项目里更容易理解的 `finger_id`。

---

## 3. 新建手部识别测试程序

新建文件：

```text
programs/test_hand_tracking.py
```

代码：

```python
import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource


def main():
    camera = CameraSource(camera_id=0)
    hand_source = MediaPipeHandSource(max_num_hands=1)

    print("手部识别测试开始")
    print("按 q 退出")

    while True:
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        hand_data, result = hand_source.process_image(image)

        image = hand_source.draw_hand(image, result)
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - Hand Tracking Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("手部识别测试结束")


if __name__ == "__main__":
    main()
```

---

## 4. 修改 app.py 运行测试程序

把 `app.py` 暂时改成：

```python
from programs.test_hand_tracking import main


main()
```

然后运行：

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

如果一切正常，应该看到摄像头窗口里出现手部识别结果。

```text
能看到摄像头画面
手伸进画面后能看到手部骨架
食指、中指、无名指、小指指尖附近有红点
红点旁边有 1 / 2 / 3 / 4
按 q 可以退出
程序退出后没有卡住
```

---

## 6. 注意点

### OpenCV 和 MediaPipe 的颜色顺序不一样

OpenCV 读到的图像默认是：

```text
BGR
```

MediaPipe 处理图像时需要：

```text
RGB
```

所以代码里需要：

```python
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
```

### MediaPipe 给的是比例坐标

MediaPipe 里的 `landmark.x` 和 `landmark.y` 不是像素坐标，而是 0 到 1 之间的比例。

所以需要乘以画面的宽高：

```python
image_x = int(landmark.x * width)
image_y = int(landmark.y * height)
```

这样才会变成图像上的像素位置。