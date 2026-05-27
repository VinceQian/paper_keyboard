class InputDecider:
    """
    判断某一帧是否产生一次有效按键输入。

    这个类不负责：
    1. 识别手指位置
    2. 判断手指在哪个键上
    3. 保存最终输入文本

    它只负责判断：
    当前这一帧，是否应该算作一次真正的按键。
    """

    def __init__(self):
        # 记录上一帧是否检测到了敲击声音
        self.last_audio_tap = False

    def get_audio_tap(self, frame):
        """
        从 frame 中读取 tap.audio。

        如果 frame 里没有 tap 或 audio，
        就默认认为没有检测到敲击。
        """
        tap_info = frame.get("tap", {})
        return tap_info.get("audio", False)

    def decide_key(self, frame, current_key):
        """
        判断当前帧是否产生有效按键。

        参数：
            frame: 当前帧数据
            current_key: 当前手指所在的按键，例如 "1"、"2"、"0"
                         如果手指不在任何键上，则是 None

        返回：
            如果产生有效输入，返回按键 id
            如果没有产生有效输入，返回 None
        """
        current_audio_tap = self.get_audio_tap(frame)

        # 条件 1：当前手指必须在某个键上
        has_key = current_key is not None

        # 条件 2：这一帧必须检测到敲击
        has_tap = current_audio_tap is True

        # 条件 3：上一帧不能已经检测到敲击
        # 这样可以避免同一次敲击被连续多帧重复记录
        is_new_tap = self.last_audio_tap is False and current_audio_tap is True

        if has_key and has_tap and is_new_tap:
            result = current_key
        else:
            result = None

        # 更新状态，给下一帧使用
        self.last_audio_tap = current_audio_tap

        return result


def main():
    decider = InputDecider()

    test_frames = [
        {
            "frame_id": 1,
            "tap": {
                "audio": False
            }
        },
        {
            "frame_id": 2,
            "tap": {
                "audio": True
            }
        },
        {
            "frame_id": 3,
            "tap": {
                "audio": True
            }
        },
        {
            "frame_id": 4,
            "tap": {
                "audio": False
            }
        },
        {
            "frame_id": 5,
            "tap": {
                "audio": True
            }
        }
    ]

    test_keys = ["1", "1", "1", "1", "2"]

    for frame, key in zip(test_frames, test_keys):
        result = decider.decide_key(frame, key)
        print(f"frame {frame['frame_id']} -> 输入：{result}")


if __name__ == "__main__":
    main()