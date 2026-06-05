def get_candidate(frame):
    """
    从 frame 中读取 tap.candidate。

    当前规则：
        -1 表示没有输入候选
         0-9 表示某个手指是输入候选
    """
    return frame["tap"]["candidate"]


def get_finger_position_by_id(frame, finger_id):
    """
    根据 finger_id 从 frame 中读取对应手指的位置。

    当前 fingers 是 dict 格式：

    "fingers": {
        "1": {
            "x": 57,
            "y": 82
        }
    }

    注意：
        JSON 里的 key 是字符串。
        所以 finger_id 需要先转成字符串再查找。

    返回：
        如果找到对应手指，返回 (x, y)
        如果找不到，返回 None
    """
    fingers = frame["fingers"]

    finger = fingers.get(str(finger_id))

    if finger is None:
        return None

    return finger["x"], finger["y"]


def main():
    test_frame = {
        "frame_id": 1,
        "t": 0.03,
        "fingers": {
            "1": {
                "x": 132.4,
                "y": 78.6
            },
            "2": {
                "x": 160.0,
                "y": 80.0
            }
        },
        "tap": {
            "candidate": 1
        }
    }

    candidate = get_candidate(test_frame)
    position = get_finger_position_by_id(test_frame, candidate)

    print("candidate:", candidate)
    print("candidate position:", position)

    position = get_finger_position_by_id(test_frame, 2)
    print("finger 2 position:", position)

    position = get_finger_position_by_id(test_frame, 3)
    print("finger 3 position:", position)


if __name__ == "__main__":
    main()