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