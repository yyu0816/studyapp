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
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    start = first_day - timedelta(days=first_day.weekday())
    end = last_day + timedelta(days=(6 - last_day.weekday()))
    weeks: list[list[date]] = []
    current = start
    while current <= end:
        weeks.append([current + timedelta(days=i) for i in range(7)])
        current += timedelta(days=7)
    return weeks


def _render_day_cell(day: date, item: dict[str, Any] | None, is_current_month: bool) -> None:
    day_str = day.strftime("%Y-%m-%d")
    label = day.strftime("%d")
    style = "padding:12px; min-height:130px; border-radius:14px;"
    if not is_current_month:
        st.markdown(
            f"<div style='{style} color:#aaa; background:#fafafa; border:1px solid transparent;'></div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"<div style='{style} border:1px solid #e3e3e3; background:#fff;'>", unsafe_allow_html=True)
    if st.button(label, key=f"select_day_{day_str}"):
        st.session_state["selected_day"] = day_str

    if item and item.get("fixed_events"):
        for event in item.get("fixed_events", []):
            if not event.get("show_on_calendar", True):
                continue
            emoji = event.get("emoji", "📌")
            color = event.get("display_color", event.get("color", "#4f84ff"))
            st.markdown(
                f"<div style='margin-top:8px; padding:6px; border-radius:12px; background:{color}; color:#fff; font-size:12px;'>"
                f"{emoji} {event.get('title', '')}"
                f"</div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def _ensure_daily_overrides() -> dict[str, list[dict[str, Any]]]:
    if "daily_override_events" not in st.session_state:
        st.session_state["daily_override_events"] = {}
    return st.session_state["daily_override_events"]


def _render_date_preview(selected_day: str, item: dict[str, Any]) -> None:
    daily_overrides = _ensure_daily_overrides()
    overrides = daily_overrides.get(selected_day, [])
    st.markdown("---")
    st.markdown(f"### {selected_day} 預覽")
    st.markdown(
        "<div style='padding:18px; border-radius:18px; background:#f4f7fb; box-shadow:0 10px 30px rgba(0,0,0,0.06);'>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-bottom:14px;'><strong>當天須完成讀書內容</strong></div>", unsafe_allow_html=True)
    if item.get("tasks"):
        for task in item.get("tasks", []):
            st.markdown(f"<div style='margin-bottom:8px;'>• {task}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div>尚未指定讀書內容</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:18px 0 12px;'><strong>當日行程</strong></div>", unsafe_allow_html=True)
    if item.get("fixed_events") or overrides:
        for event in item.get("fixed_events", []) + overrides:
            if not event.get("show_on_calendar", True):
                continue
            emoji = event.get("emoji", "📌")
            color = event.get("display_color", event.get("color", "#4f84ff"))
            title = event.get("title", "未命名行程")
            start = event.get("start", "")
            end = event.get("end", "")
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding:12px; border-radius:14px; background:{color}; color:#fff;'>"
                f"<span>{emoji} {title}</span>"
                f"<span style='font-size:12px;'>{start} - {end}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("<div>目前無當日行程</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:18px 0 12px;'><strong>新增或刪除當日行程</strong></div>", unsafe_allow_html=True)
    title_value = st.text_input("行程名稱", key=f"daily_event_title_{selected_day}")
    start_value = st.text_input("開始時間", key=f"daily_event_start_{selected_day}")
    end_value = st.text_input("結束時間", key=f"daily_event_end_{selected_day}")
    emoji_value = st.text_input("表情符號", value="📌", key=f"daily_event_emoji_{selected_day}")
    color_value = st.text_input("顏色(色碼)", value="#4f84ff", key=f"daily_event_color_{selected_day}")

    if st.button("新增當日行程", key=f"add_daily_event_{selected_day}"):
        if title_value.strip():
            daily_overrides.setdefault(selected_day, []).append(
                {
                    "title": title_value.strip(),
                    "start": start_value.strip(),
                    "end": end_value.strip(),
                    "emoji": emoji_value.strip() or "📌",
                    "color": color_value.strip() or "#4f84ff",
                    "display_color": color_value.strip() or "#4f84ff",
                    "show_on_calendar": True,
                }
            )
            st.success("已新增當日行程。")

    if overrides:
        for index, event in enumerate(list(overrides)):
            if st.button(f"刪除：{event.get('title','')}", key=f"del_daily_event_{selected_day}_{index}"):
                overrides.pop(index)
                st.session_state["daily_override_events"] = daily_overrides
                st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_monthly_plan_page() -> None:
    st.subheader("月曆與讀書計畫")
    st.caption("月曆上只顯示每月格局，點選日期可查看當日預覽。")

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
        header_cols = st.columns(7)
        for col, label in zip(header_cols, headers):
            with col:
                st.markdown(f"**{label}**")

        weeks = _month_calendar_dates(year, month)
        for week in weeks:
            cols = st.columns(7)
            for col, day in zip(cols, week):
                with col:
                    day_str = day.strftime("%Y-%m-%d")
                    item = plan_by_date.get(day_str)
                    is_current_month = day.month == month and start_date <= day <= end_date
                    _render_day_cell(day, item, is_current_month)

    selected_day = st.session_state.get("selected_day")
    if selected_day and selected_day in plan_by_date:
        _render_date_preview(selected_day, plan_by_date[selected_day])
    elif selected_day:
        st.info("目前選擇的日期不在計畫範圍內。請選擇其他日期。")
