# Step 14：BLE 无线版纸面键盘

Step 13 已经确认：

```text
XIAO 可以通过 BLE notify 发送 "1"
↓
电脑 Python 可以用 bleak 收到 candidate = 1
```

这一步要把 Step 12 的有线多按钮版改成无线版。

之前的有线版是：

```text
D0-D4 按钮
↓
XIAO Serial.println("0"-"4")
↓
SerialTapSource
↓
candidate = 0 / 1 / 2 / 3 / 4
```

无线版改成：

```text
D0-D4 按钮
↓
XIAO BLE notify "0"-"4"
↓
BleTapSource
↓
candidate = 0 / 1 / 2 / 3 / 4
```

视觉部分不需要改：

```text
CameraSource
MediaPipeHandSource
PaperMapper
FrameBuilder
KeyFinder
InputDecider
TextBuffer
```

都继续使用前面已经完成的版本。

这一步会新增：

```text
input_sources/ble_tap_source.py
programs/test_ble_tap_source.py
programs/wireless_keyboard.py
```

---

## 1. XIAO 上传 BLE 多按钮程序

这版 Arduino 程序会读取 D0-D4 五个按钮。

对应关系是：

```text
D0 -> candidate = 0
D1 -> candidate = 1
D2 -> candidate = 2
D3 -> candidate = 3
D4 -> candidate = 4
```

每个按钮的另一端都接 `GND`。

在 Arduino IDE 里上传下面的程序：

```cpp
#include <NimBLEDevice.h>

// D0-D4 分别对应 0-4 号手指。
// 按下哪个按钮，就通过 BLE 发送哪个 candidate。
const int BUTTON_PIN_0 = D0;
const int BUTTON_PIN_1 = D1;
const int BUTTON_PIN_2 = D2;
const int BUTTON_PIN_3 = D3;
const int BUTTON_PIN_4 = D4;

// 板载 LED 用来提示已经发送了一次 BLE 数据。
// 如果 LED_BUILTIN 不能正常控制板载灯，可以改成：
// const int LED_PIN = 15;
const int LED_PIN = LED_BUILTIN;

// 记录每个按钮上一次的状态。
// 使用 INPUT_PULLUP 时：
// 松开按钮 -> HIGH
// 按下按钮 -> LOW
int lastButtonState0 = HIGH;
int lastButtonState1 = HIGH;
int lastButtonState2 = HIGH;
int lastButtonState3 = HIGH;
int lastButtonState4 = HIGH;

// SERVICE_UUID 表示这一组 BLE 服务。
// Python 扫描 BLE 设备时，会用这个 UUID 找到 XIAO。
const char* SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";

// CANDIDATE_UUID 是真正发送 candidate 的数据通道。
// XIAO 按按钮后，会通过这个 characteristic notify 给电脑。
const char* CANDIDATE_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";

// 之后通过这个对象发送 "0" / "1" / "2" / "3" / "4"。
NimBLECharacteristic* candidateCharacteristic;


void flashLed() {
    // 板载 LED 闪一下，表示已经发送。
    // 如果你的板载 LED 亮灭逻辑相反，可以把 HIGH 和 LOW 对调。
    digitalWrite(LED_PIN, HIGH);
    delay(80);
    digitalWrite(LED_PIN, LOW);
}


void sendCandidate(const char* candidate) {
    // 把 candidate 写入 BLE characteristic。
    candidateCharacteristic->setValue(candidate);

    // notify 表示主动通知电脑：这里有新数据。
    candidateCharacteristic->notify();

    Serial.print("BLE candidate = ");
    Serial.println(candidate);

    flashLed();
}


void setup() {
    Serial.begin(115200);
    delay(1500);

    // 五个按钮都使用内部上拉。
    // 每个按钮只需要接：GPIO 和 GND。
    pinMode(BUTTON_PIN_0, INPUT_PULLUP);
    pinMode(BUTTON_PIN_1, INPUT_PULLUP);
    pinMode(BUTTON_PIN_2, INPUT_PULLUP);
    pinMode(BUTTON_PIN_3, INPUT_PULLUP);
    pinMode(BUTTON_PIN_4, INPUT_PULLUP);

    pinMode(LED_PIN, OUTPUT);

    // 创建 BLE 设备。
    // 设备名在 macOS 扫描结果中不一定显示，但不影响后面用 SERVICE_UUID 查找。
    NimBLEDevice::init("PaperKeyboard_XIAO");

    // 创建 BLE server。
    NimBLEServer* server = NimBLEDevice::createServer();

    // 创建 BLE service。
    NimBLEService* service = server->createService(SERVICE_UUID);

    // 创建 candidate characteristic。
    // READ：电脑可以读取当前值。
    // NOTIFY：XIAO 可以主动把新值推送给电脑。
    candidateCharacteristic = service->createCharacteristic(
        CANDIDATE_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );

    // 初始值设为 -1，表示暂时没有输入。
    candidateCharacteristic->setValue("-1");

    // 启动 service。
    service->start();

    // 开始 BLE 广播。
    // Python 会扫描带有 SERVICE_UUID 的 BLE 设备。
    NimBLEAdvertising* advertising = NimBLEDevice::getAdvertising();
    advertising->addServiceUUID(SERVICE_UUID);
    advertising->setName("PaperKeyboard_XIAO");
    advertising->enableScanResponse(true);
    advertising->start();

    Serial.println("BLE multi button start");
}


void loop() {
    int buttonState0 = digitalRead(BUTTON_PIN_0);
    int buttonState1 = digitalRead(BUTTON_PIN_1);
    int buttonState2 = digitalRead(BUTTON_PIN_2);
    int buttonState3 = digitalRead(BUTTON_PIN_3);
    int buttonState4 = digitalRead(BUTTON_PIN_4);

    // 只有按钮状态发生变化时才处理。
    // 这样不会一直重复发送同一个 candidate。

    if (buttonState0 != lastButtonState0) {
        lastButtonState0 = buttonState0;

        if (buttonState0 == LOW) {
            sendCandidate("0");
        }

        delay(50);
    }

    if (buttonState1 != lastButtonState1) {
        lastButtonState1 = buttonState1;

        if (buttonState1 == LOW) {
            sendCandidate("1");
        }

        delay(50);
    }

    if (buttonState2 != lastButtonState2) {
        lastButtonState2 = buttonState2;

        if (buttonState2 == LOW) {
            sendCandidate("2");
        }

        delay(50);
    }

    if (buttonState3 != lastButtonState3) {
        lastButtonState3 = buttonState3;

        if (buttonState3 == LOW) {
            sendCandidate("3");
        }

        delay(50);
    }

    if (buttonState4 != lastButtonState4) {
        lastButtonState4 = buttonState4;

        if (buttonState4 == LOW) {
            sendCandidate("4");
        }

        delay(50);
    }
}
```

