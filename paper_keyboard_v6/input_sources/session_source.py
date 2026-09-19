# SessionSource 的作用：
# 1. 创建对象时读取 session json
# 2. 把读取到的数据保存到 self.session
# 3. 提供几个函数，让其他程序可以拿到 session 信息
#
# 这个文件写在：
# input_sources/session_source.py
#
# 需要 import：
import json
class SessionSource:
    def __init__(self,source_path):
        with open(source_path,"r") as f:
            self.source = json.load(f)  
    def get_frames(self):
        return self.source.get("frames")
    
    
    
def main():
    session = SessionSource("test_number_input_123.json")
    
    frame = session.get_frames()
    print(frame)
    
if __name__=="__main__":
    main()