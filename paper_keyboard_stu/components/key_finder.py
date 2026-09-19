import json
class KeyFinder:
    """
    根据键盘的布局，判断手指的坐标在哪个按键上
    """
    def __init__(self,layout_path):
        with open(layout_path, "r") as f:
            self.layout = json.load(f)
            self.keys = self.layout["keys"]

    def find_key(self,x,y):
        """
        判断手指是否在键上
        参数：
        x:手指的x坐标
        y:手指的y坐标
        
        返回：
        输出对应的键
        如果不在范围内，则输出None
        """
        
        for key in self.keys:   
            in_x_range = key["x"]+key["w"] >= x >= key["x"]
            in_y_range = key["y"]+key["h"] >= y >= key["y"]
            if in_x_range and in_y_range:
                return(key["id"])
        return None

def main():
    finder = KeyFinder("keyboard_number_v1.json")
    test_fingers = [(57,70), (74, 65), (200, 80)]

    for x, y in test_fingers:
        key = finder.find_key(x, y)
        print(f"坐标 ({x}, {y}) 在按键 {key} 上")
        
if __name__ == "__main__":
    main()