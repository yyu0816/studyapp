from __future__ import annotations

from typing import Any
from datetime import date
import streamlit as st


def get_adjustment_message(pacing_feedback: int, time_loss: float, mood: int) -> str:
    if pacing_feedback >= 4:
        if time_loss >= 1.5:
            return "你的節奏偏快，建議放慢一點並減少當天的學習量，保留更多休息時間。"
        return "你的節奏偏快，建議放慢節奏並把重點任務縮減到 1~2 項。"

    if pacing_feedback <= 2:
        if mood <= 2:
            return "你目前狀態偏低，建議先做高收益的複習，再逐步增加今日的進度。"
        return "你的節奏偏慢，建議把今日的目標拆成更小的步驟，提升完成感。"

    if time_loss >= 2:
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
    
    if "daily_override_events" not in st.session_state:
        st.session_state["daily_override_events"] = {}
    overrides = st.session_state["daily_override_events"].get(today_str, [])

    if "daily_override_tasks" not in st.session_state:
        st.session_state["daily_override_tasks"] = {}
    daily_tasks_overrides = st.session_state["daily_override_tasks"].get(today_str, [])

    # Filter today's events
    today_events = [
        e for e in fixed_events 
        if today_weekday in e.get("weekdays", []) and e.get("show_on_calendar", True)
    ]
    today_events.extend(overrides)
    # Sort events by start time
    today_events.sort(key=lambda x: x.get("start", ""))

    col_timeline, col_main = st.columns([1, 2], gap="large")

    with col_timeline:
        st.markdown("### 🕒 時間軸")
        timeline_html = "<div style='margin-left: 55px; border-left: 3px solid #4f84ff; padding-left: 20px; margin-top: 20px; padding-bottom: 20px;'>"
        for hour in range(24):
            hour_str = f"{hour:02d}"
            hour_events = [e for e in today_events if e.get("start", "").startswith(hour_str + ":")]
            
            timeline_html += f"""
            <div style='position: relative; min-height: 35px;'>
                <div style='position: absolute; left: -85px; top: -2px; width: 50px; text-align: right; color: #aaa; font-size: 14px;'>{hour_str}:00</div>
                <div style='position: absolute; left: -24px; top: 3px; width: 8px; height: 8px; border-radius: 50%; background-color: #eee; border: 2px solid white;'></div>
            """
            
            for event in hour_events:
                emoji = event.get("emoji", "📌")
                color = event.get("display_color", event.get("color", "#4f84ff"))
                title = event.get("title", "未命名行程")
                start = event.get("start", "")
                end = event.get("end", "")
                
                timeline_html += f"""
                <div style='position: relative; margin-bottom: 15px; margin-top: 10px;'>
                    <div style='position: absolute; left: -85px; top: -2px; width: 50px; text-align: right; font-weight: bold; color: #666; font-size: 14px;'>{start}</div>
                    <div style='position: absolute; left: -29px; top: 2px; width: 14px; height: 14px; border-radius: 50%; background-color: {color}; border: 3px solid white;'></div>
                    <div style='background-color: #fff; padding: 12px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #e3e3e3;'>
                        <strong>{emoji} {title}</strong>
                        <div style='font-size: 12px; color: #888; margin-top: 4px;'>{start} - {end}</div>
                    </div>
                </div>
                """
            timeline_html += "</div>"
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)

    with col_main:
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.markdown("#### 📝 今日行程")
            with st.container(border=True):
                if today_events:
                    for event in today_events:
                        emoji = event.get("emoji", "📌")
                        title = event.get("title", "未命名行程")
                        start = event.get("start", "")
                        end = event.get("end", "")
                        st.markdown(f"**{emoji} {title}** ({start} - {end})")
                else:
                    st.markdown("今日無行程")
                
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("➕ 新增當日行程"):
                    new_title = st.text_input("行程標題", key="new_daily_title")
                    c_start, c_end = st.columns(2)
                    with c_start:
                        st.markdown("<div style='font-size: 14px;'>開始時間</div>", unsafe_allow_html=True)
                        s_c1, s_c2 = st.columns(2)
                        with s_c1:
                            new_start_h = st.selectbox("時", [f"{i:02d}" for i in range(24)], index=12, key="new_start_h", label_visibility="collapsed")
                        with s_c2:
                            new_start_m = st.selectbox("分", [f"{i:02d}" for i in range(60)], index=0, key="new_start_m", label_visibility="collapsed")
                    with c_end:
                        st.markdown("<div style='font-size: 14px;'>結束時間</div>", unsafe_allow_html=True)
                        e_c1, e_c2 = st.columns(2)
                        with e_c1:
                            new_end_h = st.selectbox("時", [f"{i:02d}" for i in range(24)], index=13, key="new_end_h", label_visibility="collapsed")
                        with e_c2:
                            new_end_m = st.selectbox("分", [f"{i:02d}" for i in range(60)], index=0, key="new_end_m", label_visibility="collapsed")
                            
                    new_emoji = st.selectbox("表符", ["📌", "📚", "📝", "🏃", "☕", "💻", "🧠"], key="new_emoji")
                    if st.button("確認新增", key="btn_add_event"):
                        if new_title.strip():
                            st.session_state["daily_override_events"].setdefault(today_str, []).append({
                                "title": new_title.strip(),
                                "start": f"{new_start_h}:{new_start_m}",
                                "end": f"{new_end_h}:{new_end_m}",
                                "emoji": new_emoji,
                                "color": "#ff9f43",
                                "display_color": "#ff9f43",
                                "show_on_calendar": True
                            })
                            st.rerun()

            st.markdown("#### 🎭 心情反饋")
            with st.container(border=True):
                motivation = st.radio("動力 (1: 低下 - 5: 充滿動力)", [1, 2, 3, 4, 5], index=2, horizontal=True, key="daily_motivation")
                mood = st.radio("心情 (1: 低落 - 5: 心情極佳)", [1, 2, 3, 4, 5], index=2, horizontal=True, key="daily_mood_score")

        with row1_col2:
            st.markdown("#### 📖 今日讀書進度")
            with st.container(border=True):
                monthly_plan = st.session_state.get("monthly_plan", [])
                today_plan = next((item for item in monthly_plan if item.get("date") == today_str), None)
                
                tasks = []
                if today_plan and today_plan.get("tasks"):
                    tasks.extend(today_plan.get("tasks"))
                tasks.extend(daily_tasks_overrides)

                if tasks:
                    for task in tasks:
                        st.checkbox(task, key=f"task_check_{task}")
                else:
                    st.markdown("今日無指定讀書內容")
                
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("➕ 新增當日進度"):
                    new_subject = st.text_input("科目", key="new_task_subject")
                    new_task_title = st.text_input("內容標題 (例: 小組作業、心得報告...)", key="new_task_title")
                    if st.button("確認新增", key="btn_add_task"):
                        if new_task_title.strip():
                            task_text = f"{new_subject.strip()}：{new_task_title.strip()}" if new_subject.strip() else new_task_title.strip()
                            st.session_state["daily_override_tasks"].setdefault(today_str, []).append(task_text)
                            st.rerun()

            st.markdown("#### ⚖️ 進度安排反饋")
            with st.container(border=True):
                amount_feedback = st.radio("分量回饋 (1: 太少/休息太多 - 5: 太多/休息太少)", [1, 2, 3, 4, 5], index=2, horizontal=True, key="daily_amount")
                pacing_feedback = st.radio("節奏回饋 (1: 太慢 - 5: 太快)", [1, 2, 3, 4, 5], index=2, horizontal=True, key="daily_pacing_score")
                
                if "show_time_loss" not in st.session_state:
                    st.session_state["show_time_loss"] = False
                
                if st.button("新增意外損失時間", key="btn_show_time_loss"):
                    st.session_state["show_time_loss"] = True
                    st.rerun()

                time_loss = 0.0
                if st.session_state["show_time_loss"]:
                    time_loss = st.number_input("意外損失時間（小時）", min_value=0.0, step=0.5, key="daily_time_loss")

        st.markdown("#### 🗒️ 記錄區與今日成果")
        with st.container(border=True):
            daily_progress = st.text_area(
                "詳細進度說明", 
                value=st.session_state.get("daily_log", {}).get("daily_progress", ""), 
                placeholder="例如：完成 60 頁數學與 20 頁英文", 
                height=100
            )
            notes = st.text_area(
                "備註", 
                value=st.session_state.get("daily_log", {}).get("notes", ""), 
                placeholder="例如：今天需要延後 30 分鐘的複習", 
                height=80
            )

        if st.button("💾 儲存今日打卡", use_container_width=True):
            daily_data = {
                "daily_progress": daily_progress,
                "mood_score": mood,
                "motivation_score": motivation,
                "amount_score": amount_feedback,
                "pacing_score": pacing_feedback,
                "time_loss": time_loss,
                "notes": notes,
            }
            daily_data["recommendation"] = get_adjustment_message(daily_data["pacing_score"], daily_data["time_loss"], daily_data["mood_score"])
            st.session_state["daily_log"] = daily_data
            st.success("今日打卡已更新！")
            
            st.info(f"💡 **今日建議**：\n{daily_data['recommendation']}")

    if st.session_state.get("plan_name"):
        st.markdown(f"---")
        st.markdown(f"### {st.session_state['plan_name']}")
