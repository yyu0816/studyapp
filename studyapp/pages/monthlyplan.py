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

    st.markdown("### 月曆視圖")
    
    html_calendar = """
    <style>
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        border-top: 1px solid #ddd;
        border-left: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        background: #fff;
    }
    .calendar-header {
        background: #f4f6f8;
        text-align: center;
        font-weight: bold;
        padding: 8px;
        border-bottom: 1px solid #ddd;
        border-right: 1px solid #ddd;
        color: #333;
    }
    .calendar-cell {
        min-height: 120px;
        padding: 6px;
        border-bottom: 1px solid #ddd;
        border-right: 1px solid #ddd;
        background: #fff;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .calendar-cell.out-of-range {
        background: #fcfcfc;
        color: #bbb;
    }
    .calendar-date {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 4px;
        color: #555;
    }
    .calendar-event {
        font-size: 12px;
        color: #333;
        padding: 3px 6px;
        border-radius: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    <div class="calendar-grid">
    """
    
    headers = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    for h in headers:
        html_calendar += f'<div class="calendar-header">{h}</div>'

    for week in weeks:
        for day in week:
            day_str = day.strftime("%Y-%m-%d")
            is_in_range = start_date <= day <= end_date
            day_label = day.strftime("%m/%d")
            css_class = "calendar-cell" if is_in_range else "calendar-cell out-of-range"
            html_calendar += f'<div class="{css_class}"><div class="calendar-date">{day_label}</div>'
            
            if is_in_range:
                item = plan_by_date.get(day_str)
                if item and item.get("fixed_events"):
                    for event in item.get("fixed_events", []):
                        if event.get("show_on_calendar", True):
                            emoji = event.get("emoji", "📌")
                            title = event.get("title", "")
                            color = event.get("display_color", event.get("color", "#4f84ff"))
                            html_calendar += f'<div class="calendar-event" style="background:{color}33; border-left:3px solid {color};">{emoji} {title}</div>'
            html_calendar += '</div>'

    html_calendar += "</div>"

    st.markdown(html_calendar, unsafe_allow_html=True)
