# Orion Code Assistant Agent

Writes, explains, debugs, and reviews code using Gemini. Defaults to
Flash-Lite for speed/quota, but debugging uses Flash by default since
bug-fixing benefits more from stronger reasoning.

## ⚠️ Safety note

`debug_with_execution()` actually **runs** Python code locally in a
subprocess to capture a real error message. It's opt-in only (you call it
explicitly) and never triggered automatically. Only use it on code you or
the user has already looked at - don't wire it to blindly execute
AI-generated code with no review step in between.

## Setup

1. Copy this whole `code_assistant_agent` folder into `E:\Orion\`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Add your free Gemini API key - either:
   - Set an environment variable `GEMINI_API_KEY`, OR
   - Paste it directly into `config.py`

4. Test it:
   ```
   python test_code_assistant.py
   ```

## How it fits into Orion

```python
from code_assistant_agent import code_assistant_agent as coder

# Generate code from a spec
code = coder.write_code("a function that merges two sorted lists", language="python")

# Explain unfamiliar code
explanation = coder.explain_code(some_code)

# Debug with just the code (AI guesses the bug)
fix = coder.debug_code(broken_code)

# Debug with an actual error message (much more accurate)
fix = coder.debug_code(broken_code, error_message=traceback_text)

# Quick review/style check
notes = coder.review_code(some_code)

# Debug by actually running the code first to get a real traceback
# (opt-in, executes code locally - see safety note above)
result = coder.debug_with_execution(broken_code)
```

## Files

| File | Purpose |
|---|---|
| `code_assistant_agent.py` | Main agent - write/explain/debug/review functions |
| `code_runner.py` | Optional sandboxed subprocess runner for real error capture |
| `config.py` | API key, model selection, truncation limit |
| `test_code_assistant.py` | Test script |

## Functions reference

- `write_code(spec, language="python", strong_model=False)` - generate code from a description
- `explain_code(code, language="python")` - plain-language explanation
- `debug_code(code, error_message=None, language="python", strong_model=True)` - find + fix bugs
- `review_code(code, language="python")` - style/bug/performance review
- `debug_with_execution(code, language="python")` - runs code locally, then debugs using the real error

Every function makes exactly **one** Gemini API call.

## Quota notes

- `write_code`, `explain_code`, and `review_code` default to **Flash-Lite**
  (higher free-tier RPM) since they're usually quick, low-stakes calls.
- `debug_code` defaults to **Flash** (stronger reasoning, lower RPM) since
  bad fixes waste more of your time than a slightly slower response.
  Pass `strong_model=False` to use Flash-Lite instead if you're debugging
  something simple and want to save quota.
- Long code is truncated at `config.MAX_CODE_CHARS` (12,000 chars) with a
  clear note added, so a huge file doesn't blow up your prompt size or
  eat excessive tokens per call.
