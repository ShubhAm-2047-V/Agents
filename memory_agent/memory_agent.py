"""
memory_agent.py
Main entry point for Orion's Memory Intelligence Agent.

Comprehensive 20-Feature Memory System:
1. Remember user preferences
2. Remember projects
3. Remember project architecture
4. Remember coding preferences
5. Remember frequently used commands
6. Remember important people
7. Remember clients
8. Remember deadlines
9. Remember previous conversations
10. Search memory
11. Update outdated information
12. Detect conflicting memories
13. Forget specific information
14. Categorize memories
15. Assign importance levels
16. Store project-specific memory
17. Store temporary session memory
18. Retrieve relevant memory automatically
19. Explain why a memory was used
20. User-controlled memory management
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional

try:
    from . import config, memory_store as store
except ImportError:
    import config, memory_store as store

store.init_db()

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def _get_client():
    if not HAS_GENAI:
        raise RuntimeError("google-genai package is required for online AI memory operations.")
    return genai.Client(api_key=config.GEMINI_API_KEY)


# =====================================================================
# 1. REMEMBER USER PREFERENCES
# =====================================================================
def remember_preference(preference_text: str, importance: int = 4) -> Dict[str, Any]:
    """Stores user preferences (e.g. IDE theme, workflow habits, preferred libraries)."""
    conflicts = store.detect_conflicting_memories(preference_text)
    mem_id = store.save_memory(
        content=preference_text,
        category="preference",
        importance=importance,
        source_context="User preference declaration"
    )
    return {
        "memory_id": mem_id,
        "content": preference_text,
        "category": "preference",
        "importance": importance,
        "conflicts_detected": conflicts
    }


# =====================================================================
# 2. REMEMBER PROJECTS
# =====================================================================
def remember_project(project_name: str, description: str, tech_stack: Optional[List[str]] = None) -> int:
    """Stores high-level project information and goals."""
    stack_str = f" [Stack: {', '.join(tech_stack)}]" if tech_stack else ""
    content = f"Project '{project_name}': {description}{stack_str}"
    return store.save_memory(
        content=content,
        category="project",
        project=project_name,
        importance=4,
        source_context="Project specification"
    )


# =====================================================================
# 3. REMEMBER PROJECT ARCHITECTURE
# =====================================================================
def remember_project_architecture(project_name: str, architecture_notes: str) -> int:
    """Stores architectural decisions, database schemas, and folder designs."""
    content = f"Architecture for '{project_name}': {architecture_notes}"
    return store.save_memory(
        content=content,
        category="architecture",
        project=project_name,
        importance=5,
        source_context="Architecture specification"
    )


# =====================================================================
# 4. REMEMBER CODING PREFERENCES
# =====================================================================
def remember_coding_preference(coding_pref: str) -> int:
    """Stores coding style preferences (e.g. FastAPI over Flask, TypeScript strict mode, pytest)."""
    return store.save_memory(
        content=f"Coding style: {coding_pref}",
        category="coding_preference",
        importance=4,
        source_context="Coding style declaration"
    )


# =====================================================================
# 5. REMEMBER FREQUENTLY USED COMMANDS
# =====================================================================
def remember_command(command_str: str, description: str) -> int:
    """Stores reusable terminal commands, docker recipes, or scripts."""
    content = f"Command `{command_str}`: {description}"
    return store.save_memory(
        content=content,
        category="command",
        importance=3,
        source_context="Command memory"
    )


# =====================================================================
# 6. REMEMBER IMPORTANT PEOPLE
# =====================================================================
def remember_person(name: str, role_or_relationship: str, notes: str = "") -> int:
    """Stores key details about colleagues, professors, mentors, and teammates."""
    notes_str = f" - Notes: {notes}" if notes else ""
    content = f"Person '{name}' ({role_or_relationship}){notes_str}"
    return store.save_memory(
        content=content,
        category="person",
        importance=4,
        source_context="Social & professional network"
    )


# =====================================================================
# 7. REMEMBER CLIENTS
# =====================================================================
def remember_client(client_name: str, company: str, project_scope: str, billing_details: str = "") -> int:
    """Stores client profile, company details, deliverables, and rates."""
    billing_str = f" [Rates/Billing: {billing_details}]" if billing_details else ""
    content = f"Client '{client_name}' at {company}: {project_scope}{billing_str}"
    return store.save_memory(
        content=content,
        category="client",
        project=company,
        importance=5,
        source_context="Client profile"
    )


# =====================================================================
# 8. REMEMBER DEADLINES
# =====================================================================
def remember_deadline(task_name: str, due_date: str, project: Optional[str] = None) -> int:
    """Stores project, assignment, or milestone deadlines."""
    proj_str = f" for '{project}'" if project else ""
    content = f"Deadline: {task_name}{proj_str} is due on {due_date}"
    return store.save_memory(
        content=content,
        category="deadline",
        project=project,
        importance=5,
        source_context="Deadline tracking"
    )


# =====================================================================
# 9. REMEMBER PREVIOUS CONVERSATIONS
# =====================================================================
def remember(user_input: str, assistant_reply: str = "", project: Optional[str] = None) -> Optional[int]:
    """Continuous conversational learning engine. Automatically extracts facts and preferences."""
    text = user_input.strip()
    if len(text) < 4:
        return None

    # Offline regex fact extractor
    pref_match = re.search(r"\b(?:i\s+prefer|i\s+like|i\s+always\s+use|always\s+remember\s+that)\s+(.+)", text, re.I)
    if pref_match:
        fact = pref_match.group(1).strip()
        return store.save_memory(f"User preference: {fact}", category="preference", project=project, importance=4)

    proj_match = re.search(r"\b(?:i\s+am\s+working\s+on|i'm\s+building|our\s+project\s+is)\s+([a-zA-Z0-9_\-\.\s]+)", text, re.I)
    if proj_match:
        pname = proj_match.group(1).strip()
        return store.save_memory(f"Active project: {pname}", category="project", project=pname, importance=4)

    return None


# =====================================================================
# 10. SEARCH MEMORY
# =====================================================================
def search_memory(query: str, category: Optional[str] = None, project: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Searches memory database by keyword, project, or category."""
    return store.search_memories_keyword(query, category=category, project=project, limit=limit)


