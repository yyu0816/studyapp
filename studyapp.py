from __future__ import annotations

from typing import Any

from flask import Flask, request

app = Flask(__name__)

app_state: dict[str, Any] = {
    "plan": None,
    "daily_log": None,
}


def parse_subject_entries(form_data: Any) -> list[dict[str, Any]]:
    if hasattr(form_data, "getlist"):
        names = form_data.getlist("subject_name")
        pages = form_data.getlist("pages_required")
        review_video = form_data.getlist("review_video")
        mock_exam = form_data.getlist("mock_exam")
    else:
        names = form_data.get("subject_name", []) or []
        pages = form_data.get("pages_required", []) or []
        review_video = form_data.get("review_video", []) or []
        mock_exam = form_data.get("mock_exam", []) or []

    if not isinstance(names, list):
        names = [names]
    if not isinstance(pages, list):
        pages = [pages]
    if not isinstance(review_video, list):
        review_video = [review_video]
    if not isinstance(mock_exam, list):
        mock_exam = [mock_exam]

    subjects: list[dict[str, Any]] = []
    for index, name in enumerate(names):
        cleaned_name = name.strip()
        if not cleaned_name:
            continue
        subjects.append(
            {
                "name": cleaned_name,
                "pages": int(pages[index].strip()) if pages[index].strip() else 0,
                "review_video": bool(review_video[index]),
                "mock_exam": bool(mock_exam[index]),
            }
        )
    return subjects


def get_adjustment_message(pacing_feedback: str, time_loss: str, mood: str) -> str:
    feedback = pacing_feedback or "balanced"
    loss = float(time_loss) if time_loss.replace(".", "", 1).isdigit() else 0

    if feedback == "too_fast":
        if loss >= 1.5:
            return "你的節奏偏快，建議放慢一點並減少當天的學習量，保留更多休息時間。"
        return "你的節奏偏快，建議放慢節奏並把重點任務縮減到 1~2 項。"

    if feedback == "too_slow":
        if mood in {"low", "very_low"}:
            return "你目前狀態偏低，建議先做高收益的複習，再逐步增加今日的進度。"
        return "你的節奏偏慢，建議把今日的目標拆成更小的步驟，提升完成感。"

    if loss >= 2:
        return "今天意外損失了不少時間，建議把明天的安排再留出緩衝時段。"

    return "目前節奏還算穩定，保持每日小步進展即可。"


def build_plan_summary(plan_data: dict[str, Any], daily_data: dict[str, Any]) -> str:
    subject_lines = "<ul>" + "".join(
        f"<li>{item['name']}：{item['pages']} 頁，複習影片{'有' if item['review_video'] else '無'}，模擬考{'有' if item['mock_exam'] else '無'}</li>"
        for item in plan_data.get("subjects", [])
    ) + "</ul>"

    schedule_lines = "<ul>" + "".join(
        f"<li>{item['day']}：{item['start']} ～ {item['end']}</li>" for item in plan_data.get("fixed_schedule", [])
    ) + "</ul>"

    unavailable_lines = "<ul>" + "".join(
        f"<li>{item['day']}：{item['start']} ～ {item['end']}（{item['note']}）</li>" for item in plan_data.get("unavailable_hours", [])
    ) + "</ul>"

    return f"""
    <section class=\"summary-card\">
      <h3>初始設定摘要</h3>
      <p><strong>讀書天數 / 考試倒數：</strong> {plan_data.get('timeframe', '未填')}</p>
      <p><strong>科目與工作量：</strong></p>
      {subject_lines}
      <p><strong>固定學習時段：</strong></p>
      {schedule_lines}
      <p><strong>每日作息：</strong> 平日 {plan_data.get('daily_routine', {}).get('weekday_wake', '未填')} 起床，{plan_data.get('daily_routine', {}).get('weekday_sleep', '未填')} 就寢；假日 {plan_data.get('daily_routine', {}).get('weekend_wake', '未填')} 起床，{plan_data.get('daily_routine', {}).get('weekend_sleep', '未填')} 就寢。</p>
      <p><strong>不可使用時段：</strong></p>
      {unavailable_lines}
    </section>
    <section class=\"summary-card\">
      <h3>今日打卡摘要</h3>
      <p><strong>今日進度：</strong> {daily_data.get('daily_progress', '未填')}</p>
      <p><strong>心情與精力：</strong> {daily_data.get('mood', '未填')} / {daily_data.get('energy', '未填')}</p>
      <p><strong>意外時間損失：</strong> {daily_data.get('time_loss', '未填')} 小時</p>
      <p><strong>節奏回饋：</strong> {daily_data.get('pacing_feedback', '未填')}</p>
      <p><strong>建議：</strong> {daily_data.get('recommendation', '')}</p>
    </section>
    """


