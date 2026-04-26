# -*- coding: utf-8 -*-
import random
import sys
import math
from collections import deque
from dataclasses import dataclass
from enum import Enum

try:
    import pygame
except ModuleNotFoundError:
    print("This version requires pygame. Install it with: py -m pip install pygame")
    sys.exit(1)


TILE = 24
COLS = 30
ROWS = 22
HUD_HEIGHT = 56
WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + HUD_HEIGHT
FPS = 60
BASE_STEP_MS = 150
MIN_STEP_MS = 70
TURN_BUFFER_LIMIT = 3

BG = (13, 18, 22)
BOARD_BG = (18, 27, 31)
GRID = (25, 40, 44)
SNAKE_HEAD = (216, 246, 95)
SNAKE_BODY = (79, 210, 130)
SNAKE_BODY_DARK = (39, 141, 91)
SNAKE_BELLY = (151, 239, 173)
FOOD = (239, 80, 80)
FOOD_GLOW = (255, 157, 118)
TEXT = (226, 235, 225)
MUTED = (126, 146, 143)
PANEL = (10, 14, 18)
WARNING = (255, 108, 108)


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def is_opposite(self, other):
        return self.value[0] + other.value[0] == 0 and self.value[1] + other.value[1] == 0


@dataclass(frozen=True)
class Cell:
    col: int
    row: int

    def moved(self, direction):
        d_col, d_row = direction.value
        return Cell(self.col + d_col, self.row + d_row)


class SnakeGame:
    def __init__(self):
        self.high_score = 0
        self.reset()

    def reset(self):
        start = Cell(COLS // 2, ROWS // 2)
        self.snake = [
            start,
            Cell(start.col - 1, start.row),
            Cell(start.col - 2, start.row),
        ]
        self.previous_snake = list(self.snake)
        self.occupied = set(self.snake)
        self.direction = Direction.RIGHT
        self.pending_direction = Direction.RIGHT
        self.direction_queue = deque()
        self.score = 0
        self.started = False
        self.paused = False
        self.game_over = False
        self.message = "Ready"
        self.food = self.spawn_food()
        self.step_started_at = pygame.time.get_ticks()

    @property
    def level(self):
        return 1 + (self.score / 3) * 0.5

    @property
    def step_ms(self):
        return max(MIN_STEP_MS, BASE_STEP_MS - (self.level - 1) * 9)

    def spawn_food(self):
        if len(self.occupied) >= COLS * ROWS:
            return None

        for _ in range(120):
            cell = Cell(random.randrange(COLS), random.randrange(ROWS))
            if cell not in self.occupied:
                return cell

        for row in range(ROWS):
            for col in range(COLS):
                cell = Cell(col, row)
                if cell not in self.occupied:
                    return cell
        return None

    def change_direction(self, direction):
        if self.game_over:
            return

        planned_direction = self.direction_queue[-1] if self.direction_queue else self.direction
        if direction == planned_direction:
            self.started = True
            self.paused = False
            return
        if direction.is_opposite(planned_direction):
            return

        if len(self.direction_queue) < TURN_BUFFER_LIMIT:
            self.direction_queue.append(direction)
            self.pending_direction = direction

        self.started = True
        self.paused = False

    def toggle_pause(self):
        if self.started and not self.game_over:
            self.paused = not self.paused
            self.message = "Paused" if self.paused else "Resume"

    def update(self, now):
        if self.game_over or self.paused or not self.started:
            self.step_started_at = now
            return

        if now - self.step_started_at >= self.step_ms:
            self.step_started_at += self.step_ms
            self.step()

    def animation_progress(self, now):
        if self.game_over or self.paused or not self.started:
            return 1.0
        return min(1.0, max(0.0, (now - self.step_started_at) / self.step_ms))

    def step(self):
        self.previous_snake = list(self.snake)
        if self.direction_queue:
            self.direction = self.direction_queue.popleft()
            self.pending_direction = self.direction

        new_head = self.snake[0].moved(self.direction)
        growing = new_head == self.food

        if not growing:
            old_tail = self.snake[-1]
            self.occupied.remove(old_tail)

        if self.hits_wall(new_head) or new_head in self.occupied:
            if not growing:
                self.occupied.add(old_tail)
            self.game_over = True
            self.message = "Crash"
            return

        self.snake.insert(0, new_head)
        self.occupied.add(new_head)

        if growing:
            self.score += 1
            self.high_score = max(self.high_score, self.score)
            self.food = self.spawn_food()
            self.message = f"Level {self.level}" if self.score % 5 == 0 else "Nice"
        else:
            self.snake.pop()
            self.message = "Hunting"

    def hits_wall(self, cell):
        return cell.col < 0 or cell.col >= COLS or cell.row < 0 or cell.row >= ROWS


def board_pos(cell):
    return pygame.Vector2(cell.col * TILE + TILE / 2, HUD_HEIGHT + cell.row * TILE + TILE / 2)


def lerp_cell(previous, current, progress):
    start = board_pos(previous)
    end = board_pos(current)
    return start.lerp(end, ease(progress))


def ease(t):
    return t * t * (3 - 2 * t)


def segment_positions(game, progress):
    positions = []
    for index, current in enumerate(game.snake):
        previous = game.previous_snake[index] if index < len(game.previous_snake) else current
        positions.append(lerp_cell(previous, current, progress))
    return positions


def draw_board(screen):
    screen.fill(BG)
    board_rect = pygame.Rect(0, HUD_HEIGHT, WIDTH, ROWS * TILE)
    pygame.draw.rect(screen, BOARD_BG, board_rect)

    for col in range(COLS + 1):
        x = col * TILE
        pygame.draw.line(screen, GRID, (x, HUD_HEIGHT), (x, HEIGHT), 1)
    for row in range(ROWS + 1):
        y = HUD_HEIGHT + row * TILE
        pygame.draw.line(screen, GRID, (0, y), (WIDTH, y), 1)


def draw_hud(screen, game, font, small_font):
    pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, HUD_HEIGHT))
    title = font.render("Smooth Snake", True, TEXT)
    stats = small_font.render(
        f"Score {game.score:03d}   Best {game.high_score:03d}   Level {game.level:02d}",
        True,
        TEXT,
    )
    controls = small_font.render("WASD/Arrows move   P pause   R restart   Q quit", True, MUTED)
    screen.blit(title, (18, 12))
    screen.blit(stats, (WIDTH - stats.get_width() - 18, 11))
    screen.blit(controls, (WIDTH - controls.get_width() - 18, 32))

    if game.message:
        message = small_font.render(game.message, True, SNAKE_HEAD)
        screen.blit(message, (18, 35))


