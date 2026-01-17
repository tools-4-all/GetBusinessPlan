#!/usr/bin/env python3
"""Script di test per verificare la generazione PDF con copertina colorata"""

import asyncio
import json
from pdf_generator import create_pdf_from_json

# Dati di test minimi
test_data = {
    "meta": {
        "lingua": "it-IT",
        "stile": "formale",
        "orizzonte_mesi": 24,
        "data_generazione": "01/01/2024",
        "versione": "1.0"
    },
    "pdf_layout": {
        "titolo_documento": "Business Plan di Test",
        "sottotitolo": "Documento di prova per copertina colorata",
        "confidenzialita": "pubblico",
        "header": {"left": "", "right": ""},
        "footer": {"left": "", "center": "", "right": ""},
        "chapter_order": []
    },
    "data": {
        "company_name": "Azienda Test S.r.l."
    },
    "executive_summary": {
        "sintesi": "Questo è un business plan di test per verificare la copertina colorata.",
        "punti_chiave": ["Punto 1", "Punto 2"],
        "kpi_principali": []
    },
    "narrative": {
        "chapters": []
    },
    "charts": [],
    "assumptions": [],
    "dati_mancanti": [],
    "disclaimer": "Documento di test"
}

async def test():
    print("🧪 Test generazione PDF con copertina colorata...")
    try:
        pdf_path = await create_pdf_from_json(test_data)
        print(f"✅ PDF generato con successo: {pdf_path}")
        print("📄 Apri il file per verificare la copertina colorata e la pagina finale")
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
