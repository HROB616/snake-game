# Snake Game

A polished Snake game with both terminal and smooth Pygame versions.

# Development 
This project is being improved iteratively

## Controls

- 1/N for Normal difficulty or 2/E for Expert difficulty
- Arrow keys or WASD to move and start
- P to pause or resume
- R to restart
- Q or Esc to return to difficulty selection
- Q or Esc on the difficulty screen to quit

## Features

- Smooth Pygame version with interpolated 60 FPS movement
- Larger 45x33 graphical playfield
- Small particle burst when the snake eats food
- Unicode arcade-style terminal playfield
- Connected snake body with straight, curved, and tail segments
- Horizontally scaled terminal playfield so vertical and sideways movement look the same length
- Start, pause, and game-over screens
- Normal and Expert difficulty selection at the start
- Score, high score, and level display
- Speed increases as your score climbs, with Expert tripling the increase rate
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
