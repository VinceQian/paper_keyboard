def get_fingers(frame):
    """
    从 frame 中读取 fingers 列表。

    如果没有 fingers 字段，就返回空列表。
    """
    return frame.get("fingers", [])


def get_candidate(frame):
    """
    从 frame 中读取 tap.candidate。

    当前规则：
        -1 表示没有输入候选
         0-9 表示某个手指是输入候选
    """
    tap_info = frame.get("tap", {})
    return tap_info.get("candidate", -1)


def find_finger_by_id(frame, target_finger_id):
    """
    根据 finger_id 从 frame 中找到对应手指。

    找到就返回该 finger。
    找不到就返回 None。
    """
    fingers = get_fingers(frame)

    for finger in fingers:
        if finger["finger_id"] == target_finger_id:
            return finger

    return None


def get_candidate_finger(frame):
    """
    根据 tap.candidate 找到当前候选手指。

    如果 candidate == -1，返回 None。
    如果 candidate 对应的手指不在 fingers 里，也返回 None。
    """
    candidate = get_candidate(frame)

    if candidate == -1:
        return None

    return find_finger_by_id(frame, candidate)


def get_finger_position(finger):
    """
    从 finger 中读取纸面坐标。

    返回：
        (x, y)

    如果 finger 是 None，返回 None。
    """
    if finger is None:
        return None

    return finger["x"], finger["y"]


def get_current_key_id(frame, key_finder):
    """
    根据当前 frame 判断候选手指所在的按键。

    这个函数用于输入判断：
        只有 tap.candidate 指向的手指才会被检查。

    返回：
        如果候选手指落在某个键上，返回 key_id。
        如果没有候选手指，或者不在任何键上，返回 None。
    """
    candidate_finger = get_candidate_finger(frame)
    position = get_finger_position(candidate_finger)

    if position is None:
        return None

    x, y = position
    return key_finder.find_key(x, y)


def get_key_id_for_finger(frame, finger_id, key_finder):
    """
    判断指定 finger_id 当前所在的按键。

    这个函数用于显示或测试：
        它不看 tap.candidate。
        即使当前没有敲击，也可以查看某个手指指向哪个 key。

    例如：
        finger_id = 1 表示右手食指。
    """
    finger = find_finger_by_id(frame, finger_id)
    position = get_finger_position(finger)

    if position is None:
        return None

    x, y = position
    return key_finder.find_key(x, y)


def main():
    test_frame = {
        "frame_id": 1,
        "t": 0.03,
        "fingers": [
            {
                "finger_id": 1,
                "x": 132.4,
                "y": 78.6
            },
            {
                "finger_id": 2,
                "x": 160.0,
                "y": 80.0
            }
        ],
        "tap": {
            "candidate": 1
        }
    }

    print("fingers:", get_fingers(test_frame))
    print("candidate:", get_candidate(test_frame))
    print("candidate finger:", get_candidate_finger(test_frame))
    print("candidate position:", get_finger_position(get_candidate_finger(test_frame)))


if __name__ == "__main__":
    main()