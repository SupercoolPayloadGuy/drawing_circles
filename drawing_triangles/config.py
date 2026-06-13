"""
config.py — shared configuration dataclass.
"""

from dataclasses import dataclass


@dataclass
class Config:
    generations: int = 10
    side_length: float = 300.0
    speed: float = 1.0

    show_triangle_count: bool = True
    show_generation: bool = True
    show_total_generations: bool = False
    show_zoom: bool = True
    show_speed: bool = True
    dev_mode: bool = False
