# Step 13：BLE 无线输入测试

前面 Step 8–12 已经完成了 USB 串口版本：

```text
XIAO 按钮
↓
Serial.println("1")
↓
电脑 Python 读串口
↓
candidate = 1
```

这一步开始尝试无线通信。

这一节先不接按钮，也不接回 Paper Keyboard 主程序，只测试：

```text
XIAO 每隔一段时间发送一次 BLE 数据
↓
电脑 Python 扫描并连接 XIAO
↓
Python 收到 candidate = 1
```

这一步跑通后，说明电脑已经可以通过 BLE 收到 XIAO 发来的数据。后面再把“定时发送”改成“按钮按下时发送”。

---

## 1. BLE 这一层在做什么

BLE 和 USB 串口不一样。

USB 串口里，我们之前用的是：

```text
Serial.println("1")
↓
Python serial.readline()
```

BLE 里没有直接的 `readline()`。它更像是先建立一个“无线数据服务”，然后电脑去订阅其中某一个数据通道：

```text
XIAO 创建 BLE 设备
↓
XIAO 开始广播 advertising
↓
电脑扫描到这个 BLE 设备
↓
电脑连接 XIAO
↓
电脑订阅 candidate characteristic
↓
XIAO notify "1"
↓
Python 收到 "1"
```

可以先这样理解三个词：

| 名称 | 作用 |
|---|---|
| `advertising` | XIAO 向外广播：“我在这里，可以被连接” |
| `service` | 一组 BLE 功能的集合 |
| `characteristic` | 具体传输数据的通道 |

这一步我们只需要一个数据通道：

```text
candidate characteristic
```

它负责把：

```text
"1"
```

从 XIAO 发给电脑。

---

## 2. 这一步需要安装的库

### Arduino IDE

打开 Arduino IDE 的 Library Manager，安装：

```text
NimBLE-Arduino
```

XIAO ESP32C6 使用的是 BLE，这里用 NimBLE 库来创建 BLE 设备、service 和 characteristic。

### Python

macOS：

```bash
python3 -m pip install bleak
```

Windows：

```bash
python -m pip install bleak
```

或者：

```bash
py -m pip install bleak
```

`bleak` 用来让 Python 扫描、连接和读取 BLE 设备。

---

## 3. UUID 是什么

这一步会看到两个 UUID：

```cpp
const char* SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";
const char* CANDIDATE_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";
```

UUID 可以理解成 BLE 里的“编号”。

它的格式是：

```text
8位-4位-4位-4位-12位
```

例如：

```text
6e400001-b5a3-f393-e0a9-e50e24dcca9e
```

这里两个 UUID 的分工是：

| UUID | 作用 |
|---|---|
| `SERVICE_UUID` | 让电脑识别这是我们要找的 BLE 服务 |
| `CANDIDATE_UUID` | 真正发送 candidate 数据的通道 |

可以这样理解：

```text
SERVICE_UUID：这一组无线功能叫什么
CANDIDATE_UUID：candidate 数据从哪条通道发出去
```

Arduino 端和 Python 端必须使用同样的 UUID。否则电脑可能能找到设备，但找不到对应的数据通道。

---

## 4. XIAO 程序：每隔 2 秒发送一次 candidate

在 Arduino IDE 里上传下面的程序。

```cpp
#include <NimBLEDevice.h>

// 板载 LED 用来提示 XIAO 已经发送了一次 BLE 数据。
const int LED_PIN = LED_BUILTIN;

// SERVICE_UUID 用来标记这一组 BLE 服务。
// Python 扫描设备时，会寻找带有这个 service 的设备。
const char* SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";

// CANDIDATE_UUID 是真正发送 candidate 数据的通道。
// Python 连接 XIAO 后，会订阅这个 characteristic。
const char* CANDIDATE_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";

// 这个变量会保存 candidate characteristic。
// 后面要发送 "1" 时，就通过它 setValue() 和 notify()。
NimBLECharacteristic* candidateCharacteristic;

void setup() {
    // 开启 USB 串口，方便在 Arduino Serial Monitor 里看到调试信息。
    Serial.begin(115200);
    delay(1500);

    // 设置板载 LED 为输出模式。
    pinMode(LED_PIN, OUTPUT);

    // 创建 BLE 设备。
    // 这个名字不一定每次都能被 macOS / Python 显示出来，
    // 所以后面 Python 会主要通过 SERVICE_UUID 来找设备。
    NimBLEDevice::init("PaperKeyboard_XIAO");

    // 创建一个 BLE server。
    // 可以把 server 理解成：XIAO 对外提供 BLE 服务的主体。
    NimBLEServer* server = NimBLEDevice::createServer();

    // 在 server 里面创建一个 service。
    // 这个 service 的编号就是 SERVICE_UUID。
    NimBLEService* service = server->createService(SERVICE_UUID);

    // 在 service 里面创建一个 characteristic。
    // 这个 characteristic 的编号就是 CANDIDATE_UUID。
    //
    // READ：电脑可以读取当前值。
    // NOTIFY：XIAO 可以主动把新值推送给电脑。
    candidateCharacteristic = service->createCharacteristic(
        CANDIDATE_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );

    // 初始值设为 "-1"，表示当前没有输入。
    candidateCharacteristic->setValue("-1");

    // 启动 service。
    // 没有 start 的 service 不会真正对外提供。
    service->start();

    // 开始广播 advertising。
    // 电脑只有先扫描到这个广播，才能连接 XIAO。
    NimBLEAdvertising* advertising = NimBLEDevice::getAdvertising();

    // 把 SERVICE_UUID 放进广播信息里。
    // Python 会根据这个 UUID 找到 XIAO。
    advertising->addServiceUUID(SERVICE_UUID);

    // 设置广播名字。
    // 有些系统扫描时可能显示这个名字，有些时候可能显示 None。
    advertising->setName("PaperKeyboard_XIAO");

    // 开启 scan response。
    // 这可以让设备名等信息有机会被扫描工具看到。
    advertising->enableScanResponse(true);

    // 正式开始广播。
    advertising->start();

    Serial.println("BLE advertising start");
}

void loop() {
    // 这一步暂时不接按钮。
    // 每隔 2 秒主动发送一次 candidate = 1。

    // 先把 characteristic 当前值设置成 "1"。
    candidateCharacteristic->setValue("1");

    // notify 表示主动通知已经连接并订阅的电脑：
    // 现在有一个新值可以读取。
    candidateCharacteristic->notify();

    Serial.println("BLE candidate = 1");

    // 板载 LED 闪一下，表示刚刚发送了一次数据。
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);

    // 剩下的时间等待，让总间隔大约是 2 秒。
    delay(1900);
}
```

