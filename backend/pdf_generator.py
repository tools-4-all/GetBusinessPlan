import json
import re
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether
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

def create_numbered_canvas(header_left, header_right, footer_left, footer_center, footer_right, confidenzialita):
    """Crea funzioni callback per header/footer e numerazione pagine"""
    
    def on_first_page(canvas_obj, doc):
        # Prima pagina (copertina) senza header/footer
        pass
    
    def on_later_pages(canvas_obj, doc):
        page_num = canvas_obj.getPageNumber()
        canvas_obj.saveState()
        canvas_obj.setFont("Times-Roman", 8)
        canvas_obj.setFillColor(colors.HexColor('#666666'))
        
        # Header (solo dalla seconda pagina in poi)
        if page_num > 1:
            if header_left:
                canvas_obj.drawString(2*cm, A4[1] - 1.5*cm, header_left)
            if header_right:
                canvas_obj.drawRightString(A4[0] - 2*cm, A4[1] - 1.5*cm, header_right)
            
            # Linea sotto header
            canvas_obj.setStrokeColor(colors.HexColor('#cccccc'))
            canvas_obj.setLineWidth(0.5)
            canvas_obj.line(2*cm, A4[1] - 1.8*cm, A4[0] - 2*cm, A4[1] - 1.8*cm)
        
        # Footer
        if footer_left:
            canvas_obj.drawString(2*cm, 1.2*cm, footer_left)
        if footer_center:
            width = canvas_obj.stringWidth(footer_center, "Times-Roman", 8)
            canvas_obj.drawString((A4[0] - width) / 2, 1.2*cm, footer_center)
        
        # Numerazione pagine
        canvas_obj.setFont("Times-Roman", 9)
        page_text = f"Pagina {page_num}"
        canvas_obj.drawRightString(A4[0] - 2*cm, 1.5*cm, page_text)
        
        # Linea sopra footer
        canvas_obj.setStrokeColor(colors.HexColor('#cccccc'))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)
        
        # Watermark confidenzialità se presente
        if confidenzialita and confidenzialita != 'pubblico' and page_num > 1:
            canvas_obj.setFont("Times-Bold", 10)
            canvas_obj.setFillColor(colors.HexColor('#cccccc'))
            conf_text = "CONFIDENZIALE" if confidenzialita == 'confidenziale' else "USO INTERNO"
            width = canvas_obj.stringWidth(conf_text, "Times-Bold", 10)
            canvas_obj.drawString((A4[0] - width) / 2, A4[1] - 1.5*cm, conf_text)
        
        canvas_obj.restoreState()
    
    return on_first_page, on_later_pages

