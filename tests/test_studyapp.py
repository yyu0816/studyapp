import unittest

from studyapp import get_adjustment_message, parse_subject_entries


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


if __name__ == "__main__":
    unittest.main()
