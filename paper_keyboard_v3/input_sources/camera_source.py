import cv2


class CameraSource:
    """
    摄像头输入源。

    当前版本只负责：
    1. 打开摄像头
    2. 读取摄像头画面
    3. 关闭摄像头

    它暂时不负责识别手指位置。
    """

    def __init__(self, camera_id=1):
        self.camera_id = camera_id
        self.cap = cv2.VideoCapture(camera_id)

        if not self.cap.isOpened():
            print("摄像头打开失败，请检查 camera_id 或摄像头权限。")

    def read_image(self):
        """
        读取一帧摄像头画面。

        返回：
            success: 是否成功读取
            image: 摄像头画面
        """
        success, image = self.cap.read()
        return success, image

    def release(self):
        """释放摄像头。"""
        self.cap.release()


def main():
    source = CameraSource(camera_id=1)

    print("摄像头测试开始")
    print("按 q 退出")

    while True:
        success, image = source.read_image()

        if not success:
            print("读取摄像头画面失败")
            break

        cv2.imshow("Camera Test", image)

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

    source.release()
    cv2.destroyAllWindows()

    print("摄像头测试结束")


if __name__ == "__main__":
    main()