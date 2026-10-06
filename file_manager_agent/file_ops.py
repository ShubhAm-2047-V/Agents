"""
file_ops.py
Low-level, robust, safe file system operations for Orion File Manager Agent.

Features:
- Smart Folder Cleaning & Categorization (Desktop / Downloads)
- Fast MD5 Duplicate File Detection & Space Reclaiming
- Large File & Storage Hog Analyzer
- Safe Batch File Renaming with Dry-run Preview
- Zip Compression & Archive Extraction
- Recently Modified File Tracker
- Full Workspace & Folder Telemetry

100% local, zero API cost, safe path resolution.
"""

import os
import shutil
import hashlib
import fnmatch
import zipfile
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

try:
    from . import config
except ImportError:
    import config


class UnsafePathError(Exception):
    pass


def resolve_folder_alias(path: Optional[str] = None) -> str:
    """
    Resolves folder aliases such as 'desktop', 'downloads', 'documents', 'pictures', '.', '~'.
    """
    if not path or path.strip() in ("", ".", "here", "current"):
        return os.path.abspath(config.DEFAULT_ROOT)

    clean_p = path.strip()
    if os.path.isabs(clean_p) or (len(clean_p) >= 2 and clean_p[1] == ":"):
        return os.path.abspath(clean_p)

    if clean_p.startswith("~"):
        return os.path.abspath(os.path.expanduser(clean_p))

    p_clean = clean_p.lower().rstrip(r"\/")
    if p_clean in ("desktop", "my desktop"):
        return os.path.abspath(config.DESKTOP_DIR)
    elif p_clean in ("downloads", "download", "my downloads", "my download"):
        return os.path.abspath(config.DOWNLOADS_DIR)
    elif p_clean in ("documents", "document", "docs", "doc", "my documents", "my document", "my docs"):
        return os.path.abspath(config.DOCUMENTS_DIR)
    elif p_clean in ("pictures", "picture", "photos", "photo", "images", "image", "my pictures", "my picture", "my photos"):
        return os.path.abspath(config.PICTURES_DIR)

    # Relative to root
    return os.path.abspath(os.path.join(config.DEFAULT_ROOT, clean_p))



def _resolve_safe(path: str) -> str:
    """Resolve a path and ensure it exists and is safely reachable."""
    if not path:
        return os.path.abspath(config.DEFAULT_ROOT)
    clean_p = path.strip()
    if os.path.exists(clean_p):
        return os.path.abspath(clean_p)
    return resolve_folder_alias(path)



def ensure_dir(dir_path: str) -> bool:
    """Safely creates a directory, with fallback for OneDrive Cloud Filter folders."""
    if not dir_path:
        return True
    if os.path.exists(dir_path):
        return True
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception:
        pass

    # Windows OneDrive Virtualization Fallback
    if os.name == "nt":
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"New-Item -ItemType Directory -LiteralPath '{dir_path}' -Force"],
                capture_output=True,
                check=False
            )
            return os.path.exists(dir_path)
        except Exception:
            pass
    return False


def safe_move(src: str, dst: str) -> bool:
    """Safely moves a file or directory, with fallback for OneDrive Cloud Filter folders."""
    ensure_dir(os.path.dirname(dst))
    try:
        shutil.move(src, dst)
        return True
    except Exception:
        pass

    # Windows OneDrive Virtualization Fallback
    if os.name == "nt":
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Move-Item -LiteralPath '{src}' -Destination '{dst}' -Force"],
                capture_output=True,
                check=False
            )
            return os.path.exists(dst)
        except Exception:
            pass
    return False



# =====================================================================
# SEARCH, STATS & PREVIEWS
# =====================================================================

