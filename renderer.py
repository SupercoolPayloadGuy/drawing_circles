"""
renderer.py — camera, depth-coloured drawing, theme toggle, HUD, UI buttons.
"""

import math
import pygame


# ──────────────────────────────────────────────
# THEMES
# ──────────────────────────────────────────────

def _interp_stops(stops, t):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        pos, col   = stops[i]
        npos, ncol = stops[i + 1]
        if pos <= t <= npos:
            lt = (t - pos) / (npos - pos)
            return tuple(round(col[j] + (ncol[j] - col[j]) * lt) for j in range(3))
    return stops[-1][1]


DARK_THEME = {
    "background":  (10, 10, 10),
    "toggle_bg":   (25, 25, 25),
    "toggle_fg":   (180, 180, 180),
    "hud_fg":      (130, 130, 130),
    "label":       "DARK",
    "circle_stops": [
        (0.0,  (255, 130,  40)),
        (0.25, ( 70, 230,  90)),
        (0.5,  ( 40, 190, 255)),
        (0.75, (190,  70, 255)),
        (1.0,  (255,  60, 190)),
    ],
    "point_stops": [
        (0.0,  (255, 220,  60)),
        (0.25, (140, 255, 110)),
        (0.5,  ( 90, 230, 255)),
        (0.75, (230, 120, 255)),
        (1.0,  (255, 110, 210)),
    ],
}

LIGHT_THEME = {
    "background":  (245, 240, 235),
    "toggle_bg":   (230, 225, 220),
    "toggle_fg":   ( 50,  50,  50),
    "hud_fg":      (100, 100, 100),
    "label":       "LIGHT",
    "circle_stops": [
        (0.0,  (180,  85,  25)),
        (0.25, ( 35, 145,  55)),
        (0.5,  ( 25, 105, 165)),
        (0.75, (105,  45, 165)),
        (1.0,  (165,  35, 105)),
    ],
    "point_stops": [
        (0.0,  (200, 150,  35)),
        (0.25, ( 95, 185,  65)),
        (0.5,  ( 55, 155, 195)),
        (0.75, (145,  75, 185)),
        (1.0,  (185,  65, 135)),
    ],
}


def depth_color(theme, depth_01, base_alpha=220):
    r, g, b = _interp_stops(theme["circle_stops"], depth_01)
    s = base_alpha / 255
    return (round(r * s), round(g * s), round(b * s))


def point_color(theme, depth_01, alpha=255):
    r, g, b = _interp_stops(theme["point_stops"], depth_01)
    s = alpha / 255
    return (round(r * s), round(g * s), round(b * s))


# ──────────────────────────────────────────────
# CAMERA
# ──────────────────────────────────────────────

class Camera:
    _ZOOM_STEP = 1.15

    def __init__(self, screen_w, screen_h, world_center):
        self.sc     = (screen_w / 2, screen_h / 2)
        self.origin = world_center
        self.zoom   = 1.0

    def w2s(self, pt):
        return (
            (pt[0] - self.origin[0]) * self.zoom + self.sc[0],
            (pt[1] - self.origin[1]) * self.zoom + self.sc[1],
        )

    def r2s(self, r):
        return r * self.zoom

    def fit_radius(self, world_radius, margin=0.88):
        half = min(self.sc[0], self.sc[1]) * 2 / 2
        self.zoom = half * margin / max(world_radius, 0.001)

    def scroll(self, direction):
        self.zoom *= self._ZOOM_STEP if direction > 0 else 1 / self._ZOOM_STEP


# ──────────────────────────────────────────────
# RENDERER
# ──────────────────────────────────────────────

RESTART_EVENT = pygame.USEREVENT + 1


