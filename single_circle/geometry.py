"""
geometry.py — pure math helpers for single_circle.
"""

import math


def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def circle_from_points(a, b):
    center = midpoint(a, b)
    radius = distance(a, b) / 2
    return center, radius
