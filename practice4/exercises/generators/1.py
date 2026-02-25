def square_generator(n):
    """Generator that yields squares of numbers from 0 to n"""
    for i in range(n + 1):
        yield i * i

n = 10
print(f"Squares of numbers from 0 to {n}:")
for square in square_generator(n):
    print(square, end=" ")
print("\n")

