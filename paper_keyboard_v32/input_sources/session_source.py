import json


class SessionSource:
    """
    从 session JSON 文件中读取 frame 数据。

    这个类模拟一个输入源。
    以后真实摄像头、麦克风、指套按钮等输入源，
    最终也应该整理成类似的 frame 格式。

    当前 frame 格式示例：

    {
        "frame_id": 1,
        "t": 0.03,
        "fingers": [
            {
                "finger_id": 1,
                "x": 57,
                "y": 82
            }
        ],
        "tap": {
            "candidate": 1
        }
    }

    tap.candidate 规则：
        -1:
            没有输入触发。

        0-9:
            某个 finger_id 触发输入。
            当前基础版通常只会用到 1，也就是右手食指。
    """

    def __init__(self, session_path):
        self.session_path = session_path
        self.session = self.load_session(session_path)
        self.frames = self.session["frames"]

    def load_session(self, session_path):
        """读取 session JSON 文件。"""
        with open(session_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_session_id(self):
        """返回 session 的 id。"""
        return self.session["session_id"]

    def get_layout_id(self):
        """返回这个 session 对应的键盘布局 id。"""
        return self.session["layout_id"]

    def get_unit(self):
        """返回 session 使用的坐标单位。"""
        return self.session.get("unit", "mm")

    def get_frames(self):
        """返回所有 frame。"""
        return self.frames


def main():
    source = SessionSource("data/sessions/test_number_input_123.json")

    print("session_id:", source.get_session_id())
    print("layout_id:", source.get_layout_id())
    print("unit:", source.get_unit())
    print("frame 数量:", len(source.get_frames()))
    print()

    for frame in source.get_frames():
        frame_id = frame["frame_id"]
        t = frame["t"]

        fingers = frame.get("fingers", [])
        tap = frame.get("tap", {})
        candidate = tap.get("candidate", -1)

        print(
            f"frame {frame_id}, "
            f"t={t:.2f}, "
            f"fingers={len(fingers)}, "
            f"candidate={candidate}"
        )


if __name__ == "__main__":
    main()