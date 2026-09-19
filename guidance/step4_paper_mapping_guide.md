# Step 4：纸面定位与坐标映射

这一步，我们要让程序从摄像头画面里识别出纸面键盘的位置。

这一步会创建两个新文件：

```text
components/paper_mapper.py
programs/test_paper_mapping.py
```

这一步对应完整项目中的纸面定位部分：

```text
camera image + layout JSON -> homography
```

---

## 1. 理解坐标系和映射

### 图像坐标

摄像头画面里的坐标，单位是像素。

```text
左上角是 (0, 0)
x 越大，越往右
y 越大，越往下
```

比如 MediaPipe 识别到食指指尖在：

```text
image_x = 420
image_y = 260
```

意思是这个点在摄像头画面里的某个像素位置。

---

### 纸面坐标

layout JSON 里的坐标，单位是 mm。

比如 Step 3 里有一个按键：

```json
{
  "id": "1",
  "x": 40,
  "y": 67,
  "w": 34,
  "h": 30
}
```

意思是这个按键在纸面上：

```text
左上角是 (40mm, 67mm)
宽度 34mm
高度 30mm
```

---

摄像头看到的纸可能是斜的、远的、近的、旋转的。

但是 layout JSON 里纸永远是一个平整的坐标系：

```text
0mm 到 297mm
0mm 到 210mm
```

所以我们需要一个转换关系：

```text
图像坐标 -> 纸面坐标
```

这个转换关系在代码里叫：

```text
homography
```

---

Step 3 里我们在纸的四个角放了 ArUco marker。

每个 marker 有两个信息：

```text
1. 它在摄像头画面里的位置
2. 它在 layout JSON 里的纸面位置
```

当程序知道了多个 marker 的对应关系后，就可以算出整张纸的坐标转换关系。

---

## 2. 新建 PaperMapper

新建文件：

```text
components/paper_mapper.py
```

代码：

