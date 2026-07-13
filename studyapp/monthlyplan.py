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

def _format_date_list(date_strs: list[str]) -> str:
    if not date_strs: return ""
    dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in set(date_strs)])
    ranges = []
    current_range = [dates[0]]
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            current_range.append(dates[i])
        else:
            ranges.append(current_range)
            current_range = [dates[i]]
    ranges.append(current_range)
    
    formatted_ranges = []
    for r in ranges:
        if len(r) == 1:
            formatted_ranges.append(r[0].strftime("%m/%d"))
        else:
            formatted_ranges.append(f"{r[0].strftime('%m/%d')}~{r[-1].strftime('%m/%d')}")
    
    return ", ".join(formatted_ranges)

@st.dialog("新增行程")
def add_event_dialog(day_str: str):
    st.write(f"**新增行程**")
    title = st.text_input("行程名稱")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("開始日期", value=_parse_date(day_str))
    with col_d2:
        end_date = st.date_input("結束日期", value=_parse_date(day_str))
        
    is_all_day = st.checkbox("整天", value=True)
    
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
        color_mode = st.radio("顏色模式", ["預設色板", "自訂顏色"], horizontal=True, label_visibility="collapsed")
        if color_mode == "預設色板":
            color_option = st.selectbox("顏色", COLOR_OPTIONS, format_func=lambda x: x["name"], label_visibility="collapsed")
            color = color_option["value"] if isinstance(color_option, dict) else color_option
        else:
            color = st.color_picker("顏色", "#4f84ff", label_visibility="collapsed")
        
    if st.button("儲存", use_container_width=True):
        if not title:
            st.error("請輸入行程名稱")
            return
        if start_date > end_date:
            st.error("開始日期不能晚於結束日期")
            return
            
        if "daily_override_events" not in st.session_state:
            st.session_state["daily_override_events"] = {}
            
        current = start_date
        while current <= end_date:
            curr_str = current.strftime("%Y-%m-%d")
            if curr_str not in st.session_state["daily_override_events"]:
                st.session_state["daily_override_events"][curr_str] = []
                
            st.session_state["daily_override_events"][curr_str].append({
                "title": title,
                "start": start_time,
                "end": end_time,
                "emoji": emoji,
                "color": color,
                "display_color": color,
                "is_all_day": is_all_day,
                "show_on_calendar": True
            })
            current += timedelta(days=1)
            
        st.rerun()

