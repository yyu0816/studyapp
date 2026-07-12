from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _group_monthly_plan_by_month(monthly_plan: list[dict[str, Any]]) -> dict[tuple[int, int], list[dict[str, Any]]]:
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for item in monthly_plan:
        item_date = _parse_date(item["date"])
        grouped.setdefault((item_date.year, item_date.month), []).append(item)
    return grouped


def _month_calendar_dates(year: int, month: int) -> list[list[date]]:
    first_day = date(year, month, 1)
    start = first_day - timedelta(days=first_day.weekday())
    weeks: list[list[date]] = []
    current = start
    for _ in range(6):
        weeks.append([current + timedelta(days=i) for i in range(7)])
        current += timedelta(days=7)
    return weeks


def render_monthly_plan_page() -> None:
    if not st.session_state.get("monthly_plan") or not st.session_state.get("plan"):
        st.info("請先完成初始設定。")
        return

    plan = st.session_state.get("plan") or {}
    monthly_plan = st.session_state.get("monthly_plan") or []
    plan_by_date: dict[str, dict[str, Any]] = {item["date"]: item for item in monthly_plan}

    try:
        start_date = _parse_date(plan.get("start_date", ""))
        end_date = _parse_date(plan.get("end_date", ""))
    except Exception:
        st.error("計畫日期格式錯誤，請回到設定頁確認開始與結束日期。")
        return

    grouped = _group_monthly_plan_by_month(monthly_plan)
    headers = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]

    for (year, month), _items in sorted(grouped.items()):
        st.markdown(f"### {year}年{month}月")
        
        html_calendar = """
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); border-top: 1px solid #ddd; border-left: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: #fff; margin-bottom: 30px;">
        """
        for h in headers:
            html_calendar += f'<div style="background: #f4f6f8; text-align: center; font-weight: bold; padding: 8px; border-bottom: 1px solid #ddd; border-right: 1px solid #ddd; color: #333;">{h}</div>'

        weeks = _month_calendar_dates(year, month)
        for week in weeks:
            for day in week:
                day_str = day.strftime("%Y-%m-%d")
                item = plan_by_date.get(day_str)
                is_current_month = day.month == month and start_date <= day <= end_date
                day_label = day.strftime("%m/%d")
                
                bg_color = "#fff" if is_current_month else "#fcfcfc"
                text_color = "#555" if is_current_month else "#bbb"
                
                html_calendar += f'<div style="min-height: 120px; padding: 6px; border-bottom: 1px solid #ddd; border-right: 1px solid #ddd; background: {bg_color}; display: flex; flex-direction: column; gap: 4px;">'
                html_calendar += f'<div style="font-weight: 600; font-size: 14px; margin-bottom: 4px; color: {text_color};">{day_label}</div>'
                
                if is_current_month:
                    if item and item.get("fixed_events"):
                        for event in item.get("fixed_events", []):
                            if event.get("show_on_calendar", True):
                                emoji = event.get("emoji", "📌")
                                title = event.get("title", "")
                                color = event.get("display_color", event.get("color", "#4f84ff"))
                                html_calendar += f'<div style="font-size: 12px; color: #333; padding: 3px 6px; border-radius: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background:{color}33; border-left:3px solid {color};">{emoji} {title}</div>'
                    
                    if item and item.get("tasks"):
                        for task in item.get("tasks", []):
                            html_calendar += f'<div style="font-size: 11px; color: #555; padding: 2px 4px; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: #f0f0f0; border-left: 2px solid #ccc;">📖 {task}</div>'
                
                html_calendar += '</div>'
        html_calendar += "</div>"
        
        if hasattr(st, "html"):
            st.html(html_calendar)
        else:
            st.markdown(html_calendar, unsafe_allow_html=True)
