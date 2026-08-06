import json
import os
import uuid
import hashlib
import re

def _get_data_file():
    test_path = os.path.join(os.getcwd(), "plans.json")
    try:
        with open(test_path, "a") as f:
            pass
        return test_path
    except (PermissionError, OSError):
        return "/tmp/plans.json"

def _get_users_file():
    test_path = os.path.join(os.getcwd(), "users.json")
    try:
        with open(test_path, "a") as f:
            pass
        return test_path
    except (PermissionError, OSError):
        return "/tmp/users.json"

DATA_FILE = _get_data_file()
USERS_FILE = _get_users_file()

def load_all_users() -> dict[str, dict]:
    """Load all registered user accounts from JSON."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_all_users(users_dict: dict[str, dict]) -> None:
    """Save user credentials to JSON."""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def is_alphanumeric(text: str) -> bool:
    """Check if text contains ONLY English letters and numbers."""
    return bool(re.match(r'^[a-zA-Z0-9]+$', text))

def register_user(username: str, password: str) -> tuple[bool, str]:
    """Register a new user with an alphanumeric password."""
    username = username.strip()
    if not username:
        return False, "使用者名稱不能為空"
    if not is_alphanumeric(password):
        return False, "密碼僅限使用英文字母 (A-Z, a-z) 與數字 (0-9)"
        
    users = load_all_users()
    if username in users:
        return False, f"帳號「{username}」已被註冊使用"
        
    users[username] = {
        "username": username,
        "password_hash": hash_password(password)
    }
    save_all_users(users)
    return True, "註冊成功"

def verify_user_credentials(username: str, password: str) -> tuple[bool, str]:
    """Verify username and password."""
    username = username.strip()
    if not username:
        return False, "請輸入帳號"
    if not password:
        return False, "請輸入密碼"
        
    users = load_all_users()
    if username not in users:
        # Check if legacy user exists in plans
        plans = load_all_plans()
        legacy_exists = any(pdata.get("owner_name") == username for pdata in plans.values())
        if legacy_exists:
            if not is_alphanumeric(password):
                return False, "密碼僅限使用英文字母 (A-Z, a-z) 與數字 (0-9)"
            register_user(username, password)
            return True, "舊帳號密碼設定完成"
        return False, "帳號不存在，請先註冊新帳號"
        
    user_info = users[username]
    if user_info.get("password_hash") == hash_password(password):
        return True, "驗證成功"
    else:
        return False, "密碼不正確，請重新輸入"

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

def create_new_plan(name="未命名計畫", goal="", owner_name=""):
    """Create a new empty plan and return its ID."""
    plan_id = str(uuid.uuid4())
    new_plan = {
        "id": plan_id,
        "name": name,
        "goal": goal,
        "owner_name": owner_name,
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
        "enabled_features": {
            "page_dashboard": True, "dash_study_progress": True, "dash_weekly_chart": True, "dash_mood_pacing": True,
            "page_monthly": True, "monthly_calendar": True, "monthly_schedule": True, "monthly_events": True,
            "page_daily": True, "daily_timeline": True, "daily_checklist": True, "daily_mood": True, "daily_timeloss": True,
            "page_timer": True, "timer_clock": True, "timer_history": True
        },
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
        "plan_name", "plan_goal", "owner_name", "subjects", "daily_override_events", "daily_modified_fixed", "plan",
        "fixed_events", "specific_events", "enabled_pages", "enabled_features", "custom_theme"
    ]
    for key in keys_to_save:
        if key in st.session_state:
            plan[key] = st.session_state[key]
            
    if "plan_name" in st.session_state and st.session_state["plan_name"]:
        plan["name"] = st.session_state["plan_name"]
    if "plan_goal" in st.session_state:
        plan["goal"] = st.session_state["plan_goal"]
            
    save_plan(plan_id, plan)

