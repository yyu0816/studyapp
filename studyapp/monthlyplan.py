from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
from dailycheck import EMOJI_OPTIONS, COLOR_OPTIONS
from streamlit_color_picker import color_picker as _cp


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
    title = st.text_input("行程名稱")

    # Auto-sync end_date when start_date changes
    _sd_key = "_add_dlg_start"
    _ed_key = "_add_dlg_end"
    init_day = _parse_date(day_str)
    if _sd_key not in st.session_state:
        st.session_state[_sd_key] = init_day
        st.session_state[_ed_key] = init_day

    def _on_start_change():
        new_start = st.session_state[_sd_key]
        if st.session_state[_ed_key] < new_start:
            st.session_state[_ed_key] = new_start

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("開始日期", key=_sd_key, on_change=_on_start_change)
    with col_d2:
        end_date = st.date_input("結束日期", key=_ed_key)

    is_all_day = st.checkbox("整天", value=True)
    start_time, end_time = "00:00", "23:59"
    if not is_all_day:
        col1, col2 = st.columns(2)
        with col1:
            sv = st.time_input("開始時間")
            if sv: start_time = sv.strftime("%H:%M")
        with col2:
            ev = st.time_input("結束時間")
            if ev: end_time = ev.strftime("%H:%M")

    emoji = st.selectbox("表情符號", EMOJI_OPTIONS)
    color_option = st.selectbox("顏色", COLOR_OPTIONS, format_func=lambda x: x["name"])
    preset_color = color_option["value"] if isinstance(color_option, dict) else color_option
    if isinstance(color_option, dict):
        st.markdown(f"<div style='display:inline-block;width:20px;height:20px;border-radius:4px;background:{preset_color};vertical-align:middle;margin-right:6px;'></div> {color_option['name']}", unsafe_allow_html=True)
    use_custom_color = st.checkbox("使用自訂顏色", value=False)
    if use_custom_color:
        color = _cp("選擇顏色", default_color=preset_color, key="add_dlg_cp")
    else:
        color = preset_color

    if st.button("儲存", use_container_width=True):
        if not title:
            st.error("請輸入行程名稱")
            return
        if start_date > end_date:
            st.error("開始日期不能晚於結束日期")
            return
        # clean up temp keys
        st.session_state.pop(_sd_key, None)
        st.session_state.pop(_ed_key, None)

        st.session_state.setdefault("daily_override_events", {})
        cur = start_date
        while cur <= end_date:
            cs = cur.strftime("%Y-%m-%d")
            st.session_state["daily_override_events"].setdefault(cs, []).append({
                "title": title, "start": start_time, "end": end_time,
                "emoji": emoji, "color": color, "display_color": color,
                "is_all_day": is_all_day, "show_on_calendar": True,
            })
            cur += timedelta(days=1)
        st.rerun()


