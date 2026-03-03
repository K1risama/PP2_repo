from datetime import datetime, timedelta


def date_difference_in_seconds(date1, date2):
    """
    Calculates the difference between two dates in seconds
    """
    difference = abs(date2 - date1)
    return difference.total_seconds()

date1 = datetime(2024, 2, 20, 10, 30, 0)
date2 = datetime(2024, 2, 25, 15, 45, 30)

diff_seconds = date_difference_in_seconds(date1, date2)
print(f"Date 1: {date1}")
print(f"Date 2: {date2}")
print(f"Difference in seconds: {diff_seconds}")

now = datetime.now()
one_day_later = now + timedelta(days=1, hours=2, minutes=30)

diff = date_difference_in_seconds(now, one_day_later)
print(f"\nCurrent time: {now}")
print(f"After 1 day 2 hours 30 minutes: {one_day_later}")
print(f"Difference in seconds: {diff}")