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
from pathlib import Path
import importlib.util
import sys


def _import_monthly_plan_renderer():
    script_dir = Path(__file__).resolve().parent
    parent_dir = script_dir.parent
    for candidate in (script_dir, parent_dir):
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

    try:
        from pages.monthlyplan import render_monthly_plan_page
        return render_monthly_plan_page
    except ModuleNotFoundError as err:
        if err.name != "pages.monthlyplan":
            raise

    try:
        from studyapp.pages.monthlyplan import render_monthly_plan_page
        return render_monthly_plan_page
    except ModuleNotFoundError as err:
        if err.name != "studyapp.pages.monthlyplan":
            raise

    module_path = Path(__file__).resolve().parent / "pages" / "monthlyplan.py"
    if not module_path.exists():
        raise FileNotFoundError(f"Cannot find monthlyplan module at {module_path}")
    spec = importlib.util.spec_from_file_location("pages.monthlyplan", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load monthlyplan module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.render_monthly_plan_page


render_monthly_plan_page = _import_monthly_plan_renderer()

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
    {"name": "藍色", "value": "#4f84ff"},
    {"name": "紫色", "value": "#7b5cff"},
    {"name": "紅色", "value": "#ff6b6b"},
    {"name": "綠色", "value": "#2ecc71"},
    {"name": "橙色", "value": "#ff9f43"},
]
EMOJI_OPTIONS = ["📚", "📝", "🕒", "🏫", "🎯", "💡", "☕", "🛌", "🏃", "🎒"]


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


def get_adjustment_message(pacing_feedback: str, time_loss: str, mood: str) -> str:
    feedback = pacing_feedback or "balanced"
    loss = float(time_loss) if str(time_loss).replace(".", "", 1).isdigit() else 0

    if feedback == "too_fast":
        if loss >= 1.5:
            return "你的節奏偏快，建議放慢一點並減少當天的學習量，保留更多休息時間。"
        return "你的節奏偏快，建議放慢節奏並把重點任務縮減到 1~2 項。"

    if feedback == "too_slow":
        if mood in {"low", "very_low"}:
            return "你目前狀態偏低，建議先做高收益的複習，再逐步增加今日的進度。"
        return "你的節奏偏慢，建議把今日的目標拆成更小的步驟，提升完成感。"

    if loss >= 2:
        return "今天意外損失了不少時間，建議把明天的安排再留出緩衝時段。"

    return "目前節奏還算穩定，保持每日小步進展即可。"


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
    daily_data["recommendation"] = get_adjustment_message(
        daily_data["pacing_feedback"],
        daily_data["time_loss"],
        daily_data["mood"],
    )
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
                    if st.button("刪除參考書", key=f"delete_material_{idx}_{mid}"):
                        del st.session_state["subjects"][idx]["materials"][mid]
                        return
            if st.button("新增教材／材料", key=f"add_material_{idx}"):
                st.session_state["subjects"][idx]["materials"].append({"name": "", "type": "課本", "quantity": 1})
            weekdays_value = st.multiselect("希望安排在的星期", WEEKDAY_OPTIONS, default=subject.get("weekdays", []), key=f"subject_{idx}_weekdays")
            st.session_state["subjects"][idx]["weekdays"] = weekdays_value
            if st.button("刪除科目", key=f"delete_subject_{idx}") and len(st.session_state["subjects"]) > 1:
                st.session_state["subjects"].pop(idx)
                return
        st.divider()

    if st.button("新增科目"):
        st.session_state["subjects"].append({"name": "", "materials": [{"name": "", "type": "課本", "quantity": 1}], "weekdays": []})

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
            start_value = st.text_input("開始時間", value=event.get("start", ""), key=f"event_start_{idx}")
            end_value = st.text_input("結束時間", value=event.get("end", ""), key=f"event_end_{idx}")
            color_option = st.selectbox(
                "顏色",
                options=COLOR_OPTIONS,
                format_func=lambda option: option["name"] if isinstance(option, dict) else option,
                index=next((index for index, option in enumerate(COLOR_OPTIONS) if option["value"] == event.get("display_color") or option["value"] == event.get("color")), 0),
                key=f"event_color_{idx}",
            )
            emoji_option = st.selectbox(
                "表情符號",
                options=EMOJI_OPTIONS,
                index=EMOJI_OPTIONS.index(event.get("emoji", EMOJI_OPTIONS[0])) if event.get("emoji") in EMOJI_OPTIONS else 0,
                key=f"event_emoji_{idx}",
            )
            show_on_calendar = st.checkbox("顯示在月曆", value=bool(event.get("show_on_calendar", True)), key=f"event_show_{idx}")
            use_custom_color = st.checkbox("使用自訂顏色或色號", value=bool(event.get("custom_color", False)), key=f"event_custom_{idx}")
            custom_color_value = None
            if use_custom_color:
                custom_color_value = st.color_picker("自訂顏色", value=event.get("display_color") or event.get("color") or "#4f84ff", key=f"event_custom_color_{idx}")
            if st.button("刪除行程", key=f"delete_event_{idx}"):
                st.session_state["fixed_events"].pop(idx)
                return
            st.session_state["fixed_events"][idx] = {
                "title": title_value,
                "weekdays": weekdays_value,
                "start": start_value,
                "end": end_value,
                "emoji": emoji_option,
                "color": custom_color_value or (color_option["value"] if isinstance(color_option, dict) else color_option),
                "display_color": custom_color_value or (color_option["value"] if isinstance(color_option, dict) else color_option),
                "show_on_calendar": show_on_calendar,
                "custom_color": use_custom_color,
            }
        st.divider()

    if st.button("新增行程"):
        st.session_state["fixed_events"].append({"title": "", "weekdays": [], "start": "", "end": "", "emoji": "📚", "color": "#4f84ff", "display_color": "#4f84ff", "show_on_calendar": True, "custom_color": False})

    st.subheader("每日作息")
    weekday_wake = st.text_input("平日起床", value=st.session_state.get("weekday_wake", "07:00"), key="weekday_wake")
    weekday_sleep = st.text_input("平日睡覺", value=st.session_state.get("weekday_sleep", "23:30"), key="weekday_sleep")
    weekend_wake = st.text_input("假日起床", value=st.session_state.get("weekend_wake", "08:30"), key="weekend_wake")
    weekend_sleep = st.text_input("假日睡覺", value=st.session_state.get("weekend_sleep", "00:30"), key="weekend_sleep")

    if st.button("生成完整讀書計畫"):
        if end_date < start_date:
            st.error("結束日期不能早於開始日期。")
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
        }
        plan_data, daily_data = collect_plan_and_daily_data(payload)
        st.session_state["plan"] = plan_data
        st.session_state["monthly_plan"] = build_monthly_plan(plan_data)
        st.session_state["main_page"] = "月計畫"
        st.success("初始設定已完成，月計畫已建立。")


