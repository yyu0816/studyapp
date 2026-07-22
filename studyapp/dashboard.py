import streamlit as st
import pandas as pd
import altair as alt
import random
from datetime import date, timedelta

def get_mock_weekly_study_duration(week_offset=0):
    """Generate actual weekly study duration from daily_task_checks."""
    today = date.today()
    target_date = today + timedelta(days=week_offset * 7)
    start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    monthly_plan = st.session_state.get("app_state", {}).get("monthly_plan", [])
    daily_task_checks = st.session_state.get("daily_task_checks", {})
    
    data = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        duration = 0.0
        
        checks = daily_task_checks.get(day_str, {})
        day_slots = [s for s in monthly_plan if s.get("date") == day_str]
        
        for s in day_slots:
            subj = s.get("科目", "")
            mat = s.get("教材", "")
            prefix = f"{subj} - {mat}："
            for task_str, is_checked in checks.items():
                if is_checked and task_str.startswith(prefix):
                    duration += 1.0
                    break
        
        h = int(duration)
        m = int((duration - h) * 60)
        duration_str = f"{h:02d}h {m:02d}m"
        
        data.append({
            "date": day_str,
            "date_label": day.strftime("%m/%d"),
            "duration": duration,
            "duration_str": duration_str
        })
    return pd.DataFrame(data), start_of_week, end_of_week

def get_subject_study_analysis() -> tuple[list[dict], pd.DataFrame]:
    """Get actual subject study time from daily_task_checks."""
    plan = st.session_state.get("plan", {})
    subjects = plan.get("subjects", [])
    if not subjects:
        return [], pd.DataFrame()
        
    daily_task_checks = st.session_state.get("daily_task_checks", {})
    monthly_plan = st.session_state.get("app_state", {}).get("monthly_plan", [])
    
    subject_totals_map = {}
    daily_data = []
    
    for subj in subjects:
        name = subj.get("name", "未命名科目")
        color = subj.get("color", "#4f84ff")
        subject_totals_map[name] = {"name": name, "color": color, "total_hours": 0.0}
        
    for day_str, checks in daily_task_checks.items():
        day_slots = [s for s in monthly_plan if s.get("date") == day_str]
        for subj in subjects:
            name = subj.get("name", "未命名科目")
            daily_hours = 0.0
            
            for s in day_slots:
                if s.get("科目") == name:
                    mat = s.get("教材", "")
                    prefix = f"{name} - {mat}："
                    for task_str, is_checked in checks.items():
                        if is_checked and task_str.startswith(prefix):
                            daily_hours += 1.0
                            break
            
            if daily_hours > 0:
                subject_totals_map[name]["total_hours"] += daily_hours
                daily_data.append({
                    "date": day_str,
                    "subject": name,
                    "hours": daily_hours
                })
                
    subject_totals = list(subject_totals_map.values())
    subject_totals.sort(key=lambda x: x["total_hours"], reverse=True)
    
    df_daily = pd.DataFrame(daily_data) if daily_data else pd.DataFrame(columns=["date", "subject", "hours"])
    return subject_totals, df_daily

def get_mock_mood_history(month_offset=0):
    """Generate actual mood data for 30 days starting from the target month's 1st day."""
    today = date.today()
    month_target = today.month + month_offset - 1
    year = today.year + month_target // 12
    month = month_target % 12 + 1
    month_str = f"{year}年{month}月"
    
    start_date = date(year, month, 1)
    daily_moods = st.session_state.get("daily_moods", {})
    
    data = []
    for i in range(30):
        day = start_date + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        
        mood_data = daily_moods.get(day_str, {})
        if mood_data.get("submitted"):
            data.append(mood_data.get("mood", 0))
        else:
            data.append(0)
            
    return data, month_str

