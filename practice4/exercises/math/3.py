import math

def regular_polygon_area(n_sides, side_length):
    """Calculate area of a regular polygon
    Formula: Area = (n * s²) / (4 * tan(π/n))
    where n = number of sides, s = side length
    """
    return (n_sides * side_length ** 2) / (4 * math.tan(math.pi / n_sides))

n_sides = int(input("Input number of sides: "))
side_length = float(input("Input the length of a side: "))

area = regular_polygon_area(n_sides, side_length)
print(f"The area of the polygon is: {round(area)}")