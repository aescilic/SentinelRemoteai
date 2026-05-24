# detection_engine.py - Detection Logic
# there are three different checks:
#   1. Temporal   - off-hours activity
#   2. Volumetric - volume anomaly with z-score
#   3. Behavioral - suspicious accounts, bulk deletion
# each alert has a reason explaining why it was triggered
#
# note: this file got pretty long but putting them in separate files
# would be more confusing i think

from datetime import datetime
from models import Event, Baseline, Alert
import config


def temporal_check(username, events, baseline):
    """detects off-hours activities"""
    alerts = []

    night_events = []
    early_morning = []
    late_evening = []

    # split events by time range
    for event in events:
        hour = event.timestamp.hour

        if hour >= config.NIGHT_HOURS_START and hour < config.NIGHT_HOURS_END:
            night_events.append(event)
        elif hour >= config.NIGHT_HOURS_END and hour < config.WORK_HOURS_START:
            early_morning.append(event)
        elif hour >= config.WORK_HOURS_END and hour <= 23:
            late_evening.append(event)

    # CRITICAL if there is midnight activity
    if len(night_events) > 0:
        # find at which hours it happened
        hours = set()
        for e in night_events:
            hours.add(e.timestamp.strftime("%H:%M"))
        hours = sorted(list(hours))

        # count action types
        actions = {}
        for e in night_events:
            if e.action in actions:
                actions[e.action] += 1
            else:
                actions[e.action] = 1

        action_str = ""
        for key in sorted(actions.keys()):
            if action_str != "":
                action_str += ", "
            action_str += key + ": " + str(actions[key])

        # collect event ids (max 20, more than that is unnecessary)
        event_ids = []
        for e in night_events:
            if len(event_ids) < 20:
                event_ids.append(e.id)

        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_CRITICAL,
            category=config.CATEGORY_TEMPORAL,
            reason=(
                "Midnight activity (00:00-06:00). "
                + "'" + username + "' generated " + str(len(night_events)) + " events during these hours. "
                + "Hours: " + ", ".join(hours) + ". "
                + "Actions: [" + action_str + "]. "
                + "Requires urgent review."
            ),
            details={
                "window": "00:00-06:00",
                "event_count": len(night_events),
            },
            related_event_ids=event_ids,
        )
        alerts.append(alert)

    # REVIEW if there is early morning activity (06:00-08:00)
    if len(early_morning) > 0:
        actions = {}
        for e in early_morning:
            if e.action in actions:
                actions[e.action] += 1
            else:
                actions[e.action] = 1

        action_str = ""
        for key in sorted(actions.keys()):
            if action_str != "":
                action_str += ", "
            action_str += key + ": " + str(actions[key])

        event_ids = []
        for e in early_morning:
            if len(event_ids) < 20:
                event_ids.append(e.id)

        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_REVIEW,
            category=config.CATEGORY_TEMPORAL,
            reason=(
                "Early morning activity (06:00-08:00). "
                + "'" + username + "' generated " + str(len(early_morning)) + " events before work hours. "
                + "Actions: [" + action_str + "]. Needs review."
            ),
            details={"window": "06:00-08:00", "event_count": len(early_morning)},
            related_event_ids=event_ids,
        )
        alerts.append(alert)

    # REVIEW if there is late evening activity (18:00-24:00) and count > 5
    if len(late_evening) > 5:
        actions = {}
        for e in late_evening:
            if e.action in actions:
                actions[e.action] += 1
            else:
                actions[e.action] = 1

        action_str = ""
        for key in sorted(actions.keys()):
            if action_str != "":
                action_str += ", "
            action_str += key + ": " + str(actions[key])

        event_ids = []
        for e in late_evening:
            if len(event_ids) < 20:
                event_ids.append(e.id)

        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_REVIEW,
            category=config.CATEGORY_TEMPORAL,
            reason=(
                "Heavy evening activity (18:00-24:00). "
                + "'" + username + "' generated " + str(len(late_evening)) + " events after work hours. "
                + "Actions: [" + action_str + "]. Possible data exfiltration."
            ),
            details={"window": "18:00-24:00", "event_count": len(late_evening)},
            related_event_ids=event_ids,
        )
        alerts.append(alert)

    return alerts