上传后，可以打开 Arduino Serial Monitor 看一下，应该能看到：

```text
BLE multi button start
```

后面按按钮时，Serial Monitor 里也会显示：

```text
BLE candidate = 1
```

正式用 Python 连接 BLE 时，可以关闭 Serial Monitor。

---

## 2. 新建 `input_sources/ble_tap_source.py`

`BleTapSource` 的作用和 `SerialTapSource` 一样，都是提供统一接口：

```python
candidate = tap_source.get_candidate()
```

区别是：

```text
SerialTapSource 从 USB 串口读数据
BleTapSource 从 BLE notify 读数据
```

因为 `bleak` 是异步库，而前面的摄像头主程序是普通循环，所以这里把 BLE 接收放进一个后台线程里。这样 OpenCV 摄像头循环不会被 BLE 等待卡住。

新建文件：

```text
input_sources/ble_tap_source.py
```

代码：

```python
import asyncio
import threading
import time

from bleak import BleakClient
from bleak import BleakScanner


class BleTapSource:
    def __init__(
        self,
        service_uuid="6e400001-b5a3-f393-e0a9-e50e24dcca9e",
        candidate_uuid="6e400003-b5a3-f393-e0a9-e50e24dcca9e",
        scan_timeout=20.0
    ):
        self.service_uuid = service_uuid.lower()
        self.candidate_uuid = candidate_uuid
        self.scan_timeout = scan_timeout

        # pending_candidate 保存最近一次收到的 candidate。
        # 没有新输入时，用 -1 表示。
        self.pending_candidate = -1

        self.connected = False
        self.should_stop = False
        self.error = None

        # BLE 回调在后台线程里发生。
        # 主程序也会读取 pending_candidate。
        # 所以用 lock 避免两个线程同时改同一个变量。
        self.lock = threading.Lock()

        # 开一个后台线程专门处理 BLE 扫描、连接和 notify。
        self.thread = threading.Thread(
            target=self.run_ble_thread,
            daemon=True
        )

        self.thread.start()

        # 等待 BLE 连接完成。
        start_time = time.time()

        while not self.connected:
            if self.error is not None:
                raise RuntimeError(self.error)

            if time.time() - start_time > self.scan_timeout + 5:
                raise RuntimeError("BLE 连接超时")

            time.sleep(0.1)

    def run_ble_thread(self):
        try:
            asyncio.run(self.connect_and_listen())
        except Exception as e:
            self.error = str(e)

    async def connect_and_listen(self):
        print("开始扫描 BLE 设备...")

        # 不按设备名找，因为 macOS 上 name 可能是 None。
        # 直接找带有目标 service UUID 的设备。
        device = await BleakScanner.find_device_by_filter(
            lambda d, adv: self.service_uuid in [
                uuid.lower() for uuid in adv.service_uuids
            ],
            timeout=self.scan_timeout
        )

        if device is None:
            raise RuntimeError("没有找到包含目标 service 的 BLE 设备")

        print("找到 BLE 设备")
        print("name:", device.name)
        print("address:", device.address)
        print("开始连接...")

        async with BleakClient(device) as client:
            print("BLE 连接成功")

            self.connected = True

            # 订阅 candidate characteristic。
            # XIAO notify 时，会自动调用 handle_candidate。
            await client.start_notify(
                self.candidate_uuid,
                self.handle_candidate
            )

            while not self.should_stop:
                await asyncio.sleep(0.1)

            await client.stop_notify(self.candidate_uuid)

    def handle_candidate(self, sender, data):
        # data 是 BLE 发来的 bytes。
        # Arduino 发的是字符串 "0" / "1" / "2" / "3" / "4"。
        text = data.decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if text not in ["0", "1", "2", "3", "4"]:
            return

        with self.lock:
            self.pending_candidate = int(text)

    def get_candidate(self):
        # 主程序每一帧都会调用 get_candidate()。
        # 如果刚刚收到过 BLE 输入，就返回对应 candidate。
        # 返回后立刻清空成 -1，避免同一次输入被重复使用。
        with self.lock:
            candidate = self.pending_candidate
            self.pending_candidate = -1

        return candidate

    def close(self):
        self.should_stop = True
        self.thread.join(timeout=2)
```

