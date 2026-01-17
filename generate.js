/**
 * generate.js
 * Usage:
 *   node generate.js input.json output.pdf
 */

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const { marked } = require("marked");

function safeArray(v) {
  return Array.isArray(v) ? v : [];
}

function sanitizeItaliaRegimeNote(json) {
  // Se è un array ok, resta così. Se è string/altro, prova a recuperare in modo prudente.
  const it = json?.data?.italia;
  if (!it) return;

  if (Array.isArray(it.regime_fiscale_note)) {
    // filtra elementi non-string o "spazzatura" troppo corta
    it.regime_fiscale_note = it.regime_fiscale_note
      .filter(x => typeof x === "string")
      .map(s => s.trim())
      .filter(s => s.length >= 8 && !s.includes("adempimenti_checklist"));
    return;
  }

  if (typeof it.regime_fiscale_note === "string") {
    it.regime_fiscale_note = [it.regime_fiscale_note.trim()].filter(Boolean);
    return;
  }

  // fallback: se è qualcosa di invalido, trasformalo in array vuoto
  it.regime_fiscale_note = [];
}

function formatEUR(n) {
  if (typeof n !== "number" || !isFinite(n)) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}

function formatPct(n) {
  if (typeof n !== "number" || !isFinite(n)) return "—";
  return new Intl.NumberFormat("it-IT", { style: "percent", maximumFractionDigits: 0 }).format(n);
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function chunkBy(arr, size) {
  const out = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

function buildHtml(model) {
  const meta = model.meta || {};
  const layout = model.pdf_layout || {};
  const narrativeChapters = safeArray(model?.narrative?.chapters);
  const charts = safeArray(model?.charts);

  const chartById = new Map(charts.map(c => [c.id, c]));
  const chaptersInOrder = safeArray(layout.chapter_order);

  // Alcuni capitoli nel narrative includono CH9_DISCLAIMER che non è in chapter_order: lo aggiungiamo in coda se presente
  const narrativeById = new Map(narrativeChapters.map(ch => [ch.id, ch]));
  const orderedChapterIds = [
    ...chaptersInOrder.filter(id => narrativeById.has(id)),
    ...narrativeChapters.map(ch => ch.id).filter(id => !chaptersInOrder.includes(id)),
  ];

  // TOC: useremo link HTML (funziona anche se i numeri pagina non sono perfetti)
  const tocItems = orderedChapterIds
    .map((id, idx) => {
      const ch = narrativeById.get(id);
      if (!ch) return "";
      return `<div class="toc-row">
        <div class="toc-left"><span class="toc-num">${idx + 1}.</span> <a href="#${escapeHtml(id)}">${escapeHtml(ch.titolo)}</a></div>
        <div class="toc-right"></div>
      </div>`;
    })
    .join("");

  const includeTOC = !!layout?.style_hints?.include_table_of_contents;
  const maxChartsPerPage = Number(layout?.style_hints?.max_charts_per_page || 2) || 2;

  // Executive summary (kpi + 30/60/90)
  const exec = model.executive_summary || {};
  const kpis = safeArray(exec.kpi_principali);
  const recs = safeArray(exec.raccomandazioni_30_60_90);

  const kpiTable = kpis.length
    ? `<table class="table">
        <thead><tr><th>KPI</th><th>Valore</th><th>Scenario</th></tr></thead>
        <tbody>
          ${kpis
            .map(k => {
              const val =
                k.unita === "EUR" ? formatEUR(k.valore) :
                k.unita === "%" ? `${k.valore}%` :
                (k.valore ?? "—");
              return `<tr>
                <td>${escapeHtml(k.nome)}</td>
                <td class="num">${escapeHtml(String(val))}</td>
                <td>${escapeHtml(k.scenario)}</td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>`
    : `<div class="muted">Nessun KPI fornito.</div>`;

  const recTable = recs.length
    ? `<table class="table">
        <thead><tr><th>Orizzonte</th><th>Azione</th><th>Motivazione</th><th>Priorità</th></tr></thead>
        <tbody>
          ${recs
            .map(r => `<tr>
              <td>${escapeHtml(String(r.orizzonte_giorni))} gg</td>
              <td>${escapeHtml(r.azione)}</td>
              <td>${escapeHtml(r.motivazione)}</td>
              <td>${escapeHtml(r.priorita)}</td>
            </tr>`)
            .join("")}
        </tbody>
      </table>`
    : `<div class="muted">Nessuna raccomandazione fornita.</div>`;

  // Capitoli + grafici
  const chaptersHtml = orderedChapterIds
    .map((id, idx) => {
      const ch = narrativeById.get(id);
      if (!ch) return "";

      // markdown → html
      const bodyHtml = marked.parse(ch.contenuto_markdown || "");

      // charts referenced by chapter
      const ids = safeArray(ch.chart_ids).filter(cid => chartById.has(cid));
      const chartBlocks = ids.length
        ? chunkBy(ids, maxChartsPerPage)
            .map(group => {
              // Forziamo massimo N grafici per pagina con page-break
              const canvases = group
                .map(cid => {
                  const c = chartById.get(cid);
                  return `<div class="chart-card">
                      <div class="chart-title">${escapeHtml(c.titolo || cid)}</div>
                      <canvas class="chart" id="chart_${escapeHtml(cid)}" width="900" height="420"></canvas>
                      ${c.caption ? `<div class="chart-caption">${escapeHtml(c.caption)}</div>` : ""}
                    </div>`;
                })
                .join("");
              return `<div class="charts-page page-break">${canvases}</div>`;
            })
            .join("")
        : "";

      return `
        <section class="chapter" id="${escapeHtml(id)}">
          <div class="chapter-kicker">Capitolo ${idx + 1}</div>
          <h1 class="chapter-title">${escapeHtml(ch.titolo)}</h1>
          <div class="chapter-body">${bodyHtml}</div>
          ${chartBlocks}
        </section>
      `;
    })
    .join("");

  // Inseriamo in testa una sezione Executive Summary “pulita”
  const execHtml = `
    <section class="chapter" id="EXEC_SUMMARY">
      <div class="chapter-kicker">Sezione iniziale</div>
      <h1 class="chapter-title">Executive Summary</h1>
      <div class="chapter-body">
        <p>${escapeHtml(exec.sintesi || "")}</p>

        ${safeArray(exec.punti_chiave).length ? `
          <h2>Punti chiave</h2>
          <ul>
            ${safeArray(exec.punti_chiave).map(x => `<li>${escapeHtml(x)}</li>`).join("")}
          </ul>
        ` : ""}

        <h2>KPI principali</h2>
        ${kpiTable}

        <h2>Raccomandazioni 30/60/90</h2>
        ${recTable}
      </div>
    </section>
  `;

  // Styles: layout professionale (A4, margini, tipografia, tabelle, cards grafici)
  const title = layout.titolo_documento || "Business Plan";
  const subtitle = layout.sottotitolo || "";
  const confidentiality = layout.confidenzialita || "uso_interno";

  const html = `<!doctype html>
<html lang="${escapeHtml(meta.lingua || "it-IT")}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>${escapeHtml(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root{
      --text:#111;
      --muted:#666;
      --border:#e6e6e6;
      --bg:#fff;
      --soft:#f7f7f8;
      --accent:#111;
    }
    *{ box-sizing:border-box; }
    body{
      margin:0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Arial, sans-serif;
      color:var(--text);
      background:var(--bg);
      line-height:1.35;
    }
    .page{
      padding: 42px 52px 56px;
    }
    .cover{
      padding: 70px 52px 56px;
      border-bottom: 1px solid var(--border);
    }
    .cover .badge{
      display:inline-block;
      padding:6px 10px;
      border:1px solid var(--border);
      border-radius:999px;
      font-size:12px;
      color:var(--muted);
      background:var(--soft);
      letter-spacing:.02em;
    }
    .cover h1{
      margin: 14px 0 8px;
      font-size: 30px;
      letter-spacing: -0.02em;
    }
    .cover h2{
      margin:0 0 18px;
      font-weight:500;
      color:var(--muted);
      font-size:16px;
    }
    .cover .meta{
      margin-top:24px;
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap:10px 24px;
      font-size:12px;
      color:var(--muted);
    }
    .divider{ height: 18px; }

    .toc{
      padding: 42px 52px 0;
    }
    .toc h1{
      font-size: 18px;
      margin: 0 0 14px;
    }
    .toc-row{
      display:flex;
      align-items:baseline;
      justify-content:space-between;
      padding: 7px 0;
      border-bottom: 1px dashed var(--border);
      font-size: 13px;
    }
    .toc-left a{ color: var(--text); text-decoration:none; }
    .toc-left a:hover{ text-decoration:underline; }
    .toc-num{ color:var(--muted); margin-right:6px; }

    .chapter{
      padding: 36px 52px 0;
    }
    .chapter-kicker{
      color: var(--muted);
      font-size: 12px;
      letter-spacing: .06em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    .chapter-title{
      margin: 0 0 14px;
      font-size: 22px;
      letter-spacing: -0.01em;
    }
    .chapter-body{
      font-size: 13.2px;
      color: var(--text);
    }
    .chapter-body h2{
      font-size: 15px;
      margin-top: 14px;
      margin-bottom: 8px;
      letter-spacing: -0.01em;
    }
    .chapter-body ul{
      margin: 8px 0 12px 18px;
    }
    .muted{ color: var(--muted); }

    .table{
      width:100%;
      border-collapse: collapse;
      font-size: 12.6px;
      margin: 8px 0 14px;
    }
    .table th, .table td{
      border:1px solid var(--border);
      padding: 8px 10px;
      vertical-align: top;
    }
    .table th{
      background: var(--soft);
      text-align:left;
      font-weight: 650;
    }
    .table .num{ text-align:right; white-space:nowrap; }

    .charts-page{
      display:grid;
      grid-template-columns: 1fr;
      gap: 12px;
      margin-top: 16px;
    }
    .chart-card{
      border: 1px solid var(--border);
      background: #fff;
      border-radius: 12px;
      padding: 12px 14px 10px;
    }
    .chart-title{
      font-size: 12.5px;
      font-weight: 650;
      margin-bottom: 8px;
    }
    .chart-caption{
      margin-top: 6px;
      font-size: 11.5px;
      color: var(--muted);
    }
    canvas.chart{
      width: 100% !important;
      height: 320px !important;
      display:block;
    }

    /* Page breaks for PDF */
    .page-break{
      break-before: page;
      page-break-before: always;
    }

    /* Better markdown code blocks if present */
    pre{
      background: var(--soft);
      border: 1px solid var(--border);
      padding: 10px 12px;
      border-radius: 10px;
      overflow:auto;
      font-size: 12px;
    }
    code{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
  </style>
</head>
<body>
  <div class="cover">
    <div class="badge">${escapeHtml(confidentiality)}</div>
    <h1>${escapeHtml(title)}</h1>
    <h2>${escapeHtml(subtitle)}</h2>
    <div class="meta">
      <div><strong>Lingua</strong>: ${escapeHtml(meta.lingua || "it-IT")}</div>
      <div><strong>Stile</strong>: ${escapeHtml(meta.stile || "formale")}</div>
      <div><strong>Orizzonte</strong>: ${escapeHtml(String(meta.orizzonte_mesi ?? ""))} mesi</div>
      <div><strong>Data generazione</strong>: ${escapeHtml(meta.data_generazione || "")}</div>
      <div><strong>Versione</strong>: ${escapeHtml(meta.versione || "1.0")}</div>
    </div>
  </div>

  ${includeTOC ? `
    <div class="toc page-break">
      <h1>Indice</h1>
      <div class="toc-row">
        <div class="toc-left"><span class="toc-num">0.</span> <a href="#EXEC_SUMMARY">Executive Summary</a></div>
        <div class="toc-right"></div>
      </div>
      ${tocItems}
    </div>
  ` : ""}

  ${execHtml}
  ${chaptersHtml}

  <script>
    // Chart rendering after DOM load
    (function(){
      const charts = ${JSON.stringify(charts)};
      function toXY(points){
        // points: [{x: "Mese 1", y: 1000}, ...]
        return points.map(p => ({ x: p.x, y: p.y }));
      }

      function buildDataset(series, type){
        return series.map((s, idx) => {
          const data = toXY(s.points || []);
          // Non fissiamo colori: Chart.js userà palette default
          return {
            label: (s.name || ("Serie " + (idx+1))).trim(),
            data,
            parsing: { xAxisKey: "x", yAxisKey: "y" },
            tension: type === "line" ? 0.25 : 0,
          };
        });
      }

      function makeChart(cfg){
        const canvas = document.getElementById("chart_" + cfg.id);
        if(!canvas) return;
        const ctx = canvas.getContext("2d");

        const type = (cfg.tipo || "line").toLowerCase();
        let chartType = type;
        if(type === "pie") chartType = "pie";

        const datasets = buildDataset(cfg.series || [], type);

        const commonOptions = {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true, position: "bottom", labels: { boxWidth: 10 } },
            title: { display: false },
            tooltip: { enabled: true }
          },
          animation: false
        };

        if(chartType === "pie"){
          const pieData = (cfg.series?.[0]?.points || []).map(p => p.y);
          const pieLabels = (cfg.series?.[0]?.points || []).map(p => p.x);
          new Chart(ctx, {
            type: "pie",
            data: {
              labels: pieLabels,
              datasets: [{ label: cfg.titolo || cfg.id, data: pieData }]
            },
            options: commonOptions
          });
          return;
        }

        // line/bar
        new Chart(ctx, {
          type: chartType,
          data: { datasets },
          options: {
            ...commonOptions,
            scales: {
              x: {
                type: "category",
                title: { display: !!cfg.x_label, text: cfg.x_label || "" },
                grid: { display: false }
              },
              y: {
                title: { display: !!cfg.y_label, text: cfg.y_label || "" },
                ticks: { callback: (v) => {
                  // Format numbers as IT locale; keep as-is if not numeric
                  if (typeof v === "number") return new Intl.NumberFormat("it-IT").format(v);
                  return v;
                }}
              }
            }
          }
        });
      }

      // Render all charts
      charts.forEach(makeChart);

      // Signal to Puppeteer that charts are rendered
      window.__CHARTS_RENDERED__ = true;
    })();
  </script>
</body>
</html>`;

  return html;
}

async function main() {
  const inPath = process.argv[2];
  const outPath = process.argv[3] || "business-plan.pdf";
  if (!inPath) {
    console.error("Usage: node generate.js input.json output.pdf");
    process.exit(1);
  }

  const raw = fs.readFileSync(inPath, "utf-8");
  const model = JSON.parse(raw);

  sanitizeItaliaRegimeNote(model);

  const html = buildHtml(model);

  const layout = model.pdf_layout || {};
  const headerLeft = layout?.header?.left || "";
  const headerRight = layout?.header?.right || "";
  const footerLeft = layout?.footer?.left || "";
  const footerCenter = layout?.footer?.center || "";
  const footerRight = layout?.footer?.right || "Pagina {PAGE_NUMBER}";

  // Puppeteer
  const browser = await puppeteer.launch({
    headless: "new",
    // Se sei su Linux server e hai problemi: prova con args sotto
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();

  // Carica HTML
  await page.setContent(html, { waitUntil: "networkidle0" });

  // Aspetta che Chart.js abbia renderizzato
  await page.waitForFunction(() => window.__CHARTS_RENDERED__ === true, { timeout: 15000 });

  // Header/footer template (Puppeteer usa HTML minimale)
  const headerTemplate = `
    <div style="width:100%; font-size:9px; color:#666; padding:0 44px; display:flex; justify-content:space-between;">
      <div>${escapeHtml(headerLeft)}</div>
      <div>${escapeHtml(headerRight)}</div>
    </div>
  `;

  // Page number: Puppeteer fornisce classi speciali pageNumber/totalPages
  const footerTemplate = `
    <div style="width:100%; font-size:9px; color:#666; padding:0 44px; display:flex; justify-content:space-between;">
      <div>${escapeHtml(footerLeft)}</div>
      <div>${escapeHtml(footerCenter)}</div>
      <div>${escapeHtml(footerRight).replace("{PAGE_NUMBER}", '<span class="pageNumber"></span>')}</div>
    </div>
  `;

  await page.pdf({
    path: outPath,
    format: "A4",
    printBackground: true,
    margin: { top: "70px", right: "44px", bottom: "70px", left: "44px" },
    displayHeaderFooter: true,
    headerTemplate,
    footerTemplate,
  });

  await browser.close();
  console.log("PDF generato:", outPath);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
