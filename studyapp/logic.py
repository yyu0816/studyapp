from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional

MAX_SESSION_DURATION = timedelta(minutes=90)
REQUIRED_BREAK_DURATION = timedelta(minutes=10)
BREAK_EXEMPT_TYPES = {"lunch", "dinner", "bath", "sleep", "toilet", "rest"}
MIN_HALF_DAY_BUFFER_HOURS = 4
FULL_DAY_BUFFER_HOURS = 8


@dataclass
class Activity:
    start: datetime
    end: datetime
    category: str = "study"

    def duration(self) -> timedelta:
        return self.end - self.start


@dataclass
class BufferPeriod:
    date: date
    start: datetime
    end: datetime
    is_full_day: bool

    def duration(self) -> timedelta:
        return self.end - self.start


def is_valid_study_session(activity: Activity) -> bool:
    """檢查單次讀書 session 是否符合時間上限。"""
    if activity.category != "study":
        return False
    return activity.duration() <= MAX_SESSION_DURATION


def requires_post_session_break(next_activity_category: Optional[str]) -> bool:
    """判斷下一個活動是否仍需插入 10 分鐘休息。"""
    if next_activity_category is None:
        return True
    return next_activity_category.lower() not in BREAK_EXEMPT_TYPES


def get_post_session_break_window(
    session_end: datetime,
    next_activity_start: Optional[datetime] = None,
    next_activity_category: Optional[str] = None,
) -> Optional[tuple[datetime, datetime]]:
    """回傳建議的休息時段，若不需要休息則回傳 None。"""
    if not requires_post_session_break(next_activity_category):
        return None

    if next_activity_start is None:
        return session_end, session_end + REQUIRED_BREAK_DURATION

    break_end = min(session_end + REQUIRED_BREAK_DURATION, next_activity_start)
    if break_end <= session_end:
        return None
    return session_end, break_end


def find_daily_buffer_periods(
    activities: Iterable[Activity],
    minimum_hours: float = MIN_HALF_DAY_BUFFER_HOURS,
) -> List[BufferPeriod]:
    """找出單日內可視為 buffer 的連續空檔。"""
    sorted_activities = sorted(activities, key=lambda activity: activity.start)
    periods: List[BufferPeriod] = []

    if not sorted_activities:
        return [
            BufferPeriod(
                date=date.today(),
                start=datetime.combine(date.today(), datetime.min.time()),
                end=datetime.combine(date.today(), datetime.max.time()),
                is_full_day=True,
            )
        ]

    current_day = sorted_activities[0].start.date()
    day_start = datetime.combine(current_day, datetime.min.time())
    day_end = datetime.combine(current_day, datetime.max.time())
    gap_start = day_start

    for activity in sorted_activities:
        if activity.start > gap_start:
            gap = activity.start - gap_start
            if gap >= timedelta(hours=minimum_hours):
                periods.append(
                    BufferPeriod(
                        date=current_day,
                        start=gap_start,
                        end=activity.start,
                        is_full_day=False,
                    )
                )
        gap_start = max(gap_start, activity.end)

    if day_end > gap_start:
        gap = day_end - gap_start
        if gap >= timedelta(hours=minimum_hours):
            periods.append(
                BufferPeriod(
                    date=current_day,
                    start=gap_start,
                    end=day_end,
                    is_full_day=False,
                )
            )

    if not periods and all(activity.category != "study" for activity in sorted_activities):
        periods.append(
            BufferPeriod(
                date=current_day,
                start=day_start,
                end=day_end,
                is_full_day=True,
            )
        )

    return periods


def find_weekly_buffer_periods(
    weekly_activities: Iterable[Activity],
    minimum_half_day_hours: float = MIN_HALF_DAY_BUFFER_HOURS,
) -> List[BufferPeriod]:
    """找出一週內的半天或整天 buffer day。"""
    activities_by_date: dict[date, List[Activity]] = {}
    for activity in weekly_activities:
        activities_by_date.setdefault(activity.start.date(), []).append(activity)

    buffer_periods: List[BufferPeriod] = []
    for activity_date, day_activities in activities_by_date.items():
        study_sessions = [activity for activity in day_activities if activity.category == "study"]
        if not study_sessions:
            buffer_periods.append(
                BufferPeriod(
                    date=activity_date,
                    start=datetime.combine(activity_date, datetime.min.time()),
                    end=datetime.combine(activity_date, datetime.max.time()),
                    is_full_day=True,
                )
            )
            continue

        sorted_study = sorted(study_sessions, key=lambda activity: activity.start)
        day_start = datetime.combine(activity_date, datetime.min.time())
        day_end = datetime.combine(activity_date, datetime.max.time())
        gap_start = day_start

        for session in sorted_study:
            if session.start > gap_start:
                gap = session.start - gap_start
                if gap >= timedelta(hours=minimum_half_day_hours):
                    buffer_periods.append(
                        BufferPeriod(
                            date=activity_date,
                            start=gap_start,
                            end=session.start,
                            is_full_day=False,
                        )
                    )
            gap_start = max(gap_start, session.end)

        if day_end > gap_start:
            gap = day_end - gap_start
            if gap >= timedelta(hours=minimum_half_day_hours):
                buffer_periods.append(
                    BufferPeriod(
                        date=activity_date,
                        start=gap_start,
                        end=day_end,
                        is_full_day=False,
                    )
                )

    return buffer_periods


