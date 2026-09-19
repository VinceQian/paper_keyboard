# TextBuffer 的作用：
# 保存最终输入出来的文本。
#
# 例如依次输入：
#
# 1
# 2
# 3
#
# 最终文本就是：
#
# "123"
# 

class TextBuffer:
    def __init__(self):
        self.text=""
    def add_char(self,key):
        if key=="del":
            self.text=self.text[0:-1]
        else:
            self.text+=str(key)
    def get_text(self):
        return self.text
    def remove_text(self):
        self.text=""
        
def main():
    text =TextBuffer()
    test_keys=[1,2,3,"del"]
    
    for key in test_keys:
        text.add_char(key)
        print(text.get_text())
    text.remove_text()
    print(text.get_text())
        
if __name__ == "__main__":
    main()  