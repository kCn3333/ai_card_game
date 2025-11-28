import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent.parent / "ai_card_game.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    # Settings table (key-value)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    # Game statistics table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS game_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            game_type TEXT NOT NULL,
            ai_model TEXT,
            difficulty TEXT,
            result TEXT NOT NULL,
            rounds_played INTEGER,
            player_final_score INTEGER,
            ai_final_score INTEGER
        )
        """
    )

    conn.commit()
    conn.close()
