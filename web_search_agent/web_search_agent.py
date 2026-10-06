"""
web_search_agent.py
Main entry point for Orion's Advanced Web Search & Intelligence Agent.

Full Capabilities:
1. Deep Intelligence: Multi-Step Dossiers, Fact-Checking, Financial Analysis
2. Unique Modes: URL Page Analyzer, ArXiv Paper Search, 2-Sided Debate Engine, Mermaid Mindmaps
3. Multi-Format Exports: PDF (with Difference Tables), Dark HTML Dashboards, CSV Spreadsheets
4. Voice & Interactive Chat: Spoken Audio Briefs & Continuous Follow-up Chat
5. Automation: Session History, Bookmarks, and Auto-Launch
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from . import (
        config, search_backend, pdf_generator, html_exporter,
        csv_exporter, research_engine, advanced_intelligence,
        history_manager, chat_session, browser_navigator,
        browser_media_controller, clipboard_tools, live_lookups, dev_productivity
    )
    from .voice_engine import voice
except ImportError:
    import config, search_backend, pdf_generator, html_exporter, csv_exporter, research_engine, advanced_intelligence, history_manager, chat_session, browser_navigator, browser_media_controller, clipboard_tools, live_lookups, dev_productivity
    from voice_engine import voice

from google import genai
from google.genai.models import Models

# Suppress internal SDK automatic function calling warning
Models._logged_afc_warning = True
logging.getLogger("google_genai").setLevel(logging.ERROR)

# Initialize voice setting from config
voice.set_enabled(getattr(config, "VOICE_ENABLED", False))


def _get_client():
    return genai.Client(api_key=config.GEMINI_API_KEY)


def raw_search(query, max_results=None):
    """Zero-AI-cost: returns raw search results (title/url/snippet)."""
    return search_backend.search_web(query, max_results)


def raw_news(query, max_results=None):
    """Zero-AI-cost: raw news results."""
    return search_backend.search_news(query, max_results)


def answer_query(query, deep=False):
    """Searches the web and returns a clean, highly readable executive answer."""
    results = search_backend.search_web(query, config.MAX_RESULTS)

    if not results:
        return "⚠️  No relevant search results found."

    if deep:
        for r in results:
            page_text = search_backend.fetch_page_text(r["url"])
            r["content"] = page_text if page_text else r["snippet"]
    else:
        for r in results:
            r["content"] = r["snippet"]

    sources_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r['content']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a smart search assistant presenting answers directly in a command-line terminal.

USER QUERY:
{query}

SEARCH RESULTS:
{sources_block}

FORMATTING RULES:
1. Avoid markdown tables. Use clean bullet points instead.
2. Keep it crisp, skimmable, and easy to read in 10 seconds.
3. Structure strictly as follows:

📌 DIRECT ANSWER
(1-2 clear, direct sentences answering the query)

🔍 KEY HIGHLIGHTS
• Bullet point 1 with key facts / numbers
• Bullet point 2 with key facts / numbers
• Bullet point 3 (if needed)

💡 BOTTOM LINE
(One takeaway sentence or actionable summary)

🔗 SOURCES
[1] Title (domain.com)
[2] Title (domain.com)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def get_news_summary(topic, max_results=None):
    """Fetches recent news on a topic and returns a clean, readable briefing."""
    results = search_backend.search_news(topic, max_results)

    if not results:
        return f"⚠️  No recent news found for '{topic}'."

    articles_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nSource: {r.get('source', 'Unknown')} ({r.get('date', 'Recent')})\nSummary: {r.get('snippet', '')}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a news editor summarizing recent events for a terminal CLI.

TOPIC:
{topic}

ARTICLES:
{articles_block}

FORMATTING RULES:
Structure strictly as follows:

⚡ TOP HEADLINE
(A punchy 1-sentence summary of the main development)

📋 KEY UPDATES
• [Source/Date] Key fact or event in 1 sentence.
• [Source/Date] Key fact or event in 1 sentence.
• [Source/Date] Key fact or event in 1 sentence.

🌐 IMPACT & OUTLOOK
(1-2 sentences on what this means)

📰 TOP SOURCES
[1] Title (Source)
[2] Title (Source)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def compare_sources(query, max_results=None):
    """Performs a structured comparison with an explicit Difference Table."""
    results = search_backend.search_web(query, max_results)

    if not results:
        return "⚠️  No search results found to compare."

    sources_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a professional technology and product comparison analyst.

QUERY:
{query}

SEARCH RESULTS:
{sources_block}

FORMATTING RULES:
1. Always create a structured, clear markdown difference table comparing the two subjects.
2. In the table, include: Display, Processor, Battery & Charging, Camera, Build Quality, Price, and any other notable specs found in sources.
3. Be direct, objective, and highlight exact values where known (or 'Not specified' if unconfirmed).

STRUCTURE YOUR OUTPUT EXACTLY LIKE THIS:

⚖️ QUICK VERDICT
(1-2 clear sentences summarizing the main takeaway and winner for different use cases)

📊 DIFFERENCE TABLE
| Specification / Feature | Option A | Option B |
| --- | --- | --- |
| Display | ... | ... |
| Processor | ... | ... |
| Battery & Charging | ... | ... |
| Camera Setup | ... | ... |
| Build & Design | ... | ... |
| Price | ... | ... |

🎯 WHICH ONE SHOULD YOU CHOOSE?
✅ Choose Option A if:
  • Key advantage 1
  • Key advantage 2

✅ Choose Option B if:
  • Key advantage 1
  • Key advantage 2

🔍 NOTABLE CONFLICTS / GAPS IN SOURCES
• Note any conflicting specs or missing details in 1-2 lines.

🔗 SOURCES
[1] Title (domain.com)
[2] Title (domain.com)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def export_pdf(title, content, query=None):
    """Generates a styled PDF report in the exports/ directory and opens it if enabled."""
    try:
        pdf_path = pdf_generator.create_pdf_report(title, content, query=query)
        if getattr(config, "AUTO_OPEN_EXPORTS", True):
            history_manager.open_file(pdf_path)
        return pdf_path
    except Exception as e:
        print(f"⚠️  PDF Generation Warning: {e}")
        return None


def export_html(title, content, query=None):
    """Generates a modern dark-mode HTML report and opens it if enabled."""
    try:
        html_path = html_exporter.export_html_report(title, content, query=query)
        if getattr(config, "AUTO_OPEN_EXPORTS", True):
            history_manager.open_file(html_path)
        return html_path
    except Exception as e:
        print(f"⚠️  HTML Generation Warning: {e}")
        return None


def export_csv_file(title, content, query=None):
    """Generates a CSV spreadsheet from tabular data and opens it if enabled."""
    try:
        csv_path = csv_exporter.export_markdown_table_to_csv(title, content, query=query)
        if getattr(config, "AUTO_OPEN_EXPORTS", True):
            history_manager.open_file(csv_path)
        return csv_path
    except Exception as e:
        print(f"CSV Generation Warning: {e}")
        return None


# =====================================================================
# EXTENDED SEARCH INTELLIGENCE (ALL 20 FEATURES SUITE)
# =====================================================================

def search_multiple_sources(query: str, max_results: int = 15) -> Dict[str, Any]:
    """Feature 2: Multi-source search across Web, News, Technical Docs, and GitHub."""
    return search_backend.search_multiple_sources(query, max_results)


def search_technical_docs(query: str, tech: str = "") -> str:
    """Feature 4: Technical documentation search with synthesized code examples."""
    results = search_backend.search_tech_docs(query, tech)
    if not results:
        return f"No documentation found for {tech} {query}."
    sources = "\n\n".join(f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}" for i, r in enumerate(results))
    prompt = f"Summarize technical documentation for: '{tech} {query}'\n\nSOURCES:\n{sources}\n\nInclude syntax, params, code snippet, and link to docs."
    client = _get_client()
    return client.models.generate_content(model=config.MODEL, contents=prompt).text.strip()


def search_github_repos(query: str) -> str:
    """Feature 5: GitHub repository & open-source code search."""
    results = search_backend.search_github(query)
    if not results:
        return f"No GitHub repositories found for '{query}'."
    return "\n\n".join(f"• {r['title']}\n  URL: {r['url']}\n  {r['snippet']}" for r in results)


def search_stackoverflow_solutions(query: str) -> str:
    """Feature 6: Stack Overflow troubleshooting & error solution search."""
    results = search_backend.search_stackoverflow(query)
    if not results:
        return f"No Stack Overflow discussions found for '{query}'."
    sources = "\n\n".join(f"[{i+1}] {r['title']}\nURL: {r['url']}\n{r['snippet']}" for i, r in enumerate(results))
    prompt = f"Synthesize the best Stack Overflow solutions for: '{query}'\n\nSOURCES:\n{sources}\n\nProvide the direct fix and explanation."
    client = _get_client()
    return client.models.generate_content(model=config.MODEL, contents=prompt).text.strip()


def product_research(product_name: str) -> str:
    """Feature 7: Product research, specifications, pros/cons, and user ratings."""
    return answer_query(f"{product_name} detailed review specifications pros and cons user rating", deep=True)


def compare_prices(product_name: str) -> str:
    """Feature 8: Price comparison and deal finding across retailers."""
    return compare_sources(f"{product_name} price comparison Amazon Flipkart BestBuy Walmart deals discount")


def search_academic_papers(topic: str) -> str:
    """Feature 9: Academic papers, research publications, and arXiv abstracts."""
    results = search_backend.search_academic(topic)
    if not results:
        return f"No academic papers found for '{topic}'."
    sources = "\n\n".join(f"[{i+1}] {r['title']}\nURL: {r['url']}\nAbstract/Snippet: {r['snippet']}" for i, r in enumerate(results))
    prompt = f"Summarize recent academic research and key breakthroughs on: '{topic}'\n\nPAPERS:\n{sources}"
    client = _get_client()
    return client.models.generate_content(model=config.MODEL, contents=prompt).text.strip()


def search_tutorials(topic: str, level: str = "beginner") -> str:
    """Feature 10: Step-by-step programming and technical tutorials."""
    results = search_backend.search_web(f"{topic} tutorial step by step guide for {level}", max_results=6)
    sources = "\n\n".join(f"• {r['title']}\n  URL: {r['url']}\n  {r['snippet']}" for r in results)
    return f"Top Step-by-Step Tutorials for '{topic}' ({level}):\n\n{sources}"


def search_apis(service_name: str) -> str:
    """Feature 11: API documentation, endpoints, authentication, and SDKs."""
    return search_technical_docs("API documentation endpoints authentication sdk reference", tech=service_name)


def search_software_libraries(need_description: str, language: str = "python") -> str:
    """Feature 12: Discovers top software packages, npm modules, and PyPI libraries."""
    return answer_query(f"Best {language} libraries packages modules for {need_description} comparison GitHub stars")


def summarize_webpage(url: str) -> str:
    """Feature 14: Extracts and summarizes any public webpage or article URL."""
    text = search_backend.fetch_page_text(url, max_chars=8000)
    if not text:
        return f"Could not fetch readable text from {url}."
    prompt = f"Provide a comprehensive, skimmable executive summary of this webpage:\nURL: {url}\n\nPAGE TEXT:\n{text[:6000]}"
    client = _get_client()
    return client.models.generate_content(model=config.MODEL, contents=prompt).text.strip()


def extract_key_info(url_or_text: str, focus: str = "key metrics, numbers, dates, and conclusions") -> str:
    """Feature 15: Extracts important structured entities, metrics, prices, or dates."""
    if url_or_text.startswith("http://") or url_or_text.startswith("https://"):
        content = search_backend.fetch_page_text(url_or_text, max_chars=8000)
    else:
        content = url_or_text
    prompt = f"Extract all critical information ({focus}) as structured bullet points:\n\nCONTENT:\n{content[:6000]}"
    client = _get_client()
    return client.models.generate_content(model=config.MODEL, contents=prompt).text.strip()


def verify_claim(claim_statement: str) -> str:
    """Feature 16: Fact-checks a claim against multiple search sources."""
    return advanced_intelligence.fact_check_claim(claim_statement)


def find_latest_info(topic: str) -> str:
    """Feature 17: Finds latest breaking information, updates, and releases."""
    return get_news_summary(topic)


def track_topic(topic: str) -> str:
    """Feature 18: Tracks recurring topics and logs updates."""
    news = get_news_summary(topic)
    history_manager.log_search(f"TRACK: {topic}", news)
    return f"Logged topic tracker for '{topic}'.\n\n{news}"


def generate_research_report(topic: str, depth: int = 2) -> str:
    """Feature 19: Generates a full multi-stage research report and dossier."""
    return research_engine.generate_multi_step_dossier(topic, depth=depth)


def get_sources_citations(query: str) -> List[Dict[str, str]]:
    """Feature 20: Returns verified source URLs, publication titles, and citations."""
    results = search_backend.search_web(query, max_results=8)
    return [{"citation_number": i + 1, "title": r["title"], "url": r["url"]} for i, r in enumerate(results)]



def _clean_export_request(text):
    """Checks if user requested PDF, HTML, or CSV export in the query."""
    import re
    wants_pdf = False
    wants_html = False
    wants_csv = False
    lower = text.lower().strip()

    if re.search(r'\b(csv|excel|spreadsheet|in\s+csv|as\s+csv|to\s+csv)\b', lower):
        wants_csv = True
    elif re.search(r'\b(html|in\s+html|as\s+html|to\s+html)\b', lower):
        wants_html = True
    elif re.search(r'\b(pdf|in\s+a\s+pdf|in\s+pdf|as\s+a\s+pdf|as\s+pdf|generate\s+pdf)\b', lower):
        wants_pdf = True

    strip_patterns = [
        r'\s+(?:then\s+(?:he|it|you)\s+should\s+.*)$',
        r'\s+(?:then\s+(?:he|it|you)\s+should)$',
        r'\s+(?:and\s+generate\s+(?:a\s+)?(pdf|html|csv|excel).*)$',
        r'\s+(?:in\s+(?:a\s+)?(pdf|html|csv|excel).*)$',
        r'\s+(?:as\s+(?:a\s+)?(pdf|html|csv|excel).*)$',
        r'\s+(?:to\s+(?:a\s+)?(pdf|html|csv|excel).*)$',
        r'\s+(?:generate\s+(?:a\s+)?(pdf|html|csv|excel).*)$',
        r'^(pdf|html|csv)\s+'
    ]

    cleaned = text
    for pat in strip_patterns:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE).strip()

    return cleaned.strip(), wants_pdf, wants_html, wants_csv


def _is_followup_export_command(text):
    """Detects follow-up export commands like 'put this in pdf', 'save as html', 'save to csv'."""
    t = text.lower().strip()
    is_pdf = "pdf" in t
    is_html = "html" in t
    is_csv = "csv" in t or "excel" in t or "spreadsheet" in t

    if not (is_pdf or is_html or is_csv):
        return False, None

    has_pointer = any(w in t.split() for w in ["this", "that", "all", "it", "everything", "previous", "above", "last", "these"])
    has_action = any(w in t.split() for w in ["put", "save", "export", "make", "convert", "download", "create", "generate", "get", "print", "to", "in", "as"])

    if has_pointer or has_action or t in ("pdf", "html", "csv", "excel", "save pdf", "save html", "save csv"):
        if not any(t.startswith(cmd) for cmd in ["compare ", "ask ", "news ", "search ", "deep ", "research ", "factcheck ", "stock ", "finance ", "analyze ", "paper ", "debate ", "map ", "raw "]):
            export_format = "csv" if is_csv else ("html" if is_html else "pdf")
            return True, export_format
    return False, None


if __name__ == "__main__":
    print("================================================================")
    print("           Orion Advanced Web Search & Intelligence Agent       ")
    print("================================================================")
    print("Core Intelligence & Research:")
    print("  • 'search <query>'       : Free raw web results (zero AI cost)")
    print("  • 'ask <query>' / '<q>'  : Direct AI synthesized answer")
    print("  • 'compare <x> and <y>'  : Side-by-side Difference Table")
    print("  • 'research <topic>'     : Multi-query deep research dossier")
    print("  • 'analyze <url> [q]'    : Deep webpage / article reader & Q&A")
    print("  • 'paper <topic>'        : Academic & ArXiv research paper search")
    print("  • 'debate <topic>'       : 2-sided steelmanned debate & trade-offs")
    print("  • 'map <topic>'          : Concept mindmap & Mermaid diagram")
    print("  • 'factcheck <claim>'    : Truth-meter fact verification")
    print("  • 'stock <ticker>'       : Real-time financial & market data")
    print("  • 'news <topic>'         : Spoken-style news briefing")
    print("  • 'chat'                 : Interactive follow-up Q&A copilot")
    print()
    print("Smart Browser & Media:")
    print("  • 'open <site/url>'      : Open Instagram, YouTube, GitHub, or any website")
    print("  • 'close it' / 'close'   : Close active browser tab / window")
    print("  • 'play <music/video>'   : Play top video on YouTube / Spotify")
    print("  • 'screenshot <url>'     : Capture full-page PNG screenshot")
    print("  • 'yt <url>'             : Summarize YouTube video transcript")
    print("  • 'scroll down / up'     : Live browser scrolling & reload")
    print()
    print("Clipboard & Screen AI:")
    print("  • 'clipboard summarize'  : Summarize copied text & copy back (Ctrl+V)")
    print("  • 'clipboard fix'        : Fix grammar & tone in clipboard")
    print("  • 'qr <text or url>'     : Generate terminal QR code & PNG image")
    print()
    print("Live Real-World Lookups:")
    print("  • 'weather <city>'       : Instant live weather card & 3-day forecast")
    print("  • 'flights <from> to <to>': Route airlines, prices & travel times")
    print("  • 'price <product>'      : Compare retailer prices & deals")
    print("  • 'crypto gas'           : Real-time Ethereum & Bitcoin network fees")
    print()
    print("Developer Productivity & System:")
    print("  • 'whois / dns <domain>' : DNS records, IPv4/v6, and SSL certificate")
    print("  • 'git <repo>'           : GitHub stars, forks, issues & commit log")
    print("  • 'speedtest'            : Real-time ping & download bandwidth test")
    print("  • 'put this in pdf/html/csv' : Export last result to file")
    print("  • 'voice on / off'       : Toggle spoken audio briefings")
    print("  • 'clear all pdf'        : Delete generated PDFs")
    print("  • 'exit' / 'quit'        : Close agent")
    print("================================================================\n")

    has_key = bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE")
    last_result = None

    while True:
        try:
            cmd = input("WebSearch > ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break

            # Handle browser tab / website close commands (e.g. 'close it', 'close website', 'close instagram', 'close tab')
            is_close, close_target = browser_navigator.is_close_command(cmd)
            if is_close:
                print(f"\n🚪 Closing website in your browser...\n" + "─" * 60)
                success, site_name, msg = browser_navigator.close_website(close_target)
                if success:
                    print(f"✅ Closed {site_name} in your browser.\n")
                    voice.speak_async(f"Closed {site_name}.")
                else:
                    print(f"⚠️  Could not close {site_name}: {msg}\n")
                print("─" * 60 + "\n")
                continue

            # Handle browser navigation / open website commands (e.g. 'open instagram on web', 'visit github', 'launch youtube')
            nav_prefixes = ("open ", "visit ", "launch ", "browse to ", "browse ", "go to ", "goto ")
            if any(cmd.lower().startswith(p) for p in nav_prefixes):
                target_site = None
                for p in nav_prefixes:
                    if cmd.lower().startswith(p):
                        target_site = cmd[len(p):].strip()
                        break

                # Guard against internal system toggles
                if target_site and not target_site.lower().startswith(("pdf", "html", "csv", "exports", "auto", "voice")):
                    print(f"\n🌐 Resolving and launching '{target_site}' in your browser...\n" + "─" * 60)
                    success, site_name, url = browser_navigator.open_website(target_site)
                    if success:
                        print(f"✅ Opened {site_name}: {url}\n")
                        voice.speak_async(f"Opening {site_name} in your browser.")
                        last_result = {"type": "navigation", "title": f"Website: {site_name}", "query": target_site, "content": f"Opened {site_name} at {url}"}
                    else:
                        print(f"⚠️  Could not open {site_name}: {url}\n")
                    print("─" * 60 + "\n")
                    continue

            # Voice toggle
            if cmd.lower() in ("voice on", "voice enable"):
                voice.set_enabled(True)
                print("\n🎙️  Spoken voice output is now ON.\n")
                voice.speak_async("Voice briefings enabled.")
                continue
            elif cmd.lower() in ("voice off", "voice disable"):
                voice.set_enabled(False)
                print("\n🔇 Spoken voice output is now OFF.\n")
                continue

            # Auto-open toggle
            if cmd.lower() in ("auto_open on", "auto open on"):
                config.AUTO_OPEN_EXPORTS = True
                print("\n📂 Auto-opening exports is now ON.\n")
                continue
            elif cmd.lower() in ("auto_open off", "auto open off"):
                config.AUTO_OPEN_EXPORTS = False
                print("\n🔒 Auto-opening exports is now OFF.\n")
                continue

            # Interactive Research Chat Mode
            if cmd.lower() in ("chat", "copilot", "q&a", "ask follow up"):
                context_to_use = last_result.get("content", "") if last_result else ""
                topic_to_use = last_result.get("query", "Active Research") if last_result else "General Research"
                chat_session.run_interactive_chat(initial_context=context_to_use, topic=topic_to_use)
                continue

            # History & Bookmarks
            if cmd.lower() == "history":
                hist = history_manager.get_history(limit=8)
                print("\n📜 Recent Search History:\n" + "─" * 60)
                if not hist:
                    print("   (No previous search history found)")
                for i, h in enumerate(hist):
                    print(f" [{i+1}] {h.get('timestamp')} | [{h.get('type').upper()}] {h.get('query')}")
                print("─" * 60 + "\n")
                continue

            if cmd.lower().startswith("bookmark"):
                if cmd.lower() in ("bookmarks", "bookmark list"):
                    bmarks = history_manager.get_bookmarks()
                    print("\n⭐ Saved Bookmarks:\n" + "─" * 60)
                    if not bmarks:
                        print("   (No bookmarks saved yet)")
                    for b in bmarks:
                        print(f" • {b.get('title')} ({b.get('date')})\n   Query: {b.get('query')}\n")
                    print("─" * 60 + "\n")
                else:
                    note = cmd[8:].strip() or (last_result['query'] if last_result else "Saved Research")
                    if last_result:
                        history_manager.add_bookmark(note, last_result['query'], last_result.get('content', ''))
                        print(f"\n⭐ Saved bookmark for: '{last_result['query']}'\n")
                    else:
                        print("\n⚠️  No active result to bookmark.\n")
                continue

            # Clear / Delete PDF exports
            clear_pdf_phrases = (
                "clear all pdf", "clear all pdfs", "clear pdf", "clear pdfs",
                "delete all pdf", "delete all pdfs", "delete pdf", "delete pdfs",
                "clean pdf", "clean pdfs", "clear exports", "delete exports"
            )
            if cmd.lower() in clear_pdf_phrases:
                count, deleted_files = pdf_generator.clear_all_pdfs()
                if count > 0:
                    print(f"\n🗑️  Successfully deleted {count} PDF report(s) from exports/:")
                    for f in deleted_files:
                        print(f"   • {f}")
                    print()
                else:
                    print("\nℹ️  No PDF reports found in exports/ to delete.\n")
                continue

            # Follow-up export command ("put this in pdf", "save as html", "export to csv")
            is_followup, export_type = _is_followup_export_command(cmd)
            if is_followup:
                if not last_result:
                    print("\n⚠️  No previous search result available to export. Please run a query first.\n")
                    continue

                if export_type == "csv":
                    print(f"\n📊 Exporting previous result for '{last_result['query']}' to CSV Spreadsheet...\n" + "─" * 60)
                    csv_file = export_csv_file(last_result.get("title", f"Table: {last_result['query'].title()}"), last_result.get("content", ""), query=last_result.get("query", ""))
                    if csv_file:
                        print(f"✅ CSV Spreadsheet Saved & Opened: {csv_file}")
                elif export_type == "html":
                    print(f"\n🌐 Exporting previous result for '{last_result['query']}' to HTML Dashboard...\n" + "─" * 60)
                    html_file = export_html(last_result.get("title", f"Report: {last_result['query'].title()}"), last_result.get("content", ""), query=last_result.get("query", ""))
                    if html_file:
                        print(f"✅ HTML Dashboard Saved & Opened: {html_file}")
                else:
                    print(f"\n📄 Exporting previous result for '{last_result['query']}' to PDF Report...\n" + "─" * 60)
                    pdf_file = export_pdf(last_result.get("title", f"Report: {last_result['query'].title()}"), last_result.get("content", ""), query=last_result.get("query", ""))
                    if pdf_file:
                        print(f"✅ PDF Report Saved & Opened: {pdf_file}")
                print("─" * 60 + "\n")
                continue

            # Check for inline export tags ('... in a pdf', '... in html', '... in csv')
            cleaned_cmd, wants_pdf, wants_html, wants_csv = _clean_export_request(cmd)

            # Smart Browser & Media Control
            if cleaned_cmd.lower().startswith("play ") or cleaned_cmd.lower().startswith("listen to "):
                q = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n🎵 Searching and playing media for '{q}' in browser...\n" + "─" * 60)
                ok, title, url = browser_media_controller.play_media(q)
                print(f"▶️ Playing: {title}\n🔗 URL: {url}\n")
                voice.speak_async(f"Playing {title}.")
                last_result = {"type": "media", "title": f"Media: {title}", "query": q, "content": f"Playing {title} at {url}"}

            elif cleaned_cmd.lower().startswith("screenshot ") or cleaned_cmd.lower().startswith("capture "):
                target = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n📸 Capturing high-resolution screenshot of '{target}'...\n" + "─" * 60)
                ok, res_path = browser_media_controller.capture_screenshot(target)
                if ok:
                    print(f"✅ Screenshot Saved & Opened: {res_path}\n")
                    voice.speak_async("Screenshot captured.")
                    last_result = {"type": "screenshot", "title": f"Screenshot: {target}", "query": target, "content": f"Saved screenshot to {res_path}"}
                else:
                    print(f"⚠️ Screenshot failed: {res_path}\n")

            elif cleaned_cmd.lower().startswith("summarize youtube ") or cleaned_cmd.lower().startswith("yt ") or (cleaned_cmd.lower().startswith("summarize ") and "youtu" in cleaned_cmd.lower()):
                target = cleaned_cmd.split(maxsplit=1)[1].strip()
                if target.lower().startswith("youtube "):
                    target = target[8:].strip()
                print(f"\n📺 Summarizing YouTube video '{target}'...\n" + "─" * 60)
                output = browser_media_controller.summarize_youtube_video(target)
                print(output)
                voice.speak_async(output)
                last_result = {"type": "youtube_summary", "title": "YouTube Video Briefing", "query": target, "content": output}

            elif cleaned_cmd.lower() in ("scroll down", "scroll up", "reload", "refresh", "zoom in", "zoom out", "page down", "page up"):
                ok, msg = browser_media_controller.send_browser_key_action(cleaned_cmd)
                print(f"\n🎮 Browser Control: {msg}\n")
                continue

            # Clipboard AI & QR Generator
            elif cleaned_cmd.lower().startswith("clipboard ") or cleaned_cmd.lower() == "clipboard":
                action = cleaned_cmd[10:].strip() if len(cleaned_cmd) > 9 else "summarize"
                print(f"\n📋 Processing clipboard content with AI ({action})...\n" + "─" * 60)
                ok, proc_text, msg = clipboard_tools.process_clipboard_ai(action)
                if ok:
                    print(f"[Processed Clipboard Content]:\n\n{proc_text}\n\n{msg}\n")
                    voice.speak_async(proc_text)
                    last_result = {"type": "clipboard", "title": f"Clipboard AI: {action.title()}", "query": "clipboard", "content": proc_text}
                else:
                    print(f"{msg}\n")

            elif cleaned_cmd.lower().startswith("qr ") or cleaned_cmd.lower().startswith("generate qr "):
                data = cleaned_cmd.split(maxsplit=1)[1].strip()
                if data.lower().startswith("qr "):
                    data = data[3:].strip()
                print(f"\n📱 Generating QR Code for '{data}'...\n" + "─" * 60)
                ok, file_path, ascii_qr = clipboard_tools.generate_qr_code(data)
                if ok:
                    print(ascii_qr)
                    print(f"✅ QR Code Image Saved & Opened: {file_path}\n")
                    last_result = {"type": "qrcode", "title": "QR Code", "query": data, "content": f"QR Code generated for: {data}"}
                else:
                    print(f"⚠️ Error: {file_path}\n")

            # Live Real-World Lookups
            elif cleaned_cmd.lower().startswith("weather ") or cleaned_cmd.lower() == "weather":
                city = cleaned_cmd[8:].strip() if len(cleaned_cmd) > 7 else "London"
                print(f"\n🌤️ Fetching live weather for '{city}'...\n" + "─" * 60)
                output = live_lookups.get_weather(city)
                print(output)
                voice.speak_async(output)
                last_result = {"type": "weather", "title": f"Weather: {city.title()}", "query": city, "content": output}

            elif cleaned_cmd.lower().startswith("flights ") or cleaned_cmd.lower().startswith("flight "):
                route_text = cleaned_cmd.split(maxsplit=1)[1].strip()
                m_route = re.match(r'^(?:from\s+)?(.+?)\s+to\s+(.+)$', route_text, re.IGNORECASE)
                origin = m_route.group(1).strip() if m_route else "NYC"
                dest = m_route.group(2).strip() if m_route else route_text
                print(f"\n✈️ Searching live flight intelligence for {origin.title()} to {dest.title()}...\n" + "─" * 60)
                output = live_lookups.flight_search(origin, dest)
                print(output)
                voice.speak_async(output)
                last_result = {"type": "flights", "title": f"Flights: {origin.title()} to {dest.title()}", "query": f"{origin} to {dest}", "content": output}

            elif cleaned_cmd.lower().startswith("price ") or cleaned_cmd.lower().startswith("price track ") or cleaned_cmd.lower().startswith("deal "):
                product = re.sub(r'^(?:price\s+track\s+|price\s+|deal\s+for\s+|deal\s+)', '', cleaned_cmd, flags=re.IGNORECASE).strip()
                print(f"\n🏷️ Tracking prices & deals across retailers for '{product}'...\n" + "─" * 60)
                output = live_lookups.price_tracker(product)
                print(output)
                voice.speak_async(output)
                last_result = {"type": "price", "title": f"Price Check: {product.title()}", "query": product, "content": output}

            elif cleaned_cmd.lower() in ("crypto gas", "gas fees", "eth gas", "gas price", "crypto fees"):
                print(f"\n⛽ Fetching live Ethereum gas & Bitcoin network fees...\n" + "─" * 60)
                output = live_lookups.crypto_gas_fees()
                print(output)
                voice.speak_async(output)
                last_result = {"type": "crypto_gas", "title": "Crypto Gas & Fees", "query": "gas fees", "content": output}

            # Developer & Technical Productivity
            elif cleaned_cmd.lower().startswith("whois ") or cleaned_cmd.lower().startswith("dns "):
                domain = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n🌐 Resolving DNS records, IP, & SSL status for '{domain}'...\n" + "─" * 60)
                output = dev_productivity.dns_whois_lookup(domain)
                print(output)
                last_result = {"type": "dns", "title": f"DNS Intelligence: {domain}", "query": domain, "content": output}

            elif cleaned_cmd.lower().startswith("git ") or cleaned_cmd.lower().startswith("github ") or cleaned_cmd.lower().startswith("repo "):
                repo = cleaned_cmd.split(maxsplit=1)[1].strip()
                if repo.lower().startswith("inspect "):
                    repo = repo[8:].strip()
                print(f"\n🐙 Inspecting GitHub repository '{repo}'...\n" + "─" * 60)
                output = dev_productivity.git_inspect_repo(repo)
                print(output)
                voice.speak_async(output)
                last_result = {"type": "github", "title": f"GitHub Repo: {repo}", "query": repo, "content": output}

            elif cleaned_cmd.lower() in ("speedtest", "speed test", "check speed", "network speed", "ping"):
                print(f"\n🚀 Running network latency and bandwidth speed test...\n" + "─" * 60)
                output = dev_productivity.run_speedtest()
                print(output)
                voice.speak_async(output)
                last_result = {"type": "speedtest", "title": "Network Speed Diagnostic", "query": "speedtest", "content": output}

            # 1. Live Webpage / URL Deep Analyzer
            elif cleaned_cmd.lower().startswith("analyze ") or cleaned_cmd.lower().startswith("read "):
                parts = cleaned_cmd.split(maxsplit=2)
                target_url = parts[1] if len(parts) > 1 else ""
                custom_q = parts[2] if len(parts) > 2 else None
                print(f"\n🌐 Analyzing webpage: '{target_url}'...\n" + "─" * 60)
                if has_key:
                    output = advanced_intelligence.analyze_url(target_url, question=custom_q)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "analyze_url", "title": f"Webpage Analysis: {target_url[:40]}", "query": target_url, "content": output}
                else:
                    text_extracted = search_backend.fetch_page_text(target_url)
                    print(f"[Extracted Webpage Text ({len(text_extracted)} chars)]:\n{text_extracted[:1500]}...\n")
                    last_result = {"type": "analyze_url", "title": f"Webpage Text: {target_url[:40]}", "query": target_url, "content": text_extracted}

            # 2. Academic & ArXiv Science Paper Search
            elif cleaned_cmd.lower().startswith("paper ") or cleaned_cmd.lower().startswith("arxiv "):
                topic = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n🔬 Searching academic & scientific papers on '{topic}'...\n" + "─" * 60)
                if has_key:
                    output = advanced_intelligence.paper_search(topic)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "paper", "title": f"Academic Research: {topic.title()}", "query": topic, "content": output}
                else:
                    res = raw_search(f"{topic} research paper pdf arxiv")
                    output = "KEY PAPERS FOUND\n\n" + "\n\n".join(f"• {r['title']}: {r['snippet']}" for r in res)
                    print(output)
                    last_result = {"type": "paper", "title": f"Papers: {topic.title()}", "query": topic, "content": output}

            # 3. Multi-Perspective Debate Engine
            elif cleaned_cmd.lower().startswith("debate ") or cleaned_cmd.lower().startswith("versus "):
                topic = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n⚔️  Constructing steelmanned debate analysis on '{topic}'...\n" + "─" * 60)
                if has_key:
                    output = advanced_intelligence.debate_engine(topic)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "debate", "title": f"Debate Analysis: {topic.title()}", "query": topic, "content": output}
                else:
                    res = raw_search(f"{topic} pros cons debate")
                    output = "DEBATE PERSPECTIVES\n\n" + "\n\n".join(f"• {r['title']}: {r['snippet']}" for r in res)
                    print(output)
                    last_result = {"type": "debate", "title": f"Debate: {topic.title()}", "query": topic, "content": output}

            # 4. Concept Mindmap & Flowchart Generator
            elif cleaned_cmd.lower().startswith("map ") or cleaned_cmd.lower().startswith("graph "):
                topic = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n🗺️  Generating concept mindmap & flowchart for '{topic}'...\n" + "─" * 60)
                if has_key:
                    output = advanced_intelligence.generate_mindmap(topic)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "mindmap", "title": f"Mindmap: {topic.title()}", "query": topic, "content": output}
                else:
                    res = raw_search(f"{topic} concept architecture overview")
                    output = "MINDMAP CONCEPTS\n\n" + "\n\n".join(f"• {r['title']}" for r in res)
                    print(output)
                    last_result = {"type": "mindmap", "title": f"Mindmap: {topic.title()}", "query": topic, "content": output}

            # 5. Deep Multi-Query Research Dossier
            elif cleaned_cmd.lower().startswith("research ") or cleaned_cmd.lower().startswith("dossier "):
                topic = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n🏛️  Conducting multi-step deep research on '{topic}'...\n" + "─" * 60)
                if has_key:
                    output = research_engine.multi_step_research(topic)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "research", "title": f"Dossier: {topic.title()}", "query": topic, "content": output}
                else:
                    res = raw_search(topic)
                    output = "KEY SEARCH RESULTS\n\n" + "\n\n".join(f"• {r['title']}: {r['snippet']}" for r in res)
                    print(output)
                    last_result = {"type": "search", "title": f"Search: {topic.title()}", "query": topic, "content": output}

            # 6. Fact-Checking Engine
            elif cleaned_cmd.lower().startswith("factcheck ") or cleaned_cmd.lower().startswith("verify "):
                claim = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n🛡️  Fact-checking claim: '{claim}'...\n" + "─" * 60)
                if has_key:
                    output = research_engine.fact_check(claim)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "factcheck", "title": f"Fact Check: {claim.title()}", "query": claim, "content": output}
                else:
                    res = raw_search(claim)
                    output = "SOURCES FOUND\n\n" + "\n\n".join(f"• {r['title']}: {r['snippet']}" for r in res)
                    print(output)
                    last_result = {"type": "factcheck", "title": f"Fact Check: {claim.title()}", "query": claim, "content": output}

            # 7. Financial & Market Watch
            elif cleaned_cmd.lower().startswith("stock ") or cleaned_cmd.lower().startswith("finance ") or cleaned_cmd.lower().startswith("crypto "):
                target = cleaned_cmd.split(maxsplit=1)[1].strip()
                print(f"\n📈 Fetching market intelligence for '{target}'...\n" + "─" * 60)
                if has_key:
                    output = research_engine.financial_lookup(target)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "finance", "title": f"Financial Snapshot: {target.upper()}", "query": target, "content": output}
                else:
                    res = raw_search(f"{target} stock price")
                    output = "FINANCIAL SOURCES\n\n" + "\n\n".join(f"• {r['title']}: {r['snippet']}" for r in res)
                    print(output)
                    last_result = {"type": "finance", "title": f"Financial Data: {target.upper()}", "query": target, "content": output}

            # 8. News Briefing
            elif cleaned_cmd.lower().startswith("news "):
                topic = cleaned_cmd[5:].strip()
                if topic.lower().startswith("for "):
                    topic = topic[4:].strip()
                print(f"\n⚡ Searching news for '{topic}'...\n" + "─" * 60)
                if has_key:
                    output = get_news_summary(topic)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "news", "title": f"News Briefing: {topic.title()}", "query": topic, "content": output}
                else:
                    news_list = raw_news(topic)
                    raw_text = "\n\n".join(f"• {n['title']} ({n.get('source', '')} - {n.get('date', '')})\n  {n.get('snippet', '')}" for n in news_list)
                    print(f"[News Results ({len(news_list)})]:\n\n{raw_text}\n")
                    last_result = {"type": "raw_news", "title": f"News Results: {topic.title()}", "query": topic, "content": f"KEY NEWS RESULTS\n{raw_text}"}

            # 9. Raw Search (Zero-Cost)
            elif cleaned_cmd.lower().startswith("search ") or cleaned_cmd.lower().startswith("raw "):
                q = cleaned_cmd.split(maxsplit=1)[1].strip()
                if q.lower().startswith("for "):
                    q = q[4:].strip()
                print(f"\n🔍 Searching web for '{q}'...\n" + "─" * 60)
                res = raw_search(q)
                print(f"[Results ({len(res)})]:\n")
                raw_lines = []
                for i, r in enumerate(res):
                    print(f"  • {r['title']}")
                    print(f"    {r['url']}")
                    print(f"    {r['snippet']}\n")
                    raw_lines.append(f"• **{r['title']}**\n  URL: {r['url']}\n  Snippet: {r['snippet']}")

                formatted_content = f"QUICK SUMMARY\nSearch results for '{q}'.\n\nKEY SEARCH RESULTS\n" + "\n\n".join(raw_lines)
                last_result = {"type": "search", "title": f"Search: {q.title()}", "query": q, "content": formatted_content}

            # 10. Side-by-Side Comparison
            elif cleaned_cmd.lower().startswith("compare "):
                q = cleaned_cmd[8:].strip()
                print(f"\n⚖️ Comparing sources for '{q}'...\n" + "─" * 60)
                if has_key:
                    output = compare_sources(q)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "compare", "title": f"Comparison: {q.title()}", "query": q, "content": output}
                else:
                    res = raw_search(q)
                    for r in res:
                        print(f"  • {r['title']}: {r['snippet']}\n    {r['url']}\n")
                    last_result = {"type": "compare", "title": f"Comparison: {q.title()}", "query": q, "content": "KEY SOURCES\n" + "\n".join(f"• {r['title']}" for r in res)}

            # 11. Deep Article Extraction
            elif cleaned_cmd.lower().startswith("deep "):
                q = cleaned_cmd[5:].strip()
                if q.lower().startswith("for "):
                    q = q[4:].strip()
                print(f"\n🔬 Performing deep research for '{q}'...\n" + "─" * 60)
                if has_key:
                    output = answer_query(q, deep=True)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "deep", "title": f"Research Report: {q.title()}", "query": q, "content": output}
                else:
                    res = raw_search(q)
                    for r in res:
                        print(f"  • {r['title']}: {r['snippet']}\n    {r['url']}\n")

            # 12. Standard Ask Query
            else:
                q = cleaned_cmd[4:].strip() if cleaned_cmd.lower().startswith("ask ") else cleaned_cmd
                print(f"\n💡 Searching & analyzing '{q}'...\n" + "─" * 60)
                if has_key:
                    output = answer_query(q)
                    print(output)
                    voice.speak_async(output)
                    last_result = {"type": "ask", "title": f"Search Intelligence: {q.title()}", "query": q, "content": output}
                else:
                    res = raw_search(q)
                    for r in res:
                        print(f"  • {r['title']}: {r['snippet']}\n    {r['url']}\n")
                    last_result = {"type": "search", "title": f"Search: {q.title()}", "query": q, "content": "KEY SOURCES\n" + "\n".join(f"• {r['title']}" for r in res)}

            # Handle automatic export if requested inline
            if wants_csv and last_result:
                csv_file = export_csv_file(last_result["title"], last_result["content"], query=last_result["query"])
                if csv_file:
                    print(f"\n📊 CSV Spreadsheet Saved & Opened: {csv_file}")
            elif wants_html and last_result:
                html_file = export_html(last_result["title"], last_result["content"], query=last_result["query"])
                if html_file:
                    print(f"\n🌐 HTML Dashboard Saved & Opened: {html_file}")
            elif wants_pdf and last_result:
                pdf_file = export_pdf(last_result["title"], last_result["content"], query=last_result["query"])
                if pdf_file:
                    print(f"\n📄 PDF Report Saved & Opened: {pdf_file}")

            # Record in session history
            if last_result:
                history_manager.add_history_entry(
                    query_type=last_result.get("type", "search"),
                    query=last_result.get("query", ""),
                    summary=last_result.get("content", "")[:180]
                )

            print("─" * 60 + "\n")

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"Error: {e}\n")
