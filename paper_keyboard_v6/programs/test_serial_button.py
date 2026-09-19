import time

import serial


PORT = "/dev/cu.usbmodem1101"
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

    # XIAO 连接后可能会重启，稍微等一下再开始读。
    time.sleep(2)

    try:
        while True:
            line = ser.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if line == "":
                continue

            print("收到：", line)

            if line == "2":
                print("candidate = 2")

    except KeyboardInterrupt:
        print("用户退出")

    finally:
        ser.close()
        print("串口已关闭")


if __name__ == "__main__":
    main()