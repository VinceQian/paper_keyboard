from pynput.keyboard import Controller


class DirectInput:
    """
    直接输入组件。

    它负责把确认后的 key_id 输入到当前系统焦点位置。

    它不负责：
    1. 判断手指位置
    2. 判断是否触发输入
    3. 保存 TextBuffer
    4. 生成 frame

    使用方式：
        direct_input.type_key("1")
    """

    def __init__(self, enabled=False):
        self.enabled = enabled
        self.keyboard = Controller()

    def toggle(self):
        """切换是否启用直接输入。"""
        self.enabled = not self.enabled
        return self.enabled

    def set_enabled(self, enabled):
        """设置是否启用直接输入。"""
        self.enabled = enabled

    def is_enabled(self):
        """返回当前是否启用直接输入。"""
        return self.enabled

    def type_key(self, key_id):
        """
        输入一个按键。

        如果 direct input 没有启用，就什么都不做。
        """
        if not self.enabled:
            return

        if key_id is None:
            return

        key_text = str(key_id)

        self.keyboard.press(key_text)
        self.keyboard.release(key_text)


def main():
    direct_input = DirectInput(enabled=True)

    print("DirectInput 测试开始")
    print("请先把光标点到一个文本输入框里")
    print("3 秒后会输入 123")
    print("按 Ctrl+C 可提前退出")

    import time

    time.sleep(3)

    direct_input.type_key("1")
    direct_input.type_key("2")
    direct_input.type_key("3")

    print("DirectInput 测试结束")


if __name__ == "__main__":
    main()