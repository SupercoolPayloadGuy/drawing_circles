"""
intro.py — animated level-select screen.

Controls:
  UP/DOWN / W/S / scroll  — step level
  LEFT/RIGHT / A/D        — step point count
  digits (0–9)            — type level directly (1.2 s timeout)
  ENTER                   — confirm
  mouse ▲/▼ buttons       — step level
"""

import math
import time
import pygame


# ──────────────────────────────────────────────
# COLOURS
# ──────────────────────────────────────────────

BG     = (10,  10,  10)
DIM    = (30,  30,  30)
ACCENT = (255, 220,  50)
WHITE  = (215, 215, 215)
GREY   = ( 95,  95,  95)
SOFT   = (140, 140, 140)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _lerp3(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _interp_stops(stops, t):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        pos, col   = stops[i]
        npos, ncol = stops[i + 1]
        if pos <= t <= npos:
            lt = (t - pos) / (npos - pos)
            return tuple(round(col[j] + (ncol[j] - col[j]) * lt) for j in range(3))
    return stops[-1][1]


_PREVIEW_STOPS = [
    (0.0,  (255, 130,  40)),
    (0.25, ( 70, 230,  90)),
    (0.5,  ( 40, 190, 255)),
    (0.75, (190,  70, 255)),
    (1.0,  (255,  60, 190)),
]

def preview_color(t):
    return _interp_stops(_PREVIEW_STOPS, t)


def _draw_ring(surface, cx, cy, radius, color, alpha=255, width=1):
    if radius < 1:
        return
    r = round(radius)
    s = r * 2 + width * 2
    tmp = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (r + width, r + width), r, width)
    surface.blit(tmp, (round(cx) - r - width, round(cy) - r - width))


def _draw_dot(surface, cx, cy, color, alpha=255, r=4):
    s = r * 2 + 2
    tmp = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (r + 1, r + 1), r)
    surface.blit(tmp, (round(cx) - r - 1, round(cy) - r - 1))


LEVEL_NAMES = {
    1: "base", 2: "default", 3: "expanded", 4: "deep",
    5: "intense", 6: "extreme", 7: "void", 8: "abyss", 9: "beyond",
}

def level_name(n):
    return LEVEL_NAMES.get(n, f"depth {n}")


# ──────────────────────────────────────────────
# BACKGROUND ANIMATION
# ──────────────────────────────────────────────

class _BackgroundAnim:
    _BASE_R  = 90
    _N_RINGS = 5

    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.t0 = time.time()

    def draw(self, surface, chosen_level, point_count=4):
        t  = time.time() - self.t0
        cx, cy = self.cx, self.cy
        r  = self._BASE_R * (1.0 + 0.07 * math.sin(t * 0.85))

        pts = [
            (cx + r * math.cos(-math.pi / 2 + 2 * math.pi * i / point_count),
             cy + r * math.sin(-math.pi / 2 + 2 * math.pi * i / point_count))
            for i in range(point_count)
        ]

        rings = min(chosen_level, self._N_RINGS)
        for i in range(rings):
            dep   = i / max(rings - 1, 1)
            col   = preview_color(dep)
            alpha = max(20, 140 - i * 22)
            _draw_ring(surface, cx, cy, r * (1.0 + i * 0.55), col, alpha=alpha)

        _draw_ring(surface, cx, cy, r, (90, 90, 90), alpha=170)

        for px, py in pts:
            mr = math.hypot(px - cx, py - cy) / 2
            _draw_ring(surface, (px + cx) / 2, (py + cy) / 2, mr, (65, 65, 65), alpha=80)

        n = len(pts)
        for i in range(n):
            p1, p2 = pts[i], pts[(i + 1) % n]
            mr = math.hypot(p1[0] - p2[0], p1[1] - p2[1]) / 2
            _draw_ring(surface, (p1[0]+p2[0])/2, (p1[1]+p2[1])/2, mr, (55, 55, 55), alpha=60)

        phase  = (t % 3.5) / 3.5
        w_col  = preview_color(phase)
        _draw_ring(surface, cx, cy, r * (1.0 + phase * 2.8), w_col,
                   alpha=round((1.0 - phase) * 55))

        for px, py in pts:
            _draw_dot(surface, px, py, ACCENT, alpha=170)
        _draw_dot(surface, cx, cy, ACCENT, alpha=200)


