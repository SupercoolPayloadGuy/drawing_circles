"""
app.py — application init, main loop, entry point coordination.
"""

import pygame

from cli          import parse_args
from intro        import run_intro
from construction import run as run_stage
from animation    import RestartSignal


def run():
    args = parse_args()

    pygame.init()
    screen = pygame.display.set_mode((1200, 1200))
    clock  = pygame.time.Clock()

    cfg = None
    while True:
        cfg = run_intro(screen, clock, prev_config=cfg)
        if args.points:
            cfg.point_count = args.points
        try:
            run_stage(cfg, screen, clock)
        except RestartSignal:
            continue
