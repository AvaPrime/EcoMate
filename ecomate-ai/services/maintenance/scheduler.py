import csv, datetime

SCHEDULE = 'data/maintenance_schedule.csv'

def tasks_for(system_id: str):
    out = []
    with open(SCHEDULE, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out.append({
                'system_id': system_id,
                'task': r['task'],
                'due_date': (datetime.date.today() + datetime.timedelta(days=int(r['interval_days']))).isoformat(),
                'priority': r.get('priority','normal')
            })
    return out