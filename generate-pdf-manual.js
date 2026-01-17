// Script per generare PDF manualmente dal file JSON business-plan-TechStarts.json
// Versione standalone - non dipende da script.js
// Esegui questo script nella console del browser dopo aver aperto index.html
// OPPURE apri questo file come HTML (vedi generate-pdf-standalone.html)

// Funzione per convertire markdown in HTML
function markdownToHTML(md) {
    if (!md) return '';
    return md
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/\n/gim, '<br>');
}

// Funzione buildHtmlFromJSON standalone
function buildHtmlFromJSON(model) {
    const safeArray = (v) => Array.isArray(v) ? v : [];
    const escapeHtml = (str) => String(str ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    const formatEUR = (n) => {
        if (typeof n !== "number" || !isFinite(n)) return "—";
        return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
    };
    const chunkBy = (arr, size) => {
        const out = [];
        for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
        return out;
    };

    const meta = model.meta || {};
    const layout = model.pdf_layout || {};
    const narrativeChapters = safeArray(model?.narrative?.chapters);
    const charts = safeArray(model?.charts);

    const chartById = new Map(charts.map(c => [c.id, c]));
    const chaptersInOrder = safeArray(layout.chapter_order);

    const narrativeById = new Map(narrativeChapters.map(ch => [ch.id, ch]));
    const orderedChapterIds = [
        ...chaptersInOrder.filter(id => narrativeById.has(id)),
        ...narrativeChapters.map(ch => ch.id).filter(id => !chaptersInOrder.includes(id)),
    ];

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

    const exec = model.executive_summary || {};
    const kpis = safeArray(exec.kpi_principali);
    const recs = safeArray(exec.raccomandazioni_30_60_90);

    const kpiTable = kpis.length
        ? `<table class="table">
            <thead><tr><th>KPI</th><th>Valore</th><th>Scenario</th></tr></thead>
            <tbody>
                ${kpis.map(k => {
                    const val = k.unita === "EUR" ? formatEUR(k.valore) : k.unita === "%" ? `${k.valore}%` : (k.valore ?? "—");
                    return `<tr>
                        <td>${escapeHtml(k.nome)}</td>
                        <td class="num">${escapeHtml(String(val))}</td>
                        <td>${escapeHtml(k.scenario)}</td>
                    </tr>`;
                }).join("")}
            </tbody>
        </table>`
        : `<div class="muted">Nessun KPI fornito.</div>`;

    const recTable = recs.length
        ? `<table class="table">
            <thead><tr><th>Orizzonte</th><th>Azione</th><th>Motivazione</th><th>Priorità</th></tr></thead>
            <tbody>
                ${recs.map(r => `<tr>
                    <td>${escapeHtml(String(r.orizzonte_giorni))} gg</td>
                    <td>${escapeHtml(r.azione)}</td>
                    <td>${escapeHtml(r.motivazione)}</td>
                    <td>${escapeHtml(r.priorita)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`
        : `<div class="muted">Nessuna raccomandazione fornita.</div>`;

    const chaptersHtml = orderedChapterIds
        .map((id, idx) => {
            const ch = narrativeById.get(id);
            if (!ch) return "";

            let bodyHtml = ch.contenuto_markdown || "";
            if (typeof marked !== 'undefined') {
                bodyHtml = marked.parse(bodyHtml);
            } else {
                bodyHtml = markdownToHTML(bodyHtml);
            }

            const ids = safeArray(ch.chart_ids).filter(cid => chartById.has(cid));
            const chartBlocks = ids.length
                ? chunkBy(ids, maxChartsPerPage)
                    .map(group => {
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

    const title = layout.titolo_documento || "Business Plan";
    const subtitle = layout.sottotitolo || "";
    const confidentiality = layout.confidenzialita || "uso_interno";

    const styles = `
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
        .page{ padding: 42px 52px 56px; }
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
        .page-break{
            break-before: page;
            page-break-before: always;
        }
    `;

    const html = `<!doctype html>
<html lang="${escapeHtml(meta.lingua || "it-IT")}">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>${escapeHtml(title)}</title>
    ${typeof Chart !== 'undefined' ? '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>' : ''}
    <style>${styles}</style>
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
    ${typeof Chart !== 'undefined' ? `
    <script>
        (function(){
            const charts = ${JSON.stringify(charts)};
            function toXY(points){
                return points.map(p => ({ x: p.x, y: p.y }));
            }
            function buildDataset(series, type){
                return series.map((s, idx) => {
                    const data = toXY(s.points || []);
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
                                    if (typeof v === "number") return new Intl.NumberFormat("it-IT").format(v);
                                    return v;
                                }}
                            }
                        }
                    }
                });
            }
            charts.forEach(makeChart);
            window.__CHARTS_RENDERED__ = true;
        })();
    </script>
    ` : ''}
</body>
</html>`;

    return html;
}

// Funzione helper per generare PDF usando html2canvas direttamente
async function generatePDFWithHtml2Canvas(element, filename, jsonData) {
    try {
        // Carica html2canvas se non disponibile
        if (typeof html2canvas === 'undefined') {
            console.log('📥 Caricamento html2canvas...');
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            document.head.appendChild(script);
            await new Promise((resolve, reject) => {
                script.onload = resolve;
                script.onerror = reject;
                setTimeout(() => reject(new Error('Timeout html2canvas')), 10000);
            });
            console.log('✅ html2canvas caricato');
        }
        
        console.log('📸 Cattura screenshot con html2canvas...');
        
        // Se l'elemento è in un iframe, usa l'iframe window
        const elementWindow = element.ownerDocument.defaultView || window;
        const elementDoc = element.ownerDocument || document;
        
        const canvas = await html2canvas(element, {
            scale: 2,
            useCORS: true,
            logging: true,
            backgroundColor: '#ffffff',
            scrollX: 0,
            scrollY: 0,
            windowWidth: element.scrollWidth || 794,
            windowHeight: element.scrollHeight || 1123,
            allowTaint: true,
            foreignObjectRendering: true
        });
        
        console.log('✅ Screenshot catturato:', {
            width: canvas.width,
            height: canvas.height
        });
        
        const imgData = canvas.toDataURL('image/jpeg', 0.98);
        
        // Usa jsPDF se disponibile
        let pdf;
        if (typeof window.jspdf !== 'undefined') {
            const { jsPDF } = window.jspdf;
            pdf = new jsPDF('p', 'mm', 'a4');
        } else if (typeof jsPDF !== 'undefined') {
            pdf = new jsPDF('p', 'mm', 'a4');
        } else {
            throw new Error('jsPDF non disponibile per il fallback');
        }
        
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 297; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        let heightLeft = imgHeight;
        let position = 0;
        
        pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
        
        while (heightLeft >= 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
        }
        
        pdf.save(filename);
        console.log('✅ PDF generato con approccio alternativo!');
        alert('PDF generato con successo!');
    } catch (altError) {
        console.error('❌ Errore nell\'approccio alternativo:', altError);
        throw altError;
    }
}

// Funzione per generare PDF standalone
async function generatePDFStandalone() {
    console.log('🚀 Inizio generazione PDF da JSON...');
    
    try {
        // 1. Carica il file JSON
        console.log('📥 Caricamento file JSON...');
        const response = await fetch('business-plan-TechStarts.json');
        if (!response.ok) {
            throw new Error(`Errore nel caricamento: ${response.status} ${response.statusText}`);
        }
        const jsonData = await response.json();
        console.log('✅ JSON caricato:', Object.keys(jsonData));
        
        // 2. Carica Chart.js se necessario
        if (typeof Chart === 'undefined') {
            console.log('📥 Caricamento Chart.js...');
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
            document.head.appendChild(script);
            await new Promise((resolve, reject) => {
                script.onload = resolve;
                script.onerror = reject;
                setTimeout(() => reject(new Error('Timeout caricamento Chart.js')), 10000);
            });
            console.log('✅ Chart.js caricato');
        }
        
        // 3. Verifica che html2pdf sia disponibile
        if (typeof html2pdf === 'undefined') {
            throw new Error('html2pdf non disponibile. Assicurati che la libreria sia caricata.');
        }
        console.log('✅ html2pdf disponibile');
        
        // 4. Genera HTML dal JSON
        console.log('📄 Generazione HTML...');
        const contentHTML = buildHtmlFromJSON(jsonData);
        console.log('📊 HTML generato:', {
            length: contentHTML.length,
            hasBody: contentHTML.includes('<body'),
            hasContent: contentHTML.length > 1000
        });
        
        if (!contentHTML || contentHTML.length < 100) {
            throw new Error('L\'HTML generato è troppo corto o vuoto!');
        }
        
        // 4.5. Estrai lo script dei grafici PRIMA di inserire l'HTML nel DOM
        let chartScript = null;
        if (typeof Chart !== 'undefined') {
            // Estrai lo script dall'HTML usando una regex precisa
            const scriptMatch = contentHTML.match(/<script(?:\s+[^>]*)?>([\s\S]*?)<\/script>/i);
            if (scriptMatch && scriptMatch[1] && !scriptMatch[0].includes('src=')) {
                chartScript = scriptMatch[1].trim();
                console.log('✅ Script grafici estratto');
            }
        }
        
        // 5. Crea un iframe temporaneo per isolare il contenuto
        console.log('📦 Creazione iframe temporaneo...');
        const iframe = document.createElement('iframe');
        iframe.style.position = 'absolute';
        iframe.style.top = '0';
        iframe.style.left = '0';
        iframe.style.width = '794px';
        iframe.style.height = '1123px';
        iframe.style.border = 'none';
        iframe.style.visibility = 'hidden';
        iframe.style.zIndex = '-1';
        
        document.body.appendChild(iframe);
        
        // Aspetta che l'iframe sia pronto
        await new Promise(resolve => {
            iframe.onload = resolve;
            iframe.src = 'about:blank';
        });
        
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        iframeDoc.open();
        iframeDoc.write(contentHTML);
        iframeDoc.close();
        
        // Aspetta che il contenuto sia renderizzato nell'iframe
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Esegui gli script dei grafici nell'iframe se necessario
        if (chartScript) {
            try {
                const iframeWindow = iframe.contentWindow;
                // Carica Chart.js nell'iframe se necessario
                if (!iframeWindow.Chart) {
                    const script = iframeDoc.createElement('script');
                    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
                    iframeDoc.head.appendChild(script);
                    await new Promise((resolve) => {
                        script.onload = resolve;
                        setTimeout(resolve, 3000);
                    });
                }
                iframeWindow.eval(chartScript);
                console.log('✅ Script grafici eseguito nell\'iframe');
            } catch (e) {
                console.warn('Errore nell\'esecuzione dello script dei grafici nell\'iframe:', e);
            }
        }
        
        // Aspetta che i grafici siano renderizzati
        let attempts = 0;
        while (attempts < 30) {
            const iframeWindow = iframe.contentWindow;
            if (iframeWindow.__CHARTS_RENDERED__) {
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 200));
            attempts++;
        }
        
        // Usa il body dell'iframe come elemento da catturare
        const tempDiv = iframeDoc.body;
        tempDiv.style.margin = '0';
        tempDiv.style.padding = '20px';
        tempDiv.style.backgroundColor = '#ffffff';
        
        // 6. Verifica che il contenuto sia presente nell'iframe
        const hasContent = tempDiv.innerHTML.trim().length > 0;
        const hasText = tempDiv.textContent.trim().length > 0;
        
        console.log('📊 Verifica contenuto iframe:', {
            hasHTML: hasContent,
            hasText: hasText,
            htmlLength: tempDiv.innerHTML.length,
            textLength: tempDiv.textContent.length
        });
        
        if (!hasContent) {
            document.body.removeChild(iframe);
            throw new Error('Il contenuto HTML è vuoto nell\'iframe!');
        }
        
        // 7. Aspetta ancora un po' per assicurarsi che tutto sia renderizzato
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 8. Genera PDF
        console.log('📄 Generazione PDF in corso...');
        const pdfLayout = jsonData.pdf_layout;
        const title = pdfLayout?.titolo_documento || 'business-plan';
        const filename = `${title.replace(/\s+/g, '-').toLowerCase()}.pdf`;
        
        // Genera PDF usando direttamente html2canvas (più affidabile con iframe)
        console.log('📸 Generazione PDF con html2canvas...');
        await generatePDFWithHtml2Canvas(tempDiv, filename, jsonData);
        
        // 9. Rimuovi l'iframe
        if (iframe && iframe.parentNode) {
            document.body.removeChild(iframe);
        }
        
    } catch (error) {
        console.error('❌ Errore:', error);
        console.error('Stack trace:', error.stack);
        
        // Rimuovi il div temporaneo anche in caso di errore
        const tempDivs = document.querySelectorAll('div[style*="position: fixed"][style*="z-index: 9999"]');
        tempDivs.forEach(div => {
            if (div.parentNode) {
                document.body.removeChild(div);
            }
        });
        
        alert('Errore nella generazione del PDF: ' + error.message + '\n\nControlla la console per maggiori dettagli.');
        throw error; // Rilancia per permettere al chiamante di gestirlo
    }
}

// Esporta sempre le funzioni globalmente per uso manuale
if (typeof window !== 'undefined') {
    window.generatePDFStandalone = generatePDFStandalone;
    window.buildHtmlFromJSON = buildHtmlFromJSON;
}

// Funzione helper per caricare html2pdf se necessario
async function ensureHtml2Pdf() {
    if (typeof html2pdf !== 'undefined') {
        return true;
    }
    
    console.log('📥 Caricamento html2pdf...');
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
        script.onload = () => {
            console.log('✅ html2pdf caricato');
            resolve(true);
        };
        script.onerror = () => {
            console.error('❌ Errore nel caricamento di html2pdf');
            reject(new Error('Impossibile caricare html2pdf'));
        };
        document.head.appendChild(script);
        setTimeout(() => reject(new Error('Timeout caricamento html2pdf')), 10000);
    });
}

// Versione migliorata che carica automaticamente le dipendenze
async function generatePDF() {
    try {
        // Carica html2pdf se necessario
        await ensureHtml2Pdf();
        
        // Chiama la funzione principale
        await generatePDFStandalone();
    } catch (error) {
        console.error('❌ Errore:', error);
        alert('Errore: ' + error.message);
    }
}

// Esporta anche la versione migliorata
if (typeof window !== 'undefined') {
    window.generatePDF = generatePDF;
}

// Esegui automaticamente SOLO se caricato via <script> tag (non dalla console)
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    // Controlla se siamo stati caricati da un tag <script> con src
    const currentScript = document.currentScript;
    const isLoadedViaScriptTag = currentScript && currentScript.src && currentScript.src.includes('generate-pdf-manual.js');
    
    // Esegui automaticamente solo se caricato via script tag
    if (isLoadedViaScriptTag) {
        const autoRun = async () => {
            try {
                await ensureHtml2Pdf();
                await new Promise(resolve => setTimeout(resolve, 500));
                generatePDFStandalone();
            } catch (error) {
                console.error('Errore nell\'esecuzione automatica:', error);
            }
        };
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', autoRun);
        } else {
            autoRun();
        }
    } else {
        // Se eseguito dalla console, mostra istruzioni
        console.log('%c✅ Script caricato!', 'color: green; font-weight: bold;');
        console.log('%c📝 Per generare il PDF, esegui una di queste opzioni:', 'color: blue; font-weight: bold;');
        console.log('   1. generatePDF() - carica automaticamente html2pdf se necessario');
        console.log('   2. generatePDFStandalone() - richiede html2pdf già caricato');
        console.log('');
        console.log('%c💡 Se html2pdf non è caricato, usa generatePDF() che lo caricherà automaticamente.', 'color: orange;');
    }
}
