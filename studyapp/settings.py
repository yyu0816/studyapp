from __future__ import annotations

import json
import streamlit as st
import storage

DEFAULT_THEME = {
    "bg_color": "#ffffff",
    "button_color": "#4f84ff",
    "navbar_bg_color": "#f8f9fa"
}

DEFAULT_ENABLED_FEATURES = {
    "page_dashboard": True, "dash_study_progress": True, "dash_weekly_chart": True, "dash_mood_pacing": True,
    "page_monthly": True, "monthly_calendar": True, "monthly_schedule": True, "monthly_events": True,
    "page_daily": True, "daily_timeline": True, "daily_checklist": True, "daily_mood": True, "daily_timeloss": True,
    "page_timer": True, "timer_clock": True, "timer_history": True
}

def render_settings_page() -> None:
    st.title("⚙️ 設定")
    st.markdown("您可以自由選擇頁面與子功能，並自訂頂部選單與畫面視覺色彩。")
    st.markdown("---")

    plan_id = st.session_state.get("current_plan_id")
    if not plan_id:
        st.warning("⚠️ 目前未選擇任何計畫，請先由頂部選單回到計畫列表。")
        return

    # 初始化 state
    if "enabled_features" not in st.session_state or not isinstance(st.session_state["enabled_features"], dict):
        st.session_state["enabled_features"] = DEFAULT_ENABLED_FEATURES.copy()
    if "custom_theme" not in st.session_state or not isinstance(st.session_state["custom_theme"], dict):
        st.session_state["custom_theme"] = DEFAULT_THEME.copy()

    tab_features, tab_colors, tab_info = st.tabs(["🎛️ 功能選擇", "🎨 自定義色彩", "📌 基本與資料管理"])

    # ── 1. 功能選擇 ─────────────────────────────────────────────────────────────
    with tab_features:
        st.subheader("🎛️ 頁面與子功能開關控制")
        st.markdown(
            "您可以選擇開啟/關閉整個功能頁面，或是進一步勾選控制頁面內的特定子功能。\n\n"
            "*(註：「計畫頁面」與「設定」為系統基礎核心，始終固定顯示)*"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        ef = st.session_state["enabled_features"]

        # --- 1. Dashboard ---
        with st.expander("📊 儀表板 (Dashboard) 功能設定", expanded=True):
            page_dash = st.checkbox("啟用「儀表板」整體頁面", value=ef.get("page_dashboard", True), key="chk_page_dashboard")
            st.markdown("---")
            st.markdown("**頁面內部子功能：**")
            c1, c2, c3 = st.columns(3)
            with c1:
                sub_dash_progress = st.checkbox("累積學習進度與圓餅圖", value=ef.get("dash_study_progress", True), key="chk_dash_progress", disabled=not page_dash)
            with c2:
                sub_dash_weekly = st.checkbox("每週讀書時數圖表", value=ef.get("dash_weekly_chart", True), key="chk_dash_weekly", disabled=not page_dash)
            with c3:
                sub_dash_mood = st.checkbox("心情與節奏步調趨勢", value=ef.get("dash_mood_pacing", True), key="chk_dash_mood", disabled=not page_dash)

        # --- 2. Monthly Plan ---
        with st.expander("📅 月計畫 (Monthly Plan) 功能設定", expanded=True):
            page_monthly = st.checkbox("啟用「月計畫」整體頁面", value=ef.get("page_monthly", True), key="chk_page_monthly")
            st.markdown("---")
            st.markdown("**頁面內部子功能：**")
            c1, c2, c3 = st.columns(3)
            with c1:
                sub_monthly_cal = st.checkbox("月度互動行事曆", value=ef.get("monthly_calendar", True), key="chk_monthly_cal", disabled=not page_monthly)
            with c2:
                sub_monthly_sch = st.checkbox("排程進度總覽表", value=ef.get("monthly_schedule", True), key="chk_monthly_sch", disabled=not page_monthly)
            with c3:
                sub_monthly_evt = st.checkbox("固定與特定日期行程", value=ef.get("monthly_events", True), key="chk_monthly_evt", disabled=not page_monthly)

        # --- 3. Daily Check-in ---
        with st.expander("📝 每日打卡與微調 功能設定", expanded=True):
            page_daily = st.checkbox("啟用「每日打卡與微調」整體頁面", value=ef.get("page_daily", True), key="chk_page_daily")
            st.markdown("---")
            st.markdown("**頁面內部子功能：**")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                sub_daily_time = st.checkbox("當日動態時間軸", value=ef.get("daily_timeline", True), key="chk_daily_time", disabled=not page_daily)
            with c2:
                sub_daily_check = st.checkbox("今日讀書進度打卡", value=ef.get("daily_checklist", True), key="chk_daily_check", disabled=not page_daily)
            with c3:
                sub_daily_mood = st.checkbox("心情與動力反饋", value=ef.get("daily_mood", True), key="chk_daily_mood", disabled=not page_daily)
            with c4:
                sub_daily_loss = st.checkbox("意外損失時間記錄", value=ef.get("daily_timeloss", True), key="chk_daily_loss", disabled=not page_daily)

        # --- 4. Timer ---
        with st.expander("⏱️ 讀書計時器 (Timer) 功能設定", expanded=True):
            page_timer = st.checkbox("啟用「讀書計時器」整體頁面", value=ef.get("page_timer", True), key="chk_page_timer")
            st.markdown("---")
            st.markdown("**頁面內部子功能：**")
            c1, c2 = st.columns(2)
            with c1:
                sub_timer_clock = st.checkbox("計時器與番茄鐘", value=ef.get("timer_clock", True), key="chk_timer_clock", disabled=not page_timer)
            with c2:
                sub_timer_hist = st.checkbox("歷史讀書計時紀錄", value=ef.get("timer_history", True), key="chk_timer_hist", disabled=not page_timer)

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn_save, col_btn_all = st.columns([2, 1])
        with col_btn_save:
            if st.button("💾 儲存功能選擇設定", type="primary", key="btn_save_features"):
                st.session_state["enabled_features"] = {
                    "page_dashboard": page_dash, "dash_study_progress": sub_dash_progress, "dash_weekly_chart": sub_dash_weekly, "dash_mood_pacing": sub_dash_mood,
                    "page_monthly": page_monthly, "monthly_calendar": sub_monthly_cal, "monthly_schedule": sub_monthly_sch, "monthly_events": sub_monthly_evt,
                    "page_daily": page_daily, "daily_timeline": sub_daily_time, "daily_checklist": sub_daily_check, "daily_mood": sub_daily_mood, "daily_timeloss": sub_daily_loss,
                    "page_timer": page_timer, "timer_clock": sub_timer_clock, "timer_history": sub_timer_hist
                }
                storage.save_current_state()
                st.success("✅ 功能頁面與子功能設定已更新！")
                st.rerun()
        with col_btn_all:
            if st.button("全選所有功能", key="btn_select_all_features"):
                st.session_state["enabled_features"] = DEFAULT_ENABLED_FEATURES.copy()
                storage.save_current_state()
                st.rerun()

    # ── 2. 自定義色彩 ─────────────────────────────────────────────────────────────
    with tab_colors:
        st.subheader("🎨 外觀與色彩自訂")
        st.markdown("您可以自由調整畫面背景、按鈕與主選單欄位的色彩風格。")
        st.markdown("<br>", unsafe_allow_html=True)

        theme = st.session_state["custom_theme"]
        curr_bg = theme.get("bg_color", "#ffffff")
        curr_btn = theme.get("button_color", "#4f84ff")
        curr_nav = theme.get("navbar_bg_color", "#f8f9fa")

        with st.container(border=True):
            st.markdown("#### 色彩設置")
            col_bg, col_btn, col_nav = st.columns(3)

            with col_bg:
                new_bg = st.color_picker("背景色", value=curr_bg, key="cp_bg_color")
                st.caption("應用程式整體背景顏色")

            with col_btn:
                new_btn = st.color_picker("按鈕顏色", value=curr_btn, key="cp_btn_color")
                st.caption("主要按鈕與主題色彩")

            with col_nav:
                new_nav = st.color_picker("主選單背景色", value=curr_nav, key="cp_nav_bg_color")
                st.caption("頂部橫向選單列整體背景顏色")

            st.markdown("---")
            st.markdown("#### 預設主題風格")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                if st.button("☀️ 預設明亮", key="theme_preset_light", use_container_width=True):
                    st.session_state["custom_theme"] = {"bg_color": "#ffffff", "button_color": "#4f84ff", "navbar_bg_color": "#f8f9fa"}
                    storage.save_current_state()
                    st.rerun()
            with col_p2:
                if st.button("🌙 莫蘭迪深色", key="theme_preset_dark", use_container_width=True):
                    st.session_state["custom_theme"] = {"bg_color": "#1e1e2e", "button_color": "#89b4fa", "navbar_bg_color": "#181825"}
                    storage.save_current_state()
                    st.rerun()
            with col_p3:
                if st.button("🌸 柔和粉紫", key="theme_preset_purple", use_container_width=True):
                    st.session_state["custom_theme"] = {"bg_color": "#faf5ff", "button_color": "#9333ea", "navbar_bg_color": "#f3e8ff"}
                    storage.save_current_state()
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            c_save_theme, c_reset_theme = st.columns([2, 1])
            with c_save_theme:
                if st.button("💾 儲存自訂色彩", type="primary", key="btn_save_theme"):
                    st.session_state["custom_theme"] = {
                        "bg_color": new_bg,
                        "button_color": new_btn,
                        "navbar_bg_color": new_nav
                    }
                    storage.save_current_state()
                    st.success("✅ 色彩風格已更新！")
                    st.rerun()
            with c_reset_theme:
                if st.button("🔄 重置為預設色彩", key="btn_reset_theme"):
                    st.session_state["custom_theme"] = DEFAULT_THEME.copy()
                    storage.save_current_state()
                    st.rerun()

    # ── 3. 基本與資料管理 ────────────────────────────────────────────────────────
    with tab_info:
        st.subheader("📌 基本資訊")
        with st.container(border=True):
            curr_name = st.session_state.get("plan_name", "")
            curr_goal = st.session_state.get("plan_goal", "")

            new_name = st.text_input("計畫名稱", value=curr_name, key="settings_plan_name_input")
            new_goal = st.text_area("計畫目標", value=curr_goal, placeholder="例如：考取多益 850 分、進入班排前 5 名...", key="settings_plan_goal_input")

            if st.button("💾 儲存基本資訊", type="primary", key="btn_save_basic_settings"):
                if new_name.strip():
                    st.session_state["plan_name"] = new_name.strip()
                    st.session_state["plan_goal"] = new_goal.strip()
                    storage.save_current_state()
                    st.success("✅ 基本資訊已更新！")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("📦 資料備份與清理")
        with st.container(border=True):
            plan_data = storage.load_plan(plan_id) or {}
            json_str = json.dumps(plan_data, ensure_ascii=False, indent=2)
            filename = f"plan_backup_{plan_id[:8]}.json"

            st.download_button(
                label="📥 下載計畫備份 (JSON)",
                data=json_str,
                file_name=filename,
                mime="application/json",
                key="btn_download_plan_json"
            )

            st.markdown("---")
            if st.button("🧹 重置每日打卡與反饋紀錄", key="btn_clear_checkin_logs"):
                st.session_state["daily_log"] = None
                st.session_state["daily_saved"] = False
                if "daily_task_checks" in st.session_state:
                    st.session_state["daily_task_checks"] = {}
                if "daily_moods" in st.session_state:
                    st.session_state["daily_moods"] = {}
                if "daily_feedback" in st.session_state:
                    st.session_state["daily_feedback"] = {}
                if "time_loss_records" in st.session_state:
                    st.session_state["time_loss_records"] = {}
                storage.save_current_state()
                st.success("✅ 打卡與反饋紀錄已重置！")
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("🚨 危險區域")
        with st.container(border=True):
            if st.button("🗑️ 刪除目前計畫", key="btn_delete_current_plan"):
                st.session_state["confirm_delete_plan"] = True

            if st.session_state.get("confirm_delete_plan"):
                st.error("⚠️ 您確定要永久刪除此計畫嗎？這項操作無法復原！")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("🔥 確定刪除", key="btn_confirm_delete_yes", type="primary"):
                        storage.delete_plan(plan_id)
                        st.session_state["current_plan_id"] = None
                        st.session_state["confirm_delete_plan"] = False
                        st.success("計畫已順利刪除。")
                        st.rerun()
                with col_cancel:
                    if st.button("❌ 取消", key="btn_confirm_delete_no"):
                        st.session_state["confirm_delete_plan"] = False
                        st.rerun()
