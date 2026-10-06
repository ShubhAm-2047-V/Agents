"""
research_engine.py
Deep Intelligence & Research Engine for Orion.
Includes:
1. Multi-Step Deep Research Dossier Generator
2. Fact-Checking & Claim Verification Engine
3. Financial / Stock Market Intelligence
"""

import concurrent.futures
import logging
import config
import search_backend
from google import genai
from google.genai.models import Models

Models._logged_afc_warning = True
logging.getLogger("google_genai").setLevel(logging.ERROR)


def _get_client():
    return genai.Client(api_key=config.GEMINI_API_KEY)


def fact_check(claim: str) -> str:
    """
    Cross-checks a statement against credible sources and assigns a truth rating.
    """
    search_query = f"fact check {claim}"
    results = search_backend.search_web(search_query, max_results=6)
    if not results:
        results = search_backend.search_web(claim, max_results=6)

    sources_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a professional fact-checker and investigative journalist.
Analyze the claim below against the search results.

CLAIM TO VERIFY:
"{claim}"

SOURCES:
{sources_block}

INSTRUCTIONS:
Structure your report strictly as follows:

🛡️ FACT-CHECK VERDICT: [VERIFIED TRUE | MOSTLY TRUE | DISPUTED / UNCONFIRMED | FALSE / MISLEADING]

📌 EXECUTIVE SUMMARY
(2-3 sentences explaining the truth value of the claim clearly)

🔍 EVIDENCE & ANALYSIS
• Point 1: Direct confirmation or debunking facts from credible sources.
• Point 2: Context, nuances, or technical details often omitted.
• Point 3: What official organizations, studies, or reputable outlets stated.

⚠️ MISCONCEPTIONS & CONTEXT
(Explain why this claim arose or what makes it confusing/misleading)

🔗 VERIFICATION SOURCES
[1] Title (domain.com)
[2] Title (domain.com)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def financial_lookup(query: str) -> str:
    """
    Fetches real-time market data, company performance, and financial outlook.
    """
    search_query = f"{query} stock price market cap revenue earnings news"
    results = search_backend.search_web(search_query, max_results=6)

    sources_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a Wall Street financial analyst.
Provide a concise financial intelligence briefing for: "{query}".

SEARCH DATA:
{sources_block}

STRUCTURE:
📈 FINANCIAL SNAPSHOT: {query.upper()}
(1-2 sentence overview of current valuation, ticker, and market performance)

📊 KEY METRICS & RECENT DEVELOPMENTS
• Market Cap & Price: (Latest known numbers)
• Financial Health: (Revenue, growth, or recent quarter earnings results)
• Key Catalysts: (Recent announcements, product launches, or regulatory updates)

⚠️ RISKS & HEADWINDS
• Key risks or headwinds to watch.

🔗 FINANCIAL SOURCES
[1] Title (domain.com)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def multi_step_research(topic: str) -> str:
    """
    Conducts deep multi-query research by:
    1. Generating 3 targeted sub-queries
    2. Scraping and aggregating top web pages concurrently
    3. Synthesizing a comprehensive research dossier
    """
    client = _get_client()

    # Step 1: Generate 3 sub-queries
    subquery_prompt = f"""Generate exactly 3 specific, diverse search queries to deeply investigate this topic:
"{topic}"
Output only the 3 queries, one per line, with no extra text or numbering."""

    try:
        sub_resp = client.models.generate_content(model=config.MODEL, contents=subquery_prompt)
        sub_queries = [line.strip() for line in sub_resp.text.strip().split('\n') if line.strip()][:3]
    except Exception:
        sub_queries = [topic, f"{topic} latest developments", f"{topic} analysis and statistics"]

    # Step 2: Concurrently fetch search results
    all_results = []
    seen_urls = set()

    def _fetch(q):
        res = search_backend.search_web(q, max_results=4)
        for r in res:
            if r['url'] not in seen_urls:
                seen_urls.add(r['url'])
                page_content = search_backend.fetch_page_text(r['url'], max_chars=1800)
                r['full_text'] = page_content if page_content else r['snippet']
                all_results.append(r)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(_fetch, sub_queries)

    if not all_results:
        all_results = search_backend.search_web(topic, max_results=5)

    sources_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\nExtracted Content: {r.get('full_text', r['snippet'])}"
        for i, r in enumerate(all_results[:8])
    )

    # Step 3: Synthesize comprehensive dossier
    dossier_prompt = f"""You are a principal intelligence analyst compiling a Deep Research Dossier.

RESEARCH TOPIC:
{topic}

INVESTIGATIVE SOURCES:
{sources_block}

INSTRUCTIONS:
Produce an exhaustive, highly structured intelligence report formatted as follows:

🏛️ EXECUTIVE INTELLIGENCE DOSSIER: {topic.upper()}
A comprehensive 3-sentence executive briefing synthesizing the state of this topic.

📊 KEY PILLARS & ARCHITECTURE
• Pillar 1: Detailed breakdown with core facts, mechanisms, and drivers.
• Pillar 2: Detailed breakdown with core facts, mechanisms, and drivers.
• Pillar 3: Detailed breakdown with core facts, mechanisms, and drivers.

📅 TIMELINE & RECENT MILESTONES
• [Date/Period] Key historical milestone or breakthrough.
• [Date/Period] Latest major update or event.

📈 STATISTICS & DATA SUMMARY
| Metric / Aspect | Value / Observation | Source / Context |
| --- | --- | --- |
(Include 3-5 rows with verified numbers and findings)

💡 STRATEGIC OUTLOOK & IMPLICATIONS
A forward-looking analysis of where this is heading over the next 1-3 years.

🔗 VERIFIED SOURCES CONSULTED
(List top 5 sources with title and URL)
"""

    response = client.models.generate_content(model=config.MODEL, contents=dossier_prompt)
    return response.text.strip()
