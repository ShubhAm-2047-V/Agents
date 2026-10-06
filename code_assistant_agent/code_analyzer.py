"""
code_analyzer.py
Local static analysis, AST inspection, codebase scanner, test runner,
and Git assistant for Orion's Code Assistant Agent.
"""

import os
import ast
import re
import json
import difflib
import subprocess
from typing import Dict, Any, List, Optional, Tuple


def check_syntax(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Checks syntax errors locally without network calls.
    Uses Python's ast parser for Python code, and pattern/bracket matching for other languages.
    """
    lang = language.lower().strip()
    if lang in ("python", "py"):
        try:
            ast.parse(code)
            return {"valid": True, "error": None, "line": None, "offset": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e.msg),
                "line": e.lineno,
                "offset": e.offset,
                "text": e.text.strip() if e.text else ""
            }
        except Exception as e:
            return {"valid": False, "error": str(e), "line": None, "offset": None}

    # Bracket matching validator for JS/TS/C/C++/Java/Go/Rust
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    lines = code.splitlines()
    for line_no, line in enumerate(lines, 1):
        for col_no, char in enumerate(line, 1):
            if char in '({[':
                stack.append((char, line_no, col_no))
            elif char in ')}]':
                if not stack:
                    return {
                        "valid": False,
                        "error": f"Unmatched closing bracket '{char}'",
                        "line": line_no,
                        "offset": col_no
                    }
                last_char, l_no, c_no = stack.pop()
                if pairs[char] != last_char:
                    return {
                        "valid": False,
                        "error": f"Mismatched bracket: expected match for '{last_char}' from line {l_no}, found '{char}'",
                        "line": line_no,
                        "offset": col_no
                    }

    if stack:
        unclosed_char, l_no, c_no = stack[-1]
        return {
            "valid": False,
            "error": f"Unclosed bracket '{unclosed_char}' opened at line {l_no}:{c_no}",
            "line": l_no,
            "offset": c_no
        }

    return {"valid": True, "error": None, "line": None, "offset": None}


def scan_project_structure(project_dir: str) -> Dict[str, Any]:
    """
    Scans an entire directory tree and extracts file types, dependencies,
    total lines of code, and architecture overview.
    """
    abs_root = os.path.abspath(project_dir)
    if not os.path.exists(abs_root):
        return {"error": f"Directory not found: {project_dir}"}

    IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next", ".idea", ".vscode"}
    
    file_counts = {}
    total_files = 0
    total_lines = 0
    key_files = []
    tree = []

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        rel_root = os.path.relpath(root, abs_root)
        level = 0 if rel_root == "." else rel_root.count(os.sep) + 1

        if level <= 3:
            indent = "  " * level
            folder_name = os.path.basename(root) if rel_root != "." else os.path.basename(abs_root)
            tree.append(f"{indent}[Dir] {folder_name}/")

        for f in files:
            ext = os.path.splitext(f)[1].lower() or "no_ext"
            file_counts[ext] = file_counts.get(ext, 0) + 1
            total_files += 1

            if f.lower() in ("package.json", "requirements.txt", "pyproject.toml", "cargo.toml", "go.mod", "dockerfile", "readme.md", "app.py", "main.py", "index.js", "index.ts"):
                key_files.append(os.path.join(rel_root, f))

            if level <= 3:
                indent = "  " * (level + 1)
                tree.append(f"{indent}- {f}")

            # Count lines for source files
            if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".sql", ".md", ".java", ".c", ".cpp", ".go", ".rs"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fl:
                        total_lines += sum(1 for _ in fl)
                except Exception:
                    pass

    # Detect tech stack
    tech_stack = []
    if os.path.exists(os.path.join(abs_root, "package.json")):
        tech_stack.append("Node.js / JavaScript")
    if os.path.exists(os.path.join(abs_root, "requirements.txt")) or os.path.exists(os.path.join(abs_root, "pyproject.toml")):
        tech_stack.append("Python")
    if os.path.exists(os.path.join(abs_root, "Cargo.toml")):
        tech_stack.append("Rust")
    if os.path.exists(os.path.join(abs_root, "go.mod")):
        tech_stack.append("Go")
    if os.path.exists(os.path.join(abs_root, "Dockerfile")):
        tech_stack.append("Docker")

    return {
        "project_name": os.path.basename(abs_root),
        "root_path": abs_root,
        "total_files": total_files,
        "total_lines_of_code": total_lines,
        "extensions": file_counts,
        "tech_stack": tech_stack or ["Generic / Unknown"],
        "key_files": key_files,
        "directory_tree": "\n".join(tree[:60]) + ("\n  ... (truncated)" if len(tree) > 60 else "")
    }


def search_codebase(query: str, project_dir: str, file_types: Optional[List[str]] = None, is_regex: bool = False) -> List[Dict[str, Any]]:
    """Searches for a text or regex pattern across codebase files."""
    abs_root = os.path.abspath(project_dir)
    results = []
    if not os.path.exists(abs_root):
        return results

    IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    pattern = re.compile(query, re.IGNORECASE) if is_regex else None
    query_lower = query.lower()

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if file_types and ext not in file_types:
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, abs_root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    for line_no, line in enumerate(file_obj, 1):
                        matched = False
                        if is_regex and pattern.search(line):
                            matched = True
                        elif not is_regex and query_lower in line.lower():
                            matched = True

                        if matched:
                            results.append({
                                "file": rel_path,
                                "full_path": full_path,
                                "line_number": line_no,
                                "line_content": line.strip()
                            })
                            if len(results) >= 100:
                                return results
            except Exception:
                continue

    return results


def find_duplicate_code(project_dir: str, min_lines: int = 6) -> List[Dict[str, Any]]:
    """
    Scans the repository to find duplicated code blocks across files.
    """
    abs_root = os.path.abspath(project_dir)
    code_blocks = {}
    duplicates = []
    IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    VALID_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp"}

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            if os.path.splitext(f)[1].lower() in VALID_EXTS:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, abs_root)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fl:
                        lines = [line.strip() for line in fl.readlines() if line.strip() and not line.strip().startswith(("#", "//", "/*"))]
                    
                    for i in range(len(lines) - min_lines + 1):
                        block = "\n".join(lines[i:i + min_lines])
                        if len(block) > 50:
                            if block in code_blocks:
                                prev_file, prev_line = code_blocks[block]
                                if prev_file != rel_path:
                                    duplicates.append({
                                        "file1": prev_file,
                                        "line1": prev_line,
                                        "file2": rel_path,
                                        "line2": i + 1,
                                        "lines_count": min_lines,
                                        "sample": block[:150] + "..."
                                    })
                            else:
                                code_blocks[block] = (rel_path, i + 1)
                except Exception:
                    continue

    return duplicates[:20]


def run_unit_tests(test_target: str = "", framework: str = "pytest", cwd: Optional[str] = None) -> Dict[str, Any]:
    """Runs tests via pytest or unittest subprocess and returns test execution metrics."""
    work_dir = cwd or os.getcwd()
    cmd = []
    if framework.lower() == "pytest":
        cmd = ["pytest", test_target] if test_target else ["pytest"]
    elif framework.lower() == "unittest":
        cmd = ["python", "-m", "unittest", test_target] if test_target else ["python", "-m", "unittest", "discover"]
    else:
        cmd = ["npm", "test"]

    try:
        res = subprocess.run(
            cmd,
            cwd=work_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=40
        )
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "returncode": res.returncode
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def get_git_status_and_diff(repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """Inspects local git repository status, branch name, and uncommitted diff."""
    work_dir = repo_dir or os.getcwd()
    try:
        branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=work_dir, shell=True, capture_output=True, text=True)
        branch = branch_res.stdout.strip() if branch_res.returncode == 0 else "unknown"

        status_res = subprocess.run(["git", "status", "--short"], cwd=work_dir, shell=True, capture_output=True, text=True)
        status = status_res.stdout.strip() if status_res.returncode == 0 else ""

        diff_res = subprocess.run(["git", "diff", "--stat"], cwd=work_dir, shell=True, capture_output=True, text=True)
        diff_stat = diff_res.stdout.strip() if diff_res.returncode == 0 else ""

        raw_diff = subprocess.run(["git", "diff"], cwd=work_dir, shell=True, capture_output=True, text=True)
        diff_content = raw_diff.stdout[:6000] if raw_diff.returncode == 0 else ""

        return {
            "is_git_repo": True,
            "branch": branch,
            "status": status,
            "diff_stat": diff_stat,
            "diff_content": diff_content
        }
    except Exception as e:
        return {"is_git_repo": False, "error": str(e)}
