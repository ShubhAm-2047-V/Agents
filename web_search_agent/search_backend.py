"""
search_backend.py
Free web search using DuckDuckGo - no API key, no cost, no rate limit
headaches like paid search APIs. Uses the `ddgs` package.

Also includes a simple page-fetcher for pulling actual article content
when you want a deeper summary than just search snippets.
"""

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from typing import Dict, Any, List, Optional
import config


def search_web(query, max_results=None):
    """
    Returns a list of dicts: {title, url, snippet}
    Free, no API key required.
    """
    max_results = max_results or config.MAX_RESULTS
    results = []

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
    except Exception as e:
        # Gracefully handle transient DDG network or rate-limit issues
        pass

    return results


def search_news(query, max_results=None):
    """Same as search_web but hits DuckDuckGo's news index for recent articles."""
    max_results = max_results or config.MAX_RESULTS
    results = []

    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "date": r.get("date", ""),
                    "source": r.get("source", "")
                })
    except Exception as e:
        pass

    return results


def fetch_page_text(url, max_chars=None):
    """
    Downloads a URL and extracts the main visible text (best-effort).
    Used when a snippet isn't enough and you want to summarize the
    actual article. Returns "" on any failure - never raises, since
    web pages are unreliable and this should degrade gracefully.
    """
    max_chars = max_chars or config.MAX_CONTENT_CHARS
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = " ".join(soup.get_text(separator=" ").split())
        return text[:max_chars]
    except Exception:
        return ""


# =====================================================================
# SPECIALIZED SEARCH ENGINES (TECH, GITHUB, SO, SCHOLAR, PRODUCTS)
# =====================================================================

def search_tech_docs(query: str, tech: str = "", max_results: int = 8) -> List[Dict[str, Any]]:
    """Searches official developer documentation (MDN, Python Docs, React, Docker, Kubernetes, etc.)."""
    site_query = f"{tech} {query} (site:developer.mozilla.org OR site:docs.python.org OR site:react.dev OR site:docs.docker.com OR site:fastapi.tiangolo.com OR site:devdocs.io)"
    return search_web(site_query.strip(), max_results=max_results)


def search_github(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Searches repositories and open source code on GitHub."""
    gh_query = f"{query} site:github.com"
    return search_web(gh_query, max_results=max_results)


def search_stackoverflow(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Searches verified developer solutions on Stack Overflow."""
    so_query = f"{query} site:stackoverflow.com"
    return search_web(so_query, max_results=max_results)


def search_academic(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Searches preprints, academic papers, and research on arXiv & Semantic Scholar."""
    arxiv_query = f"{query} (site:arxiv.org OR site:semanticscholar.org OR site:nature.com)"
    return search_web(arxiv_query, max_results=max_results)


def search_multiple_sources(query: str, max_results: int = 15) -> Dict[str, List[Dict[str, Any]]]:
    """Simultaneously searches Web, News, Technical Docs, and GitHub."""
    return {
        "web": search_web(query, max_results=5),
        "news": search_news(query, max_results=4),
        "tech": search_tech_docs(query, max_results=3),
        "github": search_github(query, max_results=3)
    }

