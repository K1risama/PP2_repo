from datetime import datetime, timedelta

current_time = datetime.now()
print(f"With microseconds: {current_time}")

without_microseconds = current_time.replace(microsecond=0)
print(f"Without microseconds: {without_microseconds}")

without_microseconds_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
print(f"Without microseconds (str): {without_microseconds_str}")
