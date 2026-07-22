import streamlit as st
import datetime
import time
import logic
from timeline_utils import render_timeline

def render_timer_page():
    st.markdown("## ⏱️ 計時器")
    
    now = datetime.datetime.now()
    weekday_map = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}
    today_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")
    
    st.markdown(f"### {today_str}(星期{weekday_map[now.weekday()]}) {time_str}")
    
    # 取得當前進度與預設進度
    app_state = st.session_state.get("app_state", {})
    monthly_plan = app_state.get("monthly_plan") or []
    today_sessions = [s for s in monthly_plan if s.get("date") == now.strftime("%Y-%m-%d")]
    
    daily_checks = st.session_state.get("daily_task_checks", {}).get(now.strftime("%Y-%m-%d"), {})
    
    # 計算現在進度 (第一個未完成的)
    current_progress = "無"
    current_idx = -1
    for i, s in enumerate(today_sessions):
        task_id = f"task_{i}"
        if not daily_checks.get(task_id, False):
            current_progress = f"{s.get('科目', '')} - {s.get('教材', '')}"
            current_idx = i
            break
            
    if current_progress == "無" and today_sessions:
        current_progress = "今日進度已全數完成！🎉"
        current_idx = len(today_sessions)
        
    # 計算預設進度 (當前時間應該做的)
    default_progress = "無"
    default_idx = -1
    now_minutes = now.hour * 60 + now.minute
    for i, s in enumerate(today_sessions):
        if "start_time" in s and "end_time" in s:
            sm = logic.get_minutes(s["start_time"])
            em = logic.get_minutes(s["end_time"])
            if sm <= now_minutes <= em:
                default_progress = f"{s.get('科目', '')} - {s.get('教材', '')}"
                default_idx = i
                break
            elif now_minutes < sm and default_idx == -1:
                # 這是下一個即將開始的進度
                default_progress = f"{s.get('科目', '')} - {s.get('教材', '')}"
                default_idx = i

    st.markdown(f"**現在進度:** {current_progress}")
    st.markdown(f"**預設進度:** {default_progress}")
    
    # 計算狀態
    status_msg = "無排定進度"
    status_color = "#999"
    if current_idx != -1 and default_idx != -1:
        if current_idx == default_idx:
            status_msg = "進度穩定"
            status_color = "#2ecc71" # 綠色
        elif current_idx < default_idx:
            status_msg = "進度落後"
            status_color = "#e74c3c" # 紅色
        else:
            status_msg = "進度提前"
            status_color = "#3498db" # 藍色
    elif current_idx == len(today_sessions) and today_sessions:
        status_msg = "進度提前"
        status_color = "#3498db"

    st.markdown(f"""
    <div style="border: 2px solid {status_color}; padding: 10px; border-radius: 8px; width: fit-content; margin-top: 10px; margin-bottom: 20px;">
        <span style="color: {status_color}; font-weight: bold; font-size: 18px;">{status_msg}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 左右排版
    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        st.markdown("### ⏳ 計時器")
        
        # 選擇當前進度項目
        task_options = [f"{s.get('科目', '')} - {s.get('教材', '')}" for s in today_sessions]
        if not task_options:
            task_options = ["無任務"]
            
        default_index = 0
        if current_idx != -1 and current_idx < len(task_options):
            default_index = current_idx
            
        selected_task = st.selectbox("選擇當前進度項目", task_options, index=default_index)
        
        # 計時器狀態
        if "timer_start_time" not in st.session_state:
            st.session_state.timer_start_time = None
            
        if "timer_records" not in st.session_state:
            st.session_state.timer_records = {}
            
        if st.session_state.timer_start_time is None:
            if st.button("▶ 開始", use_container_width=True, type="primary"):
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_selected_task = selected_task
                st.rerun()
            
            st.markdown("""
            <div style="font-size: 64px; font-weight: bold; font-family: monospace; text-align: center; margin: 20px 0; padding: 20px; background-color: #f0f2f6; border-radius: 12px;">
                00:00
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button("⏹ 結束", use_container_width=True):
                end_time = time.time()
                elapsed = end_time - st.session_state.timer_start_time
                
                # 紀錄起來
                today_key = now.strftime("%Y-%m-%d")
                if today_key not in st.session_state.timer_records:
                    st.session_state.timer_records[today_key] = []
                    
                start_dt = datetime.datetime.fromtimestamp(st.session_state.timer_start_time)
                end_dt = datetime.datetime.fromtimestamp(end_time)
                
                # 找對應的 session 來取得顏色，或預設顏色
                task_color = "#4f84ff"
                for s in today_sessions:
                    if f"{s.get('科目', '')} - {s.get('教材', '')}" == st.session_state.timer_selected_task:
                        task_color = s.get("color", "#4f84ff")
                        break
                
                st.session_state.timer_records[today_key].append({
                    "title": st.session_state.timer_selected_task,
                    "start": start_dt.strftime("%H:%M"),
                    "end": end_dt.strftime("%H:%M"),
                    "duration_seconds": elapsed,
                    "color": task_color,
                    "emoji": "⏳"
                })
                
                st.session_state.timer_start_time = None
                st.rerun()
                
            # 即時更新的計時器 (使用 JavaScript)
            start_ts = st.session_state.timer_start_time
            html_code = f"""
            <div id="live-timer" style="font-size: 64px; font-weight: bold; font-family: monospace; text-align: center; margin: 20px 0; padding: 20px; background-color: #e8f0fe; border-radius: 12px; color: #1a73e8;">
                00:00
            </div>
            <script>
                const startTs = {start_ts} * 1000; // JS uses ms
                const timerEl = document.getElementById("live-timer");
                
                setInterval(() => {{
                    const now = Date.now();
                    const diffMs = now - startTs;
                    let diffSec = Math.floor(diffMs / 1000);
                    
                    // Cap at 179:59 (10799 seconds)
                    if (diffSec > 10799) diffSec = 10799; 
                    
                    const min = Math.floor(diffSec / 60);
                    const sec = diffSec % 60;
                    
                    timerEl.innerText = String(min).padStart(2, '0') + ":" + String(sec).padStart(2, '0');
                }}, 1000);
            </script>
            """
            st.components.v1.html(html_code, height=150)
            
    with col_right:
        st.markdown("### 📊 時間軸")
        
        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown("#### 預計進度")
            # 轉換 today_sessions 為 timeline 格式
            expected_events = []
            for s in today_sessions:
                if "start_time" in s and "end_time" in s:
                    expected_events.append({
                        "title": f"{s.get('科目', '')} ({s.get('教材', '')})",
                        "start": s["start_time"],
                        "end": s["end_time"],
                        "color": s.get("color", "#4f84ff"),
                        "emoji": "📖"
                    })
            if expected_events:
                render_timeline(expected_events, title="")
            else:
                st.info("今日無預計進度")
                
        with tc2:
            st.markdown("#### 實際進度")
            actual_events = st.session_state.timer_records.get(now.strftime("%Y-%m-%d"), [])
            if actual_events:
                render_timeline(actual_events, title="")
            else:
                st.info("尚無實際計時紀錄")
