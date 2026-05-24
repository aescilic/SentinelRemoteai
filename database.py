# database.py - Database Operations
# reads data from the existing database and writes results to new tables
# using sqlite3 because it doesnt need any setup

import sqlite3
import json
from datetime import datetime

from models import Event, Alert, Baseline
import config


def get_connection():
    """connects to the database"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")  # this improves read performance (found it online)
    return conn


def create_detection_tables(conn):
    """creates the result tables. if they already exist it leaves them alone."""

    cursor = conn.cursor()

    # alert table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS """ + config.ALERT_TABLE + """ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            category TEXT NOT NULL,
            reason TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            related_event_ids TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # baseline table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS """ + config.BASELINE_TABLE + """ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            total_events INTEGER DEFAULT 0,
            events_per_day REAL DEFAULT 0.0,
            events_per_hour_avg REAL DEFAULT 0.0,
            events_per_hour_std REAL DEFAULT 0.0,
            total_file_ops INTEGER DEFAULT 0,
            file_reads INTEGER DEFAULT 0,
            file_writes INTEGER DEFAULT 0,
            file_deletes INTEGER DEFAULT 0,
            off_hours_count INTEGER DEFAULT 0,
            off_hours_ratio REAL DEFAULT 0.0,
            deep_night_count INTEGER DEFAULT 0,
            active_hours TEXT DEFAULT '{}',
            active_days INTEGER DEFAULT 0,
            volume_zscore REAL DEFAULT 0.0,
            file_ops_zscore REAL DEFAULT 0.0,
            delete_zscore REAL DEFAULT 0.0,
            computed_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()


def clear_tables(conn):
    """deletes previous results (so each run starts fresh)"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM " + config.ALERT_TABLE)
    cursor.execute("DELETE FROM " + config.BASELINE_TABLE)
    conn.commit()


def get_all_events(conn):
    """fetches all events from the source tables"""
    all_events = []
    cursor = conn.cursor()

    for table in config.SOURCE_TABLES:
        query = f"SELECT id, event_id, timestamp, username, action, details FROM [{table}]"
        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                event = Event.from_db_row(row, source_table=table)
                all_events.append(event)
        except sqlite3.OperationalError:
            pass # table might not exist yet, thats ok

    return all_events


def get_user_events(conn, username):
    """fetches events for a specific user"""
    events = []
    cursor = conn.cursor()

    for table in config.SOURCE_TABLES:
        query = f"SELECT id, event_id, timestamp, username, action, details FROM [{table}] WHERE username = ?"
        try:
            cursor.execute(query, (username,))

            for row in cursor.fetchall():
                event = Event.from_db_row(row, source_table=table)
                events.append(event)
        except sqlite3.OperationalError:
            pass

    return events


def get_all_users(conn):
    """collects unique usernames"""
    users = set()
    cursor = conn.cursor()

    for table in config.SOURCE_TABLES:
        query = f"SELECT DISTINCT username FROM [{table}]"
        try:
            cursor.execute(query)
            for row in cursor.fetchall():
                users.add(row[0])
        except sqlite3.OperationalError:
            pass

    # convert set to list and sort (set doesnt have order)
    result = list(users)
    result.sort()
    return result


def insert_alert(conn, alert):
    """inserts a single alert"""
    cursor = conn.cursor()

    query = ("INSERT INTO " + config.ALERT_TABLE +
             " (username, timestamp, risk_level, category, reason, details, related_event_ids)"
             " VALUES (?, ?, ?, ?, ?, ?, ?)")

    cursor.execute(query, (
        alert.username,
        alert.timestamp,
        alert.risk_level,
        alert.category,
        alert.reason,
        json.dumps(alert.details, ensure_ascii=False),
        json.dumps(alert.related_event_ids),
    ))
    conn.commit()
    return cursor.lastrowid


def insert_alerts_bulk(conn, alerts):
    """inserts multiple alerts at once (faster than one by one)"""
    cursor = conn.cursor()

    for alert in alerts:
        query = ("INSERT INTO " + config.ALERT_TABLE +
                 " (username, timestamp, risk_level, category, reason, details, related_event_ids)"
                 " VALUES (?, ?, ?, ?, ?, ?, ?)")

        cursor.execute(query, (
            alert.username,
            alert.timestamp,
            alert.risk_level,
            alert.category,
            alert.reason,
            json.dumps(alert.details, ensure_ascii=False),
            json.dumps(alert.related_event_ids),
        ))

    conn.commit()
    return len(alerts)


def save_baseline(conn, baseline):
    """saves the users baseline profile"""
    cursor = conn.cursor()

    # INSERT OR REPLACE - if user exists update it, if not insert new
    query = ("INSERT OR REPLACE INTO " + config.BASELINE_TABLE +
             " (username, total_events, events_per_day, events_per_hour_avg, events_per_hour_std,"
             " total_file_ops, file_reads, file_writes, file_deletes,"
             " off_hours_count, off_hours_ratio, deep_night_count,"
             " active_hours, active_days, volume_zscore, file_ops_zscore, delete_zscore)"
             " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

    cursor.execute(query, (
        baseline.username,
        baseline.total_events,
        baseline.events_per_day,
        baseline.events_per_hour_avg,
        baseline.events_per_hour_std,
        baseline.total_file_ops,
        baseline.file_reads,
        baseline.file_writes,
        baseline.file_deletes,
        baseline.off_hours_count,
        baseline.off_hours_ratio,
        baseline.deep_night_count,
        json.dumps(baseline.active_hours),
        baseline.active_days,
        baseline.volume_zscore,
        baseline.file_ops_zscore,
        baseline.delete_zscore,
    ))
    conn.commit()


def get_all_alerts(conn, risk_level=None):
    """fetches saved alerts"""
    cursor = conn.cursor()

    if risk_level:
        query = "SELECT * FROM " + config.ALERT_TABLE + " WHERE risk_level = ? ORDER BY id"
        cursor.execute(query, (risk_level,))
    else:
        query = "SELECT * FROM " + config.ALERT_TABLE + " ORDER BY id"
        cursor.execute(query)

    columns = []
    for desc in cursor.description:
        columns.append(desc[0])

    results = []
    for row in cursor.fetchall():
        # convert row to dict
        d = {}
        for i in range(len(columns)):
            d[columns[i]] = row[i]

        # parse JSON fields
        try:
            d["details"] = json.loads(d.get("details", "{}"))
        except Exception:
            d["details"] = {}
        try:
            d["related_event_ids"] = json.loads(d.get("related_event_ids", "[]"))
        except Exception:
            d["related_event_ids"] = []

        results.append(d)

    return results


def get_all_baselines(conn):
    """fetches saved baselines"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM " + config.BASELINE_TABLE + " ORDER BY username")

    columns = []
    for desc in cursor.description:
        columns.append(desc[0])

    results = []
    for row in cursor.fetchall():
        d = {}
        for i in range(len(columns)):
            d[columns[i]] = row[i]

        try:
            d["active_hours"] = json.loads(d.get("active_hours", "{}"))
        except Exception:
            d["active_hours"] = {}

        results.append(d)

    return results
