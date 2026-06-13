"""
construction.py — triangle generation using repeated angle-bisector construction.
"""

import time
import pygame

from geometry import equilateral_triangle, triangle_extent, distance
from renderer import Renderer, Camera
from animation import AnimState, animate_generation, pump, RestartSignal
from config import Config


WIDTH  = 1200
HEIGHT = 1200

_PAUSE = 0.2


def run(cfg: Config, screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    center  = (WIDTH / 2, HEIGHT / 2)
    camera  = Camera(WIDTH, HEIGHT, center)
    renderer = Renderer(screen, camera, cfg)
    renderer.animation_done = False
    renderer._total_generations = cfg.generations

    pygame.display.set_caption(
        f"Triangle Construction  •  {cfg.generations} generations  •  "
        f"[P] pause  [B] theme  [[ ]] speed  [scroll] zoom"
    )

    state = AnimState(renderer, clock)
    state.speed_mul = cfg.speed

    _build(state, renderer, center, cfg)
    _idle(state, renderer, clock)


def _build(state, renderer, center, cfg):
    side = cfg.side_length

    tri0 = equilateral_triangle(center, side)
    init_extent = max(distance(center, v) for v in tri0)
    renderer.camera.fit_radius(init_extent * 1.1, 0.88)
    renderer.redraw()

    cur_tri = tri0

    for gen in range(cfg.generations):
        cur_tri = animate_generation(state, cur_tri, gen)
        extent = triangle_extent(renderer.done_triangles, center)
        if extent > 0:
            renderer.camera.fit_radius(extent * 1.1, 0.88)

        _pause(state, _PAUSE)
        pump(state)

    renderer.pending_draw.append([cur_tri, cfg.generations, 0.0])
    all_tris = renderer.done_triangles + [(cur_tri, cfg.generations)]
    extent = triangle_extent(all_tris, center)
    if extent > 0:
        renderer.camera.fit_radius(extent * 1.1, 0.88)
    prev_ts = time.time()
    while renderer.pending_draw:
        now = time.time()
        dt = now - prev_ts
        prev_ts = now
        renderer.advance_pending(dt, state.speed_mul)
        renderer.redraw()
        if pump(state):
            raise _RestartSignal()
        state.clock.tick(60)


def _pause(state, seconds):
    elapsed = 0.0
    prev_ts = time.time()
    while elapsed < seconds:
        now = time.time()
        dt = now - prev_ts
        if not state.renderer.paused:
            elapsed += dt
            state.renderer.advance_pending(dt, state.speed_mul)
        prev_ts = now
        state.renderer.redraw()
        if pump(state):
            raise _RestartSignal()
        state.clock.tick(60)


def _idle(state, renderer, clock):
    renderer.animation_done = True
    renderer.show_choices = True
    prev_ts = time.time()
    while True:
        now = time.time()
        dt = now - prev_ts
        prev_ts = now
        renderer.advance_pending(dt, state.speed_mul)
        renderer.redraw()
        if pump(state):
            raise RestartSignal()
        clock.tick(30)
