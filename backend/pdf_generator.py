import json
import re
import io
import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Backend non interattivo per server
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import markdown
from markdown.extensions import fenced_code, tables, nl2br

# Configura encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def escape_for_pdf(s):
    """Escape caratteri speciali per uso in Paragraph/HTML di ReportLab, preservando UTF-8."""
    if s is None:
        return ''
    # Assicura che la stringa sia in UTF-8
    if isinstance(s, bytes):
        s = s.decode('utf-8', errors='replace')
    s = str(s)
    # Escape solo caratteri HTML speciali, mantieni tutti gli altri caratteri UTF-8
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def preprocess_content_for_pdf(content):
    """Preprocessa e normalizza il contenuto markdown prima della generazione PDF"""
    if not content:
        return ""
    
    # Normalizza newline (gestisce Windows, Unix, Mac)
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Rimuovi spazi eccessivi ma mantieni struttura markdown
    # NON sostituire spazi multipli in una riga, solo normalizza
    content = re.sub(r'[ \t]{2,}', ' ', content)  # Spazi multipli -> singolo spazio
    
    # Normalizza newline multiple (mantieni max 2 consecutive)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Assicurati che i titoli inizino con # (rimuovi spazi prima)
    content = re.sub(r'^[ \t]+(#+)', r'\1', content, flags=re.MULTILINE)
    
    # Normalizza spazi dopo # - gestisce vari casi:
    # ##Titolo -> ## Titolo
    # ## Titolo -> ## Titolo (già corretto)
    # ##  Titolo -> ## Titolo (rimuovi spazi multipli)
    content = re.sub(r'^(#+)[ \t]+([^#\s])', r'\1 \2', content, flags=re.MULTILINE)
    content = re.sub(r'^(#+)([^#\s])', r'\1 \2', content, flags=re.MULTILINE)
    
    # Rimuovi spazi alla fine delle righe
    content = re.sub(r'[ \t]+\n', '\n', content)
    
    return content.strip()


