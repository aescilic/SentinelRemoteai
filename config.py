# config.py - Settings and Thresholds
# all the constants are here, if you need to change something change it from here

# ---- Time windows ----
WORK_HOURS_START = 8
WORK_HOURS_END = 18

# night activity is usually suspicious
NIGHT_HOURS_START = 0
NIGHT_HOURS_END = 6


# ---- Z-score thresholds ----
# 3 or above = immediate alarm, 2-3 = needs review
ZSCORE_CRITICAL = 3.0
ZSCORE_REVIEW = 2.0


# ---- Account checks ----
# accounts that are usually created for testing etc
SUSPICIOUS_ACCOUNTS = ["misafir", "guest", "temp", "test"]

# trusted accounts that shouldnt trigger basic alerts
WHITELISTED_ACCOUNTS = ["admin", "system", "backup_service", "it_support"]


# ---- Shadow AI ----
# list of generative AI domains that are restricted
SHADOW_AI_DOMAINS = [
    "chatgpt.com", "openai.com", 
    "anthropic.com", "claude.ai", 
    "gemini.google.com", "bard.google.com", 
    "perplexity.ai", "poe.com", "copilot.microsoft.com"
]


# ---- File operations (hourly) ----
FILE_OP_CRITICAL = 50
FILE_OP_REVIEW = 30


# ---- Delete operations ----
DELETE_CRITICAL = 15
DELETE_REVIEW = 5


# ---- Combined risk ----
# i was a bit more careful with this threshold
COMBINED_THRESHOLD_ZSCORE = 1.5


# ---- Risk labels ----
RISK_CRITICAL = "CRITICAL"
RISK_REVIEW = "REVIEW"
RISK_NORMAL = "NORMAL"


# ---- UI related ----
# used in the dashboard for coloring
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
CATEGORY_SHADOW_AI = "SHADOW_AI"


# ---- Database ----
DB_PATH = "security_audit.db"

# sometimes there are 2 different tables so i put them in a list
SOURCE_TABLES = ["security_events", "events"]

# where we save the results
ALERT_TABLE = "detection_alerts"
BASELINE_TABLE = "detection_baselines"