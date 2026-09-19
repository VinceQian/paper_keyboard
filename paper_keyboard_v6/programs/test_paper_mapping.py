import cv2

from input_sources.camera_source import CameraSource
from components.paper_mapper import PaperMapper


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    # 打开摄像头。
    camera = CameraSource(camera_id=0)

    # 创建 PaperMapper。
    # 它会读取 layout JSON，并根据里面的 marker 信息建立映射。
    mapper = PaperMapper(layout_path)

    print("纸面定位测试开始")
    print("请把生成的纸面键盘图片放到摄像头画面里")
    print("按 q 退出")

    while True:
        # 读取一帧摄像头画面。
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        # 识别 marker，并尝试计算 homography。
        # homography 不为 None，说明程序成功建立了：
        # 图像坐标 -> 纸面坐标 的转换关系。
        homography, corners, ids = mapper.get_homography(image)

        # 把识别到的 marker 框出来，方便观察。
        image = mapper.draw_detected_markers(image, corners, ids)

        if homography is not None:
            # 如果成功建立映射，就把纸张边框和按键区域画回摄像头画面。
            image = mapper.draw_board_border(image, homography)
            image = mapper.draw_keys(image, homography)

            cv2.putText(
                image,
                "paper detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2
            )
        else:
            # 如果没有检测到足够的 marker，就提示未识别纸面。
            cv2.putText(
                image,
                "paper not detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2
            )

        cv2.imshow("Paper Keyboard - Paper Mapping Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("纸面定位测试结束")


if __name__ == "__main__":
    main()