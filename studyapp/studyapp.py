from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
import streamlit as st

# 【關鍵修改】確保在任何程式碼執行前，session_state 已經準備好了
if "app_state" not in st.session_state:
    st.session_state["app_state"] = {
        "plan": None,
        "daily_log": None,
        "monthly_plan": None,
    }
app_state = st.session_state["app_state"]

st.set_page_config(page_title="讀書計畫安排助手", page_icon="📚", layout="wide")

# 3. 再來才是 import 你的頁面函式
from monthlyplan import render_monthly_plan_page
from dailycheck import render_daily_checkin_page, get_adjustment_message

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
            }
            for index in range(max(len(event_titles), len(event_days), len(event_starts), len(event_ends), len(event_colors)))
        ]

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


def build_monthly_plan(plan_data: dict[str, Any]) -> list[dict[str, Any]]:
    start_date = datetime.strptime(plan_data.get("start_date", date.today().strftime("%Y-%m-%d")), "%Y-%m-%d").date()
    end_date = plan_data.get("end_date")
    if end_date:
        try:
            end_date_value = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            end_date_value = start_date
    else:
        end_date_value = start_date + timedelta(days=max(1, int(plan_data.get("timeframe_days", 1) or 1) - 1))

    preferred_count = int(plan_data.get("preferred_subject_count", 0) or 0)
    subjects = plan_data.get("subjects", []) or []
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

    monthly_plan: list[dict[str, Any]] = []
    current_date = start_date
    while current_date <= end_date_value:
        selected_subjects = [item["name"] for item in subjects[: max(1, min(preferred_count or 1, len(subjects)))]]
        tasks = []
        for subject in subjects[: max(1, min(preferred_count or 1, len(subjects)))]:
            for material in subject.get("materials", []) or []:
                quantity = material.get("quantity", material.get("pages", 0))
                if quantity:
                    task_name = material.get("name") or material.get("type") or "教材"
                    unit = get_material_unit(material.get("type", ""))
                    tasks.append(f"{subject['name']}：{task_name} {quantity} {unit}")
        weekday_label = weekday_map[current_date.weekday()]
        daily_events = [
            event
            for event in fixed_events
            if weekday_label in event.get("weekdays", []) and event.get("show_on_calendar", True)
        ]
        monthly_plan.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": weekday_label,
                "subjects": selected_subjects,
                "tasks": tasks,
                "fixed_events": daily_events,
                "target_progress": "完成今日指定頁數",
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
        st.session_state["subjects"] = [{"name": "", "materials": [{"name": "", "type": "課本", "quantity": 1}], "weekdays": []}]
    if "fixed_events" not in st.session_state:
        st.session_state["fixed_events"] = [{"title": "", "weekdays": [], "start": "", "end": "", "emoji": "📚", "color": "#4f84ff", "display_color": "#4f84ff", "show_on_calendar": True, "custom_color": False}]
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


def get_material_unit(material_type: str) -> str:
    return MATERIAL_UNIT_MAP.get(material_type, "項")


