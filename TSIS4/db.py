# db.py  (TSIS 4)
# Handles all PostgreSQL interactions for the Snake leaderboard.
# Schema (run once):
#
#   CREATE TABLE players (
#       id       SERIAL PRIMARY KEY,
#       username VARCHAR(50) UNIQUE NOT NULL
#   );
#   CREATE TABLE game_sessions (
#       id           SERIAL PRIMARY KEY,
#       player_id    INTEGER REFERENCES players(id),
#       score        INTEGER NOT NULL,
#       level_reached INTEGER NOT NULL,
#       played_at    TIMESTAMP DEFAULT NOW()
#   );

import psycopg2
from config import DB_CONFIG


def _connect():
    return psycopg2.connect(**DB_CONFIG)


def ensure_schema():
    """Create tables if they don't exist yet."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id       SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id            SERIAL PRIMARY KEY,
                    player_id     INTEGER REFERENCES players(id),
                    score         INTEGER NOT NULL,
                    level_reached INTEGER NOT NULL,
                    played_at     TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()


def get_or_create_player(username):
    """Return player id, creating the player row if needed."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                "INSERT INTO players (username) VALUES (%s) RETURNING id;",
                (username,)
            )
            pid = cur.fetchone()[0]
        conn.commit()
    return pid


def save_result(username, score, level_reached):
    """Save a game result for the given username."""
    pid = get_or_create_player(username)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO game_sessions (player_id, score, level_reached)
                VALUES (%s, %s, %s);
            """, (pid, score, level_reached))
        conn.commit()


def get_top10():
    """Return list of (rank, username, score, level, date) top-10 all-time."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.username, gs.score, gs.level_reached,
                       gs.played_at::date
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT 10;
            """)
            rows = cur.fetchall()
    return rows


def get_personal_best(username):
    """Return the player's highest score, or 0 if no games played."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(gs.score)
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                WHERE p.username = %s;
            """, (username,))
            row = cur.fetchone()
    return row[0] if row and row[0] is not None else 0
