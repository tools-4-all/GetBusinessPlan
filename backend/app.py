from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import json
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import utils
import pdf_generator
import pdf_generator_analysis

# Carica variabili d'ambiente
load_dotenv()

app = FastAPI(title="GetBusinessPlan API", version="1.0.0")

# CORS - in produzione, specifica i domini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia in produzione con domini specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurazione OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY non configurata nelle variabili d'ambiente.")

# Verifica formato base della chiave (deve iniziare con sk-)
if not OPENAI_API_KEY.startswith("sk-"):
    print("⚠️ ATTENZIONE: La chiave API potrebbe non essere valida (dovrebbe iniziare con 'sk-')")

client = OpenAI(api_key=OPENAI_API_KEY)

# Modelli per le richieste
class BusinessPlanRequest(BaseModel):
    formData: dict
    horizonMonths: int = 24

class PDFRequest(BaseModel):
    businessPlanJson: dict

class MarketAnalysisRequest(BaseModel):
    formData: dict
    analysisType: str = "deep"  # "standard" o "deep"

class PDFAnalysisRequest(BaseModel):
    marketAnalysisJson: dict

class SuggestionRequest(BaseModel):
    questionId: str
    questionTitle: str
    questionDescription: Optional[str] = None
    currentValue: Optional[str] = None
    formType: str = "business-plan"  # "business-plan" o "market-analysis"
    contextData: Optional[dict] = None  # Dati già compilati per contesto

@app.get("/")
async def root():
    return {"message": "GetBusinessPlan API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/test")
