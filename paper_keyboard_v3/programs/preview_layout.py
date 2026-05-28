import json
import os

import cv2
import numpy as np


def load_layout(layout_path):
    """读取 layout JSON 文件。"""
    with open(layout_path, "r", encoding="utf-8") as f:
        return json.load(f)


def mm_to_px(value, scale):
    """把毫米转换成像素。"""
    return int(round(value * scale))


def create_marker_image(marker_id, size_px):
    """生成 ArUco marker 图片。"""
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    if hasattr(cv2.aruco, "generateImageMarker"):
        marker_image = cv2.aruco.generateImageMarker(
            dictionary,
            marker_id,
            size_px
        )
    else:
        marker_image = np.zeros((size_px, size_px), dtype=np.uint8)
        cv2.aruco.drawMarker(
            dictionary,
            marker_id,
            size_px,
            marker_image,
            1
        )

    return marker_image


def draw_marker(canvas, marker, scale):
    """
    把 ArUco marker 画到纸面键盘图上。

    注意：
    marker 的 id 只用于识别，不额外画文字。
    """
    marker_id = marker["id"]

    x = mm_to_px(marker["x"], scale)
    y = mm_to_px(marker["y"], scale)
    w = mm_to_px(marker["w"], scale)
    h = mm_to_px(marker["h"], scale)

    marker_image = create_marker_image(marker_id, w)

    if w != h:
        marker_image = cv2.resize(marker_image, (w, h))

    canvas[y:y + h, x:x + w] = marker_image


def draw_key(canvas, key, scale):
    """把一个按键画到纸面键盘图上，并让数字居中。"""
    x = mm_to_px(key["x"], scale)
    y = mm_to_px(key["y"], scale)
    w = mm_to_px(key["w"], scale)
    h = mm_to_px(key["h"], scale)

    cv2.rectangle(
        canvas,
        (x, y),
        (x + w, y + h),
        0,
        2,
        lineType=cv2.LINE_AA
    )

    key_id = key["id"]

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2

    text_size, baseline = cv2.getTextSize(
        key_id,
        font,
        font_scale,
        thickness
    )

    text_w = text_size[0]
    text_h = text_size[1]

    text_x = x + (w - text_w) // 2
    text_y = y + (h + text_h) // 2

    cv2.putText(
        canvas,
        key_id,
        (text_x, text_y),
        font,
        font_scale,
        0,
        thickness,
        lineType=cv2.LINE_AA
    )


def draw_layout(layout, scale):
    """根据 layout 生成完整纸面键盘图片。"""
    board = layout["board"]

    board_w_px = mm_to_px(board["w"], scale)
    board_h_px = mm_to_px(board["h"], scale)

    canvas = np.ones((board_h_px, board_w_px), dtype=np.uint8) * 255

    for marker in layout["markers"]:
        draw_marker(canvas, marker, scale)

    for key in layout["keys"]:
        draw_key(canvas, key, scale)

    cv2.rectangle(
        canvas,
        (0, 0),
        (board_w_px - 1, board_h_px - 1),
        0,
        2
    )

    return canvas


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"
    output_path = "data/generated/keyboard_number_v1.png"

    scale = 6

    layout = load_layout(layout_path)
    canvas = draw_layout(layout, scale)

    os.makedirs("data/generated", exist_ok=True)
    cv2.imwrite(output_path, canvas)

    print("已生成纸面键盘图片：", output_path)


if __name__ == "__main__":
    main()