def get_overall_progress():
    """Calculate overall completion rate and check-in days."""
    daily_task_checks = st.session_state.get("daily_task_checks", {})
    monthly_plan = st.session_state.get("app_state", {}).get("monthly_plan", [])
    from datetime import datetime
    
    today = date.today()
    
    checkin_days = 0
    for day_str, checks in daily_task_checks.items():
        if any(checks.values()):
            checkin_days += 1
            
    total_slots_this_month = 0
    completed_slots_this_month = 0
    
    for s in monthly_plan:
        d_str = s.get("date")
        if not d_str: continue
        try:
            d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
            if d_obj.month == today.month and d_obj.year == today.year:
                total_slots_this_month += 1
                subj = s.get("科目", "")
                mat = s.get("教材", "")
                prefix = f"{subj} - {mat}："
                checks = daily_task_checks.get(d_str, {})
                for task_str, is_checked in checks.items():
                    if is_checked and task_str.startswith(prefix):
                        completed_slots_this_month += 1
                        break
        except: pass
        
    completion_rate = int((completed_slots_this_month / total_slots_this_month * 100)) if total_slots_this_month > 0 else 0
    return completion_rate, checkin_days

def get_html_progress_bar(title: str, percentage: int, color_start: str, color_end: str, margin_bottom="20px"):
    """Render a vibrant custom progress bar."""
    return f"""<div style="margin-bottom: {margin_bottom};">
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
        <span style="font-weight: 600; font-size: 14px; color: #444;">{title}</span>
        <span style="font-weight: bold; font-size: 14px; color: {color_end};">{percentage}%</span>
    </div>
    <div style="width: 100%; background-color: #e0e0e0; border-radius: 8px; height: 12px; overflow: hidden;">
        <div style="width: {percentage}%; height: 100%; background: linear-gradient(90deg, {color_start} 0%, {color_end} 100%); border-radius: 8px; transition: width 0.5s ease-in-out;"></div>
    </div>
</div>"""