async def test():
    """Endpoint di test per verificare che l'API funzioni"""
    import datetime
    return {
        "status": "ok",
        "message": "API funzionante",
        "timestamp": datetime.datetime.now().isoformat(),
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.get("/api/test-openai")
async def test_openai():
    """Endpoint di test per verificare la connessione OpenAI"""
    import datetime
    try:
        # Verifica che la chiave sia configurata
        if not OPENAI_API_KEY:
            return {
                "status": "error",
                "openai_working": False,
                "error": "OPENAI_API_KEY non configurata",
                "help": "Configura OPENAI_API_KEY su Render come variabile d'ambiente.",
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        # Test con una chiamata semplice
        test_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Rispondi solo con 'OK'"}],
            max_tokens=10
        )
        return {
            "status": "ok",
            "openai_working": True,
            "response": test_response.choices[0].message.content,
            "api_key_format": "valid" if OPENAI_API_KEY.startswith("sk-") else "invalid",
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = str(e)
        is_auth_error = "401" in error_msg or "invalid_api_key" in error_msg.lower() or "incorrect api key" in error_msg.lower()
        
        return {
            "status": "error",
            "openai_working": False,
            "error": error_msg,
            "is_auth_error": is_auth_error,
            "help": "Configura OPENAI_API_KEY su Render come variabile d'ambiente." if is_auth_error else None,
            "timestamp": datetime.datetime.now().isoformat()
        }

@app.post("/api/generate-business-plan")
async def generate_business_plan(request: BusinessPlanRequest):
    """Genera il business plan chiamando OpenAI"""
    import datetime
    start_time = datetime.datetime.now()
    print(f"=== INIZIO GENERAZIONE BUSINESS PLAN ===")
    print(f"Timestamp: {start_time.isoformat()}")
    print(f"Dati ricevuti: {len(str(request.formData))} caratteri")
    
    try:
        # Carica il prompt template
        prompt_path = Path(__file__).parent / "prompt.json"
        if not prompt_path.exists():
            # Prova nella directory parent
            prompt_path = Path(__file__).parent.parent / "prompt.json"
        
        print(f"Caricamento prompt da: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_config = json.load(f)
        
        model_name = prompt_config.get('model', 'N/A')
        print(f"Modello configurato: {model_name}")
        
        # Verifica se il modello è valido (lista modelli comuni)
        valid_models = [
            'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo',
            'o1-preview', 'o1-mini', 'gpt-4o-2024-08-06', 'gpt-4-turbo-2024-04-09'
        ]
        if not any(model_name.startswith(vm.split('-')[0]) for vm in valid_models):
            print(f"⚠️ ATTENZIONE: Il modello '{model_name}' potrebbe non essere valido")
            print(f"Modelli suggeriti: {', '.join(valid_models[:3])}")
        
        # Prepara i dati utente
        user_data_json = utils.prepare_user_input_json(request.formData)
        horizon_months = request.horizonMonths
        
        # Costruisci i messaggi per OpenAI
        messages = utils.build_messages_from_prompt(
            prompt_config, user_data_json, horizon_months
        )
        
        # Prepara il request body
        request_body = {
            "model": prompt_config["model"],
            "messages": messages
        }
        
        # Aggiungi parametri opzionali
        if prompt_config.get("reasoning") and prompt_config["model"].startswith("o1"):
            request_body["reasoning"] = prompt_config["reasoning"]
        
        if prompt_config.get("text", {}).get("format"):
            fmt = prompt_config["text"]["format"]
            request_body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": fmt["name"],
                    "strict": fmt["strict"],
                    "schema": fmt["schema"]
                }
            }
        
        if prompt_config.get("temperature") is not None:
            request_body["temperature"] = prompt_config["temperature"]
        if prompt_config.get("max_tokens") is not None:
            request_body["max_tokens"] = prompt_config["max_tokens"]
        if prompt_config.get("max_completion_tokens") is not None:
            request_body["max_completion_tokens"] = prompt_config["max_completion_tokens"]
        
        # Chiama OpenAI
        openai_start = datetime.datetime.now()
        print(f"Chiamata OpenAI con modello {request_body['model']}...")
        print(f"Timestamp inizio OpenAI: {openai_start.isoformat()}")
        print(f"Request body keys: {list(request_body.keys())}")
        print(f"Numero messaggi: {len(request_body.get('messages', []))}")
        
        try:
            # Chiamata OpenAI sincrona (il client OpenAI gestisce già il timeout interno)
            # Usiamo asyncio.to_thread per non bloccare l'event loop (Python 3.9+)
            import asyncio
            import sys
            if sys.version_info >= (3, 9):
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    **request_body
                )
            else:
                # Fallback per versioni precedenti
                from concurrent.futures import ThreadPoolExecutor
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    response = await loop.run_in_executor(
                        executor,
                        lambda: client.chat.completions.create(**request_body)
                    )
            openai_end = datetime.datetime.now()
            openai_elapsed = (openai_end - openai_start).total_seconds()
            print(f"Timestamp fine OpenAI: {openai_end.isoformat()}")
            print(f"Tempo chiamata OpenAI: {openai_elapsed:.2f} secondi ({openai_elapsed/60:.2f} minuti)")
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"Risposta ricevuta, lunghezza: {len(str(content)) if content else 0}")
            else:
                print("ATTENZIONE: Risposta OpenAI senza choices")
        except Exception as openai_error:
            openai_end = datetime.datetime.now()
            openai_elapsed = (openai_end - openai_start).total_seconds()
            print(f"ERRORE OpenAI dopo {openai_elapsed:.2f} secondi")
            print(f"Tipo errore: {type(openai_error).__name__}")
            print(f"Messaggio errore: {str(openai_error)}")
            import traceback
            traceback.print_exc()
            # Restituisci un errore più dettagliato
            error_detail = f"Errore OpenAI: {str(openai_error)}"
            if "model" in str(openai_error).lower() or "invalid" in str(openai_error).lower():
                error_detail += f" (Verifica che il modello '{request_body.get('model')}' sia valido)"
            raise HTTPException(status_code=500, detail=error_detail)
        
        # Estrai il JSON dalla risposta
        content = response.choices[0].message.content
        if isinstance(content, str):
            business_plan_json = json.loads(content)
        else:
            business_plan_json = content
        
        # Sanitizza i dati (come in generate.js)
        utils.sanitize_italia_regime_note(business_plan_json)
        
        end_time = datetime.datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print(f"=== FINE GENERAZIONE BUSINESS PLAN ===")
        print(f"Tempo totale: {elapsed:.2f} secondi ({elapsed/60:.2f} minuti)")
        print(f"Timestamp fine: {end_time.isoformat()}")
        
        return JSONResponse(content={
            "success": True,
            "json": business_plan_json,
            "generation_time_seconds": elapsed
        })
        
    except json.JSONDecodeError as e:
        print(f"ERRORE parsing JSON: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore parsing JSON: {str(e)}")
    except HTTPException:
        # Rilancia le HTTPException così come sono
        raise
    except Exception as e:
        end_time = datetime.datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print(f"ERRORE GENERALE dopo {elapsed:.2f} secondi: {str(e)}")
        print(f"Tipo errore: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@app.post("/api/generate-market-analysis")
async def generate_market_analysis(request: MarketAnalysisRequest):
    """Genera analisi di mercato con deep research usando web search"""
    import datetime
    start_time = datetime.datetime.now()
    print(f"=== INIZIO ANALISI DI MERCATO ===")
    print(f"Timestamp: {start_time.isoformat()}")
    print(f"Tipo analisi: {request.analysisType}")
    print(f"Dati ricevuti: {len(str(request.formData))} caratteri")
    
    try:
        # Carica il prompt template per analisi di mercato
        prompt_path = Path(__file__).parent / "prompt_analisi.json"
        if not prompt_path.exists():
            raise HTTPException(status_code=500, detail="File prompt_analisi.json non trovato")
        
        print(f"Caricamento prompt da: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_config = json.load(f)
        
        model_name = prompt_config.get('model', 'gpt-4o')
        print(f"Modello configurato: {model_name}")
        
        # Prepara i dati utente per l'analisi
        user_data = {
            "settore": request.formData.get('industry', ''),
            "area_geografica": request.formData.get('geographicMarket', ''),
            "segmento_target": request.formData.get('targetSegment', ''),
            "competitor": request.formData.get('competitors', ''),
            "dimensione_mercato": request.formData.get('marketSize', ''),
            "focus_analisi": request.formData.get('analysisFocus', '')
        }
        user_data_json = json.dumps(user_data, ensure_ascii=False, indent=2)
        
        # Costruisci i messaggi per OpenAI
        messages = []
        for msg in prompt_config["input"]:
            content_parts = []
            for content_item in msg.get("content", []):
                if content_item.get("type") == "text":
                    text = content_item.get("text", "")
                    # Sostituisci i placeholder
                    text = text.replace("{{USER_DATA_JSON}}", user_data_json)
                    text = text.replace("{{ANALYSIS_TYPE}}", request.analysisType)
                    content_parts.append(text)
            
            if content_parts:
                messages.append({
                    "role": msg.get("role"),
                    "content": "".join(content_parts)
                })
        
        # Prepara il request body
        request_body = {
            "model": model_name,
            "messages": messages,
            "temperature": prompt_config.get("temperature", 0.3)
        }
        
        # Nota: web_search non è supportato direttamente dall'API OpenAI standard
        # Il modello userà la sua conoscenza aggiornata e il prompt chiede esplicitamente ricerche web
        # Se in futuro OpenAI aggiunge supporto per web_search, si può riabilitare qui
        
        # Aggiungi response_format se presente
        if prompt_config.get("text", {}).get("format"):
            fmt = prompt_config["text"]["format"]
            request_body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": fmt["name"],
                    "strict": fmt["strict"],
                    "schema": fmt["schema"]
                }
            }
        
        # Chiama OpenAI
        openai_start = datetime.datetime.now()
        print(f"Chiamata OpenAI con modello {model_name} per analisi di mercato...")
        print(f"Timestamp inizio OpenAI: {openai_start.isoformat()}")
        print(f"Request body keys: {list(request_body.keys())}")
        
        try:
            # Chiamata OpenAI sincrona
            import asyncio
            import sys
            if sys.version_info >= (3, 9):
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    **request_body
                )
            else:
                from concurrent.futures import ThreadPoolExecutor
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    response = await loop.run_in_executor(
                        executor,
                        lambda: client.chat.completions.create(**request_body)
                    )
            openai_end = datetime.datetime.now()
            openai_elapsed = (openai_end - openai_start).total_seconds()
            print(f"Timestamp fine OpenAI: {openai_end.isoformat()}")
            print(f"Tempo chiamata OpenAI: {openai_elapsed:.2f} secondi ({openai_elapsed/60:.2f} minuti)")
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"Risposta ricevuta, lunghezza: {len(str(content)) if content else 0}")
            else:
                print("ATTENZIONE: Risposta OpenAI senza choices")
        except Exception as openai_error:
            openai_end = datetime.datetime.now()
            openai_elapsed = (openai_end - openai_start).total_seconds()
            print(f"ERRORE OpenAI dopo {openai_elapsed:.2f} secondi")
            print(f"Tipo errore: {type(openai_error).__name__}")
            print(f"Messaggio errore: {str(openai_error)}")
            import traceback
            traceback.print_exc()
            error_detail = f"Errore OpenAI: {str(openai_error)}"
            if "model" in str(openai_error).lower() or "invalid" in str(openai_error).lower():
                error_detail += f" (Verifica che il modello '{model_name}' sia valido)"
            raise HTTPException(status_code=500, detail=error_detail)
        
        # Estrai il JSON dalla risposta
        content = response.choices[0].message.content
        if isinstance(content, str):
            market_analysis_json = json.loads(content)
        else:
            market_analysis_json = content
        
        # Valida i requisiti minimi di parole
        is_valid, validation_report = utils.validate_market_analysis_word_count(market_analysis_json)
        if not is_valid:
            print("⚠️ ATTENZIONE: L'analisi non rispetta tutti i requisiti minimi di parole")
            print(f"Avvisi: {len(validation_report['warnings'])}")
            for warning in validation_report['warnings']:
                print(f"  - {warning}")
        else:
            print("✅ Validazione parole: tutti i requisiti minimi rispettati")
        
        end_time = datetime.datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print(f"=== FINE ANALISI DI MERCATO ===")
        print(f"Tempo totale: {elapsed:.2f} secondi ({elapsed/60:.2f} minuti)")
        print(f"Timestamp fine: {end_time.isoformat()}")
        
        return JSONResponse(content={
            "success": True,
            "json": market_analysis_json,
            "generation_time_seconds": elapsed,
            "validation": validation_report if not is_valid else None  # Includi solo se ci sono problemi
        })
        
    except json.JSONDecodeError as e:
        print(f"ERRORE parsing JSON: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore parsing JSON: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        end_time = datetime.datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print(f"ERRORE GENERALE dopo {elapsed:.2f} secondi: {str(e)}")
        print(f"Tipo errore: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@app.post("/api/generate-pdf")
async def generate_pdf(request: PDFRequest):
    """Genera il PDF dal JSON del business plan"""
    try:
        pdf_path = await pdf_generator.create_pdf_from_json(request.businessPlanJson)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF non generato correttamente")
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="business-plan.pdf",
            headers={"Content-Disposition": "attachment; filename=business-plan.pdf"}
        )
    except Exception as e:
        print(f"Errore generazione PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-pdf-analysis")
async def generate_pdf_analysis(request: PDFAnalysisRequest):
    """Genera PDF dall'analisi di mercato"""
    try:
        print("=== INIZIO GENERAZIONE PDF ANALISI DI MERCATO ===")
        output_path = await pdf_generator_analysis.create_pdf_from_market_analysis(request.marketAnalysisJson)
        
        if not Path(output_path).exists():
            raise HTTPException(status_code=500, detail="File PDF non generato correttamente")
        
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="analisi-mercato.pdf"
        )
    except Exception as e:
        print(f"Errore nella generazione PDF analisi: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore generazione PDF: {str(e)}")

