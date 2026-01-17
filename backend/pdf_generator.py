import json
import re
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Backend non interattivo per server
import matplotlib.pyplot as plt

def markdown_to_paragraphs(text, styles):
    """Converte markdown in paragrafi ReportLab"""
    elements = []
    
    if not text:
        return elements
    
    # Dividi per righe
    lines = text.split('\n')
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if current_paragraph:
                elements.append(Paragraph(' '.join(current_paragraph), styles['Normal']))
                elements.append(Spacer(1, 0.3*cm))
                current_paragraph = []
            continue
        
        # Titoli
        if line.startswith('###'):
            if current_paragraph:
                elements.append(Paragraph(' '.join(current_paragraph), styles['Normal']))
                current_paragraph = []
            title = line.replace('###', '').strip()
            # Escape HTML entities
            title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(title, styles['Heading3']))
            elements.append(Spacer(1, 0.2*cm))
        elif line.startswith('##'):
            if current_paragraph:
                elements.append(Paragraph(' '.join(current_paragraph), styles['Normal']))
                current_paragraph = []
            title = line.replace('##', '').strip()
            title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(title, styles['Heading2']))
            elements.append(Spacer(1, 0.3*cm))
        elif line.startswith('#'):
            if current_paragraph:
                elements.append(Paragraph(' '.join(current_paragraph), styles['Normal']))
                current_paragraph = []
            title = line.replace('#', '').strip()
            title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(title, styles['Heading1']))
            elements.append(Spacer(1, 0.4*cm))
        # Liste
        elif line.startswith('- ') or line.startswith('* '):
            if current_paragraph:
                elements.append(Paragraph(' '.join(current_paragraph), styles['Normal']))
                current_paragraph = []
            item = line[2:].strip()
            # Escape HTML entities
            item = item.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(f"• {item}", styles['Normal']))
            elements.append(Spacer(1, 0.2*cm))
        # Liste numerate
        elif re.match(r'^\d+\.\s', line):
            if current_paragraph:
                elements.append(Paragraph(' '.join(current_paragraph), styles['Normal']))
                current_paragraph = []
            item = re.sub(r'^\d+\.\s', '', line).strip()
            item = item.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(f"• {item}", styles['Normal']))
            elements.append(Spacer(1, 0.2*cm))
        else:
            # Testo normale
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            current_paragraph.append(line)
    
    # Aggiungi ultimo paragrafo
    if current_paragraph:
        elements.append(Paragraph(' '.join(current_paragraph), styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))
    
    return elements

