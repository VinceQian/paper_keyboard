from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from audio.tap_detector import AudioPeakDetector, TapStateMachine
from core.candidate import CandidateDetector
from core.layout import KeyboardLayout
from vision.board_tracker import BoardTracker
from vision.camera import CameraSource
from vision.hand_tracker import HandTracker


# ============================================================
# User-adjustable settings
# 这个 app 专门用于录制“学生版最小 session JSON”。
# ============================================================

# ----------------------------
# File paths
# ----------------------------

LAYOUT_PATH = PROJECT_ROOT / "data" / "layouts" / "keyboard_full_v1.json"
HAND_MODEL_PATH = PROJECT_ROOT / "models" / "hand_landmarker.task"
SESSION_OUTPUT_DIR = PROJECT_ROOT / "data" / "sessions"


# ----------------------------
# Recording mode
# ----------------------------

# "tap_only":
#   只保存确认按下的 frame。
#   适合第一节课：学生只看到“每次按下时手指在哪”。
#
# "continuous":
#   保存 recording 开启后的每一帧。
#   适合后续课程：学生可以处理连续数据、audio 状态、重复触发等问题。
RECORD_MODE = "tap_only"


# ----------------------------
# Camera settings
# ----------------------------

CAMERA_INDEX = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
FLIP_CAMERA = False


# ----------------------------
# Board tracking settings
# ----------------------------

MIN_MARKERS_TO_UPDATE = 2
RANSAC_REPROJ_THRESHOLD = 3.0


# ----------------------------
# Candidate detection settings
# ----------------------------

# 这里只用于 demo 画面显示和 tap_machine 判断。
# 保存到 JSON 里的数据不会保存 candidates。
SHRINK_X_MM = 0.0
SHRINK_Y_MM = 0.0


# ----------------------------
# Audio tap detection settings
# ----------------------------

AUDIO_WINDOW_SECONDS = 0.20
AUDIO_MIN_THRESHOLD = 0.03
AUDIO_PEAK_MULTIPLIER = 4.0
AUDIO_COOLDOWN_SECONDS = 0.18


# ----------------------------
# Tap state settings
# ----------------------------

STABLE_FRAMES = 2
RELEASE_FRAMES = 2


# ----------------------------
# JSON output settings
# ----------------------------

SCHEMA_VERSION = "paper_keyboard_session_v1"
TIME_UNIT = "seconds"

# 坐标和时间保留几位小数。
TIME_DECIMALS = 3
COORD_DECIMALS = 2


