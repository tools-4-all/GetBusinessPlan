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

@app.post("/api/generate-business-plan")
async def generate_business_plan(request: BusinessPlanRequest):
    """Genera il business plan chiamando OpenAI"""
    try:
        # Carica il prompt template
        prompt_path = Path(__file__).parent / "prompt.json"
        if not prompt_path.exists():
            # Prova nella directory parent
            prompt_path = Path(__file__).parent.parent / "prompt.json"
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_config = json.load(f)
        
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
        print(f"Chiamata OpenAI con modello {request_body['model']}...")
        response = client.chat.completions.create(**request_body)
        
        # Estrai il JSON dalla risposta
        content = response.choices[0].message.content
        if isinstance(content, str):
            business_plan_json = json.loads(content)
        else:
            business_plan_json = content
        
        # Sanitizza i dati (come in generate.js)
        utils.sanitize_italia_regime_note(business_plan_json)
        
        return JSONResponse(content={
            "success": True,
            "json": business_plan_json
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
