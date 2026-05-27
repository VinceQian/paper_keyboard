import json


class SessionSource:
    """
    从 session JSON 文件中读取 frame 数据。

    这个类模拟一个输入源。
    以后真实摄像头、麦克风、颜色贴纸等输入源，
    最终也应该尽量整理成类似的 frame 格式。

    这样后面的 components 不需要关心数据到底来自哪里。
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

    def get_frames(self):
        """返回所有 frame。"""
        return self.frames


def main():
    source = SessionSource("paper_keyboard_v3/data/sessions/test_number_input_123.json")

    print("session_id:", source.get_session_id())
    print("layout_id:", source.get_layout_id())
    print("frame 数量:", len(source.get_frames()))
    print()

    for frame in source.get_frames():
        frame_id = frame["frame_id"]
        t = frame["t"]

        fingers = frame.get("fingers", [])
        tap = frame.get("tap", {})
        audio_tap = tap.get("audio", False)

        if len(fingers) > 0:
            finger = fingers[0]
            x = finger["x"]
            y = finger["y"]
            print(f"frame {frame_id}, t={t:.2f}, finger=({x}, {y}), audio={audio_tap}")
        else:
            print(f"frame {frame_id}, t={t:.2f}, finger=None, audio={audio_tap}")


if __name__ == "__main__":
    main()