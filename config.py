"""
config.py — shared configuration dataclass returned by the intro screen
            and consumed by construction + renderer.
"""
from dataclasses import dataclass, field


@dataclass
class Config:
    # Core
    level:       int   = 3
    point_count: int   = 4
    base_radius: int   = 140
    speed:       float = 1.0

    # HUD toggles
    show_circle_count: bool = True
    show_level:        bool = True
    show_total_levels: bool = False
    show_zoom:         bool = True
    show_speed:        bool = True