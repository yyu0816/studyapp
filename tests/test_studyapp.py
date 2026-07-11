import unittest

from studyapp import collect_plan_and_daily_data, get_adjustment_message, parse_subject_entries


class StudyAppLogicTests(unittest.TestCase):
    def test_parse_subject_entries_collects_subjects(self):
        payload = {
            "subject_name": ["數學", "英文"],
            "pages_required": ["120", "80"],
            "review_video": ["on", ""],
            "mock_exam": ["", "on"],
        }

        subjects = parse_subject_entries(payload)

        self.assertEqual(len(subjects), 2)
        self.assertEqual(subjects[0]["name"], "數學")
        self.assertEqual(subjects[0]["pages"], 120)
        self.assertTrue(subjects[0]["review_video"])
        self.assertFalse(subjects[0]["mock_exam"])

    def test_get_adjustment_message_recommends_slower_pacing(self):
        message = get_adjustment_message("too_fast", "1.5", "good")

        self.assertIn("放慢", message)
        self.assertIn("減少", message)

    def test_collect_plan_and_daily_data_builds_payload(self):
        form_data = {
            "timeframe": "30 天",
            "subject_name": ["數學"],
            "pages_required": ["120"],
            "review_video": ["on"],
            "mock_exam": [""],
            "schedule_day": ["週一"],
            "schedule_start": ["20:00"],
            "schedule_end": ["22:00"],
            "weekday_wake": "07:00",
            "weekday_sleep": "23:30",
            "weekend_wake": "08:30",
            "weekend_sleep": "00:30",
            "unavailable_day": ["上課日"],
            "unavailable_start": ["08:00"],
            "unavailable_end": ["17:00"],
            "unavailable_note": ["上課"],
            "daily_progress": "完成 60 頁",
            "mood": "low",
            "energy": "medium",
            "time_loss": "1.5",
            "pacing_feedback": "too_fast",
            "notes": "今天有點累",
        }

        plan_data, daily_data = collect_plan_and_daily_data(form_data)

        self.assertEqual(plan_data["timeframe"], "30 天")
        self.assertEqual(plan_data["subjects"][0]["name"], "數學")
        self.assertEqual(plan_data["fixed_schedule"][0]["day"], "週一")
        self.assertEqual(daily_data["daily_progress"], "完成 60 頁")
        self.assertIn("放慢", daily_data["recommendation"])


if __name__ == "__main__":
    unittest.main()