@st.dialog("編輯行程")
def edit_event_dialog(date_str: str, ev_idx: int):
    override = st.session_state.get("daily_override_events", {})
    ev_list_for_date = override.get(date_str, [])
    if ev_idx >= len(ev_list_for_date):
        st.error("找不到行程")
        return
        
    ev = ev_list_for_date[ev_idx]

    title_orig = ev.get("title", "")
    emoji_orig = ev.get("emoji", "📌")
    color_orig = ev.get("display_color", ev.get("color", "#4f84ff"))
    start_orig = ev.get("start", "00:00")
    end_orig   = ev.get("end", "23:59")
    
    # Find all dates that have this exact event (for grouped editing)
    matching_dates = []
    for d_str, ev_list in override.items():
        for e in ev_list:
            if (e.get("title", "") == title_orig and 
                e.get("emoji", "📌") == emoji_orig and 
                e.get("display_color", e.get("color", "#4f84ff")) == color_orig and
                e.get("start", "00:00") == start_orig and
                e.get("end", "23:59") == end_orig):
                matching_dates.append(d_str)
                break # only count the date once

    title = st.text_input("行程名稱", value=title_orig)

    _sd_key = "_edit_dlg_start"
    _ed_key = "_edit_dlg_end"
    if _sd_key not in st.session_state:
        if matching_dates:
            st.session_state[_sd_key] = _parse_date(min(matching_dates))
            st.session_state[_ed_key] = _parse_date(max(matching_dates))
        else:
            st.session_state[_sd_key] = _parse_date(date_str)
            st.session_state[_ed_key] = _parse_date(date_str)

    def _on_start_change():
        if st.session_state[_ed_key] < st.session_state[_sd_key]:
            st.session_state[_ed_key] = st.session_state[_sd_key]

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("開始日期", key=_sd_key, on_change=_on_start_change)
    with col_d2:
        end_date = st.date_input("結束日期", key=_ed_key)

    is_all_day = st.checkbox("整天", value=ev.get("is_all_day", True))
    start_time, end_time = ev.get("start", "00:00"), ev.get("end", "23:59")
    if not is_all_day:
        col1, col2 = st.columns(2)
        with col1:
            sv = st.time_input("開始時間")
            if sv: start_time = sv.strftime("%H:%M")
        with col2:
            evt = st.time_input("結束時間")
            if evt: end_time = evt.strftime("%H:%M")

    emoji_idx = EMOJI_OPTIONS.index(ev.get("emoji", EMOJI_OPTIONS[0])) if ev.get("emoji") in EMOJI_OPTIONS else 0
    emoji = st.selectbox("表情符號", EMOJI_OPTIONS, index=emoji_idx)
    # Find the current color's index in COLOR_OPTIONS
    cur_color = ev.get("display_color", ev.get("color", "#4f84ff"))
    color_idx = next((i for i, o in enumerate(COLOR_OPTIONS) if isinstance(o, dict) and o["value"] == cur_color), 0)
    color_option = st.selectbox("顏色", COLOR_OPTIONS, format_func=lambda x: x["name"], index=color_idx)
    preset_color = color_option["value"] if isinstance(color_option, dict) else color_option
    if isinstance(color_option, dict):
        st.markdown(f"<div style='display:inline-block;width:20px;height:20px;border-radius:4px;background:{preset_color};vertical-align:middle;margin-right:6px;'></div> {color_option['name']}", unsafe_allow_html=True)
    use_custom_color = st.checkbox("使用自訂顏色", value=False)
    if use_custom_color:
        color = _cp("選擇顏色", default_color=cur_color, key="edit_dlg_cp")
    else:
        color = preset_color

    col_save, col_del = st.columns(2)
    with col_save:
        if st.button("儲存", use_container_width=True, type="primary"):
            if not title:
                st.error("請輸入行程名稱")
                return
            
            # Remove all old matching events across all dates
            for d_str in matching_dates:
                override[d_str] = [e for e in override[d_str] if not (
                    e.get("title", "") == title_orig and 
                    e.get("emoji", "📌") == emoji_orig and 
                    e.get("display_color", e.get("color", "#4f84ff")) == color_orig and
                    e.get("start", "00:00") == start_orig and
                    e.get("end", "23:59") == end_orig
                )]
                
            # Re-insert across new date range
            cur = start_date
            while cur <= end_date:
                cs = cur.strftime("%Y-%m-%d")
                st.session_state["daily_override_events"].setdefault(cs, []).append({
                    "title": title, "start": start_time, "end": end_time,
                    "emoji": emoji, "color": color, "display_color": color,
                    "is_all_day": is_all_day, "show_on_calendar": True,
                })
                cur += timedelta(days=1)
            st.session_state.pop(_sd_key, None)
            st.session_state.pop(_ed_key, None)
            st.rerun()
    with col_del:
        if st.button("🗑️ 刪除", use_container_width=True):
            for d_str in matching_dates:
                override[d_str] = [e for e in override[d_str] if not (
                    e.get("title", "") == title_orig and 
                    e.get("emoji", "📌") == emoji_orig and 
                    e.get("display_color", e.get("color", "#4f84ff")) == color_orig and
                    e.get("start", "00:00") == start_orig and
                    e.get("end", "23:59") == end_orig
                )]
            st.session_state.pop(_sd_key, None)
            st.session_state.pop(_ed_key, None)
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
    override_all = st.session_state.get("daily_override_events", {})
    for week in weeks:
        row = "<tr>"
        for day in week:
            day_str = day.strftime("%Y-%m-%d")
            item = plan_by_date.get(day_str)
            in_this_month = day.month == month
            is_in_plan = in_this_month and start_date <= day <= end_date
            has_override = in_this_month and bool(override_all.get(day_str))
            # Show events for plan days AND days with user-added events outside plan range
            is_active = is_in_plan or has_override

            if is_in_plan:
                num_color = "#333"
                num_weight = "bold"
                bg = "#ffffff"
            elif has_override:
                # outside plan range but has events — slightly dimmed
                num_color = "#888"
                num_weight = "normal"
                bg = "#f5f5f5"
            else:
                num_color = "#c0c0c0"
                num_weight = "normal"
                bg = "#fafafa"

            num_html = f'<div style="font-weight:{num_weight}; color:{num_color}; font-size:14px; margin-bottom:4px;">{day.day}</div>'

            # Events
            events_html = ""
            if is_active:
                events = []
                if item and item.get("fixed_events"):
                    events.extend(item["fixed_events"])
                if day_str in override_all:
                    events.extend(override_all[day_str])
                for ev in events:
                    if ev.get("show_on_calendar", True):
                        t = ev.get("title", "")
                        c = ev.get("display_color", ev.get("color", "#4f84ff"))
                        events_html += f'<div style="font-size:11px;font-weight:bold;color:#fff;padding:2px 6px;border-radius:5px;margin-top:3px;background:{c};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{t}</div>'
                if item and item.get("tasks"):
                    for task in item["tasks"]:
                        events_html += f'<div style="font-size:10px;color:#555;padding:1px 3px;margin-top:2px;border-radius:3px;background:#f0f0f0;border-left:2px solid #ccc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">📖 {task}</div>'

            if is_active:
                cell_inner = f'{num_html}{events_html}'
                row += (
                    f'<td style="vertical-align:top; border:1px solid #cccccc; background:{bg}; '
                    f'padding:0; width:14.2857%; height:110px;">'
                    f'<div style="padding:6px; height:100%; box-sizing:border-box;">{cell_inner}</div></td>'
                )
            else:
                row += f'<td style="vertical-align:top; border:1px solid #cccccc; background:{bg}; padding:6px; height:110px; width:14.2857%;">{num_html}</td>'
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

    qp = st.query_params
    edit_val = qp.get("edit_event", None)
    if edit_val:
        st.query_params.clear()
        parts = edit_val.split("|")
        if len(parts) == 2:
            edit_event_dialog(parts[0], int(parts[1]))

    for (year, month), _items in sorted(grouped.items()):
        st.markdown(f"### {year}年{month}月")

        col_cal, col_overview = st.columns([2, 1], gap="medium")

        with col_cal:
            # Render a pure HTML table for the calendar
            calendar_html = _build_calendar_html(year, month, plan_by_date, start_date, end_date)
            st.markdown(calendar_html, unsafe_allow_html=True)
                                        
        with col_overview:
            st.markdown("#### 📅 行程總覽")
            
            # 新增行程按鈕
            if st.button("＋ 新增行程", key=f"add_btn_{year}_{month}", use_container_width=True, type="primary"):
                # Default to first day of current month within plan range
                default_day = max(start_date, date(year, month, 1))
                add_event_dialog(default_day.strftime("%Y-%m-%d"))
            
            # Collect ALL user-added events for this month from override
            # (not limited to _items dates — events can span outside plan range)
            import calendar as _cal
            user_events: list[dict] = []
            override = st.session_state.get("daily_override_events", {})
            
            # Scan every day of this month in override
            _, last_day = _cal.monthrange(year, month)
            for day_n in range(1, last_day + 1):
                d_str = date(year, month, day_n).strftime("%Y-%m-%d")
                for ev_idx, e in enumerate(override.get(d_str, [])):
                    if e.get("show_on_calendar", True):
                        user_events.append({"date": d_str, "event": e, "ev_idx": ev_idx})

            if user_events:
                # CSS: force every tertiary button to be left-aligned text
                st.markdown(
                    """
                    <style>
                    [data-testid="stBaseButton-tertiary"] {
                        justify-content: flex-start !important;
                        text-align: left !important;
                        padding-left: 0px !important;
                        padding-top: 2px !important;
                        padding-bottom: 2px !important;
                        background: transparent !important;
                        border: none !important;
                        box-shadow: none !important;
                    }
                    [data-testid="stBaseButton-tertiary"] p {
                        font-size: 13px !important;
                        text-align: left !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                # Sort by date
                user_events.sort(key=lambda x: x["date"])
                
                # Group same title+emoji+color+start+end across ALL dates (not limited to this month)
                # Collect all dates for each unique event key across the entire override dict
                grouped_ev: dict = {}
                for me in user_events:
                    ev = me["event"]
                    key = (
                        ev.get("title", ""), 
                        ev.get("emoji", "📌"), 
                        ev.get("display_color", ev.get("color", "#4f84ff")),
                        ev.get("start", "00:00"),
                        ev.get("end", "23:59")
                    )
                    grouped_ev.setdefault(key, []).append((me["date"], me["ev_idx"]))

                # For display, compute the FULL date range across all override entries
                for key, date_items in grouped_ev.items():
                    ev_title, ev_emoji, ev_color, ev_start, ev_end = key
                    # Collect all dates across whole override for this event key
                    all_dates_for_key = []
                    for d_str2, ev_list2 in override.items():
                        for e2 in ev_list2:
                            k2 = (
                                e2.get("title", ""),
                                e2.get("emoji", "📌"),
                                e2.get("display_color", e2.get("color", "#4f84ff")),
                                e2.get("start", "00:00"),
                                e2.get("end", "23:59")
                            )
                            if k2 == key and d_str2 not in all_dates_for_key:
                                all_dates_for_key.append(d_str2)
                    
                    dates = [item[0] for item in date_items]
                    first_date = date_items[0][0]
                    first_idx = date_items[0][1]
                    
                    date_str_formatted = _format_date_list(all_dates_for_key)
                    
                    col_color, col_btn = st.columns([1, 20])
                    with col_color:
                        st.markdown(f'<div style="width:4px; height:24px; background:{ev_color}; border-radius:2px; margin-top:8px;"></div>', unsafe_allow_html=True)
                    with col_btn:
                        if st.button(f"**{date_str_formatted}** {ev_emoji} {ev_title}", key=f"edit_btn_{year}_{month}_{first_date}_{first_idx}", type="tertiary", use_container_width=True):
                            edit_event_dialog(first_date, first_idx)
            else:
                st.write("本月無新增行程")
                    
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
                            # tasks without " - " separator are silently skipped
                                
                if progress:
                    for subj, details in progress.items():
                        st.markdown(f"<div style='font-size:15px; font-weight:bold; margin-top:6px; margin-bottom:2px;'>{subj}</div>", unsafe_allow_html=True)
                        for d in details:
                            st.markdown(f"<div style='font-size:14px; margin-left:10px; margin-bottom:4px;'>• {d}</div>", unsafe_allow_html=True)
                else:
                    st.write("本月無學習進度")
        
        st.markdown("---")
