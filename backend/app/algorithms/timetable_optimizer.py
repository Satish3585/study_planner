from typing import List, Tuple, Dict, Any
from app.utils.time_utils import parse_time_str, time_to_minutes, minutes_to_time, format_time_str

class TimetableOptimizer:
    """Handles interval arithmetic, schedule collision avoidance,
    and free-window extraction for the 24-hour day (0 to 1440 minutes).
    """

    @staticmethod
    def get_busy_intervals(
        wake_time: str,
        sleep_time: str,
        college_start: str,
        college_end: str,
        morning_travel_min: int,
        evening_travel_min: int,
        meals: List[Dict[str, Any]],
        exercise_time: str,
        exercise_min: int,
        commitments: List[Dict[str, Any]]
    ) -> List[Tuple[int, int]]:
        """Returns merged list of (start_min, end_min) when the student is unavailable."""
        busy: List[Tuple[int, int]] = []

        wake_m = time_to_minutes(parse_time_str(wake_time))
        sleep_m = time_to_minutes(parse_time_str(sleep_time))

        # 1. Sleep interval (protects sleep)
        if sleep_m > wake_m:
            # Sleep within same day: sleep_m to 1440, and 0 to wake_m
            busy.append((sleep_m, 1440))
            busy.append((0, wake_m))
        else:
            # Normal overnight: e.g. 23:00 to 07:00
            busy.append((sleep_m, wake_m))

        # 2. College / Work + Travel
        if college_start and college_end:
            col_start_m = time_to_minutes(parse_time_str(college_start))
            col_end_m = time_to_minutes(parse_time_str(college_end))
            # Prepend morning travel, append evening travel
            effective_start = max(0, col_start_m - morning_travel_min)
            effective_end = min(1440, col_end_m + evening_travel_min)
            busy.append((effective_start, effective_end))

        # 3. Meals
        for meal in meals:
            m_start = meal.get("start")
            m_end = meal.get("end")
            if m_start and m_end:
                busy.append((time_to_minutes(parse_time_str(m_start)), time_to_minutes(parse_time_str(m_end))))

        # 4. Exercise
        if exercise_time and exercise_min > 0:
            ex_start = time_to_minutes(parse_time_str(exercise_time))
            busy.append((ex_start, min(1440, ex_start + exercise_min)))

        # 5. Commitments
        for c in commitments:
            c_start = c.get("start")
            c_end = c.get("end")
            if c_start and c_end:
                busy.append((time_to_minutes(parse_time_str(c_start)), time_to_minutes(parse_time_str(c_end))))

        # Normalize and merge overlapping busy intervals
        return TimetableOptimizer.merge_intervals(busy)

    @staticmethod
    def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        if not intervals:
            return []
        # Filter and sort
        valid = [(max(0, s), min(1440, e)) for s, e in intervals if e > s]
        valid.sort(key=lambda x: x[0])

        merged = [valid[0]]
        for cur_start, cur_end in valid[1:]:
            prev_start, prev_end = merged[-1]
            if cur_start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, cur_end))
            else:
                merged.append((cur_start, cur_end))
        return merged

    @staticmethod
    def get_free_windows(busy_intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Returns list of (start_min, end_min) free windows in a 1440-minute day."""
        free = []
        cur = 0
        for b_start, b_end in busy_intervals:
            if b_start > cur:
                free.append((cur, b_start))
            cur = max(cur, b_end)
        if cur < 1440:
            free.append((cur, 1440))
        return free

    @staticmethod
    def filter_by_preferred_time(
        free_windows: List[Tuple[int, int]], preferred_time: str
    ) -> List[Tuple[int, int]]:
        """Orders or filters free windows favoring student's preferred study window:
        morning: 06:00-12:00 (360-720)
        afternoon: 12:00-17:00 (720-1020)
        evening: 17:00-21:00 (1020-1260)
        night: 21:00-24:00 (1260-1440)
        """
        pref_ranges = {
            "morning": (360, 720),
            "afternoon": (720, 1020),
            "evening": (1020, 1260),
            "night": (1260, 1440)
        }
        target_range = pref_ranges.get(preferred_time.lower(), (1020, 1260))

        # Sort windows by overlap with preferred range
        def pref_score(w: Tuple[int, int]) -> int:
            overlap = max(0, min(w[1], target_range[1]) - max(w[0], target_range[0]))
            return overlap

        return sorted(free_windows, key=pref_score, reverse=True)
