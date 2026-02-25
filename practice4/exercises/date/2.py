from datetime import datetime, timedelta

today = datetime.now().date()
print(f"Today: {today}")

yesterday = today - timedelta(days=1)
print(f"Yesterday: {yesterday}")

tomorrow = today + timedelta(days=1)
print(f"Tomorrow: {tomorrow}")
