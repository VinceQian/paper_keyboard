class InputDecider:
    """
    判断某一帧是否产生一次有效按键输入。

    当前版本使用 frame["tap"]["candidate"] 判断输入触发。

    tap.candidate 的含义：
        -1: 当前没有候选输入
         1: 当前候选输入来源是右手食指

    当前基础版只支持右手食指，所以 candidate 只会是 -1 或 1。
    后续多指版本可以扩展为 -1 到 9。
    """

    def __init__(self):
        # 记录上一帧的 candidate
        # 用来避免同一次敲击持续多帧时重复输入
        self.last_candidate = -1

    def get_candidate(self, frame):
        """
        从 frame 中读取 tap.candidate。

        如果 frame 里没有 tap 或 candidate，
        就默认认为没有候选输入。
        """
        tap_info = frame.get("tap", {})
        return tap_info.get("candidate", -1)

    def decide_key(self, frame, current_key_id):
        """
        判断当前帧是否产生有效按键。

        参数：
            frame:
                当前帧数据。

            current_key_id:
                当前候选手指所在的按键 id。
                例如 "1"、"2"、"0"。
                如果候选手指不在任何按键上，则是 None。

        返回：
            如果产生有效输入，返回按键 id。
            如果没有产生有效输入，返回 None。
        """
        current_candidate = self.get_candidate(frame)

        has_key = current_key_id is not None

        # 当前基础版里，candidate != -1 就表示有输入候选
        has_candidate = current_candidate != -1

        # candidate 从 -1 变成 1 的这一帧，才算一次新的输入
        is_new_candidate = (
            self.last_candidate == -1
            and current_candidate != -1
        )

        if has_key and has_candidate and is_new_candidate:
            result = current_key_id
        else:
            result = None

        self.last_candidate = current_candidate

        return result


def main():
    decider = InputDecider()

    test_frames = [
        {
            "frame_id": 1,
            "tap": {
                "candidate": -1
            }
        },
        {
            "frame_id": 2,
            "tap": {
                "candidate": 1
            }
        },
        {
            "frame_id": 3,
            "tap": {
                "candidate": 1
            }
        },
        {
            "frame_id": 4,
            "tap": {
                "candidate": -1
            }
        },
        {
            "frame_id": 5,
            "tap": {
                "candidate": 1
            }
        }
    ]

    test_key_ids = ["1", "1", "1", "1", "2"]

    for frame, key_id in zip(test_frames, test_key_ids):
        result = decider.decide_key(frame, key_id)
        print(f"frame {frame['frame_id']} -> 输入：{result}")


if __name__ == "__main__":
    main()