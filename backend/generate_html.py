import json
from markdown import markdown
from typing import Dict, List, Any

def safe_array(v):
    return v if isinstance(v, list) else []

def escape_html(s):
    if s is None:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#039;")

def format_eur(n):
    try:
        n = float(n)
        if not (isinstance(n, float) and (n.is_integer() or isinstance(n, int))):
            return "—"
    except (ValueError, TypeError):
        return "—"
    return f"{n:,.0f} €".replace(",", ".")

def chunk_by(arr, size):
    return [arr[i:i+size] for i in range(0, len(arr), size)]

def build_html_from_json(model: dict) -> str:
    """Genera HTML dal JSON (equivalente a buildHtml in generate.js)"""
    meta = model.get("meta", {})
    layout = model.get("pdf_layout", {})
    narrative_chapters = safe_array(model.get("narrative", {}).get("chapters", []))
    charts = safe_array(model.get("charts", []))
    
    chart_by_id = {c["id"]: c for c in charts}
    chapters_in_order = safe_array(layout.get("chapter_order", []))
    
    narrative_by_id = {ch["id"]: ch for ch in narrative_chapters}
    ordered_chapter_ids = [
        *[id for id in chapters_in_order if id in narrative_by_id],
        *[ch["id"] for ch in narrative_chapters if ch["id"] not in chapters_in_order]
    ]
    
    # TOC
    toc_items = "".join([
        f'<div class="toc-row"><div class="toc-left"><span class="toc-num">{idx+1}.</span> <a href="#{escape_html(id)}">{escape_html(narrative_by_id[id]["titolo"])}</a></div><div class="toc-right"></div></div>'
        for idx, id in enumerate(ordered_chapter_ids) if id in narrative_by_id
    ])
    
    include_toc = layout.get("style_hints", {}).get("include_table_of_contents", False)
    max_charts_per_page = layout.get("style_hints", {}).get("max_charts_per_page", 2) or 2
    
    # Executive Summary
    exec = model.get("executive_summary", {})
    kpis = safe_array(exec.get("kpi_principali", []))
    recs = safe_array(exec.get("raccomandazioni_30_60_90", []))
    
    kpi_table = ""
    if kpis:
        kpi_rows = "".join([
            f'<tr><td>{escape_html(k["nome"])}</td><td class="num">{escape_html(format_eur(k["valore"]) if k.get("unita") == "EUR" else (f\'{k["valore"]}%\' if k.get("unita") == "%" else str(k.get("valore", "—"))))}</td><td>{escape_html(k.get("scenario", ""))}</td></tr>'
            for k in kpis
        ])
        kpi_table = f'<table class="table"><thead><tr><th>KPI</th><th>Valore</th><th>Scenario</th></tr></thead><tbody>{kpi_rows}</tbody></table>'
    else:
        kpi_table = '<div class="muted">Nessun KPI fornito.</div>'
    
    rec_table = ""
    if recs:
        rec_rows = "".join([
            f'<tr><td>{escape_html(str(r.get("orizzonte_giorni", "")))} gg</td><td>{escape_html(r.get("azione", ""))}</td><td>{escape_html(r.get("motivazione", ""))}</td><td>{escape_html(r.get("priorita", ""))}</td></tr>'
            for r in recs
        ])
        rec_table = f'<table class="table"><thead><tr><th>Orizzonte</th><th>Azione</th><th>Motivazione</th><th>Priorità</th></tr></thead><tbody>{rec_rows}</tbody></table>'
    else:
        rec_table = '<div class="muted">Nessuna raccomandazione fornita.</div>'
    
    # Capitoli
    chapters_html = "".join([
        _build_chapter_html(narrative_by_id[id], idx, chart_by_id, max_charts_per_page)
        for idx, id in enumerate(ordered_chapter_ids) if id in narrative_by_id
    ])
    
    # Executive Summary HTML
    punti_chiave = safe_array(exec.get("punti_chiave", []))
    punti_chiave_html = ""
    if punti_chiave:
        punti_chiave_html = f'<h2>Punti chiave</h2><ul>{"".join([f"<li>{escape_html(x)}</li>" for x in punti_chiave])}</ul>'
    
    exec_html = f'''
    <section class="chapter" id="EXEC_SUMMARY">
      <div class="chapter-kicker">Sezione iniziale</div>
      <h1 class="chapter-title">Executive Summary</h1>
      <div class="chapter-body">
        <p>{escape_html(exec.get("sintesi", ""))}</p>
        {punti_chiave_html}
        <h2>KPI principali</h2>
        {kpi_table}
        <h2>Raccomandazioni 30/60/90</h2>
        {rec_table}
      </div>
    </section>
    '''
    
    # HTML completo
    title = layout.get("titolo_documento", "Business Plan")
    subtitle = layout.get("sottotitolo", "")
    confidentiality = layout.get("confidenzialita", "uso_interno")
    
    # Charts JSON per JavaScript
    charts_json = json.dumps(charts, ensure_ascii=False)
    
    html = f'''<!doctype html>
<html lang="{escape_html(meta.get("lingua", "it-IT"))}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{escape_html(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root{{
      --text:#111;
      --muted:#666;
      --border:#e6e6e6;
      --bg:#fff;
      --soft:#f7f7f8;
      --accent:#111;
    }}
    *{{ box-sizing:border-box; }}
    body{{
      margin:0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Arial, sans-serif;
      color:var(--text);
      background:var(--bg);
      line-height:1.35;
    }}
    .cover{{
      padding: 70px 52px 56px;
      border-bottom: 1px solid var(--border);
    }}
    .cover .badge{{
      display:inline-block;
      padding:6px 10px;
      border:1px solid var(--border);
      border-radius:999px;
      font-size:12px;
      color:var(--muted);
      background:var(--soft);
      letter-spacing:.02em;
    }}
    .cover h1{{
      margin: 14px 0 8px;
      font-size: 30px;
      letter-spacing: -0.02em;
    }}
    .cover h2{{
      margin:0 0 18px;
      font-weight:500;
      color:var(--muted);
      font-size:16px;
    }}
    .cover .meta{{
      margin-top:24px;
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap:10px 24px;
      font-size:12px;
      color:var(--muted);
    }}
    .toc{{
      padding: 42px 52px 0;
    }}
    .toc h1{{
      font-size: 18px;
      margin: 0 0 14px;
    }}
    .toc-row{{
      display:flex;
      align-items:baseline;
      justify-content:space-between;
      padding: 7px 0;
      border-bottom: 1px dashed var(--border);
      font-size: 13px;
    }}
    .toc-left a{{ color: var(--text); text-decoration:none; }}
    .toc-left a:hover{{ text-decoration:underline; }}
    .toc-num{{ color:var(--muted); margin-right:6px; }}
    .chapter{{
      padding: 36px 52px 0;
    }}
    .chapter-kicker{{
      color: var(--muted);
      font-size: 12px;
      letter-spacing: .06em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .chapter-title{{
      margin: 0 0 14px;
      font-size: 22px;
      letter-spacing: -0.01em;
    }}
    .chapter-body{{
      font-size: 13.2px;
      color: var(--text);
    }}
    .chapter-body h2{{
      font-size: 15px;
      margin-top: 14px;
      margin-bottom: 8px;
      letter-spacing: -0.01em;
    }}
    .chapter-body ul{{
      margin: 8px 0 12px 18px;
    }}
    .muted{{ color: var(--muted); }}
    .table{{
      width:100%;
      border-collapse: collapse;
      font-size: 12.6px;
      margin: 8px 0 14px;
    }}
    .table th, .table td{{
      border:1px solid var(--border);
      padding: 8px 10px;
      vertical-align: top;
    }}
    .table th{{
      background: var(--soft);
      text-align:left;
      font-weight: 650;
    }}
    .table .num{{ text-align:right; white-space:nowrap; }}
    .charts-page{{
      display:grid;
      grid-template-columns: 1fr;
      gap: 12px;
      margin-top: 16px;
    }}
    .chart-card{{
      border: 1px solid var(--border);
      background: #fff;
      border-radius: 12px;
      padding: 12px 14px 10px;
    }}
    .chart-title{{
      font-size: 12.5px;
      font-weight: 650;
      margin-bottom: 8px;
    }}
    .chart-caption{{
      margin-top: 6px;
      font-size: 11.5px;
      color: var(--muted);
    }}
    canvas.chart{{
      width: 100% !important;
      height: 320px !important;
      display:block;
    }}
    .page-break{{
      break-before: page;
      page-break-before: always;
    }}
    pre{{
      background: var(--soft);
      border: 1px solid var(--border);
      padding: 10px 12px;
      border-radius: 10px;
      overflow:auto;
      font-size: 12px;
    }}
    code{{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
  </style>
</head>
<body>
  <div class="cover">
    <div class="badge">{escape_html(confidentiality)}</div>
    <h1>{escape_html(title)}</h1>
    <h2>{escape_html(subtitle)}</h2>
    <div class="meta">
      <div><strong>Lingua</strong>: {escape_html(meta.get("lingua", "it-IT"))}</div>
      <div><strong>Stile</strong>: {escape_html(meta.get("stile", "formale"))}</div>
      <div><strong>Orizzonte</strong>: {escape_html(str(meta.get("orizzonte_mesi", "")))} mesi</div>
      <div><strong>Data generazione</strong>: {escape_html(meta.get("data_generazione", ""))}</div>
      <div><strong>Versione</strong>: {escape_html(meta.get("versione", "1.0"))}</div>
    </div>
  </div>

  {f'<div class="toc page-break"><h1>Indice</h1><div class="toc-row"><div class="toc-left"><span class="toc-num">0.</span> <a href="#EXEC_SUMMARY">Executive Summary</a></div><div class="toc-right"></div></div>{toc_items}</div>' if include_toc else ""}

  {exec_html}
  {chapters_html}

  <script>
    (function(){{
      const charts = {charts_json};
      function toXY(points){{
        return points.map(p => ({{ x: p.x, y: p.y }}));
      }}
      function buildDataset(series, type){{
        return series.map((s, idx) => {{
          const data = toXY(s.points || []);
          return {{
            label: (s.name || ("Serie " + (idx+1))).trim(),
            data,
            parsing: {{ xAxisKey: "x", yAxisKey: "y" }},
            tension: type === "line" ? 0.25 : 0,
          }};
        }});
      }}
      function makeChart(cfg){{
        const canvas = document.getElementById("chart_" + cfg.id);
        if(!canvas) return;
        const ctx = canvas.getContext("2d");
        const type = (cfg.tipo || "line").toLowerCase();
        let chartType = type;
        if(type === "pie") chartType = "pie";
        const datasets = buildDataset(cfg.series || [], type);
        const commonOptions = {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: true, position: "bottom", labels: {{ boxWidth: 10 }} }},
            title: {{ display: false }},
            tooltip: {{ enabled: true }}
          }},
          animation: false
        }};
        if(chartType === "pie"){{
          const pieData = (cfg.series?.[0]?.points || []).map(p => p.y);
          const pieLabels = (cfg.series?.[0]?.points || []).map(p => p.x);
          new Chart(ctx, {{
            type: "pie",
            data: {{
              labels: pieLabels,
              datasets: [{{ label: cfg.titolo || cfg.id, data: pieData }}]
            }},
            options: commonOptions
          }});
          return;
        }}
        new Chart(ctx, {{
          type: chartType,
          data: {{ datasets }},
          options: {{
            ...commonOptions,
            scales: {{
              x: {{
                type: "category",
                title: {{ display: !!cfg.x_label, text: cfg.x_label || "" }},
                grid: {{ display: false }}
              }},
              y: {{
                title: {{ display: !!cfg.y_label, text: cfg.y_label || "" }},
                ticks: {{ callback: (v) => {{
                  if (typeof v === "number") return new Intl.NumberFormat("it-IT").format(v);
                  return v;
                }}}}
              }}
            }}
          }}
        }});
      }}
      charts.forEach(makeChart);
      window.__CHARTS_RENDERED__ = true;
    }})();
  </script>
</body>
</html>'''
    
    return html

