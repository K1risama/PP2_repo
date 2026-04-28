"""
TSIS 3: Racer Game — Advanced Driving, Leaderboard & Power-Ups
Extends Practice 10 / 11 racer.py with:
  3.1 Lane hazards & road events (oil spills, speed bumps, nitro strips)
  3.2 Dynamic traffic + road obstacles with safe spawn logic & difficulty scaling
  3.3 Three power-ups: Nitro, Shield, Repair (one active at a time, timeout)
  3.4 Score = coins + distance + power-up bonuses; distance meter; leaderboard
  3.5 Screens: Main Menu, Settings, Leaderboard, Game Over
"""

import pygame
import random
import sys
import math
from pygame.locals import *
from persistence import (
    load_leaderboard, save_score, load_settings, save_settings
)

# ── Constants ─────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 480, 640
FPS      = 60

WHITE  = (255, 255, 255);  BLACK  = (0,   0,   0)
GRAY   = (100, 100, 100);  DKGRAY = (50,  50,  50)
YELLOW = (255, 220, 0);    RED    = (220, 40,  40)
BLUE   = (30,  100, 220);  GREEN  = (50,  200, 80)
ORANGE = (255, 140, 0);    PURPLE = (180, 0,   200)
CYAN   = (0,   200, 220);  BROWN  = (139, 69,  19)
LGRAY  = (180, 180, 180)

ROAD_LEFT  = 80
ROAD_RIGHT = 400
ROAD_W     = ROAD_RIGHT - ROAD_LEFT

DIVIDER_X     = (ROAD_LEFT + ROAD_RIGHT) // 2
DIVIDER_H     = 40
DIVIDER_GAP   = 20
DIVIDER_SPEED = 5

DIFFICULTY_PARAMS = {
    "easy":   {"enemy_interval": 2000, "obstacle_interval": 3000, "density_step": 150},
    "normal": {"enemy_interval": 1400, "obstacle_interval": 2200, "density_step": 100},
    "hard":   {"enemy_interval": 900,  "obstacle_interval": 1500, "density_step": 60},
}


# ── Sprites ───────────────────────────────────────────────────────────────────

class Player(pygame.sprite.Sprite):
    def __init__(self, color):
        super().__init__()
        self.image = pygame.Surface((44, 74), SRCALPHA)
        self._draw(color)
        self.rect = self.image.get_rect(
            centerx=SCREEN_W // 2, bottom=SCREEN_H - 20
        )
        self.base_speed = 5
        self.speed      = self.base_speed
        self.has_shield = False

    def _draw(self, color):
        s = self.image
        s.fill((0,0,0,0))
        pygame.draw.rect(s, color,   (7,  10, 30, 54), border_radius=6)
        pygame.draw.rect(s, (180,220,255), (11,14,22,14), border_radius=3)
        pygame.draw.rect(s, (180,220,255), (11,44,22,10), border_radius=3)
        for x,y in [(2,12),(32,12),(2,48),(32,48)]:
            pygame.draw.rect(s, DKGRAY, (x,y,10,14), border_radius=3)

    def update(self, keys):
        if keys[K_LEFT]:  self.rect.x -= self.speed
        if keys[K_RIGHT]: self.rect.x += self.speed
        if keys[K_UP]:    self.rect.y -= self.speed
        if keys[K_DOWN]:  self.rect.y += self.speed
        self.rect.left   = max(ROAD_LEFT + 2,  self.rect.left)
        self.rect.right  = min(ROAD_RIGHT - 2, self.rect.right)
        self.rect.top    = max(0,              self.rect.top)
        self.rect.bottom = min(SCREEN_H,       self.rect.bottom)


class EnemyCar(pygame.sprite.Sprite):
    COLORS = [RED, GREEN, ORANGE, PURPLE, CYAN]

    def __init__(self, player_rect):
        super().__init__()
        self.image = pygame.Surface((44, 74), SRCALPHA)
        self._draw(random.choice(self.COLORS))
        self.rect  = self.image.get_rect()
        self._safe_spawn(player_rect)
        self.speed = random.randint(3, 7)

    def _draw(self, color):
        s = self.image; s.fill((0,0,0,0))
        pygame.draw.rect(s, color, (7,10,30,54), border_radius=6)
        pygame.draw.rect(s, (180,220,255),(11,46,22,10),border_radius=3)
        pygame.draw.rect(s, (180,220,255),(11,14,22,14),border_radius=3)
        for x,y in [(2,12),(32,12),(2,48),(32,48)]:
            pygame.draw.rect(s, DKGRAY,(x,y,10,14),border_radius=3)

    def _safe_spawn(self, player_rect):
        for _ in range(20):
            x = random.randint(ROAD_LEFT + 2, ROAD_RIGHT - 46)
            if abs(x - player_rect.x) > 60:
                break
        self.rect.x      = x
        self.rect.bottom = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_H + 10:
            self.kill()


