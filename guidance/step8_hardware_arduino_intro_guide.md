# Step 8：硬件、接线与 Arduino 工具入门

从这一步开始，我们要进入硬件输入部分。

前面 Step 7 的输入来源是声音：

```text
声音超过阈值 -> candidate = 1
```

后面的硬件版会改成：

```text
按钮被按下 -> candidate = 1
```

这一步是基础的硬件入门：

```text
认识 XIAO / ESP32
↓
认识 VCC / GND / GPIO
↓
用 Arduino IDE 上传程序
↓
用 Serial Monitor 查看开发板输出
↓
控制 LED 模块亮灭
↓
读取按钮状态
↓
用按钮控制 LED 模块
↓
用按钮控制板载 LED
```

这一步不会修改前面的 Python 项目文件。

---

## 1. 这一步需要的材料

准备：

```text
XIAO ESP32C6
USB 数据线
面包板
排针
按钮
LED 模块
杜邦线
电脑
Arduino IDE
```

注意：

```text
USB 数据线必须能传数据，不能只是充电线。
```

因为这根 USB 线会同时负责：

```text
给 XIAO 供电
把 Arduino 程序上传到 XIAO
让 XIAO 通过串口把信息发回电脑
```

---

## 2. 临时连接 XIAO 的方式

XIAO 的排针正常情况下需要焊接。

不过在前期测试时，可以先不焊接临时使用：

```text
排针插在面包板上
↓
XIAO 对准排针压上去
↓
用面包板和杜邦线完成临时测试
```

后面测试完成后做稳定的手套 / 手腕模块时，再进行焊接。

---

## 3. 认识 XIAO / ESP32

XIAO ESP32C6 可以理解成一台很小的电脑。

它可以：

```text
运行上传进去的程序
读取按钮状态
控制引脚输出
通过 USB 串口把信息发给电脑
```

程序上传到 XIAO 之后，XIAO 会自己运行这个程序。

电脑这时主要负责：

```text
写代码
上传代码
查看串口输出
```

---

## 4. 接线时先分清三种角色

硬件接线时，经常会遇到三类引脚：

| 名称 | 作用 |
|---|---|
| `3V3` / `VCC` | 给模块供电 |
| `GND` | 共同的 0V 参考点 |
| `GPIO` / `D0` / `D1` | 程序可以读取或控制的信号引脚 |

这一步里会看到两种 GPIO 用法：

```text
D0：输出，用来控制 LED 模块
D1：输入，用来读取按钮状态
```

重要规则：

```text
ESP32 / XIAO 的 GPIO 按 3.3V 逻辑使用。
不要把 5V 或更高电压直接接到 GPIO。
不要让 3V3 和 GND 短接。
改线前先断开 USB 或断电。
```

---

## 5. Arduino IDE 是什么

Arduino IDE 是用来开发微控制器程序的软件。

这节课里，它主要用来做四件事：

```text
写 ESP32 程序
编译程序
把程序上传到 XIAO
打开 Serial Monitor 查看 XIAO 发回电脑的信息
```

打开 Arduino IDE 后，需要确认三件事：

```text
Board：选择 XIAO ESP32C6
Port：选择 XIAO 对应的串口
Serial Monitor baud：选择 115200
```

安装 Arduino IDE 后里面不会有 ESP32 开发板信息，需要先安装 ESP32 board package。

---

## 6. Arduino 程序的基本结构

Arduino 程序通常从下面这个结构开始：

```cpp
void setup() {

}

void loop() {

}
```

可以先这样理解：

```text
setup()：开发板启动后执行一次
loop()：setup() 结束后一直重复执行
```

也就是说：

```text
初始化设置放在 setup()
需要持续运行的事情放在 loop()
```

---

## 7. 测试 1：Serial Monitor 输出

先只插 USB。

在 Arduino IDE 里上传下面的程序：

```cpp
void setup() {
    // 开启串口通信。
    // Serial Monitor 里也要选择 115200 baud。
    Serial.begin(115200);

    // 刚启动时等一小会儿，给 Serial Monitor 连接时间。
    delay(1500);

    Serial.println("XIAO ESP32C6 start");
}

void loop() {
    // 每隔 1 秒向电脑发送一行 running。
    Serial.println("running");
    delay(1000);
}
```

上传完成后，打开 Serial Monitor，并选择：

```text
115200 baud
```

如果一切正常，应该能看到：

```text
XIAO ESP32C6 start
running
running
running
...
```

这一步确认的是：

```text
USB 线可以传数据
Arduino IDE 能上传程序
Board 和 Port 选择正确
XIAO 可以通过串口把信息发回电脑
```

---

## 8. 认识 LED 模块

LED 模块一般有三个引脚：

| 引脚 | 含义 |
|---|---|
| `G` | GND，接地 |
| `V` | VCC，接 3V3 |
| `S` | Signal，接 GPIO |

这一步用 `D0` 控制 LED 模块：

```text
LED G -> XIAO GND
LED V -> XIAO 3V3
LED S -> XIAO D0
```

---

## 9. 测试 2：控制 LED 模块闪烁

先断开 USB，再完成 LED 模块接线。

接好后，插回 USB，上传下面的程序：

```cpp
const int LED_PIN = D0;

void setup() {
    // 把 LED_PIN 设置成输出模式。
    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    // 输出 HIGH，LED 模块亮。
    digitalWrite(LED_PIN, HIGH);
    delay(500);

    // 输出 LOW，LED 模块灭。
    digitalWrite(LED_PIN, LOW);
    delay(500);
}
```

正常现象：

```text
LED 模块每 0.5 秒亮灭一次。
```

这一步要理解：

```text
D0 是输出 GPIO。
digitalWrite() 可以控制 D0 输出 HIGH 或 LOW。
LED 模块根据 D0 的输出亮灭。
```