```python
import json

import cv2
import numpy as np


class PaperMapper:
    def __init__(self, layout_path):
        # 读取 Step 3 里写好的 layout JSON。
        # 这里面记录了纸张大小、marker 的位置、按键的位置。
        with open(layout_path, "r", encoding="utf-8") as f:
            self.layout = json.load(f)

        # 保存纸张大小。
        # 后面画纸面边框时会用到 board["w"] 和 board["h"]。
        self.board = self.layout["board"]

        # 把 marker 列表整理成 dict，方便根据 marker id 查找。
        # 原来的格式是：
        # [
        #     {"id": 0, "x": 5, ...},
        #     {"id": 1, "x": 270, ...}
        # ]
        #
        # 整理后可以直接：
        # self.marker_map[0]
        # self.marker_map[1]
        self.marker_map = {}

        for marker in self.layout["markers"]:
            self.marker_map[marker["id"]] = marker

        # 选择 ArUco 字典。
        # Step 3 生成 marker 时用的是 DICT_4X4_50，
        # 这里识别时也必须用同一个字典。
        self.dictionary = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_4X4_50
        )

        # 创建 ArUco 检测参数。
        # 不同 OpenCV 版本的写法略有区别，所以这里做了兼容处理。
        if hasattr(cv2.aruco, "DetectorParameters"):
            self.parameters = cv2.aruco.DetectorParameters()
        else:
            self.parameters = cv2.aruco.DetectorParameters_create()

        # 新版 OpenCV 可以创建 ArucoDetector 对象。
        # 旧版 OpenCV 没有 ArucoDetector，就在 detect_markers 里用旧写法。
        if hasattr(cv2.aruco, "ArucoDetector"):
            self.detector = cv2.aruco.ArucoDetector(
                self.dictionary,
                self.parameters
            )
        else:
            self.detector = None

    def detect_markers(self, image):
        # ArUco marker 是黑白图案，转成灰度图就够识别了。
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 检测画面里的 marker。
        # corners：每个 marker 在图像里的四个角点
        # ids：每个 marker 的编号
        if self.detector is not None:
            corners, ids, rejected = self.detector.detectMarkers(gray)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray,
                self.dictionary,
                parameters=self.parameters
            )

        return corners, ids

    def get_marker_paper_corners(self, marker):
        # marker 在 layout JSON 里只有左上角 x, y 和宽高 w, h。
        # 但算 homography 时需要四个角点。
        x = marker["x"]
        y = marker["y"]
        w = marker["w"]
        h = marker["h"]

        # 这里返回的是 marker 在纸面坐标里的四个角。
        # 顺序是：左上、右上、右下、左下。
        return [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

    def get_homography(self, image):
        # 先从摄像头画面里检测 ArUco marker。
        corners, ids = self.detect_markers(image)

        # 如果一个 marker 都没检测到，就没法建立纸面映射。
        if ids is None:
            return None, corners, ids

        # image_points 存 marker 在摄像头画面里的角点。
        # paper_points 存同一个 marker 在纸面 layout 里的角点。
        #
        # 这两个列表是一一对应的：
        # image_points[k] 这个画面点
        # 对应 paper_points[k] 这个纸面点
        image_points = []
        paper_points = []

        for i in range(len(ids)):
            marker_id = int(ids[i][0])

            # 如果摄像头识别到了一个 layout 里没有写的 marker，忽略它。
            if marker_id not in self.marker_map:
                continue

            # 从 layout 里找到这个 marker 在纸上的位置。
            marker = self.marker_map[marker_id]

            # detected_corners 是这个 marker 在摄像头画面里的四个角点。
            detected_corners = corners[i][0]

            # expected_corners 是这个 marker 在纸面 layout 里的四个角点。
            expected_corners = self.get_marker_paper_corners(marker)

            # 把四个角点加入对应列表。
            for j in range(4):
                image_points.append(detected_corners[j])
                paper_points.append(expected_corners[j])

        # 理论上一个 marker 有四个角点，已经够算 homography。
        # 但识别到更多 marker 时会更稳。
        if len(image_points) < 4:
            return None, corners, ids

        # OpenCV 需要 numpy 数组，并且类型用 float32。
        image_points = np.array(image_points, dtype=np.float32)
        paper_points = np.array(paper_points, dtype=np.float32)

        # 计算 homography。
        # 这里得到的是：图像坐标 -> 纸面坐标 的转换关系。
        homography, mask = cv2.findHomography(
            image_points,
            paper_points
        )

        return homography, corners, ids

    def image_to_paper(self, image_x, image_y, homography):
        # 把一个图像坐标点转换成纸面坐标点。
        # 后面 MediaPipe 得到指尖 image_x, image_y 后，就会调用这个函数。
        point = np.array(
            [[[float(image_x), float(image_y)]]],
            dtype=np.float32
        )

        paper_point = cv2.perspectiveTransform(point, homography)

        paper_x = paper_point[0][0][0]
        paper_y = paper_point[0][0][1]

        return paper_x, paper_y

    def paper_to_image(self, paper_x, paper_y, homography):
        # homography 是 图像坐标 -> 纸面坐标。
        # 如果想把纸面上的点画回摄像头画面，就需要反过来转换。
        inverse = np.linalg.inv(homography)

        point = np.array(
            [[[float(paper_x), float(paper_y)]]],
            dtype=np.float32
        )

        image_point = cv2.perspectiveTransform(point, inverse)

        image_x = image_point[0][0][0]
        image_y = image_point[0][0][1]

        return image_x, image_y

    def draw_detected_markers(self, image, corners, ids):
        # 把检测到的 ArUco marker 框出来。
        # 这只是调试显示，不影响后面的判断逻辑。
        if ids is None:
            return image

        cv2.aruco.drawDetectedMarkers(image, corners, ids)
        return image

    def draw_board_border(self, image, homography):
        # 取出纸张在 layout 里的四个角。
        board_w = self.board["w"]
        board_h = self.board["h"]

        paper_corners = [
            [0, 0],
            [board_w, 0],
            [board_w, board_h],
            [0, board_h]
        ]

        image_corners = []

        # 把纸面四个角转换回图像坐标，方便画到摄像头画面上。
        for paper_x, paper_y in paper_corners:
            image_x, image_y = self.paper_to_image(
                paper_x,
                paper_y,
                homography
            )

            image_corners.append([int(image_x), int(image_y)])

        # 用绿色线把纸张边框画出来。
        # 如果绿色边框能正确贴合纸面，说明坐标映射基本是对的。
        for i in range(4):
            p1 = image_corners[i]
            p2 = image_corners[(i + 1) % 4]

            cv2.line(
                image,
                (p1[0], p1[1]),
                (p2[0], p2[1]),
                (0, 255, 0),
                3
            )

        return image

    def draw_keys(self, image, homography):
        # 把 layout JSON 里的每个按键区域画回摄像头画面。
        for key in self.layout["keys"]:
            x = key["x"]
            y = key["y"]
            w = key["w"]
            h = key["h"]

            # 每个 key 在纸面坐标里也是一个矩形。
            paper_corners = [
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h]
            ]

            image_corners = []

            # 把 key 的四个纸面角点转换回图像坐标。
            for paper_x, paper_y in paper_corners:
                image_x, image_y = self.paper_to_image(
                    paper_x,
                    paper_y,
                    homography
                )

                image_corners.append([int(image_x), int(image_y)])

            # cv2.polylines 需要 numpy 数组格式的点。
            points = np.array(
                image_corners,
                dtype=np.int32
            )

            # 用蓝色线画出按键边框。
            cv2.polylines(
                image,
                [points],
                True,
                (255, 0, 0),
                2
            )

            # 在 key 的中心位置写上按键 id。
            center_paper_x = x + w / 2
            center_paper_y = y + h / 2

            center_image_x, center_image_y = self.paper_to_image(
                center_paper_x,
                center_paper_y,
                homography
            )

            cv2.putText(
                image,
                key["id"],
                (int(center_image_x) - 8, int(center_image_y) + 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )

        return image
```

