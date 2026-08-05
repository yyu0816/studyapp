import json
import os
import uuid

# Streamlit Cloud 的 app 目錄是唯讀的，需改寫至 /tmp
# 本機開發時 /tmp 也可用，但為了方便偵錯，本機用當前目錄
def _get_data_file():
    # 若當前目錄可寫（本機），就用當前目錄
    test_path = os.path.join(os.getcwd(), "plans.json")
    try:
        # 試著測試寫入權限
        with open(test_path, "a") as f:
            pass
        return test_path
    except (PermissionError, OSError):
        # Streamlit Cloud: 使用 /tmp 目錄
        return "/tmp/plans.json"

DATA_FILE = _get_data_file()

def load_all_plans():
    """Load all plans from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading plans: {e}")
        return {}

def save_all_plans(plans_dict):
    """Save all plans to the JSON file."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(plans_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving plans: {e}")

def load_plan(plan_id):
    """Load a specific plan."""
    plans = load_all_plans()
    return plans.get(plan_id)

def save_plan(plan_id, data):
    """Save a specific plan."""
    plans = load_all_plans()
    plans[plan_id] = data
    save_all_plans(plans)

def create_new_plan(name="未命名計畫", goal=""):
    """Create a new empty plan and return its ID."""
    plan_id = str(uuid.uuid4())
    new_plan = {
        "id": plan_id,
        "name": name,
        "goal": goal,
        "app_state": {
            "plan": None,
            "daily_log": None,
            "monthly_plan": None
        },
        "daily_task_checks": {},
        "timer_records": {},
        "mood_records": {},
        "plan_name": name,
        "plan_goal": goal,
        "subjects": [{"name": "", "color": "#4f84ff", "materials": [{"name": "", "type": "課本", "quantity": 1}], "weekdays": []}],
        "fixed_events": [{"title": "", "weekdays": [], "start": "", "end": "", "emoji": "📚", "color": "#4f84ff", "display_color": "#4f84ff", "show_on_calendar": True, "custom_color": False}],
        "specific_events": [],
        "daily_override_events": {},
        "daily_modified_fixed": {},
        "enabled_pages": {"dashboard": True, "月計畫": True, "每日打卡與微調": True, "計時器": True},
        "custom_theme": {"bg_color": "#ffffff", "button_color": "#4f84ff", "navbar_bg_color": "#f8f9fa"}
    }
    save_plan(plan_id, new_plan)
    return plan_id

def delete_plan(plan_id):
    plans = load_all_plans()
    if plan_id in plans:
        del plans[plan_id]
        save_all_plans(plans)

def save_current_state():
    import streamlit as st
    plan_id = st.session_state.get("current_plan_id")
    if not plan_id:
        return
        
    plans = load_all_plans()
    if plan_id not in plans:
        return
        
    plan = plans[plan_id]
    
    # Update plan data from session_state
    keys_to_save = [
        "app_state", "daily_task_checks", "timer_records", "mood_records",
        "plan_name", "plan_goal", "subjects", "daily_override_events", "daily_modified_fixed", "plan",
        "fixed_events", "specific_events", "enabled_pages", "custom_theme"
    ]
    for key in keys_to_save:
        if key in st.session_state:
            plan[key] = st.session_state[key]
            
    if "plan_name" in st.session_state and st.session_state["plan_name"]:
        plan["name"] = st.session_state["plan_name"]
    if "plan_goal" in st.session_state:
        plan["goal"] = st.session_state["plan_goal"]
            
    save_plan(plan_id, plan)