---

## 3. 新建 `programs/test_ble_tap_source.py`

在接进完整纸面键盘之前，先单独测试 `BleTapSource`。

新建文件：

```text
programs/test_ble_tap_source.py
```

代码：

```python
import time

from input_sources.ble_tap_source import BleTapSource


def main():
    print("BleTapSource 测试开始")
    print("按 D0-D4 按钮，终端应该显示 candidate")
    print("按 Ctrl + C 退出")

    tap_source = BleTapSource()

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
        print("BLE 已关闭")


if __name__ == "__main__":
    main()
```

修改 `app.py`：

```python
from programs.test_ble_tap_source import main


main()
```

运行：

```bash
python3 app.py
```

Windows：

```bash
python app.py
```

正常情况下，按 D0-D4 按钮，终端会显示：

```text
candidate = 0
candidate = 1
candidate = 2
candidate = 3
candidate = 4
```

---

## 4. 新建 `programs/wireless_keyboard.py`

这一步在 Step 11 / Step 12 的硬件按钮版基础上改。

复制：

```text
programs/hardware_keyboard.py
```

改名为：

```text
programs/wireless_keyboard.py
```

然后只改输入源。

---

## 5. 修改 import

把原来的：

```python
from input_sources.serial_tap_source import SerialTapSource
```

改成：

```python
from input_sources.ble_tap_source import BleTapSource
```

---

## 6. 删除串口 PORT

删掉类似这样的代码：

```python
PORT = "/dev/cu.usbmodem1101"
```

BLE 版本不需要手动写串口号。

---

## 7. 修改 tap_source

把原来的：

```python
tap_source = SerialTapSource(
    port=PORT,
    baudrate=115200
)
```

改成：

```python
tap_source = BleTapSource()
```

退出时继续保留：

```python
tap_source.close()
```

因为 `BleTapSource` 和 `SerialTapSource` 都提供同一个接口：

```python
candidate = tap_source.get_candidate()
```

所以后面的 `FrameBuilder` 和 `handle_input()` 不需要改。

---

## 8. 修改提示文字

可以把程序开始时的提示文字改成：

```python
print("BLE 无线纸面键盘开始")
print("请把纸面键盘放到摄像头画面里")
print("按 D0-D4 按钮输入对应手指所在的 key")
print("按 q 退出")
print("按 p 打印当前 frame")
```

窗口标题也可以改成：

```python
cv2.imshow("Paper Keyboard - Wireless Keyboard", image)
```

---

## 9. 修改 `app.py`

```python
from programs.wireless_keyboard import main


main()
```

运行：

```bash
python3 app.py
```

Windows：

```bash
python app.py
```

---

## 10. 成功标准

无线版完成后，整体数据流是：

```text
D0-D4 按钮
↓
XIAO 读取按钮状态
↓
XIAO 通过 BLE notify 发送 "0"-"4"
↓
BleTapSource 接收 candidate
↓
FrameBuilder 把 candidate 放进 frame
↓
InputDecider 判断是否是新输入
↓
根据 candidate 找对应 finger_id 的位置
↓
KeyFinder 判断这个手指在哪个 key 上
↓
TextBuffer 保存输入结果
```

运行时应该看到：

```text
摄像头画面正常
纸面边框正常
蓝色按键框正常
当前 key 高亮正常
按 D0-D4 后能输入对应手指所在的 key
```

这一步完成后，项目就有了无线硬件按钮版本。

下一步如果继续做，就应该进入产品化阶段：

```text
电池供电
焊接
按钮固定
走线
外壳
展示整理
```
