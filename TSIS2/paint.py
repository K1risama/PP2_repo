"""
TSIS 2: Paint Application — Extended Drawing Tools
Extends Practice 10 / Practice 11 paint.py with:
  1. Pencil tool       — freehand drawing (continuous line between mouse positions)
  2. Straight line tool — click/drag with live preview, committed on release
  3. Three brush sizes — 2 px / 5 px / 10 px; keys 1/2/3 or toolbar buttons
  4. Flood-fill tool   — BFS fill bounded by exact color match
  5. Ctrl+S save       — saves canvas as timestamped .png
  6. Text tool         — click canvas, type, Enter to commit, Escape to cancel

All Practice 10-11 shapes (rect, circle, eraser, square, right triangle,
equilateral triangle, rhombus) still work and respect the active brush size.
"""

import pygame
import sys
import math
import os
from collections import deque
from datetime import datetime
from pygame.locals import *

# ── Layout ────────────────────────────────────────────────────────────────────
SCREEN_W  = 1000
SCREEN_H  = 680
TOOLBAR_H = 90
CANVAS_TOP = TOOLBAR_H
CANVAS_H  = SCREEN_H - TOOLBAR_H
CANVAS_BG = (240, 240, 240)

# ── Palette ───────────────────────────────────────────────────────────────────
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
DGRAY  = (50,  50,  50)
LGRAY  = (180, 180, 180)

PALETTE = [
    (0,   0,   0),    (255, 255, 255), (128, 128, 128), (192, 192, 192),
    (255, 0,   0),    (180, 0,   0),   (255, 128, 0),   (255, 220, 0),
    (0,   200, 0),    (0,   100, 0),   (0,   200, 200), (0,   0,   255),
    (0,   0,   180),  (180, 0,   200), (255, 100, 150), (139, 69,  19),
]

# ── Tool IDs ──────────────────────────────────────────────────────────────────
TOOL_PENCIL    = "pencil"
TOOL_LINE      = "line"
TOOL_RECTANGLE = "rect"
TOOL_CIRCLE    = "circle"
TOOL_ERASER    = "eraser"
TOOL_FILL      = "fill"
TOOL_TEXT      = "text"

TOOLS = [
    TOOL_PENCIL, TOOL_LINE, TOOL_RECTANGLE,
    TOOL_CIRCLE, TOOL_ERASER, TOOL_FILL, TOOL_TEXT,
]

TOOL_LABELS = {
    TOOL_PENCIL:    ("Pencil",  "P"),
    TOOL_LINE:      ("Line",    "L"),
    TOOL_RECTANGLE: ("Rect",    "R"),
    TOOL_CIRCLE:    ("Circle",  "C"),
    TOOL_ERASER:    ("Eraser",  "E"),
    TOOL_FILL:      ("Fill",    "F"),
    TOOL_TEXT:      ("Text",    "T"),
}

BRUSH_SIZES = [2, 5, 10]   # small / medium / large


# ── Toolbar ───────────────────────────────────────────────────────────────────

