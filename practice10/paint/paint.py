"""
Practice 10 - Task 3: Paint Application
Extended from the nerdparadise.com PyGame tutorial (part 6).
Extra features added:
  1. Draw Rectangle  – click and drag to draw a filled rectangle
  2. Draw Circle     – click and drag to draw a filled circle
  3. Eraser          – paints over canvas with the background colour
  4. Color Selection – a palette of 16 preset colours; click to choose
  Full comments throughout the code.
"""

import pygame
import sys
import math
from pygame.locals import *

# ── Layout Constants ───────────────────────────────────────────────────────────
SCREEN_W   = 900    # total window width
SCREEN_H   = 650    # total window height
TOOLBAR_H  = 80     # height of the top toolbar (tools + palette)
CANVAS_TOP = TOOLBAR_H
CANVAS_H   = SCREEN_H - TOOLBAR_H  # height of the drawable canvas area

# Background colour used for the canvas (also what the eraser paints)
CANVAS_BG  = (240, 240, 240)

# ── Colours ────────────────────────────────────────────────────────────────────
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
DGRAY  = (50,  50,  50)
LGRAY  = (180, 180, 180)
MGRAY  = (120, 120, 120)

# The 16-colour palette shown to the user
PALETTE = [
    (0,   0,   0),     (255, 255, 255),  (128, 128, 128),  (192, 192, 192),
    (255, 0,   0),     (180, 0,   0),    (255, 128, 0),    (255, 220, 0),
    (0,   200, 0),     (0,   100, 0),    (0,   200, 200),  (0,   0,   255),
    (0,   0,   180),   (180, 0,   200),  (255, 100, 150),  (139, 69,  19),
]

# ── Tool IDs ───────────────────────────────────────────────────────────────────
TOOL_PEN       = "pen"
TOOL_RECTANGLE = "rect"
TOOL_CIRCLE    = "circle"
TOOL_ERASER    = "eraser"

TOOLS = [TOOL_PEN, TOOL_RECTANGLE, TOOL_CIRCLE, TOOL_ERASER]

# Labels and keyboard shortcuts for each tool
TOOL_LABELS = {
    TOOL_PEN:       ("Pen",  "P"),
    TOOL_RECTANGLE: ("Rect", "R"),
    TOOL_CIRCLE:    ("Circ", "C"),
    TOOL_ERASER:    ("Erase","E"),
}

# ── Toolbar Drawing ────────────────────────────────────────────────────────────
def draw_toolbar(surface, font, active_tool, active_color, brush_size):
    """
    Renders the toolbar band at the top of the window:
      - Tool buttons (Pen, Rect, Circle, Eraser)
      - Current brush-size indicator
      - 16-colour palette squares
      - Active colour preview
    """
    # Toolbar background
    pygame.draw.rect(surface, DGRAY, (0, 0, SCREEN_W, TOOLBAR_H))
    pygame.draw.line(surface, LGRAY, (0, TOOLBAR_H - 1), (SCREEN_W, TOOLBAR_H - 1), 2)

    # ── Tool buttons ──────────────────────────────────────────────────────────
    btn_w, btn_h = 70, 36
    btn_y = 8
    for i, tool in enumerate(TOOLS):
        btn_x = 10 + i * (btn_w + 6)
        rect  = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        # Highlighted background for the active tool
        bg = (80, 130, 200) if tool == active_tool else (70, 70, 70)
        pygame.draw.rect(surface, bg, rect, border_radius=6)
        pygame.draw.rect(surface, LGRAY, rect, 1, border_radius=6)

        label, shortcut = TOOL_LABELS[tool]
        txt = font.render(f"{label} [{shortcut}]", True, WHITE)
        surface.blit(txt, txt.get_rect(center=rect.center))

    # ── Brush size display ─────────────────────────────────────────────────────
    size_x = 10 + len(TOOLS) * (btn_w + 6) + 10
    size_label = font.render(f"Size: {brush_size}", True, WHITE)
    surface.blit(size_label, (size_x, btn_y))
    hint = font.render("scroll ↑↓", True, LGRAY)
    surface.blit(hint, (size_x, btn_y + 18))

    # ── Active colour preview (large square) ──────────────────────────────────
    preview_x = SCREEN_W - 220
    preview_rect = pygame.Rect(preview_x, 8, 48, 48)
    pygame.draw.rect(surface, active_color, preview_rect, border_radius=4)
    pygame.draw.rect(surface, WHITE, preview_rect, 2, border_radius=4)
    lbl = font.render("Color", True, WHITE)
    surface.blit(lbl, (preview_x + 52, 20))

    # ── Palette ────────────────────────────────────────────────────────────────
    pal_x0 = SCREEN_W - 160
    pal_size = 16     # pixel size of each colour swatch
    pal_gap  = 2
    cols_per_row = 8
    for idx, color in enumerate(PALETTE):
        col = idx % cols_per_row
        row = idx // cols_per_row
        px  = pal_x0 + col * (pal_size + pal_gap)
        py  = 8       + row * (pal_size + pal_gap)
        rect = pygame.Rect(px, py, pal_size, pal_size)
        pygame.draw.rect(surface, color, rect)
        if color == active_color:
            pygame.draw.rect(surface, WHITE, rect, 2)


