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

def calculate_daily_available_sessions(current_date, plan):
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
        blocking_intervals.append((sleep_m, wake_m))
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
    
    for ev in fixed_events:
        if weekday_str in ev.get("weekdays", []):
            sm = get_minutes(ev.get("start", "00:00"))
            em = get_minutes(ev.get("end", "00:00"))
            if sm < em:
                if not ev.get("concurrent_with_study", False):
                    blocking_intervals.append((sm, em))
                    
    blocking_intervals = merge_intervals(blocking_intervals)
    
    # Calculate exact free sessions matching get_daily_free_slots
    total_sessions = 0
    current_m = 0
    for b_start, b_end in blocking_intervals:
        if b_start > current_m:
            free_duration = b_start - current_m
            total_sessions += (free_duration + 10) // 70
        current_m = max(current_m, b_end)
        
    if 1440 > current_m:
        free_duration = 1440 - current_m
        total_sessions += (free_duration + 10) // 70
        
    return float(total_sessions)

def get_daily_free_slots(current_date, plan) -> list[tuple[int, int]]:
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
        blocking_intervals.append((sleep_m, wake_m))
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
    
    for ev in fixed_events:
        if weekday_str in ev.get("weekdays", []):
            sm = get_minutes(ev.get("start", "00:00"))
            em = get_minutes(ev.get("end", "00:00"))
            if sm < em:
                if not ev.get("concurrent_with_study", False):
                    blocking_intervals.append((sm, em))
                    
    blocking_intervals = merge_intervals(blocking_intervals)
    
    # Extract 60-minute slots with 10-minute breaks
    slots = []
    current_m = 0
    for b_start, b_end in blocking_intervals:
        if b_start > current_m:
            free_duration = b_start - current_m
            num_slots = (free_duration + 10) // 70
            for i in range(num_slots):
                slots.append((current_m + i * 70, current_m + i * 70 + 60))
        current_m = max(current_m, b_end)
        
    if 1440 > current_m:
        free_duration = 1440 - current_m
        num_slots = (free_duration + 10) // 70
        for i in range(num_slots):
            slots.append((current_m + i * 70, current_m + i * 70 + 60))
            
    return slots

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
    
    # 1. 取得每天可用 Session
    daily_sessions = {}
    total_sessions = 0
    current_date = start_date
    for _ in range(total_days):
        slots = get_daily_free_slots(current_date, plan)
        s = len(slots)
        daily_sessions[current_date] = {"sessions": s, "slots": slots, "scheduled": []}
        total_sessions += s
        current_date += timedelta(days=1)
        
    if total_sessions == 0:
        return []

    UNIT_MAP = {"課本": "頁", "教材": "頁", "筆記": "頁", "練習題": "回", "模擬考": "回", "教學影片": "小時"}
    week_map = {"星期一": 0, "星期二": 1, "星期三": 2, "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6,
                "週一": 0, "週二": 1, "週三": 2, "週四": 3, "週五": 4, "週六": 5, "週日": 6}

    # 計算有效天數與緩衝天數 (八二法則)
    effective_days = math.floor(total_days * 0.8)
    effective_end_date = start_date + timedelta(days=max(0, effective_days - 1))

    # 2. 為每個科目安排日期 (逆向推算)
    subject_schedules = []
    for subject in subjects_data:
        subj_name = subject.get("name", "未命名科目")
        materials = subject.get("materials", [])
        
        exam_date_str = subject.get("exam_date")
        if exam_date_str:
            try:
                exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
            except:
                exam_date = end_date
        else:
            exam_date = end_date
            
        prefs_raw = subject.get("weekdays", [])
        prefs_idx = [week_map[p] for p in prefs_raw if p in week_map]
        
        # Rule C: 如果只有一天偏好，自動增加一天 (相隔 3 天)
        if len(prefs_idx) == 1:
            added_idx = (prefs_idx[0] + 3) % 7
            prefs_idx.append(added_idx)
            
        target_dates = []
        days_since_last_scheduled = 0
        
        curr_d = exam_date - timedelta(days=1)
        while curr_d >= start_date:
            if curr_d > end_date:
                curr_d -= timedelta(days=1)
                continue
                
            days_to_exam = (exam_date - curr_d).days
            should_schedule = False
            
            if days_to_exam <= 7:
                # 考前一週：每2天排一次 (衝刺期不受緩衝日限制)
                if days_since_last_scheduled >= 2 or len(target_dates) == 0:
                    should_schedule = True
            else:
                # 長期備戰期：必須在 effective_end_date 之前才排程，保留後面的全域緩衝日
                if curr_d <= effective_end_date:
                    if prefs_idx:
                        # 依據偏好
                        if curr_d.weekday() in prefs_idx:
                            should_schedule = True
                    else:
                        # 無偏好：每2天排一次
                        if days_since_last_scheduled >= 2:
                            should_schedule = True
                        
            if should_schedule:
                target_dates.append(curr_d)
                days_since_last_scheduled = 0
            else:
                days_since_last_scheduled += 1
                
            curr_d -= timedelta(days=1)
            
        target_dates.reverse() # 照時間順序
        
        # 處理教材進度
        for mat in materials:
            mat_type = mat.get("type", "其他")
            mat_name = mat.get("name", "未命名教材")
            qty = int(mat.get("quantity", 0))
            unit = UNIT_MAP.get(mat_type, "項")
            if qty > 0:
                subject_schedules.append({
                    "subject": subj_name,
                    "color": subject.get("color", "#4f84ff"),
                    "material": mat_name,
                    "unit": unit,
                    "target_dates": list(target_dates),
                    "remaining_qty": qty,
                    "assigned_count": 0
                })
                
    # 3. 裝箱排程 (Bin Packing 防碰撞機制)
    schedule = []
    tasks_to_schedule = []
    for sp in subject_schedules:
        for t_date in sp["target_dates"]:
            tasks_to_schedule.append({
                "preferred_date": t_date,
                "sp": sp
            })
            
    tasks_to_schedule.sort(key=lambda x: x["preferred_date"])
    
    for task in tasks_to_schedule:
        pref_date = task["preferred_date"]
        sp = task["sp"]
        assigned_date = None
        
        # 第一階段：強迫分攤，該日不可已有此科目
        check_date = pref_date
        while check_date >= start_date:
            d_info = daily_sessions.get(check_date)
            if d_info and len(d_info["scheduled"]) < d_info["sessions"] and sp not in d_info["scheduled"]:
                assigned_date = check_date
                break
            check_date -= timedelta(days=1)
            
        if not assigned_date:
            check_date = pref_date + timedelta(days=1)
            while check_date <= end_date:
                d_info = daily_sessions.get(check_date)
                if d_info and len(d_info["scheduled"]) < d_info["sessions"] and sp not in d_info["scheduled"]:
                    assigned_date = check_date
                    break
                check_date += timedelta(days=1)
                
        # 第二階段：如果真的所有日子都擠滿了，才允許同一天疊加
        if not assigned_date:
            check_date = pref_date
            while check_date >= start_date:
                d_info = daily_sessions.get(check_date)
                if d_info and len(d_info["scheduled"]) < d_info["sessions"]:
                    assigned_date = check_date
                    break
                check_date -= timedelta(days=1)
                
            if not assigned_date:
                check_date = pref_date + timedelta(days=1)
                while check_date <= end_date:
                    d_info = daily_sessions.get(check_date)
                    if d_info and len(d_info["scheduled"]) < d_info["sessions"]:
                        assigned_date = check_date
                        break
                    check_date += timedelta(days=1)
                    
        if assigned_date:
            daily_sessions[assigned_date]["scheduled"].append(sp)
            sp["assigned_count"] += 1
            
    # 計算每個科目真正被分配到的陣列 (確保所有量都被完美分攤到獲取的天數上)
    for sp in subject_schedules:
        qty = sp["remaining_qty"]
        allocated = sp["assigned_count"]
        if allocated > 0:
            base_prog = qty // allocated
            rem_prog = qty % allocated
            sp["progress_array"] = [base_prog + 1 if i < rem_prog else base_prog for i in range(allocated)]
        else:
            sp["progress_array"] = []

    # 4. 產生最終排程
    curr_d = start_date
    day_idx = 0
    while curr_d <= end_date:
        d_info = daily_sessions.get(curr_d)
        if not d_info:
            curr_d += timedelta(days=1)
            continue
            
        d_str = curr_d.strftime("%Y-%m-%d")
        scheduled_items = d_info["scheduled"]
        s_count = d_info["sessions"]
        
        for session_idx in range(1, s_count + 1):
            slot = d_info["slots"][session_idx - 1] if session_idx - 1 < len(d_info["slots"]) else (0, 60)
            start_str = f"{slot[0]//60:02d}:{slot[0]%60:02d}"
            end_str = f"{slot[1]//60:02d}:{slot[1]%60:02d}"
            
            if session_idx - 1 < len(scheduled_items):
                sp = scheduled_items[session_idx - 1]
                
                if sp["progress_array"]:
                    progress_val = sp["progress_array"].pop(0)
                else:
                    progress_val = 0
                
                progress_str = f"{progress_val} {sp['unit']}"
                sp["remaining_qty"] -= progress_val

                schedule.append({
                    "date": d_str,
                    "第幾天": f"Day {day_idx + 1}",
                    "屬性": "學習日",
                    "學習區塊": f"第 {session_idx} 節 (1小時)",
                    "start_time": start_str,
                    "end_time": end_str,
                    "科目": sp["subject"],
                    "color": sp["color"],
                    "教材": sp["material"],
                    "目標進度": progress_str
                })
            else:
                schedule.append({
                    "date": d_str,
                    "第幾天": f"Day {day_idx + 1}",
                    "屬性": "緩衝/總複習日",
                    "學習區塊": f"第 {session_idx} 節 (1小時)",
                    "start_time": start_str,
                    "end_time": end_str,
                    "科目": "總複習 (自由安排)",
                    "教材": "-",
                    "目標進度": "0 單位 (僅複習)"
                })
                
        day_idx += 1
        curr_d += timedelta(days=1)

    return schedule
