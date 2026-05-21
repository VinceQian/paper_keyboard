from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--layout",
        type=str,
        default="data/layouts/keyboard_full_v1.json",
        help="Path to keyboard layout JSON.",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="models/hand_landmarker.task",
        help="Path to MediaPipe hand landmarker model.",
    )

    parser.add_argument(
        "--camera",
        type=int,
        default=1,
        help="Camera index.",
    )

    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Camera width.",
    )

    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Camera height.",
    )

    parser.add_argument(
        "--min-markers",
        type=int,
        default=2,
        help="Minimum visible markers required to update calibration.",
    )

    parser.add_argument(
        "--record-name",
        type=str,
        default=None,
        help="Optional output filename for recorded JSON.",
    )

    parser.add_argument(
        "--stable-frames",
        type=int,
        default=2,
        help="How many stable visual frames are required before accepting a tap.",
    )

    parser.add_argument(
        "--release-frames",
        type=int,
        default=2,
        help="How many empty frames are required before accepting the next tap.",
    )

    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def main() -> None:
    args = parse_args()

    layout_path = resolve_path(args.layout)
    model_path = resolve_path(args.model)
    output_dir = PROJECT_ROOT / "data" / "recorded"

    layout = KeyboardLayout.from_json(layout_path)

    camera = CameraSource(
        camera_index=args.camera,
        width=args.width,
        height=args.height,
        fps=30,
        flip_horizontal=False,
    )

    board_tracker = BoardTracker(
        layout=layout,
        min_markers_to_update=args.min_markers,
        ransac_reproj_threshold=3.0,
    )

    hand_tracker = HandTracker(
        model_path=model_path,
        num_hands=1,
    )

    candidate_detector = CandidateDetector(
        layout=layout,
        margin=0.0,
        include_none=False,
    )

    audio_detector = AudioPeakDetector(
        min_threshold=0.03,
        peak_multiplier=4.0,
        cooldown_seconds=0.18,
        recent_window_seconds=0.20,
    )

    tap_machine = TapStateMachine(
        stable_frames=args.stable_frames,
        release_frames=args.release_frames,
    )

    recorder = DemoRecorder(
        output_dir=output_dir,
        layout_id=layout.layout_id,
        source="live_candidate_record_demo",
        notes=(
            "Only confirmed tap events are recorded. "
            "Continuous non-tap frames are not saved."
        ),
    )

    camera.open()
    audio_detector.start()

    print("Live candidate record demo started.")
    print("Layout:", layout.layout_id)
    print("Camera:", args.camera)
    print("Model:", model_path)
    print()
    print("Controls:")
    print("- q: quit")
    print("- r: reset board calibration")
    print("- c: clear output text and tap state")
    print("- space: toggle event recording")
    print("- s: save recording")
    print()
    print("Recording rule:")
    print("- When recording is enabled, only confirmed tap events are saved.")
    print("- Hover frames are displayed but not recorded.")
    print()

    recording_enabled = False
    saved_once = False

    output_text = ""
    last_tap_event = None
    last_tap_time = 0.0

    start_time = time.time()
    prev_time = time.time()

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

            timestamp_ms = int((time.time() - start_time) * 1000)

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

            audio_recent = audio_detector.has_recent_peak(window_seconds=0.20)

            tap_event = tap_machine.update(
                key_label=current_key_label,
                audio_recent=audio_recent,
            )

            if tap_event is not None:
                output_text += tap_event
                last_tap_event = tap_event
                last_tap_time = time.time()

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
                            "tap_state": tap_machine.state,
                            "board_calibrated": board_result.calibrated,
                            "board_updated": board_result.updated,
                            "visible_marker_count": board_result.visible_marker_count,
                            "used_marker_ids": board_result.used_marker_ids,
                            "current_key_label": current_key_label,
                            "audio_status": audio_detector.get_status().__dict__,
                        },
                    )

            if board_result.calibrated:
                board_tracker.draw_board_overlay(
                    output,
                    board_result,
                    current_key_label=current_key_label,
                )

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

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
                tap_state=tap_machine.state,
                output_text=output_text,
                last_tap_event=last_tap_event,
                last_tap_time=last_tap_time,
            )

            cv2.imshow("Live Candidate Record Demo", output)

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
                output_path = recorder.save(args.record_name)
                saved_once = True
                print("Saved recording:", output_path)

    finally:
        if recorder.frames and not saved_once:
            output_path = recorder.save(args.record_name)
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

    cv2.putText(
        output,
        f"Audio recent: {audio_status.recent_peak}",
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255) if audio_status.recent_peak else (180, 180, 180),
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
        (0, 255, 255) if audio_status.recent_peak else (180, 180, 180),
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
        f"Output: {output_text}",
        (20, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 0),
        2,
        cv2.LINE_AA,
    )

    if last_tap_event is not None and time.time() - last_tap_time < 0.5:
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

    record_color = (0, 0, 255) if recording_enabled else (180, 180, 180)
    record_text = (
        f"Recording confirmed taps: {recording_enabled} | "
        f"events={recorded_events} | space toggle | s save"
    )

    cv2.putText(
        output,
        record_text,
        (20, 380),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        record_color,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        output,
        f"FPS: {fps:.1f}",
        (20, 420),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 0, 0),
        2,
        cv2.LINE_AA,
    )


if __name__ == "__main__":
    main()