def _build_chapter_html(ch, idx, chart_by_id, max_charts_per_page):
    """Costruisce HTML per un singolo capitolo"""
    body_html = markdown(ch.get("contenuto_markdown", ""))
    
    chart_ids = safe_array(ch.get("chart_ids", []))
    chart_ids = [cid for cid in chart_ids if cid in chart_by_id]
    
    chart_blocks = ""
    if chart_ids:
        chart_groups = chunk_by(chart_ids, max_charts_per_page)
        chart_blocks = "".join([
            f'<div class="charts-page page-break">{"".join([_build_chart_html(chart_by_id[cid]) for cid in group])}</div>'
            for group in chart_groups
        ])
    
    return f'''
        <section class="chapter" id="{escape_html(ch["id"])}">
          <div class="chapter-kicker">Capitolo {idx + 1}</div>
          <h1 class="chapter-title">{escape_html(ch.get("titolo", ""))}</h1>
          <div class="chapter-body">{body_html}</div>
          {chart_blocks}
        </section>
      '''

def _build_chart_html(c):
    """Costruisce HTML per un singolo grafico"""
    caption_html = f'<div class="chart-caption">{escape_html(c.get("caption", ""))}</div>' if c.get("caption") else ""
    return f'''<div class="chart-card">
                      <div class="chart-title">{escape_html(c.get("titolo", c.get("id", "")))}</div>
                      <canvas class="chart" id="chart_{escape_html(c["id"])}" width="900" height="420"></canvas>
                      {caption_html}
                    </div>'''
