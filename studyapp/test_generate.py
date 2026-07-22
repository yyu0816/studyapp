import sys
sys.path.append('.')
from logic import get_daily_free_slots
import scratch_generate
scratch_generate.get_daily_free_slots = get_daily_free_slots
scratch_generate.UNIT_MAP = {'書籍': '頁', '線上課程': '堂', '題庫': '題', '影片': '部', '其他': '項'}

plan = {
    'start_date': '2026-07-01',
    'end_date': '2026-07-30',
    'weekday_wake': '07:00',
    'weekday_sleep': '23:30',
    'weekend_wake': '08:00',
    'weekend_sleep': '23:30',
    'fixed_events': [],
    'routines': {},
    'subjects': [
        {'name': 'aaa', 'materials': [{'name': 'mat1', 'quantity': 100, 'type': '書籍'}], 'exam_date': '2026-07-30'},
        {'name': 'bbb', 'materials': [{'name': 'mat2', 'quantity': 30, 'type': '書籍'}], 'exam_date': '2026-07-30'},
        {'name': 'ccc', 'materials': [{'name': 'mat3', 'quantity': 30, 'type': '書籍'}], 'exam_date': '2026-07-30'}
    ]
}

schedule = scratch_generate.generate_daily_schedule(plan)
for day in schedule[:2]:
    print(f"Day {day['date']}:")
    for ev in day['events'][:5]:
        print(f"  {ev['time']} {ev['subject']} {ev['progress']}")
