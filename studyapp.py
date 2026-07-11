from __future__ import annotations

from typing import Any

import streamlit as st

app_state: dict[str, Any] = {
    "plan": None,
    "daily_log": None,
}


def parse_subject_entries(form_data: Any) -> list[dict[str, Any]]:
    if hasattr(form_data, "getlist"):
        names = form_data.getlist("subject_name")
        pages = form_data.getlist("pages_required")
        review_video = form_data.getlist("review_video")
        mock_exam = form_data.getlist("mock_exam")
    else:
        names = form_data.get("subject_name", []) or []
        pages = form_data.get("pages_required", []) or []
        review_video = form_data.get("review_video", []) or []
        mock_exam = form_data.get("mock_exam", []) or []

    if not isinstance(names, list):
        names = [names]
    if not isinstance(pages, list):
        pages = [pages]
    if not isinstance(review_video, list):
        review_video = [review_video]
    if not isinstance(mock_exam, list):
        mock_exam = [mock_exam]

    subjects: list[dict[str, Any]] = []
    for index, name in enumerate(names):
        cleaned_name = str(name).strip()
        if not cleaned_name:
            continue
        page_value = str(pages[index]).strip() if index < len(pages) else ""
        review_value = review_video[index] if index < len(review_video) else ""
        mock_value = mock_exam[index] if index < len(mock_exam) else ""
        subjects.append(
            {
                "name": cleaned_name,
                "pages": int(page_value) if page_value.isdigit() else 0,
                "review_video": bool(review_value),
                "mock_exam": bool(mock_value),
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
        f"<li>{item['name']}：{item['pages']} 頁，複習影片{'有' if item['review_video'] else '無'}，模擬考{'有' if item['mock_exam'] else '無'}</li>"
        for item in plan_data.get("subjects", [])
    ) + "</ul>"

    schedule_lines = "<ul>" + "".join(
        f"<li>{item['day']}：{item['start']} ～ {item['end']}</li>" for item in plan_data.get("fixed_schedule", [])
    ) + "</ul>"

    unavailable_lines = "<ul>" + "".join(
        f"<li>{item['day']}：{item['start']} ～ {item['end']}（{item['note']}）</li>" for item in plan_data.get("unavailable_hours", [])
    ) + "</ul>"

    return f"""
    <section style="padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.08); margin-bottom: 12px;">
      <h3>初始設定摘要</h3>
      <p><strong>讀書天數 / 考試倒數：</strong> {plan_data.get('timeframe', '未填')}</p>
      <p><strong>科目與工作量：</strong></p>
      {subject_lines}
      <p><strong>固定學習時段：</strong></p>
      {schedule_lines}
      <p><strong>每日作息：</strong> 平日 {plan_data.get('daily_routine', {}).get('weekday_wake', '未填')} 起床，{plan_data.get('daily_routine', {}).get('weekday_sleep', '未填')} 就寢；假日 {plan_data.get('daily_routine', {}).get('weekend_wake', '未填')} 起床，{plan_data.get('daily_routine', {}).get('weekend_sleep', '未填')} 就寢。</p>
      <p><strong>不可使用時段：</strong></p>
      {unavailable_lines}
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

    schedule_days = get_list_field("schedule_day")
    schedule_starts = get_list_field("schedule_start")
    schedule_ends = get_list_field("schedule_end")
    unavailable_days = get_list_field("unavailable_day")
    unavailable_starts = get_list_field("unavailable_start")
    unavailable_ends = get_list_field("unavailable_end")
    unavailable_notes = get_list_field("unavailable_note")

    plan_data: dict[str, Any] = {
        "timeframe": get_field("timeframe"),
        "subjects": parse_subject_entries(form_data),
        "fixed_schedule": [
            {
                "day": schedule_days[index] if index < len(schedule_days) else "",
                "start": schedule_starts[index] if index < len(schedule_starts) else "",
                "end": schedule_ends[index] if index < len(schedule_ends) else "",
            }
            for index in range(max(len(schedule_days), len(schedule_starts), len(schedule_ends)))
        ],
        "daily_routine": {
            "weekday_wake": get_field("weekday_wake"),
            "weekday_sleep": get_field("weekday_sleep"),
            "weekend_wake": get_field("weekend_wake"),
            "weekend_sleep": get_field("weekend_sleep"),
        },
        "unavailable_hours": [
            {
                "day": unavailable_days[index] if index < len(unavailable_days) else "",
                "start": unavailable_starts[index] if index < len(unavailable_starts) else "",
                "end": unavailable_ends[index] if index < len(unavailable_ends) else "",
                "note": unavailable_notes[index] if index < len(unavailable_notes) else "",
            }
            for index in range(max(len(unavailable_days), len(unavailable_starts), len(unavailable_ends), len(unavailable_notes)))
        ],
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


def render_home_page() -> None:
    st.set_page_config(page_title="讀書計畫安排助手", page_icon="📚", layout="wide")
    st.title("讀書計畫安排助手")
    st.caption("這個頁面幫你把「初始設定」與「每日打卡」整理在一起，讓你的學習計畫更可持續。")

    with st.form("study_plan_form"):
        st.subheader("1. 初始設定")
        timeframe = st.text_input("總共讀書天數 / 考試倒數", placeholder="例如：56 天")

        st.subheader("科目與工作量")
        subject_count = st.number_input("科目數量", min_value=1, max_value=10, step=1, value=st.session_state.get("subject_count", 1))
        st.session_state["subject_count"] = subject_count

        subject_names: list[str] = []
        subject_pages: list[str] = []
        subject_review: list[str] = []
        subject_mock: list[str] = []
        for index in range(subject_count):
            cols = st.columns([2, 1, 1, 1])
            with cols[0]:
                name = st.text_input(f"科目名稱 {index + 1}", key=f"subject_name_{index}")
            with cols[1]:
                pages = st.number_input(f"需讀頁數 {index + 1}", min_value=0, step=1, key=f"pages_required_{index}")
            with cols[2]:
                review = st.checkbox(f"複習影片 {index + 1}", key=f"review_video_{index}")
            with cols[3]:
                mock = st.checkbox(f"模擬考 {index + 1}", key=f"mock_exam_{index}")
            if name:
                subject_names.append(name)
                subject_pages.append(str(int(pages)))
                subject_review.append("on" if review else "")
                subject_mock.append("on" if mock else "")

        st.subheader("固定學習時段")
        schedule_count = st.number_input("固定時段數量", min_value=1, max_value=10, step=1, value=st.session_state.get("schedule_count", 1))
        st.session_state["schedule_count"] = schedule_count
        schedule_days: list[str] = []
        schedule_starts: list[str] = []
        schedule_ends: list[str] = []
        for index in range(schedule_count):
            cols = st.columns(3)
            with cols[0]:
                schedule_days.append(st.text_input(f"日期 / 週次 {index + 1}", key=f"schedule_day_{index}"))
            with cols[1]:
                schedule_starts.append(st.text_input(f"開始時間 {index + 1}", key=f"schedule_start_{index}"))
            with cols[2]:
                schedule_ends.append(st.text_input(f"結束時間 {index + 1}", key=f"schedule_end_{index}"))

        st.subheader("每日作息")
        weekday_wake = st.text_input("平日起床", placeholder="07:00")
        weekday_sleep = st.text_input("平日睡覺", placeholder="23:30")
        weekend_wake = st.text_input("假日起床", placeholder="08:30")
        weekend_sleep = st.text_input("假日睡覺", placeholder="00:30")

        st.subheader("不可使用時段")
        unavailable_count = st.number_input("不可使用時段數量", min_value=1, max_value=10, step=1, value=st.session_state.get("unavailable_count", 1))
        st.session_state["unavailable_count"] = unavailable_count
        unavailable_days: list[str] = []
        unavailable_starts: list[str] = []
        unavailable_ends: list[str] = []
        unavailable_notes: list[str] = []
        for index in range(unavailable_count):
            cols = st.columns(4)
            with cols[0]:
                unavailable_days.append(st.text_input(f"日期 / 時段 {index + 1}", key=f"unavailable_day_{index}"))
            with cols[1]:
                unavailable_starts.append(st.text_input(f"開始時間 {index + 1}", key=f"unavailable_start_{index}"))
            with cols[2]:
                unavailable_ends.append(st.text_input(f"結束時間 {index + 1}", key=f"unavailable_end_{index}"))
            with cols[3]:
                unavailable_notes.append(st.text_input(f"備註 {index + 1}", key=f"unavailable_note_{index}"))

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

        submitted = st.form_submit_button("儲存計畫與打卡")
        if submitted:
            payload = {
                "timeframe": timeframe,
                "subject_name": subject_names,
                "pages_required": subject_pages,
                "review_video": subject_review,
                "mock_exam": subject_mock,
                "schedule_day": schedule_days,
                "schedule_start": schedule_starts,
                "schedule_end": schedule_ends,
                "weekday_wake": weekday_wake,
                "weekday_sleep": weekday_sleep,
                "weekend_wake": weekend_wake,
                "weekend_sleep": weekend_sleep,
                "unavailable_day": unavailable_days,
                "unavailable_start": unavailable_starts,
                "unavailable_end": unavailable_ends,
                "unavailable_note": unavailable_notes,
                "daily_progress": daily_progress,
                "mood": mood,
                "energy": energy,
                "time_loss": str(time_loss),
                "pacing_feedback": pacing_feedback,
                "notes": notes,
            }
            plan_data, daily_data = collect_plan_and_daily_data(payload)
            app_state["plan"] = plan_data
            app_state["daily_log"] = daily_data
            st.success("計畫與打卡已儲存")
            st.subheader("計畫摘要")
            st.write(build_plan_summary(plan_data, daily_data), unsafe_allow_html=True)

    if app_state["plan"] and app_state["daily_log"]:
        st.subheader("上一筆摘要")
        st.write(build_plan_summary(app_state["plan"], app_state["daily_log"]), unsafe_allow_html=True)


def main() -> None:
    render_home_page()


if __name__ == "__main__":
    main()