def summarize_buffer_days(buffer_periods: Iterable[BufferPeriod]) -> List[str]:
    """用文字說明 buffer day 的種類。"""
    summary: List[str] = []
    for buffer in buffer_periods:
        if buffer.is_full_day:
            summary.append(f"{buffer.date}：整天緩衝日")
        else:
            summary.append(
                f"{buffer.date}：{buffer.start.strftime('%H:%M')} - {buffer.end.strftime('%H:%M')} 半天緩衝時段"
            )
    return summary


WEEKDAY_NAME_TO_INDEX = {
    "週一": 0,
    "週二": 1,
    "週三": 2,
    "週四": 3,
    "週五": 4,
    "週六": 5,
    "週日": 6,
}

BREAK_EXEMPT_KEYWORDS = {
    "午餐",
    "晚餐",
    "盥洗",
    "睡覺",
    "toilet",
    "bath",
    "sleep",
    "lunch",
    "dinner",
}


def normalize_weekday_name(name: str) -> str:
    return name.strip()


def weekday_to_date(start_date: date, weekday_name: str) -> Optional[date]:
    normalized = normalize_weekday_name(weekday_name)
    if normalized not in WEEKDAY_NAME_TO_INDEX:
        return None
    target_index = WEEKDAY_NAME_TO_INDEX[normalized]
    delta_days = (target_index - start_date.weekday()) % 7
    return start_date + timedelta(days=delta_days)


def is_break_exempt_activity(title: Optional[str]) -> bool:
    if not title:
        return False
    lowered = title.lower()
    return any(keyword in lowered for keyword in BREAK_EXEMPT_KEYWORDS)


def expand_fixed_events_to_activities(
    fixed_events: list[dict[str, Any]],
    start_date: date,
    end_date: date,
) -> List[Activity]:
    """將 studyapp 固定行程轉成一週內的 Activity。"""
    activities: List[Activity] = []
    current_date = start_date
    while current_date <= end_date:
        weekday_name = list(WEEKDAY_NAME_TO_INDEX.keys())[current_date.weekday()]
        for event in fixed_events:
            if weekday_name in event.get("weekdays", []):
                if not event.get("start") or not event.get("end"):
                    continue
                try:
                    start_time = datetime.strptime(event["start"], "%H:%M").time()
                    end_time = datetime.strptime(event["end"], "%H:%M").time()
                except ValueError:
                    continue
                start_dt = datetime.combine(current_date, start_time)
                end_dt = datetime.combine(current_date, end_time)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                activities.append(
                    Activity(start=start_dt, end=end_dt, category=event.get("title", "fixed"))
                )
        current_date += timedelta(days=1)
    return activities


def count_subject_assignments(plan_data: dict[str, Any], week_start: date, week_end: date) -> dict[date, int]:
    assignments: dict[date, int] = {}
    current_date = week_start
    while current_date <= week_end:
        assignments[current_date] = 0
        current_date += timedelta(days=1)

    for subject in plan_data.get("subjects", []) or []:
        for weekday in subject.get("weekdays", []) or []:
            assigned_date = weekday_to_date(week_start, weekday)
            if assigned_date and week_start <= assigned_date <= week_end:
                assignments[assigned_date] += 1
    return assignments


