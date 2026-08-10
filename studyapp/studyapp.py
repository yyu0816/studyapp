from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
import streamlit as st
import dashboard

import importlib
import storage
try:
    importlib.reload(storage)
except Exception:
    pass

from storage import (
    generate_verification_code,
    send_verification_email,
    find_usernames_by_email,
    reset_user_password_with_email,
    verify_user_credentials,
    register_user,
    is_alphanumeric,
    is_valid_email
)

try:
    import click
    original_secho = click.secho
    def safe_secho(*args, **kwargs):
        try:
            original_secho(*args, **kwargs)
        except UnicodeEncodeError:
            pass
    click.secho = safe_secho
except Exception:
    pass

st.set_page_config(page_title="讀書計畫安排助手", page_icon="📚", layout="wide")

# 確保基礎 state 準備好 (支援從 URL 參數恢復使用者與計畫狀態)
if "user_name" not in st.session_state and st.query_params.get("user"):
    st.session_state["user_name"] = st.query_params.get("user")

if "current_plan_id" not in st.session_state:
    st.session_state["current_plan_id"] = st.query_params.get("plan_id") or None
elif not st.session_state["current_plan_id"] and st.query_params.get("plan_id"):
    st.session_state["current_plan_id"] = st.query_params.get("plan_id")
    
# 如果在 app 內（已選定計畫），但 app_state 遺失，嘗試補回
if st.session_state["current_plan_id"] and "app_state" not in st.session_state:
    plan_data = storage.load_plan(st.session_state["current_plan_id"])
    if plan_data:
        st.session_state["app_state"] = plan_data.get("app_state", {"plan": None, "daily_log": None, "monthly_plan": None})
    else:
        st.session_state["app_state"] = {"plan": None, "daily_log": None, "monthly_plan": None}
elif "app_state" not in st.session_state:
    st.session_state["app_state"] = {"plan": None, "daily_log": None, "monthly_plan": None}

app_state = st.session_state.get("app_state", {})

# 3. 再來才是 import 你的頁面函式
from monthlyplan import render_monthly_plan_page
from dailycheck import render_daily_checkin_page, get_adjustment_message
from datetime import date, datetime, timedelta
from timeline_utils import render_timeline
from timer import render_timer_page
from settings import render_settings_page

MATERIAL_TYPES = ["課本", "教材", "練習題", "模擬考", "教學影片", "筆記", "其他"]
MATERIAL_UNIT_MAP = {
    "課本": "頁",
    "教材": "頁",
    "筆記": "頁",
    "練習題": "回",
    "模擬考": "回",
    "教學影片": "小時",
}
WEEKDAY_OPTIONS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
COLOR_OPTIONS = [
    {"name": "🔵 藍色",  "value": "#4f84ff"},
    {"name": "🟣 紫色",  "value": "#7b5cff"},
    {"name": "🔴 紅色",  "value": "#ff6b6b"},
    {"name": "🟢 綠色",  "value": "#2ecc71"},
    {"name": "🟠 橙色",  "value": "#ff9f43"},
    {"name": "🟡 黃色",  "value": "#f9ca24"},
    {"name": "⚪ 灰色",  "value": "#636e72"},
    {"name": "🤍 深紅",  "value": "#b71540"},
]
EMOJI_OPTIONS = [
    "📚", "📝", "🕒", "🏫", "🎯", "💡", "☕", "🛌", "🏃", "🎒",
    "😀", "😎", "🤔", "😴", "💪", "🙌", "✨", "🔥", "💯", "🎉",
    "📖", "✏️", "📐", "🔬", "💻", "🧠", "🗓️", "✅", "❌", "📌",
    "🍎", "🍔", "🥤", "🎵", "🎧", "🎨", "⚽", "🏀", "🎮", "🎬",
    "🚗", "🚌", "🚆", "✈️", "🏠", "🏢", "🏥", "🏦", "🛒", "🌲",
    "🏐", "🚿", "🏊", "🤸", "⚾", "🎾", "🧘", "🍜", "🧃", "📺",
    "🧖", "🏄", "😜", "🥳", "👍", "🧹", "🛕", "📦", "🔓", "⏰",
    "🌿", "🐶", "🐱", "⛰️", "🌊", "🔭", "🧪", "📱", "😉", "🥱",
]


def parse_subject_entries(form_data: Any) -> list[dict[str, Any]]:
    if isinstance(form_data, dict) and isinstance(form_data.get("subjects"), list):
        subjects: list[dict[str, Any]] = []
        for subject in form_data["subjects"]:
            if not isinstance(subject, dict):
                continue
            materials: list[dict[str, Any]] = []
            for material in subject.get("materials", []) or []:
                if not isinstance(material, dict):
                    continue
                name = str(material.get("name", "") or "").strip()
                material_type = str(material.get("type", "課本") or "課本").strip() or "課本"
                quantity = material.get("quantity", material.get("pages", 0))
                try:
                    quantity_value = int(quantity)
                except (TypeError, ValueError):
                    quantity_value = 0
                material_entry = {
                    "name": name,
                    "type": material_type,
                    "quantity": quantity_value if quantity_value > 0 else 0,
                }
                if "pages" in material:
                    material_entry["pages"] = material.get("pages")
                materials.append(material_entry)
            if subject.get("name") or materials:
                subjects.append({
                    "name": str(subject.get("name", "") or "").strip(),
                    "color": str(subject.get("color", "#4f84ff") or "#4f84ff"),
                    "materials": materials,
                    "weekdays": list(subject.get("weekdays", []) or []),
                })
        return subjects

    if hasattr(form_data, "getlist"):
        names = form_data.getlist("subject_name")
        pages = form_data.getlist("pages_required")
        review_video = form_data.getlist("review_video")
        mock_exam = form_data.getlist("mock_exam")
        review_dates = form_data.getlist("review_date")
        mock_dates = form_data.getlist("mock_date")
    else:
        names = form_data.get("subject_name", []) or []
        pages = form_data.get("pages_required", []) or []
        review_video = form_data.get("review_video", []) or []
        mock_exam = form_data.get("mock_exam", []) or []
        review_dates = form_data.get("review_date", []) or []
        mock_dates = form_data.get("mock_date", []) or []

    if not isinstance(names, list):
        names = [names]
    if not isinstance(pages, list):
        pages = [pages]
    if not isinstance(review_video, list):
        review_video = [review_video]
    if not isinstance(mock_exam, list):
        mock_exam = [mock_exam]
    if not isinstance(review_dates, list):
        review_dates = [review_dates]
    if not isinstance(mock_dates, list):
        mock_dates = [mock_dates]

    subjects: list[dict[str, Any]] = []
    for index, name in enumerate(names):
        cleaned_name = str(name).strip()
        if not cleaned_name:
            continue
        page_value = str(pages[index]).strip() if index < len(pages) else ""
        review_value = str(review_video[index]).strip() if index < len(review_video) else ""
        mock_value = str(mock_exam[index]).strip() if index < len(mock_exam) else ""
        review_date_value = str(review_dates[index]).strip() if index < len(review_dates) else ""
        mock_date_value = str(mock_dates[index]).strip() if index < len(mock_dates) else ""
        review_is_true = review_value.lower() in {"on", "true", "1", "yes"}
        mock_is_true = mock_value.lower() in {"on", "true", "1", "yes"}
        subjects.append(
            {
                "name": cleaned_name,
                "materials": [
                    {
                        "name": "頁數",
                        "type": "教材",
                        "quantity": int(page_value) if page_value.isdigit() and int(page_value) > 0 else 0,
                    }
                ],
                "review_video": int(review_value) if review_value.isdigit() and int(review_value) > 0 else (1 if review_is_true else 0),
                "mock_exam": int(mock_value) if mock_value.isdigit() and int(mock_value) > 0 else (1 if mock_is_true else 0),
                "review_date": review_date_value,
                "mock_date": mock_date_value,
            }
        )
    return subjects





