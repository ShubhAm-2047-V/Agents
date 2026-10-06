"""
csv_exporter.py
Extracts tabular comparison data and research metrics into CSV spreadsheets.
"""

import os
import csv
import re
from datetime import datetime


def export_markdown_table_to_csv(title: str, text: str, query: str = None) -> str:
    """
    Parses any markdown table or key-value specification list in the text and exports to CSV.
    Returns: Absolute path to the generated CSV file.
    """
    output_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(output_dir, exist_ok=True)

    clean_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip().replace(' ', '_').lower() or "table_export"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{clean_name}_{timestamp}.csv")

    rows = []
    lines = text.split('\n')
    in_table = False

    for line in lines:
        stripped = line.strip()
        # Parse markdown tables (| col1 | col2 |)
        if stripped.startswith('|') and '|' in stripped[1:]:
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                continue
            cells = [re.sub(r'[\*\`\_]', '', c.strip()) for c in stripped.split('|')[1:-1]]
            if cells:
                rows.append(cells)
                in_table = True
        # If no markdown table, parse '• Feature: Val A vs Val B'
        elif not in_table and stripped.startswith(('•', '-', '*')) and ':' in stripped:
            raw = re.sub(r'^[•\-\*]\s*', '', stripped)
            parts = raw.split(':', 1)
            feat = parts[0].strip()
            rest = parts[1].strip()
            if ' vs ' in rest:
                vals = re.split(r'\s+vs\s+', rest, flags=re.IGNORECASE)
                rows.append([feat, vals[0].strip(), vals[1].strip()])
            else:
                rows.append([feat, rest])

    # If no structured rows detected, create a 2-column key-value dump
    if not rows:
        rows.append(["Query / Topic", query or title])
        rows.append(["Date Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        rows.append(["Summary", text[:1000]])

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(r)

    return os.path.abspath(filename)
