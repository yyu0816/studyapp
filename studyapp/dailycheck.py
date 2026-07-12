from __future__ import annotations

from typing import Any
from datetime import date
import streamlit as st

# Full shared emoji library (must match studyapp.py EMOJI_OPTIONS)
EMOJI_OPTIONS = [
    "📚", "📝", "🕒", "🏫", "🎯", "💡", "☕", "🛌", "🏃", "🎒",
    "😀", "😎", "🤔", "😴", "💪", "🙌", "✨", "🔥", "💯", "🎉",
    "📖", "✏️", "📐", "🔬", "💻", "🧠", "🗓️", "✅", "❌", "📌",
    "🍎", "🍔", "🥤", "🎵", "🎧", "🎨", "⚽", "🏀", "🎮", "🎬",
    "🚗", "🚌", "🚆", "✈️", "🏠", "🏢", "🏥", "🏦", "🛒", "🌲",
    "🏐", "🚿", "🏊", "🤸", "⚾", "🎾", "🧘", "🍜", "🧃", "📺",
]

COLOR_OPTIONS = [
    {"name": "藍色",  "value": "#4f84ff"},
    {"name": "紫色",  "value": "#7b5cff"},
    {"name": "紅色",  "value": "#ff6b6b"},
    {"name": "綠色",  "value": "#2ecc71"},
    {"name": "橙色",  "value": "#ff9f43"},
    {"name": "粉色",  "value": "#fd79a8"},
    {"name": "深藍",  "value": "#0652DD"},
    {"name": "深綠",  "value": "#009432"},
]


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


def _time_to_minutes(h: str, m: str) -> int:
    return int(h) * 60 + int(m)


def render_daily_checkin_page() -> None:
    st.subheader("每日打卡與微調")
    if not st.session_state.get("plan"):
        st.info("請先完成初始設定。")
        return

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

    # time_loss records: list of {"start": "HH:MM", "end": "HH:MM", "minutes": N, "reason": "..."}
    if "time_loss_records" not in st.session_state:
        st.session_state["time_loss_records"] = {}
    time_loss_records = st.session_state["time_loss_records"].get(today_str, [])

    # Filter today's fixed events
    today_events = [
        e for e in fixed_events
        if today_weekday in e.get("weekdays", []) and e.get("show_on_calendar", True)
    ]
    today_events.extend(overrides)
    today_events.sort(key=lambda x: x.get("start", ""))

    # ── Timeline ──────────────────────────────────────────────────────────────
    col_timeline, col_main = st.columns([1, 2], gap="large")

    with col_timeline:
        st.markdown("### 🕒 時間軸")

        # Build a map: hour (int) -> list of events starting in that hour
        hour_event_map: dict[int, list] = {h: [] for h in range(24)}
        for event in today_events:
            start_str = event.get("start", "")
            try:
                h = int(start_str.split(":")[0])
                if 0 <= h < 24:
                    hour_event_map[h].append(event)
            except (ValueError, IndexError):
                pass

        timeline_html = (
            "<div style='margin-left: 60px; border-left: 3px solid #4f84ff; "
            "padding-left: 16px; margin-top: 20px; padding-bottom: 20px;'>"
        )
        for hour in range(24):
            hour_str = f"{hour:02d}"
            hour_events = hour_event_map[hour]

            # Hour tick mark — always shown, sits to the left of the line
            timeline_html += (
                f"<div style='position: relative; min-height: 44px;'>"
                f"<div style='position: absolute; left: -88px; top: 0; width: 56px; "
                f"text-align: right; color: #bbb; font-size: 13px; line-height: 1;'>"
                f"{hour_str}:00</div>"
                f"<div style='position: absolute; left: -21px; top: 4px; width: 10px; height: 10px; "
                f"border-radius: 50%; background-color: #dde; border: 2px solid white;'></div>"
            )

            # Events starting this hour are rendered inside their own block
            for event in hour_events:
                emoji = event.get("emoji", "📌")
                color = event.get("display_color", event.get("color", "#4f84ff"))
                title = event.get("title", "未命名行程")
                start = event.get("start", "")
                end = event.get("end", "")

                timeline_html += (
                    f"<div style='position: relative; margin-bottom: 12px; margin-top: 8px;'>"
                    # event time label — shifted further left so it doesn't overlap the line tick
                    f"<div style='position: absolute; left: -88px; top: 0; width: 56px; "
                    f"text-align: right; font-weight: bold; color: #555; font-size: 12px; line-height: 1.2;'>"
                    f"{start}</div>"
                    # coloured dot on the line
                    f"<div style='position: absolute; left: -26px; top: 4px; width: 14px; height: 14px; "
                    f"border-radius: 50%; background-color: {color}; border: 2px solid white; "
                    f"box-shadow: 0 0 0 2px {color}33;'></div>"
                    # card
                    f"<div style='background-color: {color}22; border-left: 4px solid {color}; "
                    f"padding: 8px 10px; border-radius: 6px;'>"
                    f"<strong>{emoji} {title}</strong>"
                    f"<div style='font-size: 11px; color: #777; margin-top: 2px;'>{start} – {end}</div>"
                    f"</div></div>"
                )

            timeline_html += "</div>"

        timeline_html += "</div>"

        if hasattr(st, "html"):
            st.html(timeline_html)
        else:
            st.markdown(timeline_html, unsafe_allow_html=True)

    # ── Main Area ─────────────────────────────────────────────────────────────
    with col_main:
        row1_col1, row1_col2 = st.columns(2)

        # ── 今日行程 ─────────────────────────────────────────────────────────
        with row1_col1:
            st.markdown("#### 📝 今日行程")
            with st.container(border=True):
                if today_events:
                    for event in today_events:
                        emoji = event.get("emoji", "📌")
                        title = event.get("title", "未命名行程")
                        start = event.get("start", "")
                        end = event.get("end", "")
                        st.markdown(f"**{emoji} {title}** ({start} – {end})")
                else:
                    st.markdown("今日無行程")

                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("➕ 新增當日行程"):
                    new_title = st.text_input("行程標題", key="new_daily_title")

                    # Start / End time pickers
                    c_start, c_end = st.columns(2)
                    with c_start:
                        st.markdown("**開始時間**")
                        s_h_col, s_m_col = st.columns(2)
                        with s_h_col:
                            new_start_h = st.selectbox(
                                "開始時", [f"{i:02d}" for i in range(24)],
                                index=8, key="new_start_h")
                        with s_m_col:
                            new_start_m = st.selectbox(
                                "開始分", [f"{i:02d}" for i in range(60)],
                                index=0, key="new_start_m")
                    with c_end:
                        st.markdown("**結束時間**")
                        e_h_col, e_m_col = st.columns(2)
                        with e_h_col:
                            new_end_h = st.selectbox(
                                "結束時", [f"{i:02d}" for i in range(24)],
                                index=9, key="new_end_h")
                        with e_m_col:
                            new_end_m = st.selectbox(
                                "結束分", [f"{i:02d}" for i in range(60)],
                                index=0, key="new_end_m")

                    st.markdown(
                        f"⏱ 預覽：**{new_start_h}:{new_start_m}** → **{new_end_h}:{new_end_m}**"
                    )

                    # Emoji picker (full library)
                    new_emoji = st.selectbox("表符", EMOJI_OPTIONS, index=0, key="new_emoji")

                    # Background colour picker
                    new_color_option = st.selectbox(
                        "背景色",
                        options=COLOR_OPTIONS,
                        format_func=lambda o: o["name"],
                        index=0,
                        key="new_event_color",
                    )
                    use_custom_new_color = st.checkbox("使用自訂顏色", key="new_event_use_custom_color")
                    new_color_value = new_color_option["value"]
                    if use_custom_new_color:
                        new_color_value = st.color_picker(
                            "自訂顏色", value=new_color_value, key="new_event_custom_color"
                        )

                    if st.button("確認新增", key="btn_add_event"):
                        if new_title.strip():
                            st.session_state["daily_override_events"].setdefault(today_str, []).append({
                                "title": new_title.strip(),
                                "start": f"{new_start_h}:{new_start_m}",
                                "end":   f"{new_end_h}:{new_end_m}",
                                "emoji": new_emoji,
                                "color": new_color_value,
                                "display_color": new_color_value,
                                "show_on_calendar": True,
                            })
                            st.rerun()

            # ── 心情反饋 ──────────────────────────────────────────────────────
            st.markdown("#### 🎭 心情反饋")
            with st.container(border=True):
                is_mood_submitted = st.session_state.get("mood_submitted", False)
                motivation = st.radio(
                    "動力 (1: 低下 - 5: 充滿動力)", [1, 2, 3, 4, 5],
                    index=2, horizontal=True, key="daily_motivation",
                    disabled=is_mood_submitted)
                mood = st.radio(
                    "心情 (1: 低落 - 5: 心情極佳)", [1, 2, 3, 4, 5],
                    index=2, horizontal=True, key="daily_mood_score",
                    disabled=is_mood_submitted)

                if not is_mood_submitted:
                    if st.button("確認送出", key="btn_submit_mood"):
                        # ── 確認提醒 ──────────────────────────────────
                        st.session_state["mood_pending_confirm"] = True
                        st.rerun()

                    if st.session_state.get("mood_pending_confirm"):
                        st.warning(
                            f"⚠️ 請確認填入數值是否正確：\n\n"
                            f"**動力**：{motivation}　**心情**：{mood}\n\n"
                            "確認後將無法修改。"
                        )
                        c_yes, c_no = st.columns(2)
                        with c_yes:
                            if st.button("✅ 確認", key="btn_mood_yes"):
                                st.session_state["mood_submitted"] = True
                                st.session_state["mood_pending_confirm"] = False
                                st.rerun()
                        with c_no:
                            if st.button("❌ 取消", key="btn_mood_no"):
                                st.session_state["mood_pending_confirm"] = False
                                st.rerun()
                else:
                    st.success("已送出心情與動力紀錄！")

        # ── 今日讀書進度 ──────────────────────────────────────────────────────
        with row1_col2:
            st.markdown("#### 📖 今日讀書進度")
            with st.container(border=True):
                monthly_plan = st.session_state.get("monthly_plan", [])
                today_plan = next(
                    (item for item in monthly_plan if item.get("date") == today_str), None
                )

                tasks: list[str] = []
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
                    new_task_title = st.text_input(
                        "內容標題 (例: 小組作業、心得報告...)", key="new_task_title"
                    )
                    if st.button("確認新增", key="btn_add_task"):
                        if new_task_title.strip():
                            task_text = (
                                f"{new_subject.strip()}：{new_task_title.strip()}"
                                if new_subject.strip()
                                else new_task_title.strip()
                            )
                            st.session_state["daily_override_tasks"].setdefault(today_str, []).append(task_text)
                            st.rerun()

            # ── 進度安排反饋 ──────────────────────────────────────────────────
            st.markdown("#### ⚖️ 進度安排反饋")
            with st.container(border=True):
                amount_feedback = st.radio(
                    "分量回饋 (1: 分量太少；5: 分量太多)",
                    [1, 2, 3, 4, 5], index=2, horizontal=True, key="daily_amount"
                )
                pacing_feedback = st.radio(
                    "節奏回饋 (1: 節奏太慢、休息太多；5: 節奏太快、休息太少)",
                    [1, 2, 3, 4, 5], index=2, horizontal=True, key="daily_pacing_score"
                )

                # ── 意外損失時間（多筆） ───────────────────────────────────────
                if "show_time_loss" not in st.session_state:
                    st.session_state["show_time_loss"] = False

                if st.button("新增意外損失時間", key="btn_show_time_loss"):
                    st.session_state["show_time_loss"] = True

                if st.session_state["show_time_loss"]:
                    with st.form("form_time_loss", clear_on_submit=True):
                        st.markdown("**新增一筆意外損失**")
                        fl_c1, fl_c2 = st.columns(2)
                        with fl_c1:
                            st.markdown("開始時間")
                            lsh_col, lsm_col = st.columns(2)
                            with lsh_col:
                                loss_start_h = st.selectbox(
                                    "開始時", [f"{i:02d}" for i in range(24)], key="loss_s_h")
                            with lsm_col:
                                loss_start_m = st.selectbox(
                                    "開始分", [f"{i:02d}" for i in range(60)], key="loss_s_m")
                        with fl_c2:
                            st.markdown("結束時間")
                            leh_col, lem_col = st.columns(2)
                            with leh_col:
                                loss_end_h = st.selectbox(
                                    "結束時", [f"{i:02d}" for i in range(24)], key="loss_e_h")
                            with lem_col:
                                loss_end_m = st.selectbox(
                                    "結束分", [f"{i:02d}" for i in range(60)], key="loss_e_m")
                        loss_reason = st.text_input("原因（選填）", key="loss_reason")

                        submitted = st.form_submit_button("新增這筆")
                        if submitted:
                            start_mins = _time_to_minutes(loss_start_h, loss_start_m)
                            end_mins   = _time_to_minutes(loss_end_h,   loss_end_m)
                            diff_mins  = end_mins - start_mins
                            if diff_mins <= 0:
                                diff_mins += 24 * 60
                            st.session_state["time_loss_records"].setdefault(today_str, []).append({
                                "start":   f"{loss_start_h}:{loss_start_m}",
                                "end":     f"{loss_end_h}:{loss_end_m}",
                                "minutes": diff_mins,
                                "reason":  loss_reason.strip(),
                            })
                            st.rerun()

                # Show existing records
                time_loss_records = st.session_state["time_loss_records"].get(today_str, [])
                if time_loss_records:
                    st.markdown("**已記錄的意外損失：**")
                    total_mins = 0
                    for i, rec in enumerate(time_loss_records):
                        mins = rec.get("minutes", 0)
                        total_mins += mins
                        reason_str = f"　原因：{rec['reason']}" if rec.get("reason") else ""
                        st.markdown(
                            f"- {rec['start']} → {rec['end']}　**{mins} 分鐘**{reason_str}"
                        )
                    total_h = total_mins // 60
                    total_m = total_mins % 60
                    st.info(f"⏱ 今日合計損失：**{total_h} 小時 {total_m} 分鐘**（{total_mins} 分鐘）")
                else:
                    total_mins = 0

                time_loss = round(total_mins / 60, 2)

        # ── 記錄區 ───────────────────────────────────────────────────────────
        st.markdown("#### 🗒️ 記錄區與今日成果")
        with st.container(border=True):
            is_daily_saved = st.session_state.get("daily_saved", False)
            daily_progress = st.text_area(
                "詳細進度說明",
                value=(st.session_state.get("daily_log") or {}).get("daily_progress", ""),
                placeholder="例如：完成 60 頁數學與 20 頁英文",
                height=100,
                disabled=is_daily_saved,
            )
            notes = st.text_area(
                "備註",
                value=(st.session_state.get("daily_log") or {}).get("notes", ""),
                placeholder="例如：今天需要延後 30 分鐘的複習",
                height=80,
                disabled=is_daily_saved,
            )

        if not is_daily_saved:
            if st.button("💾 儲存今日打卡", use_container_width=True):
                # Read current radio values safely
                motivation_val = st.session_state.get("daily_motivation", 3)
                mood_val = st.session_state.get("daily_mood_score", 3)
                daily_data = {
                    "daily_progress":  daily_progress,
                    "mood_score":      mood_val,
                    "motivation_score": motivation_val,
                    "amount_score":    amount_feedback,
                    "pacing_score":    pacing_feedback,
                    "time_loss":       time_loss,
                    "notes":           notes,
                }
                daily_data["recommendation"] = get_adjustment_message(
                    daily_data["pacing_score"],
                    daily_data["time_loss"],
                    daily_data["mood_score"],
                )
                st.session_state["daily_log"] = daily_data
                st.session_state["daily_saved"] = True
                st.rerun()
        else:
            st.success("今日打卡已儲存且鎖定！")
            st.info(f"💡 **今日建議**：\n{(st.session_state.get('daily_log') or {}).get('recommendation', '')}")
            if st.button("✏️ 編輯今日打卡", use_container_width=True):
                st.session_state["daily_saved"] = False
                st.rerun()

    if st.session_state.get("plan_name"):
        st.markdown("---")
        st.markdown(f"### {st.session_state['plan_name']}")