def markdown_to_paragraphs(text, styles):
    """Converte markdown in paragrafi ReportLab usando libreria markdown standard"""
    elements = []
    
    if not text:
        return elements
    
    # Normalizza il testo prima del parsing
    text = preprocess_content_for_pdf(text)
    
    # PRIMA: Identifica righe completamente in maiuscolo come titoli
    # Processa riga per riga per identificare titoli in maiuscolo
    lines = text.split('\n')
    processed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            processed_lines.append('')
            i += 1
            continue
        
        # Controlla se la riga è completamente in maiuscolo (titolo)
        # Pattern: righe come "PUNTO CHIAVE 1", "ANALISI DEL MERCATO", "SEZIONE 2", etc.
        # Deve avere almeno 3 caratteri e essere principalmente maiuscolo
        # Esclude righe che iniziano con # (già markdown), sono troppo corte, o sono solo numeri/punteggiatura
        if len(line) >= 3 and not line.startswith('#'):
            # Rimuovi spazi e punteggiatura per analisi
            text_only = ''.join([c for c in line if c.isalnum() or c.isspace()])
            
            if len(text_only) >= 3:
                # Conta caratteri alfabetici maiuscoli vs totali alfabetici
                alpha_chars = [c for c in line if c.isalpha()]
                upper_chars = [c for c in line if c.isupper() and c.isalpha()]
                
                # Se ci sono caratteri alfabetici
                if len(alpha_chars) >= 3:
                    upper_ratio = len(upper_chars) / len(alpha_chars) if alpha_chars else 0
                    
                    # Se almeno l'80% dei caratteri alfabetici è maiuscolo
                    # E la riga non è solo numeri/punteggiatura
                    if upper_ratio >= 0.8:
                        # Sezioni che devono essere trattate come sottoparagrafi (H3)
                        # invece di titoli principali (H2)
                        sottoparagrafi_keywords = [
                            'PUNTI CHIAVE',
                            'PUNTO CHIAVE',
                            'PIANO OPERATIVO',
                            'ROADMAP',
                            'PIANO OPERATIVO E ROADMAP',
                            'ANALISI DEI RISCHI',
                            'ANALISI RISCHI'
                        ]
                        
                        # Normalizza la riga per il confronto (rimuovi spazi extra, punteggiatura)
                        line_normalized = ' '.join(line.split()).upper()
                        
                        # Controlla se contiene una delle keyword dei sottoparagrafi
                        is_sottoparagrafo = any(keyword in line_normalized for keyword in sottoparagrafi_keywords)
                        
                        if is_sottoparagrafo:
                            # Tratta come sottoparagrafo: aggiungi markdown H3
                            print(f"✅ Riconosciuto sottoparagrafo in maiuscolo: '{line}'")
                            processed_lines.append(f'### {line}')
                        else:
                            # Pattern comuni per titoli in maiuscolo:
                            # - "ANALISI DEL MERCATO"
                            # - "SEZIONE 1", "SEZIONE 2"
                            # - "CONCLUSIONI"
                            # Tratta come titolo: aggiungi markdown H2
                            print(f"✅ Riconosciuto titolo in maiuscolo: '{line}'")
                            processed_lines.append(f'## {line}')
                        i += 1
                        continue
        
        # Altrimenti mantieni la riga originale
        processed_lines.append(lines[i])
        i += 1
    
    # Ricostruisci il testo con i titoli in maiuscolo convertiti
    text = '\n'.join(processed_lines)
    
    # Configura markdown con estensioni utili
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'nl2br'])
    
    # Converti markdown in HTML
    html = md.convert(text)
    
    # Funzione per convertire tag HTML in formato ReportLab con supporto UTF-8
    def clean_html_for_reportlab(html_text):
        """Converte HTML in formato compatibile con ReportLab Paragraph, preservando UTF-8"""
        if not html_text:
            return ""
        # Assicura encoding UTF-8
        if isinstance(html_text, bytes):
            html_text = html_text.decode('utf-8', errors='replace')
        html_text = str(html_text)
        # ReportLab supporta: <b>, <i>, <u>, <font>, <br/>, <a>, <sup>, <sub>
        html_text = re.sub(r'<strong>(.+?)</strong>', r'<b>\1</b>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<em>(.+?)</em>', r'<i>\1</i>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<code>(.+?)</code>', r'<font name="Courier">\1</font>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<pre>(.+?)</pre>', r'<font name="Courier">\1</font>', html_text, flags=re.DOTALL)
        # Rimuovi tag non supportati
        html_text = re.sub(r'</?div[^>]*>', '', html_text)
        html_text = re.sub(r'</?span[^>]*>', '', html_text)
        return html_text.strip()
    
    # Processa l'HTML sequenzialmente mantenendo l'ordine
    # Dividi per blocchi HTML principali
    parts = []
    current_pos = 0
    
    # Trova tutti i tag principali nell'ordine
    for match in re.finditer(r'<(h[1-6]|p|ul|ol|li)>(.+?)</\1>', html, re.DOTALL):
        # Aggiungi testo prima del match come paragrafo se presente
        before = html[current_pos:match.start()].strip()
        if before:
            parts.append(('text', before))
        
        tag_type = match.group(1)
        content = match.group(2)
        
        if tag_type.startswith('h'):
            level = int(tag_type[1])
            parts.append(('heading', level, content))
        elif tag_type in ('ul', 'ol'):
            # Processa lista
            items = re.findall(r'<li>(.+?)</li>', content, re.DOTALL)
            for idx, item in enumerate(items, 1):
                parts.append(('list_item', tag_type == 'ol', item))
        elif tag_type == 'li':
            parts.append(('list_item', False, content))
        elif tag_type == 'p':
            parts.append(('paragraph', content))
        
        current_pos = match.end()
    
    # Aggiungi testo rimanente
    remaining = html[current_pos:].strip()
    if remaining:
        parts.append(('text', remaining))
    
    # Se non abbiamo trovato tag, processa tutto come testo
    if not parts:
        parts = [('text', html)]
    
    # Converti in elementi ReportLab
    for part in parts:
        part_type = part[0]
        
        if part_type == 'heading':
            level, content = part[1], part[2]
            content_html = clean_html_for_reportlab(content)
            if level == 1:
                elements.append(Paragraph(content_html, styles['CustomHeading1']))
                elements.append(Spacer(1, 0.4*cm))
            elif level == 2:
                elements.append(Paragraph(content_html, styles['CustomHeading2']))
                elements.append(Spacer(1, 0.3*cm))
            else:
                elements.append(Paragraph(content_html, styles['Heading3']))
                elements.append(Spacer(1, 0.2*cm))
        
        elif part_type == 'list_item':
            is_ordered, content = part[1], part[2]
            content_html = clean_html_for_reportlab(content)
            # Per liste ordinate, usa un contatore (semplificato)
            if is_ordered:
                # Non possiamo sapere il numero esatto senza contesto, usiamo bullet
                elements.append(Paragraph(f"• {content_html}", styles['Normal']))
            else:
                elements.append(Paragraph(f"• {content_html}", styles['Normal']))
            elements.append(Spacer(1, 0.15*cm))
        
        elif part_type == 'paragraph':
            content = part[1]
            content_html = clean_html_for_reportlab(content)
            if content_html:
                elements.append(Paragraph(content_html, styles['Normal']))
                elements.append(Spacer(1, 0.3*cm))
        
        elif part_type == 'text':
            content = part[1]
            # Rimuovi tag <p> se presenti
            content = re.sub(r'</?p[^>]*>', '', content)
            content_html = clean_html_for_reportlab(content)
            if content_html:
                elements.append(Paragraph(content_html, styles['Normal']))
                elements.append(Spacer(1, 0.3*cm))
    
    return elements

