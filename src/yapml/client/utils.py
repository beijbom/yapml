from datetime import timedelta


def time_delta_string(delta: timedelta) -> str:
    """
    Convert a timestamp to a human-readable relative time string.

    Args:
        timestamp: The datetime to convert

    Returns:
        A string like "just now", "5 seconds ago", "2 minutes ago", "3 hours ago", "2 days ago", etc.
    """
    # Convert to total seconds
    seconds = int(delta.total_seconds())

    # Define time intervals
    minute = 60
    hour = minute * 60
    day = hour * 24
    week = day * 7
    month = day * 30
    year = day * 365

    if seconds < 10:
        return "just now"
    elif seconds < minute:
        return f"{seconds} seconds ago"
    elif seconds < 2 * minute:
        return "a minute ago"
    elif seconds < hour:
        return f"{seconds // minute} minutes ago"
    elif seconds < 2 * hour:
        return "an hour ago"
    elif seconds < day:
        return f"{seconds // hour} hours ago"
    elif seconds < 2 * day:
        return "yesterday"
    elif seconds < week:
        return f"{seconds // day} days ago"
    elif seconds < 2 * week:
        return "a week ago"
    elif seconds < month:
        return f"{seconds // week} weeks ago"
    elif seconds < 2 * month:
        return "a month ago"
    elif seconds < year:
        return f"{seconds // month} months ago"
    elif seconds < 2 * year:
        return "a year ago"
    else:
        return f"{seconds // year} years ago"
