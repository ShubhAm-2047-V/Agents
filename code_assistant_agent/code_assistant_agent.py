"""
code_assistant_agent.py
Main entry point for Orion's Code Assistant Agent.

Comprehensive 20-Feature Engineering Intelligence System:
1. Explain code
2. Generate code
3. Fix bugs
4. Detect syntax errors
5. Detect logical errors
6. Refactor code
7. Generate documentation
8. Generate comments
9. Generate README
10. Generate API documentation
11. Create project structures
12. Analyze existing projects
13. Search codebase
14. Find duplicate code
15. Detect security problems
16. Optimize slow code
17. Generate unit tests
18. Run tests and explain failures
19. Git commit/branch assistance
20. Deploy projects
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional

try:
    from . import config, code_runner, code_analyzer
except ImportError:
    import config, code_runner, code_analyzer

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def _get_client():
    if not HAS_GENAI:
        raise RuntimeError("google-genai package is required for online AI code generation.")
    return genai.Client(api_key=config.GEMINI_API_KEY)


def _truncate(code: str) -> str:
    if len(code) > config.MAX_CODE_CHARS:
        return code[:config.MAX_CODE_CHARS] + "\n\n# [TRUNCATED - file exceeds length limit]"
    return code


# =====================================================================
# 1. EXPLAIN CODE
# =====================================================================
def explain_code(code: str, language: str = "python") -> str:
    """Returns a clear, structured plain-language explanation of code logic, flow, and edge cases."""
    code = _truncate(code)
    prompt = f"""Explain what this {language} code does in plain language.
Structure the response as:
1. **Purpose & Architecture Overview** (1-2 sentences)
2. **Step-by-Step Logic Breakdown** (bullet points)
3. **Key Dependencies & Inputs/Outputs**
4. **Notable Edge Cases, Assumptions, or Quirks**

CODE:
```{language}
{code}
```
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_FAST, contents=prompt)
    return response.text.strip()


# =====================================================================
# 2. GENERATE CODE
# =====================================================================
def generate_code(spec: str, language: str = "python", framework: Optional[str] = None, strong_model: bool = False) -> str:
    """Generates clean, production-ready code from a specification."""
    model = config.MODEL_STRONG if strong_model else config.MODEL_FAST
    framework_hint = f" using {framework}" if framework else ""
    prompt = f"""Write high-quality, production-ready {language}{framework_hint} code for the following specification.
Include clear inline comments, robust error handling, and type annotations where applicable.
Return the code in a clean code block with a one-sentence usage example at the top.

SPECIFICATION:
{spec}
"""
    client = _get_client()
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text.strip()


# =====================================================================
# 3. FIX BUGS
# =====================================================================
def fix_bugs(code: str, error_message: Optional[str] = None, language: str = "python", strong_model: bool = True) -> str:
    """Finds root cause of bugs and provides fully corrected code."""
    model = config.MODEL_STRONG if strong_model else config.MODEL_FAST
    code = _truncate(code)
    err_context = f"\nERROR OUTPUT / TRACEBACK:\n{error_message}\n" if error_message else "\nNo error message provided - analyze statically.\n"
    prompt = f"""You are an expert software debugger for {language}.
Identify the root cause of the bug and fix it completely.

Structure:
1. **Root Cause Diagnosis**: Exactly what went wrong.
2. **Corrected Code**: Full fixed snippet.
3. **Prevention Advice**: How to prevent similar issues.

CODE:
```{language}
{code}
```
{err_context}
"""
    client = _get_client()
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text.strip()


# Alias for backwards compatibility
debug_code = fix_bugs
write_code = generate_code


