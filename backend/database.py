import sqlite3
import threading
from backend.config import DB_PATH

_lock = threading.Lock()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with _lock:
        conn = get_db()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id       TEXT PRIMARY KEY,
                task_type     TEXT NOT NULL,
                data_source   TEXT NOT NULL,
                requirements  TEXT NOT NULL DEFAULT '{}',
                status        TEXT DEFAULT 'pending',
                phase         TEXT DEFAULT 'idle',
                progress_pct  REAL DEFAULT 0.0,
                current_step  TEXT DEFAULT '',
                message       TEXT DEFAULT '',
                results       TEXT,
                report        TEXT,
                error         TEXT,
                api_key       TEXT,
                created_at    TEXT DEFAULT (datetime('now','localtime')),
                updated_at    TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS task_steps (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id       TEXT NOT NULL,
                step_name     TEXT NOT NULL,
                status        TEXT DEFAULT 'running',
                started_at    TEXT,
                completed_at  TEXT DEFAULT (datetime('now','localtime')),
                detail        TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        conn.close()
