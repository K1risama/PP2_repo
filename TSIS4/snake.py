"""
TSIS 4: Snake Game — Database Integration & Advanced Gameplay
Extends Practice 10 / 11 snake.py with:
  3.1 PostgreSQL leaderboard (players + game_sessions tables via db.py)
  3.2 Poison food — shortens snake by 2; game over if length ≤ 1
  3.3 Three power-ups: Speed Boost, Slow Motion, Shield (timed)
  3.4 Obstacle blocks from Level 3 (safe spawn, collision = game over)
  3.5 settings.json — snake color, grid overlay, sound
  3.6 Four screens: Main Menu, Game Over, Leaderboard, Settings
"""

import pygame
import random
import sys
import json
import os
from pygame.locals import *
import db

# ── Constants ─────────────────────────────────────────────────────────────────
CELL     = 20
COLS     = 30
ROWS     = 26
SCREEN_W = COLS * CELL   # 600
SCREEN_H = ROWS * CELL   # 520

FOODS_PER_LEVEL = 3
BASE_FPS        = 8
FPS_INCREMENT   = 2
POWERUP_FIELD_TIMEOUT = 8000   # ms before power-up disappears from field
POWERUP_EFFECT_DURATION = 5000 # ms for speed/slow effects

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "snake_color": [0, 200, 50],
    "grid":        True,
    "sound":       False,
}

# Colors
BLACK   = (0,   0,   0);   WHITE   = (255, 255, 255)
DKGREEN = (0,   120, 0);   GREEN   = (0,   200, 50)
LTGREEN = (150, 255, 150); RED     = (220, 40,  40)
GRAY    = (60,  60,  60);  YELLOW  = (255, 220, 0)
ORANGE  = (255, 140, 0);   PURPLE  = (180, 0,   200)
CYAN    = (0,   200, 220); BROWN   = (139, 69,  19)
DGRAY   = (50,  50,  50);  LGRAY   = (180, 180, 180)
POISON_COLOR = (120, 0, 0)

UP    = (0, -1); DOWN  = (0, 1)
LEFT  = (-1, 0); RIGHT = (1, 0)


# ── Settings I/O ──────────────────────────────────────────────────────────────

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)
    with open(SETTINGS_FILE) as f:
        try:
            data = json.load(f)
            merged = dict(DEFAULT_SETTINGS); merged.update(data)
            return merged
        except Exception:
            return dict(DEFAULT_SETTINGS)


