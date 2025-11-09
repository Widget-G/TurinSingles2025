import csv
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import pytz

TIMEZONE = 'Europe/Warsaw'
OUTPUT_FILE = 'ATP_Finals_2025_Singles_Turin.ics'

cal = Calendar()
cal.add('prodid', '-//ATP Finals 2025//Singles//PL')
cal.add('version', '2.0')
cal.add('calscale', 'GREGORIAN')

tz = pytz.timezone(TIMEZONE)

with open('matches.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        event = Event()
        start_dt = tz.localize(datetime.strptime(f"{row['date']} {row['start_time']}", "%Y-%m-%d %H:%M"))
        end_dt = tz.localize(datetime.strptime(f"{row['date']} {row['end_time']}", "%Y-%m-%d %H:%M"))
        
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('summary', f"{row['player1']} vs {row['player2']} (Turin)")
        event.add('description', f"ATP Finals 2025 Singles – {row['session']} Session")
        event.add('uid', f"{row['date']}-{row['start_time']}-{row['player1']}-{row['player2']}@atp2025")
        
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Reminder')
        alarm.add('trigger', timedelta(minutes=-30))
        event.add_component(alarm)
        
        cal.add_component(event)

with open(OUTPUT_FILE, 'wb') as f:
    f.write(cal.to_ical())

print(f"Plik {OUTPUT_FILE} wygenerowany!")
