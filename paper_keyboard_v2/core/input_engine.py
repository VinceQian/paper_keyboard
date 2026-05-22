class InputEngine:
    """
    InputEngine 是整个项目的“判断大脑”。

    它不关心摄像头、麦克风、OpenCV 窗口，也不负责保存文件。
    它只做一件事：

        给我一帧数据，我判断这一帧有没有确认输入一个按键。
    """

    def __init__(self, layout):
        self.layout = layout
        self.output_text = ""

        # True 表示：上一帧已经听到了敲击声，
        # 现在要等声音消失后，才允许下一次输入。
        self.waiting_for_audio_release = False

    def reset(self):
        """清空已经输出的文字，并重置状态。"""
        self.output_text = ""
        self.waiting_for_audio_release = False

    def update(self, frame):
        """
        处理一帧 session 数据。

        输入 frame 的格式大致是：
        {
            "frame_id": 1,
            "t": 0.033,
            "fingers": [
                {"id": "index", "x": 105.2, "y": 82.4}
            ],
            "tap": {"audio": true}
        }

        返回 result 的格式是：
        {
            "pressed": True / False,
            "key": "A" 或 None,
            "current_key": "A" 或 None,
            "output_text": 当前累计输出文字
        }
        """
        finger = self._get_index_finger(frame)
        current_key = self._find_key_by_finger(finger)
        audio_tap = self._has_audio_tap(frame)

        pressed = False
        pressed_key = None

        if not audio_tap:
            # 没有敲击声，说明这次 tap 已经结束，可以等待下一次 tap。
            self.waiting_for_audio_release = False
        else:
            # 有敲击声，但如果上一帧已经处理过这次声音，就不要重复输出。
            if not self.waiting_for_audio_release:
                self.waiting_for_audio_release = True

                if current_key is not None:
                    pressed = True
                    pressed_key = current_key
                    self.output_text += pressed_key

        return {
            "frame_id": frame.get("frame_id"),
            "t": frame.get("t"),
            "pressed": pressed,
            "key": pressed_key,
            "current_key": current_key,
            "output_text": self.output_text,
        }

    def _get_index_finger(self, frame):
        """从一帧数据里找到食指坐标。找不到就返回 None。"""
        fingers = frame.get("fingers", [])

        for finger in fingers:
            if finger.get("id") == "index":
                return finger

        return None

    def _has_audio_tap(self, frame):
        """判断这一帧有没有音频敲击信号。"""
        tap = frame.get("tap", {})
        return tap.get("audio", False) == True

    def _find_key_by_finger(self, finger):
        """根据食指坐标判断当前在哪个按键里。"""
        if finger is None:
            return None

        x = finger.get("x")
        y = finger.get("y")

        if x is None or y is None:
            return None

        return self._find_key_at_position(x, y)

    def _find_key_at_position(self, x, y):
        """判断一个纸面坐标点落在哪个 key 里。"""
        for key in self.layout["keys"]:
            key_x = key["x"]
            key_y = key["y"]
            key_w = key["w"]
            key_h = key["h"]

            inside_x = key_x <= x <= key_x + key_w
            inside_y = key_y <= y <= key_y + key_h

            if inside_x and inside_y:
                return key["label"]

        return None
