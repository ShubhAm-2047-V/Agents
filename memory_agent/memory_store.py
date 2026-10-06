"""
memory_store.py
Handles all local storage, relational indexing, and semantic search of Orion's
multi-tier memory intelligence (Preferences, Projects, Code, Commands, People, Clients, Deadlines).
Uses SQLite - fully offline, zero-cost, persistent, and structured.
"""

import sqlite3
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "orion_memory.db")


def init_db():
    """Create or migrate the memories table with full metadata support."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            project TEXT DEFAULT NULL,
            importance INTEGER DEFAULT 3,
            is_temporary INTEGER DEFAULT 0,
            source_context TEXT DEFAULT NULL,
            created_at TEXT,
            updated_at TEXT,
            embedding TEXT
        )
    """)
    conn.commit()

    # Automatic column migration if table previously existed without new columns
    cur.execute("PRAGMA table_info(memories)")
    columns = [info[1] for info in cur.fetchall()]

    if "project" not in columns:
        cur.execute("ALTER TABLE memories ADD COLUMN project TEXT DEFAULT NULL")
    if "importance" not in columns:
        cur.execute("ALTER TABLE memories ADD COLUMN importance INTEGER DEFAULT 3")
    if "is_temporary" not in columns:
        cur.execute("ALTER TABLE memories ADD COLUMN is_temporary INTEGER DEFAULT 0")
    if "source_context" not in columns:
        cur.execute("ALTER TABLE memories ADD COLUMN source_context TEXT DEFAULT NULL")

    conn.commit()
    conn.close()


def save_memory(
    content: str,
    category: str = "general",
    project: Optional[str] = None,
    importance: int = 3,
    is_temporary: bool = False,
    source_context: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> int:
    """Insert a new memory record with category, importance, and project isolation."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO memories 
           (content, category, project, importance, is_temporary, source_context, created_at, updated_at, embedding) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            content.strip(),
            category.lower().strip(),
            project.strip() if project else None,
            max(1, min(5, int(importance))),
            1 if is_temporary else 0,
            source_context,
            now,
            now,
            json.dumps(embedding) if embedding else None
        )
    )
    mem_id = cur.lastrowid
    conn.commit()
    conn.close()
    return mem_id


def update_memory(
    memory_id: int,
    new_content: str,
    category: Optional[str] = None,
    project: Optional[str] = None,
    importance: Optional[int] = None
) -> bool:
    """Updates an existing memory record."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat()
    
    updates = ["content = ?", "updated_at = ?"]
    params = [new_content.strip(), now]
    
    if category is not None:
        updates.append("category = ?")
        params.append(category.lower().strip())
    if project is not None:
        updates.append("project = ?")
        params.append(project.strip())
    if importance is not None:
        updates.append("importance = ?")
        params.append(max(1, min(5, int(importance))))

    params.append(memory_id)
    sql = f"UPDATE memories SET {', '.join(updates)} WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, params)
    rowcount = cur.rowcount
    conn.commit()
    conn.close()
    return rowcount > 0


def delete_memory(memory_id: int) -> bool:
    """Deletes a memory by ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    rowcount = cur.rowcount
    conn.commit()
    conn.close()
    return rowcount > 0


def forget_by_query(query: str) -> int:
    """Deletes all memories matching a natural query or topic."""
    matches = search_memories_keyword(query, limit=50)
    if not matches:
        return 0
    ids_to_del = [m["id"] for m in matches]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    placeholders = ",".join("?" * len(ids_to_del))
    cur.execute(f"DELETE FROM memories WHERE id IN ({placeholders})", ids_to_del)
    deleted_count = cur.rowcount
    conn.commit()
    conn.close()
    return deleted_count


def get_all_memories(include_temporary: bool = True) -> List[Dict[str, Any]]:
    """Returns all memories as dictionaries."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if include_temporary:
        rows = cur.execute("SELECT * FROM memories ORDER BY importance DESC, updated_at DESC").fetchall()
    else:
        rows = cur.execute("SELECT * FROM memories WHERE is_temporary = 0 ORDER BY importance DESC, updated_at DESC").fetchall()
    
    memories = [dict(r) for r in rows]
    conn.close()
    return memories


def clear_temporary_memories() -> int:
    """Wipes all session/temporary memories."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM memories WHERE is_temporary = 1")
    count = cur.rowcount
    conn.commit()
    conn.close()
    return count


def search_memories_keyword(
    query: str,
    category: Optional[str] = None,
    project: Optional[str] = None,
    min_importance: int = 1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    High-accuracy keyword and token search with relevance scoring.
    """
    all_m = get_all_memories(include_temporary=True)
    if not all_m:
        return []

    stop_words = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "for", "to", "of", "my", "me", "you", "your", "tell", "what", "how"}
    query_tokens = [w for w in re.findall(r"\w+", query.lower()) if w not in stop_words and len(w) > 2]
    if not query_tokens:
        query_tokens = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 1]

    scored = []
    cat_filter = category.lower().strip() if category else None
    proj_filter = project.lower().strip() if project else None

    for m in all_m:
        if m.get("importance", 3) < min_importance:
            continue
        if cat_filter and m.get("category", "").lower() != cat_filter:
            continue
        if proj_filter and (m.get("project") or "").lower() != proj_filter:
            continue

        text_to_search = f"{m.get('content', '')} {m.get('category', '')} {m.get('project', '')}".lower()
        content_tokens = set(re.findall(r"\w+", text_to_search))

        score = float(m.get("importance", 3)) * 0.5
        for q in query_tokens:
            if q in content_tokens:
                score += 3.0
            elif any(q in c or c in q for c in content_tokens if len(c) > 3):
                score += 1.5

        if score > 1.5 or not query_tokens:
            scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]


def detect_conflicting_memories(new_fact: str) -> List[Dict[str, Any]]:
    """
    Checks if a newly stated memory contradicts or conflicts with existing memories.
    e.g. 'User prefers Dark Mode' vs 'User prefers Light Mode'.
    """
    matches = search_memories_keyword(new_fact, limit=10)
    conflicts = []
    new_lower = new_fact.lower()

    # Preference oppositions
    opposites = [
        ("dark mode", "light mode"),
        ("tabs", "spaces"),
        ("fastapi", "flask"),
        ("react", "vue"),
        ("python", "javascript"),
        ("prefers", "dislikes"),
        ("likes", "hates"),
        ("enable", "disable")
    ]

    for m in matches:
        content_lower = m["content"].lower()
        for term1, term2 in opposites:
            if (term1 in new_lower and term2 in content_lower) or (term2 in new_lower and term1 in content_lower):
                conflicts.append({
                    "existing_memory_id": m["id"],
                    "existing_content": m["content"],
                    "new_content": new_fact,
                    "conflict_reason": f"Opposing preference detected: '{term1}' vs '{term2}'"
                })

    return conflicts
