import sys
sys.path.append('.')
import logic

plan = {
    'start_date': '2026-07-01',
    'end_date': '2026-07-05',
    'weekday_wake': '07:00',
    'weekday_sleep': '23:30',
    'weekend_wake': '08:00',
    'weekend_sleep': '23:30',
    'routines': {
        'prep': {'start': '23:00', 'end': '01:00'}  # Cross night
    },
    'fixed_events': [
        {
            'weekdays': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'],
            'start': '22:00', 'end': '02:00', 'concurrent_with_study': False
        }
    ],
    'specific_events': [
        {
            'start_date': '2026-07-02',
            'end_date': '2026-07-04',
            'start_time': '08:00',
            'end_time': '17:00',
            'concurrent_with_study': False
        }
    ],
    'subjects': [
        {'name': 'aaa', 'materials': [{'name': 'm1', 'quantity': 100, 'type': '書籍'}], 'exam_date': '2026-07-30'}
    ]
}

import datetime
d = datetime.date(2026, 7, 2)
slots = logic.get_daily_free_slots(d, plan)
print(f"Slots for {d}: {slots}")

d2 = datetime.date(2026, 7, 3)
slots2 = logic.get_daily_free_slots(d2, plan)
print(f"Slots for {d2}: {slots2}")
