# Drawing Circles - Recursive Geometric Construction

A visualization of recursive circle construction built from point pairs on a base circle. Available as a **pygame desktop app** or a **self-contained HTML page**.

## Quick Start

| Version | Run |
|---|---|
| **HTML** (no install) | Open `index.html` in any browser |
| **Python** | `python main.py` |

## HTML Version (`index.html`)

A fully self-contained browser rendering — zero dependencies, works offline.

**Controls:**
- **LEVEL** slider — construction depth (1–99)
- **POINTS** slider — number of base points (2–24)
- **START / STOP** — begin or cancel the animation
- **PAUSE / PLAY** — pause or resume mid-construction
- **RESTART** — reset after completion
- **scroll** — zoom in/out
- **drag** — pan the view
- **B** or theme button — toggle dark/light
- **P** — pause/resume
- **Enter** — start

## Python Version (`main.py`)

A pygame desktop app with an animated intro screen.

**Controls:**
- `ENTER` to start
- `UP` / `DOWN` / `W` / `S` — change level
- `LEFT` / `RIGHT` / `A` / `D` — change point count
- `B` — toggle dark/light theme
- `P` — pause/resume animation
- mouse wheel — zoom
- `python main.py -p 6` — set points via CLI flag

**Install:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Other Examples

- `examples/circle_algorithm.py` — pygame, console prompt for level
- `examples/simple_circle.py` — Python turtle (no deps)
- `examples/double_circle.py` — pygame variant

## Core Modules

- `geometry.py` — pure math (midpoint, distance, circle-from-pair, projections)
- `animation.py` — easing, timing, point fade-in, event handling
- `renderer.py` — camera, themes, HUD, UI buttons
- `intro.py` — level/points selector screen

## Status

- Animated circle construction in both pygame and HTML
- Variable base points (2–24)
- Recursive ring expansion for levels 1–99
- Auto-zoom, depth-based colour, easing, theme toggle
- Pause/play, restart, scroll zoom, drag pan
