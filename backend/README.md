# GetBusinessPlan Backend API

Backend Python per la generazione di business plan tramite OpenAI e generazione PDF.

## Setup Locale

1. Installa Python 3.11+ se non già presente

2. Crea un ambiente virtuale:
```bash
python3 -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

3. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

4. Installa i browser per Playwright:
```bash
playwright install chromium
```

5. Crea un file `.env` con la tua chiave API:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

6. Avvia il server:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Il server sarà disponibile su `http://localhost:8000`

## Deploy su Railway

1. Crea un account su [railway.app](https://railway.app)

2. Connetti il repository GitHub

3. Railway rileverà automaticamente che è un progetto Python

4. Aggiungi la variabile d'ambiente `OPENAI_API_KEY` nel dashboard Railway

5. Il deploy avverrà automaticamente ad ogni push

## Endpoint API

- `GET /` - Health check
- `GET /health` - Status API
- `POST /api/generate-business-plan` - Genera business plan JSON
- `POST /api/generate-pdf` - Genera PDF dal JSON
- `POST /api/generate-full` - Genera JSON e PDF in un'unica chiamata

## Struttura

- `app.py` - FastAPI main application
- `utils.py` - Funzioni helper per preparazione dati
- `generate_html.py` - Generazione HTML dal JSON
- `pdf_generator.py` - Generazione PDF con Playwright
- `prompt.json` - Template prompt per OpenAI