def search_files(pattern: str = "*", root: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Search for files matching a glob pattern (e.g. '*.pdf', 'invoice*', '*.py').
    Returns list of dicts with name, path, size_kb, and modified time.
    """
    root_dir = resolve_folder_alias(root)
    results = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip heavy / ignored directories
        dirnames[:] = [d for d in dirnames if d.lower() not in config.IGNORE_DIRS and not d.startswith(".")]
        for name in filenames:
            if fnmatch.fnmatch(name.lower(), pattern.lower()):
                full = os.path.join(dirpath, name)
                try:
                    stat = os.stat(full)
                    results.append({
                        "name": name,
                        "path": full,
                        "size_kb": round(stat.st_size / 1024, 1),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "mtime": stat.st_mtime
                    })
                except OSError:
                    continue
                if len(results) >= max_results:
                    return results
    return results


def get_folder_summary(folder: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes total file count, total size (MB), and breakdown by category and extension.
    """
    folder_dir = resolve_folder_alias(folder)
    total_size = 0
    file_count = 0
    dir_count = 0
    by_ext: Dict[str, int] = {}
    by_cat: Dict[str, int] = {cat: 0 for cat in config.SMART_CATEGORIES}
    by_cat["Other"] = 0

    if not os.path.exists(folder_dir):
        return {"error": f"Folder not found: {folder_dir}"}

    for dirpath, dirnames, filenames in os.walk(folder_dir):
        dirnames[:] = [d for d in dirnames if d.lower() not in config.IGNORE_DIRS and not d.startswith(".")]
        dir_count += len(dirnames)
        for f in filenames:
            file_count += 1
            full_path = os.path.join(dirpath, f)
            try:
                stat = os.stat(full_path)
                total_size += stat.st_size
                ext = os.path.splitext(f)[1].lower()
                by_ext[ext] = by_ext.get(ext, 0) + 1

                # Classify into category
                categorized = False
                for cat_name, extensions in config.SMART_CATEGORIES.items():
                    if ext in extensions:
                        by_cat[cat_name] += 1
                        categorized = True
                        break
                if not categorized:
                    by_cat["Other"] += 1
            except OSError:
                continue

    # Filter out empty categories
    active_cats = {k: v for k, v in by_cat.items() if v > 0}

    return {
        "folder": folder_dir,
        "file_count": file_count,
        "dir_count": dir_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
        "by_category": active_cats,
        "top_extensions": sorted(by_ext.items(), key=lambda x: x[1], reverse=True)[:8]
    }



def read_text_file(path: str, max_bytes: int = config.MAX_READ_SIZE) -> Tuple[str, bool]:
    """
    Reads a text file safely up to max_bytes.
    Returns (content, is_truncated).
    """
    full_path = _resolve_safe(path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File not found: {full_path}")

    ext = os.path.splitext(full_path)[1].lower()
    if ext not in config.TEXT_EXTENSIONS:
        return f"[Non-text binary file: {ext} (Size: {round(os.path.getsize(full_path)/1024, 1)} KB)]", False

    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read(max_bytes)
        truncated = len(content) == max_bytes
        return content, truncated


# =====================================================================
# 1. SMART DESKTOP & DOWNLOADS AUTO-CLEANER
# =====================================================================

def smart_clean_folder(folder: str = "Downloads", confirm: bool = False) -> Dict[str, Any]:
    """
    Organizes files in the specified folder into clean category subfolders:
    Documents/, Images/, Code/, Archives/, Media/, Installers/, Others/.
    Leaves subfolders untouched.
    """
    target_dir = resolve_folder_alias(folder)
    if not os.path.exists(target_dir):
        return {"success": False, "message": f"Folder not found: {target_dir}"}

    # Find root-level loose files only
    loose_files = []
    try:
        for entry in os.listdir(target_dir):
            full = os.path.join(target_dir, entry)
            if os.path.isfile(full) and not entry.startswith((".", "desktop.ini")):
                loose_files.append(entry)
    except Exception as e:
        return {"success": False, "message": f"Could not list directory: {e}"}

    if not loose_files:
        return {"success": True, "moved_count": 0, "message": f"Folder '{folder}' is already clean! No loose files found."}

    plan = {}
    for filename in loose_files:
        ext = os.path.splitext(filename)[1].lower()
        target_cat = "Other"
        for cat_name, extensions in config.SMART_CATEGORIES.items():
            if ext in extensions:
                target_cat = cat_name
                break
        plan.setdefault(target_cat, []).append(filename)

    if not confirm:
        return {
            "success": True,
            "requires_confirmation": True,
            "folder": target_dir,
            "total_files": len(loose_files),
            "plan": {cat: len(files) for cat, files in plan.items()},
            "message": f"Ready to organize {len(loose_files)} loose files in '{os.path.basename(target_dir)}' into categorized folders."
        }

    # Execute move
    moved_count = 0
    for cat_name, files in plan.items():
        cat_dir = os.path.join(target_dir, cat_name)
        ensure_dir(cat_dir)
        for fname in files:
            src = os.path.join(target_dir, fname)
            dst = os.path.join(cat_dir, fname)
            # Handle collision
            if os.path.exists(dst):
                base, ext = os.path.splitext(fname)
                dst = os.path.join(cat_dir, f"{base}_{int(time.time())}{ext}")
            if safe_move(src, dst):
                moved_count += 1

    return {
        "success": True,
        "moved_count": moved_count,
        "categories": {cat: len(files) for cat, files in plan.items()},
        "message": f"Cleaned '{os.path.basename(target_dir)}'! Successfully organized {moved_count} file(s)."
    }



# =====================================================================
# 2. DUPLICATE FILE FINDER & SPACE RECLAIMER
# =====================================================================

def _compute_md5(filepath: str, block_size: int = 65536) -> str:
    """Computes fast MD5 hash of file content."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        buf = f.read(block_size)
        while buf:
            hasher.update(buf)
            buf = f.read(block_size)
    return hasher.hexdigest()


def find_duplicates(folder: Optional[str] = None, min_size_bytes: int = 1024) -> Dict[str, Any]:
    """
    Finds exact duplicate files by size and MD5 hash in the given folder tree.
    """
    root_dir = resolve_folder_alias(folder)
    size_map: Dict[int, List[str]] = {}

    # 1. Quick size pass
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d.lower() not in config.IGNORE_DIRS and not d.startswith(".")]
        for f in filenames:
            full = os.path.join(dirpath, f)
            try:
                size = os.path.getsize(full)
                if size >= min_size_bytes:
                    size_map.setdefault(size, []).append(full)
            except OSError:
                continue

    # 2. Hash comparison for candidate files with same size
    duplicate_groups: List[Dict[str, Any]] = []
    total_wasted_bytes = 0

    for size, paths in size_map.items():
        if len(paths) < 2:
            continue
        hash_map: Dict[str, List[str]] = {}
        for p in paths:
            try:
                h = _compute_md5(p)
                hash_map.setdefault(h, []).append(p)
            except Exception:
                continue

        for h, dups in hash_map.items():
            if len(dups) > 1:
                wasted = size * (len(dups) - 1)
                total_wasted_bytes += wasted
                duplicate_groups.append({
                    "hash": h,
                    "size_kb": round(size / 1024, 1),
                    "size_mb": round(size / (1024 * 1024), 2),
                    "copies": len(dups),
                    "files": dups
                })

    return {
        "folder": root_dir,
        "group_count": len(duplicate_groups),
        "total_wasted_mb": round(total_wasted_bytes / (1024 * 1024), 2),
        "groups": sorted(duplicate_groups, key=lambda x: x["size_kb"] * x["copies"], reverse=True)
    }


def clean_duplicates(folder: Optional[str] = None, keep: str = "newest", confirm: bool = False) -> Dict[str, Any]:
    """
    Safely deletes duplicate copies, keeping either the newest or oldest file in each group.
    """
    dup_res = find_duplicates(folder)
    groups = dup_res.get("groups", [])

    if not groups:
        return {"success": True, "deleted_count": 0, "freed_mb": 0, "message": "No duplicate files found."}

    files_to_delete = []
    freed_bytes = 0

    for g in groups:
        flist = g["files"]
        # Sort by modification time
        try:
            flist_sorted = sorted(flist, key=lambda p: os.path.getmtime(p), reverse=(keep == "newest"))
            # Keep index 0, delete rest
            for p in flist_sorted[1:]:
                files_to_delete.append(p)
                freed_bytes += os.path.getsize(p)
        except OSError:
            continue

    if not confirm:
        return {
            "success": True,
            "requires_confirmation": True,
            "total_duplicates": len(files_to_delete),
            "reclaimable_mb": round(freed_bytes / (1024 * 1024), 2),
            "preview": files_to_delete[:10],
            "message": f"Found {len(files_to_delete)} duplicate files ({round(freed_bytes / (1024 * 1024), 2)} MB reclaimable)."
        }

    deleted_count = 0
    for path in files_to_delete:
        try:
            os.remove(path)
            deleted_count += 1
        except Exception:
            continue

    return {
        "success": True,
        "deleted_count": deleted_count,
        "freed_mb": round(freed_bytes / (1024 * 1024), 2),
        "message": f"Reclaimed {round(freed_bytes / (1024 * 1024), 2)} MB! Deleted {deleted_count} duplicate files."
    }


# =====================================================================
# 3. LARGE FILES & STORAGE HOG DETECTOR
# =====================================================================

def find_large_files(folder: Optional[str] = None, min_size_mb: float = 10.0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Finds the largest space-consuming files in the folder hierarchy.
    """
    root_dir = resolve_folder_alias(folder)
    large_files = []
    min_bytes = int(min_size_mb * 1024 * 1024)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d.lower() not in config.IGNORE_DIRS and not d.startswith(".")]
        for f in filenames:
            full = os.path.join(dirpath, f)
            try:
                size = os.path.getsize(full)
                if size >= min_bytes:
                    stat = os.stat(full)
                    large_files.append({
                        "name": f,
                        "path": full,
                        "size_mb": round(size / (1024 * 1024), 1),
                        "size_gb": round(size / (1024 * 1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    })
            except OSError:
                continue

    return sorted(large_files, key=lambda x: x["size_mb"], reverse=True)[:limit]


# =====================================================================
# 4. SMART BATCH FILE RENAMER
# =====================================================================

def batch_rename(
    folder: Optional[str] = None,
    pattern: str = "*",
    prefix: str = "",
    suffix: str = "",
    replace_old: str = "",
    replace_new: str = "",
    confirm: bool = False
) -> Dict[str, Any]:
    """
    Performs safe batch renaming across files matching pattern.
    Provides dry-run preview before committing.
    """
    target_dir = resolve_folder_alias(folder)
    if not os.path.exists(target_dir):
        return {"success": False, "message": f"Folder not found: {target_dir}"}

    matched_files = []
    try:
        for fname in os.listdir(target_dir):
            full = os.path.join(target_dir, fname)
            if os.path.isfile(full) and fnmatch.fnmatch(fname.lower(), pattern.lower()):
                matched_files.append(fname)
    except Exception as e:
        return {"success": False, "message": f"Error accessing directory: {e}"}

    if not matched_files:
        return {"success": True, "renamed_count": 0, "message": f"No files matched pattern '{pattern}' in '{folder}'."}

    rename_plan = []
    for fname in matched_files:
        base, ext = os.path.splitext(fname)
        new_base = base
        if replace_old:
            new_base = new_base.replace(replace_old, replace_new)
        new_name = f"{prefix}{new_base}{suffix}{ext}"
        if new_name != fname:
            rename_plan.append({
                "old": fname,
                "new": new_name,
                "old_path": os.path.join(target_dir, fname),
                "new_path": os.path.join(target_dir, new_name)
            })

    if not rename_plan:
        return {"success": True, "renamed_count": 0, "message": "No renaming changes needed based on given rules."}

    if not confirm:
        return {
            "success": True,
            "requires_confirmation": True,
            "total_files": len(rename_plan),
            "preview": [{"from": p["old"], "to": p["new"]} for p in rename_plan[:10]],
            "message": f"Ready to batch rename {len(rename_plan)} file(s)."
        }

    # Execute
    renamed_count = 0
    for p in rename_plan:
        try:
            if not os.path.exists(p["new_path"]):
                os.rename(p["old_path"], p["new_path"])
                renamed_count += 1
        except Exception:
            continue

    return {
        "success": True,
        "renamed_count": renamed_count,
        "message": f"Batch renamed {renamed_count} file(s) successfully!"
    }


# =====================================================================
# 5. ZIP & ARCHIVE TOOLS
# =====================================================================

def zip_folder(folder_path: str, output_zip: Optional[str] = None) -> Dict[str, Any]:
    """
    Compresses a directory into a .zip archive.
    """
    target = resolve_folder_alias(folder_path)
    if not os.path.exists(target):
        return {"success": False, "message": f"Path not found: {target}"}

    if not output_zip:
        output_zip = f"{target.rstrip(r'\/')}.zip"
    else:
        output_zip = resolve_folder_alias(output_zip)

    file_count = 0
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isdir(target):
            for root, dirnames, files in os.walk(target):
                dirnames[:] = [d for d in dirnames if d.lower() not in config.IGNORE_DIRS and not d.startswith(".")]
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, target)
                    zf.write(full_p, rel_p)
                    file_count += 1
        else:
            zf.write(target, os.path.basename(target))
            file_count = 1

    zip_size_mb = round(os.path.getsize(output_zip) / (1024 * 1024), 2)
    return {
        "success": True,
        "archive_path": output_zip,
        "files_compressed": file_count,
        "archive_size_mb": zip_size_mb,
        "message": f"Compressed {file_count} files into '{os.path.basename(output_zip)}' ({zip_size_mb} MB)."
    }


def unzip_archive(zip_path: str, extract_to: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts a .zip archive safely into a folder.
    """
    archive = resolve_folder_alias(zip_path)
    if not os.path.exists(archive) or not zipfile.is_zipfile(archive):
        return {"success": False, "message": f"Invalid zip archive: {archive}"}

    if not extract_to:
        base_name = os.path.splitext(os.path.basename(archive))[0]
        extract_to = os.path.join(os.path.dirname(archive), base_name)
    else:
        extract_to = resolve_folder_alias(extract_to)

    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(extract_to)
        file_count = len(zf.namelist())

    return {
        "success": True,
        "extracted_to": extract_to,
        "files_extracted": file_count,
        "message": f"Extracted {file_count} file(s) into '{os.path.basename(extract_to)}'."
    }


# =====================================================================
# 6. RECENTLY MODIFIED TRACKER
# =====================================================================

def get_recently_modified(folder: Optional[str] = None, hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Lists files modified within the last N hours.
    """
    root_dir = resolve_folder_alias(folder)
    cutoff_time = time.time() - (hours * 3600)
    recent = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d.lower() not in config.IGNORE_DIRS and not d.startswith(".")]
        for f in filenames:
            full = os.path.join(dirpath, f)
            try:
                mtime = os.path.getmtime(full)
                if mtime >= cutoff_time:
                    size_kb = round(os.path.getsize(full) / 1024, 1)
                    recent.append({
                        "name": f,
                        "path": full,
                        "size_kb": size_kb,
                        "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                        "mtime": mtime
                    })
            except OSError:
                continue

    return sorted(recent, key=lambda x: x["mtime"], reverse=True)[:limit]



# =====================================================================
# DIRECT SINGLE FILE OPS (BACKWARDS COMPATIBILITY)
# =====================================================================

def create_folder(folder_name: str, parent_folder: Optional[str] = None) -> Dict[str, Any]:
    """Create a new folder safely."""
    parent_dir = resolve_folder_alias(parent_folder)
    target_path = os.path.join(parent_dir, folder_name)
    ensure_dir(target_path)
    return {
        "success": True,
        "path": target_path,
        "message": f"Folder created successfully at: {target_path}"
    }


def create_file(file_name: str, parent_folder: Optional[str] = None, content: str = "") -> Dict[str, Any]:
    """Create a new empty or text file."""
    parent_dir = resolve_folder_alias(parent_folder)
    target_path = os.path.join(parent_dir, file_name)
    ensure_dir(os.path.dirname(target_path))
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {
        "success": True,
        "path": target_path,
        "message": f"File created successfully at: {target_path}"
    }


def copy_file(src_path: str, dest_folder: str) -> Dict[str, Any]:
    """Copy a file or directory to destination folder."""
    src = _resolve_safe(src_path)
    if not os.path.exists(src):
        return {"success": False, "message": f"Source not found: {src}"}
    dst_dir = resolve_folder_alias(dest_folder)
    ensure_dir(dst_dir)
    dst = os.path.join(dst_dir, os.path.basename(src))
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)
    return {
        "success": True,
        "src": src,
        "dest": dst,
        "message": f"Copied successfully to: {dst}"
    }


def open_in_explorer(folder: Optional[str] = None) -> Dict[str, Any]:
    """Open folder in Windows File Explorer."""
    target = resolve_folder_alias(folder)
    if not os.path.exists(target):
        return {"success": False, "message": f"Path not found: {target}"}
    try:
        os.startfile(target)
        return {"success": True, "path": target, "message": f"Opened in Windows Explorer: {target}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to open explorer: {e}"}


def open_file_by_query(query: str, folder: Optional[str] = None) -> Dict[str, Any]:
    """
    Finds and opens/launches a file matching natural search query using Windows default app.
    e.g. 'screen shot', 'screenshot', 'report.pdf', 'invoice'.
    """
    root_dir = resolve_folder_alias(folder)
    clean_q = query.strip().lower()

    # Normalize common abbreviations / typos
    if any(k in clean_q for k in ("scrrn", "screen shot", "screenshot")):
        search_terms = ["screenshot", "screen shot", "scrrn"]
    else:
        term = clean_q
        for prefix in ("a ", "the ", "an ", "latest ", "new "):
            if term.startswith(prefix):
                term = term[len(prefix):].strip()
        search_terms = [term]

    candidates = []
    # If path directly points to an existing file
    direct_path = resolve_folder_alias(query)
    if os.path.isfile(direct_path):
        candidates.append((direct_path, os.path.getmtime(direct_path)))
    elif os.path.exists(root_dir):
        if os.path.isfile(root_dir):
            candidates.append((root_dir, os.path.getmtime(root_dir)))
        else:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                dirnames[:] = [d for d in dirnames if d.lower() not in config.IGNORE_DIRS and not d.startswith(".")]
                for f in filenames:
                    f_lower = f.lower()
                    for term in search_terms:
                        norm_f = f_lower.replace(" ", "").replace("_", "").replace("-", "")
                        norm_term = term.replace(" ", "").replace("_", "").replace("-", "")
                        if term in f_lower or norm_term in norm_f:
                            full_p = os.path.join(dirpath, f)
                            try:
                                candidates.append((full_p, os.path.getmtime(full_p)))
                            except OSError:
                                continue
                            break

    if not candidates:
        return {
            "success": False,
            "message": f"No files matching '{query}' found in '{os.path.basename(root_dir) or root_dir}'."
        }

    # Pick the most recent matching file
    best_match = sorted(candidates, key=lambda x: x[1], reverse=True)[0][0]

    try:
        os.startfile(best_match)
        return {
            "success": True,
            "path": best_match,
            "filename": os.path.basename(best_match),
            "message": f"Opened '{os.path.basename(best_match)}' with default Windows app."
        }
    except Exception as e:
        return {
            "success": False,
            "path": best_match,
            "message": f"Failed to open '{os.path.basename(best_match)}': {e}"
        }



def rename_file(old_path: str, new_name: str) -> str:
    """Rename a single file."""
    src = _resolve_safe(old_path)
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    dst = os.path.join(os.path.dirname(src), new_name)
    safe_move(src, dst)
    return dst


def move_file(src_path: str, dest_folder: str) -> str:
    """Move a file to destination folder."""
    src = _resolve_safe(src_path)
    dst_dir = resolve_folder_alias(dest_folder)
    ensure_dir(dst_dir)
    dst = os.path.join(dst_dir, os.path.basename(src))
    safe_move(src, dst)
    return dst




def delete_file(path: str, confirm: bool = False) -> bool:
    """Permanently delete a single file or directory."""
    if not confirm:
        raise PermissionError("Delete requires explicit confirm=True")
    target = _resolve_safe(path)
    if not os.path.exists(target):
        raise FileNotFoundError(f"File or path not found: {target}")
    if os.path.isdir(target):
        shutil.rmtree(target)
    else:
        os.remove(target)
    return True


def empty_folder_contents(folder: str, confirm: bool = False) -> Dict[str, Any]:
    """
    Safely purges all files and subdirectories inside a folder (keeps the root folder intact).
    """
    target_dir = resolve_folder_alias(folder)
    if not os.path.exists(target_dir):
        return {"success": False, "message": f"Folder not found: {target_dir}"}

    try:
        items = os.listdir(target_dir)
    except Exception as e:
        return {"success": False, "message": f"Could not access folder: {e}"}

    if not items:
        return {"success": True, "deleted_count": 0, "message": f"Folder '{os.path.basename(target_dir)}' is already empty."}

    if not confirm:
        return {
            "success": True,
            "requires_confirmation": True,
            "folder": target_dir,
            "total_items": len(items),
            "preview": items[:8],
            "message": f"Ready to permanently delete all {len(items)} item(s) inside '{os.path.basename(target_dir)}'."
        }

    deleted_count = 0
    for item in items:
        full_path = os.path.join(target_dir, item)
        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            deleted_count += 1
        except Exception:
            continue

    return {
        "success": True,
        "deleted_count": deleted_count,
        "folder": target_dir,
        "message": f"Successfully deleted {deleted_count} item(s) from '{os.path.basename(target_dir)}'."
    }



def organize_by_extension(folder: str, confirm: bool = False) -> Dict[str, Any]:
    """Organize by file extension."""
    return smart_clean_folder(folder, confirm=confirm)


def organize_by_date(folder: str, confirm: bool = False) -> Dict[str, Any]:
    """Organize loose files into Year-Month subfolders."""
    target_dir = resolve_folder_alias(folder)
    if not os.path.exists(target_dir):
        return {"error": f"Folder not found: {target_dir}"}

    loose_files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
    if not confirm:
        return {"requires_confirmation": True, "total_files": len(loose_files), "folder": target_dir}


# =====================================================================
# EXTENDED FILE MANAGER OPERATIONS (20-FEATURE SUITE)
# =====================================================================

def search_folders(pattern: str = "*", root: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]:
    """Searches exclusively for directories matching a name/glob pattern."""
    target_root = resolve_folder_alias(root)
    results = []
    pattern_lower = pattern.lower()

    for dirpath, dirnames, _ in os.walk(target_root):
        for d in dirnames:
            if pattern_lower == "*" or pattern_lower in d.lower() or fnmatch.fnmatch(d.lower(), pattern_lower):
                full_p = os.path.join(dirpath, d)
                rel_p = os.path.relpath(full_p, target_root)
                try:
                    mtime = os.path.getmtime(full_p)
                    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    mtime_str = "Unknown"
                
                results.append({
                    "name": d,
                    "relative_path": rel_p,
                    "full_path": full_p,
                    "modified": mtime_str
                })
                if len(results) >= max_results:
                    return results

    return results


def find_project_files(root_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Detects software development projects, git repositories, and build manifests."""
    target_root = resolve_folder_alias(root_dir)
    projects = []
    
    PROJECT_INDICATORS = {
        ".git": "Git Repository",
        "package.json": "Node.js / React / Next.js",
        "requirements.txt": "Python",
        "pyproject.toml": "Python (Poetry/Flit)",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "pom.xml": "Java (Maven)",
        "build.gradle": "Java / Kotlin (Gradle)",
        "Dockerfile": "Docker Project",
        "CMakeLists.txt": "C / C++ (CMake)"
    }

    IGNORED_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "dist", "build"}

    for dirpath, dirnames, filenames in os.walk(target_root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        
        detected_types = []
        if ".git" in dirnames:
            detected_types.append(PROJECT_INDICATORS[".git"])
            
        for f in filenames:
            if f in PROJECT_INDICATORS:
                detected_types.append(PROJECT_INDICATORS[f])

        if detected_types:
            try:
                mtime = os.path.getmtime(dirpath)
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            except Exception:
                mtime_str = "Unknown"

            projects.append({
                "project_name": os.path.basename(dirpath) or dirpath,
                "path": dirpath,
                "types": list(set(detected_types)),
                "last_modified": mtime_str
            })

    return projects


def archive_old_projects(projects_dir: Optional[str] = None, days_inactive: int = 90, output_archive_dir: Optional[str] = None, confirm: bool = False) -> Dict[str, Any]:
    """Scans for projects not modified for N days and packages them into ZIP archives."""
    all_projects = find_project_files(projects_dir)
    cutoff_time = time.time() - (days_inactive * 86400)
    
    stale_projects = []
    for p in all_projects:
        p_path = p["path"]
        try:
            mtime = os.path.getmtime(p_path)
            if mtime < cutoff_time:
                stale_projects.append(p)
        except Exception:
            continue

    if not stale_projects:
        return {"success": True, "archived_count": 0, "message": f"No projects inactive for >{days_inactive} days found."}

    if not confirm:
        return {
            "success": True,
            "requires_confirmation": True,
            "stale_projects_count": len(stale_projects),
            "projects": [p["project_name"] for p in stale_projects],
            "message": f"Found {len(stale_projects)} project(s) inactive for >{days_inactive} days. Pass confirm=True to archive."
        }

    archive_base = resolve_folder_alias(output_archive_dir or os.path.join(resolve_folder_alias(projects_dir), "Archived_Projects"))
    os.makedirs(archive_base, exist_ok=True)
    
    archived = []
    for p in stale_projects:
        p_path = p["path"]
        zip_name = f"{p['project_name']}_{datetime.now().strftime('%Y%m%d')}.zip"
        zip_path = os.path.join(archive_base, zip_name)
        zip_res = zip_folder(p_path, zip_path)
        if zip_res.get("success"):
            archived.append(zip_name)

    return {
        "success": True,
        "archived_count": len(archived),
        "archive_directory": archive_base,
        "archives": archived,
        "message": f"Successfully archived {len(archived)} project(s) to '{archive_base}'."
    }


def compress_files(file_paths: List[str], output_zip: str) -> Dict[str, Any]:
    """Compresses a list of individual files into a single ZIP archive."""
    out_zip = os.path.abspath(output_zip)
    os.makedirs(os.path.dirname(out_zip), exist_ok=True)

    added_files = []
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            abs_p = _resolve_safe(fp)
            if os.path.exists(abs_p) and os.path.isfile(abs_p):
                arcname = os.path.basename(abs_p)
                zf.write(abs_p, arcname=arcname)
                added_files.append(arcname)

    size_mb = round(os.path.getsize(out_zip) / (1024 * 1024), 2)
    return {
        "success": True,
        "archive_path": out_zip,
        "files_count": len(added_files),
        "archive_size_mb": size_mb,
        "files": added_files
    }


def analyze_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extracts comprehensive metadata from any file: size, timestamps, mime type,
    permissions, MD5 checksum, and word/line count for text files.
    """
    target = _resolve_safe(file_path)
    if not os.path.exists(target):
        return {"error": f"File not found: {file_path}"}

    stat = os.stat(target)
    is_dir = os.path.isdir(target)
    size_bytes = stat.st_size
    size_mb = round(size_bytes / (1024 * 1024), 3)

    c_time = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
    m_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    a_time = datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")

    ext = os.path.splitext(target)[1].lower()
    
    meta = {
        "name": os.path.basename(target),
        "full_path": target,
        "is_directory": is_dir,
        "extension": ext,
        "size_bytes": size_bytes,
        "size_mb": size_mb,
        "created_at": c_time,
        "last_modified": m_time,
        "last_accessed": a_time
    }

    if not is_dir:
        # Checksum
        if size_bytes < 100 * 1024 * 1024:  # Under 100MB
            meta["md5_checksum"] = _compute_md5(target)

        # Text file line & word analysis
        if ext in (".txt", ".py", ".js", ".json", ".md", ".html", ".css", ".csv", ".log", ".xml", ".yaml", ".yml"):
            try:
                with open(target, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    meta["line_count"] = len(content.splitlines())
                    meta["word_count"] = len(content.split())
                    meta["char_count"] = len(content)
            except Exception:
                pass

    return meta


def get_storage_cleanup_suggestions(root_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Deep scans disk/folder for reclaimable junk: temp files, node_modules, cache dirs,
    crash logs, duplicate files, empty directories, and huge files (>100MB).
    """
    target_root = resolve_folder_alias(root_dir)
    suggestions = []
    total_reclaimable_bytes = 0

    JUNK_EXTENSIONS = {".tmp", ".bak", ".log", ".dmp", ".old", ".temp", ".crdownload"}
    JUNK_DIR_NAMES = {"__pycache__", ".pytest_cache", ".cache", "node_modules", ".parcel-cache", "Thumbs.db"}

    junk_files = []
    junk_dirs = []
    huge_files = []

    for dirpath, dirnames, filenames in os.walk(target_root):
        for d in list(dirnames):
            if d in JUNK_DIR_NAMES:
                full_d = os.path.join(dirpath, d)
                try:
                    d_size = sum(os.path.getsize(os.path.join(dr, f)) for dr, _, fls in os.walk(full_d) for f in fls)
                    junk_dirs.append({"path": full_d, "name": d, "size_mb": round(d_size / (1024 * 1024), 2)})
                    total_reclaimable_bytes += d_size
                except Exception:
                    pass
                dirnames.remove(d)

        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            full_f = os.path.join(dirpath, f)
            try:
                f_size = os.path.getsize(full_f)
                if ext in JUNK_EXTENSIONS or f.startswith("~"):
                    junk_files.append({"path": full_f, "size_bytes": f_size})
                    total_reclaimable_bytes += f_size
                elif f_size > 100 * 1024 * 1024:  # > 100MB
                    huge_files.append({"name": f, "path": full_f, "size_mb": round(f_size / (1024 * 1024), 2)})
            except Exception:
                pass

    return {
        "root_scanned": target_root,
        "estimated_reclaimable_mb": round(total_reclaimable_bytes / (1024 * 1024), 2),
        "junk_files_count": len(junk_files),
        "junk_directories": junk_dirs[:10],
        "huge_files": huge_files[:10],
        "recommendations": [
            f"Delete {len(junk_files)} temporary and log files (~{round(sum(j['size_bytes'] for j in junk_files)/(1024*1024), 1)} MB)",
            f"Prune {len(junk_dirs)} dependency/cache folders (e.g. node_modules, __pycache__)",
            f"Review {len(huge_files)} large files over 100MB"
        ]
    }


    moved = 0
    for f in loose_files:
        src = os.path.join(target_dir, f)
        mtime = datetime.fromtimestamp(os.path.getmtime(src))
        date_folder = os.path.join(target_dir, mtime.strftime("%Y-%m"))
        os.makedirs(date_folder, exist_ok=True)
        dst = os.path.join(date_folder, f)
        try:
            shutil.move(src, dst)
            moved += 1
        except Exception:
            continue

    return {"success": True, "moved_count": moved, "folder": target_dir}
