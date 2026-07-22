import sys
sys.path.append('.')
import logic
import datetime

plan = {
    'start_date': '2026-07-01',
    'end_date': '2026-07-05',
    'weekday_wake': '07:00',
    'weekday_sleep': '23:30',
    'weekend_wake': '08:00',
    'weekend_sleep': '23:30',
    'routines': {},
    'fixed_events': [],
    'specific_events': [],
    'subjects': [
        {'name': 'aaa', 'materials': [{'name': 'm1', 'quantity': 100, 'type': '書籍'}], 'exam_date': '2026-07-30'}
    ]
}

# 1. Generate normal schedule
sch = logic.generate_daily_schedule(plan)
print(f"Original Schedule Length: {len(sch)}")
for item in sch:
    if '科目' in item and item['科目'] != '總複習 (自由安排)':
        print(f"  {item['date']} {item['科目']} {item['教材']} {item['目標進度']}")

# 2. Add a blocking event from 07-03 to 07-04
plan['specific_events'].append({
    'start_date': '2026-07-03',
    'end_date': '2026-07-04',
    'start_time': '00:00',
    'end_time': '23:59',
    'concurrent_with_study': False
})

# 3. Partial reschedule from 07-03
d = datetime.date(2026, 7, 3)
sch2 = logic.generate_daily_schedule(plan, existing_schedule=sch, reschedule_from_date=d)
print(f"\nRescheduled Schedule Length: {len(sch2)}")
for item in sch2:
    if '科目' in item and item['科目'] != '總複習 (自由安排)':
        print(f"  {item['date']} {item['科目']} {item['教材']} {item['目標進度']}")
