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
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pdf_generator import markdown_to_paragraphs, create_chart_image, create_numbered_canvas

async def create_pdf_from_market_analysis(market_analysis_json: dict) -> str:
    """Crea il PDF professionale dall'analisi di mercato"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "analisi-mercato.pdf"
    
    # Estrai informazioni per header/footer
    header_info = {'left': '', 'right': ''}
    footer_info = {'left': '', 'center': 'Analisi di Mercato', 'right': ''}
    confidenzialita = 'pubblico'
    
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
    
    # Stili personalizzati
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
    
    # Story (contenuto del PDF)
    story = []
    
    # === COPERTINA PROFESSIONALE COLORATA ===
    meta = market_analysis_json.get('meta', {})
    titolo = f"Analisi di Mercato {meta.get('tipo_analisi', '').upper() if meta.get('tipo_analisi') == 'deep' else ''}"
    settore = meta.get('settore', '')
    area_geografica = meta.get('area_geografica', '')
    data_gen = meta.get('data_generazione', datetime.now().strftime('%d/%m/%Y'))
    
    # Colori professionali per la copertina (verde per analisi di mercato)
    primary_color = colors.HexColor('#065f46')  # Verde scuro professionale
    accent_color = colors.HexColor('#10b981')   # Verde medio
    light_bg = colors.HexColor('#f0fdf4')       # Sfondo chiaro verde
    
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
    
    # Definisci lo stile del sottotitolo
    subtitle_style = ParagraphStyle(
        name='CoverSubtitleColored',
        parent=styles['CoverSubtitle'],
        fontName='Times-Roman',
        fontSize=14,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=10,
        alignment=TA_CENTER,
        leading=18
    )
    
    if settore:
        story.append(Spacer(1, 0.8*cm))
        story.append(Paragraph(settore, subtitle_style))
    
    if area_geografica:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"Area Geografica: {area_geografica}", subtitle_style))
    
    story.append(Spacer(1, 2.5*cm))
    
    # Box informativo con sfondo colorato
    info_data = []
    info_data.append([f"<b>Data:</b> {data_gen}"])
    if settore:
        info_data.append([f"<b>Settore:</b> {settore}"])
    if area_geografica:
        info_data.append([f"<b>Area:</b> {area_geografica}"])
    
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
    
    story.append(PageBreak())
    
    # === INDICE ===
    story.append(Paragraph("INDICE", styles['CustomTitle']))
    story.append(Spacer(1, 0.5*cm))
    
    toc_entries = []
    page_num = 3
    
    exec_summary = market_analysis_json.get('executive_summary', {})
    if exec_summary:
        toc_entries.append(("Executive Summary", page_num))
        page_num += 1
    
    if market_analysis_json.get('market_size'):
        toc_entries.append(("Dimensioni del Mercato", page_num))
        page_num += 1
    
    if market_analysis_json.get('competitor_analysis'):
        toc_entries.append(("Analisi Competitor", page_num))
        page_num += 1
    
    if market_analysis_json.get('trends_opportunities'):
        toc_entries.append(("Trend e Opportunità", page_num))
        page_num += 1
    
    if market_analysis_json.get('swot_analysis'):
        toc_entries.append(("Analisi SWOT", page_num))
        page_num += 1
    
    if market_analysis_json.get('positioning_strategy'):
        toc_entries.append(("Strategia di Posizionamento", page_num))
        page_num += 1
    
    if market_analysis_json.get('charts'):
        toc_entries.append(("Grafici", page_num))
        page_num += 1
    
    if market_analysis_json.get('sources'):
        toc_entries.append(("Fonti", page_num))
        page_num += 1
    
    if market_analysis_json.get('assumptions'):
        toc_entries.append(("Assunzioni", page_num))
    
    # Aggiungi voci indice
    for entry_title, entry_page in toc_entries:
        toc_table = Table([[entry_title, str(entry_page)]], colWidths=[14*cm, 2*cm])
        toc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
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
    exec_summary = market_analysis_json.get('executive_summary', {})
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
        
        raccomandazioni = exec_summary.get('raccomandazioni', [])
        if raccomandazioni:
            story.append(Paragraph("<b>Raccomandazioni Principali:</b>", styles['Heading3']))
            for rec in raccomandazioni:
                rec_clean = rec.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"• {rec_clean}", styles['Normal']))
        
        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())
    
    # Market Size
    market_size = market_analysis_json.get('market_size', {})
    if market_size:
        story.append(Paragraph("DIMENSIONI DEL MERCATO", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        # TAM
        if market_size.get('tam'):
            tam = market_size['tam']
            story.append(Paragraph("<b>TAM (Total Addressable Market)</b>", styles['Heading3']))
            valore = tam.get('valore', 0)
            unita = tam.get('unita', 'EUR')
            if unita == 'EUR':
                valore_str = f"{valore:,.0f} €"
            else:
                valore_str = f"{valore:,.0f} {unita}"
            story.append(Paragraph(f"Valore: {valore_str}", styles['Normal']))
            if tam.get('fonte'):
                story.append(Paragraph(f"Fonte: {tam.get('fonte')} ({tam.get('anno', 'N/A')})", styles['Normal']))
            if tam.get('descrizione'):
                story.extend(markdown_to_paragraphs(tam.get('descrizione', ''), styles))
            story.append(Spacer(1, 0.3*cm))
        
        # SAM
        if market_size.get('sam'):
            sam = market_size['sam']
            story.append(Paragraph("<b>SAM (Serviceable Addressable Market)</b>", styles['Heading3']))
            valore = sam.get('valore', 0)
            unita = sam.get('unita', 'EUR')
            if unita == 'EUR':
                valore_str = f"{valore:,.0f} €"
            else:
                valore_str = f"{valore:,.0f} {unita}"
            story.append(Paragraph(f"Valore: {valore_str}", styles['Normal']))
            if sam.get('fonte'):
                story.append(Paragraph(f"Fonte: {sam.get('fonte')} ({sam.get('anno', 'N/A')})", styles['Normal']))
            if sam.get('descrizione'):
                story.extend(markdown_to_paragraphs(sam.get('descrizione', ''), styles))
            story.append(Spacer(1, 0.3*cm))
        
        # SOM
        if market_size.get('som'):
            som = market_size['som']
            story.append(Paragraph("<b>SOM (Serviceable Obtainable Market)</b>", styles['Heading3']))
            valore = som.get('valore', 0)
            unita = som.get('unita', 'EUR')
            if unita == 'EUR':
                valore_str = f"{valore:,.0f} €"
            else:
                valore_str = f"{valore:,.0f} {unita}"
            story.append(Paragraph(f"Valore: {valore_str}", styles['Normal']))
            if som.get('fonte'):
                story.append(Paragraph(f"Fonte: {som.get('fonte')} ({som.get('anno', 'N/A')})", styles['Normal']))
            if som.get('descrizione'):
                story.extend(markdown_to_paragraphs(som.get('descrizione', ''), styles))
            story.append(Spacer(1, 0.3*cm))
        
        story.append(PageBreak())
    
    # Competitor Analysis
    competitor_analysis = market_analysis_json.get('competitor_analysis', {})
    if competitor_analysis:
        story.append(Paragraph("ANALISI COMPETITOR", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        competitor_principali = competitor_analysis.get('competitor_principali', [])
        for competitor in competitor_principali:
            story.append(Paragraph(f"<b>{competitor.get('nome', '')}</b> ({competitor.get('tipo', '')})", styles['Heading3']))
            if competitor.get('fatturato_stimato'):
                story.append(Paragraph(f"Fatturato stimato: {competitor.get('fatturato_stimato')}", styles['Normal']))
            if competitor.get('quote_mercato'):
                story.append(Paragraph(f"Quota di mercato: {competitor.get('quote_mercato')}", styles['Normal']))
            if competitor.get('posizionamento'):
                story.append(Paragraph(f"Posizionamento: {competitor.get('posizionamento')}", styles['Normal']))
            
            if competitor.get('punti_forza'):
                story.append(Paragraph("<b>Punti di Forza:</b>", styles['Normal']))
                for pf in competitor.get('punti_forza', []):
                    story.append(Paragraph(f"• {pf}", styles['Normal']))
            
            if competitor.get('punti_debolezza'):
                story.append(Paragraph("<b>Punti di Debolezza:</b>", styles['Normal']))
                for pd in competitor.get('punti_debolezza', []):
                    story.append(Paragraph(f"• {pd}", styles['Normal']))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(PageBreak())
    
    # Trends & Opportunities
    trends_opp = market_analysis_json.get('trends_opportunities', {})
    if trends_opp:
        story.append(Paragraph("TREND E OPPORTUNITÀ", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        trend_emergenti = trends_opp.get('trend_emergenti', [])
        if trend_emergenti:
            story.append(Paragraph("<b>Trend Emergenti:</b>", styles['Heading3']))
            for trend in trend_emergenti:
                story.append(Paragraph(f"<b>{trend.get('titolo', '')}</b> (Impatto: {trend.get('impatto', '')})", styles['Normal']))
                if trend.get('descrizione'):
                    story.extend(markdown_to_paragraphs(trend.get('descrizione', ''), styles))
                if trend.get('fonte'):
                    story.append(Paragraph(f"<i>Fonte: {trend.get('fonte')}</i>", styles['Normal']))
                story.append(Spacer(1, 0.2*cm))
        
        opportunita = trends_opp.get('opportunita', [])
        if opportunita:
            story.append(Paragraph("<b>Opportunità di Mercato:</b>", styles['Heading3']))
            for opp in opportunita:
                story.append(Paragraph(f"<b>{opp.get('titolo', '')}</b> (Potenziale: {opp.get('potenziale', '')})", styles['Normal']))
                if opp.get('descrizione'):
                    story.extend(markdown_to_paragraphs(opp.get('descrizione', ''), styles))
                story.append(Spacer(1, 0.2*cm))
        
        story.append(PageBreak())
    
    # SWOT Analysis
    swot = market_analysis_json.get('swot_analysis', {})
    if swot:
        story.append(Paragraph("ANALISI SWOT", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        # Strengths
        if swot.get('strengths'):
            story.append(Paragraph("<b>Punti di Forza:</b>", styles['Heading3']))
            for s in swot.get('strengths', []):
                story.append(Paragraph(f"<b>{s.get('titolo', '')}</b>", styles['Normal']))
                if s.get('descrizione'):
                    story.extend(markdown_to_paragraphs(s.get('descrizione', ''), styles))
                story.append(Spacer(1, 0.2*cm))
        
        # Weaknesses
        if swot.get('weaknesses'):
            story.append(Paragraph("<b>Debolezze:</b>", styles['Heading3']))
            for w in swot.get('weaknesses', []):
                story.append(Paragraph(f"<b>{w.get('titolo', '')}</b> (Impatto: {w.get('impatto', '')})", styles['Normal']))
                if w.get('descrizione'):
                    story.extend(markdown_to_paragraphs(w.get('descrizione', ''), styles))
                story.append(Spacer(1, 0.2*cm))
        
        # Opportunities
        if swot.get('opportunities'):
            story.append(Paragraph("<b>Opportunità:</b>", styles['Heading3']))
            for o in swot.get('opportunities', []):
                story.append(Paragraph(f"<b>{o.get('titolo', '')}</b> (Potenziale: {o.get('potenziale', '')})", styles['Normal']))
                if o.get('descrizione'):
                    story.extend(markdown_to_paragraphs(o.get('descrizione', ''), styles))
                if o.get('fonte'):
                    story.append(Paragraph(f"<i>Fonte: {o.get('fonte')}</i>", styles['Normal']))
                story.append(Spacer(1, 0.2*cm))
        
        # Threats
        if swot.get('threats'):
            story.append(Paragraph("<b>Minacce:</b>", styles['Heading3']))
            for t in swot.get('threats', []):
                story.append(Paragraph(f"<b>{t.get('titolo', '')}</b> (Probabilità: {t.get('probabilita', '')}, Impatto: {t.get('impatto', '')})", styles['Normal']))
                if t.get('descrizione'):
                    story.extend(markdown_to_paragraphs(t.get('descrizione', ''), styles))
                story.append(Spacer(1, 0.2*cm))
        
        story.append(PageBreak())
    
    # Positioning Strategy
    positioning = market_analysis_json.get('positioning_strategy', {})
    if positioning:
        story.append(Paragraph("STRATEGIA DI POSIZIONAMENTO", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        if positioning.get('posizionamento_raccomandato'):
            story.append(Paragraph("<b>Posizionamento Raccomandato:</b>", styles['Heading3']))
            story.extend(markdown_to_paragraphs(positioning.get('posizionamento_raccomandato', ''), styles))
        
        nicchie = positioning.get('nicchie_mercato', [])
        if nicchie:
            story.append(Paragraph("<b>Nicchie di Mercato:</b>", styles['Heading3']))
            for nicchia in nicchie:
                story.append(Paragraph(f"<b>{nicchia.get('nicchia', '')}</b> (Potenziale: {nicchia.get('potenziale', '')})", styles['Normal']))
                if nicchia.get('descrizione'):
                    story.extend(markdown_to_paragraphs(nicchia.get('descrizione', ''), styles))
                story.append(Spacer(1, 0.2*cm))
        
        story.append(PageBreak())
    
    # Charts
    charts = market_analysis_json.get('charts', [])
    if charts:
        story.append(Paragraph("GRAFICI", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        for chart in charts:
            try:
                chart_img = create_chart_image(chart, width=15*cm, height=10*cm)
                img = Image(chart_img, width=15*cm, height=10*cm)
                story.append(img)
                story.append(Spacer(1, 0.3*cm))
                
                if chart.get('caption'):
                    caption_clean = chart.get('caption', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"<i>{caption_clean}</i>", styles['Normal']))
                    story.append(Spacer(1, 0.3*cm))
            except Exception as e:
                print(f"⚠️  Errore nel generare il grafico {chart.get('id', 'unknown')}: {str(e)}")
        
        story.append(PageBreak())
    
    # Sources
    sources = market_analysis_json.get('sources', [])
    if sources:
        story.append(Paragraph("FONTI", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        for source in sources:
            source_text = f"<b>{source.get('titolo', '')}</b> ({source.get('tipo', '')})"
            if source.get('data_accesso'):
                source_text += f" - Accesso: {source.get('data_accesso')}"
            story.append(Paragraph(source_text, styles['Normal']))
            story.append(Spacer(1, 0.2*cm))
    
    # Assumptions
    assumptions = market_analysis_json.get('assumptions', [])
    if assumptions:
        story.append(PageBreak())
        story.append(Paragraph("ASSUNZIONI", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        for ass in assumptions:
            ass_clean = ass.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"• {ass_clean}", styles['Normal']))
            story.append(Spacer(1, 0.2*cm))
    
    # Pagina di firma/approvazione
    story.append(PageBreak())
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("APPROVAZIONE E FIRMA", styles['CustomHeading1']))
    story.append(Spacer(1, 1*cm))
    
    data_gen = meta.get('data_generazione', datetime.now().strftime('%d/%m/%Y'))
    firma_text = f"""
    Il presente documento di Analisi di Mercato è stato redatto in data {data_gen} e approvato da:
    """
    story.append(Paragraph(firma_text, styles['Normal']))
    story.append(Spacer(1, 2*cm))
    
    # Tabella firme
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
    Questa Analisi di Mercato è stata redatta con cura e attenzione ai dettagli.<br/><br/>
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
        [f"<b>Data generazione:</b> {data_gen}"]
    ]
    if settore:
        final_info.append([f"<b>Settore:</b> {settore}"])
    if area_geografica:
        final_info.append([f"<b>Area Geografica:</b> {area_geografica}"])
    
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
    print(f"✓ PDF analisi di mercato generato con successo: {output_path}")
    
    return str(output_path)
