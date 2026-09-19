import cv2


class CameraSource:
    def __init__(self, camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)  # 打开一个摄像头。

        if not self.cap.isOpened(): # 如果摄像头打开失败，输出报错提示
            raise RuntimeError("无法打开摄像头：" + str(camera_id))

    def read_image(self):
        success, image = self.cap.read() # 读取当前摄像头画面的一帧，返回 success, image

        if not success: # 如果没有读到画面，返回 None
            return None

        return image # 如果读到画面，返回画面

    def release(self):
        self.cap.release() # 用完摄像头后释放资源，否则 Python 可能一直占用摄像头。