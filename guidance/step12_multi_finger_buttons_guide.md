# Step 12：多指按钮输入

这一步在 Step 11 的硬件按钮版基础上继续改。

Step 11 里已经实现了单指输入，这一步把它扩展成 5 个手指。

```text
D0 -> candidate = 0 -> 拇指
D1 -> candidate = 1 -> 食指
D2 -> candidate = 2 -> 中指
D3 -> candidate = 3 -> 无名指
D4 -> candidate = 4 -> 小指
```

对应的数据流是：

```text
某个按钮按下
↓
XIAO 发送对应 candidate
↓
SerialTapSource 读到 candidate
↓
FrameBuilder 写入 frame["tap"]["candidate"]
↓
InputDecider 判断是否是新输入
↓
根据 candidate 找对应 finger_id 的纸面坐标
↓
KeyFinder 判断这个手指在哪个 key 上
↓
TextBuffer 加入这个 key
```

---

## 1. 修改 XIAO 的 Arduino 程序

把 Step 9 / Step 11 使用的单按钮程序改成下面的五按钮版本。

```cpp
const int BUTTON_PIN_0 = D0;  // 拇指按钮
const int BUTTON_PIN_1 = D1;  // 食指按钮
const int BUTTON_PIN_2 = D2;  // 中指按钮
const int BUTTON_PIN_3 = D3;  // 无名指按钮
const int BUTTON_PIN_4 = D4;  // 小指按钮

int lastButtonState0 = HIGH;
int lastButtonState1 = HIGH;
int lastButtonState2 = HIGH;
int lastButtonState3 = HIGH;
int lastButtonState4 = HIGH;

void setup() {
    Serial.begin(115200);
    delay(1500);

    pinMode(BUTTON_PIN_0, INPUT_PULLUP);
    pinMode(BUTTON_PIN_1, INPUT_PULLUP);
    pinMode(BUTTON_PIN_2, INPUT_PULLUP);
    pinMode(BUTTON_PIN_3, INPUT_PULLUP);
    pinMode(BUTTON_PIN_4, INPUT_PULLUP);

    Serial.println("multi button start");
}

void loop() {
    int buttonState0 = digitalRead(BUTTON_PIN_0);
    int buttonState1 = digitalRead(BUTTON_PIN_1);
    int buttonState2 = digitalRead(BUTTON_PIN_2);
    int buttonState3 = digitalRead(BUTTON_PIN_3);
    int buttonState4 = digitalRead(BUTTON_PIN_4);

    // D0：拇指按钮，按下时发送 0
    if (buttonState0 != lastButtonState0) {
        lastButtonState0 = buttonState0;

        if (buttonState0 == LOW) {
            Serial.println("0");
        }

        delay(50);
    }

    // D1：食指按钮，按下时发送 1
    if (buttonState1 != lastButtonState1) {
        lastButtonState1 = buttonState1;

        if (buttonState1 == LOW) {
            Serial.println("1");
        }

        delay(50);
    }

    // D2：中指按钮，按下时发送 2
    if (buttonState2 != lastButtonState2) {
        lastButtonState2 = buttonState2;

        if (buttonState2 == LOW) {
            Serial.println("2");
        }

        delay(50);
    }

    // D3：无名指按钮，按下时发送 3
    if (buttonState3 != lastButtonState3) {
        lastButtonState3 = buttonState3;

        if (buttonState3 == LOW) {
            Serial.println("3");
        }

        delay(50);
    }

    // D4：小指按钮，按下时发送 4
    if (buttonState4 != lastButtonState4) {
        lastButtonState4 = buttonState4;

        if (buttonState4 == LOW) {
            Serial.println("4");
        }

        delay(50);
    }
}
```

这里仍然使用 `INPUT_PULLUP`。

所以每个按钮都是一样的接法：

```text
按钮一端 -> 对应的 D 引脚
按钮另一端 -> GND
```

具体对应关系：

```text
拇指按钮：D0 ↔ GND
食指按钮：D1 ↔ GND
中指按钮：D2 ↔ GND
无名指按钮：D3 ↔ GND
小指按钮：D4 ↔ GND
```

使用 `INPUT_PULLUP` 时：

```text
没按按钮 -> HIGH
按下按钮 -> LOW
```

所以代码里检测到 `LOW` 时，才通过串口发送对应数字。

---

## 2. 修改 `input_sources/serial_tap_source.py`

Step 10 的 `SerialTapSource` 原来只识别：

```text
"1"
```

现在改成识别：

```text
"0" / "1" / "2" / "3" / "4"
```

把 `get_candidate()` 改成：

```python
    def get_candidate(self):
        # 读取一行串口数据。
        # 如果没有新内容，因为 timeout 很短，会很快返回空字符串。
        line = self.ser.readline().decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if line == "":
            return -1

        # Step 12 约定：
        # D0 -> 0
        # D1 -> 1
        # D2 -> 2
        # D3 -> 3
        # D4 -> 4
        if line == "0":
            return 0

        if line == "1":
            return 1

        if line == "2":
            return 2

        if line == "3":
            return 3

        if line == "4":
            return 4

        # 其他内容暂时都忽略。
        return -1
```

---

## 3. `programs/hardware_keyboard.py` 基本无需修改

程序本来就不是写死食指的。

它的逻辑是：

```text
candidate 是几
↓
就把它当成 finger_id
↓
去 frame["fingers"] 里找这个手指的位置
↓
判断这个手指在哪个 key 上
```

所以当 `SerialTapSource` 可以返回 `0 / 1 / 2 / 3 / 4` 以后，主程序自然就支持多指输入。

---

## 4. 可以修改提示文字

在 `programs/hardware_keyboard.py` 里，把 Step 11 的：

```python
print("把食指放到某个 key 上，然后按 D1 按钮")
```

改成：

```python
print("把不同手指放到 key 上")
print("按 D0 / D1 / D2 / D3 / D4 按钮输入对应手指所在的 key")
```

画面里仍然显示 `current key`，这个 `current key` 只是用于观察食指位置，可以选择删去。

真正输入时，程序会根据按钮发送的 candidate 去找对应手指的位置。

---

## 5. 修改 `app.py`

继续运行硬件按钮版主程序：

```python
from programs.hardware_keyboard import main


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

## 成功标准

理想情况下：

```text
拇指放在某个 key 上，按 D0 -> 输入拇指所在 key
食指放在某个 key 上，按 D1 -> 输入食指所在 key
中指放在某个 key 上，按 D2 -> 输入中指所在 key
无名指放在某个 key 上，按 D3 -> 输入无名指所在 key
小指放在某个 key 上，按 D4 -> 输入小指所在 key
```

终端继续打印：

```text
输入： 5
当前文本： 15
```

这一步完成后，硬件输入就从单按钮升级成了五指按钮输入。