def volumetric_check(username, baseline):
    """volume anomaly detection with z-score.
    z >= 3.0 -> CRITICAL
    z >= 2.0 -> REVIEW"""
    alerts = []

    # file operations z-score check
    fops_z = abs(baseline.file_ops_zscore)

    if fops_z >= config.ZSCORE_CRITICAL:
        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_CRITICAL,
            category=config.CATEGORY_VOLUMETRIC,
            reason=(
                "EXCESSIVE file access volume. '" + username + "' performed " + str(baseline.total_file_ops) + " file operations. "
                + "Z-score: " + str(round(baseline.file_ops_zscore, 2)) + ". "
                + "Significantly above group average."
            ),
            details={"total_file_ops": baseline.total_file_ops, "zscore": round(baseline.file_ops_zscore, 2)},
        )
        alerts.append(alert)
    elif fops_z >= config.ZSCORE_REVIEW:
        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_REVIEW,
            category=config.CATEGORY_VOLUMETRIC,
            reason=(
                "High file access volume. '" + username + "' performed " + str(baseline.total_file_ops) + " file operations. "
                + "Z-score: " + str(round(baseline.file_ops_zscore, 2)) + "."
            ),
            details={"total_file_ops": baseline.total_file_ops, "zscore": round(baseline.file_ops_zscore, 2)},
        )
        alerts.append(alert)

    # total event volume z-score check
    vol_z = abs(baseline.volume_zscore)

    if vol_z >= config.ZSCORE_CRITICAL:
        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_CRITICAL,
            category=config.CATEGORY_VOLUMETRIC,
            reason=(
                "EXCESSIVE total event volume. '" + username + "' generated " + str(baseline.total_events) + " events in total. "
                + "Z-score: " + str(round(baseline.volume_zscore, 2)) + "."
            ),
            details={"total_events": baseline.total_events, "zscore": round(baseline.volume_zscore, 2)},
        )
        alerts.append(alert)
    elif vol_z >= config.ZSCORE_REVIEW:
        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_REVIEW,
            category=config.CATEGORY_VOLUMETRIC,
            reason=(
                "High total event volume. '" + username + "' generated " + str(baseline.total_events) + " events in total. "
                + "Z-score: " + str(round(baseline.volume_zscore, 2)) + "."
            ),
            details={"total_events": baseline.total_events, "zscore": round(baseline.volume_zscore, 2)},
        )
        alerts.append(alert)

    return alerts


