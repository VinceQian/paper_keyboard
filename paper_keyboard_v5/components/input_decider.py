class InputDecider:
    """
    判断 candidate 是否产生一次新的输入触发。

    它不关心 frame 的完整结构。
    它只关心 candidate 这个数值。

    candidate 的含义：
        -1:
            当前没有输入触发。

        0-9:
            某个手指触发了输入。
    """

    def __init__(self):
        # 记录上一帧的 candidate
        # 用来避免同一次触发持续多帧时重复输入
        self.last_candidate = -1

    def decide_candidate(self, candidate):
        """
        判断当前 candidate 是否是一次新的触发。

        返回：
            如果是新的触发，返回 candidate。
            如果不是新的触发，返回 None。
        """
        is_new_input = (
            self.last_candidate == -1
            and candidate != -1
        )

        self.last_candidate = candidate

        if is_new_input:
            return candidate

        return None


def main():
    decider = InputDecider()

    candidates = [-1, 1, 1, -1, 0, 0, -1, 2]

    for candidate in candidates:
        result = decider.decide_candidate(candidate)
        print("candidate:", candidate, "-> 新输入:", result)


if __name__ == "__main__":
    main()