def draw_food(screen, game, now):
    if not game.food:
        return
    center = board_pos(game.food)
    pulse = 1 + 0.12 * math.sin(now / 160)
    radius = int(TILE * 0.28 * pulse)
    pygame.draw.circle(screen, FOOD_GLOW, center, radius + 5)
    pygame.draw.circle(screen, FOOD, center, radius)


def draw_snake(screen, game, progress):
    positions = segment_positions(game, progress)
    if not positions:
        return

    body_radius = TILE * 0.36
    for index in range(len(positions) - 1, 0, -1):
        start = positions[index]
        end = positions[index - 1]
        color = SNAKE_BODY if index % 2 == 0 else SNAKE_BODY_DARK
        pygame.draw.line(screen, color, start, end, int(body_radius * 2))
        pygame.draw.circle(screen, color, start, int(body_radius))

    pygame.draw.circle(screen, SNAKE_BODY, positions[-1], int(body_radius * 0.72))
    pygame.draw.circle(screen, SNAKE_HEAD, positions[0], int(TILE * 0.43))
    pygame.draw.circle(screen, SNAKE_BELLY, positions[0], int(TILE * 0.25))
    draw_eyes(screen, positions[0], game.direction)


def draw_eyes(screen, center, direction):
    d_col, d_row = direction.value
    forward = pygame.Vector2(d_col, d_row)
    side = pygame.Vector2(-forward.y, forward.x)
    if forward.length_squared() == 0:
        forward = pygame.Vector2(1, 0)

    eye_forward = forward * (TILE * 0.17)
    eye_side = side * (TILE * 0.13)
    for offset in (-eye_side, eye_side):
        eye = center + eye_forward + offset
        pygame.draw.circle(screen, PANEL, eye, 3)


def draw_overlay(screen, title, subtitle, font, small_font, warning=False):
    panel = pygame.Rect(0, 0, 430, 140)
    panel.center = (WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(screen, (8, 12, 15), panel, border_radius=12)
    pygame.draw.rect(screen, WARNING if warning else SNAKE_BODY, panel, width=2, border_radius=12)

    title_surface = font.render(title, True, WARNING if warning else TEXT)
    subtitle_surface = small_font.render(subtitle, True, MUTED)
    screen.blit(title_surface, title_surface.get_rect(center=(panel.centerx, panel.y + 45)))
    screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(panel.centerx, panel.y + 88)))


def handle_key(event, game):
    if event.key in (pygame.K_UP, pygame.K_w):
        game.change_direction(Direction.UP)
    elif event.key in (pygame.K_DOWN, pygame.K_s):
        game.change_direction(Direction.DOWN)
    elif event.key in (pygame.K_LEFT, pygame.K_a):
        game.change_direction(Direction.LEFT)
    elif event.key in (pygame.K_RIGHT, pygame.K_d):
        game.change_direction(Direction.RIGHT)
    elif event.key == pygame.K_p:
        game.toggle_pause()
    elif event.key == pygame.K_r:
        game.reset()
    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
        return False
    return True


def main():
    pygame.init()
    pygame.display.set_caption("Smooth Snake")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Segoe UI", 28, bold=True)
    small_font = pygame.font.SysFont("Segoe UI", 17)
    game = SnakeGame()
    running = True

    while running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                running = handle_key(event, game)

        game.update(now)
        progress = game.animation_progress(now)

        draw_board(screen)
        draw_food(screen, game, now)
        draw_snake(screen, game, progress)
        draw_hud(screen, game, font, small_font)

        if not game.started:
            draw_overlay(screen, "Smooth Snake", "Press an arrow key or WASD", font, small_font)
        elif game.paused:
            draw_overlay(screen, "Paused", "Press P or move to resume", font, small_font)
        elif game.game_over:
            draw_overlay(screen, "Game Over", "Press R to restart or Q to quit", font, small_font, warning=True)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
