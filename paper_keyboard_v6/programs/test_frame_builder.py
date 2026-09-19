import time

import cv2

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource
from components.paper_mapper import PaperMapper
from components.frame_builder import FrameBuilder


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    # 打开摄像头。
    camera = CameraSource(camera_id=0)

    # 创建手部识别对象。
    hand_source = MediaPipeHandSource(max_num_hands=1)

    # 创建纸面定位对象。
    paper_mapper = PaperMapper(layout_path)

    # 创建 FrameBuilder。
    # 它会把 hand_source 和 paper_mapper 的结果整理成 frame。
    frame_builder = FrameBuilder(
        paper_mapper,
        hand_source
    )

    frame_id = 0
    start_time = time.time()

    print("FrameBuilder 测试开始")
    print("请把纸面键盘放到摄像头画面里")
    print("按 q 退出")
    print("按 p 打印当前 frame")

    while True:
        # 读取一帧摄像头画面。
        image = camera.read_image()

        if image is None:
            print("没有读取到摄像头画面")
            continue

        # 计算当前时间。
        t = time.time() - start_time

        # 根据当前画面生成 frame。
        frame, visual_data = frame_builder.build_frame(
            image,
            frame_id,
            t
        )

        # 从 visual_data 里取出调试显示需要的数据。
        homography = visual_data["homography"]
        corners = visual_data["corners"]
        ids = visual_data["ids"]
        hand_data = visual_data["hand_data"]
        mediapipe_result = visual_data["mediapipe_result"]

        # 画手部骨架。
        image = hand_source.draw_hand(image, mediapipe_result)

        # 画识别到的 ArUco marker。
        image = paper_mapper.draw_detected_markers(image, corners, ids)

        if homography is not None:
            # 画纸面边框。
            image = paper_mapper.draw_board_border(image, homography)

            # 画 layout 里的按键框。
            image = paper_mapper.draw_keys(image, homography)

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
            cv2.putText(
                image,
                "paper not detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2
            )

        # 画指尖红点和 finger_id。
        image = hand_source.draw_fingertips(image, hand_data)

        cv2.imshow("Paper Keyboard - FrameBuilder Test", image)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("p"):
            print(frame)

        frame_id = frame_id + 1

    hand_source.close()
    camera.release()
    cv2.destroyAllWindows()

    print("FrameBuilder 测试结束")


if __name__ == "__main__":
    main()