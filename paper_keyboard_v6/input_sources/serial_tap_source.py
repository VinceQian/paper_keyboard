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
        if line == "2":
            return 1

        # 其他内容暂时都忽略。
        return -1

    def close(self):
        self.ser.close()