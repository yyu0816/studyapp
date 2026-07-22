import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

def generate_daily_schedule(plan: dict) -> List[Dict[str, Any]]:
    start_date_str = plan.get("start_date")
    end_date_str = plan.get("end_date")
    
    if not start_date_str or not end_date_str:
        return []
        
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except:
        return []
        
    if end_date < start_date:
        return []

    total_days = (end_date - start_date).days + 1
    
    # 1. Calculate available slots per day
    daily_sessions = {}
    total_sessions = 0
    current_date = start_date
    for _ in range(total_days):
        # We assume get_daily_free_slots is defined in the file
        slots = get_daily_free_slots(current_date, plan)
        s = len(slots)
        daily_sessions[current_date] = {"sessions": s, "slots": slots, "scheduled": []}
        total_sessions += s
        current_date += timedelta(days=1)
        
    if total_sessions == 0:
        return []

    subjects_data = plan.get("subjects", [])
    if not subjects_data:
        return []
        
    # Calculate effective_end_date for global buffer
    effective_days = math.floor(total_days * 0.8)
    effective_end_date = start_date + timedelta(days=max(0, effective_days - 1))
    
    # 2. Prepare subjects and their target dates
    subject_schedules = []
    
    for subject in subjects_data:
        subj_name = subject.get("name", "未命名科目")
        materials = subject.get("materials", [])
        
        # Determine Exam Date
        exam_date_str = subject.get("exam_date")
        if exam_date_str:
            try:
                exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
            except:
                exam_date = end_date
        else:
            exam_date = end_date
            
        # Determine target dates
        week_map = {"週一":0, "週二":1, "週三":2, "週四":3, "週五":4, "週六":5, "週日":6}
        prefs_raw = subject.get("weekdays", [])
        prefs_idx = [week_map[p] for p in prefs_raw if p in week_map]
        if len(prefs_idx) == 1:
            added_idx = (prefs_idx[0] + 3) % 7
            prefs_idx.append(added_idx)
            
        target_dates = set()
        days_since_last_scheduled = 0
        curr_d = exam_date - timedelta(days=1)
        
        while curr_d >= start_date:
            if curr_d > end_date:
                curr_d -= timedelta(days=1)
                continue
                
            days_to_exam = (exam_date - curr_d).days
            should_schedule = False
            
            if days_to_exam <= 7:
                if days_since_last_scheduled >= 2 or len(target_dates) == 0:
                    should_schedule = True
            else:
                if curr_d <= effective_end_date:
                    if prefs_idx:
                        if curr_d.weekday() in prefs_idx:
                            should_schedule = True
                    else:
                        if days_since_last_scheduled >= 2:
                            should_schedule = True
                            
            if should_schedule:
                target_dates.add(curr_d)
                days_since_last_scheduled = 0
            else:
                days_since_last_scheduled += 1
                
            curr_d -= timedelta(days=1)
            
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
                    "target_dates": target_dates,
                    "remaining_qty": qty,
                    "assigned_count": 0
                })

    num_materials = len(subject_schedules)
    if num_materials == 0:
        return []
        
    # 3. Determine how many sessions each material gets based on TOTAL free time
    base_session = total_sessions // num_materials
    remainder = total_sessions % num_materials
    for i, sp in enumerate(subject_schedules):
        sp["remaining_sessions"] = base_session + (1 if i < remainder else 0)
        sp["total_allocated"] = sp["remaining_sessions"]

    # 4. Score-based Greedy Slot Allocator
    # We iterate day by day, slot by slot
    curr_d = start_date
    last_scheduled_subject = None
    
    while curr_d <= end_date:
        d_info = daily_sessions.get(curr_d)
        if not d_info or d_info["sessions"] == 0:
            curr_d += timedelta(days=1)
            continue
            
        # We have slots today
        scheduled_today = []
        for _ in range(d_info["sessions"]):
            best_sp = None
            best_score = -999999
            
            for sp in subject_schedules:
                if sp["remaining_sessions"] <= 0:
                    continue
                    
                # Base score: more remaining sessions = higher priority
                score = sp["remaining_sessions"] * 10
                
                # Target date bonus
                if curr_d in sp["target_dates"]:
                    score += 1000
                    
                # Penalty for repeating the same subject on the same day
                count_today = scheduled_today.count(sp["subject"])
                score -= 2000 * count_today
                
                # Minor penalty for back-to-back same subject
                if sp["subject"] == last_scheduled_subject:
                    score -= 50
                    
                if score > best_score:
                    best_score = score
                    best_sp = sp
                    
            if best_sp:
                d_info["scheduled"].append(best_sp)
                scheduled_today.append(best_sp["subject"])
                best_sp["remaining_sessions"] -= 1
                best_sp["assigned_count"] += 1
                last_scheduled_subject = best_sp["subject"]
            else:
                break # No subjects have remaining sessions
                
        curr_d += timedelta(days=1)

    # 5. Calculate progress array for each material
    for sp in subject_schedules:
        qty = sp["remaining_qty"]
        allocated = sp["assigned_count"]
        if allocated > 0:
            base_prog = qty // allocated
            rem_prog = qty % allocated
            sp["progress_array"] = [base_prog + 1 if i < rem_prog else base_prog for i in range(allocated)]
        else:
            sp["progress_array"] = []

    # 6. Generate final output schedule
    schedule = []
    curr_d = start_date
    day_idx = 0
    while curr_d <= end_date:
        d_info = daily_sessions.get(curr_d)
        if not d_info:
            curr_d += timedelta(days=1)
            continue
            
        s_count = d_info["sessions"]
        slots = d_info["slots"]
        scheduled_items = d_info["scheduled"]
        
        day_events = []
        for session_idx in range(1, s_count + 1):
            if session_idx - 1 < len(scheduled_items):
                sp = scheduled_items[session_idx - 1]
                
                if sp["progress_array"]:
                    progress_val = sp["progress_array"].pop(0)
                else:
                    progress_val = 0
                    
                if progress_val == int(progress_val):
                    progress_str = f"{int(progress_val)} {sp['unit']}"
                else:
                    progress_str = f"{progress_val:.1f} {sp['unit']}"
                    
                slot = slots[session_idx - 1]
                t_s_str = f"{slot[0]//60:02d}:{slot[0]%60:02d}"
                t_e_str = f"{slot[1]//60:02d}:{slot[1]%60:02d}"
                
                day_events.append({
                    "subject": sp["subject"],
                    "color": sp["color"],
                    "material": sp["material"],
                    "progress": progress_str,
                    "time": f"{t_s_str}–{t_e_str}"
                })
            else:
                slot = slots[session_idx - 1]
                t_s_str = f"{slot[0]//60:02d}:{slot[0]%60:02d}"
                t_e_str = f"{slot[1]//60:02d}:{slot[1]%60:02d}"
                
                day_events.append({
                    "subject": "總複習 (自由安排)",
                    "color": "#9e9e9e",
                    "material": "緩衝時段",
                    "progress": "自由安排或休息",
                    "time": f"{t_s_str}–{t_e_str}"
                })
                
        weekday_str = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][curr_d.weekday()]
        
        schedule.append({
            "day_index": day_idx + 1,
            "date": curr_d.strftime("%Y-%m-%d"),
            "weekday": weekday_str,
            "events": day_events
        })
        day_idx += 1
        curr_d += timedelta(days=1)
        
    return schedule
