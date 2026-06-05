"""
intro.py — animated pygame level-select screen.

Controls:
  UP / DOWN arrows or scroll  — step level by 1
  digit keys (0-9)            — type a number directly (multi-digit, 1s timeout)
  ENTER                       — confirm
  mouse click on ▲/▼ buttons  — step level
"""

import math
import time
import pygame


# ──────────────────────────────────────────────
# COLOURS
# ──────────────────────────────────────────────

BG       = (10, 10, 10)
DIM      = (30, 30, 30)
RING_COL = (55, 55, 55)
ACCENT   = (255, 220, 50)
WHITE    = (215, 215, 215)
GREY     = (95,  95,  95)
SOFT     = (140, 140, 140)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def ease_in_out(t):
    return t * t * (3 - 2 * t)


def lerp3(a, b, t):
    t = max(0.0, min(1.0, t))
    return (round(a[0]+(b[0]-a[0])*t),
            round(a[1]+(b[1]-a[1])*t),
            round(a[2]+(b[2]-a[2])*t))


def draw_ring_alpha(surface, cx, cy, radius, color, alpha=255, width=1):
    if radius < 1:
        return
    r = round(radius)
    s = r * 2 + width * 2
    tmp = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (r + width, r + width), r, width)
    surface.blit(tmp, (round(cx) - r - width, round(cy) - r - width))


def draw_dot_alpha(surface, cx, cy, color, alpha=255, r=4):
    s = r * 2 + 2
    tmp = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (r + 1, r + 1), r)
    surface.blit(tmp, (round(cx) - r - 1, round(cy) - r - 1))


# level → name   (no upper cap)
LEVEL_NAMES = {
    1: "base",
    2: "default",
    3: "expanded",
    4: "deep",
    5: "intense",
    6: "extreme",
    7: "void",
    8: "abyss",
    9: "beyond",
}

def level_name(n):
    return LEVEL_NAMES.get(n, f"depth {n}")


def _interp_stops(stops, t):
    """Interpolate RGB through a list of (position, (r,g,b)) stops."""
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        pos, col = stops[i]
        npos, ncol = stops[i + 1]
        if pos <= t <= npos:
            lt = (t - pos) / (npos - pos)
            return (round(col[0] + (ncol[0] - col[0]) * lt),
                    round(col[1] + (ncol[1] - col[1]) * lt),
                    round(col[2] + (ncol[2] - col[2]) * lt))
    return stops[-1][1]


_PREVIEW_STOPS = [
    (0.0,  (255, 130,  40)),
    (0.25, (70,  230,  90)),
    (0.5,  (40,  190, 255)),
    (0.75, (190, 70,  255)),
    (1.0,  (255, 60,  190)),
]

def preview_color(depth_01):
    return _interp_stops(_PREVIEW_STOPS, depth_01)


# ──────────────────────────────────────────────
# ANIMATED BACKGROUND
# ──────────────────────────────────────────────

class BackgroundAnim:
    BASE_R    = 90
    N_RINGS   = 5

    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.t0 = time.time()

    def draw(self, surface, chosen_level, point_count=4):
        t  = time.time() - self.t0
        cx, cy = self.cx, self.cy
        br = self.BASE_R

        # breathing
        breath = 1.0 + 0.07 * math.sin(t * 0.85)
        r = br * breath

        # points evenly spaced around the circle
        pts = [(cx + r * math.cos(-math.pi / 2 + 2 * math.pi * i / point_count),
                cy + r * math.sin(-math.pi / 2 + 2 * math.pi * i / point_count))
               for i in range(point_count)]

        # Show progressively more rings based on chosen level
        rings_to_show = min(chosen_level, self.N_RINGS)

        for ring_i in range(rings_to_show):
            scale  = 1.0 + ring_i * 0.55
            ring_r = r * scale
            dep    = ring_i / max(rings_to_show - 1, 1)
            col    = preview_color(dep)
            alpha  = max(20, 140 - ring_i * 22)
            draw_ring_alpha(surface, cx, cy, ring_r, col, alpha=alpha)

        # Base circle
        draw_ring_alpha(surface, cx, cy, r, (90, 90, 90), alpha=170)

        # Inner pair circles
        for px, py in pts:
            mr  = math.hypot(px-cx, py-cy) / 2
            mcx, mcy = (px+cx)/2, (py+cy)/2
            draw_ring_alpha(surface, mcx, mcy, mr, (65, 65, 65), alpha=80)

        # Neighbor pair circles
        for i in range(len(pts)):
            p1, p2 = pts[i], pts[(i+1)%len(pts)]
            mr  = math.hypot(p1[0]-p2[0], p1[1]-p2[1]) / 2
            mcx = (p1[0]+p2[0])/2
            mcy = (p1[1]+p2[1])/2
            draw_ring_alpha(surface, mcx, mcy, mr, (55, 55, 55), alpha=60)

        # Expanding wave
        wave_period = 3.5
        phase  = (t % wave_period) / wave_period
        wave_r = r * (1.0 + phase * 2.8)
        w_col  = preview_color(phase)
        draw_ring_alpha(surface, cx, cy, wave_r, w_col,
                        alpha=round((1.0-phase) * 55))

        # Points
        for px, py in pts:
            draw_dot_alpha(surface, px, py, ACCENT, alpha=170)
        draw_dot_alpha(surface, cx, cy, ACCENT, alpha=200)