def save_settings_file(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


# ── Map helpers ───────────────────────────────────────────────────────────────

def build_border_walls():
    walls = set()
    for c in range(COLS):
        walls.add((c, 0)); walls.add((c, ROWS - 1))
    for r in range(ROWS):
        walls.add((0, r)); walls.add((COLS - 1, r))
    return walls


def build_level_obstacles(snake_body, border_walls, level):
    """Randomly place 3–8 obstacle blocks inside the arena (from level 3)."""
    if level < 3:
        return set()
    count     = min(3 + (level - 3) * 2, 12)
    forbidden = set(snake_body) | border_walls
    # Buffer around head
    hx, hy = snake_body[0]
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            forbidden.add((hx+dx, hy+dy))

    candidates = [
        (c, r) for c in range(1, COLS-1) for r in range(1, ROWS-1)
        if (c, r) not in forbidden
    ]
    random.shuffle(candidates)
    return set(candidates[:count])


def all_walls(border_walls, obstacles):
    return border_walls | obstacles


def free_cells(snake_body, walls):
    occupied = set(snake_body) | walls
    return [(c, r) for c in range(1, COLS-1) for r in range(1, ROWS-1)
            if (c, r) not in occupied]


def spawn_on_free(snake_body, walls):
    cells = free_cells(snake_body, walls)
    return random.choice(cells) if cells else None


# ── Drawing ───────────────────────────────────────────────────────────────────

def cell_rect(c, r):
    return pygame.Rect(c * CELL, r * CELL, CELL, CELL)


def draw_grid(surface):
    for c in range(COLS):
        for r in range(ROWS):
            pygame.draw.rect(surface, GRAY, cell_rect(c, r), 1)


def draw_walls(surface, border_walls, obstacles):
    for (c, r) in border_walls:
        pygame.draw.rect(surface, BROWN, cell_rect(c, r))
        pygame.draw.rect(surface, (100,80,60), cell_rect(c, r), 1)
    for (c, r) in obstacles:
        pygame.draw.rect(surface, (100, 60, 30), cell_rect(c, r))
        pygame.draw.rect(surface, (140, 100, 60), cell_rect(c, r), 1)


def draw_snake(surface, snake_body, snake_color):
    for i, (c, r) in enumerate(snake_body):
        rect = cell_rect(c, r)
        if i == 0:
            pygame.draw.rect(surface, LTGREEN, rect, border_radius=4)
            er = CELL // 6
            pygame.draw.circle(surface, BLACK, (c*CELL+CELL//3, r*CELL+CELL//3), er)
            pygame.draw.circle(surface, BLACK, (c*CELL+2*CELL//3, r*CELL+CELL//3), er)
        else:
            color = tuple(max(0,v-40) for v in snake_color) if i%2==0 else tuple(snake_color)
            pygame.draw.rect(surface, color, rect.inflate(-2,-2), border_radius=3)


def draw_item(surface, pos, color, label, font):
    if pos is None: return
    c, r = pos
    cx = c*CELL + CELL//2; cy = r*CELL + CELL//2
    radius = CELL//2 - 2
    pygame.draw.circle(surface, color, (cx, cy), radius)
    pygame.draw.circle(surface, WHITE, (cx-2, cy-3), radius//3)
    if label:
        t = font.render(label, True, WHITE)
        surface.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2))


def draw_hud(surface, font, score, level, foods_to_next, personal_best,
             active_pu, pu_end, now):
    bar = pygame.Surface((SCREEN_W, CELL+4), pygame.SRCALPHA)
    bar.fill((0,0,0,160))
    surface.blit(bar, (0, 0))
    surface.blit(font.render(f"Score:{score}", True, WHITE), (4, 2))
    surface.blit(font.render(f"Lv:{level}", True, YELLOW), (130, 2))
    surface.blit(font.render(f"Next:{foods_to_next}", True, ORANGE), (200, 2))
    surface.blit(font.render(f"PB:{personal_best}", True, LGRAY), (300, 2))
    if active_pu:
        remaining = max(0, (pu_end - now) // 1000)
        pu_colors = {"speed": GREEN, "slow": CYAN, "shield": PURPLE}
        col = pu_colors.get(active_pu, WHITE)
        surface.blit(font.render(f"[{active_pu.upper()} {remaining}s]", True, col),
                     (SCREEN_W - 120, 2))


# ── UI helpers ────────────────────────────────────────────────────────────────

def button(surface, font, rect, text, bg):
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)
    c = tuple(min(v+40,255) for v in bg) if hovered else bg
    pygame.draw.rect(surface, c, rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
    t = font.render(text, True, WHITE)
    surface.blit(t, t.get_rect(center=rect.center))
    return hovered and pygame.mouse.get_pressed()[0]


# ── Screens ───────────────────────────────────────────────────────────────────

def username_screen(screen, clock, font_big, font):
    name = ""
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN and name.strip(): return name.strip()
                elif event.key == K_BACKSPACE: name = name[:-1]
                elif event.unicode and len(name) < 16: name += event.unicode
        screen.fill(DGRAY)
        t = font_big.render("Enter Username", True, WHITE)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 60)))
        box = pygame.Rect(SCREEN_W//2-110, SCREEN_H//2-22, 220, 44)
        pygame.draw.rect(screen, (80,80,80), box, border_radius=6)
        pygame.draw.rect(screen, WHITE, box, 2, border_radius=6)
        nt = font.render(name + "|", True, WHITE)
        screen.blit(nt, nt.get_rect(center=box.center))
        hint = font.render("Enter to confirm", True, LGRAY)
        screen.blit(hint, hint.get_rect(center=(SCREEN_W//2, SCREEN_H//2+40)))
        pygame.display.flip()


def main_menu(screen, clock, font_big, font):
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
        screen.fill(DGRAY)
        t = font_big.render("SNAKE", True, GREEN)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2, 100)))
        cx = SCREEN_W // 2
        if button(screen, font, pygame.Rect(cx-90,200,180,44), "Play",        (40,120,40)):  return "play"
        if button(screen, font, pygame.Rect(cx-90,260,180,44), "Leaderboard", (40,40,140)):  return "leaderboard"
        if button(screen, font, pygame.Rect(cx-90,320,180,44), "Settings",    (100,80,30)):  return "settings"
        if button(screen, font, pygame.Rect(cx-90,380,180,44), "Quit",        (140,30,30)):
            pygame.quit(); sys.exit()
        pygame.display.flip()


def leaderboard_screen(screen, clock, font_big, font):
    try:
        rows = db.get_top10()
    except Exception as e:
        rows = []
        print(f"DB error: {e}")
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
        screen.fill(DGRAY)
        t = font_big.render("Leaderboard", True, YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2, 40)))
        hdr = font.render(f"{'#':<3} {'Name':<14} {'Score':<8} {'Lv':<4} {'Date'}", True, LGRAY)
        screen.blit(hdr, (20, 90))
        pygame.draw.line(screen, LGRAY, (20,110),(SCREEN_W-20,110),1)
        for i, (name, score, level, date) in enumerate(rows):
            row = font.render(f"{i+1:<3} {name:<14} {score:<8} {level:<4} {date}", True, WHITE)
            screen.blit(row, (20, 118 + i*28))
        if button(screen, font, pygame.Rect(SCREEN_W//2-60, SCREEN_H-60, 120,40), "Back", (80,80,80)):
            return
        pygame.display.flip()


def settings_screen(screen, clock, font_big, font, settings):
    snake_colors = [
        [0,200,50],[220,40,40],[30,100,220],[255,140,0],[180,0,200]
    ]
    ci = 0
    for i,c in enumerate(snake_colors):
        if c == settings.get("snake_color",[0,200,50]): ci=i; break

    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
        screen.fill(DGRAY)
        t = font_big.render("Settings", True, WHITE)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2,50)))
        cx = SCREEN_W // 2

        glbl = "Grid: ON" if settings["grid"] else "Grid: OFF"
        if button(screen, font, pygame.Rect(cx-90,140,180,40), glbl, (60,60,120)):
            settings["grid"] = not settings["grid"]

        slbl = "Sound: ON" if settings["sound"] else "Sound: OFF"
        if button(screen, font, pygame.Rect(cx-90,200,180,40), slbl, (60,60,120)):
            settings["sound"] = not settings["sound"]

        if button(screen, font, pygame.Rect(cx-90,260,180,40), "Color ▶", (60,60,120)):
            ci = (ci+1) % len(snake_colors)
            settings["snake_color"] = snake_colors[ci]
        pygame.draw.rect(screen, tuple(snake_colors[ci]),
                         pygame.Rect(cx+96,265,30,30), border_radius=4)

        if button(screen, font, pygame.Rect(cx-90,340,180,40), "Save & Back", (40,120,40)):
            save_settings_file(settings)
            return settings
        pygame.display.flip()


