import cv2
import numpy as np

from components.paper_mapper import PaperMapper
from components.key_finder import KeyFinder
from input_sources.mediapipe_finger_source import MediaPipeFingerSource


def draw_finger_point(image, finger):
    """在画面上画出食指指尖位置。"""
    image_x = finger["image_x"]
    image_y = finger["image_y"]

    cv2.circle(
        image,
        (image_x, image_y),
        10,
        (0, 255, 0),
        -1
    )


def draw_current_key(image, key, homography):
    """
    在摄像头画面中高亮当前按键。

    key 是 layout 中的按键信息，坐标是纸面坐标。
    这里需要用 homography 的逆矩阵，把纸面坐标转回图像坐标。
    """
    x = key["x"]
    y = key["y"]
    w = key["w"]
    h = key["h"]

    paper_points = np.array(
        [
            [
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h]
            ]
        ],
        dtype=np.float32
    )

    inverse_homography = np.linalg.inv(homography)
    image_points = cv2.perspectiveTransform(paper_points, inverse_homography)
    image_points = image_points.astype(int)

    cv2.polylines(
        image,
        image_points,
        isClosed=True,
        color=(0, 255, 255),
        thickness=3
    )


def find_key_by_id(keys, key_id):
    """根据 key_id 找到对应的 key 信息。"""
    for key in keys:
        if key["id"] == key_id:
            return key

    return None


def draw_status_text(image, paper_position, key_id):
    """在画面上显示当前纸面坐标和按键。"""
    if paper_position is None:
        text = "No finger / no paper"
    else:
        paper_x, paper_y = paper_position
        text = f"paper=({paper_x:.1f}, {paper_y:.1f}) key={key_id}"

    cv2.putText(
        image,
        text,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"

    mapper = PaperMapper(layout_path)
    key_finder = KeyFinder(layout_path)
    finger_source = MediaPipeFingerSource()

    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("摄像头打开失败")
        return

    print("单指纸面映射测试开始")
    print("请把打印好的纸面键盘放到摄像头下")
    print("把食指移动到数字键上")
    print("按 q 退出")

    while True:
        success, image = cap.read()

        if not success:
            print("读取摄像头失败")
            break

        homography, corners, ids = mapper.get_homography(image)
        debug_image = mapper.draw_debug(image, corners, ids, homography)

        finger = finger_source.get_index_finger_tip(image)

        paper_position = None
        current_key_id = None

        if homography is not None and finger is not None:
            image_x = finger["image_x"]
            image_y = finger["image_y"]

            paper_x, paper_y = mapper.image_to_paper(
                image_x,
                image_y,
                homography
            )

            paper_position = (paper_x, paper_y)
            current_key_id = key_finder.find_key(paper_x, paper_y)

            draw_finger_point(debug_image, finger)

            if current_key_id is not None:
                current_key = find_key_by_id(key_finder.keys, current_key_id)
                draw_current_key(debug_image, current_key, homography)

        draw_status_text(debug_image, paper_position, current_key_id)

        cv2.imshow("Single Finger Mapping Test", debug_image)

        key = cv2.waitKey(1)

        if key == ord("q"):
            break

    finger_source.close()
    cap.release()
    cv2.destroyAllWindows()

    print("单指纸面映射测试结束")


if __name__ == "__main__":
    main()