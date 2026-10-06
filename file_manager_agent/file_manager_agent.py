"""
file_manager_agent.py
The main entry point for Orion's File Manager Agent.

Features:
1. Smart Desktop & Downloads Auto-Cleaner (Sorts into clean Documents, Images, Code, Archives, Media)
2. MD5 Duplicate File Detector & Space Reclaimer
3. Storage Hog / Large File Analyzer
4. Batch File Renamer with Dry-run Safety Preview
5. Zip Compression & Instant Archive Extraction
6. Recently Modified File Tracker
7. Deep Text File Summarization & Structural Code Inspector
8. High-performance 100% Offline NLP Parser + Gemini Flash-Lite Online Mode

Usage from your main Orion router:
    from file_manager_agent import file_manager_agent as fm

    results = fm.search("*.pdf")
    dups = fm.duplicates("Downloads")
    fm.clean_desktop()
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional
from colorama import init, Fore, Style

# Enable ANSI colors on Windows
init(autoreset=True)

# Enable UTF-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from . import config, file_ops
except ImportError:
    import config, file_ops


def _get_client():
    from google import genai
    return genai.Client(api_key=config.GEMINI_API_KEY)


# =====================================================================
# DIRECT API EXPORTS (ZERO-COST, 100% LOCAL)
# =====================================================================

def search(pattern: str = "*", root: Optional[str] = None):
    """Search for files matching glob pattern."""
    return file_ops.search_files(pattern, root)


def folder_summary(folder: Optional[str] = None):
    """Get folder statistics and category breakdown."""
    return file_ops.get_folder_summary(folder)


def clean_folder(folder: str = "Downloads", confirm: bool = False):
    """Smart clean & categorize loose files in folder."""
    return file_ops.smart_clean_folder(folder, confirm=confirm)


def clean_desktop(confirm: bool = False):
    """Clean and organize user Desktop."""
    return file_ops.smart_clean_folder(config.DESKTOP_DIR, confirm=confirm)


def clean_downloads(confirm: bool = False):
    """Clean and organize user Downloads."""
    return file_ops.smart_clean_folder(config.DOWNLOADS_DIR, confirm=confirm)


def duplicates(folder: Optional[str] = None):
    """Find exact duplicate files via MD5 hashing."""
    return file_ops.find_duplicates(folder)


def reclaim_duplicate_space(folder: Optional[str] = None, keep: str = "newest", confirm: bool = False):
    """Delete duplicate files and reclaim storage."""
    return file_ops.clean_duplicates(folder, keep=keep, confirm=confirm)


def large_files(folder: Optional[str] = None, min_size_mb: float = 10.0, limit: int = 15):
    """Find top largest space-hogging files."""
    return file_ops.find_large_files(folder, min_size_mb=min_size_mb, limit=limit)


def batch_rename(
    folder: Optional[str] = None,
    pattern: str = "*",
    prefix: str = "",
    suffix: str = "",
    replace_old: str = "",
    replace_new: str = "",
    confirm: bool = False
):
    """Safe batch rename with preview."""
    return file_ops.batch_rename(folder, pattern, prefix, suffix, replace_old, replace_new, confirm=confirm)


def zip_folder(folder_path: str, output_zip: Optional[str] = None):
    """Compress folder to .zip."""
    return file_ops.zip_folder(folder_path, output_zip)


def unzip_archive(zip_path: str, extract_to: Optional[str] = None):
    """Extract .zip archive."""
    return file_ops.unzip_archive(zip_path, extract_to)


def recent_files(folder: Optional[str] = None, hours: int = 24, limit: int = 15):
    """Find recently modified files."""
    return file_ops.get_recently_modified(folder, hours=hours, limit=limit)


def empty_folder(folder: str, confirm: bool = False):
    """Purge all contents of a folder safely."""
    return file_ops.empty_folder_contents(folder, confirm=confirm)


def create_folder(folder_name: str, parent_folder: Optional[str] = None):
    """Create a new folder."""
    return file_ops.create_folder(folder_name, parent_folder=parent_folder)


def create_file(file_name: str, parent_folder: Optional[str] = None, content: str = ""):
    """Create a new file."""
    return file_ops.create_file(file_name, parent_folder=parent_folder, content=content)


def copy(src_path: str, dest_folder: str):
    """Copy a file or directory."""
    return file_ops.copy_file(src_path, dest_folder)


def open_in_explorer(folder: Optional[str] = None):
    """Open folder in Windows Explorer."""
    return file_ops.open_in_explorer(folder)


def open_file(query: str, folder: Optional[str] = None):
    """Find and launch a file with Windows default app."""
    return file_ops.open_file_by_query(query, folder)


def rename(old_path: str, new_name: str):
    """Rename a single file."""
    return file_ops.rename_file(old_path, new_name)



def move(src_path: str, dest_folder: str):
    """Move a file to destination folder."""
    return file_ops.move_file(src_path, dest_folder)


def delete(path: str, confirm: bool = False):
    """Delete a single file (requires confirmation)."""
    return file_ops.delete_file(path, confirm=confirm)


def search_folders(pattern: str = "*", root: Optional[str] = None):
    """Search for directories matching pattern."""
    return file_ops.search_folders(pattern, root)


def find_projects(root: Optional[str] = None):
    """Find all software development projects."""
    return file_ops.find_project_files(root)


def archive_projects(projects_dir: Optional[str] = None, days_inactive: int = 90, confirm: bool = False):
    """Archive inactive projects to zip files."""
    return file_ops.archive_old_projects(projects_dir, days_inactive=days_inactive, confirm=confirm)


def compress(file_paths: List[str], output_zip: str):
    """Compress multiple files into a zip archive."""
    return file_ops.compress_files(file_paths, output_zip)


def metadata(file_path: str):
    """Analyze detailed file metadata, checksum, line counts."""
    return file_ops.analyze_file_metadata(file_path)


def cleanup_suggestions(root_dir: Optional[str] = None):
    """Get storage hog cleanup suggestions and reclaimable space."""
    return file_ops.get_storage_cleanup_suggestions(root_dir)


def sort_by_type(folder: Optional[str] = None, confirm: bool = False):
    """Sort files into categorized folders by extension type."""
    return file_ops.organize_by_extension(folder or "Downloads", confirm=confirm)



# =====================================================================
# FILE SUMMARIZATION (OFFLINE & ONLINE)
# =====================================================================

def _summarize_file_offline(path: str) -> str:
    """100% offline file inspection and structural preview."""
    try:
        content, truncated = file_ops.read_text_file(path)
        lines = content.splitlines()
        word_count = len(content.split())
        size_kb = round(len(content.encode("utf-8")) / 1024, 2)
        preview = "\n".join([f"  {line}" for line in lines[:8]])

        return f"""{Fore.CYAN}┌─ [File Inspection: {os.path.basename(path)}]{Style.RESET_ALL}
  • Size: {size_kb} KB ({len(lines)} lines, ~{word_count} words)
  • Format: {os.path.splitext(path)[1].upper() or 'Plain text'}
  • Preview:
{Fore.LIGHTBLACK_EX}{preview}{Style.RESET_ALL}
  {"... [Truncated for preview]" if truncated or len(lines) > 8 else ""}"""
    except Exception as e:
        return f"Error reading file: {e}"


def summarize_file(path: str, force_offline: bool = False) -> str:
    """Summarizes text file using Gemini when online, or structural summary offline."""
    has_api_key = bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE")
    offline = getattr(config, "OFFLINE_MODE", True) or force_offline or not has_api_key

    if offline:
        return _summarize_file_offline(path)

    try:
        content, _ = file_ops.read_text_file(path)
        prompt = f"Summarize the following file content in 3-5 concise bullet points:\n\n{content}"
        client = _get_client()
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        return response.text.strip()
    except Exception:
        return _summarize_file_offline(path)


# =====================================================================
# OFFLINE NATURAL LANGUAGE COMMAND PARSER
# =====================================================================

def _parse_command_offline(text: str) -> Dict[str, Any]:
    """100% offline regex & semantic rule-based parser for file operations."""
    clean = text.strip()
    lower = clean.lower()

    # 1. Duplicate Files
    if any(k in lower for k in ("duplicate", "dups", "dupes", "identical files")):
        if any(k in lower for k in ("clean", "delete", "remove", "reclaim", "purge", "fix", "erase")):
            m = re.search(r"\b(?:in|folder|dir)\s+([^\s]+)", clean)
            folder = m.group(1) if m else "."
            return {"action": "reclaim_duplicates", "params": {"folder": folder}, "needs_confirmation": True}
        else:
            m = re.search(r"\b(?:in|folder|dir)\s+([^\s]+)", clean)
            folder = m.group(1) if m else "."
            return {"action": "duplicates", "params": {"folder": folder}, "needs_confirmation": False}

    # 2. Bulk Delete / Empty Folder (e.g. "delete all files in download", "empty downloads")
    if any(k in lower for k in ("delete all", "remove all", "erase all", "empty", "purge", "clear all", "clear folder")):
        if "download" in lower:
            target = "Downloads"
        elif "desktop" in lower:
            target = "Desktop"
        elif "document" in lower:
            target = "Documents"
        elif "workspace" in lower or "here" in lower or "current" in lower:
            target = "."
        else:
            m = re.search(r"\b(?:in|of|from|folder|dir)\s+([a-zA-Z0-9_\-\.\/\\]+)", clean, re.I)
            if not m:
                m = re.search(r"\b(?:empty|purge|clear)\s+([a-zA-Z0-9_\-\.\/\\]+)", clean, re.I)
            target = m.group(1) if m else "Downloads"
        return {"action": "empty_folder", "params": {"folder": target}, "needs_confirmation": True}

    # 3. Create Folder (e.g. "create folder named images in pictures", "make a folder projects in desktop", "new folder test")
    if re.search(r"\b(?:create|make|new|mkdir)\s+(?:a\s+)?(?:new\s+)?(?:folder|dir|directory)\b", lower) or lower.startswith("mkdir "):
        m = re.search(r"\b(?:folder|dir|directory)\s*(?:named|called)?\s+([a-zA-Z0-9_\-\.\/\\]+)(?:\s+in\s+([a-zA-Z0-9_\-\.\/\\]+))?", clean, re.I)
        if not m:
            m = re.search(r"\b(?:mkdir)\s+([a-zA-Z0-9_\-\.\/\\]+)(?:\s+in\s+([a-zA-Z0-9_\-\.\/\\]+))?", clean, re.I)
        if m:
            f_name = m.group(1).strip("'\"")
            p_name = m.group(2).strip("'\"") if m.group(2) else "."
            return {"action": "create_folder", "params": {"folder_name": f_name, "parent_folder": p_name}, "needs_confirmation": False}

    # 4. Create File (e.g. "create file notes.txt in desktop", "make a file test.py", "touch main.py")
    if re.search(r"\b(?:create|make|new|touch)\s+(?:a\s+)?(?:new\s+)?file\b", lower) or lower.startswith("touch "):
        m = re.search(r"\b(?:file|touch)\s*(?:named|called)?\s+([a-zA-Z0-9_\-\.\/\\]+)(?:\s+in\s+([a-zA-Z0-9_\-\.\/\\]+))?", clean, re.I)
        if m:
            file_name = m.group(1).strip("'\"")
            p_name = m.group(2).strip("'\"") if m.group(2) else "."
            return {"action": "create_file", "params": {"file_name": file_name, "parent_folder": p_name}, "needs_confirmation": False}


    # 5. Copy File / Directory (e.g. "copy file.txt to backup", "copy image.png to pictures")
    if lower.startswith("copy ") or "copy " in lower:
        m_cp = re.search(r"\bcopy\s+([^\s]+)\s+to\s+([^\s]+)", clean, re.I)
        if m_cp:
            return {"action": "copy", "params": {"src_path": m_cp.group(1), "dest_folder": m_cp.group(2)}, "needs_confirmation": False}

    # 6. Open / Launch File (e.g. "open a screen shot from D:\OneDrive\Pictures", "open a scrrn shot from pictures", "open screenshot")
    if any(k in lower for k in ("open ", "launch ", "view ")) and not any(k in lower for k in ("open folder", "open directory", "open in explorer", "show in explorer")):
        m_from = re.search(r'''\b(?:open|launch|view)\s+(?:a\s+|the\s+)?(.+?)\s+(?:from|in)\s+(?:"([^"]+)"|'([^']+)'|([a-zA-Z0-9_\-\.\/\\:]+))$''', clean, re.I)
        if m_from:
            q = m_from.group(1).strip()
            folder_target = (m_from.group(2) or m_from.group(3) or m_from.group(4)).strip()
            return {"action": "open_file", "params": {"query": q, "folder": folder_target}, "needs_confirmation": False}
        else:
            m_single = re.search(r'''\b(?:open|launch|view)\s+(?:a\s+|the\s+)?(?:"([^"]+)"|'([^']+)'|([a-zA-Z0-9_\-\.\/\\:\s]+))''', clean, re.I)
            if m_single:
                q = (m_single.group(1) or m_single.group(2) or m_single.group(3)).strip()
                if q.lower() not in ("folder", "directory", "explorer", "dash", "dashboard", "help", "menu", "status"):
                    return {"action": "open_file", "params": {"query": q, "folder": "."}, "needs_confirmation": False}

    # 7. Open in Windows Explorer (e.g. "open folder downloads", "open pictures in explorer", "reveal desktop")
    if any(k in lower for k in ("open in explorer", "show in explorer", "reveal in explorer", "open folder", "open explorer", "explore")):
        m_op = re.search(r"\b(?:open|show|reveal|explore)\s+(?:folder\s+|directory\s+)?([a-zA-Z0-9_\-\.\/\\]+)?", clean, re.I)
        raw_t = m_op.group(1) if (m_op and m_op.group(1)) else "."
        target = "." if raw_t.lower() in ("explorer", "here", "current") else raw_t
        return {"action": "open_explorer", "params": {"folder": target}, "needs_confirmation": False}

    # 8. Clean Desktop / Downloads / Folder & Auto-sort
    if any(k in lower for k in ("clean", "organize", "organise", "tidy", "sort", "auto-sort", "autosort", "categorize", "categorise")):

        m = re.search(r'''\b(?:clean|organize|organise|sort|categorize|categorise)\s+(?:folder\s+|directory\s+)?(?:"([^"]+)"|'([^']+)'|([a-zA-Z0-9_\-\.\/\\:]+))''', clean, re.I)
        if m:
            target = (m.group(1) or m.group(2) or m.group(3)).strip()
            return {"action": "clean_folder", "params": {"folder": target}, "needs_confirmation": False}
        elif "desktop" in lower:
            return {"action": "clean_folder", "params": {"folder": "Desktop"}, "needs_confirmation": False}
        elif "download" in lower:
            return {"action": "clean_folder", "params": {"folder": "Downloads"}, "needs_confirmation": False}
        elif "document" in lower:
            return {"action": "clean_folder", "params": {"folder": "Documents"}, "needs_confirmation": False}
        elif "picture" in lower or "photo" in lower or "image" in lower:
            return {"action": "clean_folder", "params": {"folder": "Pictures"}, "needs_confirmation": False}
        elif "workspace" in lower or "here" in lower or "current" in lower:
            return {"action": "clean_folder", "params": {"folder": "."}, "needs_confirmation": False}
        else:
            return {"action": "clean_folder", "params": {"folder": "Downloads"}, "needs_confirmation": False}




    # 8. Show / List files in directory (e.g. "show all files in pictures", "list files in downloads")
    if any(k in lower for k in ("show files", "list files", "show all files", "files in", "what is in", "list contents")):
        m_lst = re.search(r"\b(?:in|of)\s+([a-zA-Z0-9_\-\.\/\\]+)", clean, re.I)
        target = m_lst.group(1) if m_lst else "."
        return {"action": "search", "params": {"pattern": "*", "root": target}, "needs_confirmation": False}

    # 9. Large Files / Disk Hogs
    if any(k in lower for k in ("large files", "big files", "largest files", "space hogs", "heavy files", "huge files", "biggest files")):
        m_size = re.search(r"(\d+)\s*(?:mb|gb|m|g)", lower)
        min_mb = float(m_size.group(1)) if m_size else 10.0
        if "gb" in lower:
            min_mb *= 1024
        return {"action": "large_files", "params": {"folder": ".", "min_size_mb": min_mb}, "needs_confirmation": False}

    # 10. Recently Modified Files
    if any(k in lower for k in ("recent files", "recently modified", "what changed", "modified today", "recent")):
        m_hrs = re.search(r"(\d+)\s*(?:hours?|hrs?|h)", lower)
        hrs = int(m_hrs.group(1)) if m_hrs else 24
        return {"action": "recent_files", "params": {"folder": ".", "hours": hrs}, "needs_confirmation": False}

    # 11. Zip & Archive Operations
    if lower.startswith("zip ") or "compress " in lower:
        m_zip = re.search(r"\b(?:zip|compress)\s+([^\s]+)(?:\s+(?:to|as)\s+([^\s]+))?", clean, re.I)
        if m_zip:
            return {"action": "zip", "params": {"folder": m_zip.group(1), "output_zip": m_zip.group(2)}, "needs_confirmation": False}
    elif lower.startswith("unzip ") or "extract " in lower:
        m_unzip = re.search(r"\b(?:unzip|extract)\s+([^\s]+)(?:\s+(?:to|in)\s+([^\s]+))?", clean, re.I)
        if m_unzip:
            return {"action": "unzip", "params": {"zip_path": m_unzip.group(1), "extract_to": m_unzip.group(2)}, "needs_confirmation": False}

    # 12. Search files
    m_find = re.search(r"\b(?:search|find|locate)\s+([^\s]+)", clean, re.I)
    if m_find and not any(k in lower for k in ("duplicate", "large")):
        return {"action": "search", "params": {"pattern": m_find.group(1)}, "needs_confirmation": False}

    # 13. Single Rename & Move
    m_ren = re.search(r"\brename\s+([^\s]+)\s+(?:to|as)\s+([^\s]+)", clean, re.I)
    if m_ren:
        return {"action": "rename", "params": {"old_path": m_ren.group(1), "new_name": m_ren.group(2)}, "needs_confirmation": True}

    m_mov = re.search(r"\bmove\s+([^\s]+)\s+to\s+([^\s]+)", clean, re.I)
    if m_mov:
        return {"action": "move", "params": {"src_path": m_mov.group(1), "dest_folder": m_mov.group(2)}, "needs_confirmation": True}

    # 14. Delete Single File
    m_del = re.search(r"\b(?:delete|remove|erase)\s+([^\s]+)", clean, re.I)
    if m_del:
        return {"action": "delete", "params": {"path": m_del.group(1)}, "needs_confirmation": True}

    # 15. Folder Summary / Stats
    if any(k in lower for k in ("summary", "stats", "disk usage", "folder info", "overview")):
        m_f = re.search(r"\b(?:summary|stats|overview)\s+([^\s]+)", clean, re.I)
        folder = m_f.group(1) if m_f else "."
        return {"action": "folder_summary", "params": {"folder": folder}, "needs_confirmation": False}

    # 16. File Summarize / Inspect
    if any(k in lower for k in ("inspect", "summarize", "read", "view")):
        m_s = re.search(r"\b(?:inspect|summarize|read|view)\s+(?:file\s+)?([^\s]+)", clean, re.I)
        if m_s:
            return {"action": "summarize_file", "params": {"path": m_s.group(1)}, "needs_confirmation": False}

    return {"action": "unknown", "params": {}, "needs_confirmation": False, "raw": clean}




def parse_command(natural_language_command: str, force_offline: bool = False) -> Dict[str, Any]:
    """Converts natural language into structured file actions."""
    return _parse_command_offline(natural_language_command)


# =====================================================================
# EXECUTIVE IN-TERMINAL CMD DASHBOARD
# =====================================================================

def show_cmd_dashboard(folder: str = "."):
    """Display clean, executive-grade File Manager dashboard."""
    stats = folder_summary(folder)
    target_name = os.path.basename(stats.get("folder", config.DEFAULT_ROOT)) or "Root"

    # Header Card
    print(Fore.CYAN + "┌──────────────────────────────────────────────────────────────────────┐" + Style.RESET_ALL)
    print(Fore.CYAN + "│  " + Fore.WHITE + Style.BRIGHT + "ORION FILE MANAGER & WORKSPACE ORGANIZER" + Style.RESET_ALL + "          " + Fore.GREEN + "[● Ready]" + Fore.CYAN + " │" + Style.RESET_ALL)
    print(Fore.CYAN + "└──────────────────────────────────────────────────────────────────────┘" + Style.RESET_ALL)

    # 1. Folder Overview
    print(f"\n {Fore.WHITE}{Style.BRIGHT}WORKSPACE OVERVIEW{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}(Target: {stats.get('folder')}){Style.RESET_ALL}")
    print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
    print(f"  Files Indexed:   {Fore.LIGHTCYAN_EX}{stats.get('file_count', 0):>6}{Style.RESET_ALL} files    │  Subdirectories:  {Fore.LIGHTCYAN_EX}{stats.get('dir_count', 0):>6}{Style.RESET_ALL}")
    print(f"  Total Storage:   {Fore.YELLOW}{stats.get('total_size_mb', 0):>6.1f}{Style.RESET_ALL} MB       │  Status:          {Fore.GREEN}Active & Scanned{Style.RESET_ALL}")


    # 2. Smart Category Breakdown
    cats = stats.get("by_category", {})
    if cats:
        print(f"\n {Fore.WHITE}{Style.BRIGHT}FILE CATEGORIES{Style.RESET_ALL}")
        print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
        cat_items = list(cats.items())
        for i in range(0, len(cat_items), 2):
            c1, v1 = cat_items[i]
            col1 = f"• {c1:<14} {Fore.LIGHTGREEN_EX}{v1:>4} file(s){Style.RESET_ALL}"
            col2 = ""
            if i + 1 < len(cat_items):
                c2, v2 = cat_items[i+1]
                col2 = f"• {c2:<14} {Fore.LIGHTGREEN_EX}{v2:>4} file(s){Style.RESET_ALL}"
            print(f"  {col1:<36} {col2}")

    # 3. Quick Actions Guide
    print(Fore.LIGHTBLACK_EX + "\n  " + "─" * 68 + Style.RESET_ALL)
    print(f"  {Fore.CYAN}Popular Commands:{Style.RESET_ALL}")
    print(f"  • {Fore.GREEN}'clean desktop'{Style.RESET_ALL} or {Fore.GREEN}'clean downloads'{Style.RESET_ALL}  (Auto-sort into categorized folders)")
    print(f"  • {Fore.GREEN}'find duplicates'{Style.RESET_ALL} / {Fore.GREEN}'clean duplicates'{Style.RESET_ALL} (Reclaim wasted storage)")
    print(f"  • {Fore.GREEN}'large files'{Style.RESET_ALL}                      (Find storage hogs)")
    print(f"  • {Fore.GREEN}'search *.pdf'{Style.RESET_ALL}                    (Find files matching pattern)")
    print(f"  • {Fore.GREEN}'zip <folder>'{Style.RESET_ALL} / {Fore.GREEN}'unzip <file.zip>'{Style.RESET_ALL} (Instant archive compression)")
    print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
    print(f"  {Fore.LIGHTBLACK_EX}Shortcuts: [D] Refresh  [?] Help  [Q] Exit{Style.RESET_ALL}\n")


def print_help():
    """Display clean command reference."""
    print(f"""
{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│ FILE MANAGER COMMAND REFERENCE                                         │
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
  {Fore.GREEN}1. Smart Organization & Cleaning:{Style.RESET_ALL}
    • 'clean desktop'          : Sort loose desktop files into clean categories
    • 'clean downloads'        : Organize downloads by Document, Image, Code, Archive
    • 'clean <folder_name>'    : Organize any folder

  {Fore.GREEN}2. Duplicate Detection & Disk Space:{Style.RESET_ALL}
    • 'find duplicates'        : Fast MD5 scan to find exact duplicate files
    • 'clean duplicates'       : Safely remove duplicate copies to reclaim space
    • 'large files'            : Find top space-hogging files (>10MB)

  {Fore.GREEN}3. Search, Inspect & Summary:{Style.RESET_ALL}
    • 'search *.py'            : Search files matching glob pattern
    • 'inspect <file.txt>'     : Structural line & word preview of a file
    • 'recent files'           : Show files modified in the last 24 hours
    • 'summary <folder>'       : Storage stats and file category breakdown

  {Fore.GREEN}4. File Manipulation & Archives:{Style.RESET_ALL}
    • 'rename <old> to <new>'  : Rename a file
    • 'move <src> to <dest>'   : Move a file
    • 'zip <folder>'           : Compress folder into .zip
    • 'unzip <archive.zip>'    : Extract .zip archive cleanly
    • 'delete <file>'          : Permanently delete a file
""")


# =====================================================================
# INTERACTIVE CLI LOOP
# =====================================================================

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    show_cmd_dashboard()

    while True:
        try:
            cmd = input(f"{Fore.CYAN}orion-files > {Style.RESET_ALL}").strip()
            if not cmd:
                continue

            cmd_lower = cmd.lower()
            if cmd_lower in ("exit", "quit", "q"):
                print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                break
            elif cmd_lower in ("help", "?", "man"):
                print_help()
                continue
            elif cmd_lower in ("status", "s", "dash", "dashboard", "cls", "clear", "d"):
                os.system("cls" if os.name == "nt" else "clear")
                show_cmd_dashboard()
                continue

            parsed = parse_command(cmd)
            action = parsed.get("action")
            params = parsed.get("params", {})

            # 1. Search
            if action == "search":
                pat = params.get("pattern", "*")
                results = search(pat)
                print(f"\n{Fore.WHITE}Search Results for '{pat}' ({len(results)} found):{Style.RESET_ALL}")
                print(Fore.LIGHTBLACK_EX + "─" * 68 + Style.RESET_ALL)
                for r in results[:15]:
                    print(f"  • {Fore.GREEN}{r['name']:<28}{Style.RESET_ALL} {r['size_kb']:>6.1f} KB  │  {Fore.LIGHTBLACK_EX}{r['path']}{Style.RESET_ALL}")
                if len(results) > 15:
                    print(f"  {Fore.LIGHTBLACK_EX}... and {len(results) - 15} more files.{Style.RESET_ALL}")
                print()

            # 2. Smart Clean Folder
            elif action == "clean_folder":
                target_f = params.get("folder", "Downloads")
                plan_res = clean_folder(target_f, confirm=False)
                if not plan_res.get("plan"):
                    print(f"\n  {Fore.GREEN}✓ {plan_res.get('message')}{Style.RESET_ALL}\n")
                else:
                    print(f"\n{Fore.CYAN}Organization Plan for '{os.path.basename(plan_res['folder'])}':{Style.RESET_ALL}")
                    for cat, count in plan_res["plan"].items():
                        print(f"  • {cat:<14} -> {count} file(s)")
                    confirm = input(f"\n{Fore.YELLOW}Proceed to organize these files? (y/N): {Style.RESET_ALL}").strip().lower()
                    if confirm in ("y", "yes"):
                        exec_res = clean_folder(target_f, confirm=True)
                        print(f"  {Fore.GREEN}✓ {exec_res.get('message')}{Style.RESET_ALL}\n")
                    else:
                        print(f"  {Fore.LIGHTBLACK_EX}Cancelled.{Style.RESET_ALL}\n")

            # 3. Duplicate Files
            elif action == "duplicates":
                f_target = params.get("folder", ".")
                print(f"\n{Fore.CYAN}Scanning for duplicate files in '{f_target}'...{Style.RESET_ALL}")
                dup_res = duplicates(f_target)
                groups = dup_res.get("groups", [])
                if not groups:
                    print(f"  {Fore.GREEN}✓ No duplicate files found in '{f_target}'.{Style.RESET_ALL}\n")
                else:
                    print(f"\n{Fore.YELLOW}Found {len(groups)} duplicate sets ({dup_res['total_wasted_mb']} MB wasted):{Style.RESET_ALL}")
                    for idx, g in enumerate(groups[:8], 1):
                        print(f"  [{idx}] {g['size_mb']} MB each ({g['copies']} copies):")
                        for p in g["files"]:
                            print(f"      - {Fore.LIGHTBLACK_EX}{p}{Style.RESET_ALL}")
                    print(f"\n  Type {Fore.GREEN}'clean duplicates'{Style.RESET_ALL} to safely remove extra copies.\n")

            # 4. Reclaim Duplicate Space
            elif action == "reclaim_duplicates":
                f_target = params.get("folder", ".")
                prev_res = reclaim_duplicate_space(f_target, confirm=False)
                if prev_res.get("total_duplicates", 0) == 0:
                    print(f"\n  {Fore.GREEN}✓ No duplicate files to clean.{Style.RESET_ALL}\n")
                else:
                    print(f"\n{Fore.YELLOW}Warning: Ready to delete {prev_res['total_duplicates']} duplicate file(s) ({prev_res['reclaimable_mb']} MB freed).{Style.RESET_ALL}")
                    confirm = input(f"{Fore.RED}Confirm permanent deletion of duplicate copies? (y/N): {Style.RESET_ALL}").strip().lower()
                    if confirm in ("y", "yes"):
                        clean_res = reclaim_duplicate_space(f_target, confirm=True)
                        print(f"  {Fore.GREEN}✓ {clean_res.get('message')}{Style.RESET_ALL}\n")
                    else:
                        print(f"  {Fore.LIGHTBLACK_EX}Cancelled.{Style.RESET_ALL}\n")

            # 5. Large Files
            elif action == "large_files":
                min_mb = params.get("min_size_mb", 10.0)
                lf_list = large_files(".", min_size_mb=min_mb, limit=15)
                print(f"\n{Fore.WHITE}Top Large Files (> {min_mb} MB):{Style.RESET_ALL}")
                print(Fore.LIGHTBLACK_EX + "─" * 68 + Style.RESET_ALL)
                if not lf_list:
                    print(f"  No files found exceeding {min_mb} MB.")
                else:
                    for item in lf_list:
                        print(f"  • {Fore.YELLOW}{item['size_mb']:>7.1f} MB{Style.RESET_ALL}  │  {Fore.WHITE}{item['name']:<24}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}({item['path']}){Style.RESET_ALL}")
                print()

            # 6. Recently Modified Files
            elif action == "recent_files":
                hrs = params.get("hours", 24)
                rec_list = recent_files(".", hours=hrs, limit=15)
                print(f"\n{Fore.WHITE}Recently Modified Files (Last {hrs} hours):{Style.RESET_ALL}")
                print(Fore.LIGHTBLACK_EX + "─" * 68 + Style.RESET_ALL)
                if not rec_list:
                    print(f"  No files modified in the last {hrs} hours.")
                else:
                    for item in rec_list:
                        print(f"  • {Fore.GREEN}{item['modified']}{Style.RESET_ALL}  │  {Fore.WHITE}{item['name']:<24}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}({item['size_kb']} KB){Style.RESET_ALL}")
                print()

            # 7. Zip / Compress
            elif action == "zip":
                f_in = params.get("folder", "")
                z_res = zip_folder(f_in, params.get("output_zip"))
                if z_res.get("success"):
                    print(f"\n  {Fore.GREEN}✓ {z_res.get('message')}{Style.RESET_ALL}\n")
                else:
                    print(f"\n  {Fore.RED}Error: {z_res.get('message')}{Style.RESET_ALL}\n")

            # 8. Unzip / Extract
            elif action == "unzip":
                z_path = params.get("zip_path", "")
                uz_res = unzip_archive(z_path, params.get("extract_to"))
                if uz_res.get("success"):
                    print(f"\n  {Fore.GREEN}✓ {uz_res.get('message')}{Style.RESET_ALL}\n")
                else:
                    print(f"\n  {Fore.RED}Error: {uz_res.get('message')}{Style.RESET_ALL}\n")

            # 9. Folder Summary
            elif action == "folder_summary":
                folder = params.get("folder", ".")
                show_cmd_dashboard(folder)

            # 10. Summarize / Inspect File
            elif action == "summarize_file":
                filepath = params.get("path", "")
                summary = summarize_file(filepath)
                print(f"\n{summary}\n")

            # 11. Rename Single
            elif action == "rename":
                confirm = input(f"Confirm rename '{params['old_path']}' -> '{params['new_name']}'? (y/N): ").strip().lower()
                if confirm in ("y", "yes"):
                    new_p = rename(params["old_path"], params["new_name"])
                    print(f"  {Fore.GREEN}✓ Renamed to: {new_p}{Style.RESET_ALL}\n")
                else:
                    print(f"  {Fore.LIGHTBLACK_EX}Cancelled.{Style.RESET_ALL}\n")

            # 12. Move
            elif action == "move":
                confirm = input(f"Confirm move '{params['src_path']}' -> '{params['dest_folder']}'? (y/N): ").strip().lower()
                if confirm in ("y", "yes"):
                    new_p = move(params["src_path"], params["dest_folder"])
                    print(f"  {Fore.GREEN}✓ Moved to: {new_p}{Style.RESET_ALL}\n")
                else:
                    print(f"  {Fore.LIGHTBLACK_EX}Cancelled.{Style.RESET_ALL}\n")

            # 13. Create Folder
            elif action == "create_folder":
                f_name = params.get("folder_name", "new_folder")
                p_name = params.get("parent_folder", ".")
                res = create_folder(f_name, p_name)
                print(f"\n  {Fore.GREEN}✓ {res.get('message')}{Style.RESET_ALL}\n")

            # 14. Create File
            elif action == "create_file":
                f_name = params.get("file_name", "new_file.txt")
                p_name = params.get("parent_folder", ".")
                res = create_file(f_name, p_name)
                print(f"\n  {Fore.GREEN}✓ {res.get('message')}{Style.RESET_ALL}\n")

            # 15. Copy File / Directory
            elif action == "copy":
                src = params.get("src_path", "")
                dst = params.get("dest_folder", ".")
                res = copy(src, dst)
                if res.get("success"):
                    print(f"\n  {Fore.GREEN}✓ {res.get('message')}{Style.RESET_ALL}\n")
                else:
                    print(f"\n  {Fore.RED}Error: {res.get('message')}{Style.RESET_ALL}\n")

            # 16. Open in Windows Explorer
            elif action == "open_explorer":
                target_f = params.get("folder", ".")
                res = open_in_explorer(target_f)
                print(f"\n  {Fore.GREEN}✓ {res.get('message')}{Style.RESET_ALL}\n")

            # 17. Open / Launch File
            elif action == "open_file":
                query = params.get("query", "")
                target_f = params.get("folder", ".")
                res = open_file(query, target_f)
                if res.get("success"):
                    print(f"\n  {Fore.GREEN}✓ {res.get('message')}{Style.RESET_ALL}\n")
                else:
                    print(f"\n  {Fore.YELLOW}{res.get('message')}{Style.RESET_ALL}\n")

            # 18. Empty / Purge Folder (e.g. 'delete all files in downloads')

            elif action == "empty_folder":
                target_f = params.get("folder", "Downloads")
                prev_res = empty_folder(target_f, confirm=False)
                if not prev_res.get("success"):
                    print(f"\n  {Fore.RED}Error: {prev_res.get('message')}{Style.RESET_ALL}\n")
                elif prev_res.get("total_items", 0) == 0:
                    print(f"\n  {Fore.GREEN}✓ {prev_res.get('message')}{Style.RESET_ALL}\n")
                else:
                    folder_name = os.path.basename(prev_res.get("folder", target_f)) or target_f
                    print(f"\n{Fore.YELLOW}Warning: Ready to delete all {prev_res['total_items']} item(s) inside '{folder_name}'.{Style.RESET_ALL}")
                    if prev_res.get("preview"):
                        print(f"  Preview items: {', '.join(prev_res['preview'][:6])}{'...' if prev_res['total_items'] > 6 else ''}")
                    confirm = input(f"{Fore.RED}Confirm PERMANENT delete of all contents in '{folder_name}'? (y/N): {Style.RESET_ALL}").strip().lower()
                    if confirm in ("y", "yes"):
                        exec_res = empty_folder(target_f, confirm=True)
                        print(f"  {Fore.GREEN}✓ {exec_res.get('message')}{Style.RESET_ALL}\n")
                    else:
                        print(f"  {Fore.LIGHTBLACK_EX}Cancelled.{Style.RESET_ALL}\n")

            # 18. Delete Single File
            elif action == "delete":
                path = params.get("path", "")
                confirm = input(f"{Fore.RED}Confirm PERMANENT delete of '{path}'? (y/N): {Style.RESET_ALL}").strip().lower()
                if confirm in ("y", "yes"):
                    delete(path, confirm=True)
                    print(f"  {Fore.GREEN}✓ Deleted: {path}{Style.RESET_ALL}\n")
                else:
                    print(f"  {Fore.LIGHTBLACK_EX}Cancelled.{Style.RESET_ALL}\n")



            else:
                print(f"Unrecognized command: '{cmd}'. Try {Fore.GREEN}'clean desktop'{Style.RESET_ALL}, {Fore.GREEN}'find duplicates'{Style.RESET_ALL}, {Fore.GREEN}'large files'{Style.RESET_ALL}, or {Fore.GREEN}'search *.py'{Style.RESET_ALL}.\n")

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}\n")