---

## 10. 认识按钮输入

按钮可以理解成一个开关。

这次我们使用一种简单接法：

```text
按钮一端 -> GPIO
按钮另一端 -> GND
```

代码里使用：

```cpp
pinMode(BUTTON_PIN, INPUT_PULLUP);
```

`INPUT_PULLUP` 表示打开内部上拉。

现象是：

```text
没按按钮：GPIO 默认读到 HIGH
按下按钮：GPIO 被接到 GND，读到 LOW
```

```text
LOW  表示按下
HIGH 表示松开
```

---

## 11. 接一个按钮

先断开 USB，再接线。

推荐先用 `D1` 做按钮引脚：

```text
按钮一端 -> XIAO D1
按钮另一端 -> XIAO GND
```

不要把按钮接到：

```text
3V3 和 GND 之间
```

这一步按钮只需要：

```text
D1
GND
```

接好后，再插回 USB。

---

## 12. 测试 3：读取按钮状态

上传下面的程序：

```cpp
const int LED_PIN = D0;
const int BUTTON_PIN = D1;

void setup() {
    Serial.begin(115200);
    delay(1500);

    // LED_PIN 暂时只设置成输出。
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    // 把按钮引脚设置成输入，并打开内部上拉。
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    Serial.println("button test start");
}

void loop() {
    // 读取按钮引脚当前是 HIGH 还是 LOW。
    int buttonState = digitalRead(BUTTON_PIN);

    // 使用 INPUT_PULLUP 时：
    // 按下按钮 -> LOW
    // 松开按钮 -> HIGH
    if (buttonState == LOW) {
        Serial.println("pressed");
    } else {
        Serial.println("released");
    }

    delay(200);
}
```

打开 Serial Monitor，保持：

```text
115200 baud
```

正常现象：

```text
松开按钮：released
按下按钮：pressed
```

---

## 13. 测试 4：用按钮控制 LED 模块

上传下面的程序：

```cpp
const int LED_PIN = D0;
const int BUTTON_PIN = D1;

void setup() {
    Serial.begin(115200);
    delay(1500);

    // D0 是输出，用来控制 LED 模块。
    pinMode(LED_PIN, OUTPUT);

    // D1 是输入，用来读取按钮。
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    Serial.println("button controls led start");
}

void loop() {
    int buttonState = digitalRead(BUTTON_PIN);

    if (buttonState == LOW) {
        digitalWrite(LED_PIN, HIGH);
        Serial.println("pressed");
    } else {
        digitalWrite(LED_PIN, LOW);
        Serial.println("released");
    }

    delay(200);
}
```

正常现象：

```text
松开按钮：LED 模块灭，Serial Monitor 显示 released
按下按钮：LED 模块亮，Serial Monitor 显示 pressed
```

这一步要理解：

```text
D1 是输入，用来读取按钮。
D0 是输出，用来控制 LED。
程序根据 D1 的状态，决定 D0 输出 HIGH 还是 LOW。
```

---

## 14. 测试 5：用按钮控制板载 LED

把 `LED_PIN` 改成板载 LED：

```cpp
const int LED_PIN = LED_BUILTIN;
const int BUTTON_PIN = D1;
```

完整程序：

```cpp
const int LED_PIN = LED_BUILTIN;
const int BUTTON_PIN = D1;

void setup() {
    Serial.begin(115200);
    delay(1500);

    pinMode(LED_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    Serial.println("button controls onboard led start");
}

void loop() {
    int buttonState = digitalRead(BUTTON_PIN);

    if (buttonState == LOW) {
        digitalWrite(LED_PIN, HIGH);
        Serial.println("pressed");
    } else {
        digitalWrite(LED_PIN, LOW);
        Serial.println("released");
    }

    delay(200);
}
```

正常现象：

```text
松开按钮：板载 LED 灭，Serial Monitor 显示 released
按下按钮：板载 LED 亮，Serial Monitor 显示 pressed
```

如果板载 LED 没有反应，可以把：

```cpp
const int LED_PIN = LED_BUILTIN;
```

改成：

```cpp
const int LED_PIN = 15;
```

如果亮灭状态相反，可以把 `HIGH` 和 `LOW` 对调。

---

## 15. 常见问题

如果 Serial Monitor 没有输出，先检查：

```text
有没有选对 Port
Serial Monitor 是不是 115200 baud
程序有没有上传成功
USB 线是不是数据线
```

如果 LED 模块没有亮灭，检查：

```text
LED G / V / S 有没有接对
LED S 是否接到了 D0
代码里的 LED_PIN 是否是 D0
```

如果一直显示 `pressed`，检查：

```text
按钮是不是插错了方向
D1 是否一直被接到了 GND
按钮两端是不是接在了本来就连通的同一侧
```

如果一直显示 `released`，检查：

```text
按钮按下时 D1 和 GND 是否真的连通
XIAO 是否和排针接触稳定
杜邦线有没有插错孔
```

如果显示在 `pressed` 和 `released` 之间乱跳，检查：

```text
XIAO 有没有压紧排针
线有没有晃动
按钮是否接触不良
面包板上的线是否松动
```

---

## 16. 成功标准

这一步完成后，应该做到：

```text
明白基础的接线知识
养成良好的接线习惯
能上传 Serial 输出程序
能在 Serial Monitor 里看到 running
能控制 LED 模块亮灭
能用 INPUT_PULLUP 读取一个按钮
能用按钮控制 LED 模块
能用按钮控制板载 LED
按下按钮时看到 pressed
松开按钮时看到 released
```

下一步会把按钮输出改成项目需要的格式：

```text
按下按钮 -> Serial.println("1")
```

然后用 Python 读取这个串口输出。
