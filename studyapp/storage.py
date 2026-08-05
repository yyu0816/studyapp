import json
import os
import uuid

DATA_FILE = "plans.json"

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
        "daily_modified_fixed": {}
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
        "fixed_events", "specific_events"
    ]
    for key in keys_to_save:
        if key in st.session_state:
            plan[key] = st.session_state[key]
            
    save_plan(plan_id, plan)

