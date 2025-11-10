import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Alarm
import csv
import pytz

# === KONFIGURACJA ===
TOURNAMENT = "Nitto ATP Finals 2025 – Singles"
LOCATION = "Turin, Italy"
TIMEZONE = 'Europe/Warsaw'
TIMEZONE_OBJ = pytz.timezone(TIMEZONE)
BASE_URL = "https://www.atptour.com/en/scores/current/nitto-atp-finals/605/daily-schedule?day=2"

# === ŚCIEŻKI ===
base_dir = os.path.dirname(__file__)
output_dir = os.path.join(base_dir, "output")
os.makedirs(output_dir, exist_ok=True)
ics_path = os.path.join(output_dir, "ATP_Finals_2025_Singles_Turin.ics")
log_path = os.path.join(output_dir, "log.txt")
csv_path = os.path.join(base_dir, "matches.csv")

# === FUNKCJA: pobiera mecze z ATP ===
def get_matches_from_atp():
    try:
        r = requests.get(BASE_URL, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return [], f"❌ Błąd pobierania danych z ATP: {e}"

    soup = BeautifulSoup(r.text, "html.parser")
    matches = []

    for match in soup.select(".scores-draw-entry-box"):
        players = match.select(".scores-draw-entry-box-player .name")
        time_el = match.select_one(".scores-draw-entry-box-time")

        if len(players) == 2:
            p1 = players[0].get_text(strip=True)
            p2 = players[1].get_text(strip=True)
            time_text = time_el.get_text(strip=True) if time_el else "TBD"
            matches.append((p1, p2, time_text))
    return matches, "ATP"

# === FUNKCJA: pobiera mecze z CSV ===
def get_matches_from_csv():
    matches = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                matches.append({
                    "date": row['date'],
                    "start_time": row['start_time'],
                    "end_time": row['end_time'],
                    "player1": row['player1'],
                    "player2": row['player2'],
                    "session": row['session']
                })
        return matches, "CSV"
    except Exception as e:
        return [], f"❌ Błąd wczytywania CSV: {e}"

# === FUNKCJA: tworzy kalendarz ICS ===
def create_ics(matches, source):
    cal = Calendar()
    cal.add("prodid", "-//ATP Finals 2025//kgforce//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")

    if source == "ATP":
        for i, (p1, p2, time_text) in enumerate(matches):
            date_base = datetime(2025, 11, 9 + i // 2)  # przybliżone daty
            hour = 13 if i % 2 == 0 else 21
            start = TIMEZONE_OBJ.localize(datetime(date_base.year, date_base.month, date_base.day, hour, 0))
            end = start + timedelta(hours=2)

            summary = f"{p1} vs {p2} (Turin)"
            ev = Event()
            ev.add("summary", summary)
            ev.add("description", f"{TOURNAMENT}\nScheduled: {time_text}")
            ev.add("location", LOCATION)
            ev.add("dtstart", start)
            ev.add("dtend", end)
            ev.add("dtstamp", datetime.now(TIMEZONE_OBJ))
            ev.add("uid", f"match-{i}@atpfinals2025")

            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", f"{summary} starts soon!")
            alarm.add("trigger", timedelta(minutes=-30))
            ev.add_component(alarm)

            cal.add_component(ev)
    else:  # CSV
        for row in matches:
            start_dt = TIMEZONE_OBJ.localize(datetime.strptime(f"{row['date']} {row['start_time']}", "%Y-%m-%d %H:%M"))
            end_dt = TIMEZONE_OBJ.localize(datetime.strptime(f"{row['date']} {row['end_time']}", "%Y-%m-%d %H:%M"))
            
            ev = Event()
            ev.add('dtstart', start_dt)
            ev.add('dtend', end_dt)
            ev.add('summary', f"{row['player1']} vs {row['player2']} (Turin)")
            ev.add('description', f"ATP Finals 2025 Singles – {row['session']} Session")
            ev.add('uid', f"{row['date']}-{row['start_time']}-{row['player1']}-{row['player2']}@atp2025")
            
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', 'Reminder')
            alarm.add('trigger', timedelta(minutes=-30))
            ev.add_component(alarm)
            
            cal.add_component(ev)
    return cal

# === GŁÓWNE WYKONANIE ===
if __name__ == "__main__":
    matches, source = get_matches_from_atp()
    log_lines = []

    if not matches:
        matches, source = get_matches_from_csv()
        log_lines.append("ℹ️ Źródło: CSV fallback")
    else:
        log_lines.append("ℹ️ Źródło: ATP Tour")

    calendar = create_ics(matches, source)

    with open(ics_path, "wb") as f:
        f.write(calendar.to_ical())

    log_lines.append(f"✅ Plik {ics_path} wygenerowany ({len(matches)} meczów).")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print("\n".join(log_lines))
