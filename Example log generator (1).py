import random
import sqlite3
import json
from datetime import datetime, timedelta

class SecurityEvent:
    def __init__(self, event_id, timestamp, username, action, details):
        self.event_id = event_id
        self.timestamp = timestamp
        self.username = username
        self.action = action
        self.details = details

def setup_database(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        timestamp TEXT,
        username TEXT,
        action TEXT,
        details TEXT
    )""")
    conn.commit()
    return conn

def generate_logon_event(username, t, logon_type=None):
    if logon_type is None:
        rand_val = random.randint(1, 100)
        if rand_val <= 70:
            logon_type = 2
        elif rand_val <= 85:
            logon_type = 3
        elif rand_val <= 95:
            logon_type = 7
        else:
            logon_type = 10

    auth = random.choice(["NTLM", "Kerberos"])
    ws_name = "WS_" + str(random.randint(10, 99))

    details = {"logon_type": logon_type, "auth": auth, "workstation": ws_name}
    return SecurityEvent(4624, t, username, "LOGIN", details)

def generate_logoff_event(username, t):
    ws_name = "WS_" + str(random.randint(10, 99))
    details = {"workstation": ws_name}
    return SecurityEvent(4634, t, username, "LOGOFF", details)

def generate_file_event(username, t, force_action=None):
    if force_action:
        action = force_action
    else:
        rand_val = random.randint(1, 100)
        if rand_val <= 80:
            action = "READ"
        elif rand_val <= 95:
            action = "WRITE"
        else:
            action = "DELETE"

    file_categories = [
        "C:\\Documents\\passwords",
        "C:\\Work\\project_docs",
        "\\\\server\\share\\financial_data",
        "C:\\Users\\Public\\Downloads\\archive"
    ]
    
    # Generate dynamic file names to add variety
    base_path = random.choice(file_categories)
    file_id = random.randint(1, 500)
    ext = random.choice([".txt", ".pdf", ".xlsx", ".docx"])
    chosen_file = f"{base_path}_{file_id}{ext}"

    details = {"file_path": chosen_file, "process_id": random.randint(1000, 5000)}
    return SecurityEvent(4663, t, username, action, details)

def generate_web_event(username, t, force_domain=None):
    if force_domain:
        domain = force_domain
    else:
        # 90% normal domains, 10% shadow AI domains
        rand_val = random.randint(1, 100)
        if rand_val <= 90:
            normal_domains = ["google.com", "github.com", "stackoverflow.com", "microsoft.com", "aws.amazon.com", "internal-portal.local"]
            domain = random.choice(normal_domains)
        else:
            shadow_domains = ["chatgpt.com", "claude.ai", "gemini.google.com", "perplexity.ai"]
            domain = random.choice(shadow_domains)
            
    url = f"https://{domain}/" + random.choice(["", "chat", "search?q=test", "login"])
    details = {"domain": domain, "url": url, "browser": "Chrome"}
    return SecurityEvent(5156, t, username, "WEB_VISIT", details)

def save_events_bulk(conn, events_list):
    # Sort events chronologically before saving
    events_list.sort(key=lambda x: x.timestamp)
    
    cursor = conn.cursor()
    data = [
        (e.event_id, e.timestamp.strftime("%Y-%m-%d %H:%M:%S"), e.username, e.action, json.dumps(e.details))
        for e in events_list
    ]
    cursor.executemany("INSERT INTO events (event_id, timestamp, username, action, details) VALUES (?,?,?,?,?)", data)
    conn.commit()

def run_simulation():
    users = ["admin", "ahmet_yilmaz", "ayse_demir", "mehmet_kaya", "misafir"]
    conn = setup_database("security_audit.db")

    total_alerts = 0
    all_events = []
    
    # Start date of simulation (3 days ago)
    start_date = datetime.now() - timedelta(days=3)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    print("Starting simulation...")
    print()

    for day in range(3):
        print(f"Day {day + 1}")
        current_date = start_date + timedelta(days=day)

        for user in users:
            # 1. Normal Daily Login
            login_time = current_date + timedelta(hours=random.uniform(8.0, 9.5)) # Logins between 08:00 - 09:30
            all_events.append(generate_logon_event(user, login_time))
            
            # 2. Daily Activities
            activity_count = random.randint(20, 60)
            last_activity_time = login_time
            
            for _ in range(activity_count):
                last_activity_time += timedelta(minutes=random.uniform(2, 15))
                
                # mix file events and web events
                if random.randint(1, 10) <= 7:
                    event = generate_file_event(user, last_activity_time)
                else:
                    event = generate_web_event(user, last_activity_time)
                    
                all_events.append(event)
                
                if event.action == "DELETE":
                    total_alerts += 1
            
            # 3. Normal Logoff
            logoff_time = login_time + timedelta(hours=random.uniform(8.0, 9.0)) # 8-9 hours session
            all_events.append(generate_logoff_event(user, logoff_time))

    # 4. Inject an Anomaly / Insider Threat Scenario on the last day
    anomaly_user = "misafir"
    print(f"\n[!] Injecting Insider Threat Scenario for user '{anomaly_user}'...")
    
    anomaly_date = start_date + timedelta(days=2)
    # Login at 02:30 AM
    night_login = anomaly_date + timedelta(hours=2, minutes=30)
    all_events.append(generate_logon_event(anomaly_user, night_login, logon_type=10)) # Remote interactive
    
    # Bulk read and delete
    last_time = night_login
    for _ in range(45):
        last_time += timedelta(seconds=random.randint(10, 30))
        all_events.append(generate_file_event(anomaly_user, last_time, force_action="READ"))
        
    for _ in range(25):
        last_time += timedelta(seconds=random.randint(10, 30))
        all_events.append(generate_file_event(anomaly_user, last_time, force_action="DELETE"))
        total_alerts += 25 # just for tracking
        
    # Also inject some Shadow AI usage
    print(f"[!] Injecting Shadow AI usage for user '{anomaly_user}'...")
    for _ in range(5):
        last_time += timedelta(seconds=random.randint(30, 120))
        all_events.append(generate_web_event(anomaly_user, last_time, force_domain="chatgpt.com"))
        all_events.append(generate_web_event(anomaly_user, last_time + timedelta(seconds=5), force_domain="claude.ai"))

    # Logoff at 03:15 AM
    night_logoff = last_time + timedelta(minutes=2)
    all_events.append(generate_logoff_event(anomaly_user, night_logoff))

    # Save to database
    save_events_bulk(conn, all_events)

    print("---")
    print(f"Total events: {len(all_events)}")
    print(f"Total tracking alerts: {total_alerts}")
    print("---")

    # report
    cursor = conn.cursor()

    print("\nAction Summary:")
    cursor.execute("SELECT action, COUNT(*) FROM events GROUP BY action")
    results = cursor.fetchall()
    for row in results:
        print(f"  {row[0]}: {row[1]}")

    print("\nUser Summary:")
    cursor.execute("SELECT username, COUNT(*) FROM events GROUP BY username")
    results = cursor.fetchall()
    for row in results:
        print("  " + row[0] + ": " + str(row[1]))

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    run_simulation()