def build_plan_summary(plan_data: dict[str, Any], daily_data: dict[str, Any]) -> str:
    subject_lines = "<ul>"
    for item in plan_data.get("subjects", []):
        material_texts = []
        for material in item.get("materials", []):
            unit = get_material_unit(material.get('type', ''))
            material_texts.append(f"{material.get('name') or material.get('type')} {material.get('quantity', 0)} {unit}")
        subject_lines += f"<li>{item.get('name')}：{', '.join(material_texts)}</li>"
    subject_lines += "</ul>"

    schedule_lines = "<ul>"
    for item in plan_data.get("fixed_events", []):
        schedule_lines += f"<li>{item.get('title')}：{', '.join(item.get('weekdays', []))} {item.get('start')} ～ {item.get('end')}（{item.get('display_color', item.get('color', ''))}）</li>"
    schedule_lines += "</ul>"

    return f"""
    <section style="padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.08); margin-bottom: 12px;">
      <h3>初始設定摘要</h3>
      <p><strong>開始日期：</strong> {plan_data.get('start_date', '未填')}</p>
      <p><strong>結束日期：</strong> {plan_data.get('end_date', '未填')}</p>
      <p><strong>每天偏好的科目數量：</strong> {plan_data.get('preferred_subject_count', '未填')}</p>
      <p><strong>科目與教材：</strong></p>
      {subject_lines}
      <p><strong>固定行程：</strong></p>
      {schedule_lines}
      <p><strong>每日作息：</strong> 平日 {plan_data.get('daily_routine', {}).get('weekday_wake', '未填')} 起床，{plan_data.get('daily_routine', {}).get('weekday_sleep', '未填')} 就寢；假日 {plan_data.get('daily_routine', {}).get('weekend_wake', '未填')} 起床，{plan_data.get('daily_routine', {}).get('weekend_sleep', '未填')} 就寢。</p>
    </section>
    <section style="padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.08); margin-bottom: 12px;">
      <h3>今日打卡摘要</h3>
      <p><strong>今日進度：</strong> {daily_data.get('daily_progress', '未填')}</p>
      <p><strong>心情與精力：</strong> {daily_data.get('mood', '未填')} / {daily_data.get('energy', '未填')}</p>
      <p><strong>意外時間損失：</strong> {daily_data.get('time_loss', '未填')} 小時</p>
      <p><strong>節奏回饋：</strong> {daily_data.get('pacing_feedback', '未填')}</p>
      <p><strong>建議：</strong> {daily_data.get('recommendation', '')}</p>
    </section>
    """


def _get_field(form_data: Any, name: str) -> Any:
    if hasattr(form_data, "get"):
        return form_data.get(name, "")
    return ""


def _get_list_field(form_data: Any, name: str) -> list[Any]:
    if hasattr(form_data, "getlist"):
        values = form_data.getlist(name)
    else:
        values = form_data.get(name, []) or []
    if not isinstance(values, list):
        values = [values]
    return values


def _compute_timeframe_days(start_date: str | None, end_date: str | None, fallback: int | None = None) -> int:
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            return max(1, (end - start).days + 1)
        except ValueError:
            pass
    if fallback is not None:
        return max(1, int(fallback))
    return 1


