from __future__ import annotations

import json
import streamlit as st
import storage

def render_settings_page() -> None:
    st.title("⚙️ 計畫設定")
    st.markdown("在此管理您的讀書計畫基本資訊、資料備份與安全性選項。")
    st.markdown("---")

    plan_id = st.session_state.get("current_plan_id")
    if not plan_id:
        st.warning("⚠️ 目前未選擇任何計畫，請先由頂部選單回到計畫列表。")
        return

    # 1. 基本設定
    st.subheader("📌 基本資訊設定")
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
                st.success("✅ 基本資訊已成功更新！")
                st.rerun()
            else:
                st.error("計畫名稱不能為空！")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. 資料管理與備份
    st.subheader("📦 資料與備份")
    with st.container(border=True):
        st.markdown("**匯出與備份計畫資料**")
        st.caption("您可以下載此計畫的 JSON 完整資料作為備份。")

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
        st.markdown("**打卡紀錄管理**")
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

    # 3. 危險區域
    st.subheader("🚨 危險區域")
    with st.container(border=True):
        st.markdown("<p style='color: #ff4b4b; font-weight: bold;'>刪除此讀書計畫</p>", unsafe_allow_html=True)
        st.caption("警告：刪除計畫後，所有相關排程與紀錄將無法復原。")

        if st.button("🗑️ 刪除目前計畫", key="btn_delete_current_plan", type="secondary"):
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
