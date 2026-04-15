"""
Practice 10 - Task 2: Snake Game
Extended from the lecture example.
Extra features added:
  1. Border (wall) collision – snake dies if it leaves the playing area
  2. Food spawns only on empty cells (not on walls or the snake body)
  3. Levels – every 3 foods collected increases the level
  4. Speed increases with each level
  5. Score and level counters displayed on screen
  6. Full comments throughout the code
"""

import pygame
import random
import sys
from pygame.locals import *

# ── Constants ──────────────────────────────────────────────────────────────────
CELL        = 20          # size of each grid cell in pixels
COLS        = 30          # number of columns in the grid
ROWS        = 25          # number of rows  in the grid
SCREEN_W    = COLS * CELL # 600 px
SCREEN_H    = ROWS * CELL # 500 px

# How many food items collected per level
FOODS_PER_LEVEL = 3

# Starting FPS (speed) and how much it grows per level
BASE_FPS    = 8
FPS_INCREMENT = 2

# Colors
BLACK       = (0,   0,   0)
DKGREEN     = (0,   120, 0)
GREEN       = (0,   200, 50)
LTGREEN     = (150, 255, 150)
RED         = (220, 40,  40)
WHITE       = (255, 255, 255)
GRAY        = (60,  60,  60)
YELLOW      = (255, 220, 0)
ORANGE      = (255, 140, 0)
WALL_COLOR  = (80,  60,  40)

# Directions as (dx, dy) grid offsets
UP    = (0,  -1)
DOWN  = (0,   1)
LEFT  = (-1,  0)
RIGHT = (1,   0)

# ── Wall Map ──────────────────────────────────────────────────────────────────
def build_walls():
    """
    Returns a set of (col, row) tuples that represent wall cells.
    The border of the grid is always a wall.
    """
    walls = set()
    for c in range(COLS):
        walls.add((c, 0))           # top border
        walls.add((c, ROWS - 1))    # bottom border
    for r in range(ROWS):
        walls.add((0, r))           # left border
        walls.add((COLS - 1, r))    # right border
    return walls


# ── Food Spawning ─────────────────────────────────────────────────────────────
def spawn_food(snake_body, walls):
    """
    Returns a random (col, row) position that is not occupied by
    a wall cell or any segment of the snake body.
    """
    occupied = set(snake_body) | walls
    # Collect all free cells and pick one at random
    free_cells = [
        (c, r)
        for c in range(1, COLS - 1)
        for r in range(1, ROWS - 1)
        if (c, r) not in occupied
    ]
    if not free_cells:
        return None  # no free cells (extremely unlikely but safe)
    return random.choice(free_cells)


# ── Drawing Helpers ───────────────────────────────────────────────────────────
def cell_rect(col, row):
    """Convert grid coordinates to a pygame.Rect for drawing."""
    return pygame.Rect(col * CELL, row * CELL, CELL, CELL)


def draw_grid(surface):
    """Draw faint grid lines to visualise cells (optional, nice touch)."""
    for c in range(COLS):
        for r in range(ROWS):
            pygame.draw.rect(surface, GRAY, cell_rect(c, r), 1)


def draw_walls(surface, walls):
    """Draw every wall cell as a dark brick-like rectangle."""
    for (c, r) in walls:
        rect = cell_rect(c, r)
        pygame.draw.rect(surface, WALL_COLOR, rect)
        # Small inner highlight to give a brickwork look
        pygame.draw.rect(surface, (100, 80, 60), rect, 1)


