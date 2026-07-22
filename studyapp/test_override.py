import sys
sys.path.append('.')
import logic
import datetime

plan = {
    'start_date': '2026-07-01',
    'end_date': '2026-07-02',
    'weekday_wake': '07:00',
    'weekday_sleep': '23:30',
    'weekend_wake': '08:00',
    'weekend_sleep': '23:30',
    'routines': {},
    'fixed_events': [],
    'specific_events': [],
    'daily_override_events': {
        '2026-07-02': [
            {'title': 'all day ev', 'is_all_day': True, 'concurrent_with_study': False}
        ]
    },
    'subjects': [
        {'name': 'aaa', 'materials': [{'name': 'm1', 'quantity': 100, 'type': '書籍'}], 'exam_date': '2026-07-30'}
    ]
}

sch = logic.generate_daily_schedule(plan)
print(f"Schedule Length: {len(sch)}")
for item in sch:
    if '科目' in item and item['科目'] != '總複習 (自由安排)':
        print(f"  {item['date']} {item['科目']} {item['教材']} {item['目標進度']}")
