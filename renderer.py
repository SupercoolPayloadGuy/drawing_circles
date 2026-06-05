"""
renderer.py — pygame drawing, camera/zoom, depth-coloured circles,
              theme toggle, pause indicator, restart button, HUD.
"""

import math
import pygame

# ──────────────────────────────────────────────
# THEMES
# ──────────────────────────────────────────────

DARK_THEME = {
    "background": (10, 10, 10),
    "toggle_bg":  (25, 25, 25),
    "toggle_fg":  (180, 180, 180),
    "hud_fg":     (130, 130, 130),
    "label":      "DARK",
    # depth gradient: warm inner → cool outer  (RGB tuples)
    "depth_inner": (255, 200,  80),   # amber
    "depth_outer": ( 80, 160, 255),   # sky-blue
    "point_inner": (255, 220,  50),
    "point_outer": (100, 200, 255),
}

LIGHT_THEME = {
    "background": (245, 245, 240),
    "toggle_bg":  (220, 220, 210),
    "toggle_fg":  ( 50,  50,  50),
    "hud_fg":     (120, 120, 120),
    "label":      "LIGHT",
    "depth_inner": (180,  80,  20),   # burnt orange
    "depth_outer": ( 20,  80, 180),   # deep blue
    "point_inner": (200,  60,  10),
    "point_outer": ( 20, 100, 200),
}

# ──────────────────────────────────────────────
# DEPTH COLOUR  (shared helper, theme-aware)
# ──────────────────────────────────────────────

def depth_color(theme, depth_01, base_alpha=220):
    """
    Interpolate between inner and outer colour based on depth_01 in [0,1].
    Returns an (R,G,B) tuple with brightness scaled by base_alpha/255.
    """
    t  = max(0.0, min(1.0, depth_01))
    ci = theme["depth_inner"]
    co = theme["depth_outer"]
    r  = round(ci[0] + (co[0] - ci[0]) * t)
    g  = round(ci[1] + (co[1] - ci[1]) * t)
    b  = round(ci[2] + (co[2] - ci[2]) * t)
    s  = base_alpha / 255
    return (round(r * s), round(g * s), round(b * s))


def point_color(theme, depth_01, alpha=255):
    t  = max(0.0, min(1.0, depth_01))
    ci = theme["point_inner"]
    co = theme["point_outer"]
    r  = round(ci[0] + (co[0] - ci[0]) * t)
    g  = round(ci[1] + (co[1] - ci[1]) * t)
    b  = round(ci[2] + (co[2] - ci[2]) * t)
    s  = alpha / 255
    return (round(r * s), round(g * s), round(b * s))


# ──────────────────────────────────────────────
# CAMERA
# ──────────────────────────────────────────────

class Camera:
    ZOOM_MIN  = 0.01
    ZOOM_MAX  = 60.0
    ZOOM_STEP = 1.15

    def __init__(self, screen_w, screen_h, world_center):
        self.sw     = screen_w
        self.sh     = screen_h
        self.sc     = (screen_w / 2, screen_h / 2)
        self.origin = world_center
        self.zoom   = 1.0

    def w2s(self, pt):
        sx = (pt[0] - self.origin[0]) * self.zoom + self.sc[0]
        sy = (pt[1] - self.origin[1]) * self.zoom + self.sc[1]
        return (sx, sy)

    def r2s(self, r):
        return r * self.zoom

    def fit_radius(self, world_radius, margin=0.88):
        half   = min(self.sw, self.sh) / 2
        target = half * margin
        self.zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX,
                                           target / max(world_radius, 0.001)))

    def scroll(self, direction):
        if direction > 0:
            self.zoom = min(self.ZOOM_MAX, self.zoom * self.ZOOM_STEP)
        else:
            self.zoom = max(self.ZOOM_MIN, self.zoom / self.ZOOM_STEP)


# ──────────────────────────────────────────────
# RENDERER
# ──────────────────────────────────────────────

# Custom event fired when the restart button is clicked
RESTART_EVENT = pygame.USEREVENT + 1


