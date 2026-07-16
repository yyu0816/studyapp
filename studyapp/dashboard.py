import streamlit as st
import pandas as pd
import altair as alt
import random
from datetime import date, timedelta

def get_mock_weekly_study_duration() -> pd.DataFrame:
    """Generate mock weekly study duration for the line chart."""
    today = date.today()
    data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        # Random duration between 1.0 and 8.0 hours
        duration = round(random.uniform(1.0, 8.0), 1)
        
        # Convert to HH:MM format
        h = int(duration)
        m = int((duration - h) * 60)
        duration_str = f"{h:02d}h {m:02d}m"
        
        data.append({
            "date": day.strftime("%Y-%m-%d"),
            "duration": duration,
            "duration_str": duration_str
        })
    return pd.DataFrame(data)

def get_subject_ranking() -> list[dict]:
    """Get subject completion rankings. Uses real subjects if available, else mock."""
    plan = st.session_state.get("plan", {})
    subjects = plan.get("subjects", [])
    
    if not subjects:
        # Mock subjects if none exist
        return [
            {"name": "國文", "progress": 85, "color": "#ff7675"},
            {"name": "英文", "progress": 72, "color": "#74b9ff"},
            {"name": "數學", "progress": 45, "color": "#55efc4"},
        ]
    
    # Process real subjects, generate mock progress
    ranking = []
    for subj in subjects:
        name = subj.get("name", "未命名科目")
        color = subj.get("color", "#4f84ff")
        # Mock a random progress percentage for now
        progress = random.randint(10, 95)
        ranking.append({"name": name, "progress": progress, "color": color})
        
    # Sort by progress descending
    ranking.sort(key=lambda x: x["progress"], reverse=True)
    return ranking[:3] # Max 3 items

def get_mock_mood_history() -> list[int]:
    """Generate 30 days of mock mood data (1-5 scale, 0 for missing data)."""
    return [random.choice([0, 1, 2, 3, 4, 5]) for _ in range(30)]

def render_html_progress_bar(title: str, percentage: int, color_start: str, color_end: str):
    """Render a vibrant custom progress bar."""
    html = f"""<div style="margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
        <span style="font-weight: 600; font-size: 14px; color: #444;">{title}</span>
        <span style="font-weight: bold; font-size: 14px; color: {color_end};">{percentage}%</span>
    </div>
    <div style="width: 100%; background-color: #e0e0e0; border-radius: 8px; height: 12px; overflow: hidden;">
        <div style="width: {percentage}%; height: 100%; background: linear-gradient(90deg, {color_start} 0%, {color_end} 100%); border-radius: 8px; transition: width 0.5s ease-in-out;"></div>
    </div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_dashboard():
    """Main render function for the dashboard page."""
    
    st.markdown("## 📊 儀表板 (Dashboard)")
    
    # Generate mock data
    df_weekly = get_mock_weekly_study_duration()
    subject_rankings = get_subject_ranking()
    mood_history = get_mock_mood_history()
    
    # Main Layout: Left 1/3, Right 2/3
    col_left, col_right = st.columns([1, 2], gap="large")
    
    # ================== LEFT COLUMN (1/3) ==================
    with col_left:
        # --- Left Top (1/3 height visually) ---
        st.markdown("#### 🎯 總體進度")
        with st.container(border=True):
            st.markdown("<div style='padding: 10px 0;'>", unsafe_allow_html=True)
            # Mock percentages for demonstration
            render_html_progress_bar("當月完成度", 68, "#ff9a9e", "#fecfef")
            render_html_progress_bar("打卡天數", 42, "#a1c4fd", "#c2e9fb")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # --- Left Bottom (2/3 height visually) ---
        st.markdown("#### 📈 一周讀書時長")
        with st.container(border=True):
            # Create Altair Line Chart
            chart = alt.Chart(df_weekly).mark_line(point=alt.OverlayMarkDef(size=80, filled=True)).encode(
                x=alt.X('date:T', title='日期', axis=alt.Axis(format='%m/%d', tickCount=7)),
                y=alt.Y('duration:Q', title='讀書時長 (小時)', scale=alt.Scale(domain=[0, max(df_weekly['duration']) + 2])),
                tooltip=[
                    alt.Tooltip('date:T', title='日期', format='%Y-%m-%d'),
                    alt.Tooltip('duration_str:N', title='讀書時長')
                ]
            ).properties(
                height=300
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

    # ================== RIGHT COLUMN (2/3) ==================
    with col_right:
        # --- Right Top (1/3 height visually) ---
        st.markdown("#### 🏆 科目完成進度排行榜")
        if not subject_rankings:
            st.info("目前尚無科目資料。")
        else:
            boxes_html = '<div style="border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; padding: 1rem; width: fit-content; display: flex; gap: 16px; justify-content: flex-start; flex-wrap: wrap; margin-bottom: 16px;">'
            for subj_data in subject_rankings:
                boxes_html += f"""<div style="width: 100px; height: 100px; flex-shrink: 0; border-radius: 16px; background: linear-gradient(135deg, #ffffff 0%, #f3f4f6 100%); display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 2px solid {subj_data['color']}33; box-sizing: border-box;">
    <h4 style="margin: 0 0 4px 0; color: #555; font-size: 14px;">{subj_data['name']}</h4>
    <h2 style="margin: 0; color: {subj_data['color']}; font-weight: 800; font-size: 24px;">{subj_data['progress']}%</h2>