def find_plan_buffer_days(
    plan_data: dict[str, Any],
    week_start: date,
    week_end: date,
    minimum_half_day_hours: float = MIN_HALF_DAY_BUFFER_HOURS,
) -> List[BufferPeriod]:
    """根據 studyapp 的 plan_data 找出一週內合適的 buffer day。"""
    assignments = count_subject_assignments(plan_data, week_start, week_end)
    fixed_activities = expand_fixed_events_to_activities(plan_data.get("fixed_events", []) or [], week_start, week_end)
    buffer_days: List[BufferPeriod] = []

    for day, count in assignments.items():
        if count == 0:
            buffer_days.append(
                BufferPeriod(
                    date=day,
                    start=datetime.combine(day, datetime.min.time()),
                    end=datetime.combine(day, datetime.max.time()),
                    is_full_day=True,
                )
            )
            continue

        day_events = [activity for activity in fixed_activities if activity.start.date() == day]
        if not day_events:
            continue

        sorted_events = sorted(day_events, key=lambda activity: activity.start)
        gap_start = datetime.combine(day, datetime.min.time())
        for event in sorted_events:
            if event.start > gap_start:
                gap = event.start - gap_start
                if gap >= timedelta(hours=minimum_half_day_hours):
                    buffer_days.append(BufferPeriod(date=day, start=gap_start, end=event.start, is_full_day=False))
            gap_start = max(gap_start, event.end)

        day_end = datetime.combine(day, datetime.max.time())
        if day_end > gap_start and (day_end - gap_start) >= timedelta(hours=minimum_half_day_hours):
            buffer_days.append(BufferPeriod(date=day, start=gap_start, end=day_end, is_full_day=False))

    if not buffer_days:
        # 若一週都沒有明確候選，則回傳週內第一個無 subjects 的日期
        no_subject_days = [day for day, count in assignments.items() if count == 0]
        if no_subject_days:
            day = no_subject_days[0]
            buffer_days.append(
                BufferPeriod(
                    date=day,
                    start=datetime.combine(day, datetime.min.time()),
                    end=datetime.combine(day, datetime.max.time()),
                    is_full_day=True,
                )
            )

    return buffer_days


import math
from typing import Any, Dict

def merge_intervals(intervals):
    if not intervals: return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def get_minutes(time_str):
    try:
        t = datetime.strptime(time_str, "%H:%M").time()
        return t.hour * 60 + t.minute
    except:
        return 0

def calculate_daily_available_pomodoros(current_date, plan):
    is_weekend = current_date.weekday() >= 5
    wake_key = "weekend_wake" if is_weekend else "weekday_wake"
    sleep_key = "weekend_sleep" if is_weekend else "weekday_sleep"
    
    wake_time = plan.get(wake_key, "07:00")
    sleep_time = plan.get(sleep_key, "23:30")
    
    wake_m = get_minutes(wake_time)
    sleep_m = get_minutes(sleep_time)
    
    blocking_intervals = []
    
    # 1. Sleep
    if sleep_m <= wake_m:
        blocking_intervals.append((0, wake_m))
        if sleep_m > 0:
            blocking_intervals.append((sleep_m, 1440))
    else:
        blocking_intervals.append((0, wake_m))
        blocking_intervals.append((sleep_m, 1440))
        
    # 2. Routines
    routines = plan.get("routines", {})
    for r_name, r_data in routines.items():
        if r_data.get("start") and r_data.get("end"):
            sm = get_minutes(r_data["start"])
            em = get_minutes(r_data["end"])
            if sm < em:
                blocking_intervals.append((sm, em))
                
    # 3. Non-parallel fixed events
    weekday_str = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][current_date.weekday()]
    fixed_events = plan.get("fixed_events", [])
    
    parallel_intervals = []
    
    for ev in fixed_events:
        if weekday_str in ev.get("weekdays", []):
            sm = get_minutes(ev.get("start", "00:00"))
            em = get_minutes(ev.get("end", "00:00"))
            if sm < em:
                if ev.get("concurrent_with_study", False):
                    parallel_intervals.append((sm, em))
                else:
                    blocking_intervals.append((sm, em))
                    
    blocking_intervals = merge_intervals(blocking_intervals)
    parallel_intervals = merge_intervals(parallel_intervals)
    
    total_blocked_minutes = 0
    for b_start, b_end in blocking_intervals:
        overlap = 0
        for p_start, p_end in parallel_intervals:
            o_start = max(b_start, p_start)
            o_end = min(b_end, p_end)
            if o_start < o_end:
                overlap += (o_end - o_start)
        total_blocked_minutes += (b_end - b_start) - overlap
        
    free_minutes = 1440 - total_blocked_minutes
    free_hours = free_minutes / 60.0
    return math.floor(free_hours * 2)