def game_over_screen(screen, clock, font_big, font, score, level, personal_best):
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
        screen.fill(DGRAY)
        for txt, color, y in [
            ("GAME OVER",           RED,    160),
            (f"Score: {score}",     WHITE,  225),
            (f"Level: {level}",     YELLOW, 260),
            (f"Best: {personal_best}", LGRAY, 295),
        ]:
            s = font_big.render(txt,True,color) if txt=="GAME OVER" else font.render(txt,True,color)
            screen.blit(s, s.get_rect(center=(SCREEN_W//2,y)))
        cx = SCREEN_W // 2
        if button(screen, font, pygame.Rect(cx-90,350,180,44), "Retry",     (40,120,40)): return "retry"
        if button(screen, font, pygame.Rect(cx-90,410,180,44), "Main Menu", (60,60,140)): return "menu"
        pygame.display.flip()


# ── Main game ─────────────────────────────────────────────────────────────────

def run_game(screen, clock, font, username, settings):
    snake_color  = tuple(settings.get("snake_color", [0,200,50]))
    show_grid    = settings.get("grid", True)
    border_walls = build_border_walls()

    # Snake initial state
    sc, sr = COLS//2, ROWS//2
    snake  = [(sc, sr), (sc-1, sr), (sc-2, sr)]
    direction = next_dir = RIGHT

    level       = 1
    foods_eaten = 0
    score       = 0
    fps         = BASE_FPS

    obstacles   = build_level_obstacles(snake, border_walls, level)
    walls       = all_walls(border_walls, obstacles)

    # Spawn items
    food_pos   = spawn_on_free(snake, walls)
    poison_pos = None
    powerup    = None   # (pos, kind, spawn_time)

    # Power-up state
    active_pu  = None
    pu_end     = 0

    last_poison_spawn  = pygame.time.get_ticks()
    last_powerup_spawn = pygame.time.get_ticks()
    POISON_INTERVAL    = 6000
    POWERUP_INTERVAL   = 7000

    try:
        personal_best = db.get_personal_best(username)
    except Exception:
        personal_best = 0

    font_hud = pygame.font.SysFont("Arial", 18, bold=True)
    font_item = pygame.font.SysFont("Arial", 9, bold=True)

    while True:
        clock.tick(fps)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_UP    and direction != DOWN:  next_dir = UP
                elif event.key == K_DOWN  and direction != UP:    next_dir = DOWN
                elif event.key == K_LEFT  and direction != RIGHT: next_dir = LEFT
                elif event.key == K_RIGHT and direction != LEFT:  next_dir = RIGHT
                elif event.key == K_ESCAPE:
                    return score, level

        direction = next_dir
        hx, hy = snake[0]
        dx, dy = direction
        new_head = (hx+dx, hy+dy)

        # Wall collision
        if new_head in walls:
            if active_pu == "shield":
                active_pu = None
                new_head = snake[0]  # stay in place
            else:
                return score, level

        # Self collision
        if new_head in snake[:-1]:
            if active_pu == "shield":
                active_pu = None
            else:
                return score, level

        snake.insert(0, new_head)

        # Food
        if new_head == food_pos:
            score       += 10 * level
            foods_eaten += 1
            food_pos     = spawn_on_free(snake, walls)
            if foods_eaten >= FOODS_PER_LEVEL:
                level       += 1
                foods_eaten  = 0
                fps          = BASE_FPS + (level-1) * FPS_INCREMENT
                obstacles    = build_level_obstacles(snake, border_walls, level)
                walls        = all_walls(border_walls, obstacles)
        else:
            snake.pop()

        # Poison food
        if new_head == poison_pos:
            snake = snake[:-2] if len(snake) > 3 else snake[:1]
            poison_pos = None
            if len(snake) <= 1:
                return score, level
            score = max(0, score - 5)

        # Power-up collection
        if powerup and new_head == powerup[0]:
            kind = powerup[1]
            powerup   = None
            active_pu = kind
            if kind == "speed":
                fps      = BASE_FPS + (level-1)*FPS_INCREMENT + 4
                pu_end   = now + POWERUP_EFFECT_DURATION
            elif kind == "slow":
                fps      = max(2, BASE_FPS + (level-1)*FPS_INCREMENT - 3)
                pu_end   = now + POWERUP_EFFECT_DURATION
            elif kind == "shield":
                pu_end   = now + 30000   # until triggered

        # Power-up expiry
        if active_pu in ("speed","slow") and now > pu_end:
            fps       = BASE_FPS + (level-1)*FPS_INCREMENT
            active_pu = None

        # Spawn poison
        if poison_pos is None and now - last_poison_spawn > POISON_INTERVAL:
            poison_pos        = spawn_on_free(snake, walls)
            last_poison_spawn = now

        # Spawn power-up
        if powerup is None and now - last_powerup_spawn > POWERUP_INTERVAL:
            pos  = spawn_on_free(snake, walls)
            kind = random.choice(["speed", "slow", "shield"])
            powerup            = (pos, kind, now)
            last_powerup_spawn = now

        # Power-up field timeout
        if powerup and now - powerup[2] > POWERUP_FIELD_TIMEOUT:
            powerup = None

        # ── Draw ─────────────────────────────────────────────────────────────
        screen.fill(BLACK)
        if show_grid: draw_grid(screen)
        draw_walls(screen, border_walls, obstacles)
        draw_snake(screen, snake, snake_color)

        # Food
        draw_item(screen, food_pos, RED, None, font_item)

        # Poison
        if poison_pos:
            draw_item(screen, poison_pos, POISON_COLOR, "☠", font_item)

        # Power-up on field
        if powerup:
            pu_colors = {"speed": GREEN, "slow": CYAN, "shield": PURPLE}
            pu_labels = {"speed": "SPD", "slow": "SLO", "shield": "SHD"}
            draw_item(screen, powerup[0],
                      pu_colors[powerup[1]], pu_labels[powerup[1]], font_item)

        foods_to_next = FOODS_PER_LEVEL - foods_eaten
        draw_hud(screen, font_hud, score, level, foods_to_next, personal_best,
                 active_pu, pu_end, now)

        # Shield glow on head
        if active_pu == "shield":
            hcx = snake[0][0]*CELL+CELL//2; hcy = snake[0][1]*CELL+CELL//2
            pygame.draw.circle(screen, PURPLE, (hcx, hcy), CELL, 2)

        pygame.display.flip()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Snake – TSIS 4")
    clock    = pygame.time.Clock()
    font_big = pygame.font.SysFont("Arial", 48, bold=True)
    font     = pygame.font.SysFont("Arial", 20)

    # Init DB (ignore errors if DB not available)
    try:
        db.ensure_schema()
    except Exception as e:
        print(f"[DB] Could not connect: {e}")

    settings = load_settings()

    while True:
        choice = main_menu(screen, clock, font_big, font)

        if choice == "leaderboard":
            leaderboard_screen(screen, clock, font_big, font)

        elif choice == "settings":
            settings = settings_screen(screen, clock, font_big, font, settings)

        elif choice == "play":
            username = username_screen(screen, clock, font_big, font)
            while True:
                score, level = run_game(screen, clock, font, username, settings)
                try:
                    db.save_result(username, score, level)
                    personal_best = db.get_personal_best(username)
                except Exception as e:
                    print(f"[DB] Save error: {e}")
                    personal_best = score

                result = game_over_screen(screen, clock, font_big, font,
                                         score, level, personal_best)
                if result == "menu":
                    break


if __name__ == "__main__":
    main()
