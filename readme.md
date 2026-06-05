# Drawing Circles - Recursive Geometric Construction

A visualization of a recursive geometric algorithm that constructs circles based on points on a base circle.

## Project Overview

This project demonstrates a beautiful geometric pattern by recursively drawing circles. The algorithm starts with a base circle, places N points on its circumference, and then draws circles connecting these points in various combinations.

## How It Works

### Algorithm Steps

1. **Initial Circle**: Draw a base circle with radius R and center at origin
2. **Place Points**: Distribute N equally-spaced points on the circumference of the base circle
3. **Inner Circles**: Draw circles connecting the center point to each outer point (diameter = distance between center and point)
4. **Outer Circles**: Draw circles between every pair of points on the circumference (diameter = distance between the two points)

### Mathematical Foundation

- Points are placed at angles: `θ = 2π * i / N` (where i ranges from 0 to N-1)
- Circle center between two points: midpoint of the line connecting them
- Circle radius: half the distance between the two points
- Each new circle follows the same construction principles recursively

## Scripts

### `simple_circle.py`
**Graphics Library**: Turtle (Python's built-in graphics module)

Static visualization of the circle construction algorithm. This script:
- Draws the complete pattern without animation
- Uses turtle graphics for simplicity
- Fast rendering of all geometric elements
- Best for understanding the final result

**Key Settings**:
- `R = 150`: Radius of the base circle
- `N = 4`: Number of points on the base circle

**Run**: `python simple_circle.py`

### `double_circle.py`
**Graphics Library**: Pygame

Animated visualization of the circle construction algorithm. This script:
- Animates each step of the construction process
- Uses pygame for better performance and control
- Shows circles and points appearing progressively
- Helpful for understanding the construction sequence

**Key Settings**:
- `WIDTH = 1200, HEIGHT = 1200`: Canvas size
- `BASE_RADIUS = 140`: Radius of the base circle
- `DELAY = 1`: Seconds between animation steps

**Run**: `python double_circle.py` (requires pygame: `pip install pygame`)

## Visual Examples

With N=4 points:
- 1 base circle
- 4 circles connecting center to outer points
- 6 circles connecting pairs of outer points (C(4,2) = 6)
- **Total: 11 circles**

With N=6 points:
- 1 base circle
- 6 circles connecting center to outer points
- 15 circles connecting pairs of outer points (C(6,2) = 15)
- **Total: 22 circles**

## Dependencies

- **simple_circle.py**: None (uses built-in turtle module)
- **double_circle.py**: `pygame` (install via `pip install pygame`)

## TODO

- [ ] **Algorithm Enhancement**: Implement infinite recursive steps - extend the algorithm to recursively apply the same construction to newly created circles, creating a fractal-like pattern
- [ ] **Animation Improvements**: Enhance the pygame animation with:
  - Smooth transitions and easing effects
  - Color gradients based on recursion depth
  - Interactive controls (pause/play, speed adjustment)
  - Trail effects or fade-out for completed circles
  - Better visual hierarchy showing construction order

## Future Enhancements

- Support for different polygon shapes (triangles, pentagons, etc.)
- 3D visualization with matplotlib or VTK
- Export frames to video format
- Performance optimization for deep recursion
