import json
import os
import time

import cv2
import numpy as np


def load_layout(layout_path):
    with open(layout_path, "r", encoding="utf-8") as f:
        return json.load(f)


def mm_to_px(value, scale):
    return int(round(value * scale))


def create_marker_image(marker_id, size_px):
    if not hasattr(cv2, "aruco"):
        raise RuntimeError(
            "当前 OpenCV 没有 aruco 模块。请安装：python3 -m pip install opencv-contrib-python"
        )

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

    text_size, _ = cv2.getTextSize(
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


def draw_board_border(canvas):
    height, width = canvas.shape

    cv2.rectangle(
        canvas,
        (0, 0),
        (width - 1, height - 1),
        0,
        2
    )


def draw_layout(layout, scale):
    board = layout["board"]

    board_w_px = mm_to_px(board["w"], scale)
    board_h_px = mm_to_px(board["h"], scale)

    canvas = np.ones((board_h_px, board_w_px), dtype=np.uint8) * 255

    for marker in layout["markers"]:
        draw_marker(canvas, marker, scale)

    for key in layout["keys"]:
        draw_key(canvas, key, scale)

    draw_board_border(canvas)

    return canvas


def save_image(output_path, image):
    output_folder = os.path.dirname(output_path)

    if output_folder != "":
        os.makedirs(output_folder, exist_ok=True)

    cv2.imwrite(output_path, image)


def render_layout(layout_path, scale):
    layout = load_layout(layout_path)
    image = draw_layout(layout, scale)
    return image


def main():
    layout_path = "data/layouts/keyboard_number_v1.json"
    output_path = "data/generated/keyboard_number_v1.png"

    preview_scale = 3
    save_scale = 6

    last_mtime = None
    preview_image = None

    cv2.namedWindow("Paper Keyboard - Layout Preview", cv2.WINDOW_NORMAL)

    print("layout 实时预览开始")
    print("q：退出")
    print("s：保存 PNG")
    print("r：手动重新加载 layout")
    print("+ / -：调整预览大小")
    print()

    while True:
        need_reload = False

        try:
            current_mtime = os.path.getmtime(layout_path)

            if last_mtime is None:
                need_reload = True
            elif current_mtime != last_mtime:
                need_reload = True

            if need_reload:
                preview_image = render_layout(layout_path, preview_scale)
                last_mtime = current_mtime
                print("已重新渲染 layout，preview_scale =", preview_scale)

        except Exception as e:
            print("渲染 layout 失败：", e)
            time.sleep(0.5)

        if preview_image is not None:
            cv2.imshow("Paper Keyboard - Layout Preview", preview_image)

        key = cv2.waitKey(100)

        if key & 0xFF == ord("q"):
            break

        if key & 0xFF == ord("r"):
            try:
                preview_image = render_layout(layout_path, preview_scale)
                last_mtime = os.path.getmtime(layout_path)
                print("已手动重新加载 layout")
            except Exception as e:
                print("手动重新加载失败：", e)

        if key & 0xFF == ord("s"):
            try:
                save_image_to_save = render_layout(layout_path, save_scale)
                save_image(output_path, save_image_to_save)
                print("已保存：", output_path)
            except Exception as e:
                print("保存失败：", e)

        if key & 0xFF == ord("+") or key & 0xFF == ord("="):
            preview_scale = preview_scale + 1
            preview_image = render_layout(layout_path, preview_scale)
            print("preview_scale =", preview_scale)

        if key & 0xFF == ord("-"):
            preview_scale = max(1, preview_scale - 1)
            preview_image = render_layout(layout_path, preview_scale)
            print("preview_scale =", preview_scale)

    cv2.destroyAllWindows()
    print("layout 实时预览结束")


if __name__ == "__main__":
    main()