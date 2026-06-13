"""
geometry.py — pure math for triangle angle-bisector construction.
No pygame dependency. All coordinates are world-space floats.
"""

import math
import numpy as np


def normalize(v):
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


def angle_bisector(prev_v, vertex, next_v):
    """Internal angle bisector direction at `vertex`."""
    u1 = normalize(np.array(prev_v) - np.array(vertex))
    u2 = normalize(np.array(next_v) - np.array(vertex))
    return normalize(u1 + u2)


def perpendicular_dir(d):
    """Rotate 2D direction vector 90° counter-clockwise."""
    return np.array([-d[1], d[0]])


def line_intersection(p1, d1, p2, d2):
    """Intersection of two lines: p1 + t*d1 and p2 + s*d2."""
    A = np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]])
    b = np.array(p2) - np.array(p1)
    t = np.linalg.solve(A, b)[0]
    return np.array(p1) + t * d1


def equilateral_triangle(center, side_length):
    """Return three vertices of an equilateral triangle centered at `center`."""
    cx, cy = center
    h = math.sqrt(3) / 2 * side_length
    r = 2 * h / 3
    return [
        np.array([cx, cy - r]),
        np.array([cx - side_length / 2, cy + h - r]),
        np.array([cx + side_length / 2, cy + h - r]),
    ]


def next_generation(triangle):
    """Compute the next triangle using angle-bisector perpendicular construction.

    Given triangle as [A, B, C] (list of 3 numpy arrays),
    returns (new_triangle, bisectors, perps) where:
      - new_triangle = [P, Q, R] vertices of the next generation
      - bisectors = [bA, bB, bC] direction vectors of internal bisectors
      - perps = [pA, pB, pC] direction vectors of perpendicular lines
    """
    A, B, C = triangle

    bA = angle_bisector(B, A, C)
    bB = angle_bisector(C, B, A)
    bC = angle_bisector(A, C, B)

    pA = perpendicular_dir(bA)
    pB = perpendicular_dir(bB)
    pC = perpendicular_dir(bC)

    P = line_intersection(A, pA, B, pB)
    Q = line_intersection(B, pB, C, pC)
    R = line_intersection(C, pC, A, pA)

    return ([P, Q, R], [bA, bB, bC], [pA, pB, pC])


def distance(a, b):
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def triangle_center(triangle):
    return np.mean(triangle, axis=0)


def triangle_extent(triangles, center):
    """Furthest distance from `center` to any vertex among all triangles."""
    best = 0.0
    for tri, _ in triangles:
        for v in tri:
            best = max(best, distance(center, v))
    return best
