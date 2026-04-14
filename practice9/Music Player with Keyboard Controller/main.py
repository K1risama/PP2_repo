import pygame
import sys
import os
import time

# Initialize pygame and mixer
pygame.init()
pygame.mixer.init()

# Screen settings
WIDTH, HEIGHT = 520, 420
FPS = 30

# Colors
BG = (18, 18, 28)
PANEL = (28, 28, 42)
ACCENT = (100, 200, 255)
WHITE = (240, 240, 240)
GRAY = (130, 130, 150)
DARK_GRAY = (60, 60, 80)
GREEN = (80, 210, 120)
RED = (220, 80, 80)


def find_tracks(music_folder="music"):
    """Find all MP3 and WAV files in the music folder."""
    supported = (".mp3", ".wav", ".ogg")
    tracks = []
    if os.path.isdir(music_folder):
        for f in sorted(os.listdir(music_folder)):
            if f.lower().endswith(supported):
                tracks.append(os.path.join(music_folder, f))
    return tracks


def get_track_name(path):
    """Return clean filename without extension."""
    return os.path.splitext(os.path.basename(path))[0]


def draw_progress_bar(surface, x, y, w, h, progress, color_bg, color_fill):
    """Draw a simple progress bar (0.0 to 1.0)."""
    pygame.draw.rect(surface, color_bg, (x, y, w, h), border_radius=h // 2)
    fill_w = int(w * max(0.0, min(1.0, progress)))
    if fill_w > 0:
        pygame.draw.rect(surface, color_fill, (x, y, fill_w, h), border_radius=h // 2)


def wrap_text(text, font, max_width):
    """Wrap text into lines that fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Music Player")
    clock = pygame.time.Clock()

    # Fonts
    font_title = pygame.font.SysFont("Courier New", 22, bold=True)
    font_track = pygame.font.SysFont("Arial", 17, bold=True)
    font_info = pygame.font.SysFont("Arial", 14)
    font_keys = pygame.font.SysFont("Courier New", 13)

    # Load tracks
    tracks = find_tracks("music")
    current_index = 0
    is_playing = False
    play_start_time = 0.0
    track_position = 0.0   # seconds elapsed
    track_length = 0.0     # total seconds (estimated)

    def load_track(index):
        """Load and optionally prepare the track at given index."""
        nonlocal track_length
        if not tracks:
            return
        try:
            pygame.mixer.music.load(tracks[index])
            # pygame doesn't expose duration directly; we leave it at 0 if unavailable
            track_length = 0.0
        except Exception as e:
            print(f"Error loading track: {e}")

    def play_current():
        nonlocal is_playing, play_start_time, track_position
        if not tracks:
            return
        load_track(current_index)
        pygame.mixer.music.play()
        is_playing = True
        play_start_time = time.time()
        track_position = 0.0

    def stop_music():
        nonlocal is_playing, track_position
        pygame.mixer.music.stop()
        is_playing = False
        track_position = 0.0

    def next_track():
        nonlocal current_index
        if not tracks:
            return
        current_index = (current_index + 1) % len(tracks)
        if is_playing:
            play_current()
        else:
            load_track(current_index)

    def prev_track():
        nonlocal current_index
        if not tracks:
            return
        current_index = (current_index - 1) % len(tracks)
        if is_playing:
            play_current()
        else:
            load_track(current_index)

    # Pre-load first track if available
    if tracks:
        load_track(current_index)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:          # Play / Resume
                    if not is_playing:
                        play_current()
                elif event.key == pygame.K_s:        # Stop
                    stop_music()
                elif event.key == pygame.K_n:        # Next
                    next_track()
                elif event.key == pygame.K_b:        # Back (Previous)
                    prev_track()
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Auto-advance when track ends
        if is_playing and not pygame.mixer.music.get_busy():
            next_track()

        # Update elapsed time
        if is_playing:
            track_position = time.time() - play_start_time

        # ── Draw ──────────────────────────────────────────
        screen.fill(BG)

        # Title bar
        pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 60))
        title_surf = font_title.render("♪  MUSIC PLAYER", True, ACCENT)
        screen.blit(title_surf, (20, 18))

        # Status indicator
        status_text = "● PLAYING" if is_playing else "■ STOPPED"
        status_color = GREEN if is_playing else RED
        status_surf = font_info.render(status_text, True, status_color)
        screen.blit(status_surf, (WIDTH - status_surf.get_width() - 20, 22))

        # Track count
        if tracks:
            count_text = f"Track {current_index + 1} / {len(tracks)}"
        else:
            count_text = "No tracks found"
        count_surf = font_info.render(count_text, True, GRAY)
        screen.blit(count_surf, (WIDTH - count_surf.get_width() - 20, 40))

        # Track name display
        pygame.draw.rect(screen, PANEL, (20, 80, WIDTH - 40, 80), border_radius=10)
        if tracks:
            name = get_track_name(tracks[current_index])
            lines = wrap_text(name, font_track, WIDTH - 80)
            for i, line in enumerate(lines[:3]):
                surf = font_track.render(line, True, WHITE)
                screen.blit(surf, (40, 90 + i * 24))
        else:
            no_track = font_track.render("No music files in ./music/", True, GRAY)
            screen.blit(no_track, (40, 100))

        # Progress bar
        bar_y = 180
        elapsed_str = f"{int(track_position // 60):02d}:{int(track_position % 60):02d}"
        elapsed_surf = font_info.render(elapsed_str, True, GRAY)
        screen.blit(elapsed_surf, (20, bar_y - 22))

        # Indeterminate progress — just animate a pulse when playing
        if is_playing:
            pulse = (track_position % 4) / 4.0
        else:
            pulse = 0.0
        draw_progress_bar(screen, 20, bar_y, WIDTH - 40, 8, pulse, DARK_GRAY, ACCENT)

        # Playlist (show up to 5 tracks)
        pygame.draw.rect(screen, PANEL, (20, 210, WIDTH - 40, 130), border_radius=8)
        list_title = font_info.render("PLAYLIST", True, ACCENT)
        screen.blit(list_title, (36, 218))

        display_tracks = tracks if tracks else []
        start = max(0, current_index - 2)
        visible = display_tracks[start: start + 5]
        for i, t in enumerate(visible):
            actual_index = start + i
            color = WHITE if actual_index == current_index else GRAY
            prefix = "▶ " if actual_index == current_index else "  "
            name = get_track_name(t)
            if len(name) > 44:
                name = name[:41] + "..."
            surf = font_info.render(f"{prefix}{actual_index + 1}. {name}", True, color)
            screen.blit(surf, (36, 236 + i * 20))

        # Controls legend
        pygame.draw.rect(screen, PANEL, (20, 355, WIDTH - 40, 50), border_radius=8)
        controls = "[P] Play   [S] Stop   [N] Next   [B] Back   [Q] Quit"
        ctrl_surf = font_keys.render(controls, True, GRAY)
        screen.blit(ctrl_surf, ((WIDTH - ctrl_surf.get_width()) // 2, 372))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
