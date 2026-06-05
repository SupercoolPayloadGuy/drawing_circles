"""
geometry.py — pure math, no pygame dependency.
All coordinates are in world-space (floats).
"""

import math
import itertools


def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def circle_from_points(a, b):
    """Return (center, radius) of the circle whose diameter is segment a-b."""
    return midpoint(a, b), distance(a, b) / 2


def angle_on_circle(center, point):
    return math.atan2(point[1] - center[1], point[0] - center[0])


def farthest_extent(origin, circles):
    """
    Radius of the smallest circle centred on `origin` that encloses
    all (center, radius) pairs in `circles`.
    """
    best = 0.0
    for center, radius in circles:
        best = max(best, distance(origin, center) + radius)
    return best


def project_onto_ring(points, origin, ring_radius):
    """
    Project each point radially outward from `origin` onto a circle
    of radius `ring_radius`.
    """
    result = []
    for p in points:
        dx, dy = p[0] - origin[0], p[1] - origin[1]
        ang = math.atan2(dy, dx)
        result.append((
            origin[0] + ring_radius * math.cos(ang),
            origin[1] + ring_radius * math.sin(ang),
        ))
    return result


def deduplicate(points, snap=1):
    """Remove near-duplicate points by snapping to a grid of `snap` units."""
    seen = set()
    out  = []
    for p in points:
        key = (round(p[0] / snap), round(p[1] / snap))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def all_pairs(points):
    return list(itertools.combinations(points, 2))


def cardinal_points(center, radius):
    """Return [TOP, RIGHT, BOTTOM, LEFT] on a circle."""
    import math
    cx, cy = center
    angles = [-math.pi / 2, 0, math.pi / 2, math.pi]
    return [(cx + radius * math.cos(a), cy + radius * math.sin(a)) for a in angles]