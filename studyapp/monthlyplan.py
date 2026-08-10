from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
from dailycheck import COLOR_OPTIONS, EMOJI_OPTIONS, render_emoji_picker
from logic import calculate_daily_available_sessions
import logic

def _sync_hex_to_cp(hex_key: str, cp_key: str):
    val = st.session_state.get(hex_key, "")
    if val.startswith("#") and len(val) == 7:
        st.session_state[cp_key] = val


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

def _trigger_reschedule_if_needed():
    plan_data = st.session_state.get("plan") or st.session_state.get("app_state", {}).get("plan")
    if not plan_data:
        current_id = st.session_state.get("current_plan_id")
        if current_id:
            import storage
            saved = storage.load_plan(current_id)
            if saved:
                plan_data = saved.get("plan") or saved.get("app_state", {}).get("plan")

    if plan_data:
        # Sync latest daily_override_events into plan_data
        override_events = st.session_state.get("daily_override_events", {})
        plan_data["daily_override_events"] = override_events
        st.session_state["plan"] = plan_data
        st.session_state.setdefault("app_state", {})["plan"] = plan_data

        import logic
        from studyapp import build_monthly_plan
        import storage

        existing_schedule = st.session_state.get("app_state", {}).get("monthly_plan")
        new_schedule = logic.generate_daily_schedule(
            plan_data,
            existing_schedule=existing_schedule,
            reschedule_from_date=date.today()
        )
        st.session_state.setdefault("app_state", {})["monthly_plan"] = new_schedule
        st.session_state["monthly_plan"] = build_monthly_plan(plan_data, new_schedule)
        storage.save_current_state()
    st.rerun()

@st.dialog("新增行程")
def add_event_dialog(day_str: str):
    _title_key = "_add_dlg_title"
    title = st.text_input("行程名稱", key=_title_key)

    # Auto-sync end_date when start_date changes
    _sd_key = "_add_dlg_start"
    _ed_key = "_add_dlg_end"
    init_day = _parse_date(day_str) if day_str else date.today()
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

    is_all_day = st.checkbox("整天", value=True, key="_add_dlg_all_day")
    start_time, end_time = "00:00", "23:59"
    if not is_all_day:
        col1, col2 = st.columns(2)
        with col1:
            sv = st.time_input("開始時間", key="_add_dlg_st")
            if sv: start_time = sv.strftime("%H:%M")
        with col2:
            ev = st.time_input("結束時間", key="_add_dlg_et")
            if ev: end_time = ev.strftime("%H:%M")

    emoji = render_emoji_picker("表情符號", "📌", "add_event_dlg")
    color_option = st.selectbox("顏色", COLOR_OPTIONS, format_func=lambda x: x["name"], key="_add_dlg_color_sel")
    preset_color = color_option["value"] if isinstance(color_option, dict) else color_option
    if isinstance(color_option, dict):
        st.markdown(f"<div style='display:inline-block;width:20px;height:20px;border-radius:4px;background:{preset_color};vertical-align:middle;margin-right:6px;'></div> {color_option['name']}", unsafe_allow_html=True)
    use_custom_color = st.checkbox("使用自訂顏色", key="add_custom_color_cb")
    if use_custom_color:
        st.caption("※ 若選擇器無反應，可直接輸入 HEX 色號 (如 #ff0000)")
        c1, c2 = st.columns([1, 2])
        with c1:
            if "add_dlg_cp" not in st.session_state:
                st.session_state["add_dlg_cp"] = preset_color
            picked_color = st.color_picker("顏色", key="add_dlg_cp", label_visibility="collapsed")
        with c2:
            hex_val = st.text_input("HEX", value=picked_color, key="add_dlg_hex", label_visibility="collapsed", on_change=_sync_hex_to_cp, args=("add_dlg_hex", "add_dlg_cp"))
            
        if hex_val.startswith("#") and len(hex_val) == 7:
            color = hex_val
        else:
            color = picked_color
    else:
        color = preset_color

    concurrent_with_study = st.checkbox("是否可和讀書計畫並行？", value=False, key="_add_dlg_concurrent")

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("儲存行程", use_container_width=True, type="primary", key="btn_save_add_event"):
            if not title:
                st.error("請輸入行程名稱")
                return
            if start_date > end_date:
                st.error("開始日期不能晚於結束日期")
                return
            # clean up temp keys
            st.session_state.pop(_title_key, None)
            st.session_state.pop(_sd_key, None)
            st.session_state.pop(_ed_key, None)
            st.session_state.pop("_add_dlg_all_day", None)
            st.session_state.pop("_add_dlg_concurrent", None)
            st.session_state.pop("add_dlg_cp", None)
            st.session_state.pop("show_add_event_dialog", None)

            st.session_state.setdefault("daily_override_events", {})
            cur = start_date
            while cur <= end_date:
                cs = cur.strftime("%Y-%m-%d")
                st.session_state["daily_override_events"].setdefault(cs, []).append({
                    "title": title, "start": start_time, "end": end_time,
                    "emoji": emoji, "color": color, "display_color": color,
                    "is_all_day": is_all_day, "show_on_calendar": True,
                    "concurrent_with_study": concurrent_with_study,
                })
                cur += timedelta(days=1)
            _trigger_reschedule_if_needed()
    with col_cancel:
        if st.button("取消", use_container_width=True, type="secondary", key="btn_cancel_add_event"):
            st.session_state.pop("show_add_event_dialog", None)
            st.rerun()

