# Drawing Circles - Recursive Geometric Construction

A pygame visualization of recursive circle construction built from point pairs on a base circle.

## Project Overview

This repository contains a working animated construction of circle geometry. The main flow begins with a base circle, builds cardinal and pairwise circles, and expands outward through successive levels while keeping the drawing centered and visible.

## Current Behavior

- `main.py` is the primary entry point.
- An intro level-select screen appears first.
- The animation builds circles step-by-step.
- Points fade in, circles draw with easing, and the view auto-zooms.
- Theme toggling and scroll zoom are supported.

## What You Can Run

### `main.py`
The main application:
- Runs a pygame intro screen with level selection.
- Supports levels 1 through 6.
- Animates a base circle, inner circles, and additional rings.
- Automatically expands the construction ring-by-ring.

**Controls**:
- `ENTER` to start after choosing a level
- `UP` / `DOWN` / mouse wheel to change the level
- `B` or space to toggle dark/light theme
- mouse wheel to zoom in/out during the animation

**Run**: `python main.py`

### `examples/circle_algorithm.py`
A standalone pygame example that prompts for a level in the console and animates the construction.

### `examples/simple_circle.py`
A turtle-based static version in `examples/` for quick geometry exploration.

### `examples/double_circle.py`
A second pygame example in `examples/` showcasing the same circle construction logic with an alternate script layout.

## Core Modules

- `geometry.py` — pure math helpers: midpoint, distance, circle-from-pair, projections, deduplication, point pairs, and cardinal points.
- `animation.py` — animation timing, easing, circle drawing, point fade-in, and event pumping.
- `renderer.py` — pygame rendering, camera transforms, themes, HUD, and toggle UI.
- `intro.py` — animated intro screen and level selector.

## Installation

This project uses Python and relies on `pygame` for the main animation.

1. Create and activate a Python virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

3. Run the main app:

```bash
python main.py
```

### Optional

- `examples/simple_circle.py` uses Python's built-in `turtle` module and does not require extra packages.
- `examples/circle_algorithm.py` and `examples/double_circle.py` use `pygame`.

## Status

**Done:**
- Animated circle construction in pygame
- Intro level selection screen with mouse/keyboard controls
- Recursive ring expansion for levels 1+ up to 6
- Auto-zoom to keep new circles visible
- Theme toggle and zoom controls
- Point fade-in animation and easing curves

## TODO

- [ ] Add a pause/play control for the main animation
- [ ] Add a reset/restart button after the animation finishes
- [ ] Improve level visuals with depth-based color or opacity
- [ ] Add direct keyboard controls for level selection during intro
- [ ] Support more than 6 levels with smarter duration scaling
- [ ] Write a small `README` screenshot or sample output image

## Future Enhancements

- Add a fractal-style recursive construction of newly created circles
- Export animation frames or GIF/video output
- Add support for alternate base shapes (polygons, ellipses)
- Add a non-pygame web/HTML5 rendering version
