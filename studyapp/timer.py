import streamlit as st
import datetime
import time
import logic
from timeline_utils import render_timeline

def render_timer_page():
    # Use UTC+8 for Taiwan local time
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    weekday_map = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}
    today_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")
    
    st.markdown(f"### {today_str}(星期{weekday_map[now.weekday()]}) {time_str}")
    
    # 取得當前進度與預設進度
    app_state = st.session_state.get("app_state", {})
    monthly_plan = app_state.get("monthly_plan") or []
    today_sessions = [s for s in monthly_plan if s.get("date") == now.strftime("%Y-%m-%d")]
    
    daily_checks = st.session_state.get("daily_task_checks", {}).get(now.strftime("%Y-%m-%d"), {})
    
    # 格式化科目名稱
    def format_task(s):
        subj = s.get('科目', '')
        mat = s.get('教材', '')
        if not mat or mat == '-' or subj == mat:
            return subj
        return f"{subj} - {mat}"

    # 判斷該 session 是否在打卡中已完成
    def is_session_done(s):
        subj_mat_prefix = f"{s.get('科目', '')} - {s.get('教材', '')}："
        for task_name, checked in daily_checks.items():
            if task_name.startswith(subj_mat_prefix) and checked:
                return True
        return False

    # 計算現在進度 (第一個未完成的)
    current_progress = "無"
    current_idx = -1
    for i, s in enumerate(today_sessions):
        if not is_session_done(s):
            current_progress = format_task(s)
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
                default_progress = format_task(s)
                default_idx = i
                break
            elif now_minutes < sm and default_idx == -1:
                # 這是下一個即將開始的進度
                default_progress = format_task(s)
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
    
    
    # 左右排版
    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        st.markdown("### ⏳ 計時器")
        
        st.markdown("#### 選擇計時進度")
        
        # 取得所有有安排進度的日期
        all_dates = sorted(list(set(s.get("date") for s in monthly_plan if s.get("date"))))
        if not all_dates:
            all_dates = [now.strftime("%Y-%m-%d")]
            
        default_date_idx = all_dates.index(now.strftime("%Y-%m-%d")) if now.strftime("%Y-%m-%d") in all_dates else 0
        selected_date = st.selectbox("選擇日期", all_dates, index=default_date_idx)
        
        sessions_for_selected_date = [s for s in monthly_plan if s.get("date") == selected_date]
        
        # 去除重複的選項 (但保留順序)
        seen = set()
        task_options = []
        for s in sessions_for_selected_date:
            name = format_task(s)
            if name not in seen:
                seen.add(name)
                task_options.append(name)
        
        if not task_options:
            task_options = ["無任務"]
            
        default_task_idx = 0
        if selected_date == now.strftime("%Y-%m-%d") and current_idx != -1 and current_idx < len(task_options):
            default_task_idx = current_idx
            
        selected_task = st.selectbox("選擇項目", task_options, index=default_task_idx)
        
        # 計時器狀態
        if "timer_state" not in st.session_state:
            st.session_state.timer_state = "stopped"
            st.session_state.timer_start_time = None
            st.session_state.timer_accumulated_sec = 0.0
            
        if "timer_records" not in st.session_state:
            st.session_state.timer_records = {}
            
        if st.session_state.timer_state == "stopped":
            if st.button("▶ 開始", use_container_width=True, type="primary"):
                st.session_state.timer_state = "running"
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_accumulated_sec = 0.0
                st.session_state.timer_selected_task = selected_task
                st.rerun()
            
            st.markdown("""
            <div style="font-size: 64px; font-weight: bold; font-family: monospace; text-align: center; margin: 20px 0; padding: 20px; background-color: #f0f2f6; border-radius: 12px;">
                00:00
            </div>
            """, unsafe_allow_html=True)
        else:
            bc1, bc2 = st.columns(2)
            
            if st.session_state.timer_state == "running":
                with bc1:
                    if st.button("⏸ 暫停", use_container_width=True):
                        elapsed_since_start = time.time() - st.session_state.timer_start_time
                        st.session_state.timer_accumulated_sec += elapsed_since_start
                        st.session_state.timer_state = "paused"
                        st.session_state.timer_start_time = None
                        st.rerun()
            elif st.session_state.timer_state == "paused":
                with bc1:
                    if st.button("▶ 繼續", use_container_width=True, type="primary"):
                        st.session_state.timer_start_time = time.time()
                        st.session_state.timer_state = "running"
                        st.rerun()
                        
            with bc2:
                if st.button("⏹ 結束", use_container_width=True):
                    total_elapsed = st.session_state.timer_accumulated_sec
                    if st.session_state.timer_state == "running":
                        total_elapsed += (time.time() - st.session_state.timer_start_time)
                    
                    # 紀錄起來，確保時間是本地時間
                    today_key = now.strftime("%Y-%m-%d")
                    if today_key not in st.session_state.timer_records:
                        st.session_state.timer_records[today_key] = []
                        
                    end_dt = now
                    start_dt = end_dt - datetime.timedelta(seconds=total_elapsed)
                    
                    # 找對應的 session 來取得顏色，或預設顏色
                    task_color = "#4f84ff"
                    for s in today_sessions:
                        if format_task(s) == st.session_state.timer_selected_task:
                            task_color = s.get("color", "#4f84ff")
                            break
                    
                    st.session_state.timer_records[today_key].append({
                        "title": st.session_state.timer_selected_task,
                        "start": start_dt.strftime("%H:%M"),
                        "end": end_dt.strftime("%H:%M"),
                        "duration_seconds": total_elapsed,
                        "color": task_color,
                        "emoji": "⏳"
                    })
                    
                    st.session_state.timer_state = "stopped"
                    st.session_state.timer_start_time = None
                    st.session_state.timer_accumulated_sec = 0.0
                    st.rerun()
                    
            # 即時更新的計時器 (使用 JavaScript)
            if st.session_state.timer_state == "running":
                elapsed_sec = st.session_state.timer_accumulated_sec + (time.time() - st.session_state.timer_start_time)
                is_running = "true"
            else:
                elapsed_sec = st.session_state.timer_accumulated_sec
                is_running = "false"
                
            html_code = f"""
            <div id="live-timer" style="font-size: 64px; font-weight: bold; font-family: monospace; text-align: center; margin: 20px 0; padding: 20px; border-radius: 12px; transition: all 0.3s ease;">
                00:00
            </div>
            <script>
                // 網頁載入時的基準時間
                const initialElapsedMs = {elapsed_sec} * 1000;
                const renderTimeMs = Date.now();
                const timerEl = document.getElementById("live-timer");
                const isRunning = {is_running};
                
                function formatTime(diffMs) {{
                    let diffSec = Math.floor(diffMs / 1000);
                    if (diffSec < 0) diffSec = 0;
                    if (diffSec > 10799) diffSec = 10799; 
                    const min = Math.floor(diffSec / 60);
                    const sec = diffSec % 60;
                    return String(min).padStart(2, '0') + ":" + String(sec).padStart(2, '0');
                }}
                
                if (isRunning) {{
                    timerEl.style.backgroundColor = "#e8f0fe";
                    timerEl.style.color = "#1a73e8";
                    setInterval(() => {{
                        const now = Date.now();
                        const diffMs = (now - renderTimeMs) + initialElapsedMs;
                        timerEl.innerText = formatTime(diffMs);
                    }}, 1000);
                }} else {{
                    // 暫停狀態
                    timerEl.innerText = formatTime(initialElapsedMs);
                    timerEl.style.backgroundColor = "#fff3cd";
                    timerEl.style.color = "#856404";
                }}
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
                        "title": format_task(s),
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
