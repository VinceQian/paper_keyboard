import json


class ManualSource:
    """
    用代码生成模拟输入 frame。

    这个类主要用于测试：
    不需要摄像头，也不需要麦克风，
    直接用一段字符串生成模拟输入数据。

    当前 frame 格式：

    {
        "frame_id": 1,
        "t": 0.03,
        "fingers": [
            {
                "finger_id": 1,
                "x": 132.4,
                "y": 78.6
            }
        ],
        "tap": {
            "candidate": 1
        }
    }

    candidate 规则：
        -1: 没有触发输入
         1: 右手食指触发输入
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

        返回：
            {
                "1": {"x": 57.0, "y": 82.0},
                "2": {"x": 103.0, "y": 82.0}
            }
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

    def create_frame(self, frame_id, t, key_id, candidate):
        """
        创建一帧模拟数据。

        参数：
            frame_id: 当前是第几帧
            t: 当前时间
            key_id: 手指所在的按键 id
            candidate: 当前输入候选手指
                       -1 表示没有触发
                        1 表示右手食指触发
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
                "candidate": candidate
            }
        }

        return frame

    def generate_frames(self, text, frame_time=0.03):
        """
        根据输入文本生成一组 frames。

        每个字符生成 3 帧：

        第 1 帧：
            手指在键上，但没有触发输入
            candidate = -1

        第 2 帧：
            手指在键上，并触发输入
            candidate = 1

        第 3 帧：
            手指仍在键上，但触发结束
            candidate = -1

        这样可以模拟一次完整按键过程。
        """
        frames = []
        frame_id = 1
        t = 0.0

        for key_id in text:
            if key_id not in self.key_centers:
                print(f"跳过未知按键：{key_id}")
                continue

            frames.append(
                self.create_frame(
                    frame_id=frame_id,
                    t=t,
                    key_id=key_id,
                    candidate=-1
                )
            )
            frame_id += 1
            t += frame_time

            frames.append(
                self.create_frame(
                    frame_id=frame_id,
                    t=t,
                    key_id=key_id,
                    candidate=1
                )
            )
            frame_id += 1
            t += frame_time

            frames.append(
                self.create_frame(
                    frame_id=frame_id,
                    t=t,
                    key_id=key_id,
                    candidate=-1
                )
            )
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
        candidate = frame["tap"]["candidate"]

        x = finger["x"]
        y = finger["y"]

        print(
            f"frame {frame_id}, "
            f"t={t:.2f}, "
            f"finger_id={finger['finger_id']}, "
            f"finger=({x}, {y}), "
            f"candidate={candidate}"
        )


if __name__ == "__main__":
    main()