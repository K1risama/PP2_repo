def parallelogram_area(base, height):
    """Calculate area of a parallelogram: Area = base * height"""
    return base * height

base = float(input("Length of base: "))
height = float(input("Height of parallelogram: "))

area = parallelogram_area(base, height)
print(f"Expected Output: {area}")