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
    raise ValueError("OPENAI_API_KEY non configurata nelle variabili d'ambiente")

client = OpenAI(api_key=OPENAI_API_KEY)

# Modelli per le richieste
class BusinessPlanRequest(BaseModel):
    formData: dict
    horizonMonths: int = 24

class PDFRequest(BaseModel):
    businessPlanJson: dict

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
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "openai_working": False,
            "error": str(e),
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
        
        print(f"Modello configurato: {prompt_config.get('model', 'N/A')}")
        
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
        
        try:
            # Timeout per la chiamata OpenAI (5 minuti)
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            # Esegui la chiamata OpenAI in un thread separato per evitare di bloccare l'event loop
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await asyncio.wait_for(
                    loop.run_in_executor(executor, lambda: client.chat.completions.create(**request_body)),
                    timeout=300.0
                )
            openai_end = datetime.datetime.now()
            openai_elapsed = (openai_end - openai_start).total_seconds()
            print(f"Timestamp fine OpenAI: {openai_end.isoformat()}")
            print(f"Tempo chiamata OpenAI: {openai_elapsed:.2f} secondi ({openai_elapsed/60:.2f} minuti)")
            print(f"Risposta ricevuta, lunghezza: {len(str(response.choices[0].message.content)) if response.choices[0].message.content else 0}")
        except asyncio.TimeoutError:
            print(f"ERRORE: Timeout chiamata OpenAI dopo 5 minuti")
            raise HTTPException(status_code=504, detail="Timeout chiamata OpenAI: la generazione ha impiegato troppo tempo")
        except Exception as openai_error:
            print(f"ERRORE OpenAI: {str(openai_error)}")
            print(f"Tipo errore: {type(openai_error).__name__}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Errore OpenAI: {str(openai_error)}")
        
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
        raise HTTPException(status_code=500, detail=f"Errore parsing JSON: {str(e)}")
    except Exception as e:
        print(f"Errore: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
