import pygame
import sys

# Initialize pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
RED = (220, 50, 50)

# Ball settings
BALL_RADIUS = 25
BALL_STEP = 20


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Moving Ball Game")
    clock = pygame.time.Clock()

    # Ball starts at center
    ball_x = SCREEN_WIDTH // 2
    ball_y = SCREEN_HEIGHT // 2

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                new_x, new_y = ball_x, ball_y

                if event.key == pygame.K_UP:
                    new_y -= BALL_STEP
                elif event.key == pygame.K_DOWN:
                    new_y += BALL_STEP
                elif event.key == pygame.K_LEFT:
                    new_x -= BALL_STEP
                elif event.key == pygame.K_RIGHT:
                    new_x += BALL_STEP
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # Only move if within boundaries
                if (BALL_RADIUS <= new_x <= SCREEN_WIDTH - BALL_RADIUS and
                        BALL_RADIUS <= new_y <= SCREEN_HEIGHT - BALL_RADIUS):
                    ball_x, ball_y = new_x, new_y

        # Draw
        screen.fill(WHITE)
        pygame.draw.circle(screen, RED, (ball_x, ball_y), BALL_RADIUS)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
