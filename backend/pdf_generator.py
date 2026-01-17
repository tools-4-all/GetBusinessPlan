from weasyprint import HTML, CSS
from pathlib import Path
import os
from generate_html import build_html_from_json

async def create_pdf_from_json(business_plan_json: dict) -> str:
    """Genera PDF usando WeasyPrint (più leggero di Playwright, senza dipendenze native)"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Genera HTML dal JSON (for_pdf=True per mostrare grafici come tabelle)
    html_content = build_html_from_json(business_plan_json, for_pdf=True)
    
    # CSS per il PDF (migliora la formattazione)
    pdf_css = CSS(string='''
        @page {
            size: A4;
            margin: 70px 44px;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Arial, sans-serif;
        }
        .page-break {
            page-break-before: always;
        }
        .cover {
            page-break-after: always;
        }
        .toc {
            page-break-after: always;
        }
    ''')
    
    # Genera il PDF
    output_path = output_dir / "business-plan.pdf"
    HTML(string=html_content).write_pdf(
        str(output_path),
        stylesheets=[pdf_css]
    )
    
    return str(output_path)
