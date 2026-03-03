from datetime import datetime, timedelta
current_date = datetime.now()
print(f"Current date: {current_date}")

five_days_ago = current_date - timedelta(days=5)
print(f"Five days ago: {five_days_ago}")

