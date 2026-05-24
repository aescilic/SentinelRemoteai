# run_detection.py - Main Runner
# runs all modules one after another
# usage: python run_detection.py

import sys
import os
from datetime import datetime

# fix for Turkish characters in Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import database as db
import baselines as baseline_module
from baselines import baseline_summary
from detection_engine import run_detection_for_all_users
import config


def main():
    # command line arguments
    args = sys.argv[1:]

    baseline_only = False

    for arg in args:
        if arg == "--baseline-only":
            baseline_only = True
        elif arg == "--help" or arg == "-h":
            print("Usage: python run_detection.py [--baseline-only] [--help]")
            return

    print("")
    print("=" * 60)
    print("  SentinelRemote AI - Detection Engine")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    print("")

    # Step 1: Connect to database
    print("[1/5] Connecting to database...")
    if not os.path.exists(config.DB_PATH):
        print("  ERROR: Database not found: " + config.DB_PATH)
        sys.exit(1)

    conn = db.get_connection()
    db.create_detection_tables(conn)

    # clear previous results
    db.clear_tables(conn)

    # Step 2: Fetch events
    print("[2/5] Fetching events...")
    all_events = db.get_all_events(conn)
    users = db.get_all_users(conn)
    print("  " + str(len(all_events)) + " events loaded")
    print("  " + str(len(users)) + " users found: " + ", ".join(users))

    # group events by user
    user_events = {}
    for event in all_events:
        if event.username not in user_events:
            user_events[event.username] = []
        user_events[event.username].append(event)

    # Step 3: Calculate baselines
    print("[3/5] Calculating baseline profiles...")
    calculated_baselines = baseline_module.calculate_all_baselines(user_events)

    for baseline in calculated_baselines:
        db.save_baseline(conn, baseline)
        print("")
        print(baseline_summary(baseline))

    if baseline_only:
        print("")
        print("  Baselines saved: " + config.DB_PATH)
        conn.close()
        return



    # Step 4: Run detection engine
    print("")
    print("[4/5] Running detection engine...")
    print("  Temporal detection: ON")
    print("  Volumetric detection: ON")
    print("  Behavioral detection: ON")
    print("  Combined escalation: ON")

    all_alerts = run_detection_for_all_users(user_events, calculated_baselines)

    # save alerts
    if len(all_alerts) > 0:
        count = db.insert_alerts_bulk(conn, all_alerts)

        critical_count = 0
        review_count = 0
        normal_count = 0
        for a in all_alerts:
            if a.risk_level == config.RISK_CRITICAL:
                critical_count += 1
            elif a.risk_level == config.RISK_REVIEW:
                review_count += 1
            elif a.risk_level == config.RISK_NORMAL:
                normal_count += 1

        print("")
        print("  " + str(count) + " alerts generated:")
        print("    🔴 CRITICAL: " + str(critical_count))
        print("    🟡 REVIEW:   " + str(review_count))
        print("    🟢 NORMAL:   " + str(normal_count) + " (False Positive/Safe)")
    else:
        print("")
        print("  No alerts generated - all activity is normal.")

    print("")
    print("=" * 60)
    print("  Detection completed successfully.")
    print("  Results saved to database: " + config.DB_PATH)
    print("  To view results run: python -m streamlit run dashboard.py")
    print("=" * 60)
    print("")

    conn.close()


if __name__ == "__main__":
    main()
