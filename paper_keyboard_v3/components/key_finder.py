import json


class KeyFinder:
    """
    根据键盘布局，判断某个坐标点对应哪个按键。

    layout 文件中的每个 key 都是一个矩形：
    {
        "id": "1",
        "x": 20,
        "y": 20,
        "w": 20,
        "h": 22
    }

    判断逻辑：
    如果 x 在 [key_x, key_x + key_w] 范围内，
    并且 y 在 [key_y, key_y + key_h] 范围内，
    就说明这个点落在这个按键上。
    """

    def __init__(self, layout_path):
        self.layout_path = layout_path
        self.layout = self.load_layout(layout_path)
        self.keys = self.layout["keys"]

    def load_layout(self, layout_path):
        """读取键盘布局 JSON 文件。"""
        with open(layout_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def find_key(self, x, y):
        """
        根据坐标查找按键。

        参数：
            x: 手指的 x 坐标
            y: 手指的 y 坐标

        返回：
            如果坐标落在某个按键内，返回按键 label，比如 "1"
            如果没有落在任何按键内，返回 None
        """
        for key in self.keys:
            key_x = key["x"]
            key_y = key["y"]
            key_w = key["w"]
            key_h = key["h"]

            inside_x = key_x <= x <= key_x + key_w
            inside_y = key_y <= y <= key_y + key_h

            if inside_x and inside_y:
                return key["id"]

        return None

def main():
    finder = KeyFinder("paper_keyboard_v3/data/layouts/keyboard_number_v1.json")

    test_points = [
        (25, 25),
        (50, 25),
        (125, 55),
        (10, 10)
    ]

    for x, y in test_points:
        key = finder.find_key(x, y)
        print(f"坐标 ({x}, {y}) -> 按键：{key}")

if __name__ == "__main__":
    main()