上传后，打开 Arduino Serial Monitor，baud 选择：

```text
115200
```

如果程序正常启动，应该看到：

```text
BLE advertising start
BLE candidate = 1
BLE candidate = 1
BLE candidate = 1
...
```

看到以后，XIAO 就已经开始通过 BLE 广播并定时发送数据了。

---

## 5. Python 程序：扫描并接收 BLE 数据

新建：

```text
programs/test_ble_button.py
```

写入：

```python
import asyncio

from bleak import BleakClient
from bleak import BleakScanner


# 这个 UUID 要和 Arduino 代码里的 SERVICE_UUID 一致。
# Python 扫描时会找带有这个 service 的设备。
SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"

# 这个 UUID 要和 Arduino 代码里的 CANDIDATE_UUID 一致。
# Python 连接后，会订阅这个 characteristic。
CANDIDATE_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


def handle_candidate(sender, data):
    # data 是 XIAO 通过 BLE 发来的 bytes。
    # Arduino 发送的是字符串 "1"，所以这里把 bytes 解码成普通文本。
    text = data.decode("utf-8", errors="ignore").strip()

    if text == "":
        return

    print("收到：", text)

    if text in ["0", "1", "2", "3", "4"]:
        print("candidate =", int(text))


async def async_main():
    print("开始扫描 BLE 设备...")

    # 扫描附近 BLE 设备。
    # 这里不按设备名找，因为有时 name / local_name 会显示成 None。
    # 直接找包含 SERVICE_UUID 的设备更稳定。
    device = await BleakScanner.find_device_by_filter(
        lambda d, adv: SERVICE_UUID.lower() in [
            uuid.lower() for uuid in adv.service_uuids
        ],
        timeout=20.0
    )

    if device is None:
        print("没有找到包含目标 service 的 BLE 设备")
        print("请确认 XIAO 已经上传 BLE 程序，并且正在供电。")
        return

    print("找到设备")
    print("name:", device.name)
    print("address:", device.address)
    print("开始连接...")

    # 连接 XIAO。
    async with BleakClient(device) as client:
        print("连接成功")
        print("等待 XIAO 定时发送 candidate = 1")
        print("按 Ctrl + C 退出")

        # 订阅 candidate characteristic。
        # XIAO 每次 notify 时，handle_candidate 会自动被调用。
        await client.start_notify(
            CANDIDATE_UUID,
            handle_candidate
        )

        while True:
            await asyncio.sleep(1)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
```

这里把真正的异步程序写在：

```python
async def async_main():
```

再用普通函数包装：

```python
def main():
    asyncio.run(async_main())
```

这样 `app.py` 仍然可以保持和前面一样的写法。

---

## 6. 修改 `app.py`

```python
from programs.test_ble_button import main


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

## 7. 正常现象

终端应该先显示：

```text
开始扫描 BLE 设备...
找到设备
name: None
address: ...
开始连接...
连接成功
等待 XIAO 定时发送 candidate = 1
```

之后大约每 2 秒显示一次：

```text
收到： 1
candidate = 1
```

`name` 显示成 `None` 没关系。只要设备的 `service_uuid` 能对上，Python 就能找到它。

---

## 8. 如果找不到设备

先确认 Arduino Serial Monitor 里有没有：

```text
BLE advertising start
```

如果没有，说明 XIAO 上的 BLE 程序可能没有正常启动。

如果 Arduino 端正常，但 Python 找不到设备，检查：

```text
电脑蓝牙是否打开
XIAO 是否正在供电
Python 是否安装 bleak
macOS 是否给 Terminal / VS Code 蓝牙权限
附近是否有其他程序已经连接了 XIAO
```

macOS 可以检查：

```text
系统设置
↓
隐私与安全性
↓
蓝牙
```

给当前运行 Python 的程序打开权限。

---

## 9. 成功标准

这一步完成后，应该做到：

```text
XIAO 能创建 BLE 设备
XIAO 能广播 service UUID
Python 能扫描到带有目标 service 的设备
Python 能连接 XIAO
Python 能订阅 candidate characteristic
XIAO 每隔 2 秒发送一次 "1"
Python 能收到 candidate = 1
```

下一步可以把定时发送改成按钮触发：

```text
D1 按钮按下
↓
XIAO 通过 BLE notify "1"
↓
Python 收到 candidate = 1
```
