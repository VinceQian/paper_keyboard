# Step 1：摄像头测试

首先，我们要确认电脑可以通过 Python 打开摄像头，并能实时显示画面。

这一步，我们会创建两个新文件：

```text
input_sources/camera_source.py
programs/test_camera.py
```

这一步对应完整项目中的第一段数据来源：

```text
摄像头 -> image
```

后面的 MediaPipe、纸面定位、按键判断，都要基于摄像头的画面继续做。

---

## 0. 先确认当前项目还能运行

进入项目文件夹，先运行原来的程序。

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

如果能看到原来 replay 的输出：

```text
1
12
123
```

说明当前版本没有问题。

这一节新增的代码只是在基础版本外面接摄像头，不需要修改之前已经写好的核心逻辑。

---

## 1. 确认当前 Python 环境

如果项目里有 `.venv` 文件夹，但还没有激活，可以这样激活。

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

## 2. 安装 OpenCV

OpenCV 是一个常用的计算机视觉工具库。这一步我们只用它做三件事：

```text
打开摄像头
读取一帧画面
显示画面窗口
```

安装命令：

macOS：

```bash
python3 -m pip install opencv-python
```

Windows：

```bash
python -m pip install opencv-python
```

如果 Windows 上 `python` 不可用，可以试：

```bash
py -m pip install opencv-python
```

安装完成后，可以简单检查：

macOS：

```bash
python3 -c "import cv2; print(cv2.__version__)"
```

Windows：

```bash
python -c "import cv2; print(cv2.__version__)"
```

如果能打印出版本号，说明 OpenCV 安装成功。

---

## 3. 新建 CameraSource

新建文件：

```text
input_sources/camera_source.py
```

代码：

```python
import cv2


class CameraSource:
    def __init__(self, camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)  # 打开一个摄像头。

        if not self.cap.isOpened(): # 如果摄像头打开失败，输出报错提示
            raise RuntimeError("无法打开摄像头：" + str(camera_id))

    def read_image(self):
        success, image = self.cap.read() # 读取当前摄像头画面的一帧，返回 success, image

        if not success: # 如果没有读到画面，返回 None
            return None

        return image # 如果读到画面，返回画面

    def release(self):
        self.cap.release() # 用完摄像头后释放资源，否则 Python 可能一直占用摄像头。
```

---

## 4. 新建摄像头测试程序

新建文件：

```text
programs/test_camera.py
```

代码：

```python
import cv2

from input_sources.camera_source import CameraSource


def main():
    camera = CameraSource(camera_id=0) 

    print("摄像头测试开始")
    print("按 q 退出")

    while True:
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        cv2.imshow("Paper Keyboard - Camera Test", image)  # 把图像显示在一个窗口里

        key = cv2.waitKey(1) # 窗口刷新和等待键盘输入的时间

        if key & 0xFF == ord("q"): # 只取 key 的最后八位
            break

    camera.release()
    cv2.destroyAllWindows() # 关闭所有创建的窗口

    print("摄像头测试结束")


if __name__ == "__main__":
    main()
```

---

## 5. 修改 app.py 运行测试程序

把 `app.py` 暂时改成：

```python
from programs.test_camera import main


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

## 6. 成功标准

如果一切正常，应该看到一个摄像头窗口。

```text
能看到摄像头画面
画面能实时变化
按 q 可以退出
程序退出后没有卡住
```

---

## 7. 常见问题

### 安装了 OpenCV，但运行时说找不到 cv2

这通常说明安装库的 Python 和运行程序的 Python 不是同一个。

可以分别检查：

macOS：

```bash
which python3
python3 -m pip --version
python3 -c "import cv2; print(cv2.__version__)"
```

Windows：

```bash
where python
python -m pip --version
python -c "import cv2; print(cv2.__version__)"
```

如果项目使用了 venv，要先激活 venv，再安装 OpenCV。

---