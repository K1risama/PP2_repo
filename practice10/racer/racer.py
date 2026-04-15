"""
Practice 10 - Task 1: Racer Game
Extended from the CodersLegacy PyGame tutorial series.
Extra features added:
  - Randomly appearing coins on the road
  - Coin counter displayed in the top right corner
  - Full comments throughout the code
"""

import pygame
import random
import sys
from pygame.locals import *

# ── Constants ──────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 400, 600   # Window dimensions
FPS = 60                         # Frames per second cap

# Colors (RGB)
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GRAY   = (100, 100, 100)
DKGRAY = (50,  50,  50)
YELLOW = (255, 220, 0)
RED    = (220, 40,  40)
BLUE   = (30,  100, 220)
GREEN  = (50,  200, 80)
ORANGE = (255, 140, 0)

# Road geometry
ROAD_LEFT  = 80    # left edge of drivable road
ROAD_RIGHT = 320   # right edge of drivable road
ROAD_W     = ROAD_RIGHT - ROAD_LEFT

# Lane divider strip settings (scrolling white dashes)
DIVIDER_X     = SCREEN_W // 2   # center of road
DIVIDER_H     = 40              # height of each dash
DIVIDER_GAP   = 20              # gap between dashes
DIVIDER_SPEED = 5               # pixels per frame (same as cars)

# ── Player Car ─────────────────────────────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    """The car controlled by the player (arrow keys)."""

    def __init__(self):
        super().__init__()
        # Draw the car as a simple colored rectangle with details
        self.image = pygame.Surface((40, 70), SRCALPHA)
        self._draw_car(BLUE)
        self.rect = self.image.get_rect()
        # Start near the bottom-center of the road
        self.rect.centerx = SCREEN_W // 2
        self.rect.bottom   = SCREEN_H - 20
        self.speed = 5

    def _draw_car(self, color):
        """Draws a simple top-down car onto self.image."""
        surf = self.image
        surf.fill((0, 0, 0, 0))  # transparent background
        # Body
        pygame.draw.rect(surf, color, (5, 10, 30, 50), border_radius=6)
        # Windshield
        pygame.draw.rect(surf, (180, 220, 255), (9, 14, 22, 14), border_radius=3)
        # Rear window
        pygame.draw.rect(surf, (180, 220, 255), (9, 42, 22, 10), border_radius=3)
        # Wheels
        for x, y in [(2, 12), (28, 12), (2, 44), (28, 44)]:
            pygame.draw.rect(surf, DKGRAY, (x, y, 10, 14), border_radius=3)

    def update(self, keys):
        """Move the player car based on pressed arrow keys."""
        if keys[K_LEFT]:
            self.rect.x -= self.speed
        if keys[K_RIGHT]:
            self.rect.x += self.speed
        if keys[K_UP]:
            self.rect.y -= self.speed
        if keys[K_DOWN]:
            self.rect.y += self.speed

        # Clamp player within road boundaries
        self.rect.left  = max(ROAD_LEFT + 2,  self.rect.left)
        self.rect.right = min(ROAD_RIGHT - 2, self.rect.right)
        self.rect.top    = max(0,              self.rect.top)
        self.rect.bottom = min(SCREEN_H,       self.rect.bottom)


# ── Enemy Car ──────────────────────────────────────────────────────────────────
class EnemyCar(pygame.sprite.Sprite):
    """An obstacle car that spawns at the top and scrolls downward."""

    COLORS = [RED, GREEN, ORANGE, (180, 0, 180), (0, 180, 180)]

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 70), SRCALPHA)
        color = random.choice(self.COLORS)
        self._draw_car(color)
        self.rect = self.image.get_rect()
        # Spawn at a random lane position on the road
        self.rect.x = random.randint(ROAD_LEFT + 2, ROAD_RIGHT - 42)
        self.rect.bottom = -10  # start just above the screen
        self.speed = random.randint(3, 7)

    def _draw_car(self, color):
        """Draws a simple top-down enemy car (mirrored, facing down)."""
        surf = self.image
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, color, (5, 10, 30, 50), border_radius=6)
        pygame.draw.rect(surf, (180, 220, 255), (9, 46, 22, 10), border_radius=3)
        pygame.draw.rect(surf, (180, 220, 255), (9, 14, 22, 14), border_radius=3)
        for x, y in [(2, 12), (28, 12), (2, 44), (28, 44)]:
            pygame.draw.rect(surf, DKGRAY, (x, y, 10, 14), border_radius=3)

    def update(self):
        """Scroll the enemy car downward; remove if it leaves the screen."""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_H + 10:
            self.kill()  # remove from all sprite groups


# ── Coin ───────────────────────────────────────────────────────────────────────
class Coin(pygame.sprite.Sprite):
    """
    A randomly appearing coin on the road.
    Scrolls downward like enemy cars; collected on player collision.
    """

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20), SRCALPHA)
        # Draw a gold circle with a shine highlight
        pygame.draw.circle(self.image, YELLOW, (10, 10), 10)
        pygame.draw.circle(self.image, (255, 255, 180), (7, 6), 4)  # shine
        pygame.draw.circle(self.image, (200, 160, 0), (10, 10), 10, 2)  # rim

        self.rect = self.image.get_rect()
        # Spawn randomly on the road
        self.rect.x = random.randint(ROAD_LEFT + 10, ROAD_RIGHT - 30)
        self.rect.bottom = -5
        self.speed = 5  # same as road scroll speed

    def update(self):
        """Scroll coin downward; remove when it exits the screen."""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_H + 10:
            self.kill()