def palette_click(mx, my):
    """
    Returns the colour under the mouse if it clicked the palette area,
    otherwise None.
    """
    pal_x0   = SCREEN_W - 160
    pal_size = 16
    pal_gap  = 2
    cols_per_row = 8

    for idx, color in enumerate(PALETTE):
        col = idx % cols_per_row
        row = idx // cols_per_row
        px  = pal_x0 + col * (pal_size + pal_gap)
        py  = 8       + row * (pal_size + pal_gap)
        if pygame.Rect(px, py, pal_size, pal_size).collidepoint(mx, my):
            return color
    return None


# ── Canvas Helpers ─────────────────────────────────────────────────────────────
def canvas_pos(mx, my):
    """Convert screen (mx, my) to canvas coordinates."""
    return mx, my - CANVAS_TOP


def in_canvas(mx, my):
    """Return True if the mouse is within the drawable canvas area."""
    return 0 <= mx < SCREEN_W and CANVAS_TOP <= my < SCREEN_H


# ── Shape Drawing Helpers ──────────────────────────────────────────────────────
def draw_rect_shape(surface, color, start, end, brush_size):
    """
    Draw a filled rectangle from start to end.
    An outline with the same colour but width=brush_size is drawn around it.
    """
    x1, y1 = start
    x2, y2 = end
    rect = pygame.Rect(min(x1, x2), min(y1, y2),
                       abs(x2 - x1) or 1, abs(y2 - y1) or 1)
    pygame.draw.rect(surface, color, rect)


