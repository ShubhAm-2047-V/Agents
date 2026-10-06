"""
advanced_intelligence.py
Advanced Intelligence Capabilities for Orion Web Search Agent:
1. Live URL & Webpage Deep Analyzer
2. Academic & ArXiv Science Paper Search
3. Multi-Perspective Debate & Steelman Engine
4. Concept Mindmap & Flowchart Generator (Mermaid.js + ASCII)
"""

import re
import logging
import config
import search_backend
from google import genai
from google.genai.models import Models

Models._logged_afc_warning = True
logging.getLogger("google_genai").setLevel(logging.ERROR)


def _get_client():
    return genai.Client(api_key=config.GEMINI_API_KEY)


def analyze_url(url: str, question: str = None) -> str:
    """
    Downloads and extracts text from a specific URL, producing an executive analysis or answering a specific query.
    """
    page_text = search_backend.fetch_page_text(url, max_chars=8000)
    if not page_text:
        return f"⚠️ Could not extract readable content from URL: {url}. (The page may be blocking scrapers or using heavy client-side JavaScript)."

    client = _get_client()

    if question:
        prompt = f"""You are an expert analyst analyzing a specific web page to answer a user's question.

URL: {url}
PAGE CONTENT:
{page_text}

USER QUESTION:
{question}

INSTRUCTIONS:
Answer the question accurately using ONLY the information from this webpage.
Format your answer clearly with:
- 📌 DIRECT ANSWER
- 🔍 SPECIFIC DETAILS / EVIDENCE FROM PAGE
- 🔗 SOURCE URL: {url}
"""
    else:
        prompt = f"""You are an executive intelligence assistant.
Analyze this webpage and produce a clean, comprehensive executive briefing.

URL: {url}
PAGE CONTENT:
{page_text}

STRUCTURE:
🌐 WEBPAGE EXECUTIVE BRIEFING
(2-3 sentence overview of the page's core topic and author/publisher)

📋 KEY TAKEAWAYS & CORE POINTS
• Key point 1
• Key point 2
• Key point 3

📊 DATA, SPECS & METRICS MENTIONED (if applicable)
• Any key numbers, dates, pricing, or technical details

💡 IMPLICATION / CONCLUSION
(Brief closing insight)

🔗 SOURCE: {url}
"""

    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def paper_search(topic: str) -> str:
    """
    Searches academic papers, preprints (ArXiv), and scientific journals.
    """
    search_query = f"{topic} arxiv research paper pdf methodology results"
    results = search_backend.search_web(search_query, max_results=6)

    sources_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a scientific research editor and academic advisor.
Synthesize the academic and scientific literature on this topic based on the search results below:

TOPIC: {topic}

ACADEMIC SOURCES:
{sources_block}

STRUCTURE:
🔬 ACADEMIC RESEARCH SYNTHESIS: {topic.upper()}
(2-sentence overview of the scientific consensus and state-of-the-art)

🧪 CORE METHODOLOGIES & APPROACHES
• Major theoretical or experimental approaches used in the literature.

📊 KEY SCIENTIFIC FINDINGS & BENCHMARKS
• Quantifiable outcomes, accuracy/performance gains, or primary empirical results.

🔭 FUTURE RESEARCH DIRECTIONS & OPEN PROBLEMS
• Gaps in existing research and active areas of investigation.

📚 KEY PAPERS & CITATIONS
(List the most relevant papers with titles and links)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def debate_engine(topic: str) -> str:
    """
    Constructs a steelmanned, 2-sided debate panel on a controversial or trade-off question.
    """
    results = search_backend.search_web(f"{topic} pros cons comparison debate trade offs", max_results=6)

    sources_block = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are an objective mediator and logic analyst.
Conduct a structured, steelmanned debate analysis on the topic: "{topic}".

SEARCH DATA:
{sources_block}

STRUCTURE:
⚔️ THE CORE DEBATE: {topic.upper()}
(1-2 sentence framing of why this question is actively debated)

🔵 SIDE A: THE CASE FOR [Perspective A]
• Steelmanned Argument 1: Strongest evidence and core advantage.
• Steelmanned Argument 2: Practical considerations and real-world proof.

🔴 SIDE B: THE CASE FOR [Perspective B]
• Steelmanned Argument 1: Strongest evidence and core advantage.
• Steelmanned Argument 2: Practical considerations and real-world proof.

⚖️ KEY TRADE-OFFS MATRIX
| Dimension / Criteria | Perspective A | Perspective B |
| --- | --- | --- |
(3-4 rows comparing cost, performance, learning curve, sustainability, or risk)

🏆 OBJECTIVE SYNTHESIS & WHEN TO CHOOSE WHICH
• Choose Perspective A if: (Specific scenario/constraints)
• Choose Perspective B if: (Specific scenario/constraints)

🔗 DEBATE SOURCES
[1] Title (domain.com)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def generate_mindmap(topic: str) -> str:
    """
    Generates a concept mindmap with both a clean ASCII flowchart for the terminal
    and valid Mermaid.js code for the HTML dashboard.
    """
    results = search_backend.search_web(f"{topic} architecture workflow key components", max_results=5)
    sources_block = "\n\n".join(f"[{i+1}] {r['title']}: {r['snippet']}" for i, r in enumerate(results))

    prompt = f"""You are a systems architect and visual knowledge engineer.
Create a concept hierarchy and flow diagram for: "{topic}".

CONTEXT:
{sources_block}

INSTRUCTIONS:
1. Provide a clean ASCII concept tree for the terminal.
2. Provide a valid Mermaid.js flowchart code block ```mermaid ... ``` that visualizes the nodes and relationships.
3. Keep the layout logical, clear, and comprehensive.

STRUCTURE:
🗺️ CONCEPT MINDMAP: {topic.upper()}

```
[Main Topic]
 ├── [Category 1]
 │    ├── Sub-concept A
 │    └── Sub-concept B
 ├── [Category 2]
 │    ├── Sub-concept C
 │    └── Sub-concept D
 └── [Category 3]
      └── Key Outcome / Impact
```

```mermaid
graph TD
    Root["{topic}"] --> C1["Category 1"]
    Root --> C2["Category 2"]
    Root --> C3["Category 3"]
    C1 --> S1["Sub-concept A"]
    C1 --> S2["Sub-concept B"]
    C2 --> S3["Sub-concept C"]
    C3 --> O1["Outcome / Impact"]
```

💡 KEY ARCHITECTURAL TAKEAWAY
(1-2 sentences summarizing how the system/concept connects together)
"""

    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()