# =====================================================================
# 4. DETECT SYNTAX ERRORS
# =====================================================================
def detect_syntax_errors(code: str, language: str = "python") -> Dict[str, Any]:
    """Inspects code for syntax errors, bracket mismatches, and parsing failures."""
    local_check = code_analyzer.check_syntax(code, language)
    if not local_check["valid"]:
        return {
            "has_syntax_errors": True,
            "error_message": local_check["error"],
            "line": local_check.get("line"),
            "offset": local_check.get("offset"),
            "snippet": local_check.get("text", "")
        }

    # If local check passes or for non-python languages, optionally verify with AI
    return {
        "has_syntax_errors": False,
        "error_message": "No syntax errors detected. AST parsed cleanly.",
        "line": None,
        "offset": None
    }


# =====================================================================
# 5. DETECT LOGICAL ERRORS
# =====================================================================
def detect_logical_errors(code: str, language: str = "python", expected_behavior: Optional[str] = None) -> str:
    """Analyzes off-by-one errors, infinite loops, race conditions, edge case failures, unhandled nulls."""
    code = _truncate(code)
    exp_block = f"\nEXPECTED BEHAVIOR: {expected_behavior}\n" if expected_behavior else ""
    prompt = f"""Perform a deep logic analysis of this {language} code.
Check specifically for:
- Off-by-one errors & boundary conditions
- Infinite loops or unhandled recursion termination
- Null / None / undefined pointer dereferences
- Race conditions or state mutation leaks
- Unreachable code branches or incorrect boolean operators

CODE:
```{language}
{code}
```
{exp_block}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_STRONG, contents=prompt)
    return response.text.strip()


# =====================================================================
# 6. REFACTOR CODE
# =====================================================================
def refactor_code(code: str, goals: str = "clean architecture, readability, DRY, performance", language: str = "python") -> str:
    """Refactors code applying modern patterns, clean architecture, and SOLID principles."""
    code = _truncate(code)
    prompt = f"""Refactor the following {language} code to improve: {goals}.
Maintain exact functional equivalence while simplifying logic, removing redundancies, and adhering to best practices.

CODE:
```{language}
{code}
```
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_STRONG, contents=prompt)
    return response.text.strip()


# =====================================================================
# 7. GENERATE DOCUMENTATION
# =====================================================================
def generate_documentation(code: str, doc_type: str = "markdown", language: str = "python") -> str:
    """Generates comprehensive documentation (docstrings, markdown reference, JSDoc, Sphinx)."""
    code = _truncate(code)
    prompt = f"""Generate comprehensive {doc_type} documentation for the following {language} code.
Include:
- Module summary
- Function / Class signatures, parameters, types, and return values
- Usage examples
- Raised exceptions / error codes

CODE:
```{language}
{code}
```
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_FAST, contents=prompt)
    return response.text.strip()


# =====================================================================
# 8. GENERATE COMMENTS
# =====================================================================
def generate_comments(code: str, style: str = "concise", language: str = "python") -> str:
    """Adds clear, meaningful inline comments explaining non-trivial logic."""
    code = _truncate(code)
    prompt = f"""Add informative, professional inline comments to this {language} code ({style} style).
Explain 'why' things are done, rather than just restating obvious code syntax.
Return ONLY the commented code block.

CODE:
```{language}
{code}
```
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_FAST, contents=prompt)
    return response.text.strip()


# =====================================================================
# 9. GENERATE README
# =====================================================================
def generate_readme(project_name: str, description: str, tech_stack: Optional[List[str]] = None, features: Optional[List[str]] = None, repo_dir: Optional[str] = None) -> str:
    """Generates a production-grade README.md with badges, architecture, setup guide, and usage."""
    scanned_info = ""
    if repo_dir and os.path.exists(repo_dir):
        summary = code_analyzer.scan_project_structure(repo_dir)
        scanned_info = f"\nPROJECT STRUCTURE DETECTED:\n{summary['directory_tree']}\nTech: {summary['tech_stack']}\n"

    prompt = f"""Generate a polished, professional README.md for a project named '{project_name}'.
DESCRIPTION: {description}
TECH STACK: {', '.join(tech_stack) if tech_stack else 'Detect from context'}
FEATURES: {', '.join(features) if features else 'Derive standard full-stack features'}
{scanned_info}

Include:
- Title & Badges
- Overview & Highlights
- Architecture & Project Structure
- Prerequisites & Installation
- Configuration (.env variables)
- Usage / Quickstart Commands
- Testing & Deployment
- License & Contributing
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_STRONG, contents=prompt)
    return response.text.strip()


# =====================================================================
# 10. GENERATE API DOCUMENTATION
# =====================================================================
def generate_api_documentation(code_or_endpoints: str, format_type: str = "markdown") -> str:
    """Generates API documentation table, OpenAPI/Swagger specifications, and curl examples."""
    prompt = f"""Generate complete API documentation in {format_type} format for the following endpoints / code.