HTML_PAGE = """
<!doctype html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Study Planner</title>
  <style>
    :root { color-scheme: dark; }
    body {
      font-family: 'Segoe UI', sans-serif;
      margin: 0;
      background: linear-gradient(135deg, #09111f, #223c5e);
      color: #eef4ff;
      line-height: 1.6;
    }
    main {
      max-width: 960px;
      margin: 0 auto;
      padding: 24px;
    }
    .hero {
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 18px 40px rgba(0,0,0,0.2);
    }
    h1, h2, h3 { margin-top: 0; }
    .card {
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 16px;
    }
    .grid { display: grid; gap: 12px; }
    .row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
    label { display: block; font-size: 0.95rem; margin-bottom: 4px; color: #cfe0ff; }
    input, select, textarea, button {
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.2);
      background: rgba(4, 8, 16, 0.45);
      color: #f8fbff;
      font-size: 0.95rem;
    }
    button {
      cursor: pointer;
      background: linear-gradient(135deg, #4f84ff, #7b5cff);
      border: none;
      font-weight: 600;
      transition: transform 0.2s ease;
    }
    button:hover { transform: translateY(-1px); }
    .secondary { background: rgba(255,255,255,0.16); }
    .field-group { display: flex; flex-direction: column; gap: 6px; }
    .chip-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .chip { padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,0.14); font-size: 0.9rem; }
    .summary-card { padding: 14px; border-radius: 14px; background: rgba(255,255,255,0.12); margin-bottom: 12px; }
    .muted { color: #c4d7ff; font-size: 0.92rem; }
    .inline { display: flex; align-items: center; gap: 8px; }
  </style>
</head>
<body>
  <main>
    <section class=\"hero\">
      <h1>讀書計畫安排助手</h1>
      <p class=\"muted\">這個頁面幫你把「初始設定」與「每日打卡」整理在一起，讓你的學習計畫更可持續。</p>
    </section>
    __BODY__
  </main>
  <script>
    function addRow(type) {
      const container = document.getElementById(type + '-container');
      const row = document.createElement('div');
      row.className = 'row';
      if (type === 'subject') {
        row.innerHTML = `
          <div class=\"field-group\"><label>科目名稱</label><input name=\"subject_name\" placeholder=\"例如：化學\"></div>
          <div class=\"field-group\"><label>需讀頁數</label><input type=\"number\" name=\"pages_required\" min=\"0\" placeholder=\"120\"></div>
          <div class=\"field-group\"><label>複習影片</label><select name=\"review_video\"><option value=\"\">無</option><option value=\"on\">有</option></select></div>
          <div class=\"field-group\"><label>模擬考</label><select name=\"mock_exam\"><option value=\"\">無</option><option value=\"on\">有</option></select></div>`;
      } else if (type === 'schedule') {
        row.innerHTML = `
          <div class=\"field-group\"><label>日期 / 週次</label><input name=\"schedule_day\" placeholder=\"週一、週三、考前 3 天\"></div>
          <div class=\"field-group\"><label>開始時間</label><input name=\"schedule_start\" placeholder=\"20:00\"></div>
          <div class=\"field-group\"><label>結束時間</label><input name=\"schedule_end\" placeholder=\"22:00\"></div>`;
      } else if (type === 'unavailable') {
        row.innerHTML = `
          <div class=\"field-group\"><label>日期 / 時段</label><input name=\"unavailable_day\" placeholder=\"平日、上課日\"></div>
          <div class=\"field-group\"><label>開始時間</label><input name=\"unavailable_start\" placeholder=\"08:00\"></div>
          <div class=\"field-group\"><label>結束時間</label><input name=\"unavailable_end\" placeholder=\"17:00\"></div>
          <div class=\"field-group\"><label>備註</label><input name=\"unavailable_note\" placeholder=\"上課/打工\"></div>`;
      }
      container.appendChild(row);
    }
  </script>
</body>
</html>
"""


