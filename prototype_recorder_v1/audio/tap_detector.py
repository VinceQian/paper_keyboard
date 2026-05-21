from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import numpy as np
import sounddevice as sd


@dataclass
class AudioStatus:
    recent_peak: bool
    last_peak_value: float
    last_rms: float
    threshold: float
    noise_floor: float
    seconds_since_last_peak: float
    peak_counter: int


class AudioPeakDetector:
    """
    Detect short tap-like audio peaks.

    Important:
    - Uses time.perf_counter() for monotonic timing.
    - Provides consume_peak(), so the main loop can handle each peak once.
    - Estimates peak_time inside the audio block instead of using only callback time.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        block_size: int = 512,
        min_threshold: float = 0.03,
        peak_multiplier: float = 4.0,
        cooldown_seconds: float = 0.18,
        recent_window_seconds: float = 0.12,
        max_noise_history: int = 80,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.min_threshold = min_threshold
        self.peak_multiplier = peak_multiplier
        self.cooldown_seconds = cooldown_seconds
        self.recent_window_seconds = recent_window_seconds
        self.max_noise_history = max_noise_history

        self.noise_history: list[float] = []

        self.last_peak_time = 0.0
        self.last_peak_value = 0.0
        self.last_rms = 0.0
        self.current_threshold = min_threshold
        self.noise_floor = 0.0

        self.peak_counter = 0
        self.last_consumed_peak_counter = 0

        self.lock = threading.Lock()
        self.stream: sd.InputStream | None = None

    def start(self) -> None:
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            callback=self._callback,
        )
        self.stream.start()
        print("AudioPeakDetector started.")

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("AudioPeakDetector stopped.")

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            print("Audio status:", status)

        callback_time = time.perf_counter()

        audio = indata[:, 0]
        abs_audio = np.abs(audio)

        rms = float(np.sqrt(np.mean(audio ** 2)))
        peak = float(np.max(abs_audio))
        peak_index = int(np.argmax(abs_audio))

        # Approximate when the peak happened inside this audio block.
        # The callback happens after a block is available, so the peak may have
        # happened slightly before callback_time.
        seconds_from_peak_to_block_end = (len(audio) - 1 - peak_index) / self.sample_rate
        estimated_peak_time = callback_time - seconds_from_peak_to_block_end

        with self.lock:
            if self.noise_history:
                noise_floor = float(np.median(self.noise_history))
            else:
                noise_floor = rms

            threshold = max(
                self.min_threshold,
                noise_floor * self.peak_multiplier,
            )

            is_peak = (
                peak > threshold
                and estimated_peak_time - self.last_peak_time > self.cooldown_seconds
            )

            if is_peak:
                self.last_peak_time = estimated_peak_time
                self.last_peak_value = peak
                self.peak_counter += 1
            else:
                self.noise_history.append(rms)

                if len(self.noise_history) > self.max_noise_history:
                    self.noise_history.pop(0)

            self.last_rms = rms
            self.current_threshold = threshold
            self.noise_floor = noise_floor

    def consume_peak(self) -> tuple[bool, float, float]:
        """
        Return one new peak event if it has not been consumed yet.

        Returns:
            has_new_peak, peak_time, peak_value
        """
        with self.lock:
            if self.peak_counter == self.last_consumed_peak_counter:
                return False, 0.0, 0.0

            self.last_consumed_peak_counter = self.peak_counter
            return True, self.last_peak_time, self.last_peak_value

    def has_recent_peak(self, window_seconds: float | None = None) -> bool:
        if window_seconds is None:
            window_seconds = self.recent_window_seconds

        with self.lock:
            return time.perf_counter() - self.last_peak_time <= window_seconds

    def get_status(self) -> AudioStatus:
        with self.lock:
            seconds_since_last_peak = time.perf_counter() - self.last_peak_time

            return AudioStatus(
                recent_peak=seconds_since_last_peak <= self.recent_window_seconds,
                last_peak_value=self.last_peak_value,
                last_rms=self.last_rms,
                threshold=self.current_threshold,
                noise_floor=self.noise_floor,
                seconds_since_last_peak=seconds_since_last_peak,
                peak_counter=self.peak_counter,
            )


class TapStateMachine:
    """
    Kept for compatibility with earlier demos.

    The latest live_candidate_record_demo.py no longer relies on this as the
    main tap decision logic. It uses audio peak time + visual history instead.
    """

    def __init__(
        self,
        stable_frames: int = 2,
        release_frames: int = 2,
    ):
        self.stable_frames = stable_frames
        self.release_frames = release_frames

        self.state = "IDLE"
        self.current_key: str | None = None
        self.stable_count = 0
        self.release_count = 0

    def reset(self) -> None:
        self.state = "IDLE"
        self.current_key = None
        self.stable_count = 0
        self.release_count = 0

    def update(
        self,
        key_label: str | None,
        audio_recent: bool,
    ) -> str | None:
        event = None

        if self.state == "IDLE":
            if key_label is not None:
                self.current_key = key_label
                self.stable_count = 1
                self.release_count = 0
                self.state = "HOVER"

        elif self.state == "HOVER":
            if key_label == self.current_key:
                self.stable_count += 1

            elif key_label is None:
                self.reset()

            else:
                self.current_key = key_label
                self.stable_count = 1
                self.release_count = 0

            if (
                self.current_key is not None
                and self.stable_count >= self.stable_frames
                and audio_recent
            ):
                event = self.current_key
                self.state = "WAIT_RELEASE"
                self.release_count = 0

        elif self.state == "WAIT_RELEASE":
            if key_label is None:
                self.release_count += 1

                if self.release_count >= self.release_frames:
                    self.reset()
            else:
                self.release_count = 0

        return event