Include:
- HTTP Method & Path
- Authentication Requirements
- Headers, Query Parameters & Path Parameters
- Request Body Schema (JSON) with example payload
- Success (200/201) and Error (400/401/404/500) Response Schemas
- Example `curl` command for each endpoint

INPUT:
{code_or_endpoints}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_FAST, contents=prompt)
    return response.text.strip()


# =====================================================================
# 11. CREATE PROJECT STRUCTURES
# =====================================================================
def create_project_structure(project_name: str, project_type: str = "fastapi", target_dir: Optional[str] = None) -> Dict[str, Any]:
    """Scaffolds directory structures and starter files on disk."""
    base_dir = os.path.abspath(target_dir or os.path.join(os.getcwd(), "projects", project_name))
    os.makedirs(base_dir, exist_ok=True)

    templates = {
        "fastapi": {
            "dirs": ["app", "app/api", "app/core", "app/models", "app/schemas", "tests"],
            "files": {
                "main.py": "from fastapi import FastAPI\n\napp = FastAPI(title='" + project_name + "')\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello from " + project_name + "'}\n",
                "requirements.txt": "fastapi>=0.100.0\nuvicorn[standard]>=0.23.0\npydantic>=2.0\npytest>=7.0.0\n",
                ".env.example": "PORT=8000\nENV=development\nSECRET_KEY=change_me\n",
                "README.md": f"# {project_name}\n\nFastAPI backend service.\n\n## Quickstart\n```bash\npip install -r requirements.txt\nuvicorn main:app --reload\n```\n"
            }
        },
        "flask": {
            "dirs": ["app", "app/templates", "app/static", "tests"],
            "files": {
                "app.py": "from flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.route('/')\ndef index():\n    return jsonify({'status': 'running', 'app': '" + project_name + "'})\n\nif __name__ == '__main__':\n    app.run(debug=True, port=5000)\n",
                "requirements.txt": "flask>=3.0.0\npytest>=7.0.0\n",
                "README.md": f"# {project_name}\n\nFlask application.\n"
            }
        },
        "cli": {
            "dirs": ["src", "tests"],
            "files": {
                "src/cli.py": "import sys\n\ndef main():\n    print('Running " + project_name + " CLI')\n\nif __name__ == '__main__':\n    main()\n",
                "requirements.txt": "colorama\nclick\n",
                "README.md": f"# {project_name} CLI\n"
            }
        },
        "react": {
            "dirs": ["src", "src/components", "src/pages", "src/assets", "public"],
            "files": {
                "src/App.jsx": "export default function App() {\n  return <div><h1>Welcome to " + project_name + "</h1></div>;\n}\n",
                "package.json": '{\n  "name": "' + project_name.lower() + '",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build"\n  }\n}\n',
                "README.md": f"# {project_name}\n\nReact application.\n"
            }
        }
    }

    t_key = project_type.lower().strip()
    tmpl = templates.get(t_key, templates["fastapi"])

    created_dirs = []
    created_files = []

    for d in tmpl["dirs"]:
        dp = os.path.join(base_dir, d)
        os.makedirs(dp, exist_ok=True)
        created_dirs.append(d)

    for f_rel, content in tmpl["files"].items():
        fp = os.path.join(base_dir, f_rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        if not os.path.exists(fp):
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            created_files.append(f_rel)

    return {
        "success": True,
        "project_name": project_name,
        "project_type": project_type,
        "root_directory": base_dir,
        "directories": created_dirs,
        "files": created_files
    }


# =====================================================================
# 12. ANALYZE EXISTING PROJECTS
# =====================================================================
def analyze_project(project_dir: str) -> Dict[str, Any]:
    """Scans and analyzes an entire project codebase structure, lines of code, and tech stack."""
    return code_analyzer.scan_project_structure(project_dir)


# =====================================================================
# 13. SEARCH CODEBASE
# =====================================================================
def search_codebase(query: str, project_dir: str, file_types: Optional[List[str]] = None, is_regex: bool = False) -> List[Dict[str, Any]]:
    """Searches for keywords, function definitions, or regex patterns across files."""
    return code_analyzer.search_codebase(query, project_dir, file_types=file_types, is_regex=is_regex)


# =====================================================================
# 14. FIND DUPLICATE CODE
# =====================================================================
def find_duplicate_code(project_dir: str, min_lines: int = 6) -> List[Dict[str, Any]]:
    """Finds repeated/copy-pasted blocks of code across repository files."""
    return code_analyzer.find_duplicate_code(project_dir, min_lines=min_lines)


# =====================================================================
# 15. DETECT SECURITY PROBLEMS
# =====================================================================
def detect_security_problems(code_or_path: str, language: str = "python") -> str:
    """Audits code for vulnerabilities, injection risks, hardcoded secrets, and unsafe dependencies."""
    content = code_or_path
    if os.path.exists(code_or_path) and os.path.isfile(code_or_path):
        with open(code_or_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

    content = _truncate(content)
    prompt = f"""Conduct a comprehensive application security audit on this {language} code.
Check for:
1. **Hardcoded Secrets**: API keys, passwords, bearer tokens, private keys
2. **Injection Vulnerabilities**: SQL injection, Command injection, XSS, Template injection
3. **Insecure Deserialization / Execution**: `eval()`, `exec()`, `pickle.loads()`, `yaml.load()` without SafeLoader
4. **Authentication / Authorization & Cryptography Flaws**: Weak hashing (MD5/SHA1), CORS misconfigurations
5. **Path Traversal & Unvalidated File Operations**

CODE:
```{language}
{content}
```
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_STRONG, contents=prompt)
    return response.text.strip()


# =====================================================================
# 16. OPTIMIZE SLOW CODE
# =====================================================================
def optimize_slow_code(code: str, focus: str = "speed and memory complexity", language: str = "python") -> str:
    """Identifies bottlenecks, calculates Big-O complexity, and generates optimized alternatives."""
    code = _truncate(code)
    prompt = f"""Analyze and optimize this {language} code for {focus}.
Structure:
1. **Complexity Analysis**: Current Time & Space Complexity (Big-O)
2. **Bottlenecks Identified**: Inefficient loops, duplicate calculations, unnecessary allocations
3. **Optimized Solution**: Drop-in replacement code with explanation of improvements
4. **Optimized Big-O**: New Time & Space Complexity

CODE:
```{language}
{code}
```
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_STRONG, contents=prompt)
    return response.text.strip()


# =====================================================================
# 17. GENERATE UNIT TESTS
# =====================================================================
def generate_unit_tests(code: str, framework: str = "pytest", language: str = "python") -> str:
    """Generates complete unit tests including edge cases, mock objects, and happy paths."""
    code = _truncate(code)
    prompt = f"""Write a comprehensive test suite using {framework} for the following {language} code.
Requirements:
- Happy path tests
- Boundary and edge cases (empty inputs, None, large numbers, invalid types)
- Exception raising / error scenario assertions
- Clear test names and docstrings
- Mocking for external I/O or network dependencies

CODE:
```{language}
{code}
```
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_STRONG, contents=prompt)
    return response.text.strip()


# =====================================================================
# 18. RUN TESTS AND EXPLAIN FAILURES
# =====================================================================
def run_tests_and_explain(test_target: str = "", framework: str = "pytest", cwd: Optional[str] = None) -> str:
    """Runs test suite and uses AI reasoning to diagnose failures and suggest instant fixes."""
    run_res = code_analyzer.run_unit_tests(test_target, framework, cwd)
    if run_res["success"]:
        return f"✅ All tests PASSED successfully!\n\nOutput:\n{run_res['stdout']}"

    # Diagnose failures
    prompt = f"""The following test suite failed. Diagnose the failures and provide exact fixes.
STDOUT:
{run_res['stdout']}

STDERR:
{run_res['stderr']}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_FAST, contents=prompt)
    return f"❌ Test Failures Detected:\n\n{response.text.strip()}"


