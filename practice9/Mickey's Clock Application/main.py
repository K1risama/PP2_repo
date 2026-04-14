import pygame
import sys
import math
import datetime

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 500, 500
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 10  # Update frequently enough to feel live

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK = (30, 30, 30)
YELLOW = (255, 220, 50)
RED = (200, 40, 40)

# Clock face radius
CLOCK_RADIUS = 180


def draw_clock_face(surface):
    """Draw the clock face with tick marks and numbers."""
    # Background circle
    pygame.draw.circle(surface, WHITE, CENTER, CLOCK_RADIUS)
    pygame.draw.circle(surface, DARK, CENTER, CLOCK_RADIUS, 4)

    # Draw minute tick marks (60 ticks)
    for i in range(60):
        angle = math.radians(i * 6 - 90)
        if i % 5 == 0:
            # Hour marks — longer and thicker
            inner = CLOCK_RADIUS - 18
            outer = CLOCK_RADIUS - 4
            color = DARK
            width = 3
        else:
            # Minute marks
            inner = CLOCK_RADIUS - 10
            outer = CLOCK_RADIUS - 4
            color = GRAY
            width = 1

        x1 = int(CENTER[0] + inner * math.cos(angle))
        y1 = int(CENTER[1] + inner * math.sin(angle))
        x2 = int(CENTER[0] + outer * math.cos(angle))
        y2 = int(CENTER[1] + outer * math.sin(angle))
        pygame.draw.line(surface, color, (x1, y1), (x2, y2), width)

    # Draw numbers (12 positions)
    font = pygame.font.SysFont("Arial", 22, bold=True)
    for i in range(1, 13):
        angle = math.radians(i * 30 - 90)
        r = CLOCK_RADIUS - 38
        x = int(CENTER[0] + r * math.cos(angle))
        y = int(CENTER[1] + r * math.sin(angle))
        text = font.render(str(i), True, DARK)
        rect = text.get_rect(center=(x, y))
        surface.blit(text, rect)


def draw_hand(surface, angle_deg, length, color, width, image=None):
    """
    Draw a clock hand.
    angle_deg: 0 = 12 o'clock, increases clockwise.
    If image is provided, rotate and blit it instead of drawing a line.
    """
    angle_rad = math.radians(angle_deg - 90)
    tip_x = int(CENTER[0] + length * math.cos(angle_rad))
    tip_y = int(CENTER[1] + length * math.sin(angle_rad))

    if image:
        # Rotate image: pygame rotates counter-clockwise, so negate
        rotated = pygame.transform.rotate(image, -angle_deg)
        rect = rotated.get_rect(center=CENTER)
        surface.blit(rotated, rect)
    else:
        # Draw a thick line from center to tip
        base_x = int(CENTER[0] - (length * 0.2) * math.cos(angle_rad))
        base_y = int(CENTER[1] - (length * 0.2) * math.sin(angle_rad))
        pygame.draw.line(surface, color, (base_x, base_y), (tip_x, tip_y), width)
        # Draw rounded cap at tip
        pygame.draw.circle(surface, color, (tip_x, tip_y), width // 2)


def load_hand_image(path, hand_length):
    """
    Try to load mickey hand image.
    Returns scaled image or None if not found.
    """
    try:
        img = pygame.image.load(path).convert_alpha()
        # Scale so the height matches the desired hand length * 2
        scale_factor = (hand_length * 2) / img.get_height()
        new_w = int(img.get_width() * scale_factor)
        new_h = int(img.get_height() * scale_factor)
        img = pygame.transform.scale(img, (new_w, new_h))
        return img
    except Exception:
        return None


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mickey's Clock")
    clock = pygame.time.Clock()

    # Try loading Mickey hand images
    # Right hand = minutes, Left hand = seconds
    # Place your mickey_hand.png in the images/ folder
    right_hand_img = load_hand_image("images/mickey_hand.png", 130)
    left_hand_img = load_hand_image("images/mickey_hand.png", 150)

    title_font = pygame.font.SysFont("Arial", 18)
    time_font = pygame.font.SysFont("Courier New", 26, bold=True)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        # Get current time
        now = datetime.datetime.now()
        minutes = now.minute
        seconds = now.second

        # Calculate angles (each minute/second = 6 degrees)
        minute_angle = minutes * 6           # 0–354°
        second_angle = seconds * 6           # 0–354°

        # Draw background
        screen.fill((245, 240, 230))

        # Draw clock face
        draw_clock_face(screen)

        # Draw minute hand (RIGHT hand of Mickey)
        if right_hand_img:
            draw_hand(screen, minute_angle, 130, RED, 6, image=right_hand_img)
        else:
            draw_hand(screen, minute_angle, 130, (30, 30, 180), 8)

        # Draw second hand (LEFT hand of Mickey)
        if left_hand_img:
            draw_hand(screen, second_angle, 150, YELLOW, 4, image=left_hand_img)
        else:
            draw_hand(screen, second_angle, 150, RED, 4)

        # Center dot
        pygame.draw.circle(screen, DARK, CENTER, 8)
        pygame.draw.circle(screen, WHITE, CENTER, 4)

        # Display digital time below clock
        time_str = now.strftime("%M:%S")
        time_surf = time_font.render(f"Time: {time_str}", True, DARK)
        screen.blit(time_surf, time_surf.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

        # Label
        label = title_font.render("Mickey's Clock  |  Right=Minutes  Left=Seconds", True, GRAY)
        screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT - 18)))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