# ──────────────────────────────────────────────
# LEVEL SELECTOR
# ──────────────────────────────────────────────

class _LevelSelector:
    MIN_LEVEL  = 1
    MAX_LEVEL  = 99
    MIN_POINTS = 2
    MAX_POINTS = 24
    _DIGIT_TIMEOUT = 1.2

    def __init__(self, cx, cy, font_big, font_med, font_small):
        self.cx, self.cy   = cx, cy
        self.font_big      = font_big
        self.font_med      = font_med
        self.font_small    = font_small
        self.level         = 2
        self.point_count   = 4
        self._confirm_t    = None
        self._digit_buf    = ""
        self._digit_ts     = 0.0
        self.hover_up      = False
        self.hover_dn      = False
        self.btn_up        = pygame.Rect(cx + 60,  cy + 5, 44, 44)
        self.btn_dn        = pygame.Rect(cx - 104, cy + 5, 44, 44)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            k = event.key
            if pygame.K_0 <= k <= pygame.K_9:
                now = time.time()
                if now - self._digit_ts > self._DIGIT_TIMEOUT:
                    self._digit_buf = ""
                self._digit_buf += str(k - pygame.K_0)
                self._digit_ts   = now
                val = int(self._digit_buf)
                if val >= self.MIN_LEVEL:
                    self.level = min(self.MAX_LEVEL, val)
                return False

            if k in (pygame.K_UP, pygame.K_w):
                self._clear_buf()
                self.level = min(self.MAX_LEVEL, self.level + 1)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self._clear_buf()
                self.level = max(self.MIN_LEVEL, self.level - 1)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.point_count = min(self.MAX_POINTS, self.point_count + 1)
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.point_count = max(self.MIN_POINTS, self.point_count - 1)
            elif k == pygame.K_RETURN:
                self._confirm_t = time.time()
                return True
            elif k == pygame.K_BACKSPACE and self._digit_buf:
                self._digit_buf = self._digit_buf[:-1]
                val = int(self._digit_buf) if self._digit_buf else self.MIN_LEVEL
                self.level = max(self.MIN_LEVEL, val)

        if event.type == pygame.MOUSEWHEEL:
            self._clear_buf()
            self.level = max(self.MIN_LEVEL, min(self.MAX_LEVEL, self.level + event.y))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_up.collidepoint(event.pos):
                self._clear_buf()
                self.level = min(self.MAX_LEVEL, self.level + 1)
            elif self.btn_dn.collidepoint(event.pos):
                self._clear_buf()
                self.level = max(self.MIN_LEVEL, self.level - 1)

        if event.type == pygame.MOUSEMOTION:
            self.hover_up = self.btn_up.collidepoint(event.pos)
            self.hover_dn = self.btn_dn.collidepoint(event.pos)

        return False

    def _clear_buf(self):
        self._digit_buf = ""

    def draw(self, surface):
        cx, cy = self.cx, self.cy
        dep_t  = min(1.0, (self.level - 1) / 8.0)

        # Title
        title = self.font_big.render("CIRCLE CONSTRUCTION", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, cy - 200))
        sub = self.font_small.render("choose your depth", True, GREY)
        surface.blit(sub, (cx - sub.get_width() // 2, cy - 155))

        # Level number
        num_col = _lerp3((255, 220, 50), (80, 200, 255), dep_t)
        if self._confirm_t is not None:
            flash = (time.time() - self._confirm_t) / 0.25
            if flash < 1.0:
                num_col = _lerp3(num_col, (255, 255, 255), 1.0 - flash)
            else:
                self._confirm_t = None
        num_s = self.font_big.render(str(self.level), True, num_col)
        surface.blit(num_s, (cx - num_s.get_width() // 2, cy - 30))

        # Level name
        name_col = _lerp3(SOFT, (100, 180, 240), dep_t)
        name_s   = self.font_med.render(level_name(self.level), True, name_col)
        surface.blit(name_s, (cx - name_s.get_width() // 2, cy + 52))

        # Arrow buttons
        for btn, lbl, hover in [
            (self.btn_up, "▶", self.hover_up),
            (self.btn_dn, "◀", self.hover_dn),
        ]:
            col = ACCENT if hover else GREY
            s   = self.font_med.render(lbl, True, col)
            surface.blit(s, (btn.x + (btn.w - s.get_width()) // 2,
                             btn.y + (btn.h - s.get_height()) // 2))

        # Point count
        pts_s = self.font_small.render(
            f"POINTS: {self.point_count}   [← →] or [A D]",
            True, _lerp3(SOFT, (100, 180, 240), dep_t))
        surface.blit(pts_s, (cx - pts_s.get_width() // 2, cy + 88))

        # Digit buffer hint
        if self._digit_buf:
            buf_s = self.font_small.render(f"typing: {self._digit_buf}_", True, ACCENT)
        else:
            buf_s = self.font_small.render("or type a number directly", True, GREY)
        surface.blit(buf_s, (cx - buf_s.get_width() // 2, cy + 112))

        # Progress bar
        bar_w, bar_h = 300, 4
        bx, by   = cx - bar_w // 2, cy + 138
        filled   = round(bar_w * min(1.0, (self.level - 1) / 8.0))
        pygame.draw.rect(surface, DIM, (bx, by, bar_w, bar_h), border_radius=2)
        if filled > 0:
            pygame.draw.rect(surface, _lerp3((255, 220, 50), (80, 200, 255), dep_t),
                             (bx, by, filled, bar_h), border_radius=2)

        # Enter hint
        hint = self.font_small.render("[ENTER] to start", True, GREY)
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 165))

        # Dot progress (up to 9, then +N)
        MAX_DOTS = 9
        shown    = min(self.level, MAX_DOTS)
        ox       = cx - (MAX_DOTS - 1) * 20 // 2
        oy       = cy + 200
        for i in range(MAX_DOTS):
            col = _lerp3((255, 220, 50), (80, 200, 255), i / (MAX_DOTS - 1)) \
                  if (i + 1) <= shown else DIM
            pygame.draw.circle(surface, col, (ox + i * 20, oy), 4)
        if self.level > MAX_DOTS:
            extra = self.font_small.render(f"+{self.level - MAX_DOTS}", True, (80, 200, 255))
            surface.blit(extra, (ox + MAX_DOTS * 20 + 4, oy - 7))


# ──────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ──────────────────────────────────────────────

def run_intro(screen, clock):
    """Show the animated intro screen; return (level, point_count) on confirmation."""
    w, h   = screen.get_size()
    cx, cy = w // 2, h // 2

    pygame.display.set_caption("Circle Construction  —  Select Level")

    font_big   = pygame.font.SysFont("monospace", 54, bold=True)
    font_med   = pygame.font.SysFont("monospace", 24)
    font_small = pygame.font.SysFont("monospace", 18)

    bg_anim  = _BackgroundAnim(cx, cy)
    selector = _LevelSelector(cx, cy, font_big, font_med, font_small)

    confirmed_at = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if selector.handle_event(event):
                confirmed_at = time.time()

        if selector._digit_buf and time.time() - selector._digit_ts > selector._DIGIT_TIMEOUT:
            selector._digit_buf = ""

        screen.fill(BG)
        bg_anim.draw(screen, selector.level, selector.point_count)
        selector.draw(screen)
        pygame.display.flip()
        clock.tick(60)

        if confirmed_at is not None and time.time() - confirmed_at >= 0.28:
            return selector.level, selector.point_count