# =====================================================================
# 19. GIT COMMIT / BRANCH ASSISTANCE
# =====================================================================
def git_assistance(action: str = "commit_message", repo_dir: Optional[str] = None, context: Optional[str] = None) -> str:
    """Generates conventional git commit messages, branch names, and PR summaries."""
    status_info = code_analyzer.get_git_status_and_diff(repo_dir)
    diff_text = status_info.get("diff_content", "") or status_info.get("diff_stat", "") or (context or "No diff detected")

    prompt = f"""You are a Git workflow expert. Assist with: {action.upper()}
Repository Status:
- Branch: {status_info.get('branch', 'unknown')}
- Modified Files:\n{status_info.get('status', 'none')}

GIT DIFF / CONTEXT:
{diff_text}

Provide:
1. Recommended {action} (e.g. Conventional Commit format `feat(scope): ...` or `fix(...)`)
2. Alternative options
3. Ready-to-copy shell commands
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_FAST, contents=prompt)
    return response.text.strip()


# =====================================================================
# 20. DEPLOY PROJECTS
# =====================================================================
def deploy_project(project_type: str = "docker", project_dir: Optional[str] = None, port: int = 8000) -> str:
    """Generates deployment scripts, Dockerfile, docker-compose.yml, or CI/CD GitHub Actions."""
    scanned = {}
    if project_dir and os.path.exists(project_dir):
        scanned = code_analyzer.scan_project_structure(project_dir)

    prompt = f"""Generate production deployment configurations for a {project_type.upper()} deployment.
