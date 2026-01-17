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
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pdf_generator import markdown_to_paragraphs, create_chart_image

async def create_pdf_from_market_analysis(market_analysis_json: dict) -> str:
    """Crea il PDF professionale dall'analisi di mercato"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "analisi-mercato.pdf"
    
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
    meta = market_analysis_json.get('meta', {})
    titolo = f"Analisi di Mercato {meta.get('tipo_analisi', '').upper() if meta.get('tipo_analisi') == 'deep' else ''}"
    settore = meta.get('settore', '')
    area_geografica = meta.get('area_geografica', '')
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(titolo, styles['CustomTitle']))
    if settore:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(settore, styles['Heading2']))
    if area_geografica:
        story.append(Paragraph(f"Area: {area_geografica}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Data generazione
    data_gen = meta.get('data_generazione', datetime.now().strftime('%d/%m/%Y'))
    story.append(Paragraph(f"<i>Generato il: {data_gen}</i>", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
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
    
    # Genera il PDF
    doc.build(story)
    print(f"✓ PDF analisi di mercato generato con successo: {output_path}")
    
    return str(output_path)
