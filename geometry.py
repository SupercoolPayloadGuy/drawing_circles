"""
geometry.py — pure math, no pygame dependency.
All coordinates are world-space floats.
"""

import math
import itertools


def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def circle_from_points(a, b):
    """Circle whose diameter is segment a–b."""
    return midpoint(a, b), distance(a, b) / 2


def angle_on_circle(center, point):
    return math.atan2(point[1] - center[1], point[0] - center[0])


def farthest_extent(origin, circles):
    """Radius of the smallest circle centred on `origin` enclosing all (center, radius) pairs."""
    return max((distance(origin, c) + r for c, r in circles), default=0.0)


def project_onto_ring(points, origin, ring_radius):
    """Project each point radially from `origin` onto a circle of `ring_radius`."""
    result = []
    for p in points:
        ang = math.atan2(p[1] - origin[1], p[0] - origin[0])
        result.append((
            origin[0] + ring_radius * math.cos(ang),
            origin[1] + ring_radius * math.sin(ang),
        ))
    return result


def deduplicate(points, snap=1):
    """Remove near-duplicate points by snapping to a grid of `snap` units."""
    seen, out = set(), []
    for p in points:
        key = (round(p[0] / snap), round(p[1] / snap))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def all_pairs(points):
    return itertools.combinations(points, 2)


def cardinal_points(center, radius, count=4):
    """Return `count` points evenly spaced around a circle, starting at the top."""
    cx, cy = center
    start  = -math.pi / 2
    return [
        (cx + radius * math.cos(start + 2 * math.pi * i / count),
         cy + radius * math.sin(start + 2 * math.pi * i / count))
        for i in range(count)
    ]