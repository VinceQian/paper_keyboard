# Step 11：硬件按钮版纸面键盘

这一步把 Step 7 的声音输入版改成硬件按钮输入版。

Step 7 的数据流是：

```text
食指位置 -> current_key
声音超过阈值 -> candidate = 1
candidate 触发时 -> 输入食指所在的 key
```

Step 11 改成：

```text
食指位置 -> current_key
D1 按钮按下 -> XIAO 串口发送 1
SerialTapSource 读到 1 -> candidate = 1
candidate 触发时 -> 输入食指所在的 key
```

这一步不需要重写视觉部分，也不需要改 `FrameBuilder`、`KeyFinder`、`InputDecider`、`TextBuffer`。

核心变化只有一个：

```text
AudioSource
↓
SerialTapSource
```

---

## 1. 新建文件

复制 Step 7 的文件：

```text
programs/audio_keyboard.py
```

改名为：

```text
programs/hardware_keyboard.py
```

后面的修改都在 `programs/hardware_keyboard.py` 里完成。

---

## 2. 修改 import

找到 Step 7 里的声音输入：

```python
from input_sources.audio_source import AudioSource
```

改成串口输入：

```python
from input_sources.serial_tap_source import SerialTapSource
```

---

## 3. 设置串口端口

在 import 后面加上串口端口。

```python
PORT = "/dev/cu.usbmodem1101"
```

这里要改成 Step 9 / Step 10 已经测试成功的端口。

---

## 4. 把 `AudioSource` 换成 `SerialTapSource`

找到 Step 7 里创建 `audio_source` 的代码：

```python
audio_source = AudioSource(
    threshold=0.04,
    cooldown=0.25,
    candidate_id=1
)
```

改成：

```python
tap_source = SerialTapSource(
    port=PORT,
    baudrate=115200
)
```

这里的 `tap_source` 表示：

```text
输入触发来源
```

在 Step 7 里，它来自声音。

在 Step 11 里，它来自 XIAO 串口按钮。

---

## 5. 修改 `FrameBuilder`

找到 Step 7 里的：

```python
frame_builder = FrameBuilder(
    paper_mapper,
    hand_source,
    audio_source
)
```

改成：

```python
frame_builder = FrameBuilder(
    paper_mapper,
    hand_source,
    tap_source
)
```

`FrameBuilder` 不需要改，因为 `AudioSource` 和 `SerialTapSource` 都有同一个接口：

```python
get_candidate()
```

所以 `FrameBuilder` 只需要知道：

```python
candidate = tap_source.get_candidate()
```

不需要关心 candidate 是声音产生的，还是按钮产生的。

---

## 6. 删除声音启动代码

Step 7 里有：

```python
audio_source.start()
```

硬件按钮版不需要这一行，直接删掉。

`SerialTapSource` 在创建对象时已经打开串口，后面可以直接读取。

---

## 7. 修改退出时的关闭代码

找到 Step 7 结尾的：

```python
audio_source.stop()
```

改成：

```python
tap_source.close()
```

完整退出顺序可以保持类似这样：

```python
tap_source.close()
hand_source.close()
camera.release()
cv2.destroyAllWindows()
```

---

## 8. 删除音量显示

Step 7 里有显示当前音量的代码：

```python
cv2.putText(
    image,
    "volume: " + str(round(audio_source.get_volume(), 3)),
    (30, 120),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.0,
    (0, 255, 255),
    2
)
```

硬件按钮版不需要显示音量，直接删掉。

保留这些显示即可：

```text
current key
text
```

---

## 9. 修改提示文字

把 Step 7 的：

```python
print("声音输入纸面键盘开始")
print("把食指放到某个 key 上，然后敲击纸面")
```

改成：

```python
print("硬件按钮纸面键盘开始")
print("把食指放到某个 key 上，然后按 D1 按钮")
```

窗口标题也可以从：

```python
cv2.imshow("Paper Keyboard - Audio Keyboard", image)
```

改成：

```python
cv2.imshow("Paper Keyboard - Hardware Keyboard", image)
```

---

## 10. 不需要改的部分

其他函数和逻辑都可以继续沿用 Step 7 的版本：
也就是说，这一步不是重写一个新程序，而是在 Step 7 的基础上替换输入源。

---

## 11. 修改 `app.py`

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

## 12. 成功标准

画面里应该看到：

```text
纸面边框
蓝色按键框
当前 key 黄色高亮
手部骨架
指尖红点和 finger_id
当前文本 text
```

测试方式：

```text
食指放在 1 上
按 D1 按钮
输入 1

食指放在 5 上
按 D1 按钮
输入 5
```

终端应该打印类似：

```text
输入： 1
当前文本： 1
```

这一步完成后，硬件按钮版纸面键盘就跑通了：

```text
视觉负责判断手指在哪个 key 上
硬件按钮负责触发输入
TextBuffer 保存输入结果
```

下一步可以扩展成多指输入：

```text
D1 -> candidate = 1
D2 -> candidate = 2
D3 -> candidate = 3
```
