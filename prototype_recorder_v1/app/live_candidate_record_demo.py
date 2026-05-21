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
from vision.board_tracker import BoardTracker
from vision.camera import CameraSource
from vision.hand_tracker import HandTracker


# ============================================================
# User-adjustable settings
# 你平时要调参数，主要改这里，不需要命令行传参。
# ============================================================

# Layout and model files
LAYOUT_PATH = PROJECT_ROOT / "data" / "layouts" / "keyboard_full_v1.json"
HAND_MODEL_PATH = PROJECT_ROOT / "models" / "hand_landmarker.task"
OUTPUT_DIR = PROJECT_ROOT / "data" / "recorded"

# Camera settings
CAMERA_INDEX = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
FLIP_CAMERA = False

# Board tracking settings
# 至少看到多少个 marker 才更新纸面校准。
# 如果看不到足够 marker，会继续使用 last good homography。
MIN_MARKERS_TO_UPDATE = 2
RANSAC_REPROJ_THRESHOLD = 3.0

# Candidate detection settings
# 缩小实际按键判定区域，单位 mm。
# 0 表示使用完整按键矩形。
SHRINK_X_MM = 0.0
SHRINK_Y_MM = 0.0

# Audio tap detection settings
# AUDIO_WINDOW_SECONDS:
# 敲击声音出现后，在多长时间内认为 audio_recent=True。
# 线上演示如果慢慢按，可以先用 0.18~0.20。
AUDIO_WINDOW_SECONDS = 0.20
AUDIO_MIN_THRESHOLD = 0.03
AUDIO_PEAK_MULTIPLIER = 4.0
AUDIO_COOLDOWN_SECONDS = 0.18

# Tap state settings
# STABLE_FRAMES:
# 当前 key 连续稳定多少帧后，才允许音频确认。
# RELEASE_FRAMES:
# 手指离开按键区域多少帧后，才允许下一次 tap。
STABLE_FRAMES = 2
RELEASE_FRAMES = 2

# Recording settings
# RECORD_NAME = None 会自动生成 session_xxx.json
RECORD_NAME = None


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

    recorder = DemoRecorder(
        output_dir=OUTPUT_DIR,
        layout_id=layout.layout_id,
        source="live_candidate_record_demo_direct",
        notes=(
            "Direct tap detection demo. "
            "Uses current visual candidate + recent audio peak. "
            "No history buffer or motion-based tap selection."
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
    print("Controls:")
    print("- q: quit")
    print("- r: reset board calibration")
    print("- c: clear output text and tap state")
    print("- space: toggle event recording")
    print("- s: save recording")
    print()

    recording_enabled = False
    saved_once = False

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

                print("Tap:", tap_event, "| Output:", output_text)

                if recording_enabled:
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
                tap_machine.reset()
                print("Output text and tap state cleared.")

            if key == ord(" "):
                recording_enabled = not recording_enabled
                print("Recording enabled:", recording_enabled)

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

    cv2.putText(
        output,
        f"FPS: {fps:.1f}",
        (20, 460),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 0, 0),
        2,
        cv2.LINE_AA,
    )


if __name__ == "__main__":
    main()