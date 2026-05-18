import json
import threading
from typing import Optional, List, Dict, Any
from backend.database import get_db

_lock = threading.Lock()


def create_task(task_id: str, task_type: str, data_source: str,
                requirements: Dict[str, Any], api_key: Optional[str] = None) -> Dict:
    with _lock:
        conn = get_db()
        conn.execute(
            "INSERT INTO tasks (task_id, task_type, data_source, requirements, api_key) VALUES (?,?,?,?,?)",
            (task_id, task_type, data_source, json.dumps(requirements, ensure_ascii=False), api_key)
        )
        conn.commit()
        conn.close()
    return get_task(task_id)


def get_task(task_id: str) -> Optional[Dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_dict(row)


def update_task(task_id: str, **kwargs):
    if not kwargs:
        return
    valid = {"status", "phase", "progress_pct", "current_step", "message",
             "results", "report", "error", "updated_at"}
    fields = {k: v for k, v in kwargs.items() if k in valid}
    if not fields:
        return
    fields["updated_at"] = "datetime('now','localtime')"
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values())
    with _lock:
        conn = get_db()
        conn.execute(f"UPDATE tasks SET {sets} WHERE task_id=?", vals + [task_id])
        conn.commit()
        conn.close()


def list_tasks(limit: int = 50) -> List[Dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def delete_task(task_id: str):
    with _lock:
        conn = get_db()
        conn.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM task_steps WHERE task_id=?", (task_id,))
        conn.commit()
        conn.close()


def add_step(task_id: str, step_name: str, detail: str = ""):
    with _lock:
        conn = get_db()
        conn.execute(
            "INSERT INTO task_steps (task_id, step_name, started_at, detail) VALUES (?,?,datetime('now','localtime'),?)",
            (task_id, step_name, detail)
        )
        conn.commit()
        conn.close()


def _row_to_dict(row) -> Dict:
    d = dict(row)
    for field in ("results", "report", "requirements"):
        if d.get(field) and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except json.JSONDecodeError:
                pass
    return d
