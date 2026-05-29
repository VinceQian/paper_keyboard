import json
import os


def build_session(session_id, layout_id, frames, unit="mm"):
    """
    根据基本信息和 frames，生成一个完整的 session 字典。

    参数：
        session_id:
            这次输入记录的 id。

        layout_id:
            使用的键盘布局 id。

        frames:
            输入过程中的所有 frame。

        unit:
            坐标单位，默认是 mm。

    frame 格式示例：

    {
        "frame_id": 1,
        "t": 0.03,
        "fingers": [
            {
                "finger_id": 1,
                "x": 57,
                "y": 82
            }
        ],
        "tap": {
            "candidate": 1
        }
    }

    tap.candidate 规则：
        -1:
            没有输入候选 / 没有触发。

        0-9:
            某个手指触发输入。
            当前基础版通常只会用到 1，也就是右手食指。
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
                    "x": 57,
                    "y": 82
                }
            ],
            "tap": {
                "candidate": -1
            }
        },
        {
            "frame_id": 2,
            "t": 0.03,
            "fingers": [
                {
                    "finger_id": 1,
                    "x": 57,
                    "y": 82
                }
            ],
            "tap": {
                "candidate": 1
            }
        },
        {
            "frame_id": 3,
            "t": 0.06,
            "fingers": [
                {
                    "finger_id": 1,
                    "x": 57,
                    "y": 82
                }
            ],
            "tap": {
                "candidate": -1
            }
        }
    ]

    session = build_session(
        session_id="test_writer_output",
        layout_id="keyboard_number_v1",
        frames=test_frames
    )

    output_path = "data/generated/test_writer_output.json"
    save_session(output_path, session)

    print("session 已保存到：", output_path)


if __name__ == "__main__":
    main()