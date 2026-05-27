import json


class ManualSource:
    """
    用代码生成模拟输入 frame。

    这个类主要用于测试：
    不需要摄像头，也不需要麦克风，
    直接用一段字符串生成模拟输入数据。
    """

    def __init__(self, layout_path):
        self.layout_path = layout_path
        self.layout = self.load_layout(layout_path)
        self.key_centers = self.build_key_centers()

    def load_layout(self, layout_path):
        """读取键盘布局 JSON 文件。"""
        with open(layout_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def build_key_centers(self):
        """
        根据 layout 计算每个按键的中心点。

        例如一个按键：
        {
            "id": "1",
            "x": 20,
            "y": 20,
            "w": 20,
            "h": 22
        }

        它的中心点就是：
        x = 20 + 20 / 2
        y = 20 + 22 / 2
        """
        key_centers = {}

        for key in self.layout["keys"]:
            key_id = key["id"]
            center_x = key["x"] + key["w"] / 2
            center_y = key["y"] + key["h"] / 2

            key_centers[key_id] = {
                "x": center_x,
                "y": center_y
            }

        return key_centers

    def create_frame(self, frame_id, t, key_id, audio_tap):
        """
        创建一帧模拟数据。

        参数：
            frame_id: 当前是第几帧
            t: 当前时间
            key_id: 手指所在的按键 id
            audio_tap: 是否检测到敲击声音
        """
        position = self.key_centers[key_id]

        frame = {
            "frame_id": frame_id,
            "t": t,
            "fingers": [
                {
                    "finger_id": 1,
                    "x": position["x"],
                    "y": position["y"]
                }
            ],
            "tap": {
                "audio": audio_tap
            }
        }

        return frame

    def generate_frames(self, text, frame_time=0.03):
        """
        根据输入文本生成一组 frames。

        每个字符生成 3 帧：
        1. 手指在键上，但还没敲击
        2. 手指在键上，检测到敲击
        3. 手指在键上，敲击结束

        这样可以模拟一次完整按键过程。
        """
        frames = []
        frame_id = 1
        t = 0.0

        for key_id in text:
            if key_id not in self.key_centers:
                print(f"跳过未知按键：{key_id}")
                continue

            frames.append(self.create_frame(frame_id, t, key_id, False))
            frame_id += 1
            t += frame_time

            frames.append(self.create_frame(frame_id, t, key_id, True))
            frame_id += 1
            t += frame_time

            frames.append(self.create_frame(frame_id, t, key_id, False))
            frame_id += 1
            t += frame_time

        return frames


def main():
    source = ManualSource("data/layouts/keyboard_number_v1.json")

    frames = source.generate_frames("123")

    for frame in frames:
        frame_id = frame["frame_id"]
        t = frame["t"]
        finger = frame["fingers"][0]
        audio_tap = frame["tap"]["audio"]

        x = finger["x"]
        y = finger["y"]

        print(f"frame {frame_id}, t={t:.2f}, finger=({x}, {y}), audio={audio_tap}")


if __name__ == "__main__":
    main()