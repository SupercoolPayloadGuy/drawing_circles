import pygame
import math
import itertools
import time

# ==================================================
# SETTINGS
# ==================================================

WIDTH = 1200
HEIGHT = 1200

BACKGROUND = (240, 240, 240)
CIRCLE_COLOR = (80, 80, 80)
POINT_COLOR = (40, 120, 255)

BASE_RADIUS = 140

DELAY = 1  # seconds between animation steps

# ==================================================
# PYGAME
# ==================================================

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Recursive Circle Construction")

CENTER = (WIDTH // 2, HEIGHT // 2)

# ==================================================
# HELPERS
# ==================================================

drawn_circles = []
drawn_points = []

def midpoint(a, b):
    return (
        (a[0] + b[0]) / 2,
        (a[1] + b[1]) / 2
    )

def distance(a, b):
    return math.hypot(
        a[0] - b[0],
        a[1] - b[1]
    )

def circle_from_points(a, b):
    center = midpoint(a, b)
    radius = distance(a, b) / 2
    return center, radius

def redraw():

    screen.fill(BACKGROUND)

    for center, radius in drawn_circles:

        pygame.draw.circle(
            screen,
            CIRCLE_COLOR,
            (round(center[0]), round(center[1])),
            round(radius),
            1
        )

    for point in drawn_points:

        pygame.draw.circle(
            screen,
            POINT_COLOR,
            (round(point[0]), round(point[1])),
            5
        )

    pygame.display.flip()

def add_circle(center, radius):

    drawn_circles.append((center, radius))
    redraw()

def add_point(point):

    drawn_points.append(point)
    redraw()

def wait():
    end = time.time() + DELAY

    while time.time() < end:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        time.sleep(0.01)

# ==================================================
# BASE POINTS
# ==================================================

A = CENTER

angles = [
    -math.pi/2,   # top
    0,            # right
    math.pi/2,    # bottom
    math.pi       # left
]

outer = []

for ang in angles:

    x = A[0] + BASE_RADIUS * math.cos(ang)
    y = A[1] + BASE_RADIUS * math.sin(ang)

    outer.append((x, y))

TOP, RIGHT, BOTTOM, LEFT = outer

# ==================================================
# STAGE 1
# Original circle
# ==================================================

add_circle(A, BASE_RADIUS)
wait()

# ==================================================
# STAGE 2
# Outer points
# ==================================================

add_point(A)

for p in outer:
    add_point(p)

wait()

# ==================================================
# STAGE 3
# Center -> outer circles
# ==================================================

for p in [TOP, BOTTOM]:

    c, r = circle_from_points(A, p)
    add_circle(c, r)

wait()

for p in [LEFT, RIGHT]:

    c, r = circle_from_points(A, p)
    add_circle(c, r)

wait()

# ==================================================
# STAGE 4
# Outer pair circles
# ==================================================

pairs = [

    (TOP, RIGHT),
    (BOTTOM, LEFT),

    (TOP, LEFT),
    (BOTTOM, RIGHT),

    (TOP, BOTTOM),
    (LEFT, RIGHT)

]

for i in range(0, len(pairs), 2):

    for p1, p2 in pairs[i:i+2]:

        c, r = circle_from_points(p1, p2)
        add_circle(c, r)

    wait()

# ==================================================
# ENCLOSING CIRCLE #1
# ==================================================

max_extent = BASE_RADIUS

for center, radius in drawn_circles:

    extent = distance(A, center) + radius

    if extent > max_extent:
        max_extent = extent

FIRST_OUTER_RADIUS = max_extent

add_circle(A, FIRST_OUTER_RADIUS)
wait()

# ==================================================
# LEVEL 1 POINTS
# ==================================================

inner_midpoints = []

for p in outer:
    inner_midpoints.append(midpoint(A, p))

projected = []

for p in inner_midpoints:

    dx = p[0] - A[0]
    dy = p[1] - A[1]

    angle = math.atan2(dy, dx)

    x = A[0] + FIRST_OUTER_RADIUS * math.cos(angle)
    y = A[1] + FIRST_OUTER_RADIUS * math.sin(angle)

    projected.append((x, y))

for p in projected:
    add_point(p)

wait()

# ==================================================
# ALL 9 POINTS
# ==================================================

all_points = [A]
all_points.extend(projected)
all_points.extend(outer)

# ==================================================
# LEVEL 1 CONNECTIONS
# ==================================================

all_pairs = list(itertools.combinations(all_points, 2))

for p1, p2 in all_pairs:

    c, r = circle_from_points(p1, p2)
    add_circle(c, r)

    pygame.event.pump()

    time.sleep(0.08)

# ==================================================
# FINAL ENCLOSING CIRCLE
# ==================================================

max_extent = 0

for center, radius in drawn_circles:

    extent = distance(A, center) + radius

    if extent > max_extent:
        max_extent = extent

add_circle(A, max_extent)

# ==================================================
# LOOP
# ==================================================

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

pygame.quit()