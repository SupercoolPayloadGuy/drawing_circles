import pygame
import math
import itertools
import time

# ==================================================
# SETTINGS
# ==================================================

WIDTH  = 1200
HEIGHT = 1200

BASE_RADIUS = 140

DRAW_DURATION  = 0.28   # seconds per circle (uniform)
PAUSE_BETWEEN  = 0.08
STAGE_PAUSE    = 0.30
POINT_FADE_DUR = 0.40   # seconds for a point to fade in

# ==================================================
# THEME
# ==================================================

DARK_THEME = {
    "background": (10, 10, 10),
    "circle":     (200, 200, 200),
    "point":      (255, 220, 50),
    "toggle_bg":  (30, 30, 30),
    "toggle_fg":  (200, 200, 200),
    "label":      "DARK",
}

LIGHT_THEME = {
    "background": (245, 245, 242),
    "circle":     (40, 40, 40),
    "point":      (20, 20, 200),
    "toggle_bg":  (220, 220, 215),
    "toggle_fg":  (40, 40, 40),
    "label":      "LIGHT",
}

theme = DARK_THEME

# ==================================================
# PYGAME INIT
# ==================================================

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Circle Construction  •  B / Space = toggle theme")
font   = pygame.font.SysFont("monospace", 16)

CENTER = (WIDTH // 2, HEIGHT // 2)
clock  = pygame.time.Clock()

# ==================================================
# STATE
# ==================================================

done_circles = []   # list of (center, radius)
# points stored as (x, y, alpha 0-255)
done_points  = []

anim_circle     = None   # (center, radius)
anim_t          = 0.0
anim_start_ang  = -math.pi / 2   # angle on the circle where drawing begins

# ==================================================
# TOGGLE BUTTON
# ==================================================

TOGGLE_RECT = pygame.Rect(WIDTH - 140, 20, 120, 36)

def draw_toggle():
    bg = theme["toggle_bg"]
    fg = theme["toggle_fg"]
    pygame.draw.rect(screen, bg, TOGGLE_RECT, border_radius=8)
    pygame.draw.rect(screen, fg, TOGGLE_RECT, 1, border_radius=8)
    lbl = font.render(f"[B]  {theme['label']}", True, fg)
    screen.blit(lbl, (TOGGLE_RECT.x + 10, TOGGLE_RECT.y + 10))

# ==================================================
# DRAW HELPERS
# ==================================================

def lerp_color(c, alpha):
    """Return color c with brightness scaled by alpha (0-255)."""
    s = alpha / 255
    return (round(c[0]*s), round(c[1]*s), round(c[2]*s))

def draw_arc(center, radius, start_angle, sweep, color):
    """Draw a partial arc: sweep is 0..1 fraction of the full circle."""
    r = round(radius)
    if r < 1 or sweep <= 0:
        return
    n_segs = max(8, round(180 * sweep))
    end_a  = start_angle + 2 * math.pi * sweep
    prev   = None
    for i in range(n_segs + 1):
        a  = start_angle + (end_a - start_angle) * i / n_segs
        px = center[0] + r * math.cos(a)
        py = center[1] + r * math.sin(a)
        if prev:
            pygame.draw.line(screen, color, prev, (round(px), round(py)), 1)
        prev = (round(px), round(py))

def redraw():
    screen.fill(theme["background"])

    # Completed circles
    for center, radius in done_circles:
        if radius < 1:
            continue
        pygame.draw.circle(
            screen, theme["circle"],
            (round(center[0]), round(center[1])),
            round(radius), 1
        )

    # Animating circle (partial arc)
    if anim_circle and anim_t > 0:
        center, radius = anim_circle
        draw_arc(center, radius, anim_start_ang, anim_t, theme["circle"])

    # Points with alpha
    pc = theme["point"]
    for (px, py, alpha) in done_points:
        color = lerp_color(pc, alpha)
        pygame.draw.circle(screen, color, (round(px), round(py)), 5)

    draw_toggle()
    pygame.display.flip()

# ==================================================
# EVENT PUMP
# ==================================================

def pump():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_b, pygame.K_SPACE):
                toggle_theme()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if TOGGLE_RECT.collidepoint(event.pos):
                toggle_theme()

def toggle_theme():
    global theme
    theme = LIGHT_THEME if theme is DARK_THEME else DARK_THEME
    redraw()

# ==================================================
# GEOMETRY
# ==================================================

def midpoint(a, b):
    return ((a[0]+b[0])/2, (a[1]+b[1])/2)

def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def circle_from_points(a, b):
    return midpoint(a, b), distance(a, b) / 2

def angle_on_circle(center, point):
    """Angle (radians) from center to point."""
    return math.atan2(point[1] - center[1], point[0] - center[0])

# ==================================================
# ANIMATION PRIMITIVES
# ==================================================

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def animate_circle(center, radius, from_point=None, duration=DRAW_DURATION):
    """
    Draw circle arc starting at from_point (if given, else top of circle).
    from_point: one of the two defining points — arc starts there.
    """
    global anim_circle, anim_t, anim_start_ang

    if from_point is not None:
        anim_start_ang = angle_on_circle(center, from_point)
    else:
        anim_start_ang = -math.pi / 2

    anim_circle = (center, radius)
    start = time.time()
    while True:
        elapsed = time.time() - start
        raw = min(elapsed / duration, 1.0)
        anim_t = ease_in_out(raw)
        redraw()
        pump()
        clock.tick(60)
        if raw >= 1.0:
            break
    done_circles.append((center, radius))
    anim_circle = None
    anim_t = 0.0

