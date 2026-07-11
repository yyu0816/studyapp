import unittest

from studyapp import build_monthly_plan, collect_plan_and_daily_data, get_adjustment_message, parse_subject_entries


class StudyAppLogicTests(unittest.TestCase):
    def test_parse_subject_entries_supports_materials(self):
        payload = {
            "subjects": [
                {
                    "name": "數學",
                    "materials": [
                        {"name": "教材", "type": "教材", "pages": 120},
                        {"name": "教學影片", "type": "教學影片", "pages": 3},
                    ],
                }
            ]
        }

        subjects = parse_subject_entries(payload)

        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0]["name"], "數學")
        self.assertEqual(subjects[0]["materials"][0]["type"], "教材")
        self.assertEqual(subjects[0]["materials"][1]["pages"], 3)

    def test_get_adjustment_message_recommends_slower_pacing(self):
        message = get_adjustment_message("too_fast", "1.5", "good")

        self.assertIn("放慢", message)
        self.assertIn("減少", message)

    def test_collect_plan_and_daily_data_builds_payload(self):
        form_data = {
            "start_date": "2026-07-11",
            "end_date": "2026-07-20",
            "subjects": [
                {
                    "name": "數學",
                    "materials": [{"name": "教材", "type": "教材", "pages": 120}],
                }
            ],
            "fixed_events": [
                {
                    "title": "上課",
                    "weekdays": ["週一", "週三"],
                    "start": "09:00",
                    "end": "11:00",
                    "color": "藍色",
                    "show_on_calendar": True,
                }
            ],
            "weekday_wake": "07:00",
            "weekday_sleep": "23:30",
            "weekend_wake": "08:30",
            "weekend_sleep": "00:30",
            "daily_progress": "完成 60 頁",
            "mood": "low",
            "energy": "medium",
            "time_loss": "1.5",
            "pacing_feedback": "too_fast",
            "notes": "今天有點累",
        }

        plan_data, daily_data = collect_plan_and_daily_data(form_data)

        self.assertEqual(plan_data["end_date"], "2026-07-20")
        self.assertEqual(plan_data["subjects"][0]["name"], "數學")
        self.assertEqual(plan_data["fixed_events"][0]["weekdays"], ["週一", "週三"])
        self.assertEqual(daily_data["daily_progress"], "完成 60 頁")
        self.assertIn("放慢", daily_data["recommendation"])

    def test_build_monthly_plan_uses_end_date(self):
        plan_data = {
            "start_date": "2026-07-11",
            "end_date": "2026-07-13",
            "subjects": [
                {"name": "數學", "materials": [{"name": "教材", "type": "教材", "pages": 60}]},
                {"name": "英文", "materials": [{"name": "練習題", "type": "練習題", "pages": 30}]},
            ],
            "preferred_subject_count": 2,
        }

        monthly_plan = build_monthly_plan(plan_data)

        self.assertEqual(len(monthly_plan), 3)
        self.assertEqual(monthly_plan[-1]["date"], "2026-07-13")
        self.assertIn("數學", monthly_plan[0]["subjects"])


if __name__ == "__main__":
    unittest.main()
