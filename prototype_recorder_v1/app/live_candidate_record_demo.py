from __future__ import annotations

import sys
import time
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from audio.tap_detector import AudioPeakDetector, TapStateMachine
from core.candidate import CandidateDetector
from core.layout import KeyboardLayout
from core.recorder import DemoRecorder
from output.keyboard_output import KeyboardOutput
from vision.board_tracker import BoardTracker
from vision.camera import CameraSource
from vision.hand_tracker import HandTracker


# ============================================================
# User-adjustable settings
# 你平时要调参数，主要改这里，不需要命令行传参。
# ============================================================

# ----------------------------
# File paths
# ----------------------------

LAYOUT_PATH = PROJECT_ROOT / "data" / "layouts" / "keyboard_full_v1.json"
HAND_MODEL_PATH = PROJECT_ROOT / "models" / "hand_landmarker.task"
OUTPUT_DIR = PROJECT_ROOT / "data" / "recorded"

# RECORD_NAME = None 时自动生成 session_xxx.json
RECORD_NAME = None


# ----------------------------
# Camera settings
# ----------------------------

CAMERA_INDEX = 2
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# 如果画面是镜像的，可以改成 True。
# 注意：如果开启镜像，ArUco 和坐标映射也会跟着镜像，需要实际测试。
FLIP_CAMERA = False


# ----------------------------
# Board tracking settings
# ----------------------------

# 至少看到多少个 marker 才更新纸面校准。
# 如果看不到足够 marker，会继续使用 last good homography。
MIN_MARKERS_TO_UPDATE = 2

# RANSAC 的重投影阈值。一般不用改。
RANSAC_REPROJ_THRESHOLD = 3.0


# ----------------------------
# Candidate detection settings
# ----------------------------

# 缩小实际按键判定区域，单位 mm。
# 0 表示使用完整按键矩形。
# 如果误触边缘很多，可以尝试 SHRINK_X_MM = 1.0, SHRINK_Y_MM = 2.0
SHRINK_X_MM = 0.0
SHRINK_Y_MM = 0.0


# ----------------------------
# Audio tap detection settings
# ----------------------------

# 敲击声音出现后，在多长时间内认为 audio_recent=True。
# 线上演示如果慢慢按，可以先用 0.18~0.20。
AUDIO_WINDOW_SECONDS = 0.20

# 音频峰值检测参数。
# 环境很吵时可以提高 AUDIO_MIN_THRESHOLD 或 AUDIO_PEAK_MULTIPLIER。
AUDIO_MIN_THRESHOLD = 0.03
AUDIO_PEAK_MULTIPLIER = 4.0

# 音频 cooldown，防止一次敲击声被检测成多次 peak。
AUDIO_COOLDOWN_SECONDS = 0.18


# ----------------------------
# Tap state settings
# ----------------------------

# 当前 key 连续稳定多少帧后，才允许音频确认。
STABLE_FRAMES = 2

# 手指离开按键区域多少帧后，才允许下一次 tap。
RELEASE_FRAMES = 2


# ----------------------------
# System keyboard output settings
# ----------------------------

# 默认是否启用真实系统键盘输入。
# 建议默认 False，避免测试时乱打字。
ENABLE_SYSTEM_KEYBOARD_OUTPUT = False

# 是否把字母输出成大写。
# False 更像正常键盘输入：label A 输出为 "a"
# True 会输出 "A"
OUTPUT_UPPERCASE_LETTERS = False

# 每次模拟按键后的短暂停顿，避免系统丢输入。
KEYBOARD_OUTPUT_INTERVAL_SECONDS = 0.02