def pause(seconds):
    end = time.time() + seconds
    while time.time() < end:
        redraw()
        pump()
        clock.tick(60)

def add_point_fade(pt, duration=POINT_FADE_DUR):
    """Add a point and animate it fading in."""
    done_points.append([pt[0], pt[1], 0])
    idx   = len(done_points) - 1
    start = time.time()
    while True:
        elapsed = time.time() - start
        raw   = min(elapsed / duration, 1.0)
        alpha = round(ease_in_out(raw) * 255)
        done_points[idx][2] = alpha
        redraw()
        pump()
        clock.tick(60)
        if raw >= 1.0:
            break

def add_points_fade(pts, stagger=0.06):
    """Fade in multiple points with a small stagger between them."""
    # Kick them all off nearly simultaneously with a small offset
    # We do them sequentially but keep fade short
    for pt in pts:
        done_points.append([pt[0], pt[1], 0])

    idxs  = list(range(len(done_points) - len(pts), len(done_points)))
    starts = [time.time() + i * stagger for i in range(len(pts))]
    dur    = POINT_FADE_DUR

    done_flags = [False] * len(pts)
    while not all(done_flags):
        now = time.time()
        for i, idx in enumerate(idxs):
            if done_flags[i]:
                continue
            elapsed = now - starts[i]
            if elapsed < 0:
                continue
            raw   = min(elapsed / dur, 1.0)
            done_points[idx][2] = round(ease_in_out(raw) * 255)
            if raw >= 1.0:
                done_flags[i] = True
        redraw()
        pump()
        clock.tick(60)

# ==================================================
# BASE GEOMETRY
# ==================================================

A = CENTER

angles = [-math.pi/2, 0, math.pi/2, math.pi]
outer  = []
for ang in angles:
    outer.append((A[0] + BASE_RADIUS * math.cos(ang),
                  A[1] + BASE_RADIUS * math.sin(ang)))

TOP, RIGHT, BOTTOM, LEFT = outer

# ==================================================
# CONSTRUCTION
# ==================================================

# ── Stage 1: original circle — start from TOP (first defined point)
redraw()
pause(0.3)
animate_circle(A, BASE_RADIUS, from_point=TOP)
pause(STAGE_PAUSE)

# ── Stage 2: mark points — fade in center first, then outer points
add_points_fade([A] + list(outer), stagger=0.07)
pause(STAGE_PAUSE)

# ── Stage 3: center→outer circles
#    Each circle defined by (A, p); start arc at A
for p in [TOP, BOTTOM]:
    c, r = circle_from_points(A, p)
    animate_circle(c, r, from_point=A)
    pause(PAUSE_BETWEEN)

pause(PAUSE_BETWEEN)

for p in [LEFT, RIGHT]:
    c, r = circle_from_points(A, p)
    animate_circle(c, r, from_point=A)
    pause(PAUSE_BETWEEN)

pause(STAGE_PAUSE)

# ── Stage 4: outer pair circles — start at first point of each pair
pairs = [
    (TOP, RIGHT), (BOTTOM, LEFT),
    (TOP, LEFT),  (BOTTOM, RIGHT),
    (TOP, BOTTOM),(LEFT, RIGHT),
]

for i in range(0, len(pairs), 2):
    for p1, p2 in pairs[i:i+2]:
        c, r = circle_from_points(p1, p2)
        animate_circle(c, r, from_point=p1)
        pause(PAUSE_BETWEEN)
    pause(PAUSE_BETWEEN)

pause(STAGE_PAUSE)

# ── Enclosing circle #1
max_extent = BASE_RADIUS
for center, radius in done_circles:
    extent = distance(A, center) + radius
    if extent > max_extent:
        max_extent = extent

FIRST_OUTER_RADIUS = max_extent
animate_circle(A, FIRST_OUTER_RADIUS, from_point=None)
pause(STAGE_PAUSE)

# ── Level-1 projected points
inner_midpoints = [midpoint(A, p) for p in outer]
projected = []
for p in inner_midpoints:
    dx, dy = p[0]-A[0], p[1]-A[1]
    angle = math.atan2(dy, dx)
    projected.append((
        A[0] + FIRST_OUTER_RADIUS * math.cos(angle),
        A[1] + FIRST_OUTER_RADIUS * math.sin(angle),
    ))

add_points_fade(projected, stagger=0.07)
pause(STAGE_PAUSE)

# ── All 9 points → all circle pairs — start at p1
all_points = [A] + projected + outer
all_pairs  = list(itertools.combinations(all_points, 2))

for p1, p2 in all_pairs:
    c, r = circle_from_points(p1, p2)
    animate_circle(c, r, from_point=p1)
    pump()

pause(STAGE_PAUSE)

# ── Final enclosing circle
max_extent2 = 0
for center, radius in done_circles:
    extent = distance(A, center) + radius
    if extent > max_extent2:
        max_extent2 = extent

animate_circle(A, max_extent2, from_point=None)

# ==================================================
# IDLE LOOP
# ==================================================

while True:
    redraw()
    pump()
    clock.tick(30)