def collect_plan_and_daily_data(form_data: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    event_titles = _get_list_field(form_data, "event_title")
    event_days = _get_list_field(form_data, "event_day")
    event_starts = _get_list_field(form_data, "event_start")
    event_ends = _get_list_field(form_data, "event_end")
    event_colors = _get_list_field(form_data, "event_color")

    if not event_titles and _get_field(form_data, "schedule_day"):
        event_titles = ["固定學習"]
    if not event_days and _get_field(form_data, "schedule_day"):
        event_days = _get_list_field(form_data, "schedule_day")
    if not event_starts and _get_field(form_data, "schedule_start"):
        event_starts = _get_list_field(form_data, "schedule_start")
    if not event_ends and _get_field(form_data, "schedule_end"):
        event_ends = _get_list_field(form_data, "schedule_end")
    if not event_colors:
        event_colors = ["#4f84ff"]

    if isinstance(form_data, dict) and isinstance(form_data.get("fixed_events"), list):
        fixed_events = []
        for event in form_data["fixed_events"]:
            if not isinstance(event, dict):
                continue
            weekdays = event.get("weekdays") or []
            if isinstance(weekdays, str):
                weekdays = [weekdays]
            display_color = event.get("display_color") or event.get("color") or ""
            fixed_events.append(
                {
                    "title": str(event.get("title", "") or ""),
                    "weekdays": list(weekdays),
                    "start": str(event.get("start", "") or ""),
                    "end": str(event.get("end", "") or ""),
                    "emoji": str(event.get("emoji", "📚") or "📚"),
                    "color": str(event.get("color", display_color) or display_color or "#4f84ff"),
                    "display_color": display_color or str(event.get("color", "") or "#4f84ff"),
                    "show_on_calendar": bool(event.get("show_on_calendar", True)),
                    "concurrent_with_study": bool(event.get("concurrent_with_study", False)),
                }
            )
    else:
        fixed_events = [
            {
                "title": event_titles[index] if index < len(event_titles) else "",
                "weekdays": [event_days[index]] if index < len(event_days) else [],
                "start": event_starts[index] if index < len(event_starts) else "",
                "end": event_ends[index] if index < len(event_ends) else "",
                "color": event_colors[index] if index < len(event_colors) else "#4f84ff",
                "display_color": event_colors[index] if index < len(event_colors) else "#4f84ff",
                "show_on_calendar": True,
                "concurrent_with_study": False,
            }
            for index in range(max(len(event_titles), len(event_days), len(event_starts), len(event_ends), len(event_colors)))
        ]
        
    specific_events = []
    if isinstance(form_data, dict) and isinstance(form_data.get("specific_events"), list):
        for event in form_data["specific_events"]:
            if not isinstance(event, dict):
                continue
            display_color = event.get("display_color") or event.get("color") or ""
            specific_events.append(
                {
                    "title": str(event.get("title", "") or ""),
                    "start_date": str(event.get("start_date", "") or ""),
                    "end_date": str(event.get("end_date", "") or ""),
                    "start_time": str(event.get("start_time", "") or ""),
                    "end_time": str(event.get("end_time", "") or ""),
                    "emoji": str(event.get("emoji", "🏖️") or "🏖️"),
                    "color": str(event.get("color", display_color) or display_color or "#ff9f43"),
                    "display_color": display_color or str(event.get("color", "") or "#ff9f43"),
                    "show_on_calendar": bool(event.get("show_on_calendar", True)),
                    "concurrent_with_study": bool(event.get("concurrent_with_study", False)),
                }
            )

    plan_data: dict[str, Any] = {
        "plan_name": _get_field(form_data, "plan_name"),
        "plan_goal": _get_field(form_data, "plan_goal"),
        "timeframe": _get_field(form_data, "timeframe") or _get_field(form_data, "timeframe_days") or "",
        "start_date": str(_get_field(form_data, "start_date") or ""),
        "end_date": str(_get_field(form_data, "end_date") or ""),
        "timeframe_days": _compute_timeframe_days(
            str(_get_field(form_data, "start_date") or ""),
            str(_get_field(form_data, "end_date") or ""),
            int(_get_field(form_data, "timeframe_days") or 0) or None,
        ),
        "preferred_subject_count": int(str(_get_field(form_data, "preferred_subject_count") or "0").strip() or 0),
        "subjects": parse_subject_entries(form_data),
        "fixed_events": fixed_events,
        "specific_events": specific_events,
        "weekday_wake": _get_field(form_data, "weekday_wake"),
        "weekday_sleep": _get_field(form_data, "weekday_sleep"),
        "weekend_wake": _get_field(form_data, "weekend_wake"),
        "weekend_sleep": _get_field(form_data, "weekend_sleep"),
        "routines": form_data.get("routines", {}),
        "daily_routine": {
            "weekday_wake": _get_field(form_data, "weekday_wake"),
            "weekday_sleep": _get_field(form_data, "weekday_sleep"),
            "weekend_wake": _get_field(form_data, "weekend_wake"),
            "weekend_sleep": _get_field(form_data, "weekend_sleep"),
        },
    }

    daily_data: dict[str, Any] = {
        "daily_progress": _get_field(form_data, "daily_progress"),
        "mood": _get_field(form_data, "mood"),
        "energy": _get_field(form_data, "energy"),
        "time_loss": _get_field(form_data, "time_loss"),
        "pacing_feedback": _get_field(form_data, "pacing_feedback"),
        "notes": _get_field(form_data, "notes"),
    }
    try:
        pacing_val = int(daily_data.get("pacing_feedback") or 3)
    except (TypeError, ValueError):
        pacing_val = 3
    try:
        loss_val = float(daily_data.get("time_loss") or 0)
    except (TypeError, ValueError):
        loss_val = 0.0
    try:
        mood_val = int(daily_data.get("mood") or 3)
    except (TypeError, ValueError):
        mood_val = 3
    daily_data["recommendation"] = get_adjustment_message(pacing_val, loss_val, mood_val)
    return plan_data, daily_data


def build_monthly_plan(plan_data: dict[str, Any], schedule_result: list[dict[str, Any]] = None) -> list[dict[str, Any]]:
    start_date = datetime.strptime(plan_data.get("start_date", date.today().strftime("%Y-%m-%d")), "%Y-%m-%d").date()
    end_date = plan_data.get("end_date")
    if end_date:
        try:
            end_date_value = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            end_date_value = start_date
    else:
        end_date_value = start_date + timedelta(days=max(1, int(plan_data.get("timeframe_days", 1) or 1) - 1))

    fixed_events = plan_data.get("fixed_events", []) or []

    weekday_map = {
        0: "週一",
        1: "週二",
        2: "週三",
        3: "週四",
        4: "週五",
        5: "週六",
        6: "週日",
    }

    # Group schedule result by date and aggregate same subject & material
    schedule_by_date: dict[str, list[dict[str, Any]]] = {}
    if schedule_result:
        for s in schedule_result:
            d_str = s.get("date")
            if d_str:
                schedule_by_date.setdefault(d_str, []).append(s)

    monthly_plan: list[dict[str, Any]] = []
    current_date = start_date
    while current_date <= end_date_value:
        d_str = current_date.strftime("%Y-%m-%d")
        weekday_label = weekday_map[current_date.weekday()]

        tasks = []
        selected_subjects = []
        if d_str in schedule_by_date:
            day_sessions = schedule_by_date[d_str]
            # Group by (subject, material, unit) to combine duplicate subject/material lines
            grouped: dict[tuple[str, str, str], float] = {}
            for item in day_sessions:
                subj = item.get("科目", "")
                if subj == "總複習 (自由安排)" or not subj:
                    continue
                if subj not in selected_subjects:
                    selected_subjects.append(subj)
                mat = item.get("教材", "")
                tgt = item.get("目標進度", "")
                parts = tgt.split(" ")
                qty = 0.0
                unit = "頁"
                if len(parts) >= 2:
                    try:
                        qty = float(parts[0])
                        unit = parts[1]
                    except ValueError:
                        pass
                elif len(parts) == 1 and parts[0]:
                    try:
                        qty = float(parts[0])
                    except ValueError:
                        pass
                key = (subj, mat, unit)
                grouped[key] = grouped.get(key, 0.0) + qty

            for (subj, mat, unit), total_qty in grouped.items():
                qty_str = f"{int(total_qty)}" if total_qty.is_integer() else f"{total_qty:.1f}"
                if mat and mat != "-":
                    tasks.append(f"{subj}：{mat} {qty_str} {unit}")
                else:
                    tasks.append(f"{subj}：{qty_str} {unit}")

        daily_events = [
            event
            for event in fixed_events
            if weekday_label in event.get("weekdays", []) and event.get("show_on_calendar", True)
        ]
        monthly_plan.append(
            {
                "date": d_str,
                "day_name": weekday_label,
                "subjects": selected_subjects,
                "tasks": tasks,
                "fixed_events": daily_events,
                "target_progress": "完成今日指定進度",
            }
        )
        current_date += timedelta(days=1)
    return monthly_plan


def _initialize_session_state() -> None:
    # core plan data
    if "plan" not in st.session_state:
        st.session_state["plan"] = None
    if "monthly_plan" not in st.session_state:
        st.session_state["monthly_plan"] = None
    if "daily_log" not in st.session_state:
        st.session_state["daily_log"] = None

    if "subjects" not in st.session_state:
        st.session_state["subjects"] = [{"name": "", "color": "#4f84ff", "materials": [{"name": "", "type": "課本", "quantity": 1}], "weekdays": []}]
    if "fixed_events" not in st.session_state:
        st.session_state["fixed_events"] = [{"title": "", "weekdays": [], "start": "", "end": "", "emoji": "📚", "color": "#4f84ff", "display_color": "#4f84ff", "show_on_calendar": True, "custom_color": False}]
    if "specific_events" not in st.session_state:
        st.session_state["specific_events"] = []
    if "plan_name" not in st.session_state:
        st.session_state["plan_name"] = ""
    if "plan_goal" not in st.session_state:
        st.session_state["plan_goal"] = ""
    if "preferred_subject_count" not in st.session_state:
        st.session_state["preferred_subject_count"] = 0
    if "main_page" not in st.session_state:
        st.session_state["main_page"] = "計劃頁面"
    if "selected_day" not in st.session_state:
        st.session_state["selected_day"] = None


def render_emoji_picker(label: str, current_emoji: str, key_prefix: str) -> str:
    """提供一格一格的網格型表情符號選擇器，讓使用者一目了然，不用滑動長滾輪選單。"""
    state_key = f"{key_prefix}_selected_emoji"
    if state_key not in st.session_state:
        st.session_state[state_key] = current_emoji if current_emoji in EMOJI_OPTIONS else EMOJI_OPTIONS[0]

    curr = st.session_state[state_key]
    st.markdown(f"**{label}**")
    with st.popover(f"{curr} 選擇表情符號 (點擊開啟表情格)", use_container_width=True):
        st.caption("點擊下方表情格直接選取：")
        cols = st.columns(8)
        for i, emoji_char in enumerate(EMOJI_OPTIONS):
            is_active = (emoji_char == curr)
            btn_type = "primary" if is_active else "secondary"
            if cols[i % 8].button(
                emoji_char,
                key=f"{key_prefix}_emj_{i}",
                type=btn_type,
                use_container_width=True
            ):
                st.session_state[state_key] = emoji_char
                st.rerun()

    return st.session_state.get(state_key, current_emoji)


def render_weekday_selector(label: str, selected_weekdays: list[str], key_prefix: str) -> list[str]:
    """星期按鈕選擇器，選取時直接套用自訂主題按鈕色彩 (button_color)。"""
    state_key = f"{key_prefix}_weekdays_state"
    if state_key not in st.session_state:
        st.session_state[state_key] = list(selected_weekdays)

    current_selected = st.session_state[state_key]
    st.markdown(f"**{label}**")
    cols = st.columns(7)
    for i, day_name in enumerate(WEEKDAY_OPTIONS):
        is_sel = day_name in current_selected
        btn_type = "primary" if is_sel else "secondary"
        if cols[i].button(day_name, key=f"{key_prefix}_day_btn_{i}", type=btn_type, use_container_width=True):
            if is_sel:
                current_selected.remove(day_name)
            else:
                current_selected.append(day_name)
            st.session_state[state_key] = list(current_selected)
            st.rerun()
    return st.session_state[state_key]


def get_material_unit(material_type: str) -> str:
    return MATERIAL_UNIT_MAP.get(material_type, "項")


def _add_subject():
    st.session_state["subjects"].append({"name": "", "color": "#4f84ff", "materials": [{"name": "", "type": "課本", "quantity": 1}], "weekdays": []})

def _del_subject(idx):
    st.session_state["subjects"].pop(idx)

def _add_material(idx):
    st.session_state["subjects"][idx]["materials"].append({"name": "", "type": "課本", "quantity": 1})

def _del_material(idx, mid):
    del st.session_state["subjects"][idx]["materials"][mid]

def _add_event():
    st.session_state["fixed_events"].append({"title": "", "weekdays": [], "start": "08:00", "end": "09:00", "emoji": "📚", "color": "#4f84ff", "display_color": "#4f84ff", "show_on_calendar": True, "custom_color": False})

def _del_event(idx):
    st.session_state["fixed_events"].pop(idx)

def _add_specific_event():
    st.session_state["specific_events"].append({"title": "", "start_date": "", "end_date": "", "start_time": "08:00", "end_time": "17:00", "emoji": "🏖️", "color": "#ff9f43", "display_color": "#ff9f43", "show_on_calendar": True, "custom_color": False, "concurrent_with_study": False})

def _del_specific_event(idx):
    st.session_state["specific_events"].pop(idx)

def _parse_time_str(t_str: str, default="08:00"):
    try:
        return datetime.strptime(t_str, "%H:%M").time()
    except:
        return datetime.strptime(default, "%H:%M").time()

def render_time_picker(label: str, default_time_str: str, key_prefix: str) -> str:
    try:
        if ":" in default_time_str:
            h, m = default_time_str.split(":")[:2]
        else:
            h, m = "08", "00"
        default_h = int(h)
        default_m = int(m)
    except:
        default_h, default_m = 8, 0

    st.markdown(f"<div style='font-size: 14px; margin-bottom: 4px;'>{label}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        hour = st.selectbox("時", [f"{i:02d}" for i in range(24)], index=default_h, key=f"{key_prefix}_h", label_visibility="collapsed")
    with c2:
        minute = st.selectbox("分", [f"{i:02d}" for i in range(60)], index=default_m, key=f"{key_prefix}_m", label_visibility="collapsed")
    return f"{hour}:{minute}"


def render_setup_page() -> None:
    st.subheader("1. 初始設定")
    _initialize_session_state()

    if "plan_name" not in st.session_state: st.session_state["plan_name"] = ""
    if "plan_goal" not in st.session_state: st.session_state["plan_goal"] = ""

    st.session_state["plan_name"] = st.text_input("讀書計畫名稱", value=st.session_state["plan_name"])
    st.session_state["plan_goal"] = st.text_area("計畫目標", value=st.session_state["plan_goal"], placeholder="進入班排前十、書卷獎、比上次進步五名...")

    start_date = st.date_input("開始日期", value=date.today(), key="setup_start_date")
    end_date = st.date_input("結束日期", value=start_date + timedelta(days=29), key="setup_end_date")
    if end_date < start_date:
        st.error("結束日期不能早於開始日期。")

    st.subheader("科目與教材")
    st.caption("每個科目可新增多個教材／材料，輸入完一項後再按新增科目或新增教材。")

    for idx, subject in enumerate(st.session_state["subjects"]):
        with st.container():
            st.markdown(f"### 科目 {idx + 1}")
            sc1, sc2 = st.columns([3, 1])
            with sc1:
                name_value = st.text_input("科目名稱", value=subject.get("name", ""), key=f"subject_name_{idx}")
                st.session_state["subjects"][idx]["name"] = name_value
            with sc2:
                if f"subject_color_{idx}" not in st.session_state:
                    st.session_state[f"subject_color_{idx}"] = subject.get("color", "#4f84ff")
                    
                def _update_subj_color(i=idx):
                    hex_val = st.session_state.get(f"subj_hex_in_{i}")
                    if hex_val:
                        st.session_state[f"subject_color_{i}"] = hex_val
                    
                color_val = st.color_picker("科目代表色", key=f"subject_color_{idx}")
                st.text_input("或輸入色號", value=color_val, key=f"subj_hex_in_{idx}", on_change=_update_subj_color, kwargs={"i": idx})
                st.session_state["subjects"][idx]["color"] = st.session_state[f"subject_color_{idx}"]

            materials = st.session_state["subjects"][idx].setdefault("materials", [{"name": "", "type": "課本", "quantity": 1}])
            for mid, material in enumerate(materials):
                effective_type = material.get("type", "課本")
                selected_type = effective_type if effective_type in MATERIAL_TYPES else "其他"
                cols = st.columns([2, 1.2, 1.2, 0.8])
                with cols[0]:
                    material_name = st.text_input("教材名稱", value=material.get("name", ""), key=f"subject_{idx}_material_name_{mid}")
                    st.session_state["subjects"][idx]["materials"][mid]["name"] = material_name
                with cols[1]:
                    material_type = st.selectbox(
                        "類型",
                        MATERIAL_TYPES,
                        index=MATERIAL_TYPES.index(selected_type),
                        key=f"subject_{idx}_material_type_{mid}",
                    )
                    custom_type_value = material.get("custom_type", "") if material_type == "其他" else ""
                    if material_type == "其他":
                        custom_type_value = st.text_input(
                            "其他類型",
                            value=custom_type_value,
                            key=f"subject_{idx}_material_custom_{mid}",
                        )
                        effective_type = custom_type_value.strip() or "其他"
                    else:
                        effective_type = material_type
                    st.session_state["subjects"][idx]["materials"][mid]["type"] = effective_type
                    if effective_type == "其他":
                        st.session_state["subjects"][idx]["materials"][mid]["custom_type"] = custom_type_value
                    else:
                        st.session_state["subjects"][idx]["materials"][mid].pop("custom_type", None)
                with cols[2]:
                    unit_text = get_material_unit(effective_type)
                    quantity_value = st.number_input(
                        f"數量 ({unit_text})",
                        min_value=1,
                        step=1,
                        value=int(material.get("quantity", material.get("pages", 1)) or 1),
                        key=f"subject_{idx}_material_quantity_{mid}",
                    )
                    st.session_state["subjects"][idx]["materials"][mid]["quantity"] = int(quantity_value)
                with cols[3]:
                    st.button("刪除教材", key=f"delete_material_{idx}_{mid}", on_click=_del_material, args=(idx, mid))
            st.button("新增教材／材料", key=f"add_material_{idx}", on_click=_add_material, args=(idx,))
            
            ec1, ec2 = st.columns(2)
            with ec1:
                default_exam = subject.get("exam_date")
                if isinstance(default_exam, str):
                    try:
                        default_exam = datetime.strptime(default_exam, "%Y-%m-%d").date()
                    except:
                        default_exam = end_date
                if not default_exam:
                    default_exam = end_date
                
                exam_date_val = st.date_input("考試日期 (排程基準日)", value=default_exam, key=f"subject_{idx}_exam_date")
                st.session_state["subjects"][idx]["exam_date"] = exam_date_val.strftime("%Y-%m-%d")
                
            with ec2:
                weekdays_value = render_weekday_selector("希望安排在的星期", subject.get("weekdays", []), f"subject_{idx}")
                st.session_state["subjects"][idx]["weekdays"] = weekdays_value
            if len(st.session_state["subjects"]) > 1:
                st.button("刪除科目", key=f"delete_subject_{idx}", on_click=_del_subject, args=(idx,))
        st.divider()

    st.button("新增科目", on_click=_add_subject)

    st.subheader("學習偏好")
    count_options = ["無偏好"] + [str(i) for i in range(1, 11)]
    raw_pref = st.session_state.get("preferred_subject_count", "無偏好")
    if raw_pref == 0 or raw_pref == "0" or not raw_pref:
        pref_str = "無偏好"
    else:
        pref_str = str(raw_pref)
    if pref_str not in count_options:
        pref_str = "無偏好"

    pref_idx = count_options.index(pref_str)

    preferred_subject_count_value = st.selectbox(
        "每天偏好的總科目數量",
        count_options,
        index=pref_idx,
        key="select_preferred_subj_count",
    )
    st.session_state["preferred_subject_count"] = 0 if preferred_subject_count_value == "無偏好" else int(preferred_subject_count_value)

    st.caption("你可以設定每天最希望安排的科目數量，若沒有特別偏好可選無偏好。")

    st.subheader("固定行程")
    st.caption("可像 Google Calendar 一樣新增固定行程，並選擇要不要顯示在月曆上。")

    for idx, event in enumerate(st.session_state["fixed_events"]):
        with st.container():
            title_value = st.text_input("行程標題", value=event.get("title", ""), key=f"event_title_{idx}")
            weekdays_value = render_weekday_selector("星期", event.get("weekdays", []), f"event_{idx}")
            
            st_col, end_col = st.columns(2)
            with st_col:
                start_value = render_time_picker("開始時間", event.get("start", "08:00"), f"event_start_{idx}")
            with end_col:
                end_value = render_time_picker("結束時間", event.get("end", "09:00"), f"event_end_{idx}")
            color_option = st.selectbox(
                "顏色",
                options=COLOR_OPTIONS,
                format_func=lambda option: option["name"] if isinstance(option, dict) else option,
                index=next((index for index, option in enumerate(COLOR_OPTIONS) if isinstance(option, dict) and (option["value"] == event.get("display_color") or option["value"] == event.get("color"))), 0),
                key=f"event_color_{idx}",
            )
            if isinstance(color_option, dict):
                st.markdown(f"<div style='display:inline-block;width:20px;height:20px;border-radius:4px;background:{color_option['value']};vertical-align:middle;margin-right:6px;'></div> {color_option['name']}", unsafe_allow_html=True)
            emoji_option = render_emoji_picker(
                "表情符號",
                event.get("emoji", EMOJI_OPTIONS[0]),
                f"event_{idx}"
            )
            show_on_calendar = st.checkbox("顯示在月曆", value=bool(event.get("show_on_calendar", True)), key=f"event_show_{idx}")
            concurrent_with_study = st.checkbox("是否能和讀書計畫並行？", value=bool(event.get("concurrent_with_study", False)), key=f"event_concurrent_{idx}")
            use_custom_color = st.checkbox("使用自訂顏色或色號", value=bool(event.get("custom_color", False)), key=f"event_custom_{idx}")
            custom_color_value = None
            if use_custom_color:
                custom_color_value = st.color_picker("自訂顏色", value=event.get("display_color") or event.get("color") or "#4f84ff", key=f"event_custom_color_{idx}")
            st.button("刪除行程", key=f"delete_event_{idx}", on_click=_del_event, args=(idx,))
            st.session_state["fixed_events"][idx] = {
                "title": title_value,
                "weekdays": weekdays_value,
                "start": start_value,
                "end": end_value,
                "emoji": emoji_option,
                "color": custom_color_value or (color_option["value"] if isinstance(color_option, dict) else color_option),
                "display_color": custom_color_value or (color_option["value"] if isinstance(color_option, dict) else color_option),
                "show_on_calendar": show_on_calendar,
                "concurrent_with_study": concurrent_with_study,
                "custom_color": use_custom_color,
            }
        st.divider()

    st.button("新增行程", on_click=_add_event)

    st.subheader("例外/特定日期行程")
    st.caption("新增單次、跨日期的行程（如：校外教學、段考、畢旅），系統將自動為您空出這些日子的讀書時間。")
    
    for idx, event in enumerate(st.session_state["specific_events"]):
        with st.container():
            title_value = st.text_input("行程標題", value=event.get("title", ""), key=f"specific_event_title_{idx}")
            
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                try:
                    default_start_date = datetime.strptime(event.get("start_date", ""), "%Y-%m-%d").date()
                except:
                    default_start_date = date.today()
                start_date_value = st.date_input("開始日期", value=default_start_date, key=f"specific_event_start_date_{idx}")
            with d_col2:
                try:
                    default_end_date = datetime.strptime(event.get("end_date", ""), "%Y-%m-%d").date()
                except:
                    default_end_date = start_date_value
                end_date_value = st.date_input("結束日期", value=default_end_date, key=f"specific_event_end_date_{idx}")
                
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                start_time_value = render_time_picker("開始時間", event.get("start_time", "08:00"), f"specific_event_start_time_{idx}")
            with t_col2:
                end_time_value = render_time_picker("結束時間", event.get("end_time", "17:00"), f"specific_event_end_time_{idx}")
                
            color_option = st.selectbox(
                "顏色",
                options=COLOR_OPTIONS,
                format_func=lambda option: option["name"] if isinstance(option, dict) else option,
                index=next((index for index, option in enumerate(COLOR_OPTIONS) if isinstance(option, dict) and (option["value"] == event.get("display_color") or option["value"] == event.get("color"))), 4),
                key=f"specific_event_color_{idx}",
            )
            if isinstance(color_option, dict):
                st.markdown(f"<div style='display:inline-block;width:20px;height:20px;border-radius:4px;background:{color_option['value']};vertical-align:middle;margin-right:6px;'></div> {color_option['name']}", unsafe_allow_html=True)
            
            emoji_option = render_emoji_picker(
                "表情符號",
                event.get("emoji", "🏖️"),
                f"specific_event_{idx}"
            )
            
            show_on_calendar = st.checkbox("顯示在月曆", value=bool(event.get("show_on_calendar", True)), key=f"specific_event_show_{idx}")
            concurrent_with_study = st.checkbox("是否能和讀書計畫並行？", value=bool(event.get("concurrent_with_study", False)), key=f"specific_event_concurrent_{idx}")
            
            st.button("刪除此行程", key=f"delete_specific_event_{idx}", on_click=_del_specific_event, args=(idx,))
            
            st.session_state["specific_events"][idx] = {
                "title": title_value,
                "start_date": start_date_value.strftime("%Y-%m-%d"),
                "end_date": end_date_value.strftime("%Y-%m-%d"),
                "start_time": start_time_value,
                "end_time": end_time_value,
                "emoji": emoji_option,
                "color": color_option["value"] if isinstance(color_option, dict) else color_option,
                "display_color": color_option["value"] if isinstance(color_option, dict) else color_option,
                "show_on_calendar": show_on_calendar,
                "concurrent_with_study": concurrent_with_study,
                "custom_color": False,
            }
        st.divider()

    st.button("新增特定日期行程", on_click=_add_specific_event)

    st.subheader("每日作息")
    c1, c2 = st.columns(2)
    with c1:
        weekday_wake = render_time_picker("平日起床", st.session_state.get("weekday_wake", "07:00"), "weekday_wake")
        weekend_wake = render_time_picker("假日起床", st.session_state.get("weekend_wake", "07:30"), "weekend_wake")
    with c2:
        weekday_sleep = render_time_picker("平日睡覺", st.session_state.get("weekday_sleep", "23:30"), "weekday_sleep")
        weekend_sleep = render_time_picker("假日睡覺", st.session_state.get("weekend_sleep", "00:30"), "weekend_sleep")
        
    st.markdown("#### 日常行程 (系統將自動扣除這些時段以計算可用讀書時數)")
    if "prep_start" not in st.session_state:
        st.session_state["prep_start"] = "07:30"
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        prep_start = render_time_picker("早上準備/早餐開始", st.session_state.get("prep_start", "07:30"), "prep_start")
        prep_end = render_time_picker("早上準備/早餐結束", st.session_state.get("prep_end", "08:00"), "prep_end")
    with r2:
        lunch_start = render_time_picker("午餐開始", st.session_state.get("lunch_start", "12:00"), "lunch_start")
        lunch_end = render_time_picker("午餐結束", st.session_state.get("lunch_end", "13:00"), "lunch_end")
    with r3:
        dinner_start = render_time_picker("晚餐開始", st.session_state.get("dinner_start", "18:00"), "dinner_start")
        dinner_end = render_time_picker("晚餐結束", st.session_state.get("dinner_end", "19:00"), "dinner_end")
    with r4:
        bath_start = render_time_picker("洗澡開始", st.session_state.get("bath_start", "21:00"), "bath_start")
        bath_end = render_time_picker("洗澡結束", st.session_state.get("bath_end", "21:30"), "bath_end")

    has_existing_plan = bool(st.session_state.get("app_state", {}).get("monthly_plan"))
    is_partial_reschedule = False
    
    st.divider()
    if has_existing_plan:
        st.info("💡 **系統偵測到您已有正在進行的計畫**。如果您中途新增了行程，建議勾選下方選項，系統會將您「還沒讀完的進度」重新均勻分配到「今天到計畫結束」的剩餘空閒時間中，並保留過去的打卡紀錄！")
        is_partial_reschedule = st.checkbox("保留過去紀錄，僅從今日起重新排定剩餘進度", value=True)
        
    if st.button("生成讀書計畫", type="primary"):
        if end_date < start_date:
            st.error("結束日期不能早於開始日期。")
            return
            
        import logic
        
        for start_val, end_val, label in [
            (prep_start, prep_end, "早上準備/早餐"),
            (lunch_start, lunch_end, "午餐"),
            (dinner_start, dinner_end, "晚餐"),
            (bath_start, bath_end, "洗澡")
        ]:
            if logic.get_minutes(end_val) <= logic.get_minutes(start_val):
                st.error(f"「{label}」結束時間必須晚於開始時間。")
                return

        for wake, sleep, day_type in [(weekday_wake, weekday_sleep, "平日"), (weekend_wake, weekend_sleep, "假日")]:
            wake_m = logic.get_minutes(wake)
            sleep_m = logic.get_minutes(sleep)
            
            prep_start_m = logic.get_minutes(prep_start)
            if prep_start_m < wake_m:
                st.error(f"「早上準備/早餐」開始時間 ({prep_start}) 不能早於{day_type}起床時間 ({wake})。")
                return
                
            dinner_end_m = logic.get_minutes(dinner_end)
            if sleep_m > wake_m and dinner_end_m > sleep_m:
                st.error(f"「晚餐」結束時間 ({dinner_end}) 不能晚於{day_type}睡覺時間 ({sleep})。")
                return
                
            bath_end_m = logic.get_minutes(bath_end)
            if sleep_m > wake_m and bath_end_m > sleep_m:
                st.error(f"「洗澡」結束時間 ({bath_end}) 不能晚於{day_type}睡覺時間 ({sleep})。")
                return
        payload = {
            "plan_name": st.session_state.get("plan_name", ""),
            "plan_goal": st.session_state.get("plan_goal", ""),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "preferred_subject_count": st.session_state.get("preferred_subject_count", 0),
            "subjects": st.session_state["subjects"],
            "fixed_events": st.session_state["fixed_events"],
            "specific_events": st.session_state["specific_events"],
            "weekday_wake": weekday_wake,
            "weekday_sleep": weekday_sleep,
            "weekend_wake": weekend_wake,
            "weekend_sleep": weekend_sleep,
            "routines": {
                "prep": {"start": prep_start, "end": prep_end},
                "lunch": {"start": lunch_start, "end": lunch_end},
                "dinner": {"start": dinner_start, "end": dinner_end},
                "bath": {"start": bath_start, "end": bath_end},
            }
        }
        plan_data, daily_data = collect_plan_and_daily_data(payload)
        st.session_state["plan"] = plan_data
        
        # 1. Generate monthly plan schedule automatically
        import logic
        if is_partial_reschedule:
            existing_schedule = st.session_state.get("app_state", {}).get("monthly_plan")
            schedule_result = logic.generate_daily_schedule(plan_data, existing_schedule=existing_schedule, reschedule_from_date=date.today())
        else:
            schedule_result = logic.generate_daily_schedule(plan_data)
            
        st.session_state.setdefault("app_state", {})["monthly_plan"] = schedule_result
        
        st.session_state["monthly_plan"] = build_monthly_plan(plan_data, schedule_result)
        st.session_state["main_page"] = "月計畫"
        
        # Save to storage
        import storage
        storage.save_current_state()
        
        st.success("初始設定已完成，月計畫已建立。")


# The monthly plan page rendering is implemented in pages/monthlyplan.py





def render_dashboard_page() -> None:
    if not st.session_state.get('plan'):
        st.info('目前尚未建立讀書計畫，請先到計畫頁面完成初始設定。')
        return
    dashboard.render_dashboard()


def is_dark_color(hex_color: str) -> bool:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return luminance < 128
    except Exception:
        return False


def apply_custom_theme() -> None:
    theme = st.session_state.get("custom_theme", {})
    bg_color = theme.get("bg_color", "#ffffff")
    button_color = theme.get("button_color", "#4f84ff")
    navbar_bg_color = theme.get("navbar_bg_color", "#f8f9fa")

    dark_mode = is_dark_color(bg_color)
    
    if dark_mode:
        card_bg = "#181825"
        card_text = "#f3f4f6"
        border_color = "rgba(255, 255, 255, 0.2)"
        input_bg = "#27273a"
        input_text = "#ffffff"
        sec_btn_bg = "#27273a"
        sec_btn_text = "#e5e7eb"
    else:
        card_bg = "#ffffff"
        card_text = "#1f2937"
        border_color = "rgba(0, 0, 0, 0.12)"
        input_bg = "#ffffff"
        input_text = "#1f2937"
        sec_btn_bg = "#ffffff"
        sec_btn_text = "#374151"

    css = f"""
    <style>
    /* 1. 主體背景與預設文字顏色 */
    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: {bg_color} !important;
        background: {bg_color} !important;
        color: {card_text} !important;
    }}
    
    /* 2. 徹底重寫所有外框容器 (st.container(border=True), st.expander, st.form, 邊框區塊) 內部填滿純白/純黑背景 */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlockBorderWrapper"] > div,
    div[data-testid="stVerticalBlockBorderWrapper"] div,
    div[data-testid="stVerticalBlockBorderWrapper"] div[class*="st-"],
    [data-testid="stBorderWrapper"],
    [data-testid="stBorderWrapper"] > div,
    [data-testid="stBorderWrapper"] div,
    [data-testid="stBorderWrapper"] div[class*="st-"],
    div[data-testid="stForm"],
    div[data-testid="stForm"] > div,
    div[data-testid="stForm"] div,
    details[data-testid="stExpander"],
    details[data-testid="stExpander"] > div,
    details[data-testid="stExpander"] summary {{
        background-color: {card_bg} !important;
        background: {card_bg} !important;
        color: {card_text} !important;
    }}
    
    /* 邊框與圓角樣式 */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stForm"],
    details[data-testid="stExpander"],
    [data-testid="stBorderWrapper"] {{
        border: 1px solid {border_color} !important;
        border-radius: 12px !important;
        background-color: {card_bg} !important;
        background: {card_bg} !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }}
    
    summary[data-testid="stExpanderSummary"] {{
        background-color: {card_bg} !important;
        background: {card_bg} !important;
        color: {card_text} !important;
    }}
    
    /* 3. 輸入框與選項元件背景色 */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] {
        background-color: {input_bg} !important;
        background: {input_bg} !important;
        color: {input_text} !important;
        border-color: {border_color} !important;
    }
    input, textarea {
        color: {input_text} !important;
    }

    /* 防止瀏覽器自動填入時產生怪異黃/藍色背景及建議提示干擾 */
    input:-webkit-autofill,
    input:-webkit-autofill:hover, 
    input:-webkit-autofill:focus, 
    input:-webkit-autofill:active {
        -webkit-box-shadow: 0 0 0 1000px {input_bg} inset !important;
        -webkit-text-fill-color: {input_text} !important;
        transition: background-color 5000s ease-in-out 0s;
    }

    /* 4. 精確覆蓋頂部第一列主選單塊 (頂部橫向主選單) */
    div[data-testid="stAppViewContainer"] section.main div[data-testid="stHorizontalBlock"]:first-of-type {
        background-color: {navbar_bg_color} !important;
        background: {navbar_bg_color} !important;
        padding: 12px 16px !important;
        border-radius: 12px !important;
        margin-bottom: 20px !important;
        border: 1px solid {border_color} !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stAppViewContainer"] section.main div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="column"],
    div[data-testid="stAppViewContainer"] section.main div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="element-container"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 5. 按鈕顏色獨立防護：確保按鈕有自己的實心與外框樣式，內部文字透明 */
    button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {
        background-color: {button_color} !important;
        background: {button_color} !important;
        border-color: {button_color} !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    button[kind="secondary"],
    button[data-testid="stBaseButton-secondary"] {
        background-color: {sec_btn_bg} !important;
        background: {sec_btn_bg} !important;
        color: {sec_btn_text} !important;
        border: 1px solid {border_color} !important;
    }
    button[kind="secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover {
        border-color: {button_color} !important;
        color: {button_color} !important;
    }
    button *,
    button p,
    button div,
    button span {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 6. 星期與標籤 (Multiselect Tags & Pills) 套用按鈕自訂主題色 */
    div[data-baseweb="tag"],
    span[data-baseweb="tag"],
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
    div[data-testid="stMultiSelect"] div[data-baseweb="tag"],
    div[data-baseweb="tag"] [data-role="remove"],
    div[data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: {button_color} !important;
        background: {button_color} !important;
        color: #ffffff !important;
        border-color: {button_color} !important;
    }
    div[data-baseweb="tag"] *,
    span[data-baseweb="tag"] *,
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    js = r"""
    <script>
    (function() {
        function disableAutofill() {
            try {
                const root = window.parent ? window.parent.document : document;
                const inputs = root.querySelectorAll('input:not([type="submit"]):not([type="button"]), textarea');
                inputs.forEach(el => {
                    el.setAttribute('autocomplete', 'off');
                    el.setAttribute('autocorrect', 'off');
                    el.setAttribute('autocapitalize', 'off');
                    el.setAttribute('spellcheck', 'false');
                    el.setAttribute('data-lpignore', 'true');
                    el.setAttribute('data-form-type', 'other');
                });
            } catch(e) {}
        }
        disableAutofill();
        if (window.parent && window.parent.document) {
            const obs = new MutationObserver(disableAutofill);
            obs.observe(window.parent.document.body, { childList: true, subtree: true });
        }
    })();
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


def render_home_page() -> None:
    apply_custom_theme()

    features = st.session_state.get("enabled_features")
    if not isinstance(features, dict):
        features = {
            "page_dashboard": True, "dash_study_progress": True, "dash_weekly_chart": True, "dash_mood_pacing": True,
            "page_monthly": True, "monthly_calendar": True, "monthly_schedule": True, "monthly_events": True,
            "page_daily": True, "daily_timeline": True, "daily_checklist": True, "daily_mood": True, "daily_timeloss": True,
            "page_timer": True, "timer_clock": True, "timer_history": True
        }

    # "計畫頁面" and "設定" are fixed
    page_options = ["計劃頁面"]
    if features.get("page_dashboard", True):
        page_options.append("dashboard")
    if features.get("page_monthly", True):
        page_options.append("月計畫")
    if features.get("page_daily", True):
        page_options.append("每日打卡與微調")
    if features.get("page_timer", True):
        page_options.append("計時器")
    page_options.append("設定")

    if "main_page" not in st.session_state or st.session_state["main_page"] not in page_options:
        st.session_state["main_page"] = "計劃頁面" if not st.session_state.get("plan") else page_options[min(1, len(page_options)-1)]

    # ── 頂部橫向主選單 (Horizontal Navbar at the top) ──────────────────────────
    cols_count = len(page_options) + 1
    nav_cols = st.columns(cols_count, gap="small")
    with nav_cols[0]:
        if st.button("🏠 計畫列表", key="top_nav_home", use_container_width=True):
            st.session_state["current_plan_id"] = None
            if "plan_id" in st.query_params:
                del st.query_params["plan_id"]
            st.rerun()
            
    for i, opt in enumerate(page_options):
        with nav_cols[i + 1]:
            is_active = (st.session_state["main_page"] == opt)
            btn_type = "primary" if is_active else "secondary"
            if st.button(opt, key=f"top_nav_{opt}", type=btn_type, use_container_width=True):
                st.session_state["main_page"] = opt
                st.rerun()

    # Handle view_date query param from HTML calendar links
    qp_view = st.query_params.get("view_date")
    if qp_view:
        st.query_params.clear()
        st.session_state["cal_view_date"] = qp_view

    page = st.session_state["main_page"]
    cal_view_date = st.session_state.get("cal_view_date")

    if page != "計劃頁面" and st.session_state.get("plan_name"):
        st.markdown(f"<h2>{st.session_state['plan_name']}</h2>", unsafe_allow_html=True)
        if st.session_state.get("plan_goal"):
            st.markdown(f"<p style='font-size: 16px; color: #555;'>🎯 <b>目標：</b>{st.session_state['plan_goal']}</p>", unsafe_allow_html=True)
    elif page == "計劃頁面":
        st.title("讀書計畫安排助手")
        st.caption("先完成初始設定，生成完整計畫後，再根據每日情況進行打卡與微調。")
    if page == "計劃頁面":
        render_setup_page()
    elif page == "dashboard":
        render_dashboard_page()
    elif page == "月計畫":
        render_monthly_plan_page()
    elif page == "計時器":
        render_timer_page()
    elif page == "設定":
        render_settings_page()
    else:
        render_daily_checkin_page()

def get_registered_users_map() -> dict[str, int]:
    """Returns a map of owner_name -> plan_count for users who have created & saved at least 1 plan."""
    plans = storage.load_all_plans()
    user_counts = {}
    for pdata in plans.values():
        owner = pdata.get("owner_name")
        if owner and owner.strip():
            clean = owner.strip()
            user_counts[clean] = user_counts.get(clean, 0) + 1
    return user_counts

def render_start_page():
    apply_custom_theme()
    st.title("📚 我的讀書計畫")
    
    registered_map = get_registered_users_map()
    registered_users_list = sorted(list(registered_map.keys()))
    curr_user = st.session_state.get("user_name", "").strip()

    # 1. 登入 / 註冊與當前狀態區塊
    if curr_user:
        with st.container(border=True):
            col_info, col_logout = st.columns([3, 1])
            with col_info:
                st.markdown(f"#### 👤 當前登入帳號：**{curr_user}**")
                plan_cnt = registered_map.get(curr_user, 0)
                if plan_cnt > 0:
                    st.caption(f"✅ 已獲得正式擁有權（包含 {plan_cnt} 筆已儲存計畫）")
                else:
                    st.caption("💡 帳號準備中：建立第一個計畫並儲存後，即可正式鎖定該帳號擁有權！")
            with col_logout:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("🚪 登出 / 切換帳號", key="btn_logout", use_container_width=True):
                    st.session_state["user_name"] = ""
                    st.session_state["current_plan_id"] = None
                    if "user" in st.query_params:
                        del st.query_params["user"]
                    if "plan_id" in st.query_params:
                        del st.query_params["plan_id"]
                    st.rerun()
    else:
        # 未登入：提供「🔑 登入已有帳號」與「✨ 註冊新帳號」雙頁籤
        with st.container(border=True):
            st.markdown("#### 🔐 使用者登入 / 註冊系統")
            tab_login, tab_register = st.tabs(["🔑 登入已有帳號", "✨ 註冊新帳號"])
            
            # --- Tab 1: 登入已有帳號 (內含忘記帳號/密碼 6 碼信箱驗證) ---
            with tab_login:
                with st.form(key="form_login", border=False):
                    st.markdown("請輸入您的帳號名稱與密碼（輸入完畢按 **Enter 鍵** 或點擊按鈕即可送出）：")
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        login_username = st.text_input("帳號名稱", key="input_login_username", placeholder="請輸入您的帳號名稱...")
                    with c2:
                        login_password = st.text_input("密碼 (限英文與數字)", type="password", key="input_login_password")
                    with c3:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        login_submitted = st.form_submit_button("🔑 確定登入", use_container_width=True, type="primary")

                if login_password and not storage.is_alphanumeric(login_password):
                    st.warning("⚠️ **密碼格式提醒**：檢測到英文與數字以外的符號！密碼僅能包含英文字母 (A-Z, a-z) 與數字 (0-9)，請移除中文、空格或特殊符號。")

                if login_submitted:
                    clean_user = login_username.strip()
                    if not clean_user:
                        st.error("請輸入帳號名稱！")
                    elif not login_password:
                        st.error("請輸入密碼！")
                    elif not storage.is_alphanumeric(login_password):
                        st.error("⛔ **登入失敗**：密碼包含英文與數字以外的非法符號，請修正後重新輸入！")
                    else:
                        ok, msg = storage.verify_user_credentials(clean_user, login_password)
                        if ok:
                            st.session_state["user_name"] = clean_user
                            st.query_params["user"] = clean_user
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ 登入失敗：{msg}")

                # 忘記帳號 / 密碼（透過 Gmail 接收 6 碼驗證信）
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                is_forgot_open = bool(
                    st.session_state.get("forgot_expanded") or 
                    st.session_state.get("f_user_verify") or 
                    st.session_state.get("f_pass_verify") or
                    st.session_state.get("input_f_email") or
                    st.session_state.get("input_r_user")
                )
                with st.expander("❓ 忘記使用者名稱或密碼？點此發送 6 碼驗證信到 Gmail 找回", expanded=is_forgot_open):
                    forgot_action = st.radio(
                        "請選擇協助項目：", 
                        ["🔍 忘記使用者名稱 (驗證信找回帳號)", "🔑 忘記密碼 (驗證信重設密碼)"], 
                        horizontal=True,
                        key="forgot_action_radio"
                    )

                    if "忘記使用者名稱" in forgot_action:
                        st.markdown("##### 🔍 找回使用者名稱")
                        st.caption("系統將發送 6 碼驗證碼至您註冊時綁定的 Gmail，驗證成功後即可查詢帳號名稱。")
                        
                        f_email_col, f_send_col = st.columns([3, 1])
                        with f_email_col:
                            f_email = st.text_input("註冊時綁定的 Gmail 帳號：", key="input_f_email", placeholder="例如：yourname@gmail.com")
                        with f_send_col:
                            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                            if st.button("📨 發送驗證信", key="btn_send_user_code", use_container_width=True):
                                st.session_state["forgot_expanded"] = True
                                clean_f_email = f_email.strip().lower()
                                if not clean_f_email:
                                    st.error("請先輸入 Gmail 帳號！")
                                elif not storage.is_valid_email(clean_f_email):
                                    st.error("Gmail 格式不正確！")
                                else:
                                    matched_unames = storage.find_usernames_by_email(clean_f_email)
                                    if not matched_unames:
                                        st.error("❌ 查無綁定此 Gmail 的帳號，請確認輸入是否正確。")
                                    else:
                                        v_code = generate_verification_code()
                                        ok, msg = send_verification_email(clean_f_email, v_code, "查詢帳號名稱")
                                        if ok:
                                            st.session_state["f_user_verify"] = {"email": clean_f_email, "code": v_code}
                                            st.success(msg)
                                        else:
                                            st.error(msg)

                        verify_info = st.session_state.get("f_user_verify")
                        if verify_info:
                            st.info(f"📨 驗證信已寄出至 **{verify_info['email']}**，請在下方輸入 6 碼驗證碼：")
                            v1, v2 = st.columns([2, 1])
                            with v1:
                                user_input_code = st.text_input("請輸入 6 碼驗證碼：", key="input_user_vcode", max_chars=6, placeholder="6位數字驗證碼")
                            with v2:
                                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                                if st.button("✅ 驗證身分並顯示帳號", key="btn_check_user_vcode", type="primary", use_container_width=True):
                                    st.session_state["forgot_expanded"] = True
                                    if user_input_code.strip() == verify_info["code"]:
                                        matched_unames = find_usernames_by_email(verify_info["email"])
                                        names_str = "、".join([f"**{u}**" for u in matched_unames])
                                        st.success(f"🎉 **身分驗證成功！** 綁定此 Gmail 的帳號為：{names_str}。您可直接在上方輸入帳號與密碼進行登入！")
                                        st.session_state.pop("f_user_verify", None)
                                    else:
                                        st.error("❌ 驗證碼不正確，請重新確認郵件！")

                    else:
                        st.markdown("##### 🔑 重設密碼")
                        st.caption("系統將發送 6 碼驗證碼至該帳號綁定的 Gmail，驗證成功後即可設定新密碼。")
                        
                        r_user_col, r_email_col, r_send_col = st.columns([2, 2, 1])
                        with r_user_col:
                            r_user = st.text_input("帳號名稱：", key="input_r_user", placeholder="請輸入欲重設密碼的帳號...")
                        with r_email_col:
                            r_email = st.text_input("該帳號綁定的 Gmail：", key="input_r_email", placeholder="請輸入綁定的 Gmail...")
                        with r_send_col:
                            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                            if st.button("📨 發送驗證信", key="btn_send_pass_code", use_container_width=True):
                                st.session_state["forgot_expanded"] = True
                                clean_r_user = r_user.strip()
                                clean_r_email = r_email.strip().lower()
                                if not clean_r_user:
                                    st.error("請輸入帳號名稱！")
                                elif not clean_r_email:
                                    st.error("請輸入綁定的 Gmail！")
                                else:
                                    all_users = storage.load_all_users()
                                    if clean_r_user not in all_users:
                                        st.error(f"找不到帳號「{clean_r_user}」！")
                                    elif all_users[clean_r_user].get("email", "").strip().lower() != clean_r_email:
                                        st.error("❌ 輸入的 Gmail 與該帳號綁定的信箱不一致！")
                                    else:
                                        v_code = generate_verification_code()
                                        ok, msg = send_verification_email(clean_r_email, v_code, "重設密碼")
                                        if ok:
                                            st.session_state["f_pass_verify"] = {"username": clean_r_user, "email": clean_r_email, "code": v_code}
                                            st.success(msg)
                                        else:
                                            st.error(msg)

                        pass_verify_info = st.session_state.get("f_pass_verify")
                        if pass_verify_info:
                            st.info(f"📨 驗證信已寄出至 **{pass_verify_info['email']}**，請輸入 6 碼驗證碼並設定新密碼：")
                            pv1, pv2, pv3 = st.columns([1, 1, 1])
                            with pv1:
                                pass_input_code = st.text_input("6 碼驗證碼：", key="input_pass_vcode", max_chars=6, placeholder="6位數字")
                            with pv2:
                                new_pwd = st.text_input("設定新密碼 (限英數)：", type="password", key="input_reset_pwd")
                            with pv3:
                                new_pwd2 = st.text_input("確認新密碼：", type="password", key="input_reset_pwd2")

                            if (new_pwd and not storage.is_alphanumeric(new_pwd)) or (new_pwd2 and not storage.is_alphanumeric(new_pwd2)):
                                st.warning("⚠️ **密碼格式提醒**：僅能包含英文字母 (A-Z, a-z) 與數字 (0-9)。")

                            if st.button("🔑 驗證身分並重設密碼", key="btn_confirm_reset_pwd", type="primary", use_container_width=True):
                                st.session_state["forgot_expanded"] = True
                                if pass_input_code.strip() != pass_verify_info["code"]:
                                    st.error("❌ 驗證碼不正確，請重新確認郵件！")
                                elif not new_pwd:
                                    st.error("請設定新密碼！")
                                elif not storage.is_alphanumeric(new_pwd):
                                    st.error("⛔ 新密碼包含非法符號，僅限英文與數字！")
                                elif new_pwd != new_pwd2:
                                    st.error("❌ 兩次輸入的新密碼不一致！")
                                else:
                                    ok, msg = storage.reset_user_password_with_email(pass_verify_info["username"], pass_verify_info["email"], new_pwd)
                                    if ok:
                                        st.success(f"🎉 **身分驗證成功！** 帳號「{pass_verify_info['username']}」密碼已重設成功，請直接在上方輸入新密碼登入！")
                                        st.session_state.pop("f_pass_verify", None)
                                    else:
                                        st.error(f"❌ 重設失敗：{msg}")

            # --- Tab 2: 註冊新帳號 ---
            with tab_register:
                with st.form(key="form_register", border=False):
                    st.markdown("請設定您的新帳號與密碼，並綁定 Gmail 帳號（可用於日後忘記帳號或密碼時的驗證）：")
                    cr1, cr2 = st.columns(2)
                    with cr1:
                        new_reg_name = st.text_input("新帳號名字", key="input_new_reg_name", placeholder="例如：Alex...")
                    with cr2:
                        new_reg_email = st.text_input("綁定 Gmail 帳號", key="input_new_reg_email", placeholder="例如：yourname@gmail.com")

                    cr3, cr4, cr5 = st.columns([2, 2, 1])
                    with cr3:
                        new_reg_pass = st.text_input("設定密碼 (限英文與數字)", type="password", key="input_new_reg_pass")
                    with cr4:
                        new_reg_pass2 = st.text_input("確認密碼", type="password", key="input_new_reg_pass2")
                    with cr5:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        reg_submitted = st.form_submit_button("✨ 註冊帳號", use_container_width=True, type="primary")

                if (new_reg_pass and not storage.is_alphanumeric(new_reg_pass)) or (new_reg_pass2 and not storage.is_alphanumeric(new_reg_pass2)):
                    st.warning("⚠️ **密碼格式提醒**：檢測到英文與數字以外的符號！密碼僅能包含英文字母 (A-Z, a-z) 與數字 (0-9)，請移除中文、空格或特殊符號。")

                if reg_submitted:
                    clean_reg = new_reg_name.strip()
                    clean_email = new_reg_email.strip().lower()
                    if not clean_reg:
                        st.error("帳號名字不能為空！")
                    elif not clean_email:
                        st.error("請輸入欲綁定的 Gmail 帳號！")
                    elif not storage.is_valid_email(clean_email):
                        st.error("Gmail 格式不正確，請輸入有效的 Email 地址 (例如：example@gmail.com)！")
                    elif not new_reg_pass:
                        st.error("請設定密碼！")
                    elif not storage.is_alphanumeric(new_reg_pass):
                        st.error("⛔ **註冊失敗**：密碼包含英文與數字以外的非法符號，請修正後重新輸入！")
                    elif new_reg_pass != new_reg_pass2:
                        st.error("❌ 兩次輸入的密碼不一致！")
                    else:
                        ok, msg = storage.register_user(clean_reg, new_reg_pass, clean_email)
                        if ok:
                            st.session_state["user_name"] = clean_reg
                            st.query_params["user"] = clean_reg
                            st.success(f"🎉 帳號「{clean_reg}」註冊成功，並已成功綁定 Gmail ({clean_email})！")
                            st.rerun()
                        else:
                            st.error(f"⛔ 註冊失敗：{msg}")

    st.markdown("---")
    
    user_name = st.session_state.get("user_name", "").strip()
    
    # 如果名字為空白 (未登入)，下方不顯示任何計畫 (每個名字對應各自創立的計畫)
    if not user_name:
        st.warning("🔒 目前處於未登入狀態。請先在上方「登入已有帳號」或「註冊新帳號」，即可載入您的專屬讀書計畫。")
        return

    plans = storage.load_all_plans()
    filtered_plans = {
        pid: pdata for pid, pdata in plans.items()
        if pdata.get("owner_name") == user_name
    }

    # 建立新計畫按鈕
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("➕ 建立新計畫", use_container_width=True, type="primary"):
            new_id = storage.create_new_plan(owner_name=user_name)
            st.session_state["current_plan_id"] = new_id
            st.session_state["main_page"] = "計劃頁面"
            st.query_params["plan_id"] = new_id
            st.query_params["user"] = user_name
            # 載入空白狀態
            new_plan = storage.load_plan(new_id)
            for k, v in new_plan.items():
                if k != "id":
                    st.session_state[k] = v
            st.rerun()
            
    st.markdown("---")
    
    if not filtered_plans:
        st.info(f"使用者「**{user_name}**」目前還沒有讀書計畫。點擊上方「➕ 建立新計畫」開始安排第一個計畫！")
        return
        
    # 顯示現有計畫
    cols = st.columns(3)
    for idx, (plan_id, plan_data) in enumerate(filtered_plans.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                plan_name_disp = plan_data.get("plan_name") or plan_data.get("name") or "未命名計畫"
                plan_goal_disp = plan_data.get("plan_goal") or plan_data.get("goal") or ""
                st.markdown(f"### {plan_name_disp}")
                if plan_goal_disp:
                    st.caption(f"🎯 {plan_goal_disp[:20]}{'...' if len(plan_goal_disp)>20 else ''}")
                else:
                    st.caption("無設定目標")
                
                owner = plan_data.get("owner_name")
                if owner:
                    st.caption(f"👤 所有者：{owner}")
                    
                # 可以加上日期等資訊
                plan_state = plan_data.get("plan", {})
                if plan_state and plan_state.get("start_date"):
                    st.markdown(f"🗓️ {plan_state.get('start_date')} ~ {plan_state.get('end_date')}")
                else:
                    st.markdown("🗓️ 尚未設定排程")
                
                st.markdown("<br/>", unsafe_allow_html=True)
                
                col_enter, col_del = st.columns([3, 1])
                with col_enter:
                    if st.button("進入計畫", key=f"enter_{plan_id}", use_container_width=True):
                        st.session_state["current_plan_id"] = plan_id
                        st.query_params["plan_id"] = plan_id
                        if user_name:
                            st.query_params["user"] = user_name
                        for k, v in plan_data.items():
                            if k != "id":
                                st.session_state[k] = v
                        st.session_state["main_page"] = "dashboard" if st.session_state.get("plan") else "計劃頁面"
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{plan_id}", help="刪除計畫", use_container_width=True):
                        storage.delete_plan(plan_id)
                        st.rerun()


if __name__ == "__main__":
    if not st.session_state.get("current_plan_id"):
        render_start_page()
    else:
        render_home_page()
        import storage
        storage.save_current_state()

# Trigger refresh 49
