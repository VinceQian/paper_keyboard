import json
import os


def build_session(session_id, layout_id, frames, unit="mm"):
    """
    根据基本信息和 frames，生成一个完整的 session 字典。

    参数：
        session_id: 这次输入记录的 id
        layout_id: 使用的键盘布局 id
        frames: 输入过程中的所有 frame
        unit: 坐标单位，默认是 mm

    返回：
        一个可以保存成 JSON 的 session 字典
    """
    session = {
        "session_id": session_id,
        "layout_id": layout_id,
        "unit": unit,
        "frames": frames
    }

    return session


def save_session(session_path, session):
    """
    把 session 保存成 JSON 文件。

    如果目标文件夹不存在，会自动创建。
    """
    folder = os.path.dirname(session_path)

    if folder != "":
        os.makedirs(folder, exist_ok=True)

    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def main():
    test_frames = [
        {
            "frame_id": 1,
            "t": 0.00,
            "fingers": [
                {
                    "finger_id": 1,
                    "x": 25,
                    "y": 25
                }
            ],
            "tap": {
                "audio": False
            }
        },
        {
            "frame_id": 2,
            "t": 0.03,
            "fingers": [
                {
                    "finger_id": 1,
                    "x": 25,
                    "y": 25
                }
            ],
            "tap": {
                "audio": True
            }
        }
    ]

    session = build_session(
        session_id="test_writer_output",
        layout_id="keyboard_number_v1",
        frames=test_frames
    )

    save_session("data/generated/test_writer_output.json", session)

    print("session 已保存到：data/generated/test_writer_output.json")


if __name__ == "__main__":
    main()