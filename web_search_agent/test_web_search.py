"""
test_web_search.py
Quick standalone test. Run this after setting your API key in config.py.

    python test_web_search.py

Note: requires internet access. DuckDuckGo search itself needs no API key,
only the summarization step uses your Gemini key.
"""

import web_search_agent as web

print("=== Orion Web Search Agent Test ===\n")

print("1. Raw search (zero API cost):")
results = web.raw_search("latest Python version")
for r in results[:3]:
    print(" -", r["title"])
    print("  ", r["url"])
print()

print("2. Answering a query with Gemini summarization (1 API call):")
answer = web.answer_query("what is the latest stable Python version")
print(answer, "\n")

print("3. News summary (1 API call):")
news_summary = web.get_news_summary("artificial intelligence India")
print(news_summary, "\n")

print("4. Compare sources on a query (1 API call):")
comparison = web.compare_sources("current inflation rate India")
print(comparison)
