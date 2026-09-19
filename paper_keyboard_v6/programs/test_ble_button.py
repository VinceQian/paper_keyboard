import asyncio

from bleak import BleakClient
from bleak import BleakScanner


SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
CANDIDATE_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


def handle_candidate(sender, data):
    # data 是 XIAO 通过 BLE 发来的 bytes。
    # Arduino 那边发的是字符串 "1"，这里把它解码成普通文本。
    text = data.decode("utf-8", errors="ignore").strip()

    if text == "":
        return

    print("收到：", text)

    if text in ["0", "1", "2", "3", "4"]:
        print("candidate =", int(text))


async def async_main():
    print("开始扫描 BLE 设备...")

    # 不再按名字找，因为 macOS 扫描结果里 name 可能是 None。
    # 直接找带有 SERVICE_UUID 的设备。
    device = await BleakScanner.find_device_by_filter(
        lambda d, adv: SERVICE_UUID.lower() in [
            uuid.lower() for uuid in adv.service_uuids
        ],
        timeout=20.0
    )

    if device is None:
        print("没有找到包含目标 service 的 BLE 设备")
        return

    print("找到设备")
    print("name:", device.name)
    print("address:", device.address)
    print("开始连接...")

    async with BleakClient(device) as client:
        print("连接成功")
        print("按 D1 按钮，终端应该显示 candidate = 1")

        # 订阅 candidate characteristic。
        # 之后 XIAO notify 的时候，handle_candidate 会自动被调用。
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