# ── Road Divider Helper ────────────────────────────────────────────────────────
class RoadDivider:
    """
    Manages a scrolling set of white dashes in the center of the road
    to give the illusion of movement.
    """

    def __init__(self):
        self.offset = 0  # vertical scroll offset

    def update(self):
        """Advance the scroll offset each frame."""
        self.offset = (self.offset + DIVIDER_SPEED) % (DIVIDER_H + DIVIDER_GAP)

    def draw(self, surface):
        """Draw all visible dashes."""
        step = DIVIDER_H + DIVIDER_GAP
        # Start one full step above the top so dashes slide in smoothly
        y = -step + self.offset
        while y < SCREEN_H:
            pygame.draw.rect(surface, WHITE,
                             (DIVIDER_X - 3, y, 6, DIVIDER_H))
            y += step


# ── HUD Drawing ────────────────────────────────────────────────────────────────
def draw_hud(surface, font, score, coins):
    """
    Renders the score (top-left) and coin counter (top-right) on screen.
    """
    score_surf = font.render(f"Score: {score}", True, WHITE)
    coin_surf  = font.render(f"Coins: {coins}", True, YELLOW)

    surface.blit(score_surf, (10, 10))
    # Align coin text to the right edge with a 10-pixel margin
    surface.blit(coin_surf, (SCREEN_W - coin_surf.get_width() - 10, 10))


# ── Game Over Screen ───────────────────────────────────────────────────────────
def game_over_screen(surface, font_big, font_small, score, coins):
    """
    Displays a 'Game Over' overlay and waits for the player to press R or Q.
    Returns True to restart, False to quit.
    """
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    msgs = [
        (font_big,   "GAME OVER",          RED,   SCREEN_H // 2 - 60),
        (font_small, f"Score: {score}",    WHITE, SCREEN_H // 2),
        (font_small, f"Coins: {coins}",    YELLOW,SCREEN_H // 2 + 35),
        (font_small, "R – Restart",        WHITE, SCREEN_H // 2 + 80),
        (font_small, "Q – Quit",           WHITE, SCREEN_H // 2 + 110),
    ]
    for fnt, txt, col, y in msgs:
        surf = fnt.render(txt, True, col)
        surface.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, y))

    pygame.display.flip()

    # Wait for R or Q key press
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN:
                if event.key == K_r:
                    return True
                if event.key == K_q:
                    return False


# ── Main Game ──────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Racer – Practice 10")
    clock = pygame.time.Clock()

    font_big   = pygame.font.SysFont("Arial", 48, bold=True)
    font_small = pygame.font.SysFont("Arial", 24)

    # ── Game loop ────────────────────────────────────────────────────────────
    while True:  # outer loop allows restarting after game over
        # -- Initialise game state --
        player = Player()

        all_sprites  = pygame.sprite.Group(player)
        enemy_group  = pygame.sprite.Group()
        coin_group   = pygame.sprite.Group()

        divider = RoadDivider()

        score = 0          # increments each frame the player survives
        coins_collected = 0

        # Timers control how often new enemies / coins spawn (in milliseconds)
        enemy_spawn_time = 1500   # spawn enemy every 1.5 s
        coin_spawn_time  = 2500   # spawn coin  every 2.5 s
        last_enemy_spawn = pygame.time.get_ticks()
        last_coin_spawn  = pygame.time.get_ticks()

        running = True
        while running:
            dt = clock.tick(FPS)  # milliseconds since last frame
            now = pygame.time.get_ticks()

            # ── Events ───────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

            # ── Spawning ─────────────────────────────────────────────────────
            # Spawn a new enemy car at regular intervals
            if now - last_enemy_spawn >= enemy_spawn_time:
                enemy = EnemyCar()
                enemy_group.add(enemy)
                all_sprites.add(enemy)
                last_enemy_spawn = now

            # Spawn a new coin at regular intervals
            if now - last_coin_spawn >= coin_spawn_time:
                coin = Coin()
                coin_group.add(coin)
                all_sprites.add(coin)
                last_coin_spawn = now

            # ── Updates ──────────────────────────────────────────────────────
            keys = pygame.key.get_pressed()
            player.update(keys)
            enemy_group.update()
            coin_group.update()
            divider.update()

            # Increment score each frame (survival-based)
            score += 1

            # ── Collision: player ↔ enemies ───────────────────────────────
            if pygame.sprite.spritecollide(player, enemy_group, False,
                                           pygame.sprite.collide_mask
                                           if False else None):
                # Simple rect collision is fine for a tutorial extension
                if pygame.sprite.spritecollide(player, enemy_group, False):
                    running = False  # trigger game over

            # ── Collision: player ↔ coins ─────────────────────────────────
            collected = pygame.sprite.spritecollide(player, coin_group, True)
            coins_collected += len(collected)

            # ── Drawing ───────────────────────────────────────────────────
            # Road background
            screen.fill(GRAY)                          # grass / shoulders
            pygame.draw.rect(screen, DKGRAY,
                             (ROAD_LEFT, 0, ROAD_W, SCREEN_H))  # road surface
            # Road edges
            pygame.draw.rect(screen, WHITE, (ROAD_LEFT,  0, 4, SCREEN_H))
            pygame.draw.rect(screen, WHITE, (ROAD_RIGHT - 4, 0, 4, SCREEN_H))

            divider.draw(screen)                        # scrolling dashes
            all_sprites.draw(screen)                    # sprites
            draw_hud(screen, font_small, score, coins_collected)  # HUD

            pygame.display.flip()

        # ── Game Over ─────────────────────────────────────────────────────
        restart = game_over_screen(screen, font_big, font_small,
                                   score, coins_collected)
        if not restart:
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
