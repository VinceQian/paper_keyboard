from __future__ import annotations

import math
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any


@dataclass
class KeyHistoryEntry:
    perf_timestamp: float
    frame_id: int
    frame_timestamp: float
    key_label: str | None
    board_x: float | None
    board_y: float | None
    fingers: list[dict[str, Any]]
    candidates: list[dict[str, Any]]


@dataclass
class MotionEntry:
    original_entry: KeyHistoryEntry
    smooth_x: float
    smooth_y: float
    nearest_key: dict[str, Any] | None
    nearest_key_label: str | None
    nearest_key_distance: float | None
    acceleration_value: float
    turn_value: float
    time_score: float
    key_score: float
    motion_score: float
    final_score: float


class KeyHistoryBuffer:
    """
    Store recent visual finger positions and key candidates.

    This class supports two tap-picking methods:

    1. hover-difference method:
       Estimate the hover/background key, then choose a different key near the impact.

    2. motion-peak method:
       Use the finger trajectory around the audio peak. Pick the frame that has
       strong motion change, is close to the audio peak, and is close to a key center.

    The motion-peak method is better when:
    - the finger hovers over one key,
    - briefly moves to another key to tap,
    - then returns to the hover key.
    """

    def __init__(self, max_age_seconds: float = 1.0):
        self.max_age_seconds = max_age_seconds
        self.entries: deque[KeyHistoryEntry] = deque()

    def add(
        self,
        perf_timestamp: float,
        frame_id: int,
        frame_timestamp: float,
        key_label: str | None,
        board_x: float | None,
        board_y: float | None,
        fingers: list[dict[str, Any]],
        candidates: list[dict[str, Any]],
    ) -> None:
        self.entries.append(
            KeyHistoryEntry(
                perf_timestamp=perf_timestamp,
                frame_id=frame_id,
                frame_timestamp=frame_timestamp,
                key_label=key_label,
                board_x=board_x,
                board_y=board_y,
                fingers=fingers,
                candidates=candidates,
            )
        )

        self._remove_old(perf_timestamp)

    def _remove_old(self, current_time: float) -> None:
        while (
            self.entries
            and current_time - self.entries[0].perf_timestamp > self.max_age_seconds
        ):
            self.entries.popleft()

    # -------------------------------------------------------------------------
    # Method 1: hover-difference picker
    # -------------------------------------------------------------------------

    def pick_event_by_hover_difference(
        self,
        peak_time: float,
        tap_offset: float = 0.0,
        pre_hover_start: float = 0.25,
        pre_hover_end: float = 0.08,
        impact_before: float = 0.06,
        impact_after: float = 0.06,
        post_hover_start: float = 0.08,
        post_hover_end: float = 0.25,
        min_impact_entries: int = 1,
    ) -> dict[str, Any] | None:
        adjusted_peak_time = peak_time + tap_offset

        pre_hover_entries = self._get_entries_in_range(
            start=adjusted_peak_time - pre_hover_start,
            end=adjusted_peak_time - pre_hover_end,
            require_key=True,
            require_position=False,
        )

        post_hover_entries = self._get_entries_in_range(
            start=adjusted_peak_time + post_hover_start,
            end=adjusted_peak_time + post_hover_end,
            require_key=True,
            require_position=False,
        )

        hover_entries = pre_hover_entries + post_hover_entries
        hover_key = self._mode_key(hover_entries)

        impact_entries = self._get_entries_in_range(
            start=adjusted_peak_time - impact_before,
            end=adjusted_peak_time + impact_after,
            require_key=True,
            require_position=False,
        )

        if len(impact_entries) < min_impact_entries:
            return None

        selected_entry = self._select_impact_entry(
            impact_entries=impact_entries,
            hover_key=hover_key,
            adjusted_peak_time=adjusted_peak_time,
        )

        if selected_entry is None:
            return None

        selected_label = selected_entry.key_label

        if selected_label is None:
            return None

        impact_labels = [
            entry.key_label
            for entry in impact_entries
            if entry.key_label is not None
        ]

        impact_counter = Counter(impact_labels)

        selected_count = impact_counter.get(selected_label, 0)
        selected_ratio = selected_count / max(len(impact_labels), 1)

        non_hover_labels = [
            label
            for label in impact_labels
            if hover_key is None or label != hover_key
        ]

        return {
            "method": "hover_difference",
            "key_label": selected_label,
            "key": None,
            "frame_id": selected_entry.frame_id,
            "frame_timestamp": selected_entry.frame_timestamp,
            "selected_visual_perf_timestamp": selected_entry.perf_timestamp,
            "board_x": selected_entry.board_x,
            "board_y": selected_entry.board_y,
            "fingers": selected_entry.fingers,
            "candidates": selected_entry.candidates,
            "hover_key": hover_key,
            "impact_labels": impact_labels,
            "impact_entry_count": len(impact_entries),
            "non_hover_labels": non_hover_labels,
            "selected_count": selected_count,
            "selected_ratio": selected_ratio,
            "adjusted_peak_time": adjusted_peak_time,
            "tap_offset": tap_offset,
            "pre_hover_count": len(pre_hover_entries),
            "post_hover_count": len(post_hover_entries),
        }

    # -------------------------------------------------------------------------
    # Method 2: motion-peak picker
    # -------------------------------------------------------------------------

    def pick_event_by_motion_peak(
        self,
        peak_time: float,
        keys: list[dict[str, Any]],
        tap_offset: float = 0.0,
        window_before: float = 0.25,
        window_after: float = 0.08,
        smooth_radius: int = 1,
        time_sigma: float = 0.07,
        max_key_distance: float = 32.0,
        min_entries: int = 4,
        motion_weight: float = 0.40,
        time_weight: float = 0.30,
        key_weight: float = 0.30,
    ) -> dict[str, Any] | None:
        """
        Pick a tap key using finger motion around the audio peak.

        Steps:
        1. Take visual history around adjusted_peak_time.
        2. Smooth board_x / board_y.
        3. Compute velocity change and direction change.
        4. Score every frame by:
           - motion change score
           - closeness to audio peak
           - closeness to nearest key center
        5. Select the best frame.
        6. Return the nearest key at that frame.

        This is designed for cases like:
            hover around X -> tap S -> return to X
        """

        adjusted_peak_time = peak_time + tap_offset

        raw_entries = self._get_entries_in_range(
            start=adjusted_peak_time - window_before,
            end=adjusted_peak_time + window_after,
            require_key=False,
            require_position=True,
        )

        if len(raw_entries) < min_entries:
            return None

        smoothed_positions = self._smooth_positions(
            entries=raw_entries,
            radius=smooth_radius,
        )

        motion_entries = self._build_motion_entries(
            entries=raw_entries,
            smoothed_positions=smoothed_positions,
            keys=keys,
            adjusted_peak_time=adjusted_peak_time,
            time_sigma=time_sigma,
            max_key_distance=max_key_distance,
        )

        if not motion_entries:
            return None

        self._score_motion_entries(
            motion_entries=motion_entries,
            motion_weight=motion_weight,
            time_weight=time_weight,
            key_weight=key_weight,
        )

        valid_entries = [
            entry
            for entry in motion_entries
            if entry.nearest_key is not None
            and entry.nearest_key_distance is not None
            and entry.nearest_key_distance <= max_key_distance
        ]

        if not valid_entries:
            return None

        selected_motion_entry = max(
            valid_entries,
            key=lambda entry: entry.final_score,
        )

        selected_entry = selected_motion_entry.original_entry
        selected_key = selected_motion_entry.nearest_key

        if selected_key is None:
            return None

        selected_label = str(selected_key["label"])

        debug_candidates = self._summarize_top_motion_entries(
            motion_entries=valid_entries,
            limit=5,
        )

        return {
            "method": "motion_peak",
            "key_label": selected_label,
            "key": selected_key,
            "frame_id": selected_entry.frame_id,
            "frame_timestamp": selected_entry.frame_timestamp,
            "selected_visual_perf_timestamp": selected_entry.perf_timestamp,
            "board_x": selected_motion_entry.smooth_x,
            "board_y": selected_motion_entry.smooth_y,
            "fingers": selected_entry.fingers,
            "candidates": selected_entry.candidates,
            "adjusted_peak_time": adjusted_peak_time,
            "tap_offset": tap_offset,
            "window_entry_count": len(raw_entries),
            "selected_key_distance": selected_motion_entry.nearest_key_distance,
            "acceleration_value": selected_motion_entry.acceleration_value,
            "turn_value": selected_motion_entry.turn_value,
            "motion_score": selected_motion_entry.motion_score,
            "time_score": selected_motion_entry.time_score,
            "key_score": selected_motion_entry.key_score,
            "final_score": selected_motion_entry.final_score,
            "top_motion_candidates": debug_candidates,
            "window_before": window_before,
            "window_after": window_after,
            "time_sigma": time_sigma,
            "max_key_distance": max_key_distance,
        }

    def _smooth_positions(
        self,
        entries: list[KeyHistoryEntry],
        radius: int,
    ) -> list[tuple[float, float]]:
        smoothed = []

        for i in range(len(entries)):
            start = max(0, i - radius)
            end = min(len(entries), i + radius + 1)

            xs = [
                entries[j].board_x
                for j in range(start, end)
                if entries[j].board_x is not None
            ]
            ys = [
                entries[j].board_y
                for j in range(start, end)
                if entries[j].board_y is not None
            ]

            if not xs or not ys:
                smoothed.append((0.0, 0.0))
            else:
                smoothed.append(
                    (
                        sum(xs) / len(xs),
                        sum(ys) / len(ys),
                    )
                )

        return smoothed

    def _build_motion_entries(
        self,
        entries: list[KeyHistoryEntry],
        smoothed_positions: list[tuple[float, float]],
        keys: list[dict[str, Any]],
        adjusted_peak_time: float,
        time_sigma: float,
        max_key_distance: float,
    ) -> list[MotionEntry]:
        motion_entries: list[MotionEntry] = []

        for i, entry in enumerate(entries):
            smooth_x, smooth_y = smoothed_positions[i]

            nearest_key, nearest_distance = self._find_nearest_key_by_center(
                x=smooth_x,
                y=smooth_y,
                keys=keys,
            )

            time_delta = abs(entry.perf_timestamp - adjusted_peak_time)
            time_score = math.exp(-((time_delta / max(time_sigma, 1e-6)) ** 2))

            if nearest_distance is None:
                key_score = 0.0
            else:
                key_score = max(
                    0.0,
                    1.0 - nearest_distance / max(max_key_distance, 1e-6),
                )

            acceleration_value = self._compute_acceleration_value(
                index=i,
                entries=entries,
                smoothed_positions=smoothed_positions,
            )

            turn_value = self._compute_turn_value(
                index=i,
                entries=entries,
                smoothed_positions=smoothed_positions,
            )

            motion_entries.append(
                MotionEntry(
                    original_entry=entry,
                    smooth_x=smooth_x,
                    smooth_y=smooth_y,
                    nearest_key=nearest_key,
                    nearest_key_label=(
                        str(nearest_key["label"]) if nearest_key is not None else None
                    ),
                    nearest_key_distance=nearest_distance,
                    acceleration_value=acceleration_value,
                    turn_value=turn_value,
                    time_score=time_score,
                    key_score=key_score,
                    motion_score=0.0,
                    final_score=0.0,
                )
            )

        return motion_entries

    def _compute_acceleration_value(
        self,
        index: int,
        entries: list[KeyHistoryEntry],
        smoothed_positions: list[tuple[float, float]],
    ) -> float:
        if index <= 0 or index >= len(entries) - 1:
            return 0.0

        t0 = entries[index - 1].perf_timestamp
        t1 = entries[index].perf_timestamp
        t2 = entries[index + 1].perf_timestamp

        x0, y0 = smoothed_positions[index - 1]
        x1, y1 = smoothed_positions[index]
        x2, y2 = smoothed_positions[index + 1]

        dt1 = max(t1 - t0, 1e-6)
        dt2 = max(t2 - t1, 1e-6)

        vx1 = (x1 - x0) / dt1
        vy1 = (y1 - y0) / dt1
        vx2 = (x2 - x1) / dt2
        vy2 = (y2 - y1) / dt2

        ax = vx2 - vx1
        ay = vy2 - vy1

        return math.sqrt(ax * ax + ay * ay)

    def _compute_turn_value(
        self,
        index: int,
        entries: list[KeyHistoryEntry],
        smoothed_positions: list[tuple[float, float]],
    ) -> float:
        if index <= 0 or index >= len(entries) - 1:
            return 0.0

        t0 = entries[index - 1].perf_timestamp
        t1 = entries[index].perf_timestamp
        t2 = entries[index + 1].perf_timestamp

        x0, y0 = smoothed_positions[index - 1]
        x1, y1 = smoothed_positions[index]
        x2, y2 = smoothed_positions[index + 1]

        dt1 = max(t1 - t0, 1e-6)
        dt2 = max(t2 - t1, 1e-6)

        vx1 = (x1 - x0) / dt1
        vy1 = (y1 - y0) / dt1
        vx2 = (x2 - x1) / dt2
        vy2 = (y2 - y1) / dt2

        norm1 = math.sqrt(vx1 * vx1 + vy1 * vy1)
        norm2 = math.sqrt(vx2 * vx2 + vy2 * vy2)

        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0

        cos_angle = (vx1 * vx2 + vy1 * vy2) / (norm1 * norm2)
        cos_angle = max(-1.0, min(1.0, cos_angle))

        # 0 means same direction.
        # 1 means perpendicular.
        # 2 means opposite direction.
        return 1.0 - cos_angle

    def _score_motion_entries(
        self,
        motion_entries: list[MotionEntry],
        motion_weight: float,
        time_weight: float,
        key_weight: float,
    ) -> None:
        max_acc = max(
            (entry.acceleration_value for entry in motion_entries),
            default=0.0,
        )

        max_turn = max(
            (entry.turn_value for entry in motion_entries),
            default=0.0,
        )

        for entry in motion_entries:
            acc_score = (
                entry.acceleration_value / max_acc
                if max_acc > 1e-6
                else 0.0
            )

            turn_score = (
                entry.turn_value / max_turn
                if max_turn > 1e-6
                else 0.0
            )

            # Combine acceleration and direction change.
            entry.motion_score = 0.65 * acc_score + 0.35 * turn_score

            entry.final_score = (
                motion_weight * entry.motion_score
                + time_weight * entry.time_score
                + key_weight * entry.key_score
            )

    def _find_nearest_key_by_center(
        self,
        x: float,
        y: float,
        keys: list[dict[str, Any]],
    ) -> tuple[dict[str, Any] | None, float | None]:
        best_key = None
        best_distance = None

        for key in keys:
            center_x = float(key["x"]) + float(key["w"]) / 2.0
            center_y = float(key["y"]) + float(key["h"]) / 2.0

            dx = x - center_x
            dy = y - center_y

            distance = math.sqrt(dx * dx + dy * dy)

            if best_distance is None or distance < best_distance:
                best_key = key
                best_distance = distance

        return best_key, best_distance

    def _summarize_top_motion_entries(
        self,
        motion_entries: list[MotionEntry],
        limit: int,
    ) -> list[dict[str, Any]]:
        sorted_entries = sorted(
            motion_entries,
            key=lambda entry: entry.final_score,
            reverse=True,
        )

        summary = []

        for entry in sorted_entries[:limit]:
            summary.append(
                {
                    "key": entry.nearest_key_label,
                    "frame_id": entry.original_entry.frame_id,
                    "dt": entry.original_entry.perf_timestamp,
                    "distance": entry.nearest_key_distance,
                    "acceleration": entry.acceleration_value,
                    "turn": entry.turn_value,
                    "motion_score": entry.motion_score,
                    "time_score": entry.time_score,
                    "key_score": entry.key_score,
                    "final_score": entry.final_score,
                }
            )

        return summary

    # -------------------------------------------------------------------------
    # Shared helpers
    # -------------------------------------------------------------------------

    def _get_entries_in_range(
        self,
        start: float,
        end: float,
        require_key: bool,
        require_position: bool,
    ) -> list[KeyHistoryEntry]:
        results = []

        for entry in self.entries:
            if not (start <= entry.perf_timestamp <= end):
                continue

            if require_key and entry.key_label is None:
                continue

            if require_position and (
                entry.board_x is None or entry.board_y is None
            ):
                continue

            results.append(entry)

        return results

    def _mode_key(self, entries: list[KeyHistoryEntry]) -> str | None:
        labels = [
            entry.key_label
            for entry in entries
            if entry.key_label is not None
        ]

        if not labels:
            return None

        counter = Counter(labels)
        return counter.most_common(1)[0][0]

    def _select_impact_entry(
        self,
        impact_entries: list[KeyHistoryEntry],
        hover_key: str | None,
        adjusted_peak_time: float,
    ) -> KeyHistoryEntry | None:
        non_hover_entries = [
            entry
            for entry in impact_entries
            if entry.key_label is not None
            and (hover_key is None or entry.key_label != hover_key)
        ]

        if non_hover_entries:
            return self._closest_entry_to_time(non_hover_entries, adjusted_peak_time)

        return self._closest_entry_to_time(impact_entries, adjusted_peak_time)

    def _closest_entry_to_time(
        self,
        entries: list[KeyHistoryEntry],
        target_time: float,
    ) -> KeyHistoryEntry | None:
        if not entries:
            return None

        return min(
            entries,
            key=lambda entry: abs(entry.perf_timestamp - target_time),
        )