def main() -> None:
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

    keyboard_output = KeyboardOutput(
        enabled=ENABLE_SYSTEM_KEYBOARD_OUTPUT,
        press_interval_seconds=KEYBOARD_OUTPUT_INTERVAL_SECONDS,
        uppercase_letters=OUTPUT_UPPERCASE_LETTERS,
    )

    recorder = DemoRecorder(
        output_dir=OUTPUT_DIR,
        layout_id=layout.layout_id,
        source="live_candidate_record_demo_direct",
        notes=(
            "Direct tap detection demo. "
            "Uses current visual candidate + recent audio peak. "
            "System keyboard output can be toggled by pressing o."
        ),
    )

    camera.open()
    audio_detector.start()

    print("Live candidate record demo started.")
    print("Mode: direct current-key detection")
    print("Layout:", layout.layout_id)
    print("Camera:", CAMERA_INDEX)
    print("Model:", HAND_MODEL_PATH)
    print()
    print("Tap decision:")
    print("- current visual candidate key")
    print(f"- audio recent window: {AUDIO_WINDOW_SECONDS}s")
    print(f"- stable frames: {STABLE_FRAMES}")
    print(f"- release frames: {RELEASE_FRAMES}")
    print(f"- hitbox shrink: x={SHRINK_X_MM}mm, y={SHRINK_Y_MM}mm")
    print()
    print("System keyboard output:")
    print(f"- enabled: {keyboard_output.enabled}")
    print(f"- available: {keyboard_output.available}")
    if keyboard_output.error_message:
        print(f"- error: {keyboard_output.error_message}")
    print()
    print("Controls:")
    print("- q: quit")
    print("- r: reset board calibration")
    print("- c: clear output text and tap state")
    print("- space: toggle event recording")
    print("- o: toggle system keyboard output")
    print("- s: save recording")
    print()

    recording_enabled = False
    saved_once = False

    output_text = ""
    last_tap_event = None
    last_tap_time = 0.0
    last_system_output_sent = False

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
                        "id": finger["id"],
                        "x": board_x,
                        "y": board_y,
                        "image_x": image_x,
                        "image_y": image_y,
                        "confidence": finger.get("confidence", 1.0),
                    }

                    paper_fingers.append(paper_finger)
                    fingertip_board = (board_x, board_y)

                candidates = candidate_detector.detect_candidates(paper_fingers)

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

                last_system_output_sent = keyboard_output.type_label(tap_event)

                print(
                    "Tap:",
                    tap_event,
                    "| Output:",
                    output_text,
                    "| System output:",
                    last_system_output_sent,
                )

                if recording_enabled:
                    keyboard_output_status = keyboard_output.get_status()

                    recorder.add_frame(
                        frame_id=camera_frame.frame_id,
                        timestamp=camera_frame.timestamp,
                        fingers=paper_fingers,
                        candidates=candidates,
                        audio_peak=True,
                        debug={
                            "event_type": "confirmed_tap",
                            "tap_event": tap_event,
                            "output_text": output_text,
                            "mode": "direct_current_key",
                            "tap_state": tap_machine.state,
                            "audio_recent": audio_recent,
                            "audio_status": audio_detector.get_status().__dict__,
                            "board_calibrated": board_result.calibrated,
                            "board_updated": board_result.updated,
                            "visible_marker_count": board_result.visible_marker_count,
                            "used_marker_ids": board_result.used_marker_ids,
                            "current_key_label": current_key_label,
                            "audio_window": AUDIO_WINDOW_SECONDS,
                            "stable_frames": STABLE_FRAMES,
                            "release_frames": RELEASE_FRAMES,
                            "shrink_x": SHRINK_X_MM,
                            "shrink_y": SHRINK_Y_MM,
                            "keyboard_output_enabled": keyboard_output_status.enabled,
                            "keyboard_output_available": keyboard_output_status.available,
                            "keyboard_output_sent": last_system_output_sent,
                            "keyboard_output_count": keyboard_output_status.output_count,
                            "keyboard_output_error": keyboard_output_status.error_message,
                        },
                    )

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
            keyboard_output_status = keyboard_output.get_status()

            draw_status(
                output=output,
                board_result=board_result,
                board_tracker=board_tracker,
                current_key_label=current_key_label,
                fingertip_board=fingertip_board,
                fps=fps,
                recording_enabled=recording_enabled,
                recorded_events=len(recorder.frames),
                audio_status=audio_status,
                audio_recent=audio_recent,
                tap_state=tap_machine.state,
                output_text=output_text,
                last_tap_event=last_tap_event,
                last_tap_time=last_tap_time,
                keyboard_output_status=keyboard_output_status,
                last_system_output_sent=last_system_output_sent,
            )

            cv2.imshow("Live Candidate Record Demo - Direct", output)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("r"):
                board_tracker.reset()
                print("Board calibration reset.")

            if key == ord("c"):
                output_text = ""
                last_tap_event = None
                last_tap_time = 0.0
                last_system_output_sent = False
                tap_machine.reset()
                print("Output text and tap state cleared.")

            if key == ord(" "):
                recording_enabled = not recording_enabled
                print("Recording enabled:", recording_enabled)

            if key == ord("o"):
                enabled = keyboard_output.toggle_enabled()
                print("System keyboard output enabled:", enabled)

            if key == ord("s"):
                output_path = recorder.save(RECORD_NAME)
                saved_once = True
                print("Saved recording:", output_path)

    finally:
        if recorder.frames and not saved_once:
            output_path = recorder.save(RECORD_NAME)
            print("Auto-saved recording:", output_path)

        audio_detector.stop()
        hand_tracker.close()
        camera.release()
        cv2.destroyAllWindows()
        print("Demo closed.")


def draw_status(
    output,
    board_result,
    board_tracker,
    current_key_label,
    fingertip_board,
    fps,
    recording_enabled,
    recorded_events,
    audio_status,
    audio_recent,
    tap_state,
    output_text,
    last_tap_event,
    last_tap_time,
    keyboard_output_status,
    last_system_output_sent,
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
            f"Audio peak: {audio_status.last_peak_value:.3f} "
            f"/ th {audio_status.threshold:.3f}"
        ),
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        audio_color,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        output,
        f"Tap state: {tap_state}",
        (20, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        output,
        (
            f"Direct mode | audio window={AUDIO_WINDOW_SECONDS:.2f}s | "
            f"stable={STABLE_FRAMES} | release={RELEASE_FRAMES}"
        ),
        (20, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        output,
        f"Output: {output_text}",
        (20, 320),
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
            (20, 370),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 255),
            3,
            cv2.LINE_AA,
        )

    record_color = (0, 0, 255) if recording_enabled else (180, 180, 180)
    record_text = (
        f"Recording confirmed taps: {recording_enabled} | "
        f"events={recorded_events} | space toggle | s save"
    )

    cv2.putText(
        output,
        record_text,
        (20, 420),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        record_color,
        2,
        cv2.LINE_AA,
    )

    keyboard_color = (
        (0, 255, 0)
        if keyboard_output_status.enabled and keyboard_output_status.available
        else (180, 180, 180)
    )

    keyboard_text = (
        f"System keyboard: {keyboard_output_status.enabled} | "
        f"available={keyboard_output_status.available} | "
        f"sent={keyboard_output_status.output_count} | "
        f"last_sent={last_system_output_sent}"
    )

    cv2.putText(
        output,
        keyboard_text,
        (20, 460),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        keyboard_color,
        2,
        cv2.LINE_AA,
    )

    if keyboard_output_status.error_message:
        cv2.putText(
            output,
            "Keyboard output error. Check terminal / macOS Accessibility permission.",
            (20, 500),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

        fps_y = 540
    else:
        fps_y = 500

    cv2.putText(
        output,
        f"FPS: {fps:.1f}",
        (20, fps_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 0, 0),
        2,
        cv2.LINE_AA,
    )


if __name__ == "__main__":
    main()