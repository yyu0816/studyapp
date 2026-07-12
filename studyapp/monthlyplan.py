from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
from dailycheck import EMOJI_OPTIONS, COLOR_OPTIONS


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

@st.dialog("新增行程")
def add_event_dialog(day_str: str):
    st.write(f"**日期**：{day_str}")
    title = st.text_input("行程名稱")
    is_all_day = st.checkbox("整天")
    
    col1, col2 = st.columns(2)
    start_time = "00:00"
    end_time = "23:59"
    with col1:
        if not is_all_day:
            start_val = st.time_input("開始時間")
            if start_val: start_time = start_val.strftime("%H:%M")
    with col2:
        if not is_all_day:
            end_val = st.time_input("結束時間")
            if end_val: end_time = end_val.strftime("%H:%M")
            
    c1, c2 = st.columns(2)
    with c1:
        emoji = st.selectbox("表情符號", EMOJI_OPTIONS)
    with c2:
        color_option = st.selectbox("顏色", COLOR_OPTIONS, format_func=lambda x: x["name"])
        if isinstance(color_option, dict):
            color = color_option["value"]
        else:
            color = color_option
        
    if st.button("儲存", use_container_width=True):
        if not title:
            st.error("請輸入行程名稱")
            return
        if "daily_override_events" not in st.session_state:
            st.session_state["daily_override_events"] = {}
        if day_str not in st.session_state["daily_override_events"]:
            st.session_state["daily_override_events"][day_str] = []
            
        st.session_state["daily_override_events"][day_str].append({
            "title": title,
            "start": start_time,
            "end": end_time,
            "emoji": emoji,
            "color": color,
            "display_color": color,
            "is_all_day": is_all_day,
            "show_on_calendar": True
        })
        st.rerun()

def render_monthly_plan_page() -> None:
    if not st.session_state.get("monthly_plan") or not st.session_state.get("plan"):
        st.info("請先完成初始設定。")
        return

    # Check for query params for event clicking
    add_event_target = st.query_params.get("add_event_date")
    if add_event_target:
        st.query_params.clear()
        add_event_dialog(add_event_target)

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
    
    # Process each month
    for (year, month), _items in sorted(grouped.items()):
        st.markdown(f"### {year}年{month}月")
        
        col_cal, col_overview = st.columns([2, 1])
        
        with col_cal:
            html_calendar = """
            <style>
            .grid-cell {
                min-height: 120px; 
                padding: 6px; 
                border-bottom: 1px solid #ddd; 
                border-right: 1px solid #ddd; 
                display: flex; 
                flex-direction: column; 
                gap: 4px;
                text-decoration: none;
                color: inherit;
                transition: background-color 0.2s;
                cursor: pointer;
            }
            .grid-cell:hover {
                background-color: #f0f7ff !important;
            }
            </style>
            <div style="display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); border-top: 1px solid #ddd; border-left: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: #fff; margin-bottom: 30px;">
            """
            for h in headers:
                html_calendar += f'<div style="background: #f4f6f8; text-align: center; font-weight: bold; padding: 8px; border-bottom: 1px solid #ddd; border-right: 1px solid #ddd; color: #333; font-size:14px;">{h}</div>'

            weeks = _month_calendar_dates(year, month)
            for week in weeks:
                for day in week:
                    day_str = day.strftime("%Y-%m-%d")
                    item = plan_by_date.get(day_str)
                    is_current_month = day.month == month and start_date <= day <= end_date
                    day_label = str(day.day)
                    
                    bg_color = "#fff" if is_current_month else "#fcfcfc"
                    text_color = "#333" if is_current_month else "#bbb"
                    
                    # We wrap the entire cell in an <a> tag that triggers the query param reload if it's within the valid range
                    if is_current_month:
                        html_calendar += f'<a href="?add_event_date={day_str}" target="_self" class="grid-cell" style="background: {bg_color};">'
                    else:
                        html_calendar += f'<div class="grid-cell" style="background: {bg_color}; cursor: default;">'
                        
                    html_calendar += f'<div style="font-weight: bold; font-size: 14px; margin-bottom: 4px; color: {text_color};">{day_label}</div>'
                    
                    if is_current_month:
                        events = []
                        if item and item.get("fixed_events"):
                            events.extend(item.get("fixed_events", []))
                        if "daily_override_events" in st.session_state and day_str in st.session_state["daily_override_events"]:
                            events.extend(st.session_state["daily_override_events"][day_str])
                        
                        for event in events:
                            if event.get("show_on_calendar", True):
                                emoji = event.get("emoji", "📌")
                                title = event.get("title", "")
                                color = event.get("display_color", event.get("color", "#4f84ff"))
                                html_calendar += f'<div style="font-size: 11px; color: #333; padding: 3px 4px; border-radius: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background:{color}33; border-left:3px solid {color};">{emoji} {title}</div>'
                        
                        if item and item.get("tasks"):
                            for task in item.get("tasks", []):
                                html_calendar += f'<div style="font-size: 10px; color: #555; padding: 2px 4px; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: #f0f0f0; border-left: 2px solid #ccc;">📖 {task}</div>'
                    
                    if is_current_month:
                        html_calendar += '</a>'
                    else:
                        html_calendar += '</div>'
                        
            html_calendar += "</div>"
            st.markdown(html_calendar, unsafe_allow_html=True)
            
        with col_overview:
            st.markdown("#### 📅 行程總覽")
            with st.container(border=True):
                month_events = []
                for _item in _items:
                    d_str = _item["date"]
                    d_obj = _parse_date(d_str)
                    weekday_str = headers[d_obj.weekday()]
                    
                    if _item.get("fixed_events"):
                        for e in _item["fixed_events"]:
                            if e.get("show_on_calendar", True):
                                month_events.append({"date": d_str, "weekday": weekday_str, "event": e, "type": "fixed"})
                    
                    if "daily_override_events" in st.session_state and d_str in st.session_state["daily_override_events"]:
                        for e in st.session_state["daily_override_events"][d_str]:
                            if e.get("show_on_calendar", True):
                                month_events.append({"date": d_str, "weekday": weekday_str, "event": e, "type": "temp"})
                
                if month_events:
                    for me in month_events:
                        e = me["event"]
                        color = e.get("display_color", e.get("color", "#4f84ff"))
                        label = "固" if me["type"] == "fixed" else "臨"
                        st.markdown(f"""
                        <div style="font-size:13px; margin-bottom:6px; padding:6px; border-left: 4px solid {color}; background:#f9f9f9; border-radius:4px;">
                            <strong>{me['date'][5:]} ({me['weekday']})</strong> - {e.get('emoji', '📌')} {e.get('title', '')} <span style="font-size:10px; color:#888;">[{label}]</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("本月無任何行程")
                    
            st.markdown("#### 📖 月進度")
            with st.container(border=True):
                progress = {}
                for _item in _items:
                    if _item.get("tasks"):
                        for task in _item["tasks"]:
                            parts = task.split(" - ", 1)
                            if len(parts) == 2:
                                subj = parts[0].strip()
                                detail = parts[1].strip()
                                progress.setdefault(subj, []).append(detail)
                            else:
                                progress.setdefault("其他", []).append(task)
                                
                if progress:
                    for subj, details in progress.items():
                        st.markdown(f"**{subj}**")
                        for d in details:
                            st.markdown(f"<div style='font-size:12px; margin-left:10px; margin-bottom:4px;'>• {d}</div>", unsafe_allow_html=True)
                else:
                    st.write("本月無學習進度")
        
        st.markdown("---")