def behavioral_check(username, events, baseline):
    """checks for suspicious behavior patterns"""
    alerts = []

    # check if the account is a guest/suspicious one
    is_suspicious = False
    for account in config.SUSPICIOUS_ACCOUNTS:
        if username.lower() == account.lower():
            is_suspicious = True
            break

    if is_suspicious:
        # filter file events
        file_events = []
        for e in events:
            if e.action == "READ" or e.action == "WRITE" or e.action == "DELETE":
                file_events.append(e)

        if len(file_events) > 0:
            # count action types
            actions = {}
            for e in file_events:
                if e.action in actions:
                    actions[e.action] += 1
                else:
                    actions[e.action] = 1

            action_str = ""
            for key in sorted(actions.keys()):
                if action_str != "":
                    action_str += ", "
                action_str += key + ": " + str(actions[key])

            # find which files were accessed
            accessed_files = set()
            for e in file_events:
                if "file_path" in e.details:
                    accessed_files.add(e.details["file_path"])
                elif "file" in e.details:
                    accessed_files.add(e.details["file"])
                else:
                    accessed_files.add("unknown")

            event_ids = []
            for e in file_events:
                if len(event_ids) < 20:
                    event_ids.append(e.id)

            alert = Alert(
                username=username,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                risk_level=config.RISK_CRITICAL,
                category=config.CATEGORY_BEHAVIORAL,
                reason=(
                    "SUSPICIOUS ACCOUNT: '" + username + "' performed " + str(len(file_events)) + " file operations "
                    + "[" + action_str + "]. "
                    + "Accessed " + str(len(accessed_files)) + " unique files. "
                    + "Guest accounts should not have this level of access."
                ),
                details={
                    "account_type": "guest/temporary",
                    "file_operation_count": len(file_events),
                },
                related_event_ids=event_ids,
            )
            alerts.append(alert)

    # excessive deletion check
    if baseline.file_deletes >= config.DELETE_CRITICAL:
        delete_events = []
        for e in events:
            if e.action == "DELETE":
                delete_events.append(e)

        deleted_files = set()
        for e in delete_events:
            if "file_path" in e.details:
                deleted_files.add(e.details["file_path"])
            elif "file" in e.details:
                deleted_files.add(e.details["file"])
            else:
                deleted_files.add("unknown")

        event_ids = []
        for e in delete_events:
            if len(event_ids) < 20:
                event_ids.append(e.id)

        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_CRITICAL,
            category=config.CATEGORY_BEHAVIORAL,
            reason=(
                "EXCESSIVE DELETION: '" + username + "' deleted " + str(baseline.file_deletes) + " files "
                + "(threshold: " + str(config.DELETE_CRITICAL) + "). "
                + "Z-score: " + str(round(baseline.delete_zscore, 2)) + ". "
                + "Potential sabotage."
            ),
            details={"delete_count": baseline.file_deletes, "zscore": round(baseline.delete_zscore, 2)},
            related_event_ids=event_ids,
        )
        alerts.append(alert)

    elif baseline.file_deletes >= config.DELETE_REVIEW:
        alert = Alert(
            username=username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_REVIEW,
            category=config.CATEGORY_BEHAVIORAL,
            reason=(
                "High deletion count. '" + username + "' deleted " + str(baseline.file_deletes) + " files "
                + "(threshold: " + str(config.DELETE_REVIEW) + "). "
                + "Z-score: " + str(round(baseline.delete_zscore, 2)) + "."
            ),
            details={"delete_count": baseline.file_deletes, "zscore": round(baseline.delete_zscore, 2)},
        )
        alerts.append(alert)

    # network logon check (Type 3) - only for suspicious accounts
    if is_suspicious:
        network_logons = []
        for e in events:
            if e.action == "LOGIN":
                if e.details.get("logon_type") == 3:
                    network_logons.append(e)

        if len(network_logons) > 0:
            alert = Alert(
                username=username,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                risk_level=config.RISK_REVIEW,
                category=config.CATEGORY_BEHAVIORAL,
                reason=(
                    "Network logon from suspicious account (Type 3). '" + username + "' performed " + str(len(network_logons)) + " "
                    + "network logons. This is abnormal."
                ),
                details={"logon_type": 3, "count": len(network_logons)},
            )
            alerts.append(alert)

    return alerts


def combined_risk_escalation(alerts, baseline):
    """escalates risk when temporal + volumetric anomalies happen together.
    for example: working at night AND downloading too many files = CRITICAL"""

    # find temporal alerts
    temporal_alerts = []
    for a in alerts:
        if a.category == config.CATEGORY_TEMPORAL:
            temporal_alerts.append(a)

    # if there is a temporal alert AND z-score is high, create combined alert
    threshold_exceeded = (baseline.file_ops_zscore >= config.COMBINED_THRESHOLD_ZSCORE or
                          baseline.volume_zscore >= config.COMBINED_THRESHOLD_ZSCORE)

    if len(temporal_alerts) > 0 and threshold_exceeded:
        # count volumetric alerts
        volumetric_count = 0
        for a in alerts:
            if a.category == config.CATEGORY_VOLUMETRIC:
                volumetric_count += 1

        combined_alert = Alert(
            username=baseline.username,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level=config.RISK_CRITICAL,
            category=config.CATEGORY_COMBINED,
            reason=(
                "COMBINED RISK: '" + baseline.username + "'. "
                + "Off-hours activity + high data access combined. "
                + "Volume Z=" + str(round(baseline.volume_zscore, 2)) + ", "
                + "FileOps Z=" + str(round(baseline.file_ops_zscore, 2)) + ". "
                + "High probability of insider threat."
            ),
            details={
                "temporal_alert_count": len(temporal_alerts),
                "volumetric_alert_count": volumetric_count,
                "volume_zscore": round(baseline.volume_zscore, 2),
                "file_ops_zscore": round(baseline.file_ops_zscore, 2),
            },
        )
        alerts.append(combined_alert)

    return alerts