def draw_snake(surface, snake_body):
    """
    Draw each snake segment.
    The head is drawn brighter/larger; the body is uniform green.
    """
    for i, (c, r) in enumerate(snake_body):
        rect = cell_rect(c, r)
        if i == 0:
            # Head – slightly lighter and with eyes
            pygame.draw.rect(surface, LTGREEN, rect, border_radius=4)
            # Eyes (two small dark dots)
            eye_r = CELL // 6
            pygame.draw.circle(surface, BLACK,
                               (c * CELL + CELL // 3,     r * CELL + CELL // 3), eye_r)
            pygame.draw.circle(surface, BLACK,
                               (c * CELL + 2 * CELL // 3, r * CELL + CELL // 3), eye_r)
        else:
            # Body segments alternate between two greens for a scaly look
            color = DKGREEN if i % 2 == 0 else GREEN
            pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=3)


def draw_food(surface, food_pos):
    """Draw the food as a red apple-like circle with a small green leaf."""
    if food_pos is None:
        return
    c, r = food_pos
    cx = c * CELL + CELL // 2
    cy = r * CELL + CELL // 2
    radius = CELL // 2 - 2
    pygame.draw.circle(surface, RED, (cx, cy), radius)
    pygame.draw.circle(surface, (255, 80, 80), (cx - 2, cy - 2), radius // 2)  # shine
    # Leaf
    pygame.draw.ellipse(surface, GREEN,
                        (cx, cy - radius - 4, 6, 6))


def draw_hud(surface, font, score, level, foods_to_next):
    """
    Display score, level, and foods needed to reach the next level.
    Rendered as a semi-transparent bar at the top of the screen.
    """
    bar = pygame.Surface((SCREEN_W, CELL), SRCALPHA)
    bar.fill((0, 0, 0, 140))
    surface.blit(bar, (0, 0))

    texts = [
        (f"Score: {score}",          WHITE,  10),
        (f"Level: {level}",          YELLOW, SCREEN_W // 2 - 40),
        (f"Next lvl: {foods_to_next}", ORANGE, SCREEN_W - 160),
    ]
    for txt, color, x in texts:
        surf = font.render(txt, True, color)
        surface.blit(surf, (x, 2))


# ── Message Screens ────────────────────────────────────────────────────────────
def show_message(surface, font_big, font_small, title, color, score, level):
    """
    Full-screen overlay with a title, score/level, and restart instructions.
    Waits for R (restart) or Q (quit). Returns True to restart.
    """
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    entries = [
        (font_big,   title,                 color,  SCREEN_H // 2 - 80),
        (font_small, f"Score : {score}",   WHITE,  SCREEN_H // 2 - 10),
        (font_small, f"Level  : {level}",  YELLOW, SCREEN_H // 2 + 25),
        (font_small, "R – Restart",         WHITE,  SCREEN_H // 2 + 70),
        (font_small, "Q – Quit",            WHITE,  SCREEN_H // 2 + 100),
    ]
    for fnt, txt, col, y in entries:
        s = fnt.render(txt, True, col)
        surface.blit(s, (SCREEN_W // 2 - s.get_width() // 2, y))

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN:
                if event.key == K_r:
                    return True
                if event.key == K_q:
                    return False


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Snake – Practice 10")

    font_big   = pygame.font.SysFont("Arial", 52, bold=True)
    font_small = pygame.font.SysFont("Arial", 20)

    walls = build_walls()  # fixed for the whole session

    # Outer loop allows restarting without reopening the window
    while True:
        # ── Initialise game state ──────────────────────────────────────────
        # Snake starts as a 3-segment body in the centre, moving right
        start_col = COLS // 2
        start_row = ROWS // 2
        snake_body = [
            (start_col,     start_row),  # head
            (start_col - 1, start_row),  # body
            (start_col - 2, start_row),  # tail
        ]
        direction     = RIGHT     # current movement direction
        next_direction = RIGHT    # queued direction (set by player input)

        food_pos = spawn_food(snake_body, walls)

        score         = 0
        level         = 1
        foods_eaten   = 0   # foods collected in the current level
        fps           = BASE_FPS

        clock   = pygame.time.Clock()
        running = True

        while running:
            clock.tick(fps)  # controls snake movement speed

            # ── Input ──────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    # Queue a direction change; disallow 180° reversal
                    if event.key == K_UP    and direction != DOWN:
                        next_direction = UP
                    elif event.key == K_DOWN  and direction != UP:
                        next_direction = DOWN
                    elif event.key == K_LEFT  and direction != RIGHT:
                        next_direction = LEFT
                    elif event.key == K_RIGHT and direction != LEFT:
                        next_direction = RIGHT

            # Apply the queued direction
            direction = next_direction

            # ── Move snake ─────────────────────────────────────────────────
            head_col, head_row = snake_body[0]
            dx, dy = direction
            new_head = (head_col + dx, head_row + dy)

            # ── Collision: border / wall ────────────────────────────────────
            if new_head in walls:
                # Snake hit a wall → game over
                running = False
                break

            # ── Collision: self ─────────────────────────────────────────────
            if new_head in snake_body[:-1]:
                # Snake hit its own body → game over
                running = False
                break

            # Move: insert new head
            snake_body.insert(0, new_head)

            # ── Collision: food ─────────────────────────────────────────────
            if new_head == food_pos:
                # Eat the food – grow (don't remove tail)
                score       += 10 * level   # more points at higher levels
                foods_eaten += 1

                # Check for level-up
                if foods_eaten >= FOODS_PER_LEVEL:
                    level        += 1
                    foods_eaten   = 0
                    fps           = BASE_FPS + (level - 1) * FPS_INCREMENT

                # Spawn new food
                food_pos = spawn_food(snake_body, walls)
            else:
                # Normal move – remove the tail
                snake_body.pop()

            # ── Drawing ────────────────────────────────────────────────────
            screen.fill(BLACK)
            draw_grid(screen)
            draw_walls(screen, walls)
            draw_snake(screen, snake_body)
            draw_food(screen, food_pos)
            draw_hud(screen, font_small, score, level,
                     FOODS_PER_LEVEL - foods_eaten)
            pygame.display.flip()

        # ── Game Over screen ───────────────────────────────────────────────
        if not show_message(screen, font_big, font_small,
                            "GAME OVER", RED, score, level):
            break  # player chose to quit

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
