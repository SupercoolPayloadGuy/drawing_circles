import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# -----------------------------
# Geometry helpers
# -----------------------------

def normalize(v):
    return v / np.linalg.norm(v)

def line_intersection(p1, d1, p2, d2):
    A = np.array([
        [d1[0], -d2[0]],
        [d1[1], -d2[1]]
    ])
    b = p2 - p1
    t, _ = np.linalg.solve(A, b)
    return p1 + t * d1

def angle_bisector(prev_v, vertex, next_v):
    u1 = normalize(prev_v - vertex)
    u2 = normalize(next_v - vertex)
    return normalize(u1 + u2)

def draw_infinite_line(ax, point, direction, length=10, **kwargs):
    p1 = point - direction * length
    p2 = point + direction * length
    return ax.plot(
        [p1[0], p2[0]],
        [p1[1], p2[1]],
        **kwargs
    )[0]

# -----------------------------
# Equilateral triangle
# -----------------------------

s = 4

A = np.array([0.0, 0.0])
B = np.array([s, 0.0])
C = np.array([s/2, np.sqrt(3)/2 * s])

# Internal bisectors
bA = angle_bisector(B, A, C)
bB = angle_bisector(C, B, A)
bC = angle_bisector(A, C, B)

# Perpendicular lines through vertices
pA = np.array([-bA[1], bA[0]])
pB = np.array([-bB[1], bB[0]])
pC = np.array([-bC[1], bC[0]])

# New triangle vertices
P = line_intersection(A, pA, B, pB)
Q = line_intersection(B, pB, C, pC)
R = line_intersection(C, pC, A, pA)

# -----------------------------
# Plot setup
# -----------------------------

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')

margin = 2
pts = np.vstack([A, B, C, P, Q, R])

ax.set_xlim(
    pts[:,0].min() - margin,
    pts[:,0].max() + margin
)

ax.set_ylim(
    pts[:,1].min() - margin,
    pts[:,1].max() + margin
)

ax.grid(True)

artists = []

# -----------------------------
# Animation
# -----------------------------

def update(frame):
    global artists

    for a in artists:
        try:
            a.remove()
        except:
            pass

    artists = []

    # Original triangle
    if frame >= 0:
        tri = np.array([A, B, C, A])
        artists += ax.plot(
            tri[:,0],
            tri[:,1],
            linewidth=2
        )

    # Bisector A
    if frame >= 20:
        artists.append(
            draw_infinite_line(
                ax, A, bA,
                linestyle='--'
            )
        )

    # Bisector B
    if frame >= 40:
        artists.append(
            draw_infinite_line(
                ax, B, bB,
                linestyle='--'
            )
        )

    # Bisector C
    if frame >= 60:
        artists.append(
            draw_infinite_line(
                ax, C, bC,
                linestyle='--'
            )
        )

    # Perpendicular through A
    if frame >= 80:
        artists.append(
            draw_infinite_line(
                ax, A, pA
            )
        )

    # Perpendicular through B
    if frame >= 100:
        artists.append(
            draw_infinite_line(
                ax, B, pB
            )
        )

    # Perpendicular through C
    if frame >= 120:
        artists.append(
            draw_infinite_line(
                ax, C, pC
            )
        )

    # New triangle
    if frame >= 140:
        new_tri = np.array([P, Q, R, P])
        artists += ax.plot(
            new_tri[:,0],
            new_tri[:,1],
            linewidth=3
        )

    return artists

ani = FuncAnimation(
    fig,
    update,
    frames=180,
    interval=40,
    blit=False
)

plt.show()