def draw_circle_shape(surface, color, start, end):
    """
    Draw a filled circle whose diameter is the distance from start to end.
    Centre is the midpoint; radius is half the distance.
    """
    cx = (start[0] + end[0]) // 2
    cy = (start[1] + end[1]) // 2
    radius = max(1, int(math.hypot(end[0] - start[0],
                                    end[1] - start[1]) / 2))
    pygame.draw.circle(surface, color, (cx, cy), radius)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Paint – Practice 10")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Arial", 13, bold=True)

    # The canvas is a persistent Surface that accumulates drawn content.
    # We blit it onto the screen each frame, then draw any in-progress
    # shape preview on top.
    canvas = pygame.Surface((SCREEN_W, CANVAS_H))
    canvas.fill(CANVAS_BG)

    # ── State variables ───────────────────────────────────────────────────────
    active_tool   = TOOL_PEN
    active_color  = BLACK
    brush_size    = 5

    drawing       = False   # True while the left mouse button is held
    drag_start    = None    # screen position where drag began (for shapes)
    last_pos      = None    # last mouse pos (for continuous pen/eraser drawing)

    while True:
        clock.tick(60)

        mx, my = pygame.mouse.get_pos()

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # ── Keyboard shortcuts ─────────────────────────────────────────
            if event.type == KEYDOWN:
                if event.key == K_p:
                    active_tool = TOOL_PEN
                elif event.key == K_r:
                    active_tool = TOOL_RECTANGLE
                elif event.key == K_c:
                    active_tool = TOOL_CIRCLE
                elif event.key == K_e:
                    active_tool = TOOL_ERASER

            # ── Scroll wheel: adjust brush size ───────────────────────────
            if event.type == MOUSEWHEEL:
                brush_size = max(1, min(60, brush_size + event.y))

            # ── Mouse button down ──────────────────────────────────────────
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                # Check if user clicked in the toolbar
                if my < TOOLBAR_H:
                    # Palette click?
                    pal_color = palette_click(mx, my)
                    if pal_color is not None:
                        active_color = pal_color
                    # Tool button click?
                    btn_w, btn_h = 70, 36
                    for i, tool in enumerate(TOOLS):
                        btn_rect = pygame.Rect(10 + i * (btn_w + 6), 8, btn_w, btn_h)
                        if btn_rect.collidepoint(mx, my):
                            active_tool = tool
                else:
                    # Start drawing on the canvas
                    drawing    = True
                    drag_start = (mx, my - CANVAS_TOP)   # canvas coords
                    last_pos   = drag_start

            # ── Mouse button up ────────────────────────────────────────────
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if drawing and drag_start is not None:
                    end_pos = (mx, my - CANVAS_TOP)

                    # Commit the finished shape onto the persistent canvas
                    if active_tool == TOOL_RECTANGLE:
                        draw_rect_shape(canvas, active_color,
                                        drag_start, end_pos, brush_size)
                    elif active_tool == TOOL_CIRCLE:
                        draw_circle_shape(canvas, active_color,
                                          drag_start, end_pos)
                    # Pen and Eraser are painted directly during MOUSEMOTION

                drawing    = False
                drag_start = None
                last_pos   = None

            # ── Mouse motion ───────────────────────────────────────────────
            if event.type == MOUSEMOTION and drawing and in_canvas(mx, my):
                cpos = (mx, my - CANVAS_TOP)

                if active_tool == TOOL_PEN:
                    # Draw a line segment between the last and current positions
                    if last_pos is not None:
                        pygame.draw.line(canvas, active_color,
                                         last_pos, cpos, brush_size)
                        # Circle at the end to smooth the stroke
                        pygame.draw.circle(canvas, active_color,
                                           cpos, brush_size // 2)
                    last_pos = cpos

                elif active_tool == TOOL_ERASER:
                    # Paint over with the canvas background colour
                    pygame.draw.circle(canvas, CANVAS_BG, cpos, brush_size)

        # ── Drawing ───────────────────────────────────────────────────────────
        # 1. Draw toolbar
        screen.fill(DGRAY)
        draw_toolbar(screen, font, active_tool, active_color, brush_size)

        # 2. Blit the persistent canvas
        screen.blit(canvas, (0, CANVAS_TOP))

        # 3. Draw in-progress shape preview on top (for rect / circle)
        if drawing and drag_start is not None and in_canvas(mx, my):
            current_pos = (mx, my - CANVAS_TOP)

            # Temporary surface so we don't permanently draw the preview
            preview = canvas.copy()
            if active_tool == TOOL_RECTANGLE:
                draw_rect_shape(preview, active_color,
                                drag_start, current_pos, brush_size)
            elif active_tool == TOOL_CIRCLE:
                draw_circle_shape(preview, active_color,
                                  drag_start, current_pos)
            screen.blit(preview, (0, CANVAS_TOP))

        # 4. Draw custom cursor (a circle showing brush size)
        if in_canvas(mx, my):
            color = CANVAS_BG if active_tool == TOOL_ERASER else active_color
            pygame.draw.circle(screen, color, (mx, my), max(2, brush_size // 2), 1)

        pygame.display.flip()


if __name__ == "__main__":
    main()
