# Snake Game

A polished Snake game with both terminal and smooth Pygame versions.

## Controls

- Arrow keys or WASD to move and start
- P to pause or resume
- R to restart
- Q or Esc to quit

## Features

- Smooth Pygame version with interpolated 60 FPS movement
- Unicode arcade-style terminal playfield
- Connected snake body with straight, curved, and tail segments
- Horizontally scaled terminal playfield so vertical and sideways movement look the same length
- Start, pause, and game-over screens
- Score, high score, and level display
- Speed increases as your score climbs
- Dirty rendering during active terminal play for smoother terminal performance
- Faster collision and food placement using set-backed board occupancy

## How to run

Smooth graphical version:

```bash
py -m pip install pygame
py snake_pygame.py
```

Terminal version:

```bash
py snake.py
```

On Windows, install curses support first if needed:

```bash
py -m pip install windows-curses
```

Use a terminal at least 44 columns wide and 16 rows tall for the terminal version.
