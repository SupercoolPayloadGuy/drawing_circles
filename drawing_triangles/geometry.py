"""
geometry.py — pure math for triangle angle-bisector construction.
No pygame dependency. All coordinates are world-space floats.
No numpy dependency.
"""

import math


def _norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1])


def _normalize(v):
    n = _norm(v)
    return (v[0] / n, v[1] / n) if n > 0 else v


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _scale(v, s):
    return (v[0] * s, v[1] * s)


def angle_bisector(prev_v, vertex, next_v):
    """Internal angle bisector direction at `vertex`."""
    u1 = _normalize(_sub(prev_v, vertex))
    u2 = _normalize(_sub(next_v, vertex))
    return _normalize(_add(u1, u2))


def perpendicular_dir(d):
    """Rotate 2D direction vector 90° counter-clockwise."""
    return (-d[1], d[0])


def line_intersection(p1, d1, p2, d2):
    """Intersection of two lines: p1 + t*d1 and p2 + s*d2.
    Solves using Cramer's rule.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    det = d1[0] * (-d2[1]) - (-d2[0]) * d1[1]
    t = (dx * (-d2[1]) - (-d2[0]) * dy) / det
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def equilateral_triangle(center, side_length):
    """Return three vertices of an equilateral triangle centered at `center`."""
    cx, cy = center
    h = math.sqrt(3) / 2 * side_length
    r = 2 * h / 3
    return [
        (cx, cy - r),
        (cx - side_length / 2, cy + h - r),
        (cx + side_length / 2, cy + h - r),
    ]


def next_generation(triangle):
    """Compute the next triangle using angle-bisector perpendicular construction.

    Given triangle as [A, B, C] (list of 3 (x,y) tuples),
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
    return math.hypot(a[0] - b[0], a[1] - b[1])


def triangle_center(triangle):
    n = len(triangle)
    sx = sum(v[0] for v in triangle) / n
    sy = sum(v[1] for v in triangle) / n
    return (sx, sy)


def triangle_extent(triangles, center):
    """Furthest distance from `center` to any vertex among all triangles."""
    best = 0.0
    for tri, _ in triangles:
        for v in tri:
            best = max(best, distance(center, v))
    return best
