import random
import sys
from dataclasses import dataclass
from enum import Enum

try:
    import curses
except ModuleNotFoundError:
    print("This game requires curses. On Windows, install it with: py -m pip install windows-curses")
    sys.exit(1)


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

    def is_opposite(self, other):
        return (
            self.value[0] + other.value[0] == 0
            and self.value[1] + other.value[1] == 0
        )


@dataclass(frozen=True)
class Point:
    row: int
    col: int

    def moved(self, direction):
        d_row, d_col = direction.value
        return Point(self.row + d_row, self.col + d_col)


class SnakeGame:
    MIN_ROWS = 12
    MIN_COLS = 30

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.top = 2
        self.bottom = height - 2
        self.left = 1
        self.right = width - 2
        self.reset()

    def reset(self):
        start = Point(self.height // 2, self.width // 2)
        self.snake = [
            start,
            Point(start.row, start.col - 1),
            Point(start.row, start.col - 2),
        ]
        self.direction = Direction.RIGHT
        self.pending_direction = Direction.RIGHT
        self.score = 0
        self.game_over = False
        self.food = self.spawn_food()

    def spawn_food(self):
        open_cells = [
            Point(row, col)
            for row in range(self.top + 1, self.bottom)
            for col in range(self.left + 1, self.right)
            if Point(row, col) not in self.snake
        ]
        return random.choice(open_cells) if open_cells else None

    def change_direction(self, direction):
        if not direction.is_opposite(self.direction):
            self.pending_direction = direction

    def step(self):
        if self.game_over:
            return

        self.direction = self.pending_direction
        new_head = self.snake[0].moved(self.direction)

        if self.hit_wall(new_head) or new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def hit_wall(self, point):
        return (
            point.row <= self.top
            or point.row >= self.bottom
            or point.col <= self.left
            or point.col >= self.right
        )

    def is_large_enough(self):
        return self.height >= self.MIN_ROWS and self.width >= self.MIN_COLS


KEY_DIRECTIONS = {
    curses.KEY_UP: Direction.UP,
    curses.KEY_DOWN: Direction.DOWN,
    curses.KEY_LEFT: Direction.LEFT,
    curses.KEY_RIGHT: Direction.RIGHT,
    ord("w"): Direction.UP,
    ord("s"): Direction.DOWN,
    ord("a"): Direction.LEFT,
    ord("d"): Direction.RIGHT,
}


def setup_curses(screen):
    curses.curs_set(0)
    screen.nodelay(True)
    screen.keypad(True)
    screen.timeout(100)

    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)


def draw_border(screen, game):
    for col in range(game.left, game.right + 1):
        screen.addch(game.top, col, "#")
        screen.addch(game.bottom, col, "#")

    for row in range(game.top, game.bottom + 1):
        screen.addch(row, game.left, "#")
        screen.addch(row, game.right, "#")


def draw_status(screen, game):
    controls = "Arrows/WASD move | R restart | Q quit"
    screen.addstr(0, 2, f"Score: {game.score}")
    screen.addstr(0, max(2, game.width - len(controls) - 2), controls)


def draw_game(screen, game):
    screen.clear()
    draw_status(screen, game)
    draw_border(screen, game)

    if game.food:
        screen.addch(game.food.row, game.food.col, "*", curses.color_pair(2))

    head, *body = game.snake
    screen.addch(head.row, head.col, "@", curses.color_pair(3))
    for point in body:
        screen.addch(point.row, point.col, "o", curses.color_pair(1))

    if game.game_over:
        message = "Game over - press R to restart or Q to quit"
        screen.addstr(game.height // 2, centered_col(game.width, message), message)

    screen.refresh()


def centered_col(width, text):
    return max(0, (width - len(text)) // 2)


def draw_too_small(screen):
    screen.clear()
    message = "Terminal too small. Resize to at least 30x12."
    screen.addstr(0, 0, message[: max(0, curses.COLS - 1)])
    screen.refresh()


def handle_key(key, game):
    if key in KEY_DIRECTIONS:
        game.change_direction(KEY_DIRECTIONS[key])
    elif key in (ord("r"), ord("R")):
        game.reset()
    elif key in (ord("q"), ord("Q"), 27):
        return False
    return True


def main(screen):
    setup_curses(screen)
    game = SnakeGame(curses.LINES, curses.COLS)

    while True:
        height, width = screen.getmaxyx()
        if (height, width) != (game.height, game.width):
            game = SnakeGame(height, width)

        if not game.is_large_enough():
            draw_too_small(screen)
            key = screen.getch()
            if key in (ord("q"), ord("Q"), 27):
                break
            continue

        key = screen.getch()
        if not handle_key(key, game):
            break

        game.step()
        draw_game(screen, game)


if __name__ == "__main__":
    curses.wrapper(main)
