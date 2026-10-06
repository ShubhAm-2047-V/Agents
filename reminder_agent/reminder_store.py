"""
reminder_store.py
Local SQLite storage for Orion's comprehensive scheduling and reminder system.
Supports Categories, Priorities, Snoozing, Recurrence, and Condition-based triggers.
"""

import sqlite3
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "reminders.db")
VALID_RECURRENCE = {None, "daily", "weekly", "monthly", "weekdays", "yearly"}


def init_db():
    """Initializes and migrates the reminders database table."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            due_at TEXT NOT NULL,
            recurrence TEXT,
            category TEXT DEFAULT 'general',
            priority INTEGER DEFAULT 2,
            condition TEXT DEFAULT NULL,
            created_at TEXT,
            completed INTEGER DEFAULT 0,
            last_fired_at TEXT
        )
    """)
    conn.commit()

    # Migration for new columns
    cur.execute("PRAGMA table_info(reminders)")
    cols = [c[1] for c in cur.fetchall()]
    if "category" not in cols:
        cur.execute("ALTER TABLE reminders ADD COLUMN category TEXT DEFAULT 'general'")
    if "priority" not in cols:
        cur.execute("ALTER TABLE reminders ADD COLUMN priority INTEGER DEFAULT 2")
    if "condition" not in cols:
        cur.execute("ALTER TABLE reminders ADD COLUMN condition TEXT DEFAULT NULL")

    conn.commit()
    conn.close()


def add_reminder(
    message: str,
    due_at: Any,
    recurrence: Optional[str] = None,
    category: str = "general",
    priority: int = 2,
    condition: Optional[str] = None
) -> int:
    """Adds a new reminder with priority, category, and optional trigger condition."""
    init_db()
    if recurrence and recurrence not in VALID_RECURRENCE:
        recurrence = None

    if isinstance(due_at, datetime):
        due_at_str = due_at.isoformat()
    else:
        due_at_str = str(due_at)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO reminders 
           (message, due_at, recurrence, category, priority, condition, created_at, completed) 
           VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            message.strip(),
            due_at_str,
            recurrence,
            category.lower().strip(),
            max(1, min(4, int(priority))),
            condition,
            datetime.now().isoformat()
        )
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def modify_reminder(
    reminder_id: int,
    message: Optional[str] = None,
    due_at: Optional[Any] = None,
    recurrence: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[int] = None,
    condition: Optional[str] = None
) -> bool:
    """Modifies an existing reminder's parameters."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    updates = []
    params = []
    if message is not None:
        updates.append("message = ?")
        params.append(message.strip())
    if due_at is not None:
        updates.append("due_at = ?")
        params.append(due_at.isoformat() if isinstance(due_at, datetime) else str(due_at))
    if recurrence is not None:
        updates.append("recurrence = ?")
        params.append(recurrence if recurrence in VALID_RECURRENCE else None)
    if category is not None:
        updates.append("category = ?")
        params.append(category.lower().strip())
    if priority is not None:
        updates.append("priority = ?")
        params.append(max(1, min(4, int(priority))))
    if condition is not None:
        updates.append("condition = ?")
        params.append(condition)

    if not updates:
        conn.close()
        return False

    params.append(reminder_id)
    cur.execute(f"UPDATE reminders SET {', '.join(updates)} WHERE id = ?", params)
    rowcount = cur.rowcount
    conn.commit()
    conn.close()
    return rowcount > 0


def snooze_reminder(reminder_id: int, minutes: int = 15) -> Optional[str]:
    """Snoozes an active reminder by N minutes."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute("SELECT due_at FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
    if not row:
        conn.close()
        return None

    new_due = datetime.now() + timedelta(minutes=minutes)
    new_due_str = new_due.isoformat()
    cur.execute("UPDATE reminders SET due_at = ?, completed = 0 WHERE id = ?", (new_due_str, reminder_id))
    conn.commit()
    conn.close()
    return new_due_str


def get_all_reminders(include_completed: bool = False) -> List[Dict[str, Any]]:
    """Returns all reminders formatted as dictionaries."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT * FROM reminders"
    if not include_completed:
        query += " WHERE completed = 0"
    query += " ORDER BY due_at ASC"
    rows = cur.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_due_reminders(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Returns all reminders currently due for delivery."""
    now = now or datetime.now()
    active = get_all_reminders(include_completed=False)
    due = []

    for r in active:
        due_at_str = r.get("due_at")
        try:
            due_dt = datetime.fromisoformat(due_at_str)
        except Exception:
            continue

        if due_dt <= now:
            recurrence = r.get("recurrence")
            last_fired_at = r.get("last_fired_at")
            if recurrence and last_fired_at:
                try:
                    last_fired_dt = datetime.fromisoformat(last_fired_at)
                    if _same_period(last_fired_dt, now, recurrence):
                        continue
                except Exception:
                    pass
            due.append(r)

    return due


def _same_period(last_fired: datetime, now: datetime, recurrence: str) -> bool:
    if recurrence in ("daily", "weekdays"):
        return last_fired.date() == now.date()
    if recurrence == "weekly":
        return last_fired.isocalendar()[1] == now.isocalendar()[1] and last_fired.year == now.year
    if recurrence == "monthly":
        return last_fired.month == now.month and last_fired.year == now.year
    if recurrence == "yearly":
        return last_fired.year == now.year
    return False


def mark_fired(reminder_id: int):
    """Marks a reminder as delivered or rolls it forward if recurring."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute("SELECT recurrence, due_at FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
    if not row:
        conn.close()
        return

    recurrence, due_at_str = row
    now_iso = datetime.now().isoformat()

    if not recurrence:
        cur.execute("UPDATE reminders SET completed = 1, last_fired_at = ? WHERE id = ?", (now_iso, reminder_id))
    else:
        try:
            current_due = datetime.fromisoformat(due_at_str)
            next_due = _compute_next_occurrence(current_due, recurrence)
            cur.execute("UPDATE reminders SET due_at = ?, last_fired_at = ? WHERE id = ?", (next_due.isoformat(), now_iso, reminder_id))
        except Exception:
            cur.execute("UPDATE reminders SET completed = 1, last_fired_at = ? WHERE id = ?", (now_iso, reminder_id))

    conn.commit()
    conn.close()


def _compute_next_occurrence(current_due: datetime, recurrence: str) -> datetime:
    if recurrence == "daily":
        return current_due + timedelta(days=1)
    if recurrence == "weekly":
        return current_due + timedelta(weeks=1)
    if recurrence == "monthly":
        month = current_due.month + 1
        year = current_due.year + (1 if month > 12 else 0)
        month = month if month <= 12 else 1
        try:
            return current_due.replace(year=year, month=month)
        except ValueError:
            return current_due.replace(year=year, month=month, day=28)
    if recurrence == "weekdays":
        next_day = current_due + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day
    if recurrence == "yearly":
        try:
            return current_due.replace(year=current_due.year + 1)
        except ValueError:
            return current_due.replace(year=current_due.year + 1, day=28)
    return current_due


def complete_reminder(reminder_id: int) -> bool:
    """Marks a reminder as completed/cancelled."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder_id,))
    rowcount = cur.rowcount
    conn.commit()
    conn.close()
    return rowcount > 0


def delete_reminder(reminder_id: int) -> bool:
    """Deletes a reminder from database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    rowcount = cur.rowcount
    conn.commit()
    conn.close()
    return rowcount > 0