def generate_daily_schedule(plan: dict) -> List[Dict[str, Any]]:
    subjects_data = plan.get("subjects", [])
    start_date_str = plan.get("start_date")
    end_date_str = plan.get("end_date")
    
    if not subjects_data or not start_date_str or not end_date_str:
        return []
        
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except Exception:
        return []
        
    if end_date < start_date:
        return []
        
    total_days = (end_date - start_date).days + 1
    
    # 1. 計算每天的可用番茄鐘數
    daily_pomodoros = []
    total_pomodoros = 0
    current_date = start_date
    for _ in range(total_days):
        p = calculate_daily_available_pomodoros(current_date, plan)
        daily_pomodoros.append({"date": current_date.strftime("%Y-%m-%d"), "pomodoros": p})
        total_pomodoros += p
        current_date += timedelta(days=1)
        
    if total_pomodoros == 0:
        return []

    # 2. 計算有效天數與緩衝天數 (八二法則)
    effective_days = math.floor(total_days * 0.8)
    buffer_days = total_days - effective_days
    
    # 計算「有效學習日」的番茄鐘總數
    effective_pomodoros = sum(d["pomodoros"] for d in daily_pomodoros[:effective_days])

    # 3. 處理科目資料，計算每個科目的總頁數/進度
    subject_progress = []
    for subject in subjects_data:
        name = subject.get("name", "未命名科目")
        materials = subject.get("materials", [])
        total_qty = 0
        unit = "單位"
        for mat in materials:
            total_qty += mat.get("quantity", 0)
            if mat.get("type") in ["練習題", "模擬考"]:
                unit = "回"
            elif mat.get("type") in ["課本", "教材", "筆記"]:
                unit = "頁"
            elif mat.get("type") == "教學影片":
                unit = "小時"
        
        subject_progress.append({
            "name": name,
            "total_qty": total_qty,
            "unit": unit,
            "remaining_qty": total_qty
        })

    num_subjects = len(subject_progress)
    if num_subjects == 0:
        return []

    base_pomo_per_subject = effective_pomodoros // num_subjects
    remainder = effective_pomodoros % num_subjects

    for i, sp in enumerate(subject_progress):
        pomo_count = base_pomo_per_subject + (1 if i < remainder else 0)
        sp["allocated_pomodoros"] = pomo_count
        sp["remaining_pomodoros"] = pomo_count
        sp["progress_per_pomo"] = sp["total_qty"] / pomo_count if pomo_count > 0 else 0

    # 4. 產生每一天的排程
    schedule = []
    
    available_subjects = [sp for sp in subject_progress if sp["remaining_pomodoros"] > 0]
    last_subject_name = None
    consecutive_count = 0

    # 安排有效學習日
    for day_idx in range(effective_days):
        day_info = daily_pomodoros[day_idx]
        d_str = day_info["date"]
        p_count = day_info["pomodoros"]
        
        for pomo_idx in range(1, p_count + 1):
            if not available_subjects:
                break
            
            available_subjects.sort(key=lambda x: x["remaining_pomodoros"], reverse=True)
            chosen_sp = None
            
            if available_subjects[0]["name"] == last_subject_name and consecutive_count >= 2:
                if len(available_subjects) > 1:
                    chosen_sp = available_subjects[1]
                else:
                    chosen_sp = available_subjects[0]
            else:
                chosen_sp = available_subjects[0]
            
            progress_val = chosen_sp["progress_per_pomo"]
            if progress_val.is_integer():
                progress_str = f"{int(progress_val)} {chosen_sp['unit']}"
            else:
                progress_str = f"{progress_val:.1f} {chosen_sp['unit']}"

            schedule.append({
                "date": d_str,
                "第幾天": f"Day {day_idx + 1}",
                "屬性": "學習日",
                "番茄鐘節次": f"第 {pomo_idx} 節",
                "科目": chosen_sp["name"],
                "目標進度": progress_str
            })

            chosen_sp["remaining_pomodoros"] -= 1
            if chosen_sp["remaining_pomodoros"] <= 0:
                available_subjects.remove(chosen_sp)
            
            if chosen_sp["name"] == last_subject_name:
                consecutive_count += 1
            else:
                last_subject_name = chosen_sp["name"]
                consecutive_count = 1

    # 安排緩衝/總複習日
    for day_idx in range(effective_days, total_days):
        day_info = daily_pomodoros[day_idx]
        d_str = day_info["date"]
        p_count = day_info["pomodoros"]
        
        for pomo_idx in range(1, p_count + 1):
            schedule.append({
                "date": d_str,
                "第幾天": f"Day {day_idx + 1}",
                "屬性": "緩衝/總複習日",
                "番茄鐘節次": f"第 {pomo_idx} 節",
                "科目": "總複習 (自由安排)",
                "目標進度": "0 單位 (僅複習)"
            })

    return schedule
