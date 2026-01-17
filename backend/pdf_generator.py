from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from pathlib import Path
from html.parser import HTMLParser
import re

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, d):
        self.text.append(d)
    
    def get_text(self):
        return ''.join(self.text)

def strip_html(html):
    s = HTMLStripper()
    s.feed(html)
    return s.get_text()

def markdown_to_paragraphs(md_text, styles):
    """Converte markdown in paragrafi ReportLab (semplificato, senza libreria markdown)"""
    # Semplice conversione markdown senza dipendenze esterne
    text = md_text
    
    # Rimuovi markdown headers
    text = re.sub(r'^###\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Rimuovi markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    
    # Dividi in paragrafi
    paragraphs = text.split('\n\n')
    result = []
    for para in paragraphs:
        para = para.strip()
        if para:
            # Gestisci liste
            lines = para.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    if line.startswith('- ') or line.startswith('* '):
                        result.append(Paragraph(f"• {line[2:]}", styles['Normal']))
                    else:
                        result.append(Paragraph(line, styles['Normal']))
                    result.append(Spacer(1, 4))
            result.append(Spacer(1, 6))
    return result

async def create_pdf_from_json(business_plan_json: dict) -> str:
    """Genera PDF usando ReportLab (puro Python, nessuna dipendenza nativa)"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "business-plan.pdf"
    
    # Crea il documento PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=44*mm,
        leftMargin=44*mm,
        topMargin=70*mm,
        bottomMargin=70*mm
    )
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#111111'),
        spaceAfter=14,
        leading=24
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=15,
        textColor=colors.HexColor('#111111'),
        spaceAfter=8,
        leading=18
    )
    
    # Contenuto del PDF
    story = []
    
    # Cover page
    meta = business_plan_json.get("meta", {})
    layout = business_plan_json.get("pdf_layout", {})
    title = layout.get("titolo_documento", "Business Plan")
    subtitle = layout.get("sottotitolo", "")
    confidentiality = layout.get("confidenzialita", "uso_interno")
    
    story.append(Paragraph(confidentiality.upper(), styles['Normal']))
    story.append(Spacer(1, 14))
    story.append(Paragraph(title, title_style))
    if subtitle:
        story.append(Paragraph(subtitle, styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Meta info
    meta_text = f"Lingua: {meta.get('lingua', 'it-IT')} | Stile: {meta.get('stile', 'formale')} | Orizzonte: {meta.get('orizzonte_mesi', '')} mesi"
    story.append(Paragraph(meta_text, styles['Normal']))
    story.append(PageBreak())
    
    # Executive Summary
    exec = business_plan_json.get("executive_summary", {})
    story.append(Paragraph("Executive Summary", title_style))
    story.append(Spacer(1, 8))
    
    if exec.get("sintesi"):
        story.extend(markdown_to_paragraphs(exec.get("sintesi", ""), styles))
    
    # Punti chiave
    if exec.get("punti_chiave"):
        story.append(Paragraph("Punti chiave", heading_style))
        for punto in exec.get("punti_chiave", []):
            story.append(Paragraph(f"• {punto}", styles['Normal']))
            story.append(Spacer(1, 4))
    
    # KPI
    kpis = exec.get("kpi_principali", [])
    if kpis:
        story.append(Paragraph("KPI principali", heading_style))
        kpi_data = [["KPI", "Valore", "Scenario"]]
        for kpi in kpis:
            val = kpi.get("valore", "")
            if kpi.get("unita") == "EUR":
                val = f"{val:,.0f} €"
            elif kpi.get("unita") == "%":
                val = f"{val}%"
            kpi_data.append([kpi.get("nome", ""), str(val), kpi.get("scenario", "")])
        
        kpi_table = Table(kpi_data)
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f7f7f8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111111')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e6e6e6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 12))
    
    story.append(PageBreak())
    
    # Capitoli
    narrative = business_plan_json.get("narrative", {})
    chapters = narrative.get("chapters", [])
    layout_order = layout.get("chapter_order", [])
    
    # Ordina capitoli
    chapter_dict = {ch["id"]: ch for ch in chapters}
    ordered_ids = [id for id in layout_order if id in chapter_dict]
    ordered_ids.extend([ch["id"] for ch in chapters if ch["id"] not in layout_order])
    
    for idx, ch_id in enumerate(ordered_ids):
        if ch_id not in chapter_dict:
            continue
        
        ch = chapter_dict[ch_id]
        story.append(Paragraph(f"Capitolo {idx + 1}", styles['Normal']))
        story.append(Paragraph(ch.get("titolo", ""), title_style))
        story.append(Spacer(1, 8))
        
        # Contenuto markdown
        content = ch.get("contenuto_markdown", "")
        if content:
            story.extend(markdown_to_paragraphs(content, styles))
        
        # Grafici come note (ReportLab non supporta grafici complessi facilmente)
        chart_ids = ch.get("chart_ids", [])
        charts = business_plan_json.get("charts", [])
        chart_dict = {c["id"]: c for c in charts}
        
        for chart_id in chart_ids:
            if chart_id in chart_dict:
                chart = chart_dict[chart_id]
                story.append(Spacer(1, 8))
                story.append(Paragraph(f"Grafico: {chart.get('titolo', chart_id)}", heading_style))
                # Mostra dati come testo
                if chart.get("series"):
                    for series in chart.get("series", []):
                        points_text = ", ".join([f"{p.get('x')}: {p.get('y')}" for p in series.get("points", [])[:10]])
                        story.append(Paragraph(f"{series.get('name', 'Serie')}: {points_text}", styles['Normal']))
        
        story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    
    return str(output_path)
