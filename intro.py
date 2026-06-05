"""
intro.py — animated pygame level-select screen.

Shows a pulsing/growing circle construction preview as background,
with UP/DOWN arrows (or scroll) to pick a level, ENTER to confirm.
Returns the chosen integer level.
"""

import math
import time
import pygame


# ──────────────────────────────────────────────
# COLOURS
# ──────────────────────────────────────────────

BG       = (10, 10, 10)
DIM      = (35, 35, 35)
RING_COL = (60, 60, 60)
ACCENT   = (255, 220, 50)
WHITE    = (220, 220, 220)
GREY     = (100, 100, 100)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def ease_in_out(t):
    return t * t * (3 - 2 * t)


def draw_ring(surface, cx, cy, radius, color, width=1, alpha=255):
    if radius < 1:
        return
    tmp = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (round(cx), round(cy)), round(radius), width)
    surface.blit(tmp, (0, 0))


def draw_point(surface, cx, cy, color, alpha=255, r=4):
    tmp = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (round(cx), round(cy)), r)
    surface.blit(tmp, (0, 0))


# ──────────────────────────────────────────────
# ANIMATED BACKGROUND
# ──────────────────────────────────────────────

class BackgroundAnim:
    """
    Continuously draws a gentle breathing vesica / ring expansion
    to give the intro screen life.
    """

    BASE_R = 80

    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.t0 = time.time()

    def _elapsed(self):
        return time.time() - self.t0

    def draw(self, surface):
        t   = self._elapsed()
        cx, cy = self.cx, self.cy
        br  = self.BASE_R

        # Breathing: gentle scale 0.92 .. 1.08
        breath = 1.0 + 0.08 * math.sin(t * 0.9)
        r = br * breath

        # Outer slow-rotating rings
        for i in range(1, 5):
            ang   = t * 0.15 + i * math.pi / 4
            ring_r = r * (1 + 0.55 * i)
            alpha  = max(0, 80 - i * 15)
            draw_ring(surface, cx, cy, ring_r, RING_COL, alpha=alpha)

        # Cardinal point circles
        angles = [-math.pi/2, 0, math.pi/2, math.pi]
        pts = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]

        # Base circle
        draw_ring(surface, cx, cy, r, (80, 80, 80), alpha=160)

        # Inner pair circles
        for px, py in pts:
            mr = math.hypot(px - cx, py - cy) / 2
            mcx, mcy = (px + cx) / 2, (py + cy) / 2
            draw_ring(surface, mcx, mcy, mr, (60, 60, 60), alpha=90)

        # Diagonal pair circles
        for i in range(len(pts)):
            p1 = pts[i]
            p2 = pts[(i + 2) % len(pts)]
            mr = math.hypot(p1[0] - p2[0], p1[1] - p2[1]) / 2
            mcx = (p1[0] + p2[0]) / 2
            mcy = (p1[1] + p2[1]) / 2
            draw_ring(surface, mcx, mcy, mr, (55, 55, 55), alpha=70)

        # Expanding wave ring that fades out
        wave_period = 3.5
        wave_phase  = (t % wave_period) / wave_period
        wave_r      = r * (1.0 + wave_phase * 2.5)
        wave_alpha  = round((1.0 - wave_phase) * 60)
        draw_ring(surface, cx, cy, wave_r, ACCENT, alpha=wave_alpha)

        # Points
        for px, py in pts:
            draw_point(surface, px, py, ACCENT, alpha=180)
        draw_point(surface, cx, cy, ACCENT, alpha=200)


# ──────────────────────────────────────────────
# LEVEL SELECTOR
# ──────────────────────────────────────────────

