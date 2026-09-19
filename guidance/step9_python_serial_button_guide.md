# Step 9：Python 读取 XIAO 串口按钮输入

Step 8 已经完成了最基础的硬件测试：

```text
按钮按下 / 松开
↓
XIAO 在 Serial Monitor 里显示 pressed / released
```

这一步要把按钮输出改成项目后面需要的格式：

```text
D1 按钮被按下
↓
XIAO 通过串口发送 1
↓
Python 读到 1
↓
理解成 candidate = 1
```

这一步会创建一个新文件：

```text
programs/test_serial_button.py
```

这一步还不接摄像头，也不接纸面键盘主程序，只确认：

```text
硬件按钮 -> XIAO -> USB 串口 -> Python
```

这条链路可以跑通。

---

## 1. 安装 pyserial

Python 读取串口需要用到 `pyserial`。

macOS：

```bash
python3 -m pip install pyserial
```

Windows：

```bash
python -m pip install pyserial
```

或者：

```bash
py -m pip install pyserial
```

注意包名是 `pyserial`，代码里导入时写的是：

```python
import serial
```

---

## 2. 查看串口名称

可以用命令查看当前电脑上的串口。

macOS：

```bash
python3 -m serial.tools.list_ports
```

Windows：

```bash
python -m serial.tools.list_ports
```

或者：

```bash
py -m serial.tools.list_ports
```

也可以直接看 Arduino IDE 里当前选择的 `Port`。

macOS 上可能类似：

```text
/dev/cu.usbmodem1101
/dev/cu.usbserial-110
```

Windows 上可能类似：

```text
COM3
COM4
COM5
```

后面 Python 代码里的 `PORT` 要改成自己电脑上实际的串口。

---

## 3. 修改 XIAO 的 Arduino 程序

这次不再输出 `pressed / released`。

我们改成：

```text
按钮按下时，发送一行 1
其他时候，不发送内容
```

Arduino IDE 上传下面的程序：

```cpp
const int BUTTON_PIN = D1;

int lastButtonState = HIGH;

void setup() {
    Serial.begin(115200);
    delay(1500);

    // 按钮一端接 D1，另一端接 GND。
    // INPUT_PULLUP 会打开内部上拉：
    // 没按按钮时读到 HIGH，按下按钮时读到 LOW。
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    Serial.println("serial button start");
}

void loop() {
    int buttonState = digitalRead(BUTTON_PIN);

    // 只有按钮状态发生变化时才处理，避免一直刷屏。
    if (buttonState != lastButtonState) {
        lastButtonState = buttonState;

        // 使用 INPUT_PULLUP 时，LOW 表示按钮被按下。
        if (buttonState == LOW) {
            Serial.println("1");
        }

        // 简单等待一小会儿，减少机械按钮抖动带来的重复变化。
        delay(50);
    }
}
```

接线保持：

```text
按钮一端 -> D1
按钮另一端 -> GND
```

上传成功后，可以先打开 Arduino Serial Monitor 测一下。

按一次按钮，应该看到一行：

```text
1
```

确认后，关闭 Arduino Serial Monitor。

Python 读取串口时，Arduino Serial Monitor 不能同时占用同一个串口。

---

## 4. 新建 Python 串口测试程序

新建文件：

```text
programs/test_serial_button.py
```

代码：

```python
import time

import serial


# 这里要改成自己电脑上实际的串口。
# macOS 可能是："/dev/cu.usbmodem1101"
# Windows 可能是："COM3"
PORT = "/dev/cu.usbmodem1101"

# 这里要和 Arduino 里的 Serial.begin(115200) 保持一致。
BAUDRATE = 115200


def main():
    print("Python 串口按钮测试开始")
    print("如果程序打不开串口，请先关闭 Arduino Serial Monitor")
    print("按 Ctrl + C 退出")

    ser = serial.Serial(
        PORT,
        BAUDRATE,
        timeout=0.1
    )

    # XIAO 连接串口后可能会重启，稍微等一下再开始读。
    time.sleep(2)

    try:
        while True:
            # readline() 会读取一行串口内容。
            # Arduino 里 Serial.println("1") 会发送一行 1。
            line = ser.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            # 没有收到新内容时，line 是空字符串。
            if line == "":
                continue

            print("收到：", line)

            # 这一步只关心 D1 按钮。
            # 收到 1，就表示 candidate = 1。
            if line == "1":
                print("candidate = 1")

    except KeyboardInterrupt:
        print("用户退出")

    finally:
        ser.close()
        print("串口已关闭")


if __name__ == "__main__":
    main()
```

---

## 5. 修改 app.py

把 `app.py` 改成：

```python
from programs.test_serial_button import main


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

按下按钮时，Python 终端应该显示：

```text
收到： 1
candidate = 1
```

松开按钮时，不需要输出。

如果一开始看到：

```text
收到： serial button start
```

这是 XIAO 启动时发出的提示，可以不用管。

这一步跑通后，说明：

```text
按钮
↓
XIAO D1
↓
Serial.println("1")
↓
USB 串口
↓
Python serial.readline()
```

整条链路已经通了。

下一步会把这段测试代码整理成正式输入模块：

```text
input_sources/serial_tap_source.py
```

让它和前面的 `AudioSource` 一样，都提供统一接口：

```python
candidate = tap_source.get_candidate()
```
