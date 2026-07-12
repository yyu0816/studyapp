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

    plan = st.session_state.get("plan") or {}
    monthly_plan = st.session_state.get("monthly_plan") or []
    plan_by_date: dict[str, dict[str, Any]] = {item["date"]: item for item in monthly_plan}

    try:
        start_date = _parse_date(plan.get("start_date", ""))
        end_date = _parse_date(plan.get("end_date", ""))
    except Exception:
        st.error("計畫日期格式錯誤，請回到設定頁確認開始與結束日期。")
        return

    st.markdown("""
    <style>
    .cal-btn > button {
        padding: 2px !important;
        min-height: 20px !important;
        font-weight: bold;
        color: #555;
        border: none !important;
        background: transparent !important;
    }
    .cal-btn > button:hover {
        color: #4f84ff;
    }
    </style>
    """, unsafe_allow_html=True)

    grouped = _group_monthly_plan_by_month(monthly_plan)
    headers = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    
    # Process each month
    for (year, month), _items in sorted(grouped.items()):
        st.markdown(f"### {year}年{month}月")
        
        col_cal, col_overview = st.columns([2, 1])
        
        with col_cal:
            # Render headers
            hc = st.columns(7)
            for i, h in enumerate(headers):
                with hc[i]:
                    st.markdown(f"<div style='text-align:center; font-weight:bold; color:#555; margin-bottom:8px;'>{h}</div>", unsafe_allow_html=True)
            
            weeks = _month_calendar_dates(year, month)
            for week in weeks:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    with cols[i]:
                        day_str = day.strftime("%Y-%m-%d")
                        item = plan_by_date.get(day_str)
                        is_current_month = day.month == month and start_date <= day <= end_date
                        
                        bg_color = "#fff" if is_current_month else "#fcfcfc"
                        
                        with st.container(border=True):
                            # Wrapper for button to reduce size
                            st.markdown('<div class="cal-btn">', unsafe_allow_html=True)
                            if st.button(str(day.day), key=f"btn_add_{day_str}", use_container_width=True):
                                if is_current_month:
                                    add_event_dialog(day_str)
                                else:
                                    st.warning("請選擇計畫範圍內的日期")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Render events in this cell
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
                                        st.markdown(f'<div style="font-size: 11px; color: #333; padding: 2px 4px; border-radius: 4px; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background:{color}33; border-left:3px solid {color};">{emoji} {title}</div>', unsafe_allow_html=True)
                                
                                if item and item.get("tasks"):
                                    for task in item.get("tasks", []):
                                        st.markdown(f'<div style="font-size: 10px; color: #555; padding: 1px 3px; margin-bottom: 2px; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: #f0f0f0; border-left: 2px solid #ccc;">📖 {task}</div>', unsafe_allow_html=True)
                                        
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