def shadow_ai_check(username, events):
    """checks if the user is visiting restricted AI domains (Shadow AI risk)"""
    alerts = []
    
    # filter web visits
    web_events = []
    for e in events:
        if e.action == "WEB_VISIT":
            web_events.append(e)
            
    if not web_events:
        return alerts

    # check domains against the blacklist
    for e in web_events:
        domain = e.details.get("domain", "").lower()
        if not domain:
            continue
            
        for restricted in config.SHADOW_AI_DOMAINS:
            if restricted in domain:
                # found a shadow ai visit!
                alert = Alert(
                    username=username,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    risk_level=config.RISK_REVIEW,
                    category=config.CATEGORY_SHADOW_AI,
                    reason=(
                        "SHADOW AI DETECTION: '" + username + "' accessed restricted AI service: " + domain + ". "
                        + "Possible data leakage risk. Needs review."
                    ),
                    details={
                        "domain": domain,
                        "url": e.details.get("url", ""),
                        "action": "WEB_VISIT"
                    },
                    related_event_ids=[e.id]
                )
                alerts.append(alert)
                break # only create one alert per event

    return alerts


def reduce_false_positives(alerts, events):
    """filters out common false positive patterns (harmless activity).
    without this the admin account was triggering alarms every night lol"""
    
    for alert in alerts:
        is_false_positive = False
        fp_reason = ""
        
        # 1. Whitelist check (admin/system accounts shouldnt trigger basic alerts)
        if hasattr(config, 'WHITELISTED_ACCOUNTS') and alert.username.lower() in [acc.lower() for acc in config.WHITELISTED_ACCOUNTS]:
            if alert.category != config.CATEGORY_COMBINED: # combined risk is still evaluated
                is_false_positive = True
                fp_reason = " (BENIGN: System/Admin account is in the trusted list)"
            
        # 2. Harmless evening activity (only READ/LOGIN actions)
        elif alert.category == config.CATEGORY_TEMPORAL and alert.risk_level == config.RISK_REVIEW:
            if "18:00-24:00" in alert.reason:
                # if they are just reading documents they are probably doing overtime, not a threat
                if hasattr(alert, 'related_event_ids') and alert.related_event_ids:
                    evening_actions = [e.action for e in events if hasattr(e, 'id') and e.id in alert.related_event_ids]
                    if len(evening_actions) > 0 and all(a in ["READ", "LOGIN"] for a in evening_actions):
                        is_false_positive = True
                        fp_reason = " (BENIGN: Only document reading activity outside work hours)"
                    
        # 3. Low impact volumetric (high z-score but very low actual count)
        elif alert.category == config.CATEGORY_VOLUMETRIC and alert.risk_level == config.RISK_REVIEW:
            if "total_file_ops" in alert.details and alert.details["total_file_ops"] < 20:
                is_false_positive = True
                fp_reason = " (BENIGN: Z-score is high but absolute operation count is very low)"
                
        if is_false_positive:
            alert.risk_level = config.RISK_NORMAL
            alert.reason += fp_reason
            
    return alerts


def run_detection_for_user(username, events, baseline):
    """runs all detection checks for one user"""
    all_alerts = []

    # run each check one by one
    temporal = temporal_check(username, events, baseline)
    for a in temporal:
        all_alerts.append(a)

    volumetric = volumetric_check(username, baseline)
    for a in volumetric:
        all_alerts.append(a)

    behavioral = behavioral_check(username, events, baseline)
    for a in behavioral:
        all_alerts.append(a)

    # shadow ai check
    shadow_ai = shadow_ai_check(username, events)
    for a in shadow_ai:
        all_alerts.append(a)

    # filter out false positives
    all_alerts = reduce_false_positives(all_alerts, events)

    # combined risk assessment
    all_alerts = combined_risk_escalation(all_alerts, baseline)

    return all_alerts


def run_detection_for_all_users(user_events_dict, baselines):
    """runs detection for all users"""

    # create a baseline map for fast lookup by username
    baseline_map = {}
    for b in baselines:
        baseline_map[b.username] = b

    all_alerts = []

    for username in user_events_dict:
        events = user_events_dict[username]

        if username not in baseline_map:
            # print("baseline not found for:", username)  # debug
            continue

        baseline = baseline_map[username]
        user_alerts = run_detection_for_user(username, events, baseline)

        for a in user_alerts:
            all_alerts.append(a)

    # sort so CRITICAL alerts show up first
    level_order = {
        config.RISK_CRITICAL: 0,
        config.RISK_REVIEW: 1,
        config.RISK_NORMAL: 2,
    }

    all_alerts.sort(key=lambda a: level_order.get(a.risk_level, 99))

    return all_alerts
