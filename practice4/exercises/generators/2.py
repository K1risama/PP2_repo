def even_numbers_generator(n):
    """Generator that yields even numbers from 0 to n"""
    for i in range(n + 1):
        if i % 2 == 0:
            yield i

n = int(input("Enter a number: "))

even_numbers = list(even_numbers_generator(n))
even_numbers_str = ', '.join(str(num) for num in even_numbers)
print(f"Even numbers from 0 to {n}: {even_numbers_str}")

