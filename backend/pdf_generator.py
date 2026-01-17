from playwright.async_api import async_playwright
import os
from pathlib import Path
from generate_html import build_html_from_json

async def create_pdf_from_json(business_plan_json: dict) -> str:
    """Genera PDF usando Playwright (stesso motore di Puppeteer)"""
    
    # Crea directory output se non esiste
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Genera HTML dal JSON
    html_content = build_html_from_json(business_plan_json)
    
    # Usa Playwright per generare PDF
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Imposta il contenuto HTML
        await page.set_content(html_content, wait_until="networkidle")
        
        # Aspetta che Chart.js abbia renderizzato i grafici
        try:
            await page.wait_for_function(
                "window.__CHARTS_RENDERED__ === true",
                timeout=15000
            )
        except Exception as e:
            print(f"Warning: Timeout attesa grafici: {e}")
        
        # Ottieni header/footer dal layout
        layout = business_plan_json.get("pdf_layout", {})
        header_left = layout.get("header", {}).get("left", "")
        header_right = layout.get("header", {}).get("right", "")
        footer_left = layout.get("footer", {}).get("left", "")
        footer_center = layout.get("footer", {}).get("center", "")
        footer_right = layout.get("footer", {}).get("right", "Pagina {PAGE_NUMBER}")
        
        # Header/footer template
        header_template = f'''
    <div style="width:100%; font-size:9px; color:#666; padding:0 44px; display:flex; justify-content:space-between;">
      <div>{header_left}</div>
      <div>{header_right}</div>
    </div>
  '''
        
        footer_template = f'''
    <div style="width:100%; font-size:9px; color:#666; padding:0 44px; display:flex; justify-content:space-between;">
      <div>{footer_left}</div>
      <div>{footer_center}</div>
      <div>{footer_right.replace("{PAGE_NUMBER}", '<span class="pageNumber"></span>')}</div>
    </div>
  '''
        
        # Genera il PDF
        output_path = output_dir / "business-plan.pdf"
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "70px", "right": "44px", "bottom": "70px", "left": "44px"},
            display_header_footer=True,
            header_template=header_template,
            footer_template=footer_template
        )
        
        await browser.close()
    
    return str(output_path)
