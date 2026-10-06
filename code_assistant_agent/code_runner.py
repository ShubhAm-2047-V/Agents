"""
code_runner.py
Optional helper to run Python snippets locally and capture output/errors -
useful for feeding real error messages back into the debug() function.

This is NEVER called automatically by code_assistant_agent.py - your
router must explicitly call run_python() and should only do so on code
the user has reviewed. AUTO_EXECUTE in config.py is off by default for
this reason.
"""

import subprocess
import tempfile
import os


def run_python(code, timeout=10):
    """
    Runs a Python code string in a subprocess and captures stdout/stderr.
    Returns dict: {success, stdout, stderr, returncode}

    Uses a real subprocess (not exec()) so a crashing/hanging script can't
    take down your main Orion process, and a timeout prevents infinite loops
    from hanging forever.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds (possible infinite loop).",
            "returncode": None
        }
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