class Coin(pygame.sprite.Sprite):
    def __init__(self, value=10):
        super().__init__()
        self.value = value
        size = 14 if value == 10 else 20
        self.image = pygame.Surface((size, size), SRCALPHA)
        color = YELLOW if value == 10 else ORANGE
        pygame.draw.circle(self.image, color, (size//2,size//2), size//2)
        pygame.draw.circle(self.image, WHITE, (size//4,size//4), size//5)
        self.rect  = self.image.get_rect()
        self.rect.x = random.randint(ROAD_LEFT+10, ROAD_RIGHT-30)
        self.rect.bottom = -5
        self.speed = DIVIDER_SPEED

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_H + 10: self.kill()


class OilSpill(pygame.sprite.Sprite):
    """Lane hazard: slows player down briefly."""
    def __init__(self, player_rect):
        super().__init__()
        self.image = pygame.Surface((60, 30), SRCALPHA)
        pygame.draw.ellipse(self.image, (20, 20, 80, 180), (0,0,60,30))
        self.rect = self.image.get_rect()
        self._safe_spawn(player_rect)
        self.speed = DIVIDER_SPEED

    def _safe_spawn(self, player_rect):
        for _ in range(20):
            x = random.randint(ROAD_LEFT, ROAD_RIGHT - 60)
            if abs(x - player_rect.x) > 80:
                break
        self.rect.x = x
        self.rect.bottom = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_H + 10: self.kill()


class NitroStrip(pygame.sprite.Sprite):
    """Road event: gives brief speed boost on drive-over."""
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((ROAD_W, 18), SRCALPHA)
        self.image.fill((0, 255, 120, 140))
        font = pygame.font.SysFont("Arial", 12, bold=True)
        lbl  = font.render("NITRO", True, BLACK)
        self.image.blit(lbl, (ROAD_W//2 - lbl.get_width()//2, 2))
        self.rect = self.image.get_rect(x=ROAD_LEFT, bottom=-10)
        self.speed = DIVIDER_SPEED

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_H + 10: self.kill()


class PowerUp(pygame.sprite.Sprite):
    """Collectible power-up: Nitro / Shield / Repair."""
    TYPES  = ["nitro", "shield", "repair"]
    COLORS = {"nitro": (0,255,120), "shield": (0,180,255), "repair": (255,80,80)}

    def __init__(self):
        super().__init__()
        self.kind  = random.choice(self.TYPES)
        self.image = pygame.Surface((28, 28), SRCALPHA)
        pygame.draw.rect(self.image, self.COLORS[self.kind], (0,0,28,28), border_radius=6)
        font = pygame.font.SysFont("Arial", 10, bold=True)
        lbl  = font.render(self.kind[:3].upper(), True, BLACK)
        self.image.blit(lbl, (14 - lbl.get_width()//2, 8))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(ROAD_LEFT+10, ROAD_RIGHT-38)
        self.rect.bottom = -10
        self.speed = DIVIDER_SPEED
        self.spawn_time = pygame.time.get_ticks()
        self.timeout    = 8000   # disappears after 8 s if not collected

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_H + 10: self.kill()
        if pygame.time.get_ticks() - self.spawn_time > self.timeout: self.kill()


# ── Road divider ──────────────────────────────────────────────────────────────

class RoadDivider:
    def __init__(self):
        self.offset = 0
    def update(self):
        self.offset = (self.offset + DIVIDER_SPEED) % (DIVIDER_H + DIVIDER_GAP)
    def draw(self, surface):
        step = DIVIDER_H + DIVIDER_GAP
        y = -step + self.offset
        while y < SCREEN_H:
            pygame.draw.rect(surface, WHITE, (DIVIDER_X - 3, y, 6, DIVIDER_H))
            y += step


# ── UI helpers ────────────────────────────────────────────────────────────────

def draw_road(surface):
    surface.fill(GRAY)
    pygame.draw.rect(surface, DKGRAY, (ROAD_LEFT, 0, ROAD_W, SCREEN_H))
    pygame.draw.rect(surface, WHITE,  (ROAD_LEFT, 0, 4, SCREEN_H))
    pygame.draw.rect(surface, WHITE,  (ROAD_RIGHT - 4, 0, 4, SCREEN_H))


def draw_hud(surface, font, score, coins, distance, active_pu, pu_timer, now):
    pygame.draw.rect(surface, (0,0,0,160), (0, 0, SCREEN_W, 40))
    surface.blit(font.render(f"Score:{score}", True, WHITE), (8, 10))
    surface.blit(font.render(f"Coins:{coins}", True, YELLOW), (160, 10))
    surface.blit(font.render(f"Dist:{distance}m", True, LGRAY), (290, 10))
    if active_pu:
        remaining = max(0, (pu_timer - now) // 1000)
        color = PowerUp.COLORS.get(active_pu, WHITE)
        surface.blit(font.render(f"[{active_pu.upper()} {remaining}s]", True, color),
                     (SCREEN_W // 2 - 50, SCREEN_H - 30))


def button(surface, font, rect, text, bg, hover_color=None):
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)
    color = hover_color or (min(bg[0]+30,255), min(bg[1]+30,255), min(bg[2]+30,255))
    pygame.draw.rect(surface, color if hovered else bg, rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
    txt = font.render(text, True, WHITE)
    surface.blit(txt, txt.get_rect(center=rect.center))
    return hovered and pygame.mouse.get_pressed()[0]


# ── Screens ───────────────────────────────────────────────────────────────────

def username_screen(screen, clock, font_big, font):
    """Ask the player for their username before playing."""
    name = ""
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN and name.strip():
                    return name.strip()
                elif event.key == K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode and len(name) < 16:
                    name += event.unicode
        screen.fill(DKGRAY)
        t = font_big.render("Enter your name", True, WHITE)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 60)))
        box = pygame.Rect(SCREEN_W//2 - 120, SCREEN_H//2 - 20, 240, 44)
        pygame.draw.rect(screen, (80,80,80), box, border_radius=6)
        pygame.draw.rect(screen, WHITE, box, 2, border_radius=6)
        nt = font.render(name + "|", True, WHITE)
        screen.blit(nt, nt.get_rect(center=box.center))
        hint = font.render("Press Enter to continue", True, LGRAY)
        screen.blit(hint, hint.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 40)))
        pygame.display.flip()


def main_menu(screen, clock, font_big, font):
    """Main menu: Play, Leaderboard, Settings, Quit."""
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pass  # handled by button()
        screen.fill(DKGRAY)
        t = font_big.render("RACER", True, YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2, 120)))
        cx = SCREEN_W // 2
        if button(screen, font, pygame.Rect(cx-90, 220, 180, 46), "Play",        (50,120,50)):
            return "play"
        if button(screen, font, pygame.Rect(cx-90, 280, 180, 46), "Leaderboard", (50,50,150)):
            return "leaderboard"
        if button(screen, font, pygame.Rect(cx-90, 340, 180, 46), "Settings",    (100,80,40)):
            return "settings"
        if button(screen, font, pygame.Rect(cx-90, 400, 180, 46), "Quit",        (140,40,40)):
            pygame.quit(); sys.exit()
        pygame.display.flip()


def leaderboard_screen(screen, clock, font_big, font):
    board = load_leaderboard()
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
        screen.fill(DKGRAY)
        t = font_big.render("TOP 10", True, YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2, 50)))
        headers = font.render(f"{'#':<3} {'Name':<14} {'Score':<8} {'Dist':<6} {'Date'}", True, LGRAY)
        screen.blit(headers, (30, 100))
        pygame.draw.line(screen, LGRAY, (30, 120), (SCREEN_W-30, 120), 1)
        for i, entry in enumerate(board):
            row = font.render(
                f"{i+1:<3} {entry['name']:<14} {entry['score']:<8} "
                f"{entry['distance']:<6} {entry['date']}",
                True, WHITE
            )
            screen.blit(row, (30, 130 + i * 28))
        if button(screen, font, pygame.Rect(SCREEN_W//2-60, SCREEN_H-70, 120, 40),
                  "Back", (80,80,80)):
            return
        pygame.display.flip()


def settings_screen(screen, clock, font_big, font):
    settings = load_settings()
    car_colors = [(30,100,220),(220,40,40),(50,200,80),(255,140,0),(180,0,200)]
    color_idx = 0
    # Match saved color
    for i, c in enumerate(car_colors):
        if list(c) == settings.get("car_color", [30,100,220]):
            color_idx = i; break

    diffs = ["easy", "normal", "hard"]
    diff_idx = diffs.index(settings.get("difficulty", "normal"))

    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()

        screen.fill(DKGRAY)
        t = font_big.render("Settings", True, WHITE)
        screen.blit(t, t.get_rect(center=(SCREEN_W//2, 50)))

        # Sound toggle
        slbl = "Sound: ON" if settings["sound"] else "Sound: OFF"
        if button(screen, font, pygame.Rect(SCREEN_W//2-90, 130, 180, 40), slbl, (60,60,120)):
            settings["sound"] = not settings["sound"]

        # Car color
        clbl = "Car Color ▶"
        if button(screen, font, pygame.Rect(SCREEN_W//2-90, 190, 180, 40), clbl, (60,60,120)):
            color_idx = (color_idx + 1) % len(car_colors)
            settings["car_color"] = list(car_colors[color_idx])
        pygame.draw.rect(screen, car_colors[color_idx],
                         pygame.Rect(SCREEN_W//2+96, 195, 30, 30), border_radius=4)

        # Difficulty
        dlbl = f"Diff: {diffs[diff_idx]}"
        if button(screen, font, pygame.Rect(SCREEN_W//2-90, 250, 180, 40), dlbl, (60,60,120)):
            diff_idx = (diff_idx + 1) % len(diffs)
            settings["difficulty"] = diffs[diff_idx]

        # Save & Back
        if button(screen, font, pygame.Rect(SCREEN_W//2-90, 340, 180, 40),
                  "Save & Back", (40,120,40)):
            save_settings(settings)
            return settings

        pygame.display.flip()


def game_over_screen(screen, clock, font_big, font, score, distance, coins):
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
        screen.fill(DKGRAY)
        for txt, color, y in [
            ("GAME OVER",        RED,    160),
            (f"Score: {score}",  WHITE,  230),
            (f"Distance: {distance}m", LGRAY, 265),
            (f"Coins: {coins}",  YELLOW, 300),
        ]:
            s = font_big.render(txt, True, color) if txt == "GAME OVER" else font.render(txt, True, color)
            screen.blit(s, s.get_rect(center=(SCREEN_W//2, y)))
        cx = SCREEN_W // 2
        if button(screen, font, pygame.Rect(cx-90, 360, 180, 44), "Retry",     (50,120,50)):
            return "retry"
        if button(screen, font, pygame.Rect(cx-90, 420, 180, 44), "Main Menu", (60,60,140)):
            return "menu"
        pygame.display.flip()


# ── Main game ─────────────────────────────────────────────────────────────────

def run_game(screen, clock, font, username, settings):
    """Run one game session. Returns (score, distance, coins)."""
    diff      = DIFFICULTY_PARAMS[settings.get("difficulty", "normal")]
    car_color = tuple(settings.get("car_color", [30,100,220]))

    player = Player(car_color)
    all_sprites   = pygame.sprite.Group(player)
    enemy_group   = pygame.sprite.Group()
    coin_group    = pygame.sprite.Group()
    hazard_group  = pygame.sprite.Group()   # oil, nitro strips
    powerup_group = pygame.sprite.Group()
    divider       = RoadDivider()

    score = 0; coins_collected = 0; distance = 0
    active_pu    = None   # current active power-up kind
    pu_end_time  = 0      # when the power-up expires

    now = pygame.time.get_ticks
    t0  = now()

    # Spawn timers
    last_enemy   = t0
    last_coin    = t0
    last_hazard  = t0
    last_powerup = t0
    last_nitro   = t0

    enemy_interval   = diff["enemy_interval"]
    obstacle_interval = diff["obstacle_interval"]
    density_step     = diff["density_step"]   # score points before interval decreases

    while True:
        clock.tick(FPS)
        tick_now = now()
        distance = (tick_now - t0) // 100   # centiseconds → decametres

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return score, distance, coins_collected

        # ── Difficulty scaling ────────────────────────────────────────────────
        speed_stage    = score // density_step
        cur_enemy_int  = max(400, enemy_interval - speed_stage * 50)
        cur_obs_int    = max(600, obstacle_interval - speed_stage * 40)

        # ── Spawning ──────────────────────────────────────────────────────────
        if tick_now - last_enemy > cur_enemy_int:
            e = EnemyCar(player.rect)
            enemy_group.add(e); all_sprites.add(e)
            last_enemy = tick_now

        if tick_now - last_coin > 2000:
            v = random.choices([10, 30], weights=[70, 30])[0]
            c = Coin(v)
            coin_group.add(c); all_sprites.add(c)
            last_coin = tick_now

        if tick_now - last_hazard > cur_obs_int:
            h = OilSpill(player.rect)
            hazard_group.add(h); all_sprites.add(h)
            last_hazard = tick_now

        if tick_now - last_nitro > 8000:
            n = NitroStrip()
            hazard_group.add(n); all_sprites.add(n)
            last_nitro = tick_now

        if tick_now - last_powerup > 5000 and not powerup_group:
            pu = PowerUp()
            powerup_group.add(pu); all_sprites.add(pu)
            last_powerup = tick_now

        # ── Updates ───────────────────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        player.update(keys)
        enemy_group.update()
        coin_group.update()
        hazard_group.update()
        powerup_group.update()
        divider.update()
        score += 1

        # Power-up expiry
        if active_pu and tick_now > pu_end_time:
            if active_pu == "nitro":
                player.speed = player.base_speed
            active_pu = None

        # ── Collisions ────────────────────────────────────────────────────────
        # Enemies
        if pygame.sprite.spritecollide(player, enemy_group, False):
            if player.has_shield:
                player.has_shield = False
                active_pu = None
                # destroy the enemy
                pygame.sprite.spritecollide(player, enemy_group, True)
            else:
                return score, distance, coins_collected

        # Oil spills
        oil_hits = [h for h in pygame.sprite.spritecollide(player, hazard_group, False)
                    if isinstance(h, OilSpill)]
        if oil_hits:
            player.speed = max(2, player.base_speed - 2)
        else:
            if active_pu != "nitro":
                player.speed = player.base_speed

        # Nitro strips
        nitro_hits = [h for h in pygame.sprite.spritecollide(player, hazard_group, False)
                      if isinstance(h, NitroStrip)]
        if nitro_hits:
            player.speed = player.base_speed + 4

        # Coins
        for c in pygame.sprite.spritecollide(player, coin_group, True):
            coins_collected += 1
            score += c.value

        # Power-ups
        for pu in pygame.sprite.spritecollide(player, powerup_group, True):
            kind = pu.kind
            active_pu = kind
            if kind == "nitro":
                player.speed  = player.base_speed + 6
                pu_end_time   = tick_now + 4000
            elif kind == "shield":
                player.has_shield = True
                pu_end_time       = tick_now + 30000  # until triggered
            elif kind == "repair":
                # Destroy nearest enemy as a "repair" action
                enemies = sorted(enemy_group.sprites(),
                                 key=lambda e: abs(e.rect.centery - player.rect.centery))
                if enemies:
                    enemies[0].kill()
                active_pu   = None

        # ── Drawing ───────────────────────────────────────────────────────────
        draw_road(screen)
        divider.draw(screen)
        all_sprites.draw(screen)

        # Shield glow
        if player.has_shield:
            pygame.draw.circle(screen, (0,180,255), player.rect.center, 36, 3)

        font_sm = pygame.font.SysFont("Arial", 18, bold=True)
        draw_hud(screen, font_sm, score, coins_collected, distance,
                 active_pu, pu_end_time, tick_now)

        pygame.display.flip()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Racer – TSIS 3")
    clock    = pygame.time.Clock()
    font_big = pygame.font.SysFont("Arial", 46, bold=True)
    font     = pygame.font.SysFont("Arial", 22)

    settings = load_settings()

    while True:
        choice = main_menu(screen, clock, font_big, font)

        if choice == "leaderboard":
            leaderboard_screen(screen, clock, font_big, font)

        elif choice == "settings":
            settings = settings_screen(screen, clock, font_big, font)

        elif choice == "play":
            username = username_screen(screen, clock, font_big, font)
            while True:
                score, distance, coins = run_game(
                    screen, clock, font, username, settings
                )
                save_score(username, score, distance)
                result = game_over_screen(
                    screen, clock, font_big, font, score, distance, coins
                )
                if result == "menu":
                    break
                # "retry" loops back


if __name__ == "__main__":
    main()
