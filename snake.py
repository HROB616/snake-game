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
    BASE_DELAY = 120
    MIN_DELAY = 45

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.top = 2
        self.bottom = height - 2
        self.left = 1
        self.right = width - 2
        self.high_score = 0
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
        self.started = False
        self.paused = False
        self.tick = 0
        self.food = self.spawn_food()

    def spawn_food(self):
        blocked = set(self.snake)
        open_cells = [
            Point(row, col)
            for row in range(self.top + 1, self.bottom)
            for col in range(self.left + 1, self.right)
            if Point(row, col) not in blocked
        ]
        return random.choice(open_cells) if open_cells else None

    def change_direction(self, direction):
        if not direction.is_opposite(self.direction):
            self.pending_direction = direction
            self.started = True
            self.paused = False

    def step(self):
        self.tick += 1
        if self.game_over or not self.started or self.paused:
            return

        self.direction = self.pending_direction
        new_head = self.snake[0].moved(self.direction)
        is_growing = new_head == self.food
        collision_body = self.snake if is_growing else self.snake[:-1]

        if self.hit_wall(new_head) or new_head in collision_body:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if is_growing:
            self.score += 1
            self.high_score = max(self.high_score, self.score)
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

    @property
    def level(self):
        return 1 + self.score // 5

    @property
    def delay(self):
        return max(self.MIN_DELAY, self.BASE_DELAY - (self.level - 1) * 9)

    def toggle_pause(self):
        if self.started and not self.game_over:
            self.paused = not self.paused


KEY_DIRECTIONS = {
    curses.KEY_UP: Direction.UP,
    curses.KEY_DOWN: Direction.DOWN,
    curses.KEY_LEFT: Direction.LEFT,
    curses.KEY_RIGHT: Direction.RIGHT,
    ord("w"): Direction.UP,
    ord("W"): Direction.UP,
    ord("s"): Direction.DOWN,
    ord("S"): Direction.DOWN,
    ord("a"): Direction.LEFT,
    ord("A"): Direction.LEFT,
    ord("d"): Direction.RIGHT,
    ord("D"): Direction.RIGHT,
}

COLOR_SNAKE = 1
COLOR_FOOD = 2
COLOR_HEAD = 3
COLOR_BORDER = 4
COLOR_TEXT = 5
COLOR_DIM = 6
COLOR_WARNING = 7


def setup_curses(screen):
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    screen.nodelay(True)
    screen.keypad(True)

    if curses.has_colors():
        curses.start_color()
        try:
            curses.use_default_colors()
        except curses.error:
            pass
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)


def style(color, *attrs):
    value = curses.color_pair(color) if curses.has_colors() else 0
    for attr in attrs:
        value |= attr
    return value


def addstr_safe(screen, row, col, text, attr=0):
    if row < 0 or row >= curses.LINES or col >= curses.COLS:
        return
    max_width = curses.COLS - col - 1
    if max_width <= 0:
        return
    screen.addstr(row, col, text[:max_width], attr)


def addch_safe(screen, row, col, char, attr=0):
    if 0 <= row < curses.LINES and 0 <= col < curses.COLS - 1:
        screen.addch(row, col, char, attr)


def draw_border(screen, game):
    border_attr = style(COLOR_BORDER)
    for col in range(game.left, game.right + 1):
        top_char = "=" if col not in (game.left, game.right) else "+"
        addch_safe(screen, game.top, col, top_char, border_attr)
        addch_safe(screen, game.bottom, col, top_char, border_attr)

    for row in range(game.top, game.bottom + 1):
        side_char = "|" if row not in (game.top, game.bottom) else "+"
        addch_safe(screen, row, game.left, side_char, border_attr)
        addch_safe(screen, row, game.right, side_char, border_attr)


def draw_status(screen, game):
    title = "TERMINAL SNAKE"
    stats = f"Score {game.score:03d}  Best {game.high_score:03d}  Level {game.level}"
    controls = "WASD/Arrows move | P pause | R restart | Q quit"

    if game.width >= len(title) + len(stats) + 8:
        addstr_safe(screen, 0, 2, title, style(COLOR_HEAD, curses.A_BOLD))
        addstr_safe(
            screen,
            0,
            game.width - len(stats) - 2,
            stats,
            style(COLOR_TEXT, curses.A_BOLD),
        )
    else:
        addstr_safe(
            screen,
            0,
            centered_col(game.width, stats),
            stats,
            style(COLOR_TEXT, curses.A_BOLD),
        )

    addstr_safe(screen, 1, centered_col(game.width, controls), controls, style(COLOR_DIM))


def draw_game(screen, game):
    screen.clear()
    draw_status(screen, game)
    draw_border(screen, game)

    if game.food:
        food_char = "*" if game.tick % 2 == 0 else "+"
        addch_safe(
            screen,
            game.food.row,
            game.food.col,
            food_char,
            style(COLOR_FOOD, curses.A_BOLD),
        )

    head, *body = game.snake
    addch_safe(screen, head.row, head.col, "@", style(COLOR_HEAD, curses.A_BOLD))
    for point in body:
        addch_safe(screen, point.row, point.col, "o", style(COLOR_SNAKE))

    if not game.started:
        draw_center_panel(
            screen,
            game,
            "Press an arrow key or WASD",
            "Eat food, grow longer, and chase a new best score.",
        )
    elif game.paused:
        draw_center_panel(screen, game, "Paused", "Press P or move to resume.")

    if game.game_over:
        draw_center_panel(screen, game, "Game Over", "Press R to restart or Q to quit.", warning=True)

    screen.refresh()


def centered_col(width, text):
    return max(0, (width - len(text)) // 2)


def draw_center_panel(screen, game, headline, subline, warning=False):
    row = game.height // 2
    attr = style(COLOR_WARNING if warning else COLOR_TEXT, curses.A_BOLD)
    addstr_safe(screen, row - 1, centered_col(game.width, headline), headline, attr)
    addstr_safe(screen, row + 1, centered_col(game.width, subline), subline, style(COLOR_DIM))


def draw_too_small(screen):
    screen.clear()
    message = "Terminal too small. Resize to at least 30x12."
    addstr_safe(screen, 0, 0, message)
    screen.refresh()


def handle_key(key, game):
    if key in KEY_DIRECTIONS:
        game.change_direction(KEY_DIRECTIONS[key])
    elif key in (ord("p"), ord("P")):
        game.toggle_pause()
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
            high_score = game.high_score
            game = SnakeGame(height, width)
            game.high_score = high_score

        if not game.is_large_enough():
            draw_too_small(screen)
            key = screen.getch()
            if key in (ord("q"), ord("Q"), 27):
                break
            continue

        key = screen.getch()
        if not handle_key(key, game):
            break

        screen.timeout(game.delay)
        game.step()
        draw_game(screen, game)


if __name__ == "__main__":
    curses.wrapper(main)