# The monthly plan page rendering is implemented in pages/monthlyplan.py


def render_daily_checkin_page() -> None:
    st.subheader("2. 每日打卡或微調")
    if not st.session_state.get("plan"):
        st.info("請先完成初始設定。")
        return

    daily_progress = st.text_area("今日讀書進度", value=st.session_state.get("daily_log", {}).get("daily_progress", ""), placeholder="例如：完成 60 頁數學與 20 頁英文")
    mood = st.selectbox(
        "心情與精力",
        ["good", "neutral", "low", "very_low"],
        format_func=lambda value: {"good": "好", "neutral": "普通", "low": "低", "very_low": "很低"}.get(value, value),
        key="daily_mood",
    )
    energy = st.selectbox(
        "能量等級",
        ["high", "medium", "low"],
        format_func=lambda value: {"high": "高", "medium": "中", "low": "低"}.get(value, value),
        key="daily_energy",
    )
    time_loss = st.number_input("意外時間損失（小時）", min_value=0.0, step=0.5, key="daily_time_loss")
    pacing_feedback = st.selectbox(
        "節奏回饋",
        ["balanced", "too_fast", "too_slow"],
        format_func=lambda value: {"balanced": "剛剛好", "too_fast": "進度太多", "too_slow": "進度太少"}.get(value, value),
        key="daily_pacing",
    )
    notes = st.text_area("備註", value=st.session_state.get("daily_log", {}).get("notes", ""), placeholder="例如：今天需要延後 30 分鐘的複習")

    if st.button("儲存今日打卡"):
        daily_data = {
            "daily_progress": daily_progress,
            "mood": mood,
            "energy": energy,
            "time_loss": str(time_loss),
            "pacing_feedback": pacing_feedback,
            "notes": notes,
        }
        daily_data["recommendation"] = get_adjustment_message(daily_data["pacing_feedback"], daily_data["time_loss"], daily_data["mood"])
        st.session_state["daily_log"] = daily_data
        st.success("今日打卡已更新")

    if st.session_state.get("plan_name"):
        st.markdown(f"### {st.session_state['plan_name']}")
    if st.session_state.get("daily_log"):
        st.markdown("### 今日建議")
        st.write(st.session_state["daily_log"].get("recommendation", ""))


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
    st.set_page_config(page_title="讀書計畫安排助手", page_icon="📚", layout="wide")
    st.title("讀書計畫安排助手")
    st.caption("先完成初始設定，生成完整計畫後，再根據每日情況進行打卡與微調。")

    page_options = ["計劃頁面", "dashboard", "月計畫", "每日打卡與微調"]
    default_index = page_options.index(st.session_state.get("main_page", "計劃頁面")) if st.session_state.get("main_page") in page_options else (0 if not st.session_state.get("plan") else 1)
    page = st.sidebar.selectbox("主選單", page_options, index=default_index, key="page_selection")
    st.session_state["main_page"] = page

    if st.session_state.get("plan_name"):
        st.markdown(f"### {st.session_state['plan_name']}")

    if page == "計劃頁面":
        render_setup_page()
    elif page == "dashboard":
        render_dashboard_page()
    elif page == "月計畫":
        render_monthly_plan_page()
    else:
        render_daily_checkin_page()


def main() -> None:
    _initialize_session_state()
    render_home_page()


if __name__ == "__main__":
    render_home_page()

st.write("---")
st.write("程式碼成功執行到最後一行了！")