@st.dialog("編輯行程")
def edit_event_dialog(date_str: str, ev_idx: int):
    override = st.session_state.get("daily_override_events", {})
    ev_list_for_date = override.get(date_str, [])
    if ev_idx >= len(ev_list_for_date):
        st.error("找不到行程")
        if st.button("關閉", use_container_width=True):
            st.session_state.pop("show_edit_event_dialog", None)
            st.rerun()
        return
        
    ev = ev_list_for_date[ev_idx]

    title_orig = ev.get("title", "")
    emoji_orig = ev.get("emoji", "📌")
    color_orig = ev.get("display_color", ev.get("color", "#4f84ff"))
    is_all_day_orig = ev.get("is_all_day", True)
    start_time_orig = ev.get("start", "00:00")
    end_time_orig = ev.get("end", "23:59")
    concurrent_orig = ev.get("concurrent_with_study", False)
    
    # Find all dates that have this exact event (for grouped editing)
    matching_dates = []
    for d_str, ev_list in override.items():
        for e in ev_list:
            if (e.get("title", "") == title_orig and 
                e.get("emoji", "📌") == emoji_orig and 
                e.get("display_color", e.get("color", "#4f84ff")) == color_orig and
                e.get("start", "00:00") == start_time_orig and
                e.get("end", "23:59") == end_time_orig):
                matching_dates.append(d_str)
                break # only count the date once

    _title_key = "_edit_dlg_title"
    if _title_key not in st.session_state:
        st.session_state[_title_key] = title_orig
    title = st.text_input("行程名稱", key=_title_key)

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
        new_start = st.session_state[_sd_key]
        if st.session_state[_ed_key] < new_start:
            st.session_state[_ed_key] = new_start

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("開始日期", key=_sd_key, on_change=_on_start_change)
    with col_d2:
        end_date = st.date_input("結束日期", key=_ed_key)

    _all_day_key = "_edit_dlg_all_day"
    if _all_day_key not in st.session_state:
        st.session_state[_all_day_key] = is_all_day_orig
    is_all_day = st.checkbox("整天", key=_all_day_key)
    
    start_time, end_time = "00:00", "23:59"
    if not is_all_day:
        col1, col2 = st.columns(2)
        with col1:
            try:
                st_obj = datetime.strptime(start_time_orig, "%H:%M").time()
            except:
                st_obj = datetime.strptime("00:00", "%H:%M").time()
            sv = st.time_input("開始時間", value=st_obj, key="_edit_dlg_st")
            if sv: start_time = sv.strftime("%H:%M")
        with col2:
            try:
                et_obj = datetime.strptime(end_time_orig, "%H:%M").time()
            except:
                et_obj = datetime.strptime("23:59", "%H:%M").time()
            ev_t = st.time_input("結束時間", value=et_obj, key="_edit_dlg_et")
            if ev_t: end_time = ev_t.strftime("%H:%M")

    emoji = render_emoji_picker("表情符號", emoji_orig, "edit_event_dlg")
    
    match_color_idx = 0
    for idx, opt in enumerate(COLOR_OPTIONS):
        if opt["value"] == color_orig:
            match_color_idx = idx
            break
    color_option = st.selectbox("顏色", COLOR_OPTIONS, index=match_color_idx, format_func=lambda x: x["name"], key="_edit_dlg_color_sel")
    preset_color = color_option["value"] if isinstance(color_option, dict) else color_option
    if isinstance(color_option, dict):
        st.markdown(f"<div style='display:inline-block;width:20px;height:20px;border-radius:4px;background:{preset_color};vertical-align:middle;margin-right:6px;'></div> {color_option['name']}", unsafe_allow_html=True)
    use_custom_color = st.checkbox("使用自訂顏色", key="edit_custom_color_cb")
    if use_custom_color:
        st.caption("※ 若選擇器無反應，可直接輸入 HEX 色號 (如 #ff0000)")
        c1, c2 = st.columns([1, 2])
        with c1:
            if "edit_dlg_cp" not in st.session_state:
                st.session_state["edit_dlg_cp"] = color_orig if color_orig.startswith("#") else preset_color
            picked_color = st.color_picker("顏色", key="edit_dlg_cp", label_visibility="collapsed")
        with c2:
            hex_val = st.text_input("HEX", value=picked_color, key="edit_dlg_hex", label_visibility="collapsed", on_change=_sync_hex_to_cp, args=("edit_dlg_hex", "edit_dlg_cp"))
            
        if hex_val.startswith("#") and len(hex_val) == 7:
            color = hex_val
        else:
            color = picked_color
    else:
        color = preset_color

    _concurrent_key = "_edit_dlg_concurrent"
    if _concurrent_key not in st.session_state:
        st.session_state[_concurrent_key] = concurrent_orig
    concurrent_with_study = st.checkbox("是否可和讀書計畫並行？", key=_concurrent_key)

    col_save, col_del = st.columns(2)
    with col_save:
        if st.button("儲存修改", use_container_width=True, type="primary", key="btn_save_edit_event"):
            if not title:
                st.error("請輸入行程名稱")
                return
            
            # Remove all old matching events across all dates
            for d_str in matching_dates:
                override[d_str] = [e for e in override[d_str] if not (
                    e.get("title", "") == title_orig and 
                    e.get("emoji", "📌") == emoji_orig and 
                    e.get("display_color", e.get("color", "#4f84ff")) == color_orig and
                    e.get("start", "00:00") == start_time_orig and
                    e.get("end", "23:59") == end_time_orig
                )]
                
            # Re-insert across new date range
            cur = start_date
            while cur <= end_date:
                cs = cur.strftime("%Y-%m-%d")
                st.session_state["daily_override_events"].setdefault(cs, []).append({
                    "title": title, "start": start_time, "end": end_time,
                    "emoji": emoji, "color": color, "display_color": color,
                    "is_all_day": is_all_day, "show_on_calendar": True,
                    "concurrent_with_study": concurrent_with_study,
                })
                cur += timedelta(days=1)
            st.session_state.pop(_title_key, None)
            st.session_state.pop(_sd_key, None)
            st.session_state.pop(_ed_key, None)
            st.session_state.pop(_all_day_key, None)
            st.session_state.pop(_concurrent_key, None)
            st.session_state.pop("edit_dlg_cp", None)
            st.session_state.pop("show_edit_event_dialog", None)
            _trigger_reschedule_if_needed()
    with col_del:
        if st.button("刪除此行程", use_container_width=True, type="secondary", key="btn_del_edit_event"):
            for d_str in matching_dates:
                for idx, event in enumerate(list(st.session_state["daily_override_events"].get(d_str, []))):
                    if (event.get("title", "") == title_orig and 
                        event.get("start", "") == start_time_orig and
                        event.get("end", "") == end_time_orig):
                        st.session_state["daily_override_events"][d_str].pop(idx)
                        break
            st.session_state.pop(_title_key, None)
            st.session_state.pop(_sd_key, None)
            st.session_state.pop(_ed_key, None)
            st.session_state.pop(_all_day_key, None)
            st.session_state.pop(_concurrent_key, None)
            st.session_state.pop("edit_dlg_cp", None)
            st.session_state.pop("show_edit_event_dialog", None)
            _trigger_reschedule_if_needed()

