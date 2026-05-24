# models.py - Data Structures
# the classes used in the project are defined here
# each one represents a different type of data

import json
from datetime import datetime


class Event:
    """a security event from the database"""

    def __init__(self, id, event_id, timestamp, username, action, details, source_table=""):
        self.id = id
        self.event_id = event_id          # Windows Event ID (4624=Login, 4663=File etc)
        self.timestamp = timestamp
        self.username = username
        self.action = action              # LOGIN, READ, WRITE, DELETE
        self.details = details            # extra info (stored as dict)
        self.source_table = source_table

    @classmethod
    def from_db_row(cls, row, source_table=""):
        """creates an Event object from a database row"""

        # try to parse JSON - sometimes the data is broken
        details = {}
        try:
            if row[5]:
                details = json.loads(row[5])
        except Exception:
            details = {}

        # parse timestamp - there are 2 different formats in the data for some reason
        ts_str = row[2]
        ts = None

        # try this one first
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # if that didnt work try this
        if ts is None:
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
            except ValueError:
                pass

        # if both fail just use current time (couldnt find a better solution)
        if ts is None:
            ts = datetime.now()

        return cls(
            id=row[0],
            event_id=row[1],
            timestamp=ts,
            username=row[3],
            action=row[4],
            details=details,
            source_table=source_table,
        )


class Baseline:
    """a users statistical profile.
    defines what normal behavior looks like for them."""

    def __init__(self, username, **kwargs):
        self.username = username

        # event counts
        self.total_events = kwargs.get("total_events", 0)
        self.events_per_day = kwargs.get("events_per_day", 0.0)
        self.events_per_hour_avg = kwargs.get("events_per_hour_avg", 0.0)
        self.events_per_hour_std = kwargs.get("events_per_hour_std", 0.0)

        # file operation counts
        self.total_file_ops = kwargs.get("total_file_ops", 0)
        self.file_reads = kwargs.get("file_reads", 0)
        self.file_writes = kwargs.get("file_writes", 0)
        self.file_deletes = kwargs.get("file_deletes", 0)

        # time stuff
        self.off_hours_count = kwargs.get("off_hours_count", 0)
        self.off_hours_ratio = kwargs.get("off_hours_ratio", 0.0)
        self.deep_night_count = kwargs.get("deep_night_count", 0)

        # which hours they are active
        self.active_hours = kwargs.get("active_hours", {})
        self.active_days = kwargs.get("active_days", 0)

        # z-scores - calculated compared to the group
        self.volume_zscore = kwargs.get("volume_zscore", 0.0)
        self.file_ops_zscore = kwargs.get("file_ops_zscore", 0.0)
        self.delete_zscore = kwargs.get("delete_zscore", 0.0)


class Alert:
    """a detected anomaly alert"""

    def __init__(self, username, timestamp, risk_level, category, reason,
                 details=None, related_event_ids=None, id=None):
        self.username = username
        self.timestamp = timestamp
        self.risk_level = risk_level       # CRITICAL, REVIEW, NORMAL
        self.category = category           # TEMPORAL, VOLUMETRIC etc
        self.reason = reason               # why this alert was created
        self.details = details if details else {}
        self.related_event_ids = related_event_ids if related_event_ids else []
        self.id = id

    def to_dict(self):
        """turns the object into a dictionary"""
        result = {
            "id": self.id,
            "username": self.username,
            "timestamp": self.timestamp,
            "risk_level": self.risk_level,
            "category": self.category,
            "reason": self.reason,
            "details": self.details,
            "related_event_ids": self.related_event_ids,
        }
        return result