---

## 3. 新建纸面定位测试程序

新建文件：

```text
programs/test_paper_mapping.py
```

代码：

```python
import cv2

from input_sources.camera_source import CameraSource
from components.paper_mapper import PaperMapper


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    # 打开摄像头。
    camera = CameraSource(camera_id=0)

    # 创建 PaperMapper。
    # 它会读取 layout JSON，并根据里面的 marker 信息建立映射。
    mapper = PaperMapper(layout_path)

    print("纸面定位测试开始")
    print("请把生成的纸面键盘图片放到摄像头画面里")
    print("按 q 退出")

    while True:
        # 读取一帧摄像头画面。
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        # 识别 marker，并尝试计算 homography。
        # homography 不为 None，说明程序成功建立了：
        # 图像坐标 -> 纸面坐标 的转换关系。
        homography, corners, ids = mapper.get_homography(image)

        # 把识别到的 marker 框出来，方便观察。
        image = mapper.draw_detected_markers(image, corners, ids)

        if homography is not None:
            # 如果成功建立映射，就把纸张边框和按键区域画回摄像头画面。
            image = mapper.draw_board_border(image, homography)
            image = mapper.draw_keys(image, homography)

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
            # 如果没有检测到足够的 marker，就提示未识别纸面。
            cv2.putText(
                image,
                "paper not detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2
            )

        cv2.imshow("Paper Keyboard - Paper Mapping Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("纸面定位测试结束")


if __name__ == "__main__":
    main()
```

---

## 4. 修改 app.py 运行测试程序

把 `app.py` 暂时改成：

```python
from programs.test_paper_mapping import main


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

运行后，把 Step 3 生成的纸面键盘图片放到摄像头画面里。

如果一切正常，应该看到：

```text
摄像头画面正常显示
ArUco marker 被框出来
左上角显示 paper detected
绿色边框贴合整张纸面
蓝色按键框贴合纸上的按键区域
移动或旋转纸张时，绿色边框和蓝色按键框会跟着移动或旋转
按 q 可以退出
```

这一步最重要的成功标准是：

```text
绿色边框能稳定贴合纸面，蓝色按键框能稳定贴合按键位置
```

因为这说明程序已经能把摄像头画面和 layout JSON 里的纸面坐标对应起来。

---

## 6. 可能问题

### 只检测到部分 marker

只检测到一部分 marker 时，程序有时也能算出 homography。

但是一般来说：

```text
检测到的 marker 越多，坐标映射越稳定
```

所以测试时尽量让四个 marker 都出现在画面里。

---

### 绿色边框或蓝色按键框能出来，但位置不准

重点检查：

```text
是不是改过 JSON 但没有重新保存 PNG
marker 的 id 有没有重复
marker 的 x/y/w/h 是否和图片一致
图片显示或打印时有没有被拉伸
```

---

### marker 识别不稳定

可以尝试：

```text
让 marker 大一点
让摄像头离纸远一点
避免反光
提高光照
保持画面清晰
让四个 marker 不要被手挡住
```