def render_home_page() -> str:
    body = """
    <section class=\"card\">
      <h2>1. 初始設定</h2>
      <form method=\"post\" action=\"/\">
        <div class=\"row\">
          <div class=\"field-group\">
            <label for=\"timeframe\">總共讀書天數 / 考試倒數</label>
            <input id=\"timeframe\" name=\"timeframe\" placeholder=\"例如：56 天\">
          </div>
        </div>

        <div class=\"card\">
          <div class=\"inline\">
            <h3>科目與工作量</h3>
            <button type=\"button\" class=\"secondary\" onclick=\"addRow('subject')\">新增科目</button>
          </div>
          <div id=\"subject-container\" class=\"grid\">
            <div class=\"row\">
              <div class=\"field-group\"><label>科目名稱</label><input name=\"subject_name\" placeholder=\"例如：數學\"></div>
              <div class=\"field-group\"><label>需讀頁數</label><input type=\"number\" name=\"pages_required\" min=\"0\" placeholder=\"120\"></div>
              <div class=\"field-group\"><label>複習影片</label><select name=\"review_video\"><option value=\"\">無</option><option value=\"on\">有</option></select></div>
              <div class=\"field-group\"><label>模擬考</label><select name=\"mock_exam\"><option value=\"\">無</option><option value=\"on\">有</option></select></div>
            </div>
          </div>
        </div>

        <div class=\"card\">
          <div class=\"inline\">
            <h3>固定學習時段</h3>
            <button type=\"button\" class=\"secondary\" onclick=\"addRow('schedule')\">新增時段</button>
          </div>
          <div id=\"schedule-container\" class=\"grid\">
            <div class=\"row\">
              <div class=\"field-group\"><label>日期 / 週次</label><input name=\"schedule_day\" placeholder=\"週一、週三\"></div>
              <div class=\"field-group\"><label>開始時間</label><input name=\"schedule_start\" placeholder=\"20:00\"></div>
              <div class=\"field-group\"><label>結束時間</label><input name=\"schedule_end\" placeholder=\"22:00\"></div>
            </div>
          </div>
        </div>

        <div class=\"card\">
          <h3>每日作息</h3>
          <div class=\"row\">
            <div class=\"field-group\"><label>平日起床</label><input name=\"weekday_wake\" placeholder=\"07:00\"></div>
            <div class=\"field-group\"><label>平日睡覺</label><input name=\"weekday_sleep\" placeholder=\"23:30\"></div>
            <div class=\"field-group\"><label>假日起床</label><input name=\"weekend_wake\" placeholder=\"08:30\"></div>
            <div class=\"field-group\"><label>假日睡覺</label><input name=\"weekend_sleep\" placeholder=\"00:30\"></div>
          </div>
        </div>

        <div class=\"card\">
          <div class=\"inline\">
            <h3>不可使用時段</h3>
            <button type=\"button\" class=\"secondary\" onclick=\"addRow('unavailable')\">新增時段</button>
          </div>
          <div id=\"unavailable-container\" class=\"grid\">
            <div class=\"row\">
              <div class=\"field-group\"><label>日期 / 時段</label><input name=\"unavailable_day\" placeholder=\"上課日\"></div>
              <div class=\"field-group\"><label>開始時間</label><input name=\"unavailable_start\" placeholder=\"08:00\"></div>
              <div class=\"field-group\"><label>結束時間</label><input name=\"unavailable_end\" placeholder=\"17:00\"></div>
              <div class=\"field-group\"><label>備註</label><input name=\"unavailable_note\" placeholder=\"打工/上課\"></div>
            </div>
          </div>
        </div>

        <div class=\"card\">
          <h2>2. 每日打卡或微調</h2>
          <div class=\"row\">
            <div class=\"field-group\">
              <label for=\"daily_progress\">今日讀書進度</label>
              <textarea id=\"daily_progress\" name=\"daily_progress\" rows=\"3\" placeholder=\"例如：完成 60 頁數學與 20 頁英文\"></textarea>
            </div>
            <div class=\"field-group\">
              <label for=\"mood\">心情與精力</label>
              <select id=\"mood\" name=\"mood\">
                <option value=\"good\">好</option>
                <option value=\"neutral\">普通</option>
                <option value=\"low\">低</option>
                <option value=\"very_low\">很低</option>
              </select>
            </div>
            <div class=\"field-group\">
              <label for=\"energy\">能量等級</label>
              <select id=\"energy\" name=\"energy\">
                <option value=\"high\">高</option>
                <option value=\"medium\">中</option>
                <option value=\"low\">低</option>
              </select>
            </div>
          </div>
          <div class=\"row\">
            <div class=\"field-group\">
              <label for=\"time_loss\">意外時間損失（小時）</label>
              <input id=\"time_loss\" name=\"time_loss\" type=\"number\" step=\"0.5\" min=\"0\" placeholder=\"1.5\">
            </div>
            <div class=\"field-group\">
              <label for=\"pacing_feedback\">節奏回饋</label>
              <select id=\"pacing_feedback\" name=\"pacing_feedback\">
                <option value=\"balanced\">剛剛好</option>
                <option value=\"too_fast\">進度太多</option>
                <option value=\"too_slow\">進度太少</option>
              </select>
            </div>
          </div>
          <div class=\"field-group\">
            <label for=\"notes\">備註</label>
            <textarea id=\"notes\" name=\"notes\" rows=\"3\" placeholder=\"例如：今天需要延後 30 分鐘的複習\"></textarea>
          </div>
        </div>

        <button type=\"submit\">儲存計畫與打卡</button>
      </form>
    </section>
    """
    return HTML_PAGE.replace("__BODY__", body)