class Renderer:
    _BTN_W = 130
    _BTN_H = 36
    _PAD   = 20

    def __init__(self, screen, camera, level):
        self.screen  = screen
        self.camera  = camera
        self.level   = level
        self.theme   = DARK_THEME
        self.font    = pygame.font.SysFont("monospace", 16)
        self.font_sm = pygame.font.SysFont("monospace", 13)

        sw, sh = screen.get_size()
        pad, bw, bh = self._PAD, self._BTN_W, self._BTN_H

        self.toggle_rect  = pygame.Rect(sw - bw - pad, pad, bw, bh)
        self.pause_rect   = pygame.Rect(sw - bw - pad, pad * 2 + bh, bw, bh)
        self.restart_rect = pygame.Rect(sw // 2 - 90, sh - pad - bh, 180, bh)
        self.menu_rect    = pygame.Rect(pad, pad, bw, bh)

        self.show_choices     = False
        self.choice_menu_rect = None
        self.choice_look_rect = None

        self.done_circles   = []   # [(world_center, world_radius, depth), …]
        self.done_points    = []   # [[wx, wy, alpha, depth], …]
        self.anim_circle    = None
        self.anim_t         = 0.0
        self.anim_start_ang = -math.pi / 2

        self.paused         = False
        self.animation_done = False
        self.speed_display  = 1.0   # updated each frame by AnimState

        self._hover_pause       = False
        self._hover_restart     = False
        self._hover_toggle      = False
        self._hover_menu        = False
        self._hover_choice_menu = False
        self._hover_choice_look = False

    def toggle_theme(self):
        self.theme = LIGHT_THEME if self.theme is DARK_THEME else DARK_THEME

    # ── drawing helpers ───────────────────────

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
            pt = (round(scx + sr * math.cos(a)), round(scy + sr * math.sin(a)))
            if prev:
                pygame.draw.line(self.screen, color, prev, pt, 1)
            prev = pt

    def _btn(self, rect, label, hover):
        th = self.theme
        fg = (255, 220, 50) if hover else th["toggle_fg"]
        pygame.draw.rect(self.screen, th["toggle_bg"], rect, border_radius=8)
        pygame.draw.rect(self.screen, fg, rect, 1, border_radius=8)
        lbl = self.font.render(label, True, fg)
        self.screen.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2,
                               rect.y + (rect.h - lbl.get_height()) // 2))

    # ── overlays ──────────────────────────────

    def _draw_buttons(self):
        self._btn(self.menu_rect, "← MENU", self._hover_menu)
        self._btn(self.toggle_rect, f"[B] {self.theme['label']}", self._hover_toggle)

        if not self.animation_done:
            icon = "▐▐ PAUSE" if not self.paused else "▶  PLAY"
            self._btn(self.pause_rect, f"[P] {icon}", self._hover_pause)

        if self.animation_done and not self.show_choices:
            self._btn(self.restart_rect, "↺  RESTART", self._hover_restart)

        if self.animation_done and self.show_choices:
            self._draw_completion_choices()

    def _draw_completion_choices(self):
        sw, sh = self.screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        lbl = self.font.render("CONSTRUCTION COMPLETE", True, (255, 220, 50))
        self.screen.blit(lbl, (sw // 2 - lbl.get_width() // 2, sh // 2 - 60))

        btn_w, btn_h, gap = 200, 46, 24
        cx, cy = sw // 2, sh // 2 + 6
        total  = btn_w * 2 + gap

        self.choice_menu_rect = pygame.Rect(cx - total // 2, cy - btn_h // 2, btn_w, btn_h)
        self.choice_look_rect = pygame.Rect(cx - total // 2 + btn_w + gap, cy - btn_h // 2, btn_w, btn_h)

        self._btn(self.choice_menu_rect, "← MAIN MENU", self._hover_choice_menu)
        self._btn(self.choice_look_rect, "LOOK AROUND",  self._hover_choice_look)

    def _draw_hud(self):
        fg    = self.theme["hud_fg"]
        count = len(self.done_circles) + (1 if self.anim_circle else 0)
        lines = [
            f"LEVEL {self.level}",
            f"circles  {count}",
            f"speed  {self.speed_display:.2f}x  [[ ]]",
            f"zoom  {self.camera.zoom:.2f}x  [scroll]",
        ]
        if self.paused:
            lines.append("— PAUSED —")
        for i, line in enumerate(lines):
            lbl = self.font_sm.render(line, True, fg)
            self.screen.blit(lbl, (self._PAD, self._PAD + self._BTN_H + 8 + i * 18))

    # ── hover ─────────────────────────────────

    def update_hover(self, mouse_pos):
        self._hover_toggle  = self.toggle_rect.collidepoint(mouse_pos)
        self._hover_pause   = not self.animation_done and self.pause_rect.collidepoint(mouse_pos)
        self._hover_restart = self.animation_done and not self.show_choices and \
                              self.restart_rect.collidepoint(mouse_pos)
        self._hover_menu    = self.menu_rect.collidepoint(mouse_pos)
        if self.show_choices:
            self._hover_choice_menu = bool(self.choice_menu_rect and
                                           self.choice_menu_rect.collidepoint(mouse_pos))
            self._hover_choice_look = bool(self.choice_look_rect and
                                           self.choice_look_rect.collidepoint(mouse_pos))
        else:
            self._hover_choice_menu = self._hover_choice_look = False

    # ── main redraw ───────────────────────────

    def redraw(self):
        cam = self.camera
        th  = self.theme
        self.screen.fill(th["background"])

        depths    = [d for _, _, d in self.done_circles]
        max_depth = max(depths, default=1.0) or 1.0

        for wc, wr, dep in self.done_circles:
            sr = round(cam.r2s(wr))
            if sr < 1:
                continue
            alpha = max(60, round(220 - dep * 100))
            col   = depth_color(th, dep / max_depth, base_alpha=alpha)
            sc    = cam.w2s(wc)
            pygame.draw.circle(self.screen, col, (round(sc[0]), round(sc[1])), sr, 1)

        if self.anim_circle and self.anim_t > 0:
            wc, wr, dep = self.anim_circle
            col = depth_color(th, dep / max_depth)
            self._draw_arc(wc, wr, self.anim_start_ang, self.anim_t, col)

        for wx, wy, alpha, dep in self.done_points:
            col = point_color(th, dep / max_depth, alpha=alpha)
            sc  = cam.w2s((wx, wy))
            pygame.draw.circle(self.screen, col, (round(sc[0]), round(sc[1])), 5)

        self._draw_buttons()
        self._draw_hud()
        pygame.display.flip()