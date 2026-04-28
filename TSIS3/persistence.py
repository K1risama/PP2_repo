# persistence.py  (TSIS 3)
# Handles saving/loading of leaderboard and settings to JSON files.

import json
import os
from datetime import datetime

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"

DEFAULT_SETTINGS = {
    "sound":      True,
    "car_color":  [30, 100, 220],   # RGB list (blue)
    "difficulty": "normal",         # easy / normal / hard
}


# ── Leaderboard ───────────────────────────────────────────────────────────────

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    with open(LEADERBOARD_FILE, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_score(username, score, distance):
    board = load_leaderboard()
    board.append({
        "name":     username,
        "score":    score,
        "distance": distance,
        "date":     datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    # Keep only top 10
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:10]
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, indent=2)
    return board


# ── Settings ──────────────────────────────────────────────────────────────────

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Merge with defaults so missing keys always exist
            merged = dict(DEFAULT_SETTINGS)
            merged.update(data)
            return merged
        except json.JSONDecodeError:
            return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