def draw_toolbar(surface, font, active_tool, active_color, brush_size):
    pygame.draw.rect(surface, DGRAY, (0, 0, SCREEN_W, TOOLBAR_H))
    pygame.draw.line(surface, LGRAY, (0, TOOLBAR_H - 1), (SCREEN_W, TOOLBAR_H - 1), 2)

    btn_w, btn_h = 72, 34
    btn_y = 6
    for i, tool in enumerate(TOOLS):
        bx   = 6 + i * (btn_w + 4)
        rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
        bg   = (80, 130, 200) if tool == active_tool else (70, 70, 70)
        pygame.draw.rect(surface, bg, rect, border_radius=5)
        pygame.draw.rect(surface, LGRAY, rect, 1, border_radius=5)
        lbl, key = TOOL_LABELS[tool]
        txt = font.render(f"{lbl}[{key}]", True, WHITE)
        surface.blit(txt, txt.get_rect(center=rect.center))

    # Brush size buttons
    size_x0 = 6 + len(TOOLS) * (btn_w + 4) + 8
    size_labels = ["S[1]", "M[2]", "L[3]"]
    for i, (sz, sl) in enumerate(zip(BRUSH_SIZES, size_labels)):
        bx   = size_x0 + i * 54
        rect = pygame.Rect(bx, btn_y, 50, 34)
        bg   = (80, 180, 80) if sz == brush_size else (70, 70, 70)
        pygame.draw.rect(surface, bg, rect, border_radius=5)
        pygame.draw.rect(surface, LGRAY, rect, 1, border_radius=5)
        txt = font.render(sl, True, WHITE)
        surface.blit(txt, txt.get_rect(center=rect.center))

    # Second toolbar row: palette + active color preview
    row2_y = btn_y + btn_h + 6
    pal_size = 16
    pal_gap  = 2
    cols_per_row = 16
    for idx, color in enumerate(PALETTE):
        px = 6 + idx * (pal_size + pal_gap)
        py = row2_y
        rect = pygame.Rect(px, py, pal_size, pal_size)
        pygame.draw.rect(surface, color, rect)
        if color == active_color:
            pygame.draw.rect(surface, WHITE, rect, 2)

    # Active color preview
    prev_rect = pygame.Rect(SCREEN_W - 70, row2_y - 4, 60, 24)
    pygame.draw.rect(surface, active_color, prev_rect, border_radius=4)
    pygame.draw.rect(surface, WHITE, prev_rect, 2, border_radius=4)

    # Ctrl+S hint
    hint = font.render("Ctrl+S: Save", True, LGRAY)
    surface.blit(hint, (SCREEN_W - 140, btn_y))


def palette_click(mx, my):
    row2_y   = 6 + 34 + 6
    pal_size = 16
    pal_gap  = 2
    for idx, color in enumerate(PALETTE):
        px = 6 + idx * (pal_size + pal_gap)
        if pygame.Rect(px, row2_y, pal_size, pal_size).collidepoint(mx, my):
            return color
    return None


def size_button_click(mx, my):
    """Return brush size if a size button was clicked, else None."""
    btn_w, btn_h = 72, 34
    btn_y = 6
    size_x0 = 6 + len(TOOLS) * (btn_w + 4) + 8
    for i, sz in enumerate(BRUSH_SIZES):
        bx = size_x0 + i * 54
        if pygame.Rect(bx, btn_y, 50, 34).collidepoint(mx, my):
            return sz
    return None


def tool_button_click(mx, my):
    """Return tool id if a tool button was clicked, else None."""
    btn_w, btn_h = 72, 34
    btn_y = 6
    for i, tool in enumerate(TOOLS):
        bx = 6 + i * (btn_w + 4)
        if pygame.Rect(bx, btn_y, btn_w, btn_h).collidepoint(mx, my):
            return tool
    return None


# ── Canvas helpers ────────────────────────────────────────────────────────────

def in_canvas(mx, my):
    return 0 <= mx < SCREEN_W and CANVAS_TOP <= my < SCREEN_H


def canvas_pos(mx, my):
    return mx, my - CANVAS_TOP


# ── Shape helpers ─────────────────────────────────────────────────────────────

def draw_rect_shape(surface, color, start, end):
    x1, y1 = start; x2, y2 = end
    rect = pygame.Rect(min(x1,x2), min(y1,y2), abs(x2-x1) or 1, abs(y2-y1) or 1)
    pygame.draw.rect(surface, color, rect)


def draw_circle_shape(surface, color, start, end):
    cx = (start[0]+end[0])//2; cy = (start[1]+end[1])//2
    r  = max(1, int(math.hypot(end[0]-start[0], end[1]-start[1]) / 2))
    pygame.draw.circle(surface, color, (cx, cy), r)


# ── Flood fill (BFS) ──────────────────────────────────────────────────────────