# =====================================================================
# 11. UPDATE OUTDATED INFORMATION
# =====================================================================
def update_memory(memory_id: int, new_content: str, category: Optional[str] = None, project: Optional[str] = None, importance: Optional[int] = None) -> bool:
    """Updates an outdated memory record with fresh information."""
    return store.update_memory(memory_id, new_content, category=category, project=project, importance=importance)


# =====================================================================
# 12. DETECT CONFLICTING MEMORIES
# =====================================================================
def detect_conflicts(new_fact: str) -> List[Dict[str, Any]]:
    """Checks for contradictions between new facts and stored memories."""
    return store.detect_conflicting_memories(new_fact)


# =====================================================================
# 13. FORGET SPECIFIC INFORMATION
# =====================================================================
def forget(query_or_id: Any) -> str:
    """Deletes memory by numeric ID or by matching topic/keyword query."""
    if isinstance(query_or_id, int) or (isinstance(query_or_id, str) and query_or_id.isdigit()):
        success = store.delete_memory(int(query_or_id))
        return f"Memory #{query_or_id} deleted: {success}"
    else:
        count = store.forget_by_query(str(query_or_id))
        return f"Deleted {count} memory record(s) matching '{query_or_id}'."


# =====================================================================
# 14. CATEGORIZE MEMORIES
# =====================================================================
def get_categories_overview() -> Dict[str, int]:
    """Returns memory counts grouped by category."""
    all_m = store.get_all_memories(include_temporary=True)
    counts = {}
    for m in all_m:
        cat = m.get("category", "general")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def list_by_category(category: str) -> List[Dict[str, Any]]:
    """Lists all memories within a specific category."""
    return store.search_memories_keyword("", category=category, limit=100)


# =====================================================================
# 15. ASSIGN IMPORTANCE LEVELS
# =====================================================================
def set_importance(memory_id: int, level: int) -> bool:
    """Sets importance level (1=Low, 3=Normal, 5=Critical/Never Forget)."""
    return store.update_memory(memory_id, new_content="", importance=level)


# =====================================================================
# 16. STORE PROJECT-SPECIFIC MEMORY
# =====================================================================
def store_project_memory(project_name: str, content: str, category: str = "project_notes", importance: int = 4) -> int:
    """Stores information bound specifically to a named project."""
    return store.save_memory(
        content=content,
        category=category,
        project=project_name,
        importance=importance,
        source_context=f"Project {project_name}"
    )


# =====================================================================
# 17. STORE TEMPORARY SESSION MEMORY
# =====================================================================
def store_session_memory(content: str, category: str = "session") -> int:
    """Stores ephemeral context valid only for the current session."""
    return store.save_memory(
        content=content,
        category=category,
        importance=2,
        is_temporary=True,
        source_context="Session scratchpad"
    )


def clear_session_memories() -> int:
    """Wipes all temporary session memories."""
    return store.clear_temporary_memories()


# =====================================================================
# 18. RETRIEVE RELEVANT MEMORY AUTOMATICALLY (RECALL)
# =====================================================================
def recall(user_query: str, project: Optional[str] = None, limit: int = 5) -> str:
    """
    Finds the most relevant memories for a prompt and formats them as a prompt injection block.
    """
    matches = store.search_memories_keyword(user_query, project=project, limit=limit)
    if not matches:
        return ""

    lines = [f"- [{m.get('category', 'general').upper()}] {m['content']}" for m in matches]
    return "Relevant Long-Term Memory:\n" + "\n".join(lines)


# =====================================================================
# 19. EXPLAIN WHY A MEMORY WAS USED
# =====================================================================
def explain_retrieval(user_query: str, retrieved_memories: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Explains why specific memories matched the user's prompt."""
    if retrieved_memories is None:
        retrieved_memories = store.search_memories_keyword(user_query, limit=5)

    explanations = []
    q_words = set(re.findall(r"\w+", user_query.lower()))

    for m in retrieved_memories:
        m_words = set(re.findall(r"\w+", m.get("content", "").lower()))
        matched_tokens = list(q_words.intersection(m_words))
        explanations.append({
            "memory_id": m.get("id"),
            "content": m.get("content"),
            "category": m.get("category"),
            "importance": m.get("importance"),
            "matched_keywords": matched_tokens,
            "reason": f"Matched on keywords: {', '.join(matched_tokens)}" if matched_tokens else "Matched on project / contextual relevance"
        })

    return explanations


# =====================================================================
# 20. USER-CONTROLLED MEMORY MANAGEMENT
# =====================================================================
def export_memories(file_path: str = "memory_export.json") -> str:
    """Exports all stored memories into a clean JSON file."""
    return store.export_memories_json(file_path)


def get_all_memories(include_temporary: bool = True) -> List[Dict[str, Any]]:
    """Returns raw list of all memories."""
    return store.get_all_memories(include_temporary=include_temporary)


if __name__ == "__main__":
    print("========================================")
    print("      Orion Memory Intelligence Agent")
    print("========================================")
    print("All 20 Memory Features Activated.")
    print("Categories Overview:", get_categories_overview())
