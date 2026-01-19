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
from pdf_generator import markdown_to_paragraphs, create_chart_image, create_numbered_canvas, escape_for_pdf


async def create_pdf_from_validation(validation_json: dict) -> str:
    """Crea il PDF professionale dalla validazione idea"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "validazione-idea.pdf"
    
    # Estrai informazioni per header/footer
    header_info = {'left': '', 'right': ''}
    footer_info = {'left': '', 'center': 'Validazione Idea di Business', 'right': ''}
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
    
    # Modifica lo stile Normal esistente
    styles['Normal'].fontName = 'Times-Roman'
    styles['Normal'].fontSize = 11
    styles['Normal'].textColor = colors.HexColor('#000000')
    styles['Normal'].leading = 14
    styles['Normal'].alignment = TA_JUSTIFY
    
    # Story (contenuto del PDF)
    story = []
    
    # === COPERTINA PROFESSIONALE COLORATA ===
    score = validation_json.get('scoreComplessivo', 0)
    verdict = validation_json.get('verdetto', 'DA MIGLIORARE')
    data_gen = datetime.now().strftime('%d/%m/%Y alle %H:%M')
    
    # Colori professionali per la validazione (blu per validazione)
    primary_color = colors.HexColor('#1e40af')  # Blu scuro professionale
    accent_color = colors.HexColor('#3b82f6')   # Blu medio
    light_bg = colors.HexColor('#eff6ff')       # Sfondo chiaro blu
    
    # Determina il colore del verdetto
    if verdict == 'VALIDATA':
        verdict_color = colors.HexColor('#10b981')  # Verde
    elif verdict == 'DA MIGLIORARE':
        verdict_color = colors.HexColor('#f59e0b')  # Arancione
    else:
        verdict_color = colors.HexColor('#ef4444')  # Rosso
    
    # Box colorato superiore
    cover_header = Table([
        ['']
    ], colWidths=[A4[0] - 4*cm], rowHeights=[3*cm])
    cover_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cover_header)
    
    # Spazio e contenuto principale
    story.append(Spacer(1, 2*cm))
    
    # Titolo principale
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
    story.append(Paragraph("Validazione Idea di Business", title_style))
    
    # Linea decorativa sotto il titolo
    decor_line = Table([['']], colWidths=[8*cm], rowHeights=[0.2*cm])
    decor_line.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(decor_line)
    
    story.append(Spacer(1, 1.5*cm))
    
    # Score complessivo grande
    score_style = ParagraphStyle(
        name='ScoreStyle',
        parent=styles['CoverTitle'],
        fontName='Times-Bold',
        fontSize=72,
        textColor=verdict_color,
        spaceAfter=10,
        alignment=TA_CENTER,
        leading=80
    )
    story.append(Paragraph(f"{score}/100", score_style))
    
    # Verdetto
    verdict_style = ParagraphStyle(
        name='VerdictStyle',
        parent=styles['CoverSubtitle'],
        fontName='Times-Bold',
        fontSize=24,
        textColor=verdict_color,
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=28
    )
    story.append(Paragraph(verdict, verdict_style))
    
    story.append(Spacer(1, 2*cm))
    
    # Box informativo con sfondo colorato
    info_data = []
    info_data.append([Paragraph(f"<b>Data:</b> {escape_for_pdf(data_gen)}", styles['Normal'])])
    info_data.append([Paragraph(f"<b>Score Complessivo:</b> {score}/100", styles['Normal'])])
    info_data.append([Paragraph(f"<b>Verdetto:</b> {escape_for_pdf(verdict)}", styles['Normal'])])
    
    info_table = Table(info_data, colWidths=[12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 24),
        ('RIGHTPADDING', (0, 0), (-1, -1), 24),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    story.append(info_table)
    
    story.append(PageBreak())
    
    # === INDICE ===
    story.append(Paragraph("INDICE", styles['CustomTitle']))
    story.append(Spacer(1, 0.5*cm))
    
    toc_entries = []
    page_num = 3
    
    if validation_json.get('executiveSummary'):
        toc_entries.append(("Executive Summary", page_num))
        page_num += 1
    
    toc_entries.append(("Analisi del Problema", page_num))
    page_num += 1
    
    toc_entries.append(("Analisi della Soluzione", page_num))
    page_num += 1
    
    toc_entries.append(("Analisi del Mercato", page_num))
    page_num += 1
    
    toc_entries.append(("Analisi della Competitività", page_num))
    page_num += 1
    
    toc_entries.append(("Analisi del Modello di Business", page_num))
    page_num += 1
    
    if validation_json.get('puntiForza'):
        toc_entries.append(("Punti di Forza", page_num))
        page_num += 1
    
    if validation_json.get('puntiDebolezza'):
        toc_entries.append(("Punti di Debolezza", page_num))
        page_num += 1
    
    if validation_json.get('raccomandazioni'):
        toc_entries.append(("Raccomandazioni", page_num))
        page_num += 1
    
    toc_entries.append(("Verdetto Finale", page_num))
    
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
    exec_summary = validation_json.get('executiveSummary', '')
    if exec_summary:
        story.append(Paragraph("EXECUTIVE SUMMARY", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        story.extend(markdown_to_paragraphs(exec_summary, styles))
        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())
    
    # Analisi del Problema
    analisi_problema = validation_json.get('analisiProblema', {})
    if analisi_problema:
        story.append(Paragraph("ANALISI DEL PROBLEMA", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        score_problema = analisi_problema.get('score', 0)
        valutazione = analisi_problema.get('valutazione', '')
        
        # Box con score
        score_color_hex = '#10b981' if score_problema >= 7 else '#f59e0b' if score_problema >= 5 else '#ef4444'
        score_text = Paragraph(f"<b><font size=24 color='{score_color_hex}'>Score: {score_problema}/10</font></b>", styles['Normal'])
        story.append(score_text)
        story.append(Spacer(1, 0.5*cm))
        
        if valutazione:
            story.extend(markdown_to_paragraphs(valutazione, styles))
        
        story.append(PageBreak())
    
    # Analisi della Soluzione
    analisi_soluzione = validation_json.get('analisiSoluzione', {})
    if analisi_soluzione:
        story.append(Paragraph("ANALISI DELLA SOLUZIONE", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        score_soluzione = analisi_soluzione.get('score', 0)
        valutazione = analisi_soluzione.get('valutazione', '')
        
        # Box con score
        score_color_hex = '#10b981' if score_soluzione >= 7 else '#f59e0b' if score_soluzione >= 5 else '#ef4444'
        score_text = Paragraph(f"<b><font size=24 color='{score_color_hex}'>Score: {score_soluzione}/10</font></b>", styles['Normal'])
        story.append(score_text)
        story.append(Spacer(1, 0.5*cm))
        
        if valutazione:
            story.extend(markdown_to_paragraphs(valutazione, styles))
        
        story.append(PageBreak())
    
    # Analisi del Mercato
    analisi_mercato = validation_json.get('analisiMercato', {})
    if analisi_mercato:
        story.append(Paragraph("ANALISI DEL MERCATO", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        score_mercato = analisi_mercato.get('score', 0)
        valutazione = analisi_mercato.get('valutazione', '')
        
        # Box con score
        score_color_hex = '#10b981' if score_mercato >= 7 else '#f59e0b' if score_mercato >= 5 else '#ef4444'
        score_text = Paragraph(f"<b><font size=24 color='{score_color_hex}'>Score: {score_mercato}/10</font></b>", styles['Normal'])
        story.append(score_text)
        story.append(Spacer(1, 0.5*cm))
        
        if valutazione:
            story.extend(markdown_to_paragraphs(valutazione, styles))
        
        story.append(PageBreak())
    
    # Analisi della Competitività
    analisi_competitivita = validation_json.get('analisiCompetitivita', {})
    if analisi_competitivita:
        story.append(Paragraph("ANALISI DELLA COMPETITIVITÀ", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        score_competitivita = analisi_competitivita.get('score', 0)
        valutazione = analisi_competitivita.get('valutazione', '')
        
        # Box con score
        score_color_hex = '#10b981' if score_competitivita >= 7 else '#f59e0b' if score_competitivita >= 5 else '#ef4444'
        score_text = Paragraph(f"<b><font size=24 color='{score_color_hex}'>Score: {score_competitivita}/10</font></b>", styles['Normal'])
        story.append(score_text)
        story.append(Spacer(1, 0.5*cm))
        
        if valutazione:
            story.extend(markdown_to_paragraphs(valutazione, styles))
        
        story.append(PageBreak())
    
    # Analisi del Modello di Business
    analisi_modello = validation_json.get('analisiModelloBusiness', {})
    if analisi_modello:
        story.append(Paragraph("ANALISI DEL MODELLO DI BUSINESS", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        score_modello = analisi_modello.get('score', 0)
        valutazione = analisi_modello.get('valutazione', '')
        
        # Box con score
        score_color_hex = '#10b981' if score_modello >= 7 else '#f59e0b' if score_modello >= 5 else '#ef4444'
        score_text = Paragraph(f"<b><font size=24 color='{score_color_hex}'>Score: {score_modello}/10</font></b>", styles['Normal'])
        story.append(score_text)
        story.append(Spacer(1, 0.5*cm))
        
        if valutazione:
            story.extend(markdown_to_paragraphs(valutazione, styles))
        
        story.append(PageBreak())
    
    # Punti di Forza
    punti_forza = validation_json.get('puntiForza', [])
    if punti_forza:
        story.append(Paragraph("PUNTI DI FORZA", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        for i, punto in enumerate(punti_forza, 1):
            story.append(Paragraph(f"<b>{i}. Punto di Forza</b>", styles['Heading3']))
            story.extend(markdown_to_paragraphs(punto, styles))
            story.append(Spacer(1, 0.3*cm))
        
        story.append(PageBreak())
    
    # Punti di Debolezza
    punti_debolezza = validation_json.get('puntiDebolezza', [])
    if punti_debolezza:
        story.append(Paragraph("PUNTI DI DEBOLEZZA", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        for i, punto in enumerate(punti_debolezza, 1):
            story.append(Paragraph(f"<b>{i}. Punto di Debolezza</b>", styles['Heading3']))
            story.extend(markdown_to_paragraphs(punto, styles))
            story.append(Spacer(1, 0.3*cm))
        
        story.append(PageBreak())
    
    # Raccomandazioni
    raccomandazioni = validation_json.get('raccomandazioni', [])
    if raccomandazioni:
        story.append(Paragraph("RACCOMANDAZIONI", styles['CustomHeading1']))
        story.append(Spacer(1, 0.3*cm))
        
        for i, racc in enumerate(raccomandazioni, 1):
            story.append(Paragraph(f"<b>Raccomandazione {i}</b>", styles['Heading3']))
            story.extend(markdown_to_paragraphs(racc, styles))
            story.append(Spacer(1, 0.3*cm))
        
        story.append(PageBreak())
    
    # Verdetto Finale
    story.append(Paragraph("VERDETTO FINALE", styles['CustomHeading1']))
    story.append(Spacer(1, 0.5*cm))
    
    # Box con verdetto e score
    verdict_color_hex = '#10b981' if verdict == 'VALIDATA' else '#f59e0b' if verdict == 'DA MIGLIORARE' else '#ef4444'
    verdict_box_data = [
        [Paragraph(f"<b><font size=36 color='{verdict_color_hex}'>{verdict}</font></b>", styles['Normal'])],
        [Paragraph(f"<b><font size=24>Score Complessivo: {score}/100</font></b>", styles['Normal'])]
    ]
    verdict_box = Table(verdict_box_data, colWidths=[16*cm])
    verdict_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 30),
        ('RIGHTPADDING', (0, 0), (-1, -1), 30),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor(verdict_color_hex)),
    ]))
    story.append(verdict_box)
    
    story.append(Spacer(1, 0.5*cm))
    
    # Spiegazione del verdetto
    spiegazione = validation_json.get('spiegazioneVerdetto', '')
    if spiegazione:
        story.append(Paragraph("<b>Spiegazione del Verdetto</b>", styles['Heading3']))
        story.extend(markdown_to_paragraphs(spiegazione, styles))
    
    story.append(PageBreak())
    
    # Pagina di chiusura
    closing_header = Table([['']], colWidths=[A4[0] - 4*cm], rowHeights=[2*cm])
    closing_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(closing_header)
    
    story.append(Spacer(1, 3*cm))
    
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
    
    closing_message = """
    Questa Validazione Idea di Business è stata redatta con cura e attenzione ai dettagli.<br/><br/>
    Per ulteriori informazioni o chiarimenti, non esitate a contattarci.<br/><br/>
    <i>Documento generato con SeedWise</i>
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
    
    # Genera il PDF
    doc.build(story)
    print(f"✓ PDF validazione idea generato con successo: {output_path}")
    
    return str(output_path)
