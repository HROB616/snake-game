# -*- coding: utf-8 -*-
import random
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    import curses
except ModuleNotFoundError:
    print("This game requires curses. On Windows, install it with: py -m pip install windows-curses")
    sys.exit(1)


USE_UNICODE = True
CELL_WIDTH = 2
BOARD_MARGIN = 2


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


@dataclass(frozen=True)
class StepResult:
    moved: bool = False
    ate_food: bool = False
    game_ended: bool = False
    new_head: Optional[Point] = None
    previous_head: Optional[Point] = None
    removed_tail: Optional[Point] = None
    old_food: Optional[Point] = None
    new_food: Optional[Point] = None
    level_changed: bool = False


UNICODE_THEME = {
    "h": "═",
    "v": "║",
    "tl": "╔",
    "tr": "╗",
    "bl": "╚",
    "br": "╝",
    "head": {
        Direction.UP: "▲",
        Direction.DOWN: "▼",
        # Some Windows curses terminals render the side triangles as broken glyphs.
        Direction.LEFT: "<",
        Direction.RIGHT: ">",
    },
    "body_h": "━━",
    "body_v": "┃ ",
    "corner_up_right": "╰━",
    "corner_up_left": "╯ ",
    "corner_down_right": "╭━",
    "corner_down_left": "╮ ",
    "tail_up": "╵ ",
    "tail_down": "╷ ",
    "tail_left": "╴━",
    "tail_right": "╶━",
    "food_a": "◆",
    "food_b": "◇",
    "empty": " ",
}

ASCII_THEME = {
    "h": "=",
    "v": "|",
    "tl": "+",
    "tr": "+",
    "bl": "+",
    "br": "+",
    "head": {
        Direction.UP: "^",
        Direction.DOWN: "v",
        Direction.LEFT: "<",
        Direction.RIGHT: ">",
    },
    "body_h": "--",
    "body_v": "| ",
    "corner_up_right": "+-",
    "corner_up_left": "+ ",
    "corner_down_right": "+-",
    "corner_down_left": "+ ",
    "tail_up": "| ",
    "tail_down": "| ",
    "tail_left": "--",
    "tail_right": "--",
    "food_a": "*",
    "food_b": "+",
    "empty": " ",
}