def create_chart_image(chart_data, width=15*cm, height=10*cm):
    """Crea un'immagine del grafico da inserire nel PDF"""
    tipo = chart_data.get('tipo', 'line')
    titolo = chart_data.get('titolo', '')
    x_label = chart_data.get('x_label', '')
    y_label = chart_data.get('y_label', '')
    series = chart_data.get('series', [])
    
    # Crea la figura
    fig, ax = plt.subplots(figsize=(width/cm, height/cm))
    
    # Colori per le serie
    colors_list = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    
    if tipo == 'line':
        for idx, serie in enumerate(series):
            name = serie.get('name', f'Serie {idx+1}')
            points = serie.get('points', [])
            x_values = [p.get('x', '') for p in points]
            y_values = [p.get('y', 0) for p in points]
            # Rimuovi valori vuoti
            x_clean = []
            y_clean = []
            for x, y in zip(x_values, y_values):
                if x and y is not None:
                    x_clean.append(x)
                    y_clean.append(y)
            if x_clean and y_clean:
                ax.plot(x_clean, y_clean, marker='o', label=name, 
                        color=colors_list[idx % len(colors_list)], linewidth=2, markersize=6)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    elif tipo == 'bar':
        for idx, serie in enumerate(series):
            name = serie.get('name', f'Serie {idx+1}')
            points = serie.get('points', [])
            x_values = [p.get('x', '') for p in points if p.get('x')]
            y_values = [p.get('y', 0) for p in points if p.get('x')]
            if x_values and y_values:
                x_pos = range(len(x_values))
                ax.bar([p + idx*0.25 for p in x_pos], y_values, 
                       width=0.25, label=name, color=colors_list[idx % len(colors_list)], alpha=0.8)
                ax.set_xticks([p + 0.125 for p in x_pos])
                ax.set_xticklabels(x_values, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
    elif tipo == 'pie':
        for serie in series:
            points = serie.get('points', [])
            labels = [p.get('x', '') for p in points if p.get('x')]
            values = [p.get('y', 0) for p in points if p.get('x')]
            if labels and values:
                ax.pie(values, labels=labels, autopct='%1.1f%%', 
                      colors=colors_list[:len(values)], startangle=90)
                ax.axis('equal')
    
    ax.set_title(titolo, fontsize=12, fontweight='bold', pad=10)
    if x_label:
        ax.set_xlabel(x_label, fontsize=10)
    if y_label:
        ax.set_ylabel(y_label, fontsize=10)
    
    plt.tight_layout()
    
    # Salva in un buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

async def create_pdf_from_json(business_plan_json: dict) -> str:
    """Crea il PDF professionale dal JSON"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "business-plan.pdf"
    
    # Crea il documento PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )
    
    # Stili
    styles = getSampleStyleSheet()
    
    # Stili personalizzati
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=8
    ))
    
    # Story (contenuto del PDF)
    story = []
    
    # Header e titolo
    pdf_layout = business_plan_json.get('pdf_layout', {})
    titolo = pdf_layout.get('titolo_documento', 'Business Plan')
    sottotitolo = pdf_layout.get('sottotitolo', '')
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(titolo, styles['CustomTitle']))
    if sottotitolo:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(sottotitolo, styles['Heading2']))
    story.append(Spacer(1, 0.5*cm))
    
    # Data generazione
    meta = business_plan_json.get('meta', {})
    data_gen = meta.get('data_generazione', datetime.now().strftime('%d/%m/%Y'))
    story.append(Paragraph(f"<i>Generato il: {data_gen}</i>", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Executive Summary
    exec_summary = business_plan_json.get('executive_summary', {})
    if exec_summary:
        story.append(Paragraph("EXECUTIVE SUMMARY", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        sintesi = exec_summary.get('sintesi', '')
        if sintesi:
            sintesi_clean = sintesi.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(sintesi_clean, styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
        
        punti_chiave = exec_summary.get('punti_chiave', [])
        if punti_chiave:
            story.append(Paragraph("<b>Punti Chiave:</b>", styles['Heading3']))
            for punto in punti_chiave:
                punto_clean = punto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"• {punto_clean}", styles['Normal']))
            story.append(Spacer(1, 0.3*cm))
        
        # KPI principali come tabella
        kpis = exec_summary.get('kpi_principali', [])
        if kpis:
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("<b>KPI Principali:</b>", styles['Heading3']))
            story.append(Spacer(1, 0.2*cm))
            
            kpi_data = [["KPI", "Valore", "Scenario"]]
            for kpi in kpis:
                nome = kpi.get('nome', '')
                valore = kpi.get('valore', '')
                unita = kpi.get('unita', '')
                scenario = kpi.get('scenario', '')
                
                # Formatta il valore
                if unita == 'EUR':
                    try:
                        val_num = float(valore) if isinstance(valore, str) else valore
                        valore_str = f"{val_num:,.0f} €"
                    except:
                        valore_str = str(valore)
                elif unita == '%':
                    valore_str = f"{valore}%"
                else:
                    valore_str = str(valore)
                
                kpi_data.append([nome, valore_str, scenario])
            
            if len(kpi_data) > 1:  # Se ci sono KPI oltre l'header
                kpi_table = Table(kpi_data)
                kpi_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f7f7f8')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111111')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e6e6e6')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(kpi_table)
        
        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())
    
    # Capitoli narrativi
    narrative = business_plan_json.get('narrative', {})
    chapters = narrative.get('chapters', [])
    
    # Ordine dei capitoli dal pdf_layout
    chapter_order = pdf_layout.get('chapter_order', [])
    
    # Se c'è un ordine specificato, usalo, altrimenti usa l'ordine naturale
    if chapter_order:
        chapters_dict = {ch['id']: ch for ch in chapters}
        ordered_chapters = [chapters_dict.get(ch_id) for ch_id in chapter_order if ch_id in chapters_dict]
        # Aggiungi capitoli non nell'ordine
        for ch in chapters:
            if ch['id'] not in chapter_order:
                ordered_chapters.append(ch)
        chapters = ordered_chapters
    
    # Crea un dizionario dei grafici per accesso rapido
    charts_dict = {chart['id']: chart for chart in business_plan_json.get('charts', [])}
    
    for chapter in chapters:
        titolo_ch = chapter.get('titolo', '')
        contenuto = chapter.get('contenuto_markdown', '')
        chart_ids = chapter.get('chart_ids', [])
        
        if titolo_ch:
            story.append(Paragraph(titolo_ch, styles['CustomHeading1']))
            story.append(Spacer(1, 0.3*cm))
        
        if contenuto:
            elements = markdown_to_paragraphs(contenuto, styles)
            story.extend(elements)
        
        # Aggiungi i grafici referenziati
        if chart_ids:
            story.append(Spacer(1, 0.5*cm))
            for chart_id in chart_ids:
                if chart_id in charts_dict:
                    chart = charts_dict[chart_id]
                    try:
                        chart_img = create_chart_image(chart, width=15*cm, height=10*cm)
                        img = Image(chart_img, width=15*cm, height=10*cm)
                        story.append(img)
                        story.append(Spacer(1, 0.3*cm))
                        
                        # Aggiungi caption se presente
                        caption = chart.get('caption', '')
                        if caption:
                            caption_clean = caption.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            story.append(Paragraph(f"<i>{caption_clean}</i>", styles['Normal']))
                            story.append(Spacer(1, 0.3*cm))
                    except Exception as e:
                        print(f"⚠️  Errore nel generare il grafico {chart_id}: {str(e)}")
        
        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())
    
    # Assunzioni e Dati Mancanti
    assumptions = business_plan_json.get('assumptions', [])
    if assumptions:
        story.append(Paragraph("ASSUNZIONI", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        for ass in assumptions:
            ass_clean = ass.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"• {ass_clean}", styles['Normal']))
            story.append(Spacer(1, 0.2*cm))
        story.append(Spacer(1, 0.5*cm))
    
    dati_mancanti = business_plan_json.get('dati_mancanti', [])
    if dati_mancanti:
        story.append(Paragraph("DATI MANCANTI", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        for dato in dati_mancanti:
            dato_clean = dato.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"• {dato_clean}", styles['Normal']))
            story.append(Spacer(1, 0.2*cm))
        story.append(Spacer(1, 0.5*cm))
    
    # Disclaimer
    disclaimer = business_plan_json.get('disclaimer', '')
    if disclaimer:
        story.append(PageBreak())
        story.append(Paragraph("DISCLAIMER", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        disclaimer_clean = disclaimer.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(disclaimer_clean, styles['Normal']))
    
    # Genera il PDF
    doc.build(story)
    print(f"✓ PDF generato con successo: {output_path}")
    
    return str(output_path)
