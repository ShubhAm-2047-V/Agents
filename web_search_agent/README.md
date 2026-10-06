# Orion Web Search Agent

Searches the web for free (DuckDuckGo, no API key needed) and uses Gemini
Flash-Lite to summarize results into a clean spoken-style answer.

## Setup

1. Copy this whole `web_search_agent` folder into `E:\Orion\`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Add your free Gemini API key - either:
   - Set an environment variable `GEMINI_API_KEY`, OR
   - Paste it directly into `config.py`

   (No key needed for search itself - DuckDuckGo search via `ddgs` is free
   and unauthenticated.)

4. Test it:
   ```
   python test_web_search.py
   ```

## How it fits into Orion

```python
from web_search_agent import web_search_agent as web

# Zero-cost raw search (no summarization)
results = web.raw_search("who is the CEO of OpenAI")

# AI-summarized answer (1 API call)
answer = web.answer_query("who is the CEO of OpenAI")

# Deeper answer - fetches full page text from top results (still 1 API call,
# just more tokens/slower since it reads full articles, not just snippets)
answer = web.answer_query("explain the new UPI rules 2026", deep=True)

# News digest (1 API call)
news = web.get_news_summary("Indian tech layoffs")

# For contested/fast-changing topics - explicitly flags disagreement
# between sources instead of blending into one confident answer
comparison = web.compare_sources("current RBI repo rate")
```

## Files

| File | Purpose |
|---|---|
| `search_backend.py` | Free DuckDuckGo search + page text fetcher (no API key) |
| `web_search_agent.py` | AI layer - summarizes/compares search results via Gemini |
| `config.py` | API key, result count, timeouts |
| `test_web_search.py` | Test script |

## Functions reference

**Zero-cost (no Gemini API call):**
- `raw_search(query, max_results=5)` - list of `{title, url, snippet}`
- `raw_news(query, max_results=5)` - list of `{title, url, snippet, date, source}`

**AI-assisted (1 Gemini Flash-Lite call each):**
- `answer_query(query, deep=False)` - searches + summarizes into a direct answer.
  `deep=True` fetches full article text instead of just snippets for a
  more thorough (but slower) answer.
- `get_news_summary(topic)` - short spoken-style news briefing
- `compare_sources(query)` - explicitly flags disagreement between sources,
  useful for anything contested or fast-changing (prices, scores, politics)

## Quota notes

- Search itself is completely free and unlimited (DuckDuckGo, no key).
- Each summarization function (`answer_query`, `get_news_summary`,
  `compare_sources`) makes exactly **one** Gemini call regardless of how
  many search results it pulled in - the results are batched into a
  single prompt, not looped one-by-one. This keeps quota usage low even
  for `MAX_RESULTS = 5+`.
- If DuckDuckGo occasionally rate-limits or returns empty results (it can
  happen with heavy automated use), the functions return a graceful
  "couldn't find results" message rather than crashing.