# ──────────────────────────────────────────────
# LEVEL SELECTOR
# ──────────────────────────────────────────────

class LevelSelector:
    MIN_LEVEL = 1
    MAX_LEVEL = 99   # effectively unlimited

    MIN_POINTS = 2
    MAX_POINTS = 24

    # Digit-typing buffer
    _DIGIT_TIMEOUT = 1.2   # seconds before buffer resets

    def __init__(self, cx, cy, font_big, font_med, font_small):
        self.cx         = cx
        self.cy         = cy
        self.font_big   = font_big
        self.font_med   = font_med
        self.font_small = font_small
        self.level      = 2
        self.point_count = 4
        self._confirm_t = None

        self._digit_buf   = ""
        self._digit_ts    = 0.0

        self.hover_up  = False
        self.hover_dn  = False

        self.btn_up = pygame.Rect(cx + 60,  cy + 5,  44, 44)
        self.btn_dn = pygame.Rect(cx - 104, cy + 5,  44, 44)

    # ── event handling ─────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            # Digit direct input
            if pygame.K_0 <= event.key <= pygame.K_9:
                digit = str(event.key - pygame.K_0)
                now   = time.time()
                if now - self._digit_ts > self._DIGIT_TIMEOUT:
                    self._digit_buf = ""
                self._digit_buf += digit
                self._digit_ts   = now
                val = int(self._digit_buf)
                if val >= self.MIN_LEVEL:
                    self.level = min(self.MAX_LEVEL, val)
                return False

            if event.key in (pygame.K_UP, pygame.K_w):
                self._clear_buf()
                self.level = min(self.MAX_LEVEL, self.level + 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._clear_buf()
                self.level = max(self.MIN_LEVEL, self.level - 1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.point_count = min(self.MAX_POINTS, self.point_count + 1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.point_count = max(self.MIN_POINTS, self.point_count - 1)
            elif event.key == pygame.K_RETURN:
                self._confirm_t = time.time()
                return True
            elif event.key == pygame.K_BACKSPACE:
                if self._digit_buf:
                    self._digit_buf = self._digit_buf[:-1]
                    val = int(self._digit_buf) if self._digit_buf else self.MIN_LEVEL
                    self.level = max(self.MIN_LEVEL, val)

        if event.type == pygame.MOUSEWHEEL:
            self._clear_buf()
            self.level = max(self.MIN_LEVEL,
                             min(self.MAX_LEVEL, self.level + event.y))

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

    # ── draw ───────────────────────────────────

    def draw(self, surface):
        cx, cy = self.cx, self.cy

        # Title
        title = self.font_big.render("CIRCLE CONSTRUCTION", True, WHITE)
        surface.blit(title, (cx - title.get_width()//2, cy - 200))

        sub = self.font_small.render("choose your depth", True, GREY)
        surface.blit(sub, (cx - sub.get_width()//2, cy - 155))

        # ── level number with depth colour ──
        dep_t   = min(1.0, (self.level - 1) / 8.0)
        num_col = lerp3((255, 220, 50), (80, 200, 255), dep_t)

        if self._confirm_t is not None:
            flash = (time.time() - self._confirm_t) / 0.25
            if flash < 1.0:
                num_col = lerp3(num_col, (255, 255, 255), 1.0 - flash)
            else:
                self._confirm_t = None

        num_surf = self.font_big.render(str(self.level), True, num_col)
        surface.blit(num_surf, (cx - num_surf.get_width()//2, cy - 30))

        # Level name
        name_col = lerp3(SOFT, (100, 180, 240), dep_t)
        name_s   = self.font_med.render(level_name(self.level), True, name_col)
        surface.blit(name_s, (cx - name_s.get_width()//2, cy + 52))

        # ── arrow buttons ──
        up_col = ACCENT if self.hover_up else GREY
        dn_col = ACCENT if self.hover_dn else GREY
        a_up   = self.font_med.render("▶", True, up_col)
        a_dn   = self.font_med.render("◀", True, dn_col)
        surface.blit(a_up, (self.btn_up.x + (self.btn_up.w - a_up.get_width())//2,
                             self.btn_up.y  + (self.btn_up.h - a_up.get_height())//2))
        surface.blit(a_dn, (self.btn_dn.x + (self.btn_dn.w - a_dn.get_width())//2,
                             self.btn_dn.y  + (self.btn_dn.h - a_dn.get_height())//2))

        # ── point count ──
        pts_col = lerp3(SOFT, (100, 180, 240), dep_t)
        pts_s   = self.font_small.render(
            f"POINTS: {self.point_count}   [← →] or [A D]", True, pts_col)
        surface.blit(pts_s, (cx - pts_s.get_width() // 2, cy + 86))

        # ── type-a-number hint ──
        if self._digit_buf:
            buf_s = self.font_small.render(
                f"typing: {self._digit_buf}_", True, ACCENT)
        else:
            buf_s = self.font_small.render(
                "or type a number directly", True, GREY)
        surface.blit(buf_s, (cx - buf_s.get_width()//2, cy + 90))

        # ── progress bar showing depth ──
        bar_w   = 300
        bar_h   = 4
        bx      = cx - bar_w // 2
        by      = cy + 125
        filled  = round(bar_w * min(1.0, (self.level - 1) / 8.0))
        pygame.draw.rect(surface, DIM,  (bx, by, bar_w, bar_h), border_radius=2)
        if filled > 0:
            bar_col = lerp3((255, 220, 50), (80, 200, 255), dep_t)
            pygame.draw.rect(surface, bar_col, (bx, by, filled, bar_h),
                             border_radius=2)

        # ── enter hint ──
        hint = self.font_small.render("[ENTER] to start", True, GREY)
        surface.blit(hint, (cx - hint.get_width()//2, cy + 155))

        # ── dot progress (up to 9 dots, then show +N) ──
        MAX_DOTS = 9
        shown    = min(self.level, MAX_DOTS)
        dot_r    = 4
        spacing  = 20
        ox       = cx - (MAX_DOTS - 1) * spacing // 2
        oy       = cy + 195
        for i in range(MAX_DOTS):
            active = (i + 1) <= shown
            col    = lerp3((255, 220, 50), (80, 200, 255),
                           i / (MAX_DOTS - 1)) if active else DIM
            pygame.draw.circle(surface, col, (ox + i*spacing, oy), dot_r)
        if self.level > MAX_DOTS:
            extra_s = self.font_small.render(
                f"+{self.level - MAX_DOTS}", True, (80, 200, 255))
            surface.blit(extra_s, (ox + MAX_DOTS*spacing + 4, oy - 7))


# ──────────────────────────────────────────────
# RUN INTRO
# ──────────────────────────────────────────────

def run_intro(screen, clock):
    w, h   = screen.get_size()
    cx, cy = w // 2, h // 2

    pygame.display.set_caption("Circle Construction  —  Select Level")

    font_big   = pygame.font.SysFont("monospace", 54, bold=True)
    font_med   = pygame.font.SysFont("monospace", 24)
    font_small = pygame.font.SysFont("monospace", 18)

    bg_anim  = BackgroundAnim(cx, cy)
    selector = LevelSelector(cx, cy, font_big, font_med, font_small)

    CONFIRM_HOLD = 0.28
    confirmed_at = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if selector.handle_event(event):
                confirmed_at = time.time()

        # Flush digit buffer on timeout
        if (selector._digit_buf and
                time.time() - selector._digit_ts > selector._DIGIT_TIMEOUT):
            selector._digit_buf = ""

        screen.fill(BG)
        bg_anim.draw(screen, selector.level, selector.point_count)
        selector.draw(screen)
        pygame.display.flip()
        clock.tick(60)

        if confirmed_at is not None:
            if time.time() - confirmed_at >= CONFIRM_HOLD:
                return selector.level, selector.point_count