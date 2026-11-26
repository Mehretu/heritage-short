import re
import html
from pathlib import Path

def inline_format(text: str) -> str:
    # Escape raw HTML first if needed, but preserve existing safe tags
    # Handle bold code: `**bold**`
    text = re.sub(r'`([^`]+)`', lambda m: f"<code>{html.escape(m.group(1))}</code>", text)
    text = re.sub(r'\*\*([^*]+)\*\*', lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', lambda m: f"<em>{m.group(1)}</em>", text)
    # Math format
    text = re.sub(r'\$\$(.+?)\$\$', lambda m: f'<div class="math-box">{html.escape(m.group(1))}</div>', text)
    return text

def md_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    html_parts = []
    
    in_code = False
    code_lang = ""
    code_lines = []
    
    in_mermaid = False
    mermaid_lines = []
    
    in_table = False
    table_lines = []
    
    in_ul = False
    in_ol = False
    in_quote = False
    quote_lines = []
    
    def close_lists():
        nonlocal in_ul, in_ol
        res = ""
        if in_ul:
            res += "</ul>\n"
            in_ul = False
        if in_ol:
            res += "</ol>\n"
            in_ol = False
        return res

    def close_quote():
        nonlocal in_quote, quote_lines
        res = ""
        if in_quote:
            content = "<br>\n".join(inline_format(l) for l in quote_lines)
            res += f"<blockquote>{content}</blockquote>\n"
            in_quote = False
            quote_lines = []
        return res

    def flush_table(t_lines):
        if not t_lines:
            return ""
        # Filter separator row (e.g. | :--- | :--- |)
        filtered = [l for l in t_lines if not re.match(r'^\s*\|?\s*:?-+:?\s*\|', l)]
        if not filtered:
            return ""
        
        out = ["<table>"]
        # Header
        header_cells = [c.strip() for c in filtered[0].strip('|').split('|')]
        out.append("  <thead>\n    <tr>")
        for c in header_cells:
            out.append(f"      <th>{inline_format(c)}</th>")
        out.append("    </tr>\n  </thead>\n  <tbody>")
        
        # Rows
        for r in filtered[1:]:
            cells = [c.strip() for c in r.strip('|').split('|')]
            out.append("    <tr>")
            for c in cells:
                out.append(f"      <td>{inline_format(c)}</td>")
            out.append("    </tr>")
        out.append("  </tbody>\n</table>\n")
        return "\n".join(out)

    def render_mermaid_custom(lines_list):
        content = "\n".join(lines_list)
        if "flowchart LR" in content and "Late-Night Desk" in content:
            # Narrative Arc Flowchart
            nodes = [
                ("Present", "Late-Night Desk<br><small>Sensory Catalyst</small>"),
                ("The Awakening", "Arba Minch Canopy<br><small>Emerald Groundwater</small>"),
                ("The Mischief", "Conspiracy by Gate<br><small>Saturday Morning</small>"),
                ("The Escape", "Running Barefoot<br><small>Forest Trails</small>"),
                ("The Springs", "The Sacred Springs<br><small>Bubbling Water</small>"),
                ("Brotherhood", "Pool Plunge<br><small>Laughter & Joy</small>"),
                ("Return", "Golden Silhouettes<br><small>Sunset Walk</small>"),
                ("Present", "Grounded Smile<br><small>Enduring Sanctuary</small>")
            ]
            cards = []
            for i, (title, desc) in enumerate(nodes):
                arrow = '<div class="flow-arrow">&rarr;</div>' if i < len(nodes) - 1 else ''
                cards.append(f'<div class="flow-step"><div class="flow-step-tag">{title}</div><div class="flow-step-desc">{desc}</div></div>{arrow}')
            return f'<div class="flow-container">{"".join(cards)}</div>\n'
        
        elif "flowchart TD" in content and "storyboard.json" in content:
            # System Pipeline Architecture
            return '''<div class="arch-grid">
  <div class="arch-box">
    <div class="arch-title">1. Contract & Schema</div>
    <div class="arch-body">storyboard.json<br><small>schema/storyboard.schema.json</small></div>
  </div>
  <div class="arch-arrow">&rarr;</div>
  <div class="arch-box">
    <div class="arch-title">2. Generative Stages</div>
    <div class="arch-body">
      • Gemini 3.8 Flash TTS (Amharic)<br>
      • Cloudflare FLUX.1 Schnell Keyframes<br>
      • Wan 2.2 I2V / Ken Burns Pan-Zoom<br>
      • ACE-Step 1.5 Sacred Score
    </div>
  </div>
  <div class="arch-arrow">&rarr;</div>
  <div class="arch-box">
    <div class="arch-title">3. Deterministic Caching</div>
    <div class="arch-body">Content-Addressable SHA-256<br><small>runs.jsonl (Audit Trail)</small></div>
  </div>
  <div class="arch-arrow">&rarr;</div>
  <div class="arch-box">
    <div class="arch-title">4. Assembly & Master</div>
    <div class="arch-body">
      • Sidechain Ducking (-14 LUFS)<br>
      • Baked-in Bilingual Subtitles<br>
      • 3s 'Made with AI' End Card<br>
      • 16:9 Cinema & 9:16 Mobile
    </div>
  </div>
</div>\n'''
        else:
            return f'<pre class="mermaid-fallback"><code>{html.escape(content)}</code></pre>\n'

    for line in lines:
        stripped = line.strip()
        
        # Code block handling
        if stripped.startswith("```"):
            if in_code:
                in_code = False
                html_parts.append(close_lists())
                html_parts.append(close_quote())
                code_text = html.escape("\n".join(code_lines))
                html_parts.append(f'<pre><code>{code_text}</code></pre>\n')
                code_lines = []
            elif in_mermaid:
                in_mermaid = False
                html_parts.append(render_mermaid_custom(mermaid_lines))
                mermaid_lines = []
            else:
                tag = stripped[3:].strip()
                if tag == "mermaid":
                    in_mermaid = True
                    mermaid_lines = []
                else:
                    in_code = True
                    code_lang = tag
                    code_lines = []
            continue
            
        if in_code:
            code_lines.append(line)
            continue
            
        if in_mermaid:
            mermaid_lines.append(line)
            continue
            
        # Table handling
        if stripped.startswith("|") and stripped.endswith("|"):
            html_parts.append(close_lists())
            html_parts.append(close_quote())
            if not in_table:
                in_table = True
                table_lines = [stripped]
            else:
                table_lines.append(stripped)
            continue
        else:
            if in_table:
                html_parts.append(flush_table(table_lines))
                in_table = False
                table_lines = []

        # Empty lines
        if not stripped:
            html_parts.append(close_lists())
            html_parts.append(close_quote())
            continue

        # Blockquote handling
        if stripped.startswith(">"):
            html_parts.append(close_lists())
            in_quote = True
            quote_lines.append(stripped.lstrip("> ").strip())
            continue
        else:
            if in_quote:
                html_parts.append(close_quote())

        # Headers
        if stripped.startswith("# "):
            html_parts.append(close_lists())
            html_parts.append(f"<h1>{inline_format(stripped[2:])}</h1>\n")
            continue
        if stripped.startswith("## "):
            html_parts.append(close_lists())
            html_parts.append(f"<h2>{inline_format(stripped[3:])}</h2>\n")
            continue
        if stripped.startswith("### "):
            html_parts.append(close_lists())
            html_parts.append(f"<h3>{inline_format(stripped[4:])}</h3>\n")
            continue
        if stripped.startswith("#### "):
            html_parts.append(close_lists())
            html_parts.append(f"<h4>{inline_format(stripped[5:])}</h4>\n")
            continue

        # Horizontal Rule
        if stripped in ["---", "***", "___"]:
            html_parts.append(close_lists())
            html_parts.append("<hr>\n")
            continue

        # Unordered list
        if stripped.startswith("* ") or stripped.startswith("- "):
            if in_ol:
                html_parts.append("</ol>\n")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>\n")
                in_ul = True
            html_parts.append(f"  <li>{inline_format(stripped[2:])}</li>\n")
            continue

        # Ordered list
        m_ol = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if m_ol:
            if in_ul:
                html_parts.append("</ul>\n")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>\n")
                in_ol = True
            html_parts.append(f"  <li>{inline_format(m_ol.group(2))}</li>\n")
            continue

        # Math block
        if stripped.startswith("$$") and stripped.endswith("$$"):
            html_parts.append(close_lists())
            content = stripped[2:-2].strip()
            html_parts.append(f'<div class="math-box">{html.escape(content)}</div>\n')
            continue

        # Normal paragraph
        html_parts.append(close_lists())
        html_parts.append(f"<p>{inline_format(stripped)}</p>\n")

    # Flush any remaining state
    html_parts.append(close_lists())
    html_parts.append(close_quote())
    if in_table:
        html_parts.append(flush_table(table_lines))
        
    return "".join(html_parts)


def build_full_html():
    md_path = Path("REPORT.md")
    if not md_path.exists():
        print("Error: REPORT.md not found.")
        return
    
    md_text = md_path.read_text(encoding="utf-8")
    body_html = md_to_html(md_text)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>The Forty Springs of Arba Minch — Final Engineering & Creative Production Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {{
      --primary: #0f172a;
      --secondary: #334155;
      --border: #e2e8f0;
      --border-dark: #cbd5e1;
      --bg-subtle: #f8fafc;
      --bg-header: #f1f5f9;
      --accent: #2563eb;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 10.5pt;
      line-height: 1.65;
      color: #1e293b;
      background: #ffffff;
      margin: 0 auto;
      padding: 40px 30px;
      max-width: 920px;
      -webkit-font-smoothing: antialiased;
    }}

    /* Screen-only Print Bar */
    .print-bar {{
      margin-bottom: 25px;
      padding: 12px 20px;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .print-bar span {{
      font-size: 13px;
      color: #475569;
      font-weight: 500;
    }}

    .print-btn {{
      padding: 8px 18px;
      background: #0f172a;
      color: #ffffff;
      border: none;
      border-radius: 5px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease;
    }}

    .print-btn:hover {{
      background: #1e293b;
    }}

    /* Typography */
    h1 {{
      font-size: 22pt;
      font-weight: 700;
      color: var(--primary);
      margin: 0 0 6px 0;
      letter-spacing: -0.02em;
    }}

    h2 {{
      font-size: 14pt;
      font-weight: 700;
      color: var(--primary);
      border-bottom: 1px solid var(--border-dark);
      padding-bottom: 6px;
      margin-top: 32px;
      margin-bottom: 14px;
      letter-spacing: -0.01em;
    }}

    h3 {{
      font-size: 11.5pt;
      font-weight: 650;
      color: #0f172a;
      margin-top: 20px;
      margin-bottom: 8px;
    }}

    p {{
      margin: 0 0 12px 0;
      color: #334155;
    }}

    ul, ol {{
      margin: 0 0 14px 0;
      padding-left: 24px;
      color: #334155;
    }}

    li {{
      margin-bottom: 4px;
    }}

    strong {{
      color: #0f172a;
      font-weight: 600;
    }}

    hr {{
      border: 0;
      height: 1px;
      background: var(--border);
      margin: 28px 0;
    }}

    /* Blockquotes */
    blockquote {{
      margin: 16px 0;
      padding: 12px 18px;
      background-color: var(--bg-subtle);
      border-left: 3px solid #94a3b8;
      border-radius: 0 4px 4px 0;
      color: #334155;
      font-style: italic;
    }}

    blockquote p:last-child {{
      margin-bottom: 0;
    }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0;
      font-size: 9.5pt;
    }}

    th {{
      background-color: var(--bg-header);
      color: var(--primary);
      font-weight: 600;
      text-align: left;
      padding: 9px 12px;
      border: 1px solid var(--border-dark);
    }}

    td {{
      padding: 8px 12px;
      border: 1px solid var(--border);
      color: #334155;
      vertical-align: top;
    }}

    tr:nth-child(even) td {{
      background-color: var(--bg-subtle);
    }}

    /* Code Blocks */
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 9pt;
      background: #f1f5f9;
      padding: 2px 5px;
      border-radius: 3px;
      color: #0f172a;
    }}

    pre {{
      background: #f8fafc;
      border: 1px solid var(--border-dark);
      border-radius: 5px;
      padding: 12px 16px;
      overflow-x: auto;
      margin: 16px 0;
    }}

    pre code {{
      background: none;
      padding: 0;
      font-size: 8.5pt;
      line-height: 1.5;
      color: #1e293b;
    }}

    .math-box {{
      background: #f8fafc;
      border: 1px solid var(--border-dark);
      border-radius: 4px;
      padding: 10px 14px;
      margin: 14px 0;
      text-align: center;
      font-family: ui-monospace, Menlo, Monaco, monospace;
      font-size: 10pt;
      color: #0f172a;
    }}

    /* Flowchart Visual Cards */
    .flow-container {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 6px;
      margin: 20px 0;
      padding: 16px;
      background: #f8fafc;
      border: 1px solid var(--border-dark);
      border-radius: 6px;
    }}

    .flow-step {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 5px;
      padding: 8px 12px;
      min-width: 130px;
      text-align: center;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}

    .flow-step-tag {{
      font-size: 9pt;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 2px;
    }}

    .flow-step-desc {{
      font-size: 8pt;
      color: #64748b;
      line-height: 1.3;
    }}

    .flow-arrow {{
      color: #94a3b8;
      font-weight: bold;
      font-size: 12pt;
    }}

    /* Architecture Grid */
    .arch-grid {{
      display: flex;
      flex-wrap: wrap;
      align-items: stretch;
      justify-content: space-between;
      gap: 8px;
      margin: 20px 0;
      padding: 16px;
      background: #f8fafc;
      border: 1px solid var(--border-dark);
      border-radius: 6px;
    }}

    .arch-box {{
      flex: 1;
      min-width: 170px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 5px;
      padding: 10px 12px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}

    .arch-title {{
      font-size: 9.5pt;
      font-weight: 700;
      color: #0f172a;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
      margin-bottom: 6px;
    }}

    .arch-body {{
      font-size: 8.5pt;
      color: #334155;
      line-height: 1.4;
    }}

    .arch-arrow {{
      display: flex;
      align-items: center;
      color: #94a3b8;
      font-weight: bold;
      font-size: 14pt;
    }}

    /* Print Specific Rules */
    @media print {{
      body {{
        margin: 0;
        padding: 0;
        max-width: 100%;
        font-size: 9.5pt;
        color: #000000;
      }}

      .print-bar {{
        display: none !important;
      }}

      @page {{
        size: A4 portrait;
        margin: 15mm 12mm 15mm 12mm;
      }}

      h1, h2, h3, h4 {{
        page-break-after: avoid;
        break-after: avoid;
        color: #000000;
      }}

      table, figure, .flow-container, .arch-grid, pre, blockquote {{
        page-break-inside: avoid;
        break-inside: avoid;
      }}

      tr {{
        page-break-inside: avoid;
        break-inside: avoid;
      }}

      a {{
        color: #000000;
        text-decoration: none;
      }}

      th {{
        background-color: #f1f5f9 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}

      tr:nth-child(even) td {{
        background-color: #f8fafc !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}

      blockquote {{
        background-color: #f8fafc !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}
    }}
  </style>
</head>
<body>
  <div class="print-bar">
    <div>
      <span style="font-weight: 600; color: #0f172a;">Final Engineering & Creative Production Report</span>
      <div style="font-size: 11px; color: #64748b; margin-top: 2px;">
        To remove the file directory URL from the PDF: in the Print dialog (Cmd+P), expand <strong>More settings</strong> and uncheck <strong>Headers and footers</strong>.
      </div>
    </div>
    <button class="print-btn" onclick="window.print()">Print to PDF / Save</button>
  </div>

  <main>
{body_html}
  </main>
</body>
</html>"""

    Path("REPORT.html").write_text(html_template, encoding="utf-8")
    print("Pre-rendered static REPORT.html generated successfully! (Zero JavaScript dependency)")

if __name__ == "__main__":
    build_full_html()
