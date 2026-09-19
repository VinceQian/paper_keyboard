def get_finger_position_by_id(frame, finger_id):
    """
    提取手指的x和y
    
    
    参数：
    frame:是一个存手指的字典
    finger_id:是一个手指的编号
    
    
    返回：
    手指的x和y(只有当手指编号存在时才能返回，不存在时返回None)
    """
    fingers=frame.get("fingers")
    position=fingers.get(str(finger_id))
    if position is None:
        return None

    return position.get("x"),position.get("y") 

def get_candidate(frame):
    """
    提取敲下的手指是哪根
    
    参数：
    frame:是一个存手指的字典
    返回：
    敲下的手指是哪根
    """
    x =frame.get("tap")
    return x.get("candidate")
