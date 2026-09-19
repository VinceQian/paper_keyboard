import cv2

from input_sources.camera_source import CameraSource


def main():
    camera = CameraSource(camera_id=0) 

    print("摄像头测试开始")
    print("按 q 退出")

    while True:
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        cv2.imshow("Paper Keyboard - Camera Test", image)  # 把图像显示在一个窗口里

        key = cv2.waitKey(1) # 窗口刷新和等待键盘输入的时间

        if key & 0xFF == ord("q"): # 只取 key 的最后八位
            break

    camera.release()
    cv2.destroyAllWindows() # 关闭所有创建的窗口

    print("摄像头测试结束")


if __name__ == "__main__":
    main()