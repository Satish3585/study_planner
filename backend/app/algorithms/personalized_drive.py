from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from app.algorithms.timetable_optimizer import TimetableOptimizer
from app.utils.time_utils import minutes_to_time, format_time_str, time_to_minutes, parse_time_str

class PersonalizedDriveAlgorithm:
    """The core deterministic scheduling engine.
    Combines:
    - Academic Plan (WHAT to study, priorities)
    - Student Availability (WHEN free, sleep, college, travel, meals)
    - 9-8-7 Life Balance Framework (protecting rest, avoid burnout)
    Outputs a realistic, conflict-free timetable of study sessions and breaks.
    """

    def __init__(self):
        self.optimizer = TimetableOptimizer()

    def calculate_life_balance(self, availability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates how closely the schedule adheres to the 9-8-7 guideline:
        ~9h Sleep / Recovery
        ~8h Productive Work / College
        ~7h Personal Life / Study / Rest
        """
        wake_m = time_to_minutes(parse_time_str(availability_data.get("wake_time", "07:00")))
        sleep_m = time_to_minutes(parse_time_str(availability_data.get("sleep_time", "23:00")))
        
        sleep_duration_mins = (1440 - sleep_m + wake_m) if sleep_m > wake_m else (wake_m - sleep_m)
        sleep_hours = round(sleep_duration_mins / 60.0, 1)

        col_start_m = time_to_minutes(parse_time_str(availability_data.get("college_start", "09:00")))
        col_end_m = time_to_minutes(parse_time_str(availability_data.get("college_end", "16:00")))
        college_mins = max(0, col_end_m - col_start_m)
        travel_mins = availability_data.get("morning_travel_minutes", 30) + availability_data.get("evening_travel_minutes", 30)
        work_hours = round((college_mins + travel_mins) / 60.0, 1)

        study_hours = float(availability_data.get("available_study_hours", 3.0))
        personal_hours = max(0.0, round(24.0 - sleep_hours - work_hours - study_hours, 1))

        return {
            "sleep_hours": sleep_hours,
            "work_college_hours": work_hours,
            "study_hours": study_hours,
            "personal_leisure_hours": personal_hours,
            "is_balanced": (7.5 <= sleep_hours <= 9.5) and (study_hours <= 6.0)
        }

    def generate_timetable(
        self,
        academic_plan_topics: List[Dict[str, Any]],
        availability_data: Dict[str, Any],
        start_date: date,
        days_count: int = 7,
        existing_completed_entries: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Generates structured timetable entries for the requested period.
        Never touches completed historical sessions.
        """
        if not academic_plan_topics:
            return []

        # Session configuration
        session_duration = int(availability_data.get("session_duration_minutes", 45))
        break_duration = int(availability_data.get("break_duration_minutes", 10))
        target_study_hours = float(availability_data.get("available_study_hours", 3.0))
        target_study_mins = int(target_study_hours * 60)
        preferred_time = availability_data.get("preferred_study_time", "evening")

        meals = availability_data.get("meals", [])
        commitments = availability_data.get("commitments", [])

        # Calculate daily busy intervals
        busy_intervals = self.optimizer.get_busy_intervals(
            wake_time=availability_data.get("wake_time", "07:00"),
            sleep_time=availability_data.get("sleep_time", "23:00"),
            college_start=availability_data.get("college_start", "09:00"),
            college_end=availability_data.get("college_end", "16:00"),
            morning_travel_min=availability_data.get("morning_travel_minutes", 30),
            evening_travel_min=availability_data.get("evening_travel_minutes", 30),
            meals=meals,
            exercise_time=availability_data.get("exercise_time", "07:30"),
            exercise_min=availability_data.get("exercise_minutes", 30),
            commitments=commitments
        )

        free_windows = self.optimizer.get_free_windows(busy_intervals)
        
        # Sort topics: Weak (High priority) first, then Moderate, then Strong
        sorted_topics = sorted(
            academic_plan_topics,
            key=lambda x: (
                0 if x.get("priority") == "High" else (1 if x.get("priority") == "Medium" else 2),
                x.get("score_percentage", 50.0)
            )
        )

        timetable: List[Dict[str, Any]] = []
        topic_queue_idx = 0
        total_topics = len(sorted_topics)

        # Subject rotation tracker to avoid burnout
        last_subject_id = None

        for day_offset in range(days_count):
            current_day = start_date + timedelta(days=day_offset)
            current_day_str = current_day.isoformat()

            # Identify candidate study blocks inside free windows
            daily_study_mins_scheduled = 0

            # Prioritize windows matching user preference
            ordered_windows = self.optimizer.filter_by_preferred_time(free_windows, preferred_time)

            for win_start, win_end in ordered_windows:
                if daily_study_mins_scheduled >= target_study_mins:
                    break

                curr_pos = win_start
                while curr_pos + session_duration <= win_end and daily_study_mins_scheduled < target_study_mins:
                    # Pick topic with subject rotation
                    candidate_topic = None
                    initial_idx = topic_queue_idx

                    # Attempt to find next topic from a different subject
                    for offset in range(total_topics):
                        idx = (initial_idx + offset) % total_topics
                        top = sorted_topics[idx]
                        if total_topics == 1 or top.get("subject_id") != last_subject_id:
                            candidate_topic = top
                            topic_queue_idx = (idx + 1) % total_topics
                            break

                    if not candidate_topic:
                        candidate_topic = sorted_topics[topic_queue_idx % total_topics]
                        topic_queue_idx = (topic_queue_idx + 1) % total_topics

                    last_subject_id = candidate_topic.get("subject_id")

                    # Study Block
                    block_start_m = curr_pos
                    block_end_m = curr_pos + session_duration
                    curr_pos = block_end_m
                    daily_study_mins_scheduled += session_duration

                    timetable.append({
                        "date": current_day_str,
                        "start_time": format_time_str(minutes_to_time(block_start_m)),
                        "end_time": format_time_str(minutes_to_time(block_end_m)),
                        "duration_minutes": session_duration,
                        "subject_id": candidate_topic.get("subject_id"),
                        "subject_name": candidate_topic.get("subject_name", "Academic Subject"),
                        "topic": candidate_topic.get("topic", "Core Concepts"),
                        "activity_type": candidate_topic.get("activity_type", "Study"),
                        "priority": candidate_topic.get("priority", "High"),
                        "reason": candidate_topic.get("reason", "Assessment identified focus needed here."),
                        "status": "Scheduled"
                    })

                    # Break Block (if window has room for break)
                    if curr_pos + break_duration <= win_end and daily_study_mins_scheduled < target_study_mins:
                        break_start_m = curr_pos
                        break_end_m = curr_pos + break_duration
                        curr_pos = break_end_m

                        timetable.append({
                            "date": current_day_str,
                            "start_time": format_time_str(minutes_to_time(break_start_m)),
                            "end_time": format_time_str(minutes_to_time(break_end_m)),
                            "duration_minutes": break_duration,
                            "subject_id": None,
                            "subject_name": "Break",
                            "topic": "Rest & Refresh",
                            "activity_type": "Break",
                            "priority": "Low",
                            "reason": "Controlled cognitive recovery for optimal retention.",
                            "status": "Scheduled"
                        })
                    else:
                        break

        # Re-sort timetable entries strictly by date and start_time
        timetable.sort(key=lambda x: (x["date"], x["start_time"]))
        return timetable

    def rebalance_missed_session(
        self,
        missed_entry: Dict[str, Any],
        missed_reason: str,
        upcoming_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Handles a missed session without creating unrealistic backlog.
        Elevates priority of the missed topic in the next eligible session.
        """
        missed_topic = missed_entry.get("topic")
        missed_subject_id = missed_entry.get("subject_id")

        # Find first upcoming scheduled session of lower priority or moderate topic
        updated_entries = []
        replaced = False

        for entry in upcoming_entries:
            if not replaced and entry.get("status") == "Scheduled" and entry.get("activity_type") != "Break":
                # Swap or insert missed topic with High Priority
                if entry.get("priority") != "High" or entry.get("subject_id") == missed_subject_id:
                    entry["topic"] = missed_topic
                    entry["subject_id"] = missed_subject_id
                    entry["subject_name"] = missed_entry.get("subject_name", entry.get("subject_name"))
                    entry["priority"] = "High"
                    entry["reason"] = f"Rescheduled: Prioritized after missed session due to '{missed_reason}'."
                    replaced = True
            updated_entries.append(entry)

        return updated_entries