def create_chart_image(chart_data, width=15*cm, height=10*cm):
    """Crea un grafico professionale con stile aziendale e alta qualità"""
    try:
        chart_id = chart_data.get('id', 'N/A')
        tipo = chart_data.get('tipo', 'line')
        titolo = chart_data.get('titolo', '')
        x_label = chart_data.get('x_label', '')
        y_label = chart_data.get('y_label', '')
        series = chart_data.get('series', [])
        
        
        # Validazione dati in ingresso
        if not series:
            print(f"⚠️  Grafico '{titolo}' (ID: {chart_id}) non ha serie di dati")
            return None
        
        if tipo not in ['line', 'bar', 'pie']:
            print(f"⚠️  Tipo grafico non valido: {tipo} per grafico {chart_id}")
            return None
        
        print(f"   📊 Creando grafico {chart_id}: tipo={tipo}, serie={len(series)}")
        
        # Configurazione stile professionale con supporto UTF-8
        # Trova un font che supporta caratteri italiani
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        italian_font = None
        for font_name in ['DejaVu Sans', 'Liberation Sans', 'Arial', 'Helvetica', 'Verdana']:
            if font_name in available_fonts:
                italian_font = font_name
                break
        
        if not italian_font:
            italian_font = 'sans-serif'
        
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.edgecolor': '#333333',
            'axes.linewidth': 1.2,
            'axes.grid': True,
            'axes.grid.alpha': 0.3,
            'axes.grid.color': '#E0E0E0',
            'axes.labelcolor': '#333333',
            'axes.labelsize': 11,
            'axes.titlesize': 13,
            'axes.titleweight': 'bold',
            'xtick.color': '#333333',
            'ytick.color': '#333333',
            'text.color': '#333333',
            'font.family': 'sans-serif',
            'font.sans-serif': [italian_font, 'DejaVu Sans', 'Liberation Sans', 'Arial', 'Helvetica'],
            'font.size': 10,
            'legend.frameon': True,
            'legend.framealpha': 0.9,
            'legend.facecolor': 'white',
            'legend.edgecolor': '#CCCCCC',
            'legend.fontsize': 9,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1
        })
        
        # Imposta encoding UTF-8 per matplotlib
        plt.rcParams['axes.unicode_minus'] = False
        
        # Palette colori professionale (blu/grigio aziendale)
        professional_colors = [
        '#1e3a8a',  # Blu scuro
        '#3b82f6',  # Blu medio
        '#10b981',  # Verde
        '#f59e0b',  # Arancione
        '#8b5cf6',  # Viola
        '#ef4444',  # Rosso
        '#64748b',  # Grigio
            '#06b6d4',  # Ciano
        ]
        
        # Crea figura con dimensioni precise
        fig, ax = plt.subplots(figsize=(width/cm, height/cm), 
                              facecolor='white',
                              edgecolor='none')
        
        # Rimuovi bordi superflui per aspetto più pulito
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')
        
        if tipo == 'line':
            for idx, serie in enumerate(series):
                name = serie.get('name', f'Serie {idx+1}')
                points = serie.get('points', [])
                # Filtra punti validi (con x non vuoto e y valido)
                valid_points = [(p.get('x', ''), p.get('y')) for p in points 
                               if p.get('x') and str(p.get('x', '')).strip() != '' 
                               and p.get('y') is not None]
                x_values = [str(x) for x, y in valid_points]
                y_values = [float(y) for x, y in valid_points]
                
                if x_values and y_values and len(x_values) == len(y_values):
                    color = professional_colors[idx % len(professional_colors)]
                    # Assicura che il nome della serie sia UTF-8
                    label_name = str(name)
                    if isinstance(name, bytes):
                        label_name = name.decode('utf-8', errors='replace')
                    ax.plot(x_values, y_values, 
                           marker='o', 
                           label=label_name,
                           color=color,
                           linewidth=2.5,
                           markersize=7,
                           markerfacecolor=color,
                           markeredgecolor='white',
                           markeredgewidth=1.5,
                           alpha=0.9)
            
            ax.legend(loc='best', frameon=True, fancybox=True, shadow=False)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
            ax.set_axisbelow(True)
            
        elif tipo == 'bar':
            # Raccogli dati da tutte le serie per grafico a barre raggruppate
            # Gestisce anche il caso in cui ogni serie ha lo stesso valore x (come scenari)
            x_values = []
            y_data = {}
            
            for idx, serie in enumerate(series):
                name = serie.get('name', f'Serie {idx+1}')
                points = serie.get('points', [])
                
                # Se tutti i punti hanno lo stesso x, usa il primo valore y (caso scenari)
                unique_x_values = set()
                for p in points:
                    x_val = str(p.get('x', '')).strip()
                    if x_val and x_val != '':
                        unique_x_values.add(x_val)
                
                # Se c'è un solo valore x unico per questa serie, prendi il primo y
                if len(unique_x_values) == 1:
                    x_val = list(unique_x_values)[0]
                    # Prendi il primo valore y valido
                    for p in points:
                        y_val = p.get('y')
                        if y_val is not None:
                            try:
                                y_val = float(y_val)
                                if x_val not in x_values:
                                    x_values.append(x_val)
                                if name not in y_data:
                                    y_data[name] = {}
                                y_data[name][x_val] = y_val
                                break  # Prendi solo il primo valore
                            except (ValueError, TypeError):
                                continue
                else:
                    # Caso normale: più valori x diversi
                    for p in points:
                        x_val = str(p.get('x', '')).strip()
                        y_val = p.get('y')
                        if y_val is not None:
                            try:
                                y_val = float(y_val)
                                # Ignora punti con x vuoto o solo spazi
                                if x_val and x_val != '':
                                    if x_val not in x_values:
                                        x_values.append(x_val)
                                    if name not in y_data:
                                        y_data[name] = {}
                                    # Se ci sono più valori per lo stesso x, prendi l'ultimo (o potresti fare la media)
                                    y_data[name][x_val] = y_val
                            except (ValueError, TypeError):
                                continue
            
            # Crea grafico a barre raggruppate
            if x_values and y_data:
                x_pos = range(len(x_values))
                num_series = len(y_data)
                bar_width = 0.8 / max(num_series, 1)  # Adatta la larghezza in base al numero di serie
                offset = -bar_width * (num_series - 1) / 2
                
                for idx, (name, values) in enumerate(y_data.items()):
                    positions = [x + offset for x in x_pos]
                    heights = [values.get(x_val, 0) for x_val in x_values]
                    
                    color = professional_colors[idx % len(professional_colors)]
                    # Assicura che il nome della serie sia UTF-8
                    label_name = str(name)
                    if isinstance(name, bytes):
                        label_name = name.decode('utf-8', errors='replace')
                    ax.bar(positions, heights, 
                          width=bar_width,
                          label=label_name,
                          color=color,
                          alpha=0.85,
                          edgecolor='white',
                          linewidth=1.5)
                    offset += bar_width
                
                ax.set_xticks(x_pos)
                # Assicura che le etichette siano UTF-8
                x_labels_utf8 = [str(x) if not isinstance(x, bytes) else x.decode('utf-8', errors='replace') for x in x_values]
                ax.set_xticklabels(x_labels_utf8, rotation=45, ha='right')
                ax.legend(loc='best', frameon=True)
                ax.grid(True, alpha=0.3, axis='y', linestyle='--')
                ax.set_axisbelow(True)
            
        elif tipo == 'pie':
            # Prendi la prima serie per il pie chart
            if series:
                serie = series[0]
                points = serie.get('points', [])
                # Filtra punti validi
                valid_points = [(p.get('x', ''), p.get('y')) for p in points 
                               if p.get('x') and str(p.get('x', '')).strip() != '' 
                               and p.get('y') is not None and float(p.get('y', 0)) > 0]
                labels = [str(x) for x, y in valid_points]
                values = [float(y) for x, y in valid_points]
                
                if labels and values and len(labels) == len(values):
                    colors_pie = professional_colors[:len(labels)]
                    # Assicura che le etichette siano UTF-8
                    labels_utf8 = [str(l) if not isinstance(l, bytes) else l.decode('utf-8', errors='replace') for l in labels]
                    wedges, texts, autotexts = ax.pie(
                        values, 
                        labels=labels_utf8,
                        autopct='%1.1f%%',
                        colors=colors_pie,
                        startangle=90,
                        textprops={'fontsize': 10, 'fontweight': 'bold'},
                        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
                    )
                    # Migliora leggibilità percentuali
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
        
        # Verifica che ci siano dati da visualizzare
        has_data = False
        data_info = {}
        
        if tipo == 'line':
            # Per line chart, verifica che ci sia almeno una serie con punti validi
            has_data = False
            for serie in series:
                points = serie.get('points', [])
                valid_points = [p for p in points if p.get('x') and p.get('y') is not None]
                if len(valid_points) > 0:
                    has_data = True
                    break
            data_info = {
                'serie_count': len(series),
                'points_per_serie': [len(s.get('points', [])) for s in series]
            }
        elif tipo == 'bar':
            # Per bar chart, verifica che x_values e y_data siano stati definiti e non vuoti
            if 'x_values' in locals() and 'y_data' in locals():
                has_data = len(x_values) > 0 and len(y_data) > 0
                # Verifica anche che ci sia almeno un valore y non zero
                if has_data:
                    has_non_zero = False
                    for values_dict in y_data.values():
                        if any(v != 0 for v in values_dict.values()):
                            has_non_zero = True
                            break
                    has_data = has_non_zero
                data_info = {
                    'x_values_count': len(x_values),
                    'y_data_series': len(y_data),
                    'x_values': x_values[:3] if x_values else []
                }
            else:
                has_data = False
                data_info = {'error': 'x_values o y_data non definiti'}
        elif tipo == 'pie':
            # Per pie chart, verifica che labels e values siano stati definiti e non vuoti
            if 'labels' in locals() and 'values' in locals():
                has_data = len(labels) > 0 and len(values) > 0 and len(labels) == len(values)
                # Verifica anche che ci sia almeno un valore > 0
                if has_data:
                    has_data = any(v > 0 for v in values)
                data_info = {
                    'labels_count': len(labels),
                    'values_count': len(values)
                }
            else:
                has_data = False
                data_info = {'error': 'labels o values non definiti'}
        
        print(f"   🔍 Verifica dati: has_data={has_data}, info={data_info}")
        
        if not has_data:
            plt.close(fig)
            print(f"⚠️  Grafico '{titolo}' (ID: {chart_id}) non ha dati validi: {data_info}")
            return None
        
        # Titolo e labels (assicura encoding UTF-8)
        if titolo:
            # Assicura che il titolo sia una stringa UTF-8 valida
            if isinstance(titolo, bytes):
                titolo = titolo.decode('utf-8', errors='replace')
            ax.set_title(str(titolo), fontsize=14, fontweight='bold', 
                       pad=15, color='#1a1a1a')
        if x_label:
            if isinstance(x_label, bytes):
                x_label = x_label.decode('utf-8', errors='replace')
            ax.set_xlabel(str(x_label), fontsize=11, fontweight='medium', color='#333333')
        if y_label:
            if isinstance(y_label, bytes):
                y_label = y_label.decode('utf-8', errors='replace')
            ax.set_ylabel(str(y_label), fontsize=11, fontweight='medium', color='#333333')
        
        plt.tight_layout(pad=1.5)
        
        # Salva con alta qualità
        buf = io.BytesIO()
        try:
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', pad_inches=0.1)
            buf.seek(0)
            buf_size = len(buf.getvalue())
            if buf_size == 0:
                plt.close(fig)
                return None
            plt.close(fig)
            return buf
        except Exception as save_error:
            print(f"❌ Errore nel salvare il grafico {chart_id}: {str(save_error)}")
            plt.close(fig)
            return None
    except Exception as e:
        # Cattura qualsiasi errore durante la creazione del grafico
        chart_id = chart_data.get('id', 'N/A') if 'chart_data' in locals() else 'N/A'
        titolo = chart_data.get('titolo', 'N/A') if 'chart_data' in locals() else 'N/A'
        print(f"⚠️  Errore nella creazione del grafico '{titolo}' (ID: {chart_id}): {str(e)}")
        import traceback
        print(traceback.format_exc())
        try:
            if 'fig' in locals():
                plt.close(fig)
        except:
            pass
        return None

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
    
    # Genera nome file univoco con timestamp per evitare cache
    import hashlib
    import time
    timestamp = int(time.time() * 1000)  # millisecondi
    # Aggiungi hash del contenuto per garantire unicità
    content_hash = hashlib.md5(json.dumps(business_plan_json, sort_keys=True).encode()).hexdigest()[:8]
    output_path = output_dir / f"business-plan-{timestamp}-{content_hash}.pdf"
    
    # Estrai informazioni per header/footer
    pdf_layout = business_plan_json.get('pdf_layout', {})
    header_info = pdf_layout.get('header', {})
    footer_info = pdf_layout.get('footer', {})
    confidenzialita = pdf_layout.get('confidenzialita', 'pubblico')
    
    # Crea il documento PDF con encoding UTF-8
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=3*cm,
        bottomMargin=2.5*cm,
        encoding='utf-8'
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
    
    # Stili con font professionali (Times New Roman) con supporto UTF-8
    styles = getSampleStyleSheet()
    
    # Configura encoding per ReportLab Paragraph (supporta UTF-8 nativamente)
    # Times-Roman e Times-Bold supportano caratteri latini estesi (accenti italiani)
    
    # Stili personalizzati con Times-Roman per aspetto formale
    styles.add(ParagraphStyle(
        name='CoverTitle',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=28,
        textColor=colors.HexColor('#000000'),
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=34,
        encoding='utf-8'
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
    # Times-Roman supporta caratteri latini estesi (UTF-8)
    styles['Normal'].fontName = 'Times-Roman'
    styles['Normal'].fontSize = 11
    styles['Normal'].textColor = colors.HexColor('#000000')
    styles['Normal'].leading = 14
    styles['Normal'].alignment = TA_JUSTIFY
    styles['Normal'].encoding = 'utf-8'
    
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
    
    # Box informativo con sfondo colorato (Paragraph per rendere <b> correttamente)
    info_data = []
    if company_name:
        info_data.append([Paragraph(f"<b>Azienda:</b> {escape_for_pdf(company_name)}", styles['Normal'])])
    info_data.append([Paragraph(f"<b>Data:</b> {escape_for_pdf(data_gen)}", styles['Normal'])])
    info_data.append([Paragraph(f"<b>Versione:</b> {escape_for_pdf(versione)}", styles['Normal'])])
    
    if info_data:
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
    story.append(Paragraph("INDICE", styles['CustomTitle']))
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
            # Preprocessa e normalizza
            sintesi = preprocess_content_for_pdf(sintesi)
            # Dividi in paragrafi se contiene doppie newline
            paragraphs = sintesi.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Usa markdown_to_paragraphs per supportare formattazione
                    para_elements = markdown_to_paragraphs(para.strip(), styles)
                    story.extend(para_elements)
            story.append(Spacer(1, 0.3*cm))
        
        punti_chiave = exec_summary.get('punti_chiave', [])
        if punti_chiave:
            story.append(Paragraph("<b>Punti Chiave:</b>", styles['Heading3']))
            story.append(Spacer(1, 0.2*cm))
            
            # Box colorato per punti chiave
            key_points_data = []
            for i, punto in enumerate(punti_chiave):
                punto_clean = escape_for_pdf(punto)
                key_points_data.append([Paragraph(f"<b>{i+1}.</b> {punto_clean}", styles['Normal'])])
            
            if key_points_data:
                key_points_table = Table(key_points_data, colWidths=[16*cm])
                key_points_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4ff')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3b82f6')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(key_points_table)
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
                print(f"✅ Tabella KPI aggiunta al PDF", flush=True)
        
        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())
    
    # === CAPITOLI NARRATIVI ===
    # (chapters già ordinati sopra)
    
    # Crea un dizionario dei grafici per accesso rapido
    charts_list = business_plan_json.get('charts', [])
    if not isinstance(charts_list, list):
        charts_list = []
    
    # Crea dizionario solo per grafici con 'id' valido
    charts_dict = {}
    for chart in charts_list:
        chart_id = chart.get('id') if isinstance(chart, dict) else None
        if chart_id:
            charts_dict[chart_id] = chart
        else:
            print(f"⚠️  Grafico senza 'id' valido ignorato: {chart}")
    
    print(f"📊 Totale grafici nel JSON: {len(charts_list)}")
    print(f"📊 Grafici nel dizionario (con id valido): {len(charts_dict)}")
    print(f"📊 ID grafici disponibili: {list(charts_dict.keys())}")
    
    # Dati per tabelle riassuntive
    data = business_plan_json.get('data', {})
    
    for chapter in chapters:
        chapter_id = chapter.get('id', '')
        titolo_ch = chapter.get('titolo', '')
        contenuto = chapter.get('contenuto_markdown', '')
        chart_ids = chapter.get('chart_ids', [])
        # Assicurati che chart_ids sia una lista
        if not isinstance(chart_ids, list):
            chart_ids = []
        
        if titolo_ch:
            story.append(Paragraph(titolo_ch, styles['CustomHeading1']))
            story.append(Spacer(1, 0.3*cm))
        
        # Aggiungi tabelle riassuntive per capitoli specifici
        if chapter_id == "CH3_BUSINESS_MODEL":
            business_model = data.get("business_model", {})
            pricing = business_model.get("pricing", {})
            
            if pricing.get("piani"):
                story.append(Paragraph("<b>Piani di Pricing:</b>", styles['Heading3']))
                story.append(Spacer(1, 0.2*cm))
                
                pricing_table_data = [["Piano", "Prezzo", "Periodicità"]]
                for piano in pricing["piani"]:
                    prezzo_eur = piano.get('prezzo_eur', 0)
                    try:
                        prezzo = f"{float(prezzo_eur):,.0f} €"
                    except:
                        prezzo = str(prezzo_eur)
                    periodicita = piano.get("periodicita", "").replace("_", " ").title()
                    pricing_table_data.append([
                        piano.get("nome", ""),
                        prezzo,
                        periodicita
                    ])
                
                if len(pricing_table_data) > 1:
                    pricing_table = Table(pricing_table_data, colWidths=[6*cm, 4*cm, 4*cm])
                    pricing_table.setStyle(TableStyle([
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
                    story.append(pricing_table)
                    print(f"✅ Tabella Pricing aggiunta al PDF", flush=True)
                    story.append(Spacer(1, 0.3*cm))
            
            # Unit Economics
            unit_econ = business_model.get("unit_economics", {})
            if unit_econ:
                story.append(Paragraph("<b>Unit Economics:</b>", styles['Heading3']))
                story.append(Spacer(1, 0.2*cm))
                
                ue_data = []
                if unit_econ.get("cac_eur"):
                    ue_data.append(["CAC (Customer Acquisition Cost)", f"{unit_econ.get('cac_eur', 0):,.0f} €"])
                if unit_econ.get("ltv_eur"):
                    ue_data.append(["LTV (Lifetime Value)", f"{unit_econ.get('ltv_eur', 0):,.0f} €"])
                if unit_econ.get("margine_lordo_percent"):
                    ue_data.append(["Margine Lordo", f"{unit_econ.get('margine_lordo_percent', 0):.1f}%"])
                if unit_econ.get("payback_mesi"):
                    ue_data.append(["Payback Period", f"{unit_econ.get('payback_mesi', 0):.1f} mesi"])
                
                if ue_data:
                    ue_table = Table(ue_data, colWidths=[10*cm, 6*cm])
                    ue_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4ff')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(ue_table)
                    print(f"✅ Tabella Unit Economics aggiunta al PDF", flush=True)
                    story.append(Spacer(1, 0.3*cm))
        
        elif chapter_id == "CH2_MARKET":
            market = data.get("market", {})
            tam_sam_som = market.get("tam_sam_som", {})
            
            if tam_sam_som:
                story.append(Paragraph("<b>Dimensioni del Mercato:</b>", styles['Heading3']))
                story.append(Spacer(1, 0.2*cm))
                
                market_data = []
                if tam_sam_som.get("tam_eur_annuo"):
                    market_data.append(["TAM (Total Addressable Market)", f"{tam_sam_som.get('tam_eur_annuo', 0):,.0f} €"])
                if tam_sam_som.get("sam_eur_annuo"):
                    market_data.append(["SAM (Serviceable Addressable Market)", f"{tam_sam_som.get('sam_eur_annuo', 0):,.0f} €"])
                if tam_sam_som.get("som_eur_annuo"):
                    market_data.append(["SOM (Serviceable Obtainable Market)", f"{tam_sam_som.get('som_eur_annuo', 0):,.0f} €"])
                
                if market_data:
                    market_table = Table(market_data, colWidths=[10*cm, 6*cm])
                    market_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4ff')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(market_table)
                    print(f"✅ Tabella Market aggiunta al PDF", flush=True)
                    story.append(Spacer(1, 0.3*cm))
        
        elif chapter_id == "CH6_RISKS_ROADMAP":
            risks = data.get("risks", [])
            if risks:
                story.append(Paragraph("<b>Rischi Principali:</b>", styles['Heading3']))
                story.append(Spacer(1, 0.2*cm))
                
                risks_data = [["Categoria", "Probabilità", "Impatto"]]
                for risk in risks[:5]:  # Mostra i primi 5 rischi
                    risks_data.append([
                        risk.get("categoria", "").replace("_", " ").title(),
                        risk.get("probabilita", "").title(),
                        risk.get("impatto", "").title()
                    ])
                
                if len(risks_data) > 1:
                    risks_table = Table(risks_data, colWidths=[6*cm, 4*cm, 4*cm])
                    risks_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
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
                    story.append(risks_table)
                    print(f"✅ Tabella Risks aggiunta al PDF", flush=True)
                    story.append(Spacer(1, 0.3*cm))
        
        # Aggiungi il contenuto del capitolo PRIMA dei grafici
        if contenuto:
            # Preprocessa il contenuto per normalizzazione
            contenuto = preprocess_content_for_pdf(contenuto)
            # Log per debug: verifica se ci sono titoli in maiuscolo
            lines_with_uppercase = [line.strip() for line in contenuto.split('\n') 
                                   if line.strip() and len(line.strip()) >= 3 
                                   and not line.strip().startswith('#')
                                   and sum(1 for c in line.strip() if c.isupper() and c.isalpha()) >= 3
                                   and sum(1 for c in line.strip() if c.isupper() and c.isalpha()) / max(1, sum(1 for c in line.strip() if c.isalpha())) >= 0.8]
            if lines_with_uppercase:
                print(f"📌 Titoli in maiuscolo rilevati nel capitolo '{titolo_ch}': {lines_with_uppercase[:3]}")
            elements = markdown_to_paragraphs(contenuto, styles)
            story.extend(elements)
        
        # Aggiungi i grafici referenziati DOPO il contenuto
        # IMPORTANTE: I grafici devono essere mostrati SOLO nel capitolo CH7_CHARTS
        charts_added_count = 0
        
        # Processa i grafici SOLO per il capitolo CH7_CHARTS
        if chapter_id == "CH7_CHARTS":
            print(f"📊 ===== PROCESSANDO CAPITOLO CH7_CHARTS =====")
            print(f"📊 chart_ids nel capitolo: {chart_ids}")
            print(f"📊 Totale grafici disponibili: {len(charts_dict)}")
            story.append(Spacer(1, 0.5*cm))
            
            # Strategia 1: Usa chart_ids se presenti e non vuoti
            charts_to_process = []
            if chart_ids and len(chart_ids) > 0:
                print(f"📊 Strategia 1: Usando chart_ids ({len(chart_ids)} grafici referenziati)")
                for chart_id in chart_ids:
                    if chart_id in charts_dict:
                        charts_to_process.append((chart_id, charts_dict[chart_id]))
                        print(f"   ✅ Grafico {chart_id} trovato")
                    else:
                        print(f"   ⚠️  Grafico {chart_id} non trovato in charts_dict")
                        print(f"   📋 Grafici disponibili: {list(charts_dict.keys())[:5]}...")
            
            # Strategia 2: Fallback - prendi tutti i grafici con chapter_id='CH7_CHARTS'
            if len(charts_to_process) == 0:
                print(f"📊 Strategia 2: Fallback - cercando tutti i grafici con chapter_id='CH7_CHARTS'")
                for chart_id, chart in charts_dict.items():
                    chart_chapter_id = chart.get('chapter_id', '')
                    print(f"   🔍 Grafico {chart_id}: chapter_id='{chart_chapter_id}'")
                    if chart_chapter_id == 'CH7_CHARTS':
                        charts_to_process.append((chart_id, chart))
                        print(f"   ✅ Aggiunto grafico {chart_id} al processamento")
            
            print(f"📊 Totale grafici da processare: {len(charts_to_process)}")
            
            # Processa tutti i grafici trovati
            for chart_id, chart in charts_to_process:
                print(f"📈 Processando grafico: {chart_id} - {chart.get('titolo', 'N/A')}")
                try:
                    chart_img = create_chart_image(chart, width=15*cm, height=10*cm)
                    
                    if chart_img:
                        print(f"   ✅ Immagine grafico generata per {chart_id}")
                        try:
                            # Verifica che il buffer sia valido
                            if hasattr(chart_img, 'read'):
                                chart_img.seek(0)
                                img_data = chart_img.read()
                                print(f"   📏 Dimensione immagine: {len(img_data)} bytes")
                                if len(img_data) == 0:
                                    print(f"   ⚠️  Immagine vuota per {chart_id}")
                                    continue
                                chart_img.seek(0)  # Reset per Image()
                            
                            # Crea l'immagine con dimensioni appropriate
                            chart_img.seek(0)
                            img = Image(chart_img, width=15*cm, height=10*cm)
                            story.append(Spacer(1, 0.3*cm))
                            story.append(img)
                            story.append(Spacer(1, 0.2*cm))
                            charts_added_count += 1
                            print(f"   ✅ Grafico {chart_id} aggiunto al PDF (totale: {charts_added_count})")
                            
                            # Aggiungi caption se presente
                            caption = chart.get('caption', '')
                            if caption:
                                if isinstance(caption, bytes):
                                    caption = caption.decode('utf-8', errors='replace')
                                caption_clean = escape_for_pdf(caption)
                                story.append(Paragraph(f"<i>{caption_clean}</i>", styles['Normal']))
                                story.append(Spacer(1, 0.3*cm))
                        except Exception as img_error:
                            print(f"   ❌ Errore nell'aggiungere immagine al PDF per {chart_id}: {str(img_error)}")
                            import traceback
                            print(traceback.format_exc())
                            continue
                    else:
                        print(f"   ⚠️  Grafico {chart_id} non generato (create_chart_image ha restituito None)")
                        print(f"   📊 Dettagli grafico: tipo={chart.get('tipo')}, serie={len(chart.get('series', []))}")
                except Exception as e:
                    print(f"   ❌ Errore nel generare il grafico {chart_id}: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    continue
            
            print(f"📊 ===== RIEPILOGO: {charts_added_count} grafici aggiunti al PDF per CH7_CHARTS =====")
        else:
            # Se non siamo nel capitolo CH7_CHARTS, verifica se ci sono grafici non processati
            # Questo è un fallback di sicurezza
            if chapter_id != "CH7_CHARTS" and len(charts_dict) > 0:
                # Conta quanti grafici con chapter_id='CH7_CHARTS' ci sono
                unprocessed_charts = [c for c in charts_dict.values() if c.get('chapter_id') == 'CH7_CHARTS']
                if len(unprocessed_charts) > 0:
                    print(f"⚠️  Attenzione: trovati {len(unprocessed_charts)} grafici con chapter_id='CH7_CHARTS' ma il capitolo CH7_CHARTS non è stato ancora processato")
        
        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())
    
    # Fallback finale: se non abbiamo processato nessun grafico ma ci sono grafici con chapter_id='CH7_CHARTS',
    # aggiungili alla fine (caso in cui il capitolo CH7_CHARTS non esiste o non è stato trovato)
    total_charts_processed = sum(1 for chapter in chapters if chapter.get('id') == 'CH7_CHARTS')
    if total_charts_processed == 0:
        print(f"⚠️  ===== FALLBACK FINALE: Capitolo CH7_CHARTS non trovato nei chapters =====")
        unprocessed_charts = [(c['id'], c) for c in charts_dict.values() if c.get('chapter_id') == 'CH7_CHARTS']
        if len(unprocessed_charts) > 0:
            print(f"📊 Trovati {len(unprocessed_charts)} grafici non processati, aggiungendo alla fine del documento")
            story.append(Paragraph("GRAFICI", styles['CustomHeading1']))
            story.append(Spacer(1, 0.5*cm))
            
            for chart_id, chart in unprocessed_charts:
                print(f"📈 Processando grafico (fallback finale): {chart_id} - {chart.get('titolo', 'N/A')}")
                try:
                    chart_img = create_chart_image(chart, width=15*cm, height=10*cm)
                    if chart_img:
                        try:
                            chart_img.seek(0)
                            img = Image(chart_img, width=15*cm, height=10*cm)
                            story.append(Spacer(1, 0.3*cm))
                            story.append(img)
                            story.append(Spacer(1, 0.2*cm))
                            
                            caption = chart.get('caption', '')
                            if caption:
                                if isinstance(caption, bytes):
                                    caption = caption.decode('utf-8', errors='replace')
                                caption_clean = escape_for_pdf(caption)
                                story.append(Paragraph(f"<i>{caption_clean}</i>", styles['Normal']))
                                story.append(Spacer(1, 0.3*cm))
                            print(f"✅ Grafico {chart_id} aggiunto (fallback finale)")
                        except Exception as img_error:
                            print(f"❌ Errore nell'aggiungere immagine al PDF per {chart_id} (fallback): {str(img_error)}")
                            continue
                except Exception as e:
                    print(f"❌ Errore nel generare il grafico {chart_id} (fallback): {str(e)}")
                    continue
            
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
    
    # Messaggio professionale (senza <p>; ReportLab usa alignment sullo stile)
    closing_message = """
    Questo Business Plan è stato redatto con cura e attenzione ai dettagli.<br/><br/>
    Per ulteriori informazioni o chiarimenti, non esitate a contattarci.<br/><br/>
    <i>Documento generato con GetBusinessPlan</i>
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
    
    # Box informativo finale (Paragraph per rendere <b> correttamente)
    final_info = [
        [Paragraph(f"<b>Documento:</b> {escape_for_pdf(titolo)}", styles['Normal'])],
        [Paragraph(f"<b>Data generazione:</b> {escape_for_pdf(data_gen)}", styles['Normal'])],
        [Paragraph(f"<b>Versione:</b> {escape_for_pdf(versione)}", styles['Normal'])]
    ]
    if company_name:
        final_info.insert(0, [Paragraph(f"<b>Azienda:</b> {escape_for_pdf(company_name)}", styles['Normal'])])
    
    final_info_table = Table(final_info, colWidths=[12*cm])
    final_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 24),
        ('RIGHTPADDING', (0, 0), (-1, -1), 24),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
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
    
    # Pulisci file PDF vecchi (mantieni solo gli ultimi 10)
    try:
        pdf_files = sorted(output_dir.glob("business-plan-*.pdf"), key=os.path.getmtime, reverse=True)
        for old_pdf in pdf_files[10:]:  # Mantieni solo gli ultimi 10
            try:
                old_pdf.unlink()
                print(f"🗑️  Rimosso PDF vecchio: {old_pdf.name}")
            except Exception as e:
                print(f"⚠️  Errore rimozione PDF vecchio {old_pdf.name}: {e}")
    except Exception as e:
        print(f"⚠️  Errore pulizia PDF vecchi: {e}")
    
    return str(output_path)
