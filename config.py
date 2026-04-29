# config.py

# ---- Time windows ----
WORK_HOURS_START = 8   # work hours start
WORK_HOURS_END = 18   # work hours end

# night time activities are generally regarded with suspicion
NIGHT_HOURS_START = 0
NIGHT_HOURS_END = 6


# ---- Z-score thresholds ----
# 3 or above triggers an immediate alarm; 2–3 requires review
ZSCORE_CRITICAL = 3.0
ZSCORE_REVIEW = 2.0


# ---- Account checks ----
# genelde test vs için açılan hesaplar
SUSPICIOUS_ACCOUNTS = ["misafir", "guest", "temp", "test"]


# ---- File operations (hourly) ----
FILE_OP_CRITICAL = 50
FILE_OP_REVIEW = 30


# ---- Delete operations ----
DELETE_CRITICAL = 15
DELETE_REVIEW = 5


# ---- Combined risk ----
# i handled it a bit more carefully
COMBINED_THRESHOLD_ZSCORE = 1.5


# ---- Risk labels ----
RISK_CRITICAL = "CRITICAL"
RISK_REVIEW = "REVIEW"
RISK_NORMAL = "NORMAL"


# ---- UI stuff ----
# is used in the report
RISK_COLORS = {
    "CRITICAL": "#e74c3c",
    "REVIEW": "#f39c12",
    "NORMAL": "#2ecc71",
}

# for terminal output
RISK_EMOJIS = {
    "CRITICAL": "🔴",
    "REVIEW": "🟡",
    "NORMAL": "🟢",
}


# ---- Alert categories ----
CATEGORY_TEMPORAL = "TEMPORAL"
CATEGORY_VOLUMETRIC = "VOLUMETRIC"
CATEGORY_BEHAVIORAL = "BEHAVIORAL"
CATEGORY_COMBINED = "COMBINED"


# ---- DB ----
DB_PATH = "security_audit.db"

# sometimes two different tables appear so heres a list
SOURCE_TABLES = ["security_events", "events"]

# the place where the results are recorded
ALERT_TABLE = "detection_alerts"
BASELINE_TABLE = "detection_baselines"