def main() -> None:
    SESSION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    layout = KeyboardLayout.from_json(LAYOUT_PATH)

    camera = CameraSource(
        camera_index=CAMERA_INDEX,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        fps=CAMERA_FPS,
        flip_horizontal=FLIP_CAMERA,
    )

    board_tracker = BoardTracker(
        layout=layout,
        min_markers_to_update=MIN_MARKERS_TO_UPDATE,
        ransac_reproj_threshold=RANSAC_REPROJ_THRESHOLD,
    )

    hand_tracker = HandTracker(
        model_path=HAND_MODEL_PATH,
        num_hands=1,
    )

    candidate_detector = CandidateDetector(
        layout=layout,
        margin=0.0,
        include_none=False,
        shrink_x=SHRINK_X_MM,
        shrink_y=SHRINK_Y_MM,
    )

    audio_detector = AudioPeakDetector(
        min_threshold=AUDIO_MIN_THRESHOLD,
        peak_multiplier=AUDIO_PEAK_MULTIPLIER,
        cooldown_seconds=AUDIO_COOLDOWN_SECONDS,
        recent_window_seconds=AUDIO_WINDOW_SECONDS,
    )

    tap_machine = TapStateMachine(
        stable_frames=STABLE_FRAMES,
        release_frames=RELEASE_FRAMES,
    )

    session_data = create_empty_session(layout_id=layout.layout_id)

    camera.open()
    audio_detector.start()

    print("Minimal session record demo started.")
    print("Output format: minimal frame-based session JSON")
    print("Layout:", layout.layout_id)
    print("Camera:", CAMERA_INDEX)
    print("Model:", HAND_MODEL_PATH)
    print()
    print("Recording mode:", RECORD_MODE)
    print()
    print("Controls:")
    print("- q: quit")
    print("- r: reset board calibration")
    print("- c: clear current session")
    print("- m: switch recording mode: tap_only / continuous")
    print("- space: toggle recording")
    print("- s: save minimal session JSON")
    print()

    recording_enabled = False
    saved_once = False
    record_mode = RECORD_MODE

    output_text = ""
    last_tap_event = None
    last_tap_time = 0.0

    start_perf_time = time.perf_counter()
    prev_perf_time = time.perf_counter()

    try:
        while True:
            camera_frame = camera.read()

            if camera_frame is None:
                print("Cannot read camera frame.")
                break

            frame = camera_frame.image
            output = frame.copy()

            board_result = board_tracker.update(frame)
            board_tracker.draw_markers(output, board_result)

            timestamp_ms = int((camera_frame.perf_timestamp - start_perf_time) * 1000)

            hand_result = hand_tracker.detect(frame, timestamp_ms)
            hand_tracker.draw(output, hand_result)

            paper_fingers = []
            candidates = []
            current_key_label = None
            fingertip_board = None

            if (
                board_result.calibrated
                and board_result.H_image_to_board is not None
                and hand_result.fingers
            ):
                for finger in hand_result.fingers:
                    image_x = finger["image_x"]
                    image_y = finger["image_y"]

                    board_x, board_y = board_tracker.transform_point(
                        board_result.H_image_to_board,
                        image_x,
                        image_y,
                    )

                    paper_finger = {
                        "id": normalize_finger_id(finger["id"]),
                        "x": board_x,
                        "y": board_y,
                    }

                    paper_fingers.append(paper_finger)
                    fingertip_board = (board_x, board_y)

                candidates = candidate_detector.detect_candidates(
                    [
                        {
                            "id": finger["id"],
                            "x": finger["x"],
                            "y": finger["y"],
                        }
                        for finger in paper_fingers
                    ]
                )

                if candidates:
                    current_key_label = candidates[0]["label"]

            audio_recent = audio_detector.has_recent_peak(
                window_seconds=AUDIO_WINDOW_SECONDS
            )

            tap_event = tap_machine.update(
                key_label=current_key_label,
                audio_recent=audio_recent,
            )

            if tap_event is not None:
                output_text += tap_event
                last_tap_event = tap_event
                last_tap_time = time.perf_counter()

                print("Tap:", tap_event, "| Output:", output_text)

            should_record_frame = False

            if recording_enabled:
                if record_mode == "continuous":
                    should_record_frame = True

                elif record_mode == "tap_only" and tap_event is not None:
                    should_record_frame = True

            if should_record_frame:
                minimal_frame = build_minimal_frame(
                    frame_id=camera_frame.frame_id,
                    timestamp=camera_frame.timestamp,
                    fingers=paper_fingers,
                    audio=bool(audio_recent if record_mode == "continuous" else True),
                )

                session_data["frames"].append(minimal_frame)

            if board_result.calibrated:
                board_tracker.draw_board_overlay(
                    output,
                    board_result,
                    current_key_label=current_key_label,
                )

            now_perf_time = time.perf_counter()
            fps = 1.0 / max(now_perf_time - prev_perf_time, 1e-6)
            prev_perf_time = now_perf_time

            audio_status = audio_detector.get_status()

            draw_status(
                output=output,
                board_result=board_result,
                board_tracker=board_tracker,
                current_key_label=current_key_label,
                fingertip_board=fingertip_board,
                fps=fps,
                recording_enabled=recording_enabled,
                record_mode=record_mode,
                saved_frame_count=len(session_data["frames"]),
                audio_status=audio_status,
                audio_recent=audio_recent,
                tap_state=tap_machine.state,
                output_text=output_text,
                last_tap_event=last_tap_event,
                last_tap_time=last_tap_time,
            )

            cv2.imshow("Minimal Session Record Demo", output)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("r"):
                board_tracker.reset()
                print("Board calibration reset.")

            if key == ord("c"):
                session_data = create_empty_session(layout_id=layout.layout_id)
                output_text = ""
                last_tap_event = None
                last_tap_time = 0.0
                tap_machine.reset()
                saved_once = False
                print("Current session cleared.")

            if key == ord("m"):
                record_mode = switch_record_mode(record_mode)
                print("Recording mode:", record_mode)

            if key == ord(" "):
                recording_enabled = not recording_enabled
                print("Recording enabled:", recording_enabled)

            if key == ord("s"):
                output_path = save_session_json(
                    session_data=session_data,
                    output_dir=SESSION_OUTPUT_DIR,
                    record_mode=record_mode,
                )
                saved_once = True
                print("Saved minimal session:", output_path)

    finally:
        if session_data["frames"] and not saved_once:
            output_path = save_session_json(
                session_data=session_data,
                output_dir=SESSION_OUTPUT_DIR,
                record_mode=record_mode,
            )
            print("Auto-saved minimal session:", output_path)

        audio_detector.stop()
        hand_tracker.close()
        camera.release()
        cv2.destroyAllWindows()
        print("Demo closed.")


