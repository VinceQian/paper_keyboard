# Step 10：SerialTapSource 串口输入源

这一步把 Step 9 里测试成功的串口按钮输入，整理成正式项目模块。

```text
XIAO Serial.println("1")
↓
SerialTapSource
↓
get_candidate()
↓
candidate = 1
```

这一步新增两个文件：

```text
input_sources/serial_tap_source.py
programs/test_serial_tap_source.py
```

---

## 1. 为什么要封装成 SerialTapSource

前面 Step 7 的声音输入里，`AudioSource` 提供了这个接口：

```python
candidate = audio_source.get_candidate()
```

现在硬件按钮输入也要提供同样的接口：

```python
candidate = tap_source.get_candidate()
```

这样后面的 `FrameBuilder` 不需要关心输入来自声音还是按钮。

它只需要知道：

```text
有新输入时：candidate = 1
没有新输入时：candidate = -1
```

这一步的规则很简单：

```text
收到 "1" -> 返回 1
没收到内容 -> 返回 -1
收到其他内容 -> 忽略，返回 -1
```

---

## 2. 确认 Step 9 的 Arduino 程序

XIAO 上继续使用 Step 9 的按钮程序。

当前约定是：

```text
D1 按钮 -> 发送 1
```

后面多按钮时会自然扩展成：

```text
D1 -> 1
D2 -> 2
D3 -> 3
```

Arduino 程序核心逻辑是：

```cpp
const int BUTTON_PIN = D1;

int lastButtonState = HIGH;

void setup() {
    Serial.begin(115200);
    delay(1500);

    pinMode(BUTTON_PIN, INPUT_PULLUP);

    Serial.println("serial button start");
}

void loop() {
    int buttonState = digitalRead(BUTTON_PIN);

    // 只有按钮状态发生变化时才处理，避免串口一直刷屏。
    if (buttonState != lastButtonState) {
        lastButtonState = buttonState;

        // INPUT_PULLUP:
        // 没按 -> HIGH
        // 按下 -> LOW
        if (buttonState == LOW) {
            Serial.println("1");
        }

        // 简单等待一小会儿，减少机械抖动造成的重复输出。
        delay(50);
    }
}
```

确认 Arduino Serial Monitor 里按下按钮能看到：

```text
1
```

然后关闭 Serial Monitor。

Python 读取串口时，Arduino Serial Monitor 不能同时占用同一个端口。

---

## 3. 新建 `input_sources/serial_tap_source.py`

```python
import time

import serial


class SerialTapSource:
    def __init__(
        self,
        port,
        baudrate=115200,
        timeout=0.01
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        # 打开串口。
        # port 是电脑上 XIAO 对应的端口，例如：
        # macOS: /dev/cu.usbmodem1101
        # Windows: COM3
        self.ser = serial.Serial(
            self.port,
            self.baudrate,
            timeout=self.timeout
        )

        # XIAO 打开串口后可能会重启，稍微等一下。
        time.sleep(2)

        # 清掉刚启动时可能输出的提示文字，例如 serial button start。
        self.ser.reset_input_buffer()

    def get_candidate(self):
        # 读取一行串口数据。
        # 如果没有新内容，因为 timeout 很短，会很快返回空字符串。
        line = self.ser.readline().decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if line == "":
            return -1

        # Step 9 里约定：
        # D1 按钮按下 -> XIAO 发送 "1"
        if line == "1":
            return 1

        # 其他内容暂时都忽略。
        return -1

    def close(self):
        self.ser.close()
```

---

## 4. 新建 `programs/test_serial_tap_source.py`

```python
import time

from input_sources.serial_tap_source import SerialTapSource


PORT = "/dev/cu.usbmodem1101"


def main():
    print("SerialTapSource 测试开始")
    print("按下 D1 按钮，终端应该显示 candidate = 1")
    print("按 Ctrl + C 退出")
    print()

    tap_source = SerialTapSource(
        port=PORT,
        baudrate=115200
    )

    try:
        while True:
            candidate = tap_source.get_candidate()

            if candidate != -1:
                print("candidate =", candidate)

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("用户退出")

    finally:
        tap_source.close()
        print("串口已关闭")


if __name__ == "__main__":
    main()
```

这里的 `PORT` 要继续使用 Step 9 里已经测试成功的端口。

---

## 5. 修改 `app.py`

```python
from programs.test_serial_tap_source import main


main()
```

运行：

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

按下 D1 按钮时，终端显示：

```text
candidate = 1
```

不按按钮时，终端不需要持续输出。

这一步跑通后，说明硬件按钮已经变成了项目统一输入源：

```python
tap_source.get_candidate()
```

下一步 Step 11 就可以把 `SerialTapSource` 接进前面的视觉键盘程序，用按钮替代声音来触发输入。