class Renderer:

    _BTN_W   = 130
    _BTN_H   = 36
    _PAD     = 20

    def __init__(self, screen, camera, level):
        self.screen  = screen
        self.camera  = camera
        self.level   = level
        self.theme   = DARK_THEME
        self.font    = pygame.font.SysFont("monospace", 16)
        self.font_sm = pygame.font.SysFont("monospace", 13)

        sw, sh = screen.get_size()

        # Theme toggle — top right
        self.toggle_rect = pygame.Rect(
            sw - self._BTN_W - self._PAD, self._PAD,
            self._BTN_W, self._BTN_H)

        # Pause/play — top right, below theme toggle
        self.pause_rect = pygame.Rect(
            sw - self._BTN_W - self._PAD,
            self._PAD * 2 + self._BTN_H,
            self._BTN_W, self._BTN_H)

        # Restart — bottom centre, only shown when done
        self.restart_rect = pygame.Rect(
            sw // 2 - 90, sh - self._PAD - self._BTN_H,
            180, self._BTN_H)

        # --- mutable state set by animation module ---
        self.done_circles    = []   # [(world_center, world_radius, depth_01), …]
        self.done_points     = []   # [[wx, wy, alpha, depth_01], …]
        self.anim_circle     = None # (world_center, world_radius, depth_01)
        self.anim_t          = 0.0
        self.anim_start_ang  = -math.pi / 2

        self.paused          = False
        self.animation_done  = False

        # hover state
        self._hover_pause   = False
        self._hover_restart = False
        self._hover_toggle  = False

    # ── theme ──────────────────────────────────

    def toggle_theme(self):
        self.theme = LIGHT_THEME if self.theme is DARK_THEME else DARK_THEME

    # ── draw arc helper ────────────────────────

    def _draw_arc(self, world_center, world_radius, start_angle, sweep, color):
        sr = round(self.camera.r2s(world_radius))
        if sr < 1 or sweep <= 0:
            return
        scx, scy = self.camera.w2s(world_center)
        n_segs   = max(8, round(180 * sweep))
        end_a    = start_angle + 2 * math.pi * sweep
        prev     = None
        for i in range(n_segs + 1):
            a  = start_angle + (end_a - start_angle) * i / n_segs
            px = scx + sr * math.cos(a)
            py = scy + sr * math.sin(a)
            if prev:
                pygame.draw.line(self.screen, color, prev,
                                 (round(px), round(py)), 1)
            prev = (round(px), round(py))

    # ── button helper ──────────────────────────

    def _btn(self, rect, label, hover):
        th = self.theme
        bg = th["toggle_bg"]
        fg = th["toggle_fg"] if not hover else (255, 220, 50)
        pygame.draw.rect(self.screen, bg,  rect, border_radius=8)
        pygame.draw.rect(self.screen, fg,  rect, 1, border_radius=8)
        lbl = self.font.render(label, True, fg)
        self.screen.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2,
                               rect.y + (rect.h - lbl.get_height()) // 2))

    # ── UI overlays ────────────────────────────

    def _draw_buttons(self):
        th = self.theme
        # Theme toggle
        self._btn(self.toggle_rect,
                  f"[B] {th['label']}",
                  self._hover_toggle)
        # Pause / play  (only during animation)
        if not self.animation_done:
            icon = "▐▐ PAUSE" if not self.paused else "▶  PLAY"
            self._btn(self.pause_rect, f"[P] {icon}", self._hover_pause)
        # Restart  (only when done)
        if self.animation_done:
            self._btn(self.restart_rect, "↺  RESTART", self._hover_restart)

    def _draw_hud(self):
        fg = self.theme["hud_fg"]
        lines = [
            f"LEVEL {self.level}",
            f"zoom {self.camera.zoom:.2f}x",
            "[scroll] zoom",
        ]
        if self.paused:
            lines.append("— PAUSED —")
        for i, line in enumerate(lines):
            lbl = self.font_sm.render(line, True, fg)
            self.screen.blit(lbl, (self._PAD, self._PAD + i * 18))

    # ── update hover state  ────────────────────

    def update_hover(self, mouse_pos):
        self._hover_toggle  = self.toggle_rect.collidepoint(mouse_pos)
        self._hover_pause   = (not self.animation_done and
                               self.pause_rect.collidepoint(mouse_pos))
        self._hover_restart = (self.animation_done and
                               self.restart_rect.collidepoint(mouse_pos))

    # ── main draw ──────────────────────────────

    def redraw(self):
        screen = self.screen
        cam    = self.camera
        th     = self.theme
        screen.fill(th["background"])

        # Completed circles — coloured by depth
        max_depth = max((d for _, _, d in self.done_circles), default=1.0) or 1.0
        for wc, wr, dep in self.done_circles:
            sr = round(cam.r2s(wr))
            if sr < 1:
                continue
            sc  = cam.w2s(wc)
            # opacity also fades with depth: inner brighter, outer dimmer
            alpha = round(220 - dep * 100)
            col   = depth_color(th, dep / max_depth, base_alpha=max(60, alpha))
            pygame.draw.circle(screen, col,
                               (round(sc[0]), round(sc[1])), sr, 1)

        # Animating arc
        if self.anim_circle and self.anim_t > 0:
            wc, wr, dep = self.anim_circle
            col = depth_color(th, dep / max(max_depth, 1.0))
            self._draw_arc(wc, wr, self.anim_start_ang, self.anim_t, col)

        # Points — coloured by depth
        for entry in self.done_points:
            wx, wy, alpha, dep = entry[0], entry[1], entry[2], entry[3]
            sc  = cam.w2s((wx, wy))
            col = point_color(th, dep / max(max_depth, 1.0), alpha=alpha)
            pygame.draw.circle(screen, col,
                               (round(sc[0]), round(sc[1])), 5)

        self._draw_buttons()
        self._draw_hud()
        pygame.display.flip()