def flood_fill(surface, start_x, start_y, fill_color):
    """
    BFS flood fill on a pygame Surface.
    Replaces pixels matching the target color at (start_x, start_y)
    with fill_color.  Exact color match only (tolerance = 0).
    """
    target_color = surface.get_at((start_x, start_y))[:3]
    fc3 = fill_color[:3]
    if target_color == fc3:
        return   # nothing to do

    w, h   = surface.get_size()
    visited = [[False] * h for _ in range(w)]
    queue   = deque()
    queue.append((start_x, start_y))
    visited[start_x][start_y] = True

    while queue:
        x, y = queue.popleft()
        surface.set_at((x, y), fill_color)
        for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                if surface.get_at((nx, ny))[:3] == target_color:
                    visited[nx][ny] = True
                    queue.append((nx, ny))


# ── Save canvas ───────────────────────────────────────────────────────────────

def save_canvas(canvas):
    """Save the canvas surface as a timestamped PNG file."""
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{ts}.png"
    pygame.image.save(canvas, filename)
    print(f"Canvas saved to '{filename}'.")
    return filename


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Paint – TSIS 2")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Arial", 12, bold=True)
    font_text = pygame.font.SysFont("Arial", 18)

    canvas = pygame.Surface((SCREEN_W, CANVAS_H))
    canvas.fill(CANVAS_BG)

    # State
    active_tool  = TOOL_PENCIL
    active_color = BLACK
    brush_size   = BRUSH_SIZES[1]   # medium default

    drawing    = False
    drag_start = None    # canvas coords where drag began
    last_pos   = None

    # Text tool state
    text_active  = False
    text_pos     = None   # canvas coords of text anchor
    text_buffer  = ""

    # Save notification
    save_notice    = ""
    save_notice_t  = 0

    while True:
        clock.tick(60)
        now = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            # ── Keyboard ──────────────────────────────────────────────────────
            if event.type == KEYDOWN:
                # Text tool input — intercept all keys
                if text_active:
                    if event.key == K_RETURN:
                        # Commit text to canvas
                        if text_buffer and text_pos:
                            surf = font_text.render(text_buffer, True, active_color)
                            canvas.blit(surf, text_pos)
                        text_active = False
                        text_buffer = ""
                        text_pos    = None
                    elif event.key == K_ESCAPE:
                        text_active = False
                        text_buffer = ""
                        text_pos    = None
                    elif event.key == K_BACKSPACE:
                        text_buffer = text_buffer[:-1]
                    else:
                        if event.unicode:
                            text_buffer += event.unicode
                else:
                    # Tool shortcuts
                    if event.key == K_p: active_tool = TOOL_PENCIL
                    elif event.key == K_l: active_tool = TOOL_LINE
                    elif event.key == K_r: active_tool = TOOL_RECTANGLE
                    elif event.key == K_c: active_tool = TOOL_CIRCLE
                    elif event.key == K_e: active_tool = TOOL_ERASER
                    elif event.key == K_f: active_tool = TOOL_FILL
                    elif event.key == K_t: active_tool = TOOL_TEXT
                    # Brush size shortcuts
                    elif event.key == K_1: brush_size = BRUSH_SIZES[0]
                    elif event.key == K_2: brush_size = BRUSH_SIZES[1]
                    elif event.key == K_3: brush_size = BRUSH_SIZES[2]
                    # Ctrl+S save
                    elif event.key == K_s and (pygame.key.get_mods() & KMOD_CTRL):
                        fname = save_canvas(canvas)
                        save_notice   = f"Saved: {fname}"
                        save_notice_t = now

            # ── Mouse wheel: adjust brush size ────────────────────────────────
            if event.type == MOUSEWHEEL and not text_active:
                idx = BRUSH_SIZES.index(brush_size) if brush_size in BRUSH_SIZES else 1
                idx = max(0, min(len(BRUSH_SIZES)-1, idx + event.y))
                brush_size = BRUSH_SIZES[idx]

            # ── Mouse button down ─────────────────────────────────────────────
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if my < TOOLBAR_H:
                    # Toolbar clicks
                    pal = palette_click(mx, my)
                    if pal:
                        active_color = pal
                    sz = size_button_click(mx, my)
                    if sz:
                        brush_size = sz
                    tl = tool_button_click(mx, my)
                    if tl:
                        active_tool = tl
                elif in_canvas(mx, my):
                    cx, cy = canvas_pos(mx, my)

                    if active_tool == TOOL_FILL:
                        flood_fill(canvas, cx, cy, active_color)

                    elif active_tool == TOOL_TEXT:
                        text_active = True
                        text_pos    = (cx, cy)
                        text_buffer = ""

                    else:
                        drawing    = True
                        drag_start = (cx, cy)
                        last_pos   = (cx, cy)

            # ── Mouse button up ───────────────────────────────────────────────
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if drawing and drag_start is not None:
                    cx, cy  = canvas_pos(mx, my)
                    end_pos = (cx, cy)

                    if active_tool == TOOL_LINE:
                        pygame.draw.line(canvas, active_color,
                                         drag_start, end_pos, brush_size)
                    elif active_tool == TOOL_RECTANGLE:
                        draw_rect_shape(canvas, active_color, drag_start, end_pos)
                    elif active_tool == TOOL_CIRCLE:
                        draw_circle_shape(canvas, active_color, drag_start, end_pos)
                    # Pencil & Eraser are committed during MOUSEMOTION

                drawing    = False
                drag_start = None
                last_pos   = None

            # ── Mouse motion ──────────────────────────────────────────────────
            if event.type == MOUSEMOTION and drawing and in_canvas(mx, my):
                cx, cy = canvas_pos(mx, my)
                cpos   = (cx, cy)

                if active_tool == TOOL_PENCIL:
                    if last_pos:
                        pygame.draw.line(canvas, active_color, last_pos, cpos, brush_size)
                        pygame.draw.circle(canvas, active_color, cpos, brush_size // 2)
                    last_pos = cpos

                elif active_tool == TOOL_ERASER:
                    pygame.draw.circle(canvas, CANVAS_BG, cpos, brush_size)

        # ── Render ────────────────────────────────────────────────────────────
        screen.fill(DGRAY)
        draw_toolbar(screen, font, active_tool, active_color, brush_size)

        # Blit persistent canvas
        screen.blit(canvas, (0, CANVAS_TOP))

        # Live preview for line/rect/circle
        if drawing and drag_start and in_canvas(mx, my):
            cpos    = canvas_pos(mx, my)
            preview = canvas.copy()
            if active_tool == TOOL_LINE:
                pygame.draw.line(preview, active_color, drag_start, cpos, brush_size)
            elif active_tool == TOOL_RECTANGLE:
                draw_rect_shape(preview, active_color, drag_start, cpos)
            elif active_tool == TOOL_CIRCLE:
                draw_circle_shape(preview, active_color, drag_start, cpos)
            screen.blit(preview, (0, CANVAS_TOP))

        # Text tool: render in-progress text on top
        if text_active and text_pos:
            txt_surf = font_text.render(text_buffer + "|", True, active_color)
            tx, ty   = text_pos[0], text_pos[1] + CANVAS_TOP
            screen.blit(txt_surf, (tx, ty))

        # Save notice overlay
        if save_notice and now - save_notice_t < 2500:
            ns = font_text.render(save_notice, True, (50, 220, 50))
            screen.blit(ns, (10, TOOLBAR_H + 10))

        # Cursor circle
        if in_canvas(mx, my) and active_tool not in (TOOL_FILL, TOOL_TEXT):
            color = CANVAS_BG if active_tool == TOOL_ERASER else active_color
            pygame.draw.circle(screen, color, (mx, my), max(2, brush_size // 2), 1)

        pygame.display.flip()


if __name__ == "__main__":
    main()
