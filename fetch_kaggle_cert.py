import sqlite3
import json
import pandas as pd
from datetime import datetime
import sys
import io
import os

# Force UTF-8 for stdout just in case
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def process_and_insert_email_file(file_path, conn):
    cursor = conn.cursor()
    print(f"\n[EMAIL] Processing local file: {file_path}")
    print("Only taking first 100,000 rows to protect RAM...")
    
    try:
        # reading the local file directly without kagglehub or other libraries
        df = pd.read_csv(file_path, nrows=100000)
    except FileNotFoundError:
        print(f"ERROR: '{file_path}' file not found! Make sure the file is in this folder.")
        return
    except Exception as e:
        print(f"ERROR: Could not read file - {str(e)}")
        return

    print(f"Data read successfully. Total rows: {len(df)}")
    events = []
    
    for index, row in df.iterrows():
        user = str(row.get('user', 'UNKNOWN'))
        date_str = row.get('date', None)
        pc = str(row.get('pc', 'UNKNOWN_PC'))
        
        # parse the date
        if date_str:
            try:
                t = datetime.strptime(str(date_str), "%m/%d/%Y %H:%M:%S")
            except:
                t = datetime.now()
        else:
            t = datetime.now()

        # email dataset columns: to, cc, bcc, from, size, attachments etc
        activity = str(row.get('activity', 'Send'))
        event_id = 5104 # custom ID for email events
        action = "EMAIL"
        
        details = {
            "workstation": pc,
            "source": "local_cert_email",
            "to": str(row.get('to', '')),
            "attachments": str(row.get('attachments', '0')),
            "size": str(row.get('size', '0'))
        }
            
        events.append((
            event_id, 
            t.strftime("%Y-%m-%d %H:%M:%S"), 
            user, 
            action, 
            json.dumps(details)
        ))
        
        # transfer in chunks
        if len(events) >= 5000:
            cursor.executemany("INSERT INTO security_events (event_id, timestamp, username, action, details) VALUES (?, ?, ?, ?, ?)", events)
            conn.commit()
            events = []
            
    if events:
        cursor.executemany("INSERT INTO security_events (event_id, timestamp, username, action, details) VALUES (?, ?, ?, ?, ?)", events)
        conn.commit()
        
    print(f"[EMAIL] 100,000 records successfully transferred to database!")

def main():
    # the file name is specified here, it will read "email.csv" from the folder
    local_csv_path = "email.csv"
    
    db_path = r"c:\Users\fastie\Pictures\Screenshots\tarteske\tatakyan\security_audit.db"
    
    if not os.path.exists(db_path):
        print("ERROR: security_audit.db not found. Please check that the database is in the correct folder.")
        return

    conn = sqlite3.connect(db_path)
    
    print("Starting to read local email.csv file...")
    process_and_insert_email_file(local_csv_path, conn)
            
    conn.close()
    print("\nAll operations completed.")

if __name__ == '__main__':
    main()
