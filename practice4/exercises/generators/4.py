def squares(a, b):
    """Generator that yields squares of all numbers from a to b"""
    for i in range(a, b + 1):
        yield i * i

a = 5
b = 15
print(f"Squares of numbers from {a} to {b}:")
for value in squares(a, b):
    print(value, end=" ")
print("\n")

# 5

def countdown_generator(n):
    """Generator that yields numbers from n down to 0"""
    for i in range(n, -1, -1):
        yield i

n = 10
print(f"Numbers from {n} down to 0:")
for num in countdown_generator(n):
    print(num, end=" ")
print("\n")

try:
    n = int(input("Enter a number for countdown: "))
    print(f"Countdown from {n} to 0:")
    countdown_list = list(countdown_generator(n))
    print(' → '.join(str(num) for num in countdown_list))
except ValueError:
    print("Please enter a valid integer")