def create_empty_session(layout_id: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "layout_id": layout_id,
        "time_unit": TIME_UNIT,
        "frames": [],
    }


def normalize_finger_id(raw_id: str) -> str:
    """
    MediaPipe 可能返回 right_index / left_index。
    对学生版数据，先统一成 index，降低理解成本。
    """
    raw_id = str(raw_id)

    if raw_id.endswith("_index"):
        return "index"

    return raw_id


def build_minimal_frame(
    frame_id: int,
    timestamp: float,
    fingers: list[dict],
    audio: bool,
) -> dict:
    return {
        "frame_id": int(frame_id),
        "t": round(float(timestamp), TIME_DECIMALS),
        "fingers": [
            {
                "id": str(finger["id"]),
                "x": round(float(finger["x"]), COORD_DECIMALS),
                "y": round(float(finger["y"]), COORD_DECIMALS),
            }
            for finger in fingers
        ],
        "tap": {
            "audio": bool(audio),
        },
    }


def switch_record_mode(current_mode: str) -> str:
    if current_mode == "tap_only":
        return "continuous"

    return "tap_only"


def save_session_json(
    session_data: dict,
    output_dir: Path,
    record_mode: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp_text = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"session_{record_mode}_{timestamp_text}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(session_data, file, ensure_ascii=False, indent=2)

    return output_path


def draw_status(
    output,
    board_result,
    board_tracker,
    current_key_label,
    fingertip_board,
    fps,
    recording_enabled,
    record_mode,
    saved_frame_count,
    audio_status,
    audio_recent,
    tap_state,
    output_text,
    last_tap_event,
    last_tap_time,
) -> None:
    if not board_result.calibrated:
        calib_text = (
            f"Calibration: waiting | "
            f"visible={board_result.visible_marker_count} | "
            f"need={board_tracker.min_markers_to_update}"
        )
        calib_color = (0, 0, 255)
    elif board_result.updated:
        calib_text = (
            f"Calibration: updated | "
            f"visible={board_result.visible_marker_count} | "
            f"used={board_result.used_marker_ids}"
        )
        calib_color = (0, 255, 0)
    else:
        calib_text = (
            f"Calibration: last good H | "
            f"visible={board_result.visible_marker_count} | "
            f"last={board_tracker.last_marker_count}"
        )
        calib_color = (0, 255, 255)

    cv2.putText(
        output,
        calib_text,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        calib_color,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        output,
        f"Current key: {current_key_label}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 0) if current_key_label else (0, 0, 255),
        2,
        cv2.LINE_AA,
    )

    if fingertip_board is not None:
        bx, by = fingertip_board
        board_text = f"Board coord: ({bx:.1f}, {by:.1f}) mm"
    else:
        board_text = "Board coord: None"

    cv2.putText(
        output,
        board_text,
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    audio_color = (0, 255, 255) if audio_recent else (180, 180, 180)

    cv2.putText(
        output,
        f"Audio recent: {audio_recent} | peaks={audio_status.peak_counter}",
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        audio_color,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        output,
        (
            f"Tap state: {tap_state} | "
            f"mode={record_mode}"
        ),
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    record_color = (0, 0, 255) if recording_enabled else (180, 180, 180)

    cv2.putText(
        output,
        (
            f"Recording: {recording_enabled} | "
            f"saved frames={saved_frame_count} | "
            f"space toggle | m mode | s save"
        ),
        (20, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        record_color,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        output,
        f"Output: {output_text}",
        (20, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 0),
        2,
        cv2.LINE_AA,
    )

    if last_tap_event is not None and time.perf_counter() - last_tap_time < 0.5:
        cv2.putText(
            output,
            f"TAP: {last_tap_event}",
            (20, 330),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 255),
            3,
            cv2.LINE_AA,
        )

    cv2.putText(
        output,
        f"FPS: {fps:.1f}",
        (20, 380),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 0, 0),
        2,
        cv2.LINE_AA,
    )


if __name__ == "__main__":
    main()