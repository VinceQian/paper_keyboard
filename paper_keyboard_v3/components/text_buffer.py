class TextBuffer:
    """
    保存当前已经输入出来的文本。

    这个类不负责判断按键是否有效，
    也不负责识别手指位置。
    它只负责维护最终输入结果。
    """

    def __init__(self):
        self.text = ""

    def add_key(self, key):
        """
        添加一个按键到文本末尾。

        例如：
        当前 text = "12"
        add_key("3")
        结果 text = "123"
        """
        self.text += key

    def delete_last(self):
        """
        删除最后一个字符。

        例如：
        当前 text = "123"
        delete_last()
        结果 text = "12"
        """
        if len(self.text) > 0:
            self.text = self.text[:-1]

    def clear(self):
        """清空当前文本。"""
        self.text = ""

    def get_text(self):
        """返回当前文本。"""
        return self.text

def main():
    buffer = TextBuffer()

    buffer.add_key("1")
    print(buffer.get_text())

    buffer.add_key("2")
    print(buffer.get_text())

    buffer.add_key("3")
    print(buffer.get_text())

    buffer.delete_last()
    print(buffer.get_text())

    buffer.clear()
    print(buffer.get_text())

if __name__ == "__main__":
    main()