import pygame
import datetime
import os
from clock import rotate_center

WIDTH, HEIGHT = 650, 650
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mickey's Clock")
clock = pygame.time.Clock()

BASE_PATH = os.path.dirname(__file__)
IMG_DIR = os.path.join(BASE_PATH, "images")

try:
    mickey_body = pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "main-clock.png")).convert_alpha(), (600, 600))
    right_hand = pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "right-hand.png")).convert_alpha(), (200, 400))
    left_hand = pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "left-hand.png")).convert_alpha(), (230, 500))
except pygame.error as e:
    print(f"Loading error: {e}")
    pygame.quit()
    exit()

CENTER = (mickey_body.get_width() // 2, mickey_body.get_height() // 2)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    now = datetime.datetime.now()
    seconds = now.second
    minutes = now.minute
    micro = now.microsecond / 1_000_000

    sec_angle = -((seconds + micro) * 6)
    min_angle = -((minutes + (seconds / 60)) *6)

    screen.fill((255, 255, 255))

    screen.blit(mickey_body, (0, 0))

    rot_min, min_rect = rotate_center(right_hand, min_angle, CENTER)
    screen.blit(rot_min, min_rect)

    rot_sec, sec_rect = rotate_center(left_hand, sec_angle, CENTER)
    screen.blit(rot_sec, sec_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()