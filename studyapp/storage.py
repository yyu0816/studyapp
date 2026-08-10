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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

def is_alphanumeric(text: str) -> bool:
    """Check if text contains ONLY English letters and numbers."""
    return bool(re.match(r'^[a-zA-Z0-9]+$', text))

def is_valid_email(email: str) -> bool:
    """Check if email is a valid email format."""
    email = email.strip().lower()
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def is_valid_gmail(email: str) -> bool:
    """Check if email is a valid Gmail address (@gmail.com)."""
    email = email.strip().lower()
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email))

def generate_verification_code() -> str:
    """Generate a random 6-digit verification code string."""
    return f"{random.randint(100000, 999999)}"

def send_verification_email(to_email: str, code: str, purpose: str = "帳號身分驗證") -> tuple[bool, str]:
    """
    Sends a 6-digit verification code to the given email address via SMTP.
    Strict Security: The verification code is NEVER revealed in return messages.
    """
    to_email = to_email.strip().lower()
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = None
    smtp_password = None
    
    try:
        import streamlit as st
        secrets = getattr(st, "secrets", {})
        if "smtp" in secrets:
            smtp_server = secrets["smtp"].get("server", "smtp.gmail.com")
            smtp_port = int(secrets["smtp"].get("port", 587))
            smtp_user = secrets["smtp"].get("user")
            smtp_password = secrets["smtp"].get("password")
    except Exception:
        pass
        
    if not smtp_user or not smtp_password:
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_password = os.environ.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        return False, "❌ 發信失敗：系統伺服器尚未配置發信 Gmail 與應用程式密碼 (SMTP)。請在 Streamlit Secrets 設定 [smtp] 資訊以啟用真實郵件發送功能。"

    subject = f"【讀書計畫安排助手】您的{purpose} 6 碼驗證碼"
    body = f"""您好！

您正在使用「讀書計畫安排助手」進行【{purpose}】。

您的 6 碼身分驗證碼為：
==============================
       {code}
==============================

請在系統網頁中輸入此驗證碼以完成身分驗證。
（驗證碼有效期限為本次操作期間，若非您本人操作，請忽略此信件）

— 讀書計畫安排助手 系統通知
"""

    try:
        msg = MIMEMultipart()
        msg['From'] = f"讀書計畫安排助手 <{smtp_user}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=12)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=12)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
        return True, f"✅ 驗證信已成功發送至您的 Gmail ({to_email})，請至收件匣（含垃圾郵件匣）收取 6 碼驗證碼！"
    except Exception as e:
        return False, f"❌ 郵件發送失敗（錯誤：{str(e)}），請確認發信信箱權限、應用程式密碼或網路連線。"

def register_user(username: str, password: str, email: str = "") -> tuple[bool, str]:
    """Register a new user with an alphanumeric password and bound Gmail."""
    username = username.strip()
    email = email.strip().lower()
    if not username:
        return False, "使用者名稱不能為空"
    if not is_alphanumeric(password):
        return False, "密碼僅限使用英文字母 (A-Z, a-z) 與數字 (0-9)"
    if not email:
        return False, "請輸入綁定的 Gmail 帳號"
    if not is_valid_email(email):
        return False, "Gmail 格式不正確 (例如：example@gmail.com)"
        
    users = load_all_users()
    if username in users:
        return False, f"帳號「{username}」已被註冊佔用"
        
    users[username] = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password)
    }
    save_all_users(users)
    return True, "註冊成功"

def find_usernames_by_email(email: str) -> list[str]:
    """Find all usernames associated with a bound Gmail address."""
    email = email.strip().lower()
    if not email:
        return []
    users = load_all_users()
    matched = []
    for uname, udata in users.items():
        if udata.get("email", "").strip().lower() == email:
            matched.append(uname)
    return matched

def reset_user_password_with_email(username: str, email: str, new_password: str) -> tuple[bool, str]:
    """Verify Gmail binding and reset password for a user."""
    username = username.strip()
    email = email.strip().lower()
    if not username:
        return False, "請輸入帳號名稱"
    if not email:
        return False, "請輸入綁定的 Gmail"
    if not is_alphanumeric(new_password):
        return False, "新密碼僅限使用英文字母 (A-Z, a-z) 與數字 (0-9)"
        
    users = load_all_users()
    if username not in users:
        return False, f"找不到帳號「{username}」"
        
    user_info = users[username]
    bound_email = user_info.get("email", "").strip().lower()
    if not bound_email:
        return False, f"帳號「{username}」未綁定 Gmail，無法以此方式驗證"
    if bound_email != email:
        return False, "輸入的 Gmail 與該帳號綁定的 Gmail 不一致！"
        
    user_info["password_hash"] = hash_password(new_password)
    users[username] = user_info
    save_all_users(users)
    return True, "密碼重設成功！請使用新密碼登入。"

def verify_user_credentials(username: str, password: str) -> tuple[bool, str]:
    """Verify username and password for existing users. STRICTLY FORBIDS auto-creating new users on login."""
    username = username.strip()
    if not username:
        return False, "請輸入帳號名稱"
    if not password:
        return False, "請輸入密碼"
        
    users = load_all_users()
    if username not in users:
        return False, f"帳號「{username}」尚未註冊！請切換至「註冊新帳號」頁籤進行註冊。"
        
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

