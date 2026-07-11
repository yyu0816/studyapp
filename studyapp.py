from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st

app_state: dict[str, Any] = {
    "plan": None,
    "daily_log": None,
    "monthly_plan": None,
}


def parse_subject_entries(form_data: Any) -> list[dict[str, Any]]:
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
                "pages": int(page_value) if page_value.isdigit() and int(page_value) > 0 else 0,
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
    subject_lines = "<ul>" + "".join(
        f"<li>{item['name']}：{item['pages']} 頁，複習影片 {item['review_video']} 次，模擬考 {item['mock_exam']} 次，複習日期 {item['review_date'] or '未填'}，模擬考日期 {item['mock_date'] or '未填'}</li>"
        for item in plan_data.get("subjects", [])
    ) + "</ul>"

    schedule_lines = "<ul>" + "".join(
        f"<li>{item['title']}：{item['day']} {item['start']} ～ {item['end']}（{item['color']}）</li>" for item in plan_data.get("fixed_events", [])
    ) + "</ul>"

    return f"""
    <section style="padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.08); margin-bottom: 12px;">
      <h3>初始設定摘要</h3>
      <p><strong>開始日期：</strong> {plan_data.get('start_date', '未填')}</p>
      <p><strong>總共天數：</strong> {plan_data.get('timeframe_days', '未填')}</p>
      <p><strong>每天偏好的科目數量：</strong> {plan_data.get('preferred_subject_count', '未填')}</p>
      <p><strong>科目與工作量：</strong></p>
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


def collect_plan_and_daily_data(form_data: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    def get_list_field(name: str) -> list[Any]:
        if hasattr(form_data, "getlist"):
            values = form_data.getlist(name)
        else:
            values = form_data.get(name, []) or []
        if not isinstance(values, list):
            values = [values]
        return values

    def get_field(name: str) -> Any:
        if hasattr(form_data, "get"):
            return form_data.get(name, "")
        return ""

    event_titles = get_list_field("event_title")
    event_days = get_list_field("event_day")
    event_starts = get_list_field("event_start")
    event_ends = get_list_field("event_end")
    event_colors = get_list_field("event_color")

    if not event_titles and get_field("schedule_day"):
        event_titles = ["固定學習"]
    if not event_days and get_field("schedule_day"):
        event_days = get_list_field("schedule_day")
    if not event_starts and get_field("schedule_start"):
        event_starts = get_list_field("schedule_start")
    if not event_ends and get_field("schedule_end"):
        event_ends = get_list_field("schedule_end")
    if not event_colors:
        event_colors = ["#4f84ff"]

    plan_data: dict[str, Any] = {
        "timeframe": get_field("timeframe") or get_field("timeframe_days"),
        "start_date": get_field("start_date"),
        "timeframe_days": int(get_field("timeframe_days") or 0),
        "preferred_subject_count": int(get_field("preferred_subject_count") or 0),
        "subjects": parse_subject_entries(form_data),
        "fixed_events": [
            {
                "title": event_titles[index] if index < len(event_titles) else "",
                "day": event_days[index] if index < len(event_days) else "",
                "start": event_starts[index] if index < len(event_starts) else "",
                "end": event_ends[index] if index < len(event_ends) else "",
                "color": event_colors[index] if index < len(event_colors) else "#4f84ff",
            }
            for index in range(
                max(len(event_titles), len(event_days), len(event_starts), len(event_ends), len(event_colors))
            )
        ],
        "daily_routine": {
            "weekday_wake": get_field("weekday_wake"),
            "weekday_sleep": get_field("weekday_sleep"),
            "weekend_wake": get_field("weekend_wake"),
            "weekend_sleep": get_field("weekend_sleep"),
        },
    }

    daily_data: dict[str, Any] = {
        "daily_progress": get_field("daily_progress"),
        "mood": get_field("mood"),
        "energy": get_field("energy"),
        "time_loss": get_field("time_loss"),
        "pacing_feedback": get_field("pacing_feedback"),
        "notes": get_field("notes"),
    }
    daily_data["recommendation"] = get_adjustment_message(
        daily_data["pacing_feedback"],
        daily_data["time_loss"],
        daily_data["mood"],
    )
    return plan_data, daily_data


def build_monthly_plan(plan_data: dict[str, Any]) -> list[dict[str, Any]]:
    start_date = datetime.strptime(plan_data.get("start_date", date.today().strftime("%Y-%m-%d")), "%Y-%m-%d").date()
    total_days = int(plan_data.get("timeframe_days", 0) or 0)
    preferred_count = int(plan_data.get("preferred_subject_count", 0) or 0)
    subjects = plan_data.get("subjects", []) or []

    monthly_plan: list[dict[str, Any]] = []
    for offset in range(total_days):
        current_date = start_date + timedelta(days=offset)
        selected_subjects = [item["name"] for item in subjects[: max(1, min(preferred_count, len(subjects)))]]
        monthly_plan.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": current_date.strftime("%a"),
                "subjects": selected_subjects,
                "target_progress": "完成指定頁數",
            }
        )
    return monthly_plan


def render_home_page() -> None:
    st.set_page_config(page_title="讀書計畫安排助手", page_icon="📚", layout="wide")
    st.title("讀書計畫安排助手")
    st.caption("先完成初始設定，生成完整計畫後，再根據每日情況進行打卡與微調。")

    if not app_state.get("plan"):
        with st.form("study_plan_form"):
            st.subheader("1. 初始設定")
            start_date = st.date_input("開始日期", value=date.today())
            timeframe_days = st.number_input("總共天數", min_value=1, max_value=365, step=1, value=30)
            preferred_subject_count = st.number_input("每天偏好的科目數量", min_value=1, max_value=10, step=1, value=2)

            st.subheader("科目與工作量")
            subject_count = st.number_input("科目數量", min_value=1, max_value=10, step=1, value=st.session_state.get("subject_count", 1))
            st.session_state["subject_count"] = subject_count

            subject_names: list[str] = []
            subject_pages: list[str] = []
            subject_review: list[str] = []
            subject_mock: list[str] = []
            subject_review_dates: list[str] = []
            subject_mock_dates: list[str] = []
            for index in range(subject_count):
                cols = st.columns([2, 1, 1, 1, 1, 1])
                with cols[0]:
                    name = st.text_input(f"科目名稱 {index + 1}", key=f"subject_name_{index}")
                with cols[1]:
                    pages = st.number_input(f"需讀頁數 {index + 1}", min_value=1, step=1, key=f"pages_required_{index}")
                with cols[2]:
                    review = st.number_input(f"複習影片 {index + 1}", min_value=0, step=1, key=f"review_video_{index}")
                with cols[3]:
                    review_date = st.date_input(f"複習日期 {index + 1}", key=f"review_date_{index}")
                with cols[4]:
                    mock = st.number_input(f"模擬考 {index + 1}", min_value=0, step=1, key=f"mock_exam_{index}")
                with cols[5]:
                    mock_date = st.date_input(f"模擬考日期 {index + 1}", key=f"mock_date_{index}")
                if name:
                    subject_names.append(name)
                    subject_pages.append(str(int(pages)))
                    subject_review.append(str(int(review)))
                    subject_mock.append(str(int(mock)))
                    subject_review_dates.append(review_date.strftime("%Y-%m-%d"))
                    subject_mock_dates.append(mock_date.strftime("%Y-%m-%d"))

            st.subheader("固定行程")
            event_count = st.number_input("固定行程數量", min_value=1, max_value=10, step=1, value=st.session_state.get("event_count", 1))
            st.session_state["event_count"] = event_count
            event_titles: list[str] = []
            event_days: list[str] = []
            event_starts: list[str] = []
            event_ends: list[str] = []
            event_colors: list[str] = []
            for index in range(event_count):
                cols = st.columns([2, 1, 1, 1, 1])
                with cols[0]:
                    event_titles.append(st.text_input(f"標題 {index + 1}", key=f"event_title_{index}"))
                with cols[1]:
                    event_days.append(st.text_input(f"星期 / 日期 {index + 1}", key=f"event_day_{index}"))
                with cols[2]:
                    event_starts.append(st.text_input(f"開始時間 {index + 1}", key=f"event_start_{index}"))
                with cols[3]:
                    event_ends.append(st.text_input(f"結束時間 {index + 1}", key=f"event_end_{index}"))
                with cols[4]:
                    event_colors.append(st.selectbox(f"顏色 {index + 1}", ["#4f84ff", "#7b5cff", "#ff6b6b", "#2ecc71"], key=f"event_color_{index}"))

            st.subheader("每日作息")
            weekday_wake = st.text_input("平日起床", placeholder="07:00")
            weekday_sleep = st.text_input("平日睡覺", placeholder="23:30")
            weekend_wake = st.text_input("假日起床", placeholder="08:30")
            weekend_sleep = st.text_input("假日睡覺", placeholder="00:30")

            submitted = st.form_submit_button("生成完整讀書計畫")
            if submitted:
                payload = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "timeframe_days": int(timeframe_days),
                    "preferred_subject_count": int(preferred_subject_count),
                    "subject_name": subject_names,
                    "pages_required": subject_pages,
                    "review_video": subject_review,
                    "mock_exam": subject_mock,
                    "review_date": subject_review_dates,
                    "mock_date": subject_mock_dates,
                    "event_title": event_titles,
                    "event_day": event_days,
                    "event_start": event_starts,
                    "event_end": event_ends,
                    "event_color": event_colors,
                    "weekday_wake": weekday_wake,
                    "weekday_sleep": weekday_sleep,
                    "weekend_wake": weekend_wake,
                    "weekend_sleep": weekend_sleep,
                }
                plan_data, daily_data = collect_plan_and_daily_data(payload)
                app_state["plan"] = plan_data
                app_state["daily_log"] = daily_data
                app_state["monthly_plan"] = build_monthly_plan(plan_data)
                st.success("初始設定已完成，月計畫已建立")

    if app_state.get("plan"):
        st.subheader("月計畫")
        for item in app_state["monthly_plan"] or []:
            with st.expander(f"{item['date']} {item['day_name']}"):
                st.write(f"今日要讀：{', '.join(item['subjects']) or '請補充科目'}")
                st.write(f"目標：{item['target_progress']}")

        st.subheader("2. 每日打卡或微調")
        daily_progress = st.text_area("今日讀書進度", placeholder="例如：完成 60 頁數學與 20 頁英文")
        mood = st.selectbox(
            "心情與精力",
            ["good", "neutral", "low", "very_low"],
            format_func=lambda value: {"good": "好", "neutral": "普通", "low": "低", "very_low": "很低"}.get(value, value),
        )
        energy = st.selectbox(
            "能量等級",
            ["high", "medium", "low"],
            format_func=lambda value: {"high": "高", "medium": "中", "low": "低"}.get(value, value),
        )
        time_loss = st.number_input("意外時間損失（小時）", min_value=0.0, step=0.5)
        pacing_feedback = st.selectbox(
            "節奏回饋",
            ["balanced", "too_fast", "too_slow"],
            format_func=lambda value: {"balanced": "剛剛好", "too_fast": "進度太多", "too_slow": "進度太少"}.get(value, value),
        )
        notes = st.text_area("備註", placeholder="例如：今天需要延後 30 分鐘的複習")

        if st.button("儲存今日打卡"):
            daily_data = {
                "daily_progress": daily_progress,
                "mood": mood,
                "energy": energy,
                "time_loss": str(time_loss),
                "pacing_feedback": pacing_feedback,
                "notes": notes,
            }
            daily_data["recommendation"] = get_adjustment_message(
                daily_data["pacing_feedback"],
                daily_data["time_loss"],
                daily_data["mood"],
            )
            app_state["daily_log"] = daily_data
            st.success("今日打卡已更新")

        if app_state.get("daily_log"):
            st.subheader("今日建議")
            st.write(app_state["daily_log"].get("recommendation", ""))


def main() -> None:
    render_home_page()


if __name__ == "__main__":
    main()
