import time

import cv2

from components.frame_builder import FrameBuilder
from components.frame_tools import get_key_id_for_finger
from components.key_finder import KeyFinder
from components.paper_mapper import PaperMapper
from components.visual_overlay import VisualOverlay

from input_sources.camera_source import CameraSource
from input_sources.mediapipe_hand_source import MediaPipeHandSource


class NoTapSource:
    """
    空的触发源。

    这个测试程序只测试视觉映射，
    不测试音频敲击，也不产生输入。
    所以 candidate 永远是 -1。
    """

    def get_candidate(self):
        return -1


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    camera_id = 1

    camera_source = CameraSource(camera_id=camera_id)

    paper_mapper = PaperMapper(layout_path)
    hand_source = MediaPipeHandSource(swap_hands=True)
    tap_source = NoTapSource()

    frame_builder = FrameBuilder(
        paper_mapper=paper_mapper,
        hand_source=hand_source,
        tap_source=tap_source
    )

    key_finder = KeyFinder(layout_path)
    overlay = VisualOverlay(layout_path)

    start_time = time.time()
    frame_id = 1

    print("单指纸面映射测试开始")
    print("这个程序只测试视觉映射，不测试音频输入。")
    print("把右手食指移动到纸面数字键上，观察按键是否高亮。")
    print("q：退出")
    print()

    while True:
        success, image = camera_source.read_image()

        if not success:
            print("读取摄像头失败")
            break

        t = time.time() - start_time

        frame, visual_data = frame_builder.build_frame(
            image,
            frame_id,
            t
        )

        # 这里故意不使用 tap.candidate。
        # 因为这个测试只看右手食指当前映射到哪个 key。
        current_key_id = get_key_id_for_finger(
            frame,
            finger_id=1,
            key_finder=key_finder
        )

        debug_image = overlay.draw_all(
            image,
            frame,
            visual_data,
            current_key_id,
            text=""
        )

        cv2.imshow("Single Finger Mapping Test", debug_image)

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

        frame_id += 1

    hand_source.close()
    camera_source.release()
    cv2.destroyAllWindows()

    print("单指纸面映射测试结束")


if __name__ == "__main__":
    main()