# Snake Game (Terminal)

A polished terminal-based Snake game built in Python using curses.

## Controls

- Arrow keys or WASD to move and start
- P to pause or resume
- R to restart
- Q or Esc to quit

## Features

- Unicode arcade-style playfield
- Connected snake body with straight, curved, and tail segments
- Horizontally scaled playfield so vertical and sideways movement look the same length
- Start, pause, and game-over screens
- Score, high score, and level display
- Speed increases as your score climbs
- Dirty rendering during active play for smoother terminal performance
- Faster collision and food placement using set-backed board occupancy

## How to run

```bash
py snake.py
```

On Windows, install curses support first if needed:

```bash
py -m pip install windows-curses
```

Use a terminal at least 44 columns wide and 16 rows tall.
