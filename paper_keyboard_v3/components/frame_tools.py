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

    找到就返回：
        {
            "finger_id": 1,
            "x": 132.4,
            "y": 78.6
        }

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

    x = finger["x"]
    y = finger["y"]

    return x, y


def get_current_key_id(frame, key_finder):
    """
    根据当前 frame 判断候选手指所在的按键。

    逻辑：
        1. 读取 tap.candidate
        2. 找到 candidate 对应的 finger
        3. 读取这个 finger 的纸面坐标
        4. 用 KeyFinder 判断它在哪个按键上

    返回：
        如果候选手指落在某个键上，返回 key_id。
        如果没有候选手指，或者不在任何键上，返回 None。
    """
    candidate_finger = get_candidate_finger(frame)
    position = get_finger_position(candidate_finger)

    if position is None:
        return None

    x, y = position
    key_id = key_finder.find_key(x, y)

    return key_id


def get_first_finger(frame):
    """
    从 frame 中取出第一个手指。

    这个函数主要保留给早期 replay_session 兼容使用。
    当前主流程更推荐用 get_candidate_finger()。
    """
    fingers = get_fingers(frame)

    if len(fingers) == 0:
        return None

    return fingers[0]


def get_first_finger_position(frame):
    """
    从 frame 中取出第一个手指的坐标。

    这个函数主要保留给早期 replay_session 兼容使用。
    当前主流程更推荐用 get_current_key_id()。
    """
    finger = get_first_finger(frame)

    if finger is None:
        return None

    return get_finger_position(finger)


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
    print("first finger:", get_first_finger(test_frame))
    print("first finger position:", get_first_finger_position(test_frame))


if __name__ == "__main__":
    main()