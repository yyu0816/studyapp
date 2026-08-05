from __future__ import annotations

import json
import streamlit as st
import storage

DEFAULT_THEME = {
    "bg_color": "#ffffff",
    "button_color": "#4f84ff",
    "navbar_bg_color": "#f8f9fa"
}

DEFAULT_ENABLED_PAGES = {
    "dashboard": True,
    "月計畫": True,
    "每日打卡與微調": True,
    "計時器": True
}

def render_settings_page() -> None:
    st.title("⚙️ 設定")
    st.markdown("您可以自由自訂顯示的功能頁面與外觀色彩風格。")
    st.markdown("---")

    plan_id = st.session_state.get("current_plan_id")
    if not plan_id:
        st.warning("⚠️ 目前未選擇任何計畫，請先由頂部選單回到計畫列表。")
        return

    # 初始化 state
    if "enabled_pages" not in st.session_state or not isinstance(st.session_state["enabled_pages"], dict):
        st.session_state["enabled_pages"] = DEFAULT_ENABLED_PAGES.copy()
    if "custom_theme" not in st.session_state or not isinstance(st.session_state["custom_theme"], dict):
        st.session_state["custom_theme"] = DEFAULT_THEME.copy()

    tab_features, tab_colors, tab_info = st.tabs(["🎛️ 功能選擇", "🎨 自定義色彩", "📌 基本與資料管理"])

    # ── 1. 功能選擇 ─────────────────────────────────────────────────────────────
    with tab_features:
        st.subheader("🎛️ 頁面功能顯示管理")
        st.markdown(
            "請勾選要在畫面上方選單中顯示的功能頁面。\n\n"
            "*(註：「計畫頁面」與「設定」為系統基礎核心，將保持固定顯示)*"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        enabled = st.session_state["enabled_pages"]

        with st.container(border=True):
            st.markdown("#### 可選功能頁面")
            show_dashboard = st.checkbox("📊 儀表板 (Dashboard)", value=enabled.get("dashboard", True), key="toggle_dashboard")
            show_monthly = st.checkbox("📅 月計畫 (月度排程與行事曆)", value=enabled.get("月計畫", True), key="toggle_monthly")
            show_daily = st.checkbox("📝 每日打卡與微調", value=enabled.get("每日打卡與微調", True), key="toggle_daily")
            show_timer = st.checkbox("⏱️ 讀書計時器", value=enabled.get("計時器", True), key="toggle_timer")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 儲存功能顯示設定", type="primary", key="btn_save_enabled_pages"):
                st.session_state["enabled_pages"] = {
                    "dashboard": show_dashboard,
                    "月計畫": show_monthly,
                    "每日打卡與微調": show_daily,
                    "計時器": show_timer
                }
                storage.save_current_state()
                st.success("✅ 功能頁面顯示設定已更新！")
                st.rerun()

    # ── 2. 自定義色彩 ─────────────────────────────────────────────────────────────
    with tab_colors:
        st.subheader("🎨 外觀與色彩自訂")
        st.markdown("您可以自由調整畫面背景、按鈕與主選單的色彩風格。")
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
                st.caption("頂部橫向選單列的背景顏色")

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
