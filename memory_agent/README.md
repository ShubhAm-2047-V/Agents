# Orion Memory Agent

Local-first, zero-cost memory system for Orion. Stores facts in SQLite
(fully offline), and optionally uses Gemini Flash-Lite to decide what's
worth remembering.

## Setup

1. Copy this whole `memory_agent` folder into `E:\Orion\`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Add your free Gemini API key. Either:
   - Set an environment variable `GEMINI_API_KEY`, OR
   - Open `config.py` and paste your key directly into `GEMINI_API_KEY`

   Get a free key at: https://aistudio.google.com/apikey

4. Test it works:
   ```
   python test_memory.py
   ```

## How it fits into Orion

In your main router/orchestrator script:

```python
from memory_agent import memory_agent

# Before generating a response - pull relevant past context (offline, no API cost)
context = memory_agent.recall(user_input)

# Build your prompt to Gemini/phi3 with context injected, e.g.:
full_prompt = f"{context}\n\nUser: {user_input}"

# ... generate your actual assistant reply as normal ...

# After the reply - let it decide if anything's worth saving (1 API call, Flash-Lite)
memory_agent.remember(user_input, assistant_reply)
```

## Files

| File | Purpose |
|---|---|
| `memory_store.py` | SQLite storage - save/search/update/delete memories |
| `memory_agent.py` | Main logic - `recall()` and `remember()` functions |
| `embeddings.py` | Optional semantic search upgrade (off by default) |
| `config.py` | API key + settings |
| `test_memory.py` | Quick standalone test script |
| `data/orion_memory.db` | SQLite database (auto-created on first run) |

## Quota notes

- `recall()` runs **fully offline** - zero API calls, instant, no quota used
- `remember()` makes **one small API call** per conversation turn, using
  Flash-Lite (highest free-tier RPM). It skips very short exchanges
  automatically (e.g. "ok", "thanks") to save quota.
- Semantic search (`embeddings.py`) is off by default since keyword search
  already works with zero API cost. Turn on `USE_SEMANTIC_SEARCH = True`
  in `config.py` only if keyword matching starts missing things.

## Manually adding memories

Useful for onboarding facts you already know (name, business, preferences)
without spending an API call:

```python
from memory_agent import memory_agent
memory_agent.add_manual_memory("User's name is Shubham, runs Shubdeep Labs.", "personal")
```

## Managing memories

```python
memory_agent.list_memories()      # see everything stored
memory_agent.forget(memory_id)    # delete one by id
memory_agent.wipe_all()           # reset everything
```
