import turtle
import math
from itertools import combinations

# -------------------------
# Settings
# -------------------------
R = 150
N = 4

# -------------------------
# Turtle setup
# -------------------------
screen = turtle.Screen()
screen.setup(1000, 1000)
screen.title("Circle Construction")

pen = turtle.Turtle()
pen.speed(1)
pen.hideturtle()

# -------------------------
# Helper
# -------------------------
def draw_circle(cx, cy, radius):
    pen.penup()
    pen.goto(cx, cy - radius)
    pen.setheading(0)
    pen.pendown()
    pen.circle(radius)

# -------------------------
# STEP 1
# Original circle
# -------------------------
draw_circle(0, 0, R)

# -------------------------
# STEP 2
# Points on circumference
# -------------------------
points = []

for i in range(N):
    angle = 2 * math.pi * i / N

    x = R * math.cos(angle)
    y = R * math.sin(angle)

    points.append((x, y))

    pen.penup()
    pen.goto(x, y)
    pen.dot(8)

# draw center point
pen.penup()
pen.goto(0, 0)
pen.dot(8)

# -------------------------
# STEP 3
# Circles between center
# and each outer point
# -------------------------
max_extent = R

for x, y in points:

    cx = x / 2
    cy = y / 2

    radius = math.dist((0, 0), (x, y)) / 2

    draw_circle(cx, cy, radius)

    extent = math.sqrt(cx**2 + cy**2) + radius
    max_extent = max(max_extent, extent)

# -------------------------
# STEP 4
# Circles between every
# pair of outer points
# -------------------------
for p1, p2 in combinations(points, 2):

    x1, y1 = p1
    x2, y2 = p2

    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    radius = math.dist(p1, p2) / 2

    draw_circle(cx, cy, radius)

    extent = math.sqrt(cx**2 + cy**2) + radius
    max_extent = max(max_extent, extent)

# -------------------------
# STEP 5
# Outer circle around
# everything
# -------------------------
draw_circle(0, 0, max_extent)

screen.mainloop()