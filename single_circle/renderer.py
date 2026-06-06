"""
renderer.py — drawing utilities for single_circle.
"""

import math
import pygame
import colorsys

from config import WIDTH, HEIGHT, RADIUS, BG, WHITE, LINE_WIDTH, DRAW_FLOWER


def rainbow(index, total):
    h = index / max(total, 1)
    r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


def create_mask(center):
    mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), center, RADIUS)
    return mask


def draw_arc(surface, center, radius, progress, color, width=LINE_WIDTH):
    cx, cy = center
    r = radius
    rect = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
    pygame.draw.arc(surface, color, rect, 0, math.radians(progress), width)


def draw_circle(surface, center, radius, color, width=LINE_WIDTH):
    pygame.draw.circle(surface, color,
                       (round(center[0]), round(center[1])),
                       round(radius), width)


def draw_dot(surface, center, radius=6, color=WHITE):
    pygame.draw.circle(surface, color,
                       (round(center[0]), round(center[1])),
                       radius)


def create_drawing_surface():
    return pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)


def render_frame(screen, drawing, mask, center, main_progress,
                 finished_circles, current_circle, circles,
                 current_progress, stage, points, visible_points):
    total = len(circles)

    drawing.fill((0, 0, 0, 0))

    for i, circle in enumerate(finished_circles):
        color = rainbow(i, total)
        draw_circle(drawing, circle["center"], circle["radius"], color)

    if stage == DRAW_FLOWER and current_circle < len(circles):
        circle = circles[current_circle]
        color = rainbow(current_circle, total)
        draw_arc(drawing, circle["center"], circle["radius"],
                 current_progress, color)

    drawing.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    screen.fill(BG)
    screen.blit(drawing, (0, 0))

    draw_arc(screen, center, RADIUS, main_progress, WHITE, 3)
    draw_dot(screen, center)

    for p in points[:visible_points]:
        draw_dot(screen, p)