</div>"""
            boxes_html += '</div>'
            st.markdown(boxes_html, unsafe_allow_html=True)

        # --- Right Bottom (2/3 height visually) ---
        st.markdown("#### 🌈 心情與動力波動")
        
        # Define colors for mood scores 1-5 (1: Terrible, 5: Excellent)
        mood_colors = {
            1: "#ff7675", # Red
            2: "#fab1a0", # Light Red/Orange
            3: "#ffeaa7", # Yellow
            4: "#55efc4", # Light Green
            5: "#00b894"  # Dark Green
        }
        
        circles_html = '<div style="display: grid; grid-template-columns: repeat(10, max-content); gap: 12px; justify-content: flex-start; padding: 10px 0;">'
        for idx, score in enumerate(mood_history):
            color = mood_colors.get(score, "#dfe6e9")
            label = f"Day {idx+1}" if (idx % 10 == 0 or idx % 10 == 9) else "&nbsp;"
            circles_html += f"""<div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
<span style="font-size: 10px; color: #888; height: 14px; line-height: 14px;">{label}</span>
<div style="width: 36px; height: 36px; border-radius: 50%; background-color: {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: center; align-items: center; transition: transform 0.2s;" title="第 {idx+1} 天 - 狀態分數: {score}" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'"></div>
</div>"""
        circles_html += '</div>'
        
        # Legend
        legend_html = """<div style="display: flex; gap: 16px; margin-top: 24px; font-size: 12px; color: #888; justify-content: flex-end;">
<div style="display: flex; align-items: center; gap: 4px;"><div style="width:12px; height:12px; border-radius:50%; background:#dfe6e9;"></div>無紀錄</div>
<div style="display: flex; align-items: center; gap: 4px;"><div style="width:12px; height:12px; border-radius:50%; background:#ff7675;"></div>低落</div>
<div style="display: flex; align-items: center; gap: 4px;"><div style="width:12px; height:12px; border-radius:50%; background:#ffeaa7;"></div>平穩</div>
<div style="display: flex; align-items: center; gap: 4px;"><div style="width:12px; height:12px; border-radius:50%; background:#00b894;"></div>極佳</div>
</div>"""

        container_html = f"""<div style="border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; padding: 1rem; width: fit-content;">
<p style='font-size: 14px; color: #666; margin-bottom: 8px;'>過去 30 天的心情紀錄（未來將支援自訂圖案與顏色）：</p>
{circles_html}
{legend_html}
</div>"""
        
        st.markdown(container_html, unsafe_allow_html=True)