@app.post("/api/generate-full")
async def generate_full(request: BusinessPlanRequest):
    """Genera sia il JSON che il PDF in un'unica chiamata"""
    try:
        # Genera il business plan
        bp_response = await generate_business_plan(request)
        bp_data = json.loads(bp_response.body)
        
        if not bp_data.get("success"):
            raise HTTPException(status_code=500, detail="Errore nella generazione del business plan")
        
        # Genera il PDF
        pdf_path = await pdf_generator.create_pdf_from_json(bp_data["json"])
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF non generato correttamente")
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="business-plan.pdf"
        )
    except Exception as e:
        print(f"Errore: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/get-suggestions")
async def get_suggestions(request: SuggestionRequest):
    """Genera suggerimenti professionali per una domanda specifica"""
    try:
        # Prepara il prompt per i suggerimenti
        context_info = ""
        if request.contextData:
            # Filtra solo i dati rilevanti per il contesto
            relevant_context = {}
            for key, value in request.contextData.items():
                if value and str(value).strip():
                    relevant_context[key] = value
            if relevant_context:
                context_info = f"\n\nContesto già compilato:\n{json.dumps(relevant_context, ensure_ascii=False, indent=2)}"
        
        current_value_info = ""
        if request.currentValue and request.currentValue.strip():
            current_value_info = f"\nValore attuale inserito: {request.currentValue[:200]}"
        
        description_info = ""
        if request.questionDescription:
            description_info = f"\nDescrizione: {request.questionDescription}"
        
        suggestion_prompt = f"""Sei un consulente esperto per la creazione di business plan professionali in Italia.

L'utente sta compilando la seguente domanda:
Domanda: {request.questionTitle}{description_info}{current_value_info}{context_info}

Fornisci 3-5 suggerimenti professionali e concreti per aiutare l'utente a rispondere meglio a questa domanda.
I suggerimenti devono essere:
- Specifici e pratici
- Orientati al mercato italiano quando rilevante
- Professionali e adatti a un business plan
- Concisi (max 2-3 frasi ciascuno)
- Utili per migliorare la qualità della risposta

Rispondi SOLO con un JSON array di stringhe, esempio:
["Suggerimento 1", "Suggerimento 2", "Suggerimento 3"]
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modello veloce per suggerimenti
            messages=[
                {"role": "system", "content": "Sei un assistente esperto che fornisce suggerimenti professionali per business plan. Rispondi sempre e solo con un JSON array valido."},
                {"role": "user", "content": suggestion_prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        content = response.choices[0].message.content.strip()
        
        # Estrai JSON dalla risposta (potrebbe essere dentro markdown code blocks)
        if content.startswith("```"):
            # Rimuovi markdown code blocks
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
        
        # Prova a parsare il JSON
        try:
            suggestions = json.loads(content)
            if not isinstance(suggestions, list):
                suggestions = [suggestions] if suggestions else []
        except json.JSONDecodeError:
            # Se non è JSON valido, prova a estrarre array manualmente
            import re
            matches = re.findall(r'\[(.*?)\]', content, re.DOTALL)
            if matches:
                # Prova a parsare il contenuto dell'array
                try:
                    suggestions = json.loads("[" + matches[0] + "]")
                except:
                    suggestions = []
            else:
                # Fallback: dividi per righe e prendi le prime 5
                lines = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().startswith(("[", "]"))]
                suggestions = lines[:5] if lines else []
        
        # Assicurati che sia una lista di stringhe
        if not isinstance(suggestions, list):
            suggestions = []
        
        suggestions = [str(s).strip() for s in suggestions if s and str(s).strip()][:5]
        
        return JSONResponse(content={
            "success": True,
            "suggestions": suggestions
        })
        
    except Exception as e:
        print(f"Errore generazione suggerimenti: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "success": False,
            "suggestions": [],
            "error": str(e)
        })
