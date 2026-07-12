from __future__ import annotations

from typing import Any
from datetime import date
import streamlit as st


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


def render_daily_checkin_page() -> None:
    st.subheader("每日打卡與微調")
    if not st.session_state.get("plan"):
        st.info("請先完成初始設定。")
        return

    # Use today's date for timeline display
    today_str = date.today().strftime("%Y-%m-%d")
    weekday_map = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}
    today_weekday = weekday_map[date.today().weekday()]

    plan = st.session_state.get("plan", {})
    fixed_events = plan.get("fixed_events", [])
    
    # Filter today's events
    today_events = [
        e for e in fixed_events 
        if today_weekday in e.get("weekdays", []) and e.get("show_on_calendar", True)
    ]
    # Sort events by start time
    today_events.sort(key=lambda x: x.get("start", ""))

    col_timeline, col_main = st.columns([1, 2], gap="large")

    with col_timeline:
        st.markdown("### 🕒 時間軸 (今日行程)")
        if today_events:
            timeline_html = "<div style='border-left: 3px solid #4f84ff; padding-left: 15px; margin-left: 10px;'>"
            for event in today_events:
                emoji = event.get("emoji", "📌")
                color = event.get("display_color", event.get("color", "#4f84ff"))
                title = event.get("title", "未命名行程")
                start = event.get("start", "")
                end = event.get("end", "")
                timeline_html += f"""
                <div style='position: relative; margin-bottom: 20px;'>
                    <div style='position: absolute; left: -24px; top: 0; width: 14px; height: 14px; border-radius: 50%; background-color: {color}; border: 3px solid white;'></div>
                    <div style='font-size: 12px; color: #666;'>{start} - {end}</div>
                    <div style='background-color: #f4f7fb; padding: 10px; border-radius: 8px; margin-top: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>
                        <strong>{emoji} {title}</strong>
                    </div>
                </div>
                """
            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)
        else:
            st.info("今日無固定行程")

    with col_main:
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.markdown("#### 📝 今日行程")
            st.markdown("<div style='background-color: #fafafa; padding: 10px; border-radius: 8px; min-height: 150px;'>", unsafe_allow_html=True)
            # Find tasks for today if possible from monthly_plan
            monthly_plan = st.session_state.get("monthly_plan", [])
            today_plan = next((item for item in monthly_plan if item.get("date") == today_str), None)
            
            if today_plan and today_plan.get("tasks"):
                for task in today_plan.get("tasks", []):
                    st.checkbox(task, key=f"task_check_{task}")
            else:
                st.write("今日無指定讀書內容")
            st.markdown("</div>", unsafe_allow_html=True)

        with row1_col2:
            st.markdown("#### 📖 今日讀書進度")
            daily_progress = st.text_area(
                " ", 
                value=st.session_state.get("daily_log", {}).get("daily_progress", ""), 
                placeholder="例如：完成 60 頁數學與 20 頁英文", 
                label_visibility="collapsed",
                height=150
            )

        st.markdown("<br>", unsafe_allow_html=True)
        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.markdown("#### 🎭 心情反饋")
            mood = st.selectbox(
                " ",
                ["good", "neutral", "low", "very_low"],
                format_func=lambda value: {"good": "好", "neutral": "普通", "low": "低", "very_low": "很低"}.get(value, value),
                key="daily_mood",
                label_visibility="collapsed"
            )

        with row2_col2:
            st.markdown("#### ⚖️ 安排反饋")
            pacing_feedback = st.selectbox(
                " ",
                ["balanced", "too_fast", "too_slow"],
                format_func=lambda value: {"balanced": "剛剛好", "too_fast": "進度太多", "too_slow": "進度太少"}.get(value, value),
                key="daily_pacing",
                label_visibility="collapsed"
            )
            time_loss = st.number_input("意外時間損失（小時）", min_value=0.0, step=0.5, key="daily_time_loss")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🗒️ 記錄區")
        notes = st.text_area(
            " ", 
            value=st.session_state.get("daily_log", {}).get("notes", ""), 
            placeholder="例如：今天需要延後 30 分鐘的複習", 
            label_visibility="collapsed",
            height=100
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 儲存今日打卡", use_container_width=True):
            daily_data = {
                "daily_progress": daily_progress,
                "mood": mood,
                "energy": "medium", # Default energy as we simplified the form
                "time_loss": str(time_loss),
                "pacing_feedback": pacing_feedback,
                "notes": notes,
            }
            daily_data["recommendation"] = get_adjustment_message(daily_data["pacing_feedback"], daily_data["time_loss"], daily_data["mood"])
            st.session_state["daily_log"] = daily_data
            st.success("今日打卡已更新！")
            
            # Show recommendation instantly
            st.info(f"💡 **今日建議**：\n{daily_data['recommendation']}")

    if st.session_state.get("plan_name"):
        st.markdown(f"---")
        st.markdown(f"### {st.session_state['plan_name']}")
