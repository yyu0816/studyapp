from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st


def render_monthly_plan_page() -> None:
    st.subheader("月曆與讀書計畫")
    st.caption("月曆上會顯示固定行程與每日排程；點選日期可展開查看當天任務。")

    if not st.session_state.get("monthly_plan") or not st.session_state.get("plan"):
        st.info("請先完成初始設定。")
        return

    plan = st.session_state.get("plan") or {}
    monthly_plan = st.session_state.get("monthly_plan") or []

    # index monthly_plan by date string for fast lookup
    plan_by_date: dict[str, dict] = {item["date"]: item for item in monthly_plan}

    # parse start and end from plan
    try:
        start_date = datetime.strptime(plan.get("start_date", ""), "%Y-%m-%d").date()
        end_date = datetime.strptime(plan.get("end_date", ""), "%Y-%m-%d").date()
    except Exception:
        st.error("計畫日期格式錯誤，請回到設定頁確認開始與結束日期。")
        return

    # align calendar to weeks starting on Monday and pad to full months
    calendar_start = (start_date.replace(day=1) - timedelta(days=(start_date.replace(day=1).weekday())))
    last_day_of_end_month = (end_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    calendar_end = last_day_of_end_month + timedelta(days=(6 - last_day_of_end_month.weekday()))

    # build rows of weeks
    current = calendar_start
    weeks: list[list[date]] = []
    while current <= calendar_end:
        week = [current + timedelta(days=i) for i in range(7)]
        weeks.append(week)
        current += timedelta(days=7)

    # render calendar header with weekday labels
    headers = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    st.markdown("### 月曆視圖")
    header_cols = st.columns(7)
    for col, label in zip(header_cols, headers):
        with col:
            st.markdown(f"**{label}**")

    st.markdown("<div style='border: 2px solid #ddd; padding: 8px; border-radius: 12px;'>", unsafe_allow_html=True)
    for week in weeks:
        cols = st.columns(7)
        for col, day in zip(cols, week):
            with col:
                day_str = day.strftime("%Y-%m-%d")
                is_in_range = start_date <= day <= end_date
                day_label = day.strftime("%m/%d")
                if not is_in_range:
                    st.markdown(f"<div style='min-height: 100px; border: 1px solid transparent; padding: 8px;'> <strong>{day_label}</strong> </div>", unsafe_allow_html=True)
                    continue

                item = plan_by_date.get(day_str)
                event_lines = []
                if item and item.get("fixed_events"):
                    for event in item.get("fixed_events", []):
                        if event.get("show_on_calendar", True):
                            emoji = event.get("emoji", "📌")
                            event_lines.append(f"{emoji} {event.get('title', '')}")
                if st.button(day_label, key=f"select_day_{day_str}"):
                    st.session_state["selected_day"] = day_str
                for line in event_lines:
                    st.markdown(f"<div style='font-size:12px; line-height:1.2'>{line}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    selected_day = st.session_state.get("selected_day")
    if selected_day and selected_day in plan_by_date:
        selected_item = plan_by_date[selected_day]
        st.markdown("---")
        st.markdown(f"### {selected_day} 詳細時間軸")
        if selected_item.get("fixed_events"):
            st.write("時間軸：")
            for event in selected_item.get("fixed_events", []):
                if event.get("show_on_calendar", True):
                    color = event.get("display_color", event.get("color", "#4f84ff"))
                    st.markdown(
                        f"<div style='background:{color}; color:#fff; border-radius:6px; padding:6px; margin-bottom:4px;'>"
                        f"<strong>{event.get('emoji', '📌')} {event.get('title', '')}</strong><br>"
                        f"{event.get('start','')} ～ {event.get('end','')}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.write("無固定行程")
        st.write("今日須完成：")
        if selected_item.get("tasks"):
            for task in selected_item.get("tasks", []):
                st.write(f"- {task}")
        else:
            st.write("- 尚未指定")

    st.markdown("---")
    st.markdown("### 每日詳細行程")
    for day in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)):
        day_str = day.strftime("%Y-%m-%d")
        item = plan_by_date.get(day_str, {})
        with st.expander(f"{day.strftime('%Y-%m-%d')} {item.get('day_name','')}"):
            if item.get("fixed_events"):
                st.write("時間軸：")
                for event in item.get("fixed_events", []):
                    if event.get("show_on_calendar", True):
                        color = event.get("display_color", event.get("color", "#4f84ff"))
                        st.markdown(
                            f"<div style='background:{color}; color:#fff; border-radius:6px; padding:6px; margin-bottom:4px;'>"
                            f"<strong>{event.get('emoji', '📌')} {event.get('title', '')}</strong><br>"
                            f"{event.get('start','')} ～ {event.get('end','')}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            st.write("今日須完成：")
            if item.get("tasks"):
                for task in item.get("tasks", []):
                    st.write(f"- {task}")
            else:
                st.write("- 尚未指定")
