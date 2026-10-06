"""
html_exporter.py
Generates interactive, modern dark-mode HTML reports for Orion Web Search Agent.
Includes Mermaid.js flowchart rendering, glassmorphism cards, structured tables, and copy features.
"""

import os
import re
from datetime import datetime


def markdown_to_html(text: str) -> str:
    """Converts markdown text to clean HTML with Mermaid diagram support."""
    # Convert mermaid code blocks
    text = re.sub(
        r'```mermaid\s*\n(.*?)\n```',
        r'<div class="mermaid-container"><pre class="mermaid">\1</pre></div>',
        text,
        flags=re.DOTALL
    )

    # Convert generic code blocks
    text = re.sub(
        r'```(\w*)\s*\n(.*?)\n```',
        r'<pre class="code-block"><code>\2</code></pre>',
        text,
        flags=re.DOTALL
    )

    lines = text.split('\n')
    output_lines = []
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and '|' in stripped[1:]:
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                continue
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            table_rows.append(cells)
            in_table = True
        else:
            if in_table and table_rows:
                html_table = ["<div class='table-container'><table>"]
                for r_idx, row in enumerate(table_rows):
                    tag = "th" if r_idx == 0 else "td"
                    html_table.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in row) + "</tr>")
                html_table.append("</table></div>")
                output_lines.append("".join(html_table))
                table_rows = []
                in_table = False

            if stripped.startswith('### '):
                output_lines.append(f"<h3>{stripped[4:]}</h3>")
            elif stripped.startswith('## '):
                output_lines.append(f"<h2>{stripped[3:]}</h2>")
            elif stripped.startswith('• ') or stripped.startswith('- '):
                output_lines.append(f"<li>{stripped[2:]}</li>")
            elif stripped:
                if not (stripped.startswith('<div') or stripped.startswith('<pre') or stripped.startswith('</pre') or stripped.startswith('</div') or stripped.startswith('<code') or stripped.startswith('</code')):
                    output_lines.append(f"<p>{stripped}</p>")
                else:
                    output_lines.append(stripped)

    if in_table and table_rows:
        html_table = ["<div class='table-container'><table>"]
        for r_idx, row in enumerate(table_rows):
            tag = "th" if r_idx == 0 else "td"
            html_table.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in row) + "</tr>")
        html_table.append("</table></div>")
        output_lines.append("".join(html_table))

    html_content = "\n".join(output_lines)
    # Bold **text** -> <strong>text</strong>
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
    # URLs -> clickable links
    html_content = re.sub(r'(?<!href=")(https?://[^\s<>"\)]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', html_content)
    return html_content


def export_html_report(title: str, content: str, query: str = None) -> str:
    """Creates a modern HTML report in exports/ with Mermaid diagram rendering."""
    output_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(output_dir, exist_ok=True)

    clean_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip().replace(' ', '_').lower() or "report"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{clean_name}_{timestamp}.html")

    formatted_body = markdown_to_html(content)
    date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Orion Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    <style>
        :root {{
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent: #58a6ff;
            --border: #30363d;
            --table-header: #1f242c;
            --table-alt: #12161c;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 36px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .header {{
            border-bottom: 2px solid var(--accent);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        h1 {{ font-size: 26px; color: #ffffff; margin-bottom: 8px; font-weight: 700; }}
        .meta {{ color: var(--text-secondary); font-size: 13px; }}
        h2, h3 {{ color: var(--accent); margin-top: 24px; margin-bottom: 12px; font-size: 18px; }}
        p {{ margin-bottom: 12px; color: #c9d1d9; font-size: 14.5px; }}
        li {{ margin-left: 24px; margin-bottom: 6px; color: #c9d1d9; font-size: 14px; }}
        a {{ color: var(--accent); text-decoration: none; word-break: break-all; }}
        a:hover {{ text-decoration: underline; }}
        .table-container {{
            overflow-x: auto;
            margin: 18px 0;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }}
        th {{
            background: var(--table-header);
            color: #ffffff;
            font-weight: 600;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 10px 16px;
            border-bottom: 1px solid var(--border);
            color: #c9d1d9;
        }}
        tr:nth-child(even) {{ background: var(--table-alt); }}
        .mermaid-container {{
            background: #0d1117;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid var(--border);
            text-align: center;
        }}
        .code-block {{
            background: #0d1117;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--border);
            color: #79c0ff;
            font-family: monospace;
            font-size: 13px;
            margin: 16px 0;
            overflow-x: auto;
        }}
        .footer {{
            margin-top: 36px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 12px;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta"><strong>Topic:</strong> {query or title} &nbsp;|&nbsp; <strong>Generated:</strong> {date_str}</div>
        </div>
        <div class="content">
            {formatted_body}
        </div>
        <div class="footer">
            Orion Web Search & Intelligence Agent &bull; Powered by Gemini & DuckDuckGo
        </div>
    </div>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)

    return os.path.abspath(filename)