Project Info: {scanned.get('tech_stack', 'Standard Web Service')}
Exposed Port: {port}

Provide:
1. Complete, optimized Multi-Stage `Dockerfile` with minimal image size and non-root user
2. `docker-compose.yml` with health checks and restart policies
3. `.dockerignore`
4. GitHub Actions CI/CD workflow (`.github/workflows/deploy.yml`)
5. Step-by-step launch commands
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL_STRONG, contents=prompt)
    return response.text.strip()


# Legacy aliases & helper functions
def review_code(code: str, language: str = "python") -> str:
    return refactor_code(code, goals="general code review, bugs, style, and performance", language=language)


def debug_with_execution(code: str, language: str = "python") -> str:
    if language.lower() != "python":
        raise ValueError("debug_with_execution currently only supports Python")
    result = code_runner.run_python(code)
    if result["success"]:
        return "Code ran successfully with no errors:\n\n" + (result["stdout"] or "(no output)")
    return fix_bugs(code, error_message=result["stderr"], language=language)


if __name__ == "__main__":
    print("========================================")
    print("  Orion Code Assistant Agent (Interactive)")
    print("========================================")
    print("All 20 Features Activated.")
    print("Commands:")
    print("  - 'generate <spec>'")
    print("  - 'explain <code>'")
    print("  - 'syntax <code>'")
    print("  - 'logic <code>'")
    print("  - 'refactor <code>'")
    print("  - 'security <code>'")
    print("  - 'optimize <code>'")
    print("  - 'test <code>'")
    print("  - 'structure <name>'")
    print("  - 'git'")
    print("  - 'deploy <type>'")
    print("  - 'exit' to quit\n")