class SnakeGame:
    MIN_ROWS = 16
    MIN_COLS = 44
    BASE_DELAY = 115
    MIN_DELAY = 40

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.top = 3
        self.bottom = height - 3
        self.left = 0
        self.right = max(2, (width - BOARD_MARGIN * 2 - 1) // CELL_WIDTH)
        self.high_score = 0
        self.reset()

    def reset(self):
        start = Point(self.height // 2, self.right // 2)
        self.snake = [
            start,
            Point(start.row, start.col - 1),
            Point(start.row, start.col - 2),
        ]
        self.occupied = set(self.snake)
        self.direction = Direction.RIGHT
        self.pending_direction = Direction.RIGHT
        self.score = 0
        self.game_over = False
        self.started = False
        self.paused = False
        self.tick = 0
        self.last_message = "Ready"
        self.food = self.spawn_food()

    @property
    def playable_cells(self):
        return max(0, self.bottom - self.top - 1) * max(0, self.right - self.left - 1)

    def spawn_food(self):
        if len(self.occupied) >= self.playable_cells:
            return None

        for _ in range(80):
            point = Point(
                random.randint(self.top + 1, self.bottom - 1),
                random.randint(self.left + 1, self.right - 1),
            )
            if point not in self.occupied:
                return point

        for row in range(self.top + 1, self.bottom):
            for col in range(self.left + 1, self.right):
                point = Point(row, col)
                if point not in self.occupied:
                    return point
        return None

    def change_direction(self, direction):
        if not direction.is_opposite(self.direction):
            self.pending_direction = direction
            self.started = True
            self.paused = False

    def step(self):
        self.tick += 1
        if self.game_over or not self.started or self.paused:
            return StepResult()

        previous_level = self.level
        self.direction = self.pending_direction
        previous_head = self.snake[0]
        new_head = previous_head.moved(self.direction)
        is_growing = new_head == self.food

        if not is_growing:
            tail = self.snake[-1]
            self.occupied.remove(tail)
        else:
            tail = None

        if self.hit_wall(new_head) or new_head in self.occupied:
            if tail is not None:
                self.occupied.add(tail)
            self.game_over = True
            self.last_message = "Crash"
            return StepResult(game_ended=True, new_head=new_head, previous_head=previous_head)

        self.snake.insert(0, new_head)
        self.occupied.add(new_head)

        old_food = None
        new_food = self.food
        if is_growing:
            self.score += 1
            self.high_score = max(self.high_score, self.score)
            old_food = self.food
            new_food = self.spawn_food()
            self.food = new_food
            self.last_message = f"Level {self.level}" if self.level != previous_level else "Nice bite"
        else:
            self.snake.pop()
            self.last_message = "Hunting"

        return StepResult(
            moved=True,
            ate_food=is_growing,
            new_head=new_head,
            previous_head=previous_head,
            removed_tail=tail,
            old_food=old_food,
            new_food=new_food,
            level_changed=self.level != previous_level,
        )

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
        return max(self.MIN_DELAY, self.BASE_DELAY - (self.level - 1) * 8)

    def toggle_pause(self):
        if self.started and not self.game_over:
            self.paused = not self.paused
            self.last_message = "Paused" if self.paused else "Resume"


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

COLOR_SNAKE_A = 1
COLOR_SNAKE_B = 2
COLOR_FOOD = 3
COLOR_HEAD = 4
COLOR_BORDER = 5
COLOR_TEXT = 6
COLOR_DIM = 7
COLOR_WARNING = 8


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
        curses.init_pair(COLOR_SNAKE_A, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_SNAKE_B, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_FOOD, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_HEAD, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_BORDER, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TEXT, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_DIM, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(COLOR_WARNING, curses.COLOR_RED, curses.COLOR_BLACK)


def build_styles():
    def style(color, *attrs):
        value = curses.color_pair(color) if curses.has_colors() else 0
        for attr in attrs:
            value |= attr
        return value

    return {
        "snake_a": style(COLOR_SNAKE_A, curses.A_BOLD),
        "snake_b": style(COLOR_SNAKE_B),
        "food": style(COLOR_FOOD, curses.A_BOLD),
        "head": style(COLOR_HEAD, curses.A_BOLD),
        "border": style(COLOR_BORDER, curses.A_BOLD),
        "text": style(COLOR_TEXT),
        "text_bold": style(COLOR_TEXT, curses.A_BOLD),
        "dim": style(COLOR_DIM),
        "warning": style(COLOR_WARNING, curses.A_BOLD),
        "hud": style(COLOR_TEXT, curses.A_REVERSE | curses.A_BOLD),
    }


def centered_col(width, text):
    return max(0, (width - len(text)) // 2)


def direction_between(start, end):
    delta = (end.row - start.row, end.col - start.col)
    for direction in Direction:
        if direction.value == delta:
            return direction
    return Direction.RIGHT


class TerminalRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.theme = UNICODE_THEME if USE_UNICODE else ASCII_THEME
        self.styles = build_styles()
        self.needs_full_redraw = True
        self.previous_score = None
        self.previous_level = None
        self.previous_best = None
        self.previous_message = None

    def mark_dirty(self):
        self.needs_full_redraw = True

    def addstr(self, row, col, text, attr=0):
        if row < 0 or row >= curses.LINES or col >= curses.COLS:
            return
        max_width = curses.COLS - col - 1
        if max_width <= 0:
            return
        try:
            self.screen.addstr(row, col, text[:max_width], attr)
        except curses.error:
            pass

    def draw_cell(self, point, glyph, attr=0):
        self.addstr(point.row, self.screen_col(point.col), glyph[:CELL_WIDTH].ljust(CELL_WIDTH), attr)

    def clear_cell(self, point):
        self.draw_cell(point, self.theme["empty"] * CELL_WIDTH)

    def screen_col(self, logical_col):
        if logical_col <= 0:
            return BOARD_MARGIN
        return BOARD_MARGIN + logical_col * CELL_WIDTH - (CELL_WIDTH - 1)

    def draw(self, game, result):
        if self.needs_full_redraw or not game.started or game.paused or game.game_over:
            self.full_redraw(game)
            return

        self.draw_dirty(game, result)

    def full_redraw(self, game):
        self.screen.erase()
        self.draw_hud(game, force=True)
        self.draw_border(game)
        self.draw_food(game)
        self.draw_snake(game)

        if not game.started:
            self.draw_panel(
                game,
                "SNAKE",
                "Press an arrow key or WASD",
                "Collect food. Build speed.",
            )
        elif game.paused:
            self.draw_panel(game, "PAUSED", "Press P or move", "The board is waiting.")
        elif game.game_over:
            self.draw_panel(
                game,
                "GAME OVER",
                "Press R to restart or Q to quit",
                f"Final score {game.score}   Best {game.high_score}",
                warning=True,
            )

        self.screen.refresh()
        self.needs_full_redraw = False
        self.cache_status(game)

    def draw_dirty(self, game, result):
        if result.game_ended:
            self.needs_full_redraw = True
            self.full_redraw(game)
            return

        if result.removed_tail is not None:
            self.clear_cell(result.removed_tail)

        if result.previous_head is not None:
            self.redraw_snake_cell(game, result.previous_head)

        if result.removed_tail is not None and game.snake:
            self.redraw_snake_cell(game, game.snake[-1])

        if result.old_food is not None:
            self.clear_cell(result.old_food)

        if result.moved:
            self.draw_head(game)

        self.draw_food(game)

        if self.status_changed(game) or result.level_changed:
            self.draw_hud(game)

        self.screen.refresh()
        self.cache_status(game)

    def status_changed(self, game):
        return (
            self.previous_score != game.score
            or self.previous_level != game.level
            or self.previous_best != game.high_score
            or self.previous_message != game.last_message
        )

    def cache_status(self, game):
        self.previous_score = game.score
        self.previous_level = game.level
        self.previous_best = game.high_score
        self.previous_message = game.last_message

    def draw_hud(self, game, force=False):
        top_line = f"  TERMINAL SNAKE  "
        stats = f" Score {game.score:03d}  Best {game.high_score:03d}  Level {game.level:02d} "
        speed = f" Speed {max(1, 13 - game.delay // 10):02d} "
        message = f" {game.last_message} "
        help_text = " WASD/Arrows move   P pause   R restart   Q quit "

        if force:
            self.addstr(0, 0, " " * max(0, game.width - 1), self.styles["hud"])
            self.addstr(1, 0, " " * max(0, game.width - 1), self.styles["text"])
            self.addstr(game.height - 1, 0, " " * max(0, game.width - 1), self.styles["dim"])
        else:
            self.addstr(0, 0, " " * max(0, game.width - 1), self.styles["hud"])
            self.addstr(game.height - 1, 0, " " * max(0, game.width - 1), self.styles["dim"])

        self.addstr(0, 0, top_line, self.styles["hud"])
        self.addstr(0, max(0, game.width - len(stats) - len(speed) - 1), stats + speed, self.styles["hud"])
        self.addstr(1, 2, message, self.styles["text_bold"])
        self.addstr(game.height - 1, centered_col(game.width, help_text), help_text, self.styles["dim"])

    def draw_border(self, game):
        t = self.theme
        attr = self.styles["border"]
        for col in range(game.left + 1, game.right):
            screen_col = self.screen_col(col)
            self.addstr(game.top, screen_col, t["h"] * CELL_WIDTH, attr)
            self.addstr(game.bottom, screen_col, t["h"] * CELL_WIDTH, attr)
        for row in range(game.top + 1, game.bottom):
            self.addstr(row, self.screen_col(game.left), t["v"], attr)
            self.addstr(row, self.screen_col(game.right), t["v"], attr)

        self.addstr(game.top, self.screen_col(game.left), t["tl"], attr)
        self.addstr(game.top, self.screen_col(game.right), t["tr"], attr)
        self.addstr(game.bottom, self.screen_col(game.left), t["bl"], attr)
        self.addstr(game.bottom, self.screen_col(game.right), t["br"], attr)

    def draw_snake(self, game):
        for index in range(1, len(game.snake)):
            self.draw_body_segment(game, index)
        self.draw_head(game)

    def draw_head(self, game):
        glyph = self.theme["head"][game.direction]
        self.draw_cell(game.snake[0], glyph, self.styles["head"])

    def redraw_snake_cell(self, game, point):
        try:
            index = game.snake.index(point)
        except ValueError:
            return

        if index == 0:
            self.draw_head(game)
        else:
            self.draw_body_segment(game, index)

    def draw_body_segment(self, game, index):
        point = game.snake[index]
        glyph = self.body_glyph(game.snake, index)
        attr = self.styles["snake_a"] if index % 2 == 0 else self.styles["snake_b"]
        self.draw_cell(point, glyph, attr)

    def body_glyph(self, snake, index):
        if index == len(snake) - 1:
            direction = direction_between(snake[index], snake[index - 1])
            return self.theme[f"tail_{direction.name.lower()}"]

        prev_direction = direction_between(snake[index], snake[index - 1])
        next_direction = direction_between(snake[index], snake[index + 1])
        directions = {prev_direction, next_direction}

        if directions == {Direction.LEFT, Direction.RIGHT}:
            return self.theme["body_h"]
        if directions == {Direction.UP, Direction.DOWN}:
            return self.theme["body_v"]
        if directions == {Direction.UP, Direction.RIGHT}:
            return self.theme["corner_up_right"]
        if directions == {Direction.UP, Direction.LEFT}:
            return self.theme["corner_up_left"]
        if directions == {Direction.DOWN, Direction.RIGHT}:
            return self.theme["corner_down_right"]
        if directions == {Direction.DOWN, Direction.LEFT}:
            return self.theme["corner_down_left"]
        return self.theme["body_h"]

    def draw_food(self, game):
        if not game.food:
            return
        glyph = self.theme["food_a"] if game.tick % 2 == 0 else self.theme["food_b"]
        self.draw_cell(game.food, glyph, self.styles["food"])

    def draw_panel(self, game, title, line1, line2, warning=False):
        width = min(max(len(title), len(line1), len(line2)) + 8, game.width - 6)
        left = centered_col(game.width, " " * width)
        top = max(game.top + 2, game.height // 2 - 3)
        attr = self.styles["warning"] if warning else self.styles["text_bold"]
        dim = self.styles["dim"]

        self.addstr(top, left, self.theme["tl"] + self.theme["h"] * (width - 2) + self.theme["tr"], attr)
        for row in range(top + 1, top + 5):
            self.addstr(row, left, self.theme["v"] + " " * (width - 2) + self.theme["v"], attr)
        self.addstr(top + 5, left, self.theme["bl"] + self.theme["h"] * (width - 2) + self.theme["br"], attr)
        self.draw_panel_line(top + 1, left, width, title, attr)
        self.draw_panel_line(top + 3, left, width, line1, dim)
        self.draw_panel_line(top + 4, left, width, line2, dim)

    def draw_panel_line(self, row, left, width, text, attr):
        text = text[: max(0, width - 4)]
        col = left + max(2, (width - len(text)) // 2)
        self.addstr(row, col, text, attr)


def draw_too_small(screen):
    screen.erase()
    message = "Terminal too small. Resize to at least 44x16."
    try:
        screen.addstr(0, 0, message[: max(0, curses.COLS - 1)])
    except curses.error:
        pass
    screen.refresh()


def handle_key(key, game):
    if key in KEY_DIRECTIONS:
        game.change_direction(KEY_DIRECTIONS[key])
        return True, True
    if key in (ord("p"), ord("P")):
        game.toggle_pause()
        return True, True
    if key in (ord("r"), ord("R")):
        game.reset()
        return True, True
    if key in (ord("q"), ord("Q"), 27):
        return False, False
    return True, False


def main(screen):
    setup_curses(screen)
    game = SnakeGame(curses.LINES, curses.COLS)
    renderer = TerminalRenderer(screen)

    while True:
        height, width = screen.getmaxyx()
        if (height, width) != (game.height, game.width):
            high_score = game.high_score
            game = SnakeGame(height, width)
            game.high_score = high_score
            renderer.mark_dirty()

        if not game.is_large_enough():
            draw_too_small(screen)
            key = screen.getch()
            if key in (ord("q"), ord("Q"), 27):
                break
            continue

        key = screen.getch()
        running, force_redraw = handle_key(key, game)
        if not running:
            break
        if force_redraw:
            renderer.mark_dirty()

        screen.timeout(game.delay)
        result = game.step()
        renderer.draw(game, result)


if __name__ == "__main__":
    curses.wrapper(main)
