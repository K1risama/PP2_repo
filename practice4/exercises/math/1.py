import math

def degrees_to_radians(degrees):
    """Convert degrees to radians"""
    return degrees * (math.pi / 180)

degrees = float(input("Input degree: "))
radians = degrees_to_radians(degrees)

print(f"Output radian: {radians:.6f}")