def render_result_page(plan_data: dict[str, Any], daily_data: dict[str, Any]) -> str:
    summary = build_plan_summary(plan_data, daily_data)
    body = f"""
    <section class=\"card\">
      <h2>計畫已整理完成</h2>
      <p class=\"muted\">你可以把這個畫面當成今日的學習紀錄，之後再次開啟時也能看到上一筆紀錄。</p>
      <div class=\"chip-row\">
        <span class=\"chip\">{plan_data.get('timeframe', '未填')}</span>
        <span class=\"chip\">{len(plan_data.get('subjects', []))} 個科目</span>
        <span class=\"chip\">{daily_data.get('mood', '未填')} / {daily_data.get('energy', '未填')}</span>
      </div>
      {summary}
      <a href=\"/\"><button type=\"button\">回到表單</button></a>
    </section>
    """
    return HTML_PAGE.replace("__BODY__", body)


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    if request.method == "POST":
        schedule_days = request.form.getlist("schedule_day")
        schedule_starts = request.form.getlist("schedule_start")
        schedule_ends = request.form.getlist("schedule_end")
        unavailable_days = request.form.getlist("unavailable_day")
        unavailable_starts = request.form.getlist("unavailable_start")
        unavailable_ends = request.form.getlist("unavailable_end")
        unavailable_notes = request.form.getlist("unavailable_note")

        plan_data: dict[str, Any] = {
            "timeframe": request.form.get("timeframe", ""),
            "subjects": parse_subject_entries(request.form),
            "fixed_schedule": [
                {
                    "day": schedule_days[index] if index < len(schedule_days) else "",
                    "start": schedule_starts[index] if index < len(schedule_starts) else "",
                    "end": schedule_ends[index] if index < len(schedule_ends) else "",
                }
                for index in range(max(len(schedule_days), len(schedule_starts), len(schedule_ends)))
            ],
            "daily_routine": {
                "weekday_wake": request.form.get("weekday_wake", ""),
                "weekday_sleep": request.form.get("weekday_sleep", ""),
                "weekend_wake": request.form.get("weekend_wake", ""),
                "weekend_sleep": request.form.get("weekend_sleep", ""),
            },
            "unavailable_hours": [
                {
                    "day": unavailable_days[index] if index < len(unavailable_days) else "",
                    "start": unavailable_starts[index] if index < len(unavailable_starts) else "",
                    "end": unavailable_ends[index] if index < len(unavailable_ends) else "",
                    "note": unavailable_notes[index] if index < len(unavailable_notes) else "",
                }
                for index in range(max(len(unavailable_days), len(unavailable_starts), len(unavailable_ends), len(unavailable_notes)))
            ],
        }

        daily_data: dict[str, Any] = {
            "daily_progress": request.form.get("daily_progress", ""),
            "mood": request.form.get("mood", ""),
            "energy": request.form.get("energy", ""),
            "time_loss": request.form.get("time_loss", ""),
            "pacing_feedback": request.form.get("pacing_feedback", ""),
            "notes": request.form.get("notes", ""),
        }
        daily_data["recommendation"] = get_adjustment_message(
            daily_data["pacing_feedback"],
            daily_data["time_loss"],
            daily_data["mood"],
        )
        app_state["plan"] = plan_data
        app_state["daily_log"] = daily_data
        return render_result_page(plan_data, daily_data)

    return render_home_page()


# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=8000)
