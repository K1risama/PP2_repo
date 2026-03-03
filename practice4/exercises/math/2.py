def trapezoid_area(height, base1, base2):
    """Calculate area of a trapezoid: Area = ((base1 + base2) / 2) * height"""
    return ((base1 + base2) / 2) * height

height = float(input("Height: "))
base1 = float(input("Base, first value: "))
base2 = float(input("Base, second value: "))

area = trapezoid_area(height, base1, base2)
print(f"Expected Output: {area}")