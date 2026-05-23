import json
import sys
from pathlib import Path

# 让这个 app 可以找到 core/input_engine.py。
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from core.input_engine import InputEngine


# =========================
# 可以让学生修改的常量区
# =========================
LAYOUT_PATH = BASE_DIR / "data" / "layouts" / "layout.json"
SESSION_PATH = BASE_DIR / "data" / "sessions" / "example_continuous_session.json"


# =========================
# 工具函数
# =========================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    layout = load_json(LAYOUT_PATH)
    session = load_json(SESSION_PATH)

    engine = InputEngine(layout)

    print("Replay started")
    print("Layout:", layout["layout_id"])
    print("Session:", session["schema_version"])
    print("------------------------")

    for frame in session["frames"]:
        result = engine.update(frame)

        if result["pressed"]:
            print(
                "frame", result["frame_id"],
                "time", result["t"],
                "pressed", result["key"],
                "output =", result["output_text"]
            )

    print("------------------------")
    print("Final output:", engine.output_text)


if __name__ == "__main__":
    main()