def render_dashboard():
    """Main render function for the dashboard page."""
    
    st.markdown("## 📊 儀表板 (Dashboard)")
    
    st.markdown("""
    <span id="dashboard-marker"></span>
    <style>
    /* Safely target ONLY the dashboard columns by checking for the dashboard marker */
    div[data-testid="stVerticalBlock"]:has(#dashboard-marker) div[data-testid="column"]:nth-of-type(1) > div[data-testid="stVerticalBlock"] > div.element-container:nth-of-type(4) div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlock"]:has(#dashboard-marker) div[data-testid="column"]:nth-of-type(2) > div[data-testid="stVerticalBlock"] > div.element-container:nth-of-type(4) div[data-testid="stVerticalBlockBorderWrapper"] {
        max-width: 364px !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if 'dashboard_week_offset' not in st.session_state:
        st.session_state.dashboard_week_offset = 0
        
    if 'dashboard_month_offset' not in st.session_state:
        st.session_state.dashboard_month_offset = 0
        
    # Generate real data
    df_weekly, start_week, end_week = get_mock_weekly_study_duration(st.session_state.dashboard_week_offset)
    subject_totals, df_daily = get_subject_study_analysis()
    mood_history, month_str = get_mock_mood_history(st.session_state.dashboard_month_offset)
    completion_rate, checkin_days = get_overall_progress()
    
    # Main Layout: Left 1/3, Right 2/3
    col_left, col_right = st.columns([1, 2], gap="large")
    
    # ================== LEFT COLUMN (1/3) ==================
    with col_left:
        # --- Left Top (1/3 height visually) ---
        st.markdown("#### 🎯 總體進度")
        
        left_html = f"""<div style="border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; padding: 1rem; max-width: 364px; width: 100%; height: 166px; display: flex; flex-direction: column; justify-content: center; box-sizing: border-box; margin-bottom: 16px;">
    {get_html_progress_bar("當月完成度", completion_rate, "#ff9a9e", "#fecfef", margin_bottom="20px")}
    {get_html_progress_bar("打卡天數", checkin_days, "#a1c4fd", "#c2e9fb", margin_bottom="0px")}
</div>"""
        st.markdown(left_html, unsafe_allow_html=True)
        
        # --- Left Bottom (2/3 height visually) ---
        # Wrap in a nested column so it matches the exact vertical padding of the right column's col_mood
        col_study = st.columns(1)[0]
        with col_study:
            st.markdown("#### 📈 一周讀書時長")
            with st.container(border=True, height=420):
                # Create Altair Line Chart
                chart = alt.Chart(df_weekly).mark_line(point=alt.OverlayMarkDef(size=80, filled=True)).encode(
                    x=alt.X('date_label:O', title='日期', axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y('duration:Q', title='讀書時長 (小時)', scale=alt.Scale(domain=[0, max(df_weekly['duration']) + 2])),
                    tooltip=[
                        alt.Tooltip('date:N', title='日期'),
                        alt.Tooltip('duration_str:N', title='讀書時長')
                    ]
                ).properties(
                    height=240
                ).configure_axis(
                    grid=True,
                    gridColor="#f0f0f0",
                    domain=False
                ).configure_view(
                    strokeWidth=0
                ).configure_point(
                    color="#4f84ff"
                ).configure_line(
                    color="#4f84ff",
                    strokeWidth=3
                )
                
                st.altair_chart(chart, use_container_width=True)
                
                # Week Navigation
                nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
                with nav_col1:
                    if st.button("◀", key="dash_prev_week", use_container_width=True):
                        st.session_state.dashboard_week_offset -= 1
                        st.rerun()
                with nav_col2:
                    st.markdown(f"<div style='text-align: center; padding-top: 5px; font-weight: bold; color: #555;'>{start_week.strftime('%Y/%m/%d')} ~ {end_week.strftime('%Y/%m/%d')}</div>", unsafe_allow_html=True)
                with nav_col3:
                    disabled_next = st.session_state.dashboard_week_offset >= 0
                    if st.button("▶", key="dash_next_week", disabled=disabled_next, use_container_width=True):
                        st.session_state.dashboard_week_offset += 1
                        st.rerun()
    
    # ================== RIGHT COLUMN (2/3) ==================
    with col_right:
        # --- Right Top (Study Analysis) ---
        st.markdown("#### 📊 讀書分析")
        
        if not subject_totals or all(s["total_hours"] == 0 for s in subject_totals):
            st.info("目前尚無讀書時間資料。請到「每日計畫與微調」打卡！")
        else:
            # Make pie chart take 1/3 of the width, and border matches its size
            pie_col, _ = st.columns([1, 2])
            with pie_col:
                with st.container(border=True):
                    # Format data for Pie Chart
                    pie_data = pd.DataFrame([
                        {"subject": s["name"], "hours": s["total_hours"], "color": s["color"]}
                        for s in subject_totals if s["total_hours"] > 0
                    ])
                    
                    # Create Pie Chart using Altair
                    pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50, stroke="#fff", strokeWidth=2).encode(
                        theta=alt.Theta(field="hours", type="quantitative"),
                        color=alt.Color(field="subject", type="nominal", 
                                      scale=alt.Scale(domain=pie_data['subject'].tolist(), 
                                                      range=pie_data['color'].tolist()),
                                      legend=alt.Legend(title="科目", orient="bottom")),
                        tooltip=["subject", "hours"]
                    ).properties(
                        height=200
                    )
                    st.altair_chart(pie_chart, use_container_width=True)
            
            st.markdown("---")
            
            # List of subjects with expanders
            expander_col, _ = st.columns([1, 1])
            with expander_col:
                for subj in subject_totals:
                    if subj["total_hours"] == 0: continue
                    
                    with st.expander(f"**{subj['name']}**：{subj['total_hours']} 小時"):
                        subj_df = df_daily[df_daily['subject'] == subj['name']]
                        if not subj_df.empty:
                            max_h = subj_df['hours'].max()
                            tick_values = [i * 0.5 for i in range(int(max_h * 2) + 2)]
                            
                            # Horizontal bar chart for daily breakdown
                            bar_chart = alt.Chart(subj_df).mark_bar(cornerRadiusEnd=4).encode(
                                x=alt.X('hours:Q', title='讀書時長 (小時)', axis=alt.Axis(values=tick_values, format='.1f')),
                                y=alt.Y('date:O', title='日期', sort='-x'),
                                color=alt.value(subj['color']),
                                tooltip=['date', 'hours']
                            ).properties(
                                height=alt.Step(30)
                            ).configure_view(
                                strokeWidth=0
                            ).configure_axis(
                                grid=False
                            )
                            st.altair_chart(bar_chart, use_container_width=True)
                        else:
                            st.write("無每日詳細資料。")

        # --- Right Bottom (2/3 height visually) ---
        
        # Define colors for mood scores 1-5 (1: Terrible, 5: Excellent)
        mood_colors = {
            1: "#ff7675", # Red (Terrible)
            2: "#fab1a0", # Light Red/Orange (Poor)
            3: "#ffeaa7", # Yellow (Fair)
            4: "#55efc4", # Light Green (Good)
            5: "#00b894"  # Dark Green (Excellent)
        }
        mood_labels = {
            1: "低落",
            2: "微低",
            3: "平穩",
            4: "良好",
            5: "極佳"
        }
        # Split the 2/3 right column into two halves. 
        # The first half (1/3 of total) will exactly match the left column's width.
        col_mood, _ = st.columns(2)
        
        with col_mood:
            st.markdown("#### 🌈 心情與動力波動")
            with st.container(border=True, height=420):
                st.markdown("<p style='font-size: 14px; color: #666; margin-bottom: 8px;'>過去 30 天的心情紀錄（未來將支援自訂圖案與顏色）：</p>", unsafe_allow_html=True)
                
                circles_html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-start; padding: 5px 0;">'
                for idx, score in enumerate(mood_history):
                    color = mood_colors.get(score, "#dfe6e9")
                    label = f"Day {idx+1}"
                    circles_html += f"""<div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
<span style="font-size: 9px; color: #aaa; height: 12px; line-height: 12px;">{label}</span>
<div style="width: 32px; height: 32px; border-radius: 50%; background-color: {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: center; align-items: center; transition: transform 0.2s;" title="第 {idx+1} 天 - 狀態分數: {score}" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'"></div>
</div>"""
                circles_html += '</div>'
                
                st.markdown(circles_html, unsafe_allow_html=True)
                
                # Legend
                # Legend built programmatically from parameters
                legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; font-size: 11px; color: #888; justify-content: center;">'
                legend_html += '<div style="display: flex; align-items: center; gap: 4px;"><div style="width:10px; height:10px; border-radius:50%; background:#dfe6e9;"></div>無紀錄</div>'
                for score, color in mood_colors.items():
                    legend_html += f'<div style="display: flex; align-items: center; gap: 4px;"><div style="width:10px; height:10px; border-radius:50%; background:{color};"></div>{mood_labels[score]}</div>'
                legend_html += '</div>'
                st.markdown(legend_html, unsafe_allow_html=True)
                
                # Month Navigation
                nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
                with nav_col1:
                    if st.button("◀", key="dash_prev_month", use_container_width=True):
                        st.session_state.dashboard_month_offset -= 1
                        st.rerun()
                with nav_col2:
                    st.markdown(f"<div style='text-align: center; padding-top: 5px; font-weight: bold; color: #555;'>{month_str}</div>", unsafe_allow_html=True)
                with nav_col3:
                    disabled_next_month = st.session_state.dashboard_month_offset >= 0
                    if st.button("▶", key="dash_next_month", disabled=disabled_next_month, use_container_width=True):
                        st.session_state.dashboard_month_offset += 1
                        st.rerun()