class LevelSelector:

    MAX_LEVEL = 6
    MIN_LEVEL = 1

    def __init__(self, cx, cy, font_big, font_small):
        self.cx         = cx
        self.cy         = cy
        self.font_big   = font_big
        self.font_small = font_small
        self.level      = 2          # default
        self.hover_up   = False
        self.hover_dn   = False
        self._confirm_t = None       # timestamp of confirm press (for flash)

        # Arrow button areas
        self.btn_up = pygame.Rect(cx - 30, cy + 60, 60, 44)
        self.btn_dn = pygame.Rect(cx - 30, cy + 112, 60, 44)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.level = min(self.MAX_LEVEL, self.level + 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.level = max(self.MIN_LEVEL, self.level - 1)
            elif event.key == pygame.K_RETURN:
                self._confirm_t = time.time()
                return True   # confirmed

        if event.type == pygame.MOUSEWHEEL:
            self.level = max(self.MIN_LEVEL,
                             min(self.MAX_LEVEL, self.level + event.y))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_up.collidepoint(event.pos):
                self.level = min(self.MAX_LEVEL, self.level + 1)
            elif self.btn_dn.collidepoint(event.pos):
                self.level = max(self.MIN_LEVEL, self.level - 1)

        if event.type == pygame.MOUSEMOTION:
            self.hover_up = self.btn_up.collidepoint(event.pos)
            self.hover_dn = self.btn_dn.collidepoint(event.pos)

        return False

    def draw(self, surface):
        cx, cy = self.cx, self.cy

        # ── title ──
        title = self.font_big.render("CIRCLE CONSTRUCTION", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, cy - 180))

        sub = self.font_small.render(
            "choose your depth", True, GREY)
        surface.blit(sub, (cx - sub.get_width() // 2, cy - 140))

        # ── level number ──
        # Flash white on confirm
        num_col = WHITE
        if self._confirm_t is not None:
            flash = (time.time() - self._confirm_t) / 0.25
            if flash < 1.0:
                v = round(255 * (1 - flash))
                num_col = (255, 220, 50 + v // 3)
            else:
                self._confirm_t = None

        num_surf = self.font_big.render(str(self.level), True, num_col)
        surface.blit(num_surf, (cx - num_surf.get_width() // 2, cy + 10))

        # Label below number
        labels = {
            1: "base",
            2: "default",
            3: "expanded",
            4: "deep",
            5: "intense",
            6: "extreme",
        }
        lbl = self.font_small.render(
            labels.get(self.level, "level"), True, GREY)
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy + 72))

        # ── arrow buttons ──
        up_col   = ACCENT if self.hover_up else GREY
        dn_col   = ACCENT if self.hover_dn else GREY
        arrow_up = self.font_small.render("▲", True, up_col)
        arrow_dn = self.font_small.render("▼", True, dn_col)
        surface.blit(arrow_up, (cx - arrow_up.get_width() // 2,
                                self.btn_up.y + 8))
        surface.blit(arrow_dn, (cx - arrow_dn.get_width() // 2,
                                self.btn_dn.y + 8))

        # ── enter hint ──
        hint = self.font_small.render("[ENTER] to start", True, GREY)
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 180))

        # ── level dots ──
        total  = self.MAX_LEVEL
        dot_r  = 5
        spacing = 22
        ox = cx - (total - 1) * spacing // 2
        oy = cy + 230
        for i in range(1, total + 1):
            col   = ACCENT if i == self.level else DIM
            pygame.draw.circle(surface, col, (ox + (i-1)*spacing, oy), dot_r)


# ──────────────────────────────────────────────
# RUN INTRO
# ──────────────────────────────────────────────

def run_intro(screen, clock):
    """
    Display the animated intro / level-select screen.
    Blocks until the player confirms a level.
    Returns the chosen integer level.
    """
    w, h   = screen.get_size()
    cx, cy = w // 2, h // 2

    pygame.display.set_caption("Circle Construction  •  Select Level")

    font_big   = pygame.font.SysFont("monospace", 52, bold=True)
    font_small = pygame.font.SysFont("monospace", 20)

    bg_anim  = BackgroundAnim(cx, cy)
    selector = LevelSelector(cx, cy - 60, font_big, font_small)

    CONFIRM_HOLD = 0.30   # seconds to show the flash before returning

    confirmed_at = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if selector.handle_event(event):
                confirmed_at = time.time()

        screen.fill(BG)
        bg_anim.draw(screen)
        selector.draw(screen)
        pygame.display.flip()
        clock.tick(60)

        if confirmed_at is not None:
            if time.time() - confirmed_at >= CONFIRM_HOLD:
                return selector.level