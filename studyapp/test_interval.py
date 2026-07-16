from datetime import datetime, date, timedelta

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
    t = datetime.strptime(time_str, "%H:%M").time()
    return t.hour * 60 + t.minute

def calculate_daily_available_hours(current_date, plan):
    is_weekend = current_date.weekday() >= 5
    wake_key = "weekend_wake" if is_weekend else "weekday_wake"
    sleep_key = "weekend_sleep" if is_weekend else "weekday_sleep"
    
    wake_time = plan.get(wake_key, "07:00")
    sleep_time = plan.get(sleep_key, "23:30")
    
    wake_m = get_minutes(wake_time)
    sleep_m = get_minutes(sleep_time)
    
    blocking_intervals = []
    
    # 1. Sleep
    if sleep_m <= wake_m: # e.g. 00:30 to 08:30
        blocking_intervals.append((0, wake_m))
        if sleep_m > 0:
            blocking_intervals.append((sleep_m, 1440))
    else: # e.g. 23:30 to 07:00 next day
        blocking_intervals.append((0, wake_m))
        blocking_intervals.append((sleep_m, 1440))
        
    # 2. Routines (Meals, Bath)
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
    return free_minutes / 60.0

if __name__ == "__main__":
    plan = {
        "weekday_wake": "07:00",
        "weekday_sleep": "23:00",
        "routines": {
            "lunch": {"start": "12:00", "end": "13:00"}
        },
        "fixed_events": [
            {"weekdays": ["週一"], "start": "12:30", "end": "13:30", "concurrent_with_study": True}
        ]
    }
    # Blocking: 0-420, 1380-1440, 720-780 (Lunch)
    # Parallel: 750-810
    # Overlap between Lunch (720-780) and Parallel (750-810) is 750-780 (30 mins)
    # Blocked by lunch = 60 - 30 = 30 mins
    # Total blocked: 420 + 60 + 30 = 510 mins
    # Free = 1440 - 510 = 930 mins = 15.5 hours
    print(calculate_daily_available_hours(date(2023, 10, 2), plan))