def _build_calendar_html(year: int, month: int, plan_by_date: dict, start_date: date, end_date: date) -> str:
    """Build a pure HTML table for the calendar month."""
    headers = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    weeks = _month_calendar_dates(year, month)

    header_cells = "".join(
        f'<th style="text-align:center; font-weight:600; color:#555; font-size:13px; padding:10px 4px; background:#f9f9f9; border:1px solid #cccccc;">{h}</th>'
        for h in headers
    )

    rows_html = ""
    for week in weeks:
        row = "<tr>"
        for day in week:
            day_str = day.strftime("%Y-%m-%d")
            item = plan_by_date.get(day_str)
            is_current = day.month == month and start_date <= day <= end_date

            num_color = "#333" if is_current else "#c0c0c0"
            num_weight = "bold" if is_current else "normal"
            bg = "#ffffff" if is_current else "#fafafa"

            # Clickable date number
            if is_current:
                num_html = f'<span class="cal-date" data-date="{day_str}" onclick="window.parent.postMessage({{type:\'streamlit:setComponentValue\', value: \'{day_str}\'}}, \'*\')"></span><div style="font-weight:{num_weight}; color:{num_color}; font-size:14px; margin-bottom:4px; cursor:pointer;" onclick="document.getElementById(\'calclick_{day_str}\').click()">{day.day}</div>'
            else:
                num_html = f'<div style="font-weight:{num_weight}; color:{num_color}; font-size:14px; margin-bottom:4px;">{day.day}</div>'

            # Events
            events_html = ""
            if is_current:
                events = []
                if item and item.get("fixed_events"):
                    events.extend(item["fixed_events"])
                override = st.session_state.get("daily_override_events", {})
                if day_str in override:
                    events.extend(override[day_str])
                for ev in events:
                    if ev.get("show_on_calendar", True):
                        t = ev.get("title", "")
                        c = ev.get("display_color", ev.get("color", "#4f84ff"))
                        events_html += f'<div style="font-size:11px;font-weight:bold;color:#fff;padding:2px 6px;border-radius:5px;margin-top:3px;background:{c};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{t}</div>'
                if item and item.get("tasks"):
                    for task in item["tasks"]:
                        events_html += f'<div style="font-size:10px;color:#555;padding:1px 3px;margin-top:2px;border-radius:3px;background:#f0f0f0;border-left:2px solid #ccc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">📖 {task}</div>'

            row += f'<td style="vertical-align:top; border:1px solid #cccccc; background:{bg}; padding:6px; min-height:110px; width:14.2857%;">{num_html}{events_html}</td>'
        row += "</tr>"
        rows_html += row

    return f"""
    <table style="border-collapse:collapse; width:100%; table-layout:fixed; font-family:sans-serif;">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """


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

    # Check if a date was clicked via hidden buttons
    clicked_date = st.session_state.pop("_cal_clicked_date", None)
    if clicked_date:
        add_event_dialog(clicked_date)

    for (year, month), _items in sorted(grouped.items()):
        st.markdown(f"### {year}年{month}月")

        col_cal, col_overview = st.columns([2, 1], gap="medium")

        with col_cal:
            # Render a pure HTML table for the calendar
            calendar_html = _build_calendar_html(year, month, plan_by_date, start_date, end_date)
            st.markdown(calendar_html, unsafe_allow_html=True)

            # Hidden buttons for each day in the current month so clicks work
            weeks = _month_calendar_dates(year, month)
            st.markdown('<div style="display:none">', unsafe_allow_html=True)
            for week in weeks:
                for day in week:
                    if day.month == month and start_date <= day <= end_date:
                        day_str = day.strftime("%Y-%m-%d")
                        if st.button("x", key=f"calclick_{year}_{month}_{day_str}"):
                            st.session_state["_cal_clicked_date"] = day_str
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
                                        
        with col_overview:
            st.markdown("#### 📅 行程總覽")
            with st.container(border=True):
                month_events = []
                for _item in _items:
                    d_str = _item["date"]
                    
                    if _item.get("fixed_events"):
                        for e in _item["fixed_events"]:
                            if e.get("show_on_calendar", True):
                                month_events.append({"date": d_str, "event": e})
                    
                    if "daily_override_events" in st.session_state and d_str in st.session_state["daily_override_events"]:
                        for e in st.session_state["daily_override_events"][d_str]:
                            if e.get("show_on_calendar", True):
                                month_events.append({"date": d_str, "event": e})
                
                if month_events:
                    # Group by title and emoji
                    grouped_ev = {}
                    for me in month_events:
                        title = me["event"].get("title", "")
                        emoji = me["event"].get("emoji", "📌")
                        color = me["event"].get("display_color", me["event"].get("color", "#4f84ff"))
                        key = (title, emoji, color)
                        grouped_ev.setdefault(key, []).append(me["date"])
                        
                    for (title, emoji, color), dates in grouped_ev.items():
                        date_str_formatted = _format_date_list(dates)
                        st.markdown(f"""
                        <div style="font-size:13px; margin-bottom:6px; padding:6px; border-left: 4px solid {color}; background:#f9f9f9; border-radius:4px;">
                            <strong>[{date_str_formatted}]</strong> {emoji} {title}
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
                                if detail not in progress.setdefault(subj, []):
                                    progress[subj].append(detail)
                            else:
                                if task not in progress.setdefault("其他", []):
                                    progress["其他"].append(task)
                                
                if progress:
                    for subj, details in progress.items():
                        st.markdown(f"**{subj}**")
                        for d in details:
                            st.markdown(f"<div style='font-size:12px; margin-left:10px; margin-bottom:4px;'>• {d}</div>", unsafe_allow_html=True)
                else:
                    st.write("本月無學習進度")
        
        st.markdown("---")
