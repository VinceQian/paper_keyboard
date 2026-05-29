from input_sources.manual_source import ManualSource
from components.session_writer import build_session, save_session


def main():
    """
    生成一段模拟输入 session。

    这个程序不使用摄像头和麦克风，
    而是通过 ManualSource 直接生成测试 frames。
    """
    layout_path = "data/layouts/keyboard_number_v1.json"

    text = "12345"
    session_id = "manual_input_12345"
    layout_id = "keyboard_number_v1"
    output_path = "data/generated/manual_input_12345.json"

    source = ManualSource(layout_path)
    frames = source.generate_frames(text)

    session = build_session(
        session_id=session_id,
        layout_id=layout_id,
        frames=frames
    )

    save_session(output_path, session)

    print("已生成模拟输入 session")
    print("输入内容：", text)
    print("frame 数量：", len(frames))
    print("保存位置：", output_path)


if __name__ == "__main__":
    main()