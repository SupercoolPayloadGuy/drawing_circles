"""
config.py — shared constants and Config dataclass for single_circle.
"""

from dataclasses import dataclass

WIDTH  = 1200
HEIGHT = 1200

N         = 100000
RADIUS    = 350

FPS = 60

CIRCLE_DRAW_SPEED = 240     # Degrees per second
POINT_APPEAR_DELAY = 0.02   # Seconds

BG    = (0, 0, 0)
WHITE = (255, 255, 255)

LINE_WIDTH = 2

COLOR_SCHEMES = ["rainbow", "warm", "cool", "mono", "sunset"]

# Stage constants
DRAW_MAIN_CIRCLE = 0
SHOW_POINTS      = 1
DRAW_FLOWER      = 2
DONE             = 3


@dataclass
class Config:
    speed: float = 1.0
    point_count: int = 24
    main_radius: int = 350
    color_scheme: str = "rainbow"
    show_circle_count: bool = True
    show_progress_bar: bool = True