async def create_pdf_from_json(business_plan_json: dict) -> str:
    """Crea il PDF professionale dal JSON"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "business-plan.pdf"
    
    # Estrai informazioni per header/footer
    pdf_layout = business_plan_json.get('pdf_layout', {})
    header_info = pdf_layout.get('header', {})
    footer_info = pdf_layout.get('footer', {})
    confidenzialita = pdf_layout.get('confidenzialita', 'pubblico')
    
    # Crea il documento PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=3*cm,
        bottomMargin=2.5*cm
    )
    
    # Crea le funzioni callback per header/footer
    on_first_page, on_later_pages = create_numbered_canvas(
        header_info.get('left', ''),
        header_info.get('right', ''),
        footer_info.get('left', ''),
        footer_info.get('center', ''),
        footer_info.get('right', ''),
        confidenzialita
    )
    
    # Assegna i callback
    doc.onFirstPage = on_first_page
    doc.onLaterPages = on_later_pages
    
    # Stili con font professionali (Times New Roman)
    styles = getSampleStyleSheet()
    
    # Stili personalizzati con Times-Roman per aspetto formale
    styles.add(ParagraphStyle(
        name='CoverTitle',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=28,
        textColor=colors.HexColor('#000000'),
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=34
    ))
    
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        parent=styles['Heading2'],
        fontName='Times-Roman',
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=20
    ))
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=24,
        textColor=colors.HexColor('#000000'),
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=18,
        textColor=colors.HexColor('#000000'),
        spaceAfter=12,
        spaceBefore=16,
        leading=22
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontName='Times-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=8,
        spaceBefore=12,
        leading=18
    ))
    
    # Modifica lo stile Normal esistente invece di aggiungerne uno nuovo
    styles['Normal'].fontName = 'Times-Roman'
    styles['Normal'].fontSize = 11
    styles['Normal'].textColor = colors.HexColor('#000000')
    styles['Normal'].leading = 14
    styles['Normal'].alignment = TA_JUSTIFY
    
    styles.add(ParagraphStyle(
        name='TOCEntry',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=11,
        leftIndent=0,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='TOCHeading',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=16,
        textColor=colors.HexColor('#000000'),
        spaceAfter=20,
        alignment=TA_CENTER
    ))
    
    # Story (contenuto del PDF)
    story = []
    
    # === COPERTINA PROFESSIONALE COLORATA ===
    titolo = pdf_layout.get('titolo_documento', 'Business Plan')
    sottotitolo = pdf_layout.get('sottotitolo', '')
    meta = business_plan_json.get('meta', {})
    data = business_plan_json.get('data', {})
    company_name = data.get('company_name', '')
    data_gen = meta.get('data_generazione', datetime.now().strftime('%d/%m/%Y'))
    versione = meta.get('versione', '1.0')
    
    # Colori professionali per la copertina
    primary_color = colors.HexColor('#1e3a8a')  # Blu scuro professionale
    accent_color = colors.HexColor('#3b82f6')   # Blu medio
    light_bg = colors.HexColor('#f0f4ff')        # Sfondo chiaro
    
    # Box colorato superiore
    cover_header = Table([
        ['']  # Spazio per il box colorato
    ], colWidths=[A4[0] - 4*cm], rowHeights=[3*cm])
    cover_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cover_header)
    
    # Spazio e contenuto principale
    story.append(Spacer(1, 2*cm))
    
    # Titolo principale con stile elegante
    title_style = ParagraphStyle(
        name='CoverTitleColored',
        parent=styles['CoverTitle'],
        fontName='Times-Bold',
        fontSize=32,
        textColor=primary_color,
        spaceAfter=15,
        alignment=TA_CENTER,
        leading=38
    )
    story.append(Paragraph(titolo, title_style))
    
    # Linea decorativa sotto il titolo
    decor_line = Table([['']], colWidths=[8*cm], rowHeights=[0.2*cm])
    decor_line.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(decor_line)
    
    if sottotitolo:
        story.append(Spacer(1, 0.8*cm))
        subtitle_style = ParagraphStyle(
            name='CoverSubtitleColored',
            parent=styles['CoverSubtitle'],
            fontName='Times-Roman',
            fontSize=14,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=20,
            alignment=TA_CENTER,
            leading=18
        )
        story.append(Paragraph(sottotitolo, subtitle_style))
    
    story.append(Spacer(1, 2.5*cm))
    
    # Box informativo con sfondo colorato
    info_data = []
    if company_name:
        info_data.append([f"<b>Azienda:</b> {company_name}"])
    info_data.append([f"<b>Data:</b> {data_gen}"])
    info_data.append([f"<b>Versione:</b> {versione}"])
    
    if info_data:
        info_table = Table(info_data, colWidths=[12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_bg),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 1.5*cm))
    
    # Badge confidenzialità se presente
    if confidenzialita and confidenzialita != 'pubblico':
        conf_text = "CONFIDENZIALE" if confidenzialita == 'confidenziale' else "USO INTERNO"
        conf_color = colors.HexColor('#dc2626') if confidenzialita == 'confidenziale' else colors.HexColor('#f59e0b')
        conf_table = Table([[conf_text]], colWidths=[6*cm], rowHeights=[1*cm])
        conf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), conf_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(conf_table)
    
    story.append(PageBreak())
    
    # === INDICE ===
    story.append(Paragraph("INDICE", styles['TOCHeading']))
    story.append(Spacer(1, 0.5*cm))
    
    # Costruisci l'indice dai capitoli
    narrative = business_plan_json.get('narrative', {})
    chapters = narrative.get('chapters', [])
    chapter_order = pdf_layout.get('chapter_order', [])
    
    if chapter_order:
        chapters_dict = {ch['id']: ch for ch in chapters}
        ordered_chapters = [chapters_dict.get(ch_id) for ch_id in chapter_order if ch_id in chapters_dict]
        for ch in chapters:
            if ch['id'] not in chapter_order:
                ordered_chapters.append(ch)
        chapters = ordered_chapters
    
    toc_entries = []
    page_num = 3  # Inizia dopo copertina e indice
    
    # Executive Summary
    exec_summary = business_plan_json.get('executive_summary', {})
    if exec_summary:
        toc_entries.append(("Executive Summary", page_num))
        page_num += 1
    
    # Capitoli
    for chapter in chapters:
        titolo_ch = chapter.get('titolo', '')
        if titolo_ch:
            toc_entries.append((titolo_ch, page_num))
            page_num += 1
    
    # Assunzioni
    assumptions = business_plan_json.get('assumptions', [])
    if assumptions:
        toc_entries.append(("Assunzioni", page_num))
        page_num += 1
    
    # Dati Mancanti
    dati_mancanti = business_plan_json.get('dati_mancanti', [])
    if dati_mancanti:
        toc_entries.append(("Dati Mancanti", page_num))
        page_num += 1
    
    # Disclaimer
    disclaimer = business_plan_json.get('disclaimer', '')
    if disclaimer:
        toc_entries.append(("Disclaimer", page_num))
    
    # Aggiungi voci indice
    for entry_title, entry_page in toc_entries:
        # Crea una tabella per allineare titolo e numero pagina
        toc_table = Table([[entry_title, str(entry_page)]], colWidths=[14*cm, 2*cm])
        toc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(toc_table)
    
    story.append(PageBreak())
    
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
                kpi_table = Table(kpi_data, colWidths=[6*cm, 4*cm, 4*cm])
                kpi_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('TOPPADDING', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ]))
                story.append(kpi_table)
        
        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())
    
    # === CAPITOLI NARRATIVI ===
    # (chapters già ordinati sopra)
    
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
        story.append(Paragraph("DISCLAIMER E NOTE LEGALI", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        disclaimer_clean = disclaimer.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(disclaimer_clean, styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
        # Note legali aggiuntive
        note_legali = """
        <b>Note Legali:</b><br/><br/>
        Questo documento è stato generato automaticamente mediante intelligenza artificiale. 
        Le informazioni contenute sono basate sui dati forniti dall'utente e su assunzioni 
        esplicitate nel documento. Si raccomanda di:<br/><br/>
        • Verificare tutti i dati finanziari e le proiezioni con un consulente fiscale o commercialista abilitato<br/>
        • Verificare la conformità normativa con un consulente legale specializzato<br/>
        • Validare le assunzioni di mercato con ricerche di mercato approfondite<br/>
        • Aggiornare regolarmente il documento con dati reali man mano che diventano disponibili<br/><br/>
        Il presente documento non costituisce consulenza finanziaria, legale o fiscale. 
        L'utilizzo delle informazioni contenute è a proprio rischio e pericolo.
        """
        story.append(Paragraph(note_legali, styles['Normal']))
    
    # Pagina di firma/approvazione
    story.append(PageBreak())
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("APPROVAZIONE E FIRMA", styles['CustomHeading1']))
    story.append(Spacer(1, 1*cm))
    
    firma_text = f"""
    Il presente Business Plan è stato redatto in data {data_gen} e approvato da:
    """
    story.append(Paragraph(firma_text, styles['Normal']))
    story.append(Spacer(1, 2*cm))
    
    # Tabella firme
    if company_name:
        firma_table = Table([
            ['Preparato da:', ''],
            ['', ''],
            ['', ''],
            ['Firma:', ''],
            ['', ''],
            ['', ''],
            ['Approvato da:', ''],
            ['', ''],
            ['', ''],
            ['Firma:', ''],
        ], colWidths=[8*cm, 8*cm])
        firma_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('LINEBELOW', (0, 2), (1, 2), 1, colors.black),
            ('LINEBELOW', (0, 5), (1, 5), 1, colors.black),
            ('LINEBELOW', (0, 9), (1, 9), 1, colors.black),
        ]))
        story.append(firma_table)
    
    # === PAGINA FINALE DI CHIUSURA ===
    story.append(PageBreak())
    
    # Box colorato superiore (come copertina)
    closing_header = Table([['']], colWidths=[A4[0] - 4*cm], rowHeights=[2*cm])
    closing_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(closing_header)
    
    story.append(Spacer(1, 3*cm))
    
    # Messaggio di chiusura
    closing_title_style = ParagraphStyle(
        name='ClosingTitle',
        parent=styles['CoverTitle'],
        fontName='Times-Bold',
        fontSize=24,
        textColor=primary_color,
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=30
    )
    story.append(Paragraph("Grazie per l'attenzione", closing_title_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    # Messaggio professionale
    closing_message = """
    <p align="center">
    Questo Business Plan è stato redatto con cura e attenzione ai dettagli.<br/><br/>
    Per ulteriori informazioni o chiarimenti, non esitate a contattarci.<br/><br/>
    <i>Documento generato con GetBusinessPlan</i>
    </p>
    """
    closing_style = ParagraphStyle(
        name='ClosingMessage',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        textColor=colors.HexColor('#4b5563'),
        alignment=TA_CENTER,
        leading=18
    )
    story.append(Paragraph(closing_message, closing_style))
    
    story.append(Spacer(1, 2*cm))
    
    # Box informativo finale
    final_info = [
        [f"<b>Documento:</b> {titolo}"],
        [f"<b>Data generazione:</b> {data_gen}"],
        [f"<b>Versione:</b> {versione}"]
    ]
    if company_name:
        final_info.insert(0, [f"<b>Azienda:</b> {company_name}"])
    
    final_info_table = Table(final_info, colWidths=[12*cm])
    final_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    story.append(final_info_table)
    
    story.append(Spacer(1, 4*cm))
    
    # Footer decorativo
    footer_decor = Table([['']], colWidths=[A4[0] - 4*cm], rowHeights=[0.3*cm])
    footer_decor.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent_color),
    ]))
    story.append(footer_decor)
    
    # Genera il PDF
    doc.build(story)
    print(f"✓ PDF generato con successo: {output_path}")
    
    return str(output_path)