def _add_subject():
    st.session_state["subjects"].append({"name": "", "materials": [{"name": "", "type": "課本", "quantity": 1}], "weekdays": []})

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

    plan_name = st.text_input("讀書計畫名稱", value=st.session_state.get("plan_name", ""), key="plan_name")
    plan_goal = st.text_area("計畫目標", value=st.session_state.get("plan_goal", ""), placeholder="例如：每天至少看完 50 頁，並保持穩定複習節奏。", key="plan_goal")

    start_date = st.date_input("開始日期", value=date.today(), key="setup_start_date")
    end_date = st.date_input("結束日期", value=start_date + timedelta(days=29), key="setup_end_date")
    if end_date < start_date:
        st.error("結束日期不能早於開始日期。")

    st.subheader("科目與教材")
    st.caption("每個科目可新增多個教材／材料，輸入完一項後再按新增科目或新增教材。")

    for idx, subject in enumerate(st.session_state["subjects"]):
        with st.container():
            st.markdown(f"### 科目 {idx + 1}")
            name_value = st.text_input("科目名稱", value=subject.get("name", ""), key=f"subject_name_{idx}")
            st.session_state["subjects"][idx]["name"] = name_value

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
            weekdays_value = st.multiselect("希望安排在的星期", WEEKDAY_OPTIONS, default=subject.get("weekdays", []), key=f"subject_{idx}_weekdays")
            st.session_state["subjects"][idx]["weekdays"] = weekdays_value
            if len(st.session_state["subjects"]) > 1:
                st.button("刪除科目", key=f"delete_subject_{idx}", on_click=_del_subject, args=(idx,))
        st.divider()

    st.button("新增科目", on_click=_add_subject)

    st.subheader("學習偏好")
    count_options = ["無偏好"] + [str(i) for i in range(1, 11)]
    preferred_subject_count_value = st.selectbox(
        "每天偏好的總科目數量",
        count_options,
        index=count_options.index(str(st.session_state.get("preferred_subject_count", "無偏好"))) if str(st.session_state.get("preferred_subject_count", "無偏好")) in count_options else 0,
        key="preferred_subject_count",
    )
    preferred_subject_count = 0 if preferred_subject_count_value == "無偏好" else int(preferred_subject_count_value)

    st.caption("你可以設定每天最希望安排的科目數量，若沒有特別偏好可選無偏好。")

    st.subheader("固定行程")
    st.caption("可像 Google Calendar 一樣新增固定行程，並選擇要不要顯示在月曆上。")

    for idx, event in enumerate(st.session_state["fixed_events"]):
        with st.container():
            title_value = st.text_input("行程標題", value=event.get("title", ""), key=f"event_title_{idx}")
            weekdays_value = st.multiselect("星期", WEEKDAY_OPTIONS, default=event.get("weekdays", []), key=f"event_weekdays_{idx}")
            
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
            emoji_option = st.selectbox(
                "表情符號",
                options=EMOJI_OPTIONS,
                index=EMOJI_OPTIONS.index(event.get("emoji", EMOJI_OPTIONS[0])) if event.get("emoji") in EMOJI_OPTIONS else 0,
                key=f"event_emoji_{idx}",
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

    st.subheader("每日作息")
    c1, c2 = st.columns(2)
    with c1:
        weekday_wake = render_time_picker("平日起床", st.session_state.get("weekday_wake", "07:00"), "weekday_wake")
        weekend_wake = render_time_picker("假日起床", st.session_state.get("weekend_wake", "08:30"), "weekend_wake")
    with c2:
        weekday_sleep = render_time_picker("平日睡覺", st.session_state.get("weekday_sleep", "23:30"), "weekday_sleep")
        weekend_sleep = render_time_picker("假日睡覺", st.session_state.get("weekend_sleep", "00:30"), "weekend_sleep")
        
    st.markdown("#### 日常行程 (系統將自動扣除這些時段以計算可用讀書時數)")
    # Auto-default prep_start to the later of weekday/weekend wake
    auto_prep_start = max(weekday_wake, weekend_wake)
    if "prep_start" not in st.session_state:
        st.session_state["prep_start"] = auto_prep_start
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        prep_start = render_time_picker("早上準備/早餐開始", st.session_state.get("prep_start", auto_prep_start), "prep_start")
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

    if st.button("生成完整讀書計畫"):
        if end_date < start_date:
            st.error("結束日期不能早於開始日期。")
            return
            
        import logic
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
            "preferred_subject_count": preferred_subject_count,
            "subjects": st.session_state["subjects"],
            "fixed_events": st.session_state["fixed_events"],
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
        st.session_state["monthly_plan"] = build_monthly_plan(plan_data)
        st.session_state["main_page"] = "月計畫"
        st.success("初始設定已完成，月計畫已建立。")


# The monthly plan page rendering is implemented in pages/monthlyplan.py





def render_dashboard_page() -> None:
    st.subheader("Dashboard")
    if not st.session_state.get("plan"):
        st.info("目前尚未建立讀書計畫，請先到計劃頁面完成初始設定。")
        return
    plan = st.session_state["plan"]
    st.markdown(f"### {st.session_state.get('plan_name', plan.get('plan_name', '未命名計畫'))}")
    st.write(st.session_state.get("plan_goal", plan.get("plan_goal", "尚未設定計畫目標。")))
    st.markdown("---")
    st.write(f"**開始日期**：{plan.get('start_date', '未填')}")
    st.write(f"**結束日期**：{plan.get('end_date', '未填')}")
    st.write(f"**每天偏好的科目數量**：{plan.get('preferred_subject_count', '無偏好')}")
    st.write(f"**科目數量**：{len(plan.get('subjects', []))}")
    st.write(f"**固定行程數量**：{len(plan.get('fixed_events', []))}")
    if st.session_state.get("monthly_plan"):
        st.write(f"**已產生天數**：{len(st.session_state['monthly_plan'])}")
    if st.session_state.get("daily_log"):
        st.markdown("### 最新每日打卡")
        st.write(st.session_state["daily_log"].get("daily_progress", ""))
        st.write(f"心情：{st.session_state['daily_log'].get('mood', '')}")
        st.write(f"建議：{st.session_state['daily_log'].get('recommendation', '')}")


def render_home_page() -> None:
    
    st.markdown("""
    <style>
    .menu-btn > button {
        width: 100%;
        border-radius: 8px;
        transition: all 0.3s;
        border: 1px solid #ddd;
        background: transparent;
        margin-bottom: 8px;
    }
    .menu-btn > button:hover {
        background-color: #4f84ff;
        color: white;
        border-color: #4f84ff;
    }
    </style>
    """, unsafe_allow_html=True)

    page_options = ["計劃頁面", "dashboard", "月計畫", "每日打卡與微調"]
    
    if "main_page" not in st.session_state:
        st.session_state["main_page"] = "計劃頁面" if not st.session_state.get("plan") else "dashboard"

    st.sidebar.markdown("### 主選單")
    for i, opt in enumerate(page_options):
        with st.sidebar:
            st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
            if st.button(opt, use_container_width=True, key=f"sidebar_main_menu_{i}_{opt}"):
                st.session_state["main_page"] = opt
            st.markdown('</div>', unsafe_allow_html=True)

    # Handle view_date query param from HTML calendar links
    qp_view = st.query_params.get("view_date")
    if qp_view:
        st.query_params.clear()
        st.session_state["cal_view_date"] = qp_view

    page = st.session_state["main_page"]

    cal_view_date = st.session_state.get("cal_view_date")

    if page != "每日打卡與微調":
        if cal_view_date:
            col_progress, col_main = st.columns([1, 3])
        else:
            col_progress, col_main = None, None
        
        if col_progress:
            with col_progress:
                st.markdown(f"### 📅 {cal_view_date}")
                st.markdown("當日讀書進度")
                schedule_data = st.session_state.get("app_state", {}).get("monthly_plan")
                if not schedule_data:
                    st.info("尚未生成排程計畫")
                else:
                    daily_schedule = [s for s in schedule_data if s.get("date") == cal_view_date]
                    if not daily_schedule:
                        st.write("這天沒有排定進度或為非學習日。")
                    else:
                        for item in daily_schedule:
                            attr = item.get("屬性", "")
                            block = item.get("學習區塊", "")
                            subj = item.get("科目", "")
                            target = item.get("目標進度", "")
                            color = "#4f84ff" if attr == "學習日" else "#ff9f43"
                            st.markdown(f"<div style='border-left:3px solid {color}; padding:4px 8px; margin-bottom:6px; font-size:13px;'><b>{block}</b><br/>{subj}：{target}</div>", unsafe_allow_html=True)
                if st.button("✕ 關閉", key="close_daily_view", use_container_width=True):
                    st.session_state["cal_view_date"] = None
                    st.rerun()
        
        container = col_main if col_main else st
        with container:
            st.title("讀書計畫安排助手")
            st.caption("先完成初始設定，生成完整計畫後，再根據每日情況進行打卡與微調。")
            if st.session_state.get("plan_name"):
                st.markdown(f"### {st.session_state['plan_name']}")

    if page == "計劃頁面":
        if col_main:
            with col_main:
                render_setup_page()
        else:
            render_setup_page()
    elif page == "dashboard":
        if col_main:
            with col_main:
                render_dashboard_page()
        else:
            render_dashboard_page()
    elif page == "月計畫":
        if col_main:
            with col_main:
                render_monthly_plan_page()
        else:
            render_monthly_plan_page()
    else:
        render_daily_checkin_page()


if __name__ == "__main__":
    render_home_page()
