"""
renderer.py — all pygame drawing, camera, theme, UI overlay.

The renderer owns a Camera that maps world coords → screen coords.
Everything outside this module should pass world-space values and
call redraw() to update the display.
"""

import math
import pygame

# ──────────────────────────────────────────────
# THEMES
# ──────────────────────────────────────────────

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

# ──────────────────────────────────────────────
# CAMERA
# ──────────────────────────────────────────────

class Camera:
    """
    Translates between world coords and screen coords.

    screen = (world - origin) * zoom + screen_center
    world  = (screen - screen_center) / zoom + origin
    """

    ZOOM_MIN = 0.02
    ZOOM_MAX = 40.0
    ZOOM_STEP = 1.15   # multiplier per scroll tick

    def __init__(self, screen_w, screen_h, world_center):
        self.sw = screen_w
        self.sh = screen_h
        self.sc = (screen_w / 2, screen_h / 2)   # screen centre (fixed)
        self.origin = world_center                 # world point at screen centre
        self.zoom   = 1.0

    def world_to_screen(self, wx, wy):
        sx = (wx - self.origin[0]) * self.zoom + self.sc[0]
        sy = (wy - self.origin[1]) * self.zoom + self.sc[1]
        return (sx, sy)

    def w2s(self, pt):
        return self.world_to_screen(pt[0], pt[1])

    def radius_to_screen(self, r):
        return r * self.zoom

    def fit_radius(self, world_radius, margin=0.88):
        """
        Set zoom so that world_radius fills `margin` fraction of the half-screen.
        """
        half = min(self.sw, self.sh) / 2
        target = half * margin
        self.zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, target / world_radius))

    def scroll(self, direction):
        """direction: +1 = zoom in, -1 = zoom out."""
        if direction > 0:
            self.zoom = min(self.ZOOM_MAX, self.zoom * self.ZOOM_STEP)
        else:
            self.zoom = max(self.ZOOM_MIN, self.zoom / self.ZOOM_STEP)


# ──────────────────────────────────────────────
# RENDERER
# ──────────────────────────────────────────────

class Renderer:

    TOGGLE_W  = 120
    TOGGLE_H  = 36
    TOGGLE_PAD = 20

    def __init__(self, screen, camera, level):
        self.screen  = screen
        self.camera  = camera
        self.level   = level
        self.theme   = DARK_THEME
        self.font    = pygame.font.SysFont("monospace", 16)

        sw = screen.get_width()
        self.toggle_rect = pygame.Rect(
            sw - self.TOGGLE_W - self.TOGGLE_PAD,
            self.TOGGLE_PAD,
            self.TOGGLE_W,
            self.TOGGLE_H,
        )

        # State injected by animation module
        self.done_circles  = []   # list of (world_center, world_radius)
        self.done_points   = []   # list of [wx, wy, alpha 0-255]
        self.anim_circle   = None # (world_center, world_radius)
        self.anim_t        = 0.0
        self.anim_start_ang = -math.pi / 2

    # ── theme ──────────────────────────────────

    def toggle_theme(self):
        self.theme = LIGHT_THEME if self.theme is DARK_THEME else DARK_THEME

    # ── helpers ────────────────────────────────

    @staticmethod
    def lerp_color(c, alpha):
        s = alpha / 255
        return (round(c[0] * s), round(c[1] * s), round(c[2] * s))

    def _draw_arc(self, world_center, world_radius, start_angle, sweep):
        sr = round(self.camera.radius_to_screen(world_radius))
        if sr < 1 or sweep <= 0:
            return
        scx, scy = self.camera.w2s(world_center)
        n_segs = max(8, round(180 * sweep))
        end_a  = start_angle + 2 * math.pi * sweep
        prev   = None
        color  = self.theme["circle"]
        for i in range(n_segs + 1):
            a  = start_angle + (end_a - start_angle) * i / n_segs
            px = scx + sr * math.cos(a)
            py = scy + sr * math.sin(a)
            if prev:
                pygame.draw.line(self.screen, color, prev,
                                 (round(px), round(py)), 1)
            prev = (round(px), round(py))

    # ── UI overlays ────────────────────────────

    def _draw_toggle(self):
        bg = self.theme["toggle_bg"]
        fg = self.theme["toggle_fg"]
        pygame.draw.rect(self.screen, bg, self.toggle_rect, border_radius=8)
        pygame.draw.rect(self.screen, fg, self.toggle_rect, 1, border_radius=8)
        lbl = self.font.render(f"[B]  {self.theme['label']}", True, fg)
        self.screen.blit(lbl, (self.toggle_rect.x + 10, self.toggle_rect.y + 10))

    def _draw_hud(self):
        fg = self.theme["toggle_fg"]
        lbl = self.font.render(f"LEVEL {self.level}", True, fg)
        self.screen.blit(lbl, (20, 20))
        zoom_lbl = self.font.render(
            f"zoom {self.camera.zoom:.2f}x  [scroll]", True, fg)
        self.screen.blit(zoom_lbl, (20, 44))

    # ── main draw call ─────────────────────────

    def redraw(self):
        self.screen.fill(self.theme["background"])

        # Completed circles
        cam = self.camera
        color = self.theme["circle"]
        for wc, wr in self.done_circles:
            sr = round(cam.radius_to_screen(wr))
            if sr < 1:
                continue
            sc = cam.w2s(wc)
            pygame.draw.circle(self.screen, color,
                               (round(sc[0]), round(sc[1])), sr, 1)

        # Animating arc
        if self.anim_circle and self.anim_t > 0:
            self._draw_arc(self.anim_circle[0], self.anim_circle[1],
                           self.anim_start_ang, self.anim_t)

        # Points
        pc = self.theme["point"]
        for entry in self.done_points:
            wx, wy, alpha = entry[0], entry[1], entry[2]
            sc = cam.w2s((wx, wy))
            pygame.draw.circle(self.screen, self.lerp_color(pc, alpha),
                               (round(sc[0]), round(sc[1])), 5)

        self._draw_toggle()
        self._draw_hud()
        pygame.display.flip()