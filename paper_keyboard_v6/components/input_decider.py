# InputDecider 的作用：
# 判断 candidate 是否是一次新的输入触发。
#
# candidate 的规则：
#
# -1
#     没有触发输入
#
# 0-9
#     某个 finger_id 触发了输入
#
# 为什么不能看到 candidate 就输入？
#
# 因为一次敲击可能会持续好几帧。
# 例如：
#
# -1, 1, 1, 1, -1, 2, 2, -1
#
# 这里 candidate=1 出现了三帧，但这只是一次敲击。
# 所以只能输入一次。
#
# 判断新输入的规则：
#
# 上一帧是 -1
# 当前帧不是 -1
#
# 这时才认为产生了一次新输入。
class InputDecider:
    def __init__(self):
        self.last_candidate=-1
        
    def decide_candidate(self,candidate):
        if candidate!=self.last_candidate and candidate!=-1:
            self.last_candidate=candidate
            return candidate
        else:
            self.last_candidate=candidate
            return None
        
def main():
    decider = InputDecider()
    test_deciders =[-1,0,1,2,2,-1]
    
    for candidate in test_deciders:
        answer=decider.decide_candidate(candidate)
        print(answer)
        
if __name__ == "__main__":
    main()