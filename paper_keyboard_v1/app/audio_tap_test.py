from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from audio.tap_detector import AudioPeakDetector


def main() -> None:
    detector = AudioPeakDetector(
        min_threshold=0.03,
        peak_multiplier=4.0,
        cooldown_seconds=0.18,
        recent_window_seconds=0.20,
    )

    detector.start()

    print("Audio tap test started.")
    print("Tap the table or paper keyboard.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            status = detector.get_status()

            print(
                f"recent={status.recent_peak} | "
                f"peak={status.last_peak_value:.4f} | "
                f"rms={status.last_rms:.4f} | "
                f"threshold={status.threshold:.4f} | "
                f"noise={status.noise_floor:.4f}"
            )

            time.sleep(0.10)

    except KeyboardInterrupt:
        print("Stopping audio tap test.")

    finally:
        detector.stop()


if __name__ == "__main__":
    main()