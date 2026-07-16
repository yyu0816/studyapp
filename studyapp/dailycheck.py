from __future__ import annotations

from typing import Any
from datetime import date, timedelta
import streamlit as st
import logic
from timeline_utils import render_timeline, get_contrast_color

# Full shared emoji library — kept in sync with studyapp.py EMOJI_OPTIONS
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

COLOR_OPTIONS = [
    {"name": "🔵 藍色", "value": "#4f84ff"},
    {"name": "🟣 紫色", "value": "#7b5cff"},
    {"name": "🔴 紅色", "value": "#ff6b6b"},
    {"name": "🟢 綠色", "value": "#2ecc71"},
    {"name": "🟠 橙色", "value": "#ff9f43"},
    {"name": "🟡 黃色", "value": "#f9ca24"},
    {"name": "⚪ 灰色", "value": "#636e72"},
    {"name": "🤍 深紅", "value": "#b71540"},
]


# The get_contrast_color logic has been moved to timeline_utils.py


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
    if not st.session_state.get("plan"):
        st.info("請先完成初始設定。")
        return

    if "view_date" not in st.session_state:
        st.session_state["view_date"] = date.today()

    today = st.session_state["view_date"]
    today_str = today.strftime("%Y-%m-%d")
    weekday_map = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}
    today_weekday = weekday_map[today.weekday()]

    plan = st.session_state.get("plan", {})
    end_date_str = plan.get("end_date")
    countdown_text = ""
    if end_date_str:
        try:
            from datetime import datetime
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            days_left = (end_date - today).days
            if days_left > 0:
                countdown_text = f"⏳ 距離目標還有 <b>{days_left}</b> 天"
            elif days_left == 0:
                countdown_text = "🎉 就是今天！"
            else:
                countdown_text = "計畫已結束"
        except:
            pass

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        with st.container(border=True):
            hc1, hc2, hc3 = st.columns([1, 6, 1])
            with hc1:
                if st.button("◀", key="prev_day", use_container_width=True):
                    st.session_state["view_date"] -= timedelta(days=1)
                    st.rerun()
            with hc2:
                st.markdown(f"<h3 style='text-align: center; margin-bottom: 0; margin-top: 0;'>📅 {today_str} ({today_weekday})</h3>", unsafe_allow_html=True)
                if countdown_text:
                    st.markdown(f"<p style='text-align: center; font-size: 1.1rem; color: #ff4b4b; margin-top: 5px; margin-bottom: 0;'>{countdown_text}</p>", unsafe_allow_html=True)
            with hc3:
                if st.button("▶", key="next_day", use_container_width=True):
                    st.session_state["view_date"] += timedelta(days=1)
                    st.rerun()

    with col_r:
        free_sessions = logic.calculate_daily_available_sessions(today, plan)
        st.metric("今日可安排讀書時間", f"{free_sessions} 小時")

    fixed_events = plan.get("fixed_events", [])

    if "daily_override_events" not in st.session_state:
        st.session_state["daily_override_events"] = {}
    overrides = st.session_state["daily_override_events"].get(today_str, [])

    if "daily_override_tasks" not in st.session_state:
        st.session_state["daily_override_tasks"] = {}
    daily_tasks_overrides = st.session_state["daily_override_tasks"].get(today_str, [])

    if "time_loss_records" not in st.session_state:
        st.session_state["time_loss_records"] = {}
    
    if "daily_modified_fixed" not in st.session_state:
        st.session_state["daily_modified_fixed"] = {}
    modified_fixed = st.session_state["daily_modified_fixed"].get(today_str, {})

    # Persist mood & motivation so they survive Streamlit reruns
    if "saved_motivation" not in st.session_state:
        st.session_state["saved_motivation"] = 3
    if "saved_mood" not in st.session_state:
        st.session_state["saved_mood"] = 3

    # Build today_events
    today_events = []
    
    # 1. Fixed events
    for f_idx, e in enumerate(fixed_events):
        if today_weekday in e.get("weekdays", []):
            if f_idx in modified_fixed:
                if not modified_fixed[f_idx].get("deleted"):
                    m_event = modified_fixed[f_idx].copy()
                    m_event["_is_fixed"] = True
                    m_event["_fixed_idx"] = f_idx
                    today_events.append(m_event)
            else:
                e_copy = e.copy()
                e_copy["_is_fixed"] = True
                e_copy["_fixed_idx"] = f_idx
                today_events.append(e_copy)
                
    # 2. Overrides (newly added daily events)
    for o_idx, e in enumerate(overrides):
        e_copy = e.copy()
        e_copy["_is_override"] = True
        e_copy["_override_idx"] = o_idx
        today_events.append(e_copy)

    today_events.sort(key=lambda x: x.get("start", ""))

    col_timeline, col_main = st.columns([1, 2], gap="large")
    with col_timeline:
        render_timeline(today_events)

    # ── Main Area ─────────────────────────────────────────────────────────────
    with col_main:
        row1_col1, row1_col2 = st.columns(2)

        # ── 今日行程 ─────────────────────────────────────────────────────────
        with row1_col1:
            st.markdown("#### 📝 今日行程")
            with st.container(border=True):
                if today_events:
                    for i, event in enumerate(today_events):
                        emoji = event.get("emoji", "📌")
                        title = event.get("title", "未命名行程")
                        start = event.get("start", "")
                        end   = event.get("end", "")

                        with st.expander(f"{emoji} **{title}** ({start}–{end})", expanded=False):
                            new_t = st.text_input("行程標題", value=title, key=f"edit_title_{i}")
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                st.markdown("開始時間")
                                eh1, em1 = st.columns(2)
                                with eh1:
                                    e_sh = st.selectbox("時", [f"{h:02d}" for h in range(24)],
                                        index=int(start.split(":")[0]) if start else 8,
                                        key=f"edit_sh_{i}")
                                with em1:
                                    e_sm = st.selectbox("分", [f"{m:02d}" for m in range(60)],
                                        index=int(start.split(":")[1]) if start and ":" in start else 0,
                                        key=f"edit_sm_{i}")
                            with ec2:
                                st.markdown("結束時間")
                                eh2, em2 = st.columns(2)
                                with eh2:
                                    e_eh = st.selectbox("時", [f"{h:02d}" for h in range(24)],
                                        index=int(end.split(":")[0]) if end else 9,
                                        key=f"edit_eh_{i}")
                                with em2:
                                    e_em = st.selectbox("分", [f"{m:02d}" for m in range(60)],
                                        index=int(end.split(":")[1]) if end and ":" in end else 0,
                                        key=f"edit_em_{i}")
                            
                            st.info(f"⏱ 預覽：{e_sh}:{e_sm} → {e_eh}:{e_em}")
                            
                            new_emoji_e = st.selectbox("表符", EMOJI_OPTIONS,
                                index=EMOJI_OPTIONS.index(emoji) if emoji in EMOJI_OPTIONS else 0,
                                key=f"edit_emoji_{i}")
                            
                            new_concurrent = st.checkbox("是否能和讀書計畫並行？", 
                                value=bool(event.get("concurrent_with_study", False)), 
                                key=f"edit_concurrent_{i}")

                            c_save, c_del = st.columns(2)
                            with c_save:
                                if st.button("💾 儲存修改", key=f"save_edit_{i}"):
                                    updated_event = {
                                        "title": new_t.strip(),
                                        "start": f"{e_sh}:{e_sm}",
                                        "end":   f"{e_eh}:{e_em}",
                                        "emoji": new_emoji_e,
                                        "color": event.get("color"),
                                        "display_color": event.get("display_color"),
                                        "concurrent_with_study": new_concurrent,
                                        "show_on_calendar": True
                                    }
                                    if event.get("_is_fixed"):
                                        st.session_state["daily_modified_fixed"].setdefault(today_str, {})[event["_fixed_idx"]] = updated_event
                                    else:
                                        st.session_state["daily_override_events"][today_str][event["_override_idx"]].update(updated_event)
                                    st.rerun()
                            with c_del:
                                if st.button("🗑️ 刪除此行程", key=f"del_override_{i}"):
                                    if event.get("_is_fixed"):
                                        st.session_state["daily_modified_fixed"].setdefault(today_str, {})[event["_fixed_idx"]] = {"deleted": True}
                                    else:
                                        st.session_state["daily_override_events"][today_str].pop(event["_override_idx"])
                                    st.rerun()
                else:
                    st.markdown("今日無行程")

                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("➕ 新增當日行程"):
                    new_title = st.text_input("行程標題", key="new_daily_title")

                    c_start, c_end = st.columns(2)
                    with c_start:
                        st.markdown("**開始時間**")
                        s_h_col, s_m_col = st.columns(2)
                        with s_h_col:
                            new_start_h = st.selectbox(
                                "開始-時", [f"{i:02d}" for i in range(24)],
                                index=8, key="new_start_h")
                        with s_m_col:
                            new_start_m = st.selectbox(
                                "開始-分", [f"{i:02d}" for i in range(60)],
                                index=0, key="new_start_m")
                    with c_end:
                        st.markdown("**結束時間**")
                        e_h_col, e_m_col = st.columns(2)
                        with e_h_col:
                            new_end_h = st.selectbox(
                                "結束-時", [f"{i:02d}" for i in range(24)],
                                index=9, key="new_end_h")
                        with e_m_col:
                            new_end_m = st.selectbox(
                                "結束-分", [f"{i:02d}" for i in range(60)],
                                index=0, key="new_end_m")

                    st.info(f"⏱ 預覽：{new_start_h}:{new_start_m} → {new_end_h}:{new_end_m}")

                    new_emoji = st.selectbox("表符", EMOJI_OPTIONS, index=0, key="new_emoji")

                    # Color picker with preview
                    new_color_option = st.selectbox(
                        "背景色", options=COLOR_OPTIONS,
                        format_func=lambda o: o["name"],
                        index=0, key="new_event_color",
                    )
                    new_color_value = new_color_option["value"]
                    st.markdown(
                        f"<div style='display:inline-block;width:22px;height:14px;"
                        f"border-radius:3px;background:{new_color_value};"
                        f"vertical-align:middle;margin-right:6px;'></div>"
                        f"<span style='font-size:13px;color:#555;'>{new_color_option['name']}</span>",
                        unsafe_allow_html=True,
                    )
                    use_custom_new = st.checkbox("使用自訂顏色", key="new_event_use_custom_color")
                    if use_custom_new:
                        new_color_value = st.color_picker(
                            "自訂顏色", value=new_color_value, key="new_event_custom_color"
                        )

                    concurrent_new = st.checkbox("是否能和讀書計畫並行？", key="new_event_concurrent")

                    if st.button("確認新增", key="btn_add_event"):
                        if new_title.strip():
                            st.session_state["daily_override_events"].setdefault(today_str, []).append({
                                "title":   new_title.strip(),
                                "start":   f"{new_start_h}:{new_start_m}",
                                "end":     f"{new_end_h}:{new_end_m}",
                                "emoji":   new_emoji,
                                "color":   new_color_value,
                                "display_color": new_color_value,
                                "show_on_calendar": True,
                                "concurrent_with_study": concurrent_new,
                            })
                            st.rerun()

            # ── 心情反饋 ──────────────────────────────────────────────────────
            st.markdown("#### 🎭 心情反饋")
            with st.container(border=True):
                is_mood_submitted = st.session_state.get("mood_submitted", False)

                if not is_mood_submitted:
                    motivation = st.radio(
                        "動力 (1: 低下 - 5: 充滿動力)", [1, 2, 3, 4, 5],
                        index=st.session_state["saved_motivation"] - 1,
                        horizontal=True, key="daily_motivation")
                    mood = st.radio(
                        "心情 (1: 低落 - 5: 心情極佳)", [1, 2, 3, 4, 5],
                        index=st.session_state["saved_mood"] - 1,
                        horizontal=True, key="daily_mood_score")
                    
                    # Save immediately as user changes
                    st.session_state["saved_motivation"] = motivation
                    st.session_state["saved_mood"] = mood

                    if st.button("確認送出", key="btn_submit_mood"):
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
                    # Show locked values from saved state
                    st.radio("動力", [1, 2, 3, 4, 5],
                        index=st.session_state["saved_motivation"] - 1,
                        horizontal=True, key="daily_motivation_locked", disabled=True)
                    st.radio("心情", [1, 2, 3, 4, 5],
                        index=st.session_state["saved_mood"] - 1,
                        horizontal=True, key="daily_mood_score_locked", disabled=True)
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
                    new_subject    = st.text_input("科目", key="new_task_subject")
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

                if "show_time_loss" not in st.session_state:
                    st.session_state["show_time_loss"] = False

                if st.button("新增意外損失時間", key="btn_show_time_loss"):
                    st.session_state["show_time_loss"] = True

                if st.session_state["show_time_loss"]:
                    st.markdown("**新增一筆意外損失**")
                    fl_c1, fl_c2 = st.columns(2)
                    with fl_c1:
                        st.markdown("開始時間")
                        lsh_col, lsm_col = st.columns(2)
                        with lsh_col:
                            loss_start_h = st.selectbox(
                                "開始時", [f"{h:02d}" for h in range(24)], key="loss_s_h")
                        with lsm_col:
                            loss_start_m = st.selectbox(
                                "開始分", [f"{m:02d}" for m in range(60)], key="loss_s_m")
                    with fl_c2:
                        st.markdown("結束時間")
                        leh_col, lem_col = st.columns(2)
                        with leh_col:
                            loss_end_h = st.selectbox(
                                "結束時", [f"{h:02d}" for h in range(24)], key="loss_e_h")
                        with lem_col:
                            loss_end_m = st.selectbox(
                                "結束分", [f"{m:02d}" for m in range(60)], key="loss_e_m")
                    
                    st.info(f"⏱ 預覽：{loss_start_h}:{loss_start_m} → {loss_end_h}:{loss_end_m}")
                    loss_reason = st.text_input("原因（選填）", key="loss_reason")

                    if st.button("新增這筆"):
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
                        if "loss_reason" in st.session_state:
                            del st.session_state["loss_reason"]
                        st.rerun()

                time_loss_records = st.session_state["time_loss_records"].get(today_str, [])
                if time_loss_records:
                    st.markdown("**已記錄的意外損失：**")
                    total_mins = 0
                    for rec in time_loss_records:
                        mins = rec.get("minutes", 0)
                        total_mins += mins
                        reason_str = f"　原因：{rec['reason']}" if rec.get("reason") else ""
                        st.markdown(f"- {rec['start']} → {rec['end']}　**{mins} 分鐘**{reason_str}")
                    total_h = total_mins // 60
                    total_m = total_mins % 60
                    st.info(f"⏱ 今日合計損失：**{total_h} 小時 {total_m} 分鐘**")
                else:
                    total_mins = 0

                time_loss = round(total_mins / 60, 2)

        # ── 紀錄區 ───────────────────────────────────────────────────────────
        st.markdown("#### 🗒️ 紀錄區")
        with st.container(border=True):
            is_daily_saved = st.session_state.get("daily_saved", False)
            daily_progress = st.text_area(
                "今日紀錄",
                value=(st.session_state.get("daily_log") or {}).get("daily_progress", ""),
                placeholder="寫點東西吧!",
                height=200, disabled=is_daily_saved,
                label_visibility="collapsed"
            )
            notes = ""  # Kept for compatibility

        if not is_daily_saved:
            if st.button("💾 儲存今日打卡", use_container_width=True):
                motivation_val = st.session_state.get("saved_motivation", 3)
                mood_val       = st.session_state.get("saved_mood", 3)
                daily_data = {
                    "daily_progress":   daily_progress,
                    "mood_score":       mood_val,
                    "motivation_score": motivation_val,
                    "amount_score":     amount_feedback,
                    "pacing_score":     pacing_feedback,
                    "time_loss":        time_loss,
                    "notes":            notes,
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
            st.info(
                f"💡 **今日建議**：\n"
                f"{(st.session_state.get('daily_log') or {}).get('recommendation', '')}"
            )
            if st.button("✏️ 編輯今日打卡", use_container_width=True):
                st.session_state["daily_saved"] = False
                st.rerun()

    if st.session_state.get("plan_name"):
        st.markdown("---")
        st.markdown(f"### {st.session_state['plan_name']}")
