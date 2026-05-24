# baselines.py - Baseline (Normal Profile) Calculation
# we create a "normal behavior" profile for each user
# then we compare new events against this profile
#
# z-score formula (from statistics class): z = (x - mean) / std
# hopefully it works correctly...

import math
from models import Baseline
import config


def calculate_user_baseline(username, events):
    """
    creates a single users profile.
    counts total operations, file reads/writes etc.
    """

    baseline = Baseline(username=username)

    # if the user has no events dont crash, just return empty
    if not events:
        return baseline

    baseline.total_events = len(events)

    # count file operations
    read_count = 0
    write_count = 0
    delete_count = 0

    for e in events:
        if e.action == "READ":
            read_count += 1
        elif e.action == "WRITE":
            write_count += 1
        elif e.action == "DELETE":
            delete_count += 1

    baseline.file_reads = read_count
    baseline.file_writes = write_count
    baseline.file_deletes = delete_count
    
    # total file operations
    baseline.total_file_ops = read_count + write_count + delete_count

    # find which hours they are active
    hour_distribution = {}
    different_days = set() # using set so it doesnt count same day twice

    for event in events:
        hour = event.timestamp.hour
        day = event.timestamp.date()

        if hour in hour_distribution:
            hour_distribution[hour] += 1
        else:
            hour_distribution[hour] = 1

        different_days.add(day)

        # check if its outside work hours
        if hour < config.WORK_HOURS_START or hour >= config.WORK_HOURS_END:
            baseline.off_hours_count += 1

        # midnight activity
        if hour >= config.NIGHT_HOURS_START and hour < config.NIGHT_HOURS_END:
            baseline.deep_night_count += 1

    baseline.active_hours = hour_distribution
    baseline.active_days = len(different_days)

    # off-hours ratio (added if check to avoid division by zero)
    if baseline.total_events > 0:
        baseline.off_hours_ratio = baseline.off_hours_count / baseline.total_events

    # daily average
    if baseline.active_days > 0:
        baseline.events_per_day = baseline.total_events / baseline.active_days

    # hourly average and standard deviation
    hour_values = list(hour_distribution.values())
    if len(hour_values) > 0:
        total = 0
        for val in hour_values:
            total += val
        average = total / len(hour_values)
        baseline.events_per_hour_avg = average

        # standard deviation (n-1 because its a sample)
        if len(hour_values) > 1:
            diff_squared_sum = 0
            for val in hour_values:
                diff = val - average
                diff_squared_sum += (diff * diff)
            
            variance = diff_squared_sum / (len(hour_values) - 1)
            baseline.events_per_hour_std = math.sqrt(variance)

    return baseline


def calculate_group_zscores(baselines):
    """
    calculates Z-Score relative to other users.
    z = (persons value - group average) / group std
    """

    if len(baselines) < 2:
        return baselines

    volumes = []
    file_operations = []
    deletions = []

    for b in baselines:
        volumes.append(b.total_events)
        file_operations.append(b.total_file_ops)
        deletions.append(b.file_deletes)

    # average and std for total volume
    vol_avg = sum(volumes) / len(volumes)
    vol_diff = 0
    for v in volumes:
        vol_diff += (v - vol_avg) ** 2
    vol_std = math.sqrt(vol_diff / (len(volumes) - 1))

    # average and std for file operations
    fops_avg = sum(file_operations) / len(file_operations)
    fops_diff = 0
    for v in file_operations:
        fops_diff += (v - fops_avg) ** 2
    fops_std = math.sqrt(fops_diff / (len(file_operations) - 1))

    # average and std for deletions
    del_avg = sum(deletions) / len(deletions)
    del_diff = 0
    for v in deletions:
        del_diff += (v - del_avg) ** 2
    del_std = math.sqrt(del_diff / (len(deletions) - 1))

    # assign z-scores
    for baseline in baselines:
        if vol_std > 0:
            baseline.volume_zscore = (baseline.total_events - vol_avg) / vol_std
        if fops_std > 0:
            baseline.file_ops_zscore = (baseline.total_file_ops - fops_avg) / fops_std
        if del_std > 0:
            baseline.delete_zscore = (baseline.file_deletes - del_avg) / del_std

    return baselines


def calculate_all_baselines(user_events_dict):
    """
    main function - calculates baselines for all users.
    called from run_detection.py
    """
    baselines = []
    
    for username, events in user_events_dict.items():
        user_baseline = calculate_user_baseline(username, events)
        baselines.append(user_baseline)
        
    # compare everyone against each other
    baselines = calculate_group_zscores(baselines)
    
    return baselines


def baseline_summary(baseline):
    """returns a summary string for printing to terminal"""
    return f"  User: {baseline.username} | Total Events: {baseline.total_events} | File Ops: {baseline.total_file_ops} | Z-Score (Vol): {baseline.volume_zscore:.2f}"
