def get_first_finger(frame):
    """
    从 frame 中取出第一个手指。

    当前版本先只处理一个手指。
    如果没有检测到手指，就返回 None。
    """
    fingers = frame.get("fingers", [])

    if len(fingers) == 0:
        return None

    return fingers[0]


def get_first_finger_position(frame):
    """
    从 frame 中取出第一个手指的坐标。

    返回：
        如果有手指，返回 (x, y)
        如果没有手指，返回 None
    """
    finger = get_first_finger(frame)

    if finger is None:
        return None

    x = finger["x"]
    y = finger["y"]

    return x, y


def get_audio_tap(frame):
    """
    从 frame 中读取 tap.audio。

    如果 frame 里没有 tap 或 audio，
    就默认认为没有检测到敲击声音。
    """
    tap_info = frame.get("tap", {})
    return tap_info.get("audio", False)


def main():
    test_frame = {
        "frame_id": 1,
        "t": 0.03,
        "fingers": [
            {
                "finger_id": 1,
                "x": 25,
                "y": 25
            }
        ],
        "tap": {
            "audio": True
        }
    }

    finger = get_first_finger(test_frame)
    position = get_first_finger_position(test_frame)
    audio_tap = get_audio_tap(test_frame)

    print("第一个手指：", finger)
    print("第一个手指坐标：", position)
    print("是否检测到敲击声音：", audio_tap)


if __name__ == "__main__":
    main()