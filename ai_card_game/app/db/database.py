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


def save_game_result(game_type: str, result: str, player_score: int, ai_score: int, ai_model: str = "") -> None:
    """Save a game result to the database."""
    from datetime import datetime
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO game_stats (created_at, game_type, ai_model, result, player_final_score, ai_final_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (datetime.now().isoformat(), game_type, ai_model, result, player_score, ai_score)
    )
    conn.commit()
    conn.close()


def get_statistics() -> dict:
    """Get aggregated game statistics."""
    conn = get_connection()
    cur = conn.cursor()
    
    stats = {
        "total_games": 0,
        "wins": 0,
        "losses": 0,
        "pushes": 0,
        "win_rate": 0.0,
        "recent_games": []
    }
    
    # Total counts
    cur.execute("SELECT COUNT(*) FROM game_stats")
    stats["total_games"] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM game_stats WHERE result = 'win'")
    stats["wins"] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM game_stats WHERE result = 'loss'")
    stats["losses"] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM game_stats WHERE result = 'push'")
    stats["pushes"] = cur.fetchone()[0]
    
    if stats["total_games"] > 0:
        stats["win_rate"] = (stats["wins"] / stats["total_games"]) * 100
    
    # Recent games (last 10)
    cur.execute(
        """
        SELECT created_at, game_type, result, player_final_score, ai_final_score
        FROM game_stats ORDER BY id DESC LIMIT 10
        """
    )
    stats["recent_games"] = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    return stats