def _build_calendar_html(year: int, month: int, plan_by_date: dict, start_date: date, end_date: date) -> str:
    """Build a pure HTML table for the calendar month with clickable dates."""
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
            is_active = is_in_plan or has_override

            if is_in_plan:
                num_color = "#333"
                num_weight = "bold"
                bg = "#ffffff"
            elif has_override:
                num_color = "#888"
                num_weight = "normal"
                bg = "#f5f5f5"
            else:
                num_color = "#c0c0c0"
                num_weight = "normal"
                bg = "#fafafa"

            num_html = f'<div style="font-weight:{num_weight}; color:{num_color}; font-size:14px; margin-bottom:4px;">{day.day}</div>'

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
                        em = ev.get("emoji", "📌")
                        c = ev.get("display_color", ev.get("color", "#4f84ff"))
                        events_html += f'<div style="font-size:11px;font-weight:bold;color:#fff;padding:2px 6px;border-radius:5px;margin-top:3px;background:{c};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{em} {t}">{em} {t}</div>'

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

    if st.session_state.get("show_add_event_dialog"):
        add_event_dialog(st.session_state.get("add_event_dialog_day", ""))

    if st.session_state.get("show_edit_event_dialog"):
        e_date, e_idx = st.session_state["show_edit_event_dialog"]
        edit_event_dialog(e_date, e_idx)

    qp = st.query_params
    edit_val = qp.get("edit_event", None)
    
    if edit_val:
        st.query_params.clear()
        parts = edit_val.split("|")
        if len(parts) == 2:
            st.session_state["show_edit_event_dialog"] = (parts[0], int(parts[1]))
            st.rerun()

    for (year, month), _items in sorted(grouped.items()):
        st.markdown(f"### {year}年{month}月")

        col_cal, col_overview = st.columns([2, 1], gap="medium")

        with col_cal:
            # HTML Table Calendar
            calendar_html = _build_calendar_html(year, month, plan_by_date, start_date, end_date)
            st.markdown(calendar_html, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 🔍 查看單日詳細進度")
            st.write("*(請在此選擇日期以檢視當日的讀書量分配與行程)*")
            c_date, c_btn = st.columns([2, 1])
            with c_date:
                view_d = st.date_input("選擇日期", value=max(start_date, date(year, month, 1)), key=f"view_d_{year}_{month}", label_visibility="collapsed")
            with c_btn:
                if st.button("顯示當日進度", key=f"btn_view_{year}_{month}", use_container_width=True):
                    st.session_state["cal_view_date"] = view_d.strftime("%Y-%m-%d")
                    st.rerun()

            # 日期選擇觸發後將在頂部詳細視圖展開呈現

        with col_overview:
            st.markdown("#### 📅 行程總覽")
            
            # 新增行程按鈕
            if st.button("＋ 新增行程", key=f"add_btn_{year}_{month}", use_container_width=True, type="primary"):
                # Default to first day of current month within plan range
                default_day = max(start_date, date(year, month, 1))
                st.session_state["show_add_event_dialog"] = True
                st.session_state["add_event_dialog_day"] = default_day.strftime("%Y-%m-%d")
                st.rerun()
            
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
                            st.session_state["show_edit_event_dialog"] = (first_date, first_idx)
                            st.rerun()
            else:
                st.write("本月無新增行程")
                    
            st.markdown("#### 📖 月進度")
            with st.container(border=True):
                schedule_data = st.session_state.get("app_state", {}).get("monthly_plan") or []
                prefix = f"{year}-{month:02d}-"
                month_schedules = [s for s in schedule_data if s.get("date", "").startswith(prefix)]
                
                progress = {}
                if month_schedules:
                    for s in month_schedules:
                        subj = s.get("科目", "")
                        if subj == "總複習 (自由安排)":
                            continue
                        tgt = s.get("目標進度", "")
                        parts = tgt.split(" ")
                        if len(parts) == 2:
                            try:
                                val = float(parts[0])
                                unit = parts[1]
                                if subj not in progress:
                                    progress[subj] = {}
                                progress[subj][unit] = progress[subj].get(unit, 0) + val
                            except:
                                pass
                                
                if progress:
                    for subj, units in progress.items():
                        st.markdown(f"<div style='font-size:15px; font-weight:bold; margin-top:6px; margin-bottom:2px;'>{subj}</div>", unsafe_allow_html=True)
                        for unit, val in units.items():
                            val_str = f"{int(val)}" if val.is_integer() else f"{val:.1f}"
                            st.markdown(f"<div style='font-size:14px; margin-left:10px; margin-bottom:4px;'>• 共 {val_str} {unit}</div>", unsafe_allow_html=True)
                else:
                    st.write("本月無學習進度")

            # 每日詳細視圖 (位於月進度框框下方)
            cal_view_date = st.session_state.get("cal_view_date")
            if cal_view_date and cal_view_date.startswith(f"{year}-{month:02d}-"):
                st.markdown(f"#### 📌 {cal_view_date} 詳細進度")
                with st.container(border=True):
                    schedule_data = st.session_state.get("app_state", {}).get("monthly_plan") or []
                    daily_schedule = [s for s in schedule_data if s.get("date") == cal_view_date]
                    
                    st.markdown("**📖 當日讀書進度：**")
                    if daily_schedule:
                        grouped_tasks: dict[tuple[str, str, str, str], float] = {}
                        for item in daily_schedule:
                            subj = item.get("科目", "")
                            if subj == "總複習 (自由安排)" or not subj:
                                continue
                            mat = item.get("教材", "")
                            target = item.get("目標進度", "")
                            color = item.get("color", "#4f84ff")
                            parts = target.split(" ")
                            qty = 0.0
                            unit = "頁"
                            if len(parts) >= 2:
                                try:
                                    qty = float(parts[0])
                                    unit = parts[1]
                                except ValueError:
                                    pass
                            elif len(parts) == 1 and parts[0]:
                                try:
                                    qty = float(parts[0])
                                except ValueError:
                                    pass
                            key = (subj, mat, unit, color)
                            grouped_tasks[key] = grouped_tasks.get(key, 0.0) + qty

                        if grouped_tasks:
                            for (subj, mat, unit, color), total_qty in grouped_tasks.items():
                                qty_str = f"{int(total_qty)}" if total_qty.is_integer() else f"{total_qty:.1f}"
                                mat_str = f" ({mat})" if mat and mat != "-" else ""
                                st.markdown(f"- **{subj}**{mat_str}：{qty_str} {unit}")
                        else:
                            st.caption("今日為自由複習日 / 無指定讀書進度。")
                    else:
                        st.caption("今日無指定讀書進度。")
                    
                    # 顯示當日行程 (固定行程與特定行程)
                    events_today = []
                    override_events = st.session_state.get("daily_override_events", {}).get(cal_view_date, [])
                    events_today.extend(override_events)
                    
                    plan_fixed = st.session_state.get("plan", {}).get("fixed_events", [])
                    try:
                        view_dt = datetime.strptime(cal_view_date, "%Y-%m-%d").date()
                        weekday_map = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}
                        w_str = weekday_map[view_dt.weekday()]
                        for fe in plan_fixed:
                            if w_str in fe.get("weekdays", []) and fe.get("show_on_calendar", True):
                                events_today.append(fe)
                    except Exception:
                        pass

                    if events_today:
                        st.markdown("**🗓️ 當日行程：**")
                        for ev in events_today:
                            em = ev.get("emoji", "📌")
                            t = ev.get("title", "未命名行程")
                            s = ev.get("start", "")
                            e = ev.get("end", "")
                            time_str = f" ({s}~{e})" if s and e else ""
                            st.markdown(f"- {em} **{t}**{time_str}")

                    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
                    if st.button("✕ 關閉每日詳細視圖", key=f"close_daily_view_{year}_{month}", use_container_width=True):
                        st.session_state["cal_view_date"] = None
                        st.rerun()
        
        st.markdown("---")
