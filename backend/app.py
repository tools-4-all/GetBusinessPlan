from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
import stripe
import firebase_admin
from firebase_admin import credentials, auth

# Carica variabili d'ambiente
load_dotenv()

# Inizializza Firebase Admin SDK
firebase_initialized = False
try:
    # Prova a caricare le credenziali da variabile d'ambiente (JSON string)
    firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if firebase_creds_json:
        try:
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print("✅ Firebase Admin inizializzato con credenziali da variabile d'ambiente")
            print(f"   Project ID: {cred_dict.get('project_id', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f"❌ ERRORE: FIREBASE_CREDENTIALS_JSON non è un JSON valido: {e}")
        except Exception as e:
            print(f"❌ ERRORE nell'inizializzazione Firebase Admin da JSON: {e}")
    else:
        # Prova a caricare da file (per sviluppo locale)
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
        if os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                firebase_initialized = True
                print(f"✅ Firebase Admin inizializzato con credenziali da {cred_path}")
            except Exception as e:
                print(f"❌ ERRORE nell'inizializzazione Firebase Admin da file: {e}")
        else:
            print("⚠️ ATTENZIONE: Firebase Admin non configurato. L'autenticazione non funzionerà.")
            print("   Configura FIREBASE_CREDENTIALS_JSON o FIREBASE_CREDENTIALS_PATH")
except Exception as e:
    print(f"⚠️ ERRORE nell'inizializzazione Firebase Admin: {e}")
    import traceback
    traceback.print_exc()
    print("   L'autenticazione potrebbe non funzionare correttamente")

app = FastAPI(title="GetBusinessPlan API", version="1.0.0")

# Security scheme per Bearer token
security = HTTPBearer(auto_error=False)

# Funzione per verificare il token Firebase
async def verify_firebase_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Verifica il token Firebase e restituisce l'utente autenticato"""
    if not credentials:
        print("❌ verify_firebase_token: Nessun token fornito")
        raise HTTPException(
            status_code=401,
            detail="Token di autenticazione richiesto. Effettua il login per continuare."
        )
    
    token = credentials.credentials
    
    # Verifica che Firebase Admin sia inizializzato
    try:
        firebase_admin.get_app()
    except ValueError:
        print("❌ ERRORE CRITICO: Firebase Admin non inizializzato!")
        raise HTTPException(
            status_code=500,
            detail="Errore di configurazione del server. Contatta il supporto."
        )
    
    if not token or len(token) < 10:
        print(f"❌ verify_firebase_token: Token non valido (lunghezza: {len(token) if token else 0})")
        raise HTTPException(
            status_code=401,
            detail="Token non valido. Effettua nuovamente il login."
        )
    
    print(f"🔍 Verifica token Firebase (lunghezza: {len(token)}, preview: {token[:20]}...)")
    
    # Verifica che Firebase Admin sia inizializzato
    try:
        app = firebase_admin.get_app()
        print(f"✅ Firebase Admin app trovata: {app.name}")
    except ValueError as e:
        print(f"❌ ERRORE: Firebase Admin app non trovata: {e}")
        raise HTTPException(
            status_code=500,
            detail="Errore di configurazione del server. Firebase Admin non inizializzato."
        )
    
    try:
        # Verifica il token con Firebase Admin
        print("🔄 Chiamata auth.verify_id_token...")
        decoded_token = auth.verify_id_token(token, check_revoked=False)
        print(f"✅ Token verificato con successo!")
        print(f"   Email: {decoded_token.get('email', 'N/A')}")
        print(f"   UID: {decoded_token.get('uid', 'N/A')}")
        print(f"   Project ID (aud): {decoded_token.get('aud', 'N/A')}")
        print(f"   Issuer: {decoded_token.get('iss', 'N/A')}")
        
        # Verifica che il project ID corrisponda (opzionale, per debug)
        try:
            app = firebase_admin.get_app()
            # Il project_id dovrebbe essere nelle credenziali
            if hasattr(app.credential, 'project_id'):
                expected_project_id = app.credential.project_id
                token_project_id = decoded_token.get('aud')
                if expected_project_id and token_project_id and expected_project_id != token_project_id:
                    print(f"⚠️ ATTENZIONE: Project ID mismatch! Token: {token_project_id}, Config: {expected_project_id}")
        except:
            pass
        
        return decoded_token
    except ValueError as e:
        print(f"❌ Errore verifica token Firebase (ValueError): {e}")
        raise HTTPException(
            status_code=401,
            detail="Token non valido. Effettua nuovamente il login."
        )
    except firebase_admin.exceptions.InvalidArgumentError as e:
        print(f"❌ Errore verifica token Firebase (InvalidArgumentError): {e}")
        raise HTTPException(
            status_code=401,
            detail="Token non valido. Effettua nuovamente il login."
        )
    except Exception as e:
        print(f"❌ Errore verifica token Firebase (generico): {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=401,
            detail="Token non valido o scaduto. Effettua nuovamente il login."
        )

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

# Configurazione Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    print("⚠️ ATTENZIONE: STRIPE_SECRET_KEY non configurata. Il pagamento non funzionerà.")

# Prezzi (in centesimi di euro) - usati come fallback se Price ID non configurati
PRICE_BUSINESS_PLAN = int(os.getenv("PRICE_BUSINESS_PLAN_CENTS", "1999"))  # 19.99€ default
PRICE_MARKET_ANALYSIS = int(os.getenv("PRICE_MARKET_ANALYSIS_CENTS", "1499"))  # 14.99€ default

# Price ID Stripe (raccomandato - crea i Price in Stripe Dashboard e inserisci gli ID qui)
STRIPE_PRICE_BUSINESS_PLAN = os.getenv("STRIPE_PRICE_BUSINESS_PLAN", "")
STRIPE_PRICE_MARKET_ANALYSIS = os.getenv("STRIPE_PRICE_MARKET_ANALYSIS", "")
STRIPE_PRICE_BUSINESS_PLAN_UPSELL = os.getenv("STRIPE_PRICE_BUSINESS_PLAN_UPSELL", "")
STRIPE_PRICE_MARKET_ANALYSIS_UPSELL = os.getenv("STRIPE_PRICE_MARKET_ANALYSIS_UPSELL", "")

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

class CreateCheckoutRequest(BaseModel):
    documentType: str  # "business-plan" o "market-analysis"
    successUrl: str
    cancelUrl: str
    includeUpsell: bool = False  # Se True, include anche l'altro servizio con sconto

class VerifyPaymentRequest(BaseModel):
    sessionId: str
    documentType: str  # "business-plan" o "market-analysis"

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

@app.get("/api/test-firebase")
async def test_firebase():
    """Endpoint di test per verificare che Firebase Admin sia configurato correttamente"""
    try:
        # Verifica che Firebase Admin sia inizializzato
        app = firebase_admin.get_app()
        print(f"✅ Firebase Admin app trovata: {app.name}")
        
        # Prova a ottenere informazioni sul progetto
        project_id = None
        try:
            # Le credenziali contengono il project_id
            cred = app.credential
            if hasattr(cred, 'project_id'):
                project_id = cred.project_id
        except:
            pass
        
        return {
            "success": True,
            "message": "Firebase Admin è configurato correttamente",
            "firebase_initialized": firebase_initialized,
            "project_id": project_id or "N/A",
            "app_name": app.name
        }
    except ValueError:
        return {
            "success": False,
            "message": "Firebase Admin non è inizializzato",
            "firebase_initialized": firebase_initialized,
            "error": "Firebase Admin app non trovata"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Errore nella verifica Firebase Admin: {str(e)}",
            "firebase_initialized": firebase_initialized,
            "error": str(e)
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
        
        # Migliora la qualità con post-processing
        business_plan_json = utils.enhance_business_plan_quality(business_plan_json)
        
        # Valida la qualità del business plan
        is_valid, validation_report = utils.validate_business_plan_quality(business_plan_json)
        if not is_valid:
            print("⚠️ ATTENZIONE: Il business plan non rispetta tutti i requisiti minimi di qualità")
            print(f"Avvisi: {len(validation_report['warnings'])}")
            for warning in validation_report['warnings']:
                print(f"  - {warning}")
        else:
            print("✅ Validazione qualità: tutti i requisiti minimi rispettati")
        
        end_time = datetime.datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print(f"=== FINE GENERAZIONE BUSINESS PLAN ===")
        print(f"Tempo totale: {elapsed:.2f} secondi ({elapsed/60:.2f} minuti)")
        print(f"Timestamp fine: {end_time.isoformat()}")
        
        return JSONResponse(content={
            "success": True,
            "json": business_plan_json,
            "generation_time_seconds": elapsed,
            "validation": validation_report if not is_valid else None  # Includi solo se ci sono problemi
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

@app.post("/api/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    user: dict = Depends(verify_firebase_token)
):
    """Crea una sessione di checkout Stripe - Richiede autenticazione"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe non configurato")
    
    # L'utente è autenticato (verificato da verify_firebase_token)
    user_email = user.get('email', 'unknown')
    user_id = user.get('uid', 'unknown')
    print(f"✅ Checkout session richiesta da utente autenticato: {user_email} (UID: {user_id})")
    
    try:
        # Determina il prezzo in base al tipo di documento
        line_items = []
        
        if request.documentType == "business-plan":
            # Usa Price ID se configurato, altrimenti usa price_data
            if STRIPE_PRICE_BUSINESS_PLAN:
                line_items.append({
                    'price': STRIPE_PRICE_BUSINESS_PLAN,
                    'quantity': 1,
                })
            else:
                # Fallback a price_data se Price ID non configurato
                line_items.append({
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': 'Business Plan Professionale',
                        },
                        'unit_amount': PRICE_BUSINESS_PLAN,
                    },
                    'quantity': 1,
                })
            
            # Se include upsell, aggiungi anche l'analisi di mercato con sconto
            if request.includeUpsell:
                if STRIPE_PRICE_MARKET_ANALYSIS_UPSELL:
                    line_items.append({
                        'price': STRIPE_PRICE_MARKET_ANALYSIS_UPSELL,
                        'quantity': 1,
                    })
                else:
                    # Fallback a price_data con sconto del 30%
                    upsell_price = int(PRICE_MARKET_ANALYSIS * 0.7)
                    line_items.append({
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {
                                'name': 'Analisi di Mercato (Offerta Speciale)',
                            },
                            'unit_amount': upsell_price,
                        },
                        'quantity': 1,
                    })
                
        elif request.documentType == "market-analysis":
            # Usa Price ID se configurato, altrimenti usa price_data
            if STRIPE_PRICE_MARKET_ANALYSIS:
                line_items.append({
                    'price': STRIPE_PRICE_MARKET_ANALYSIS,
                    'quantity': 1,
                })
            else:
                # Fallback a price_data se Price ID non configurato
                line_items.append({
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': 'Analisi di Mercato',
                        },
                        'unit_amount': PRICE_MARKET_ANALYSIS,
                    },
                    'quantity': 1,
                })
            
            # Se include upsell, aggiungi anche il business plan con sconto
            if request.includeUpsell:
                if STRIPE_PRICE_BUSINESS_PLAN_UPSELL:
                    line_items.append({
                        'price': STRIPE_PRICE_BUSINESS_PLAN_UPSELL,
                        'quantity': 1,
                    })
                else:
                    # Fallback a price_data con sconto del 30%
                    upsell_price = int(PRICE_BUSINESS_PLAN * 0.7)
                    line_items.append({
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {
                                'name': 'Business Plan Professionale (Offerta Speciale)',
                            },
                            'unit_amount': upsell_price,
                        },
                        'quantity': 1,
                    })
        else:
            raise HTTPException(status_code=400, detail="Tipo documento non valido")
        
        # Crea la sessione di checkout
        metadata = {
            'document_type': request.documentType
        }
        if request.includeUpsell:
            metadata['include_upsell'] = 'true'
            if request.documentType == "business-plan":
                metadata['upsell_type'] = 'market-analysis'
            else:
                metadata['upsell_type'] = 'business-plan'
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.successUrl + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancelUrl,
            metadata=metadata
        )
        
        return JSONResponse(content={
            "success": True,
            "sessionId": checkout_session.id,
            "url": checkout_session.url
        })
    except Exception as e:
        print(f"Errore creazione checkout session: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore creazione checkout: {str(e)}")

@app.post("/api/verify-payment")
async def verify_payment(request: VerifyPaymentRequest):
    """Verifica che il pagamento sia stato completato"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe non configurato")
    
    try:
        # Recupera la sessione di checkout
        session = stripe.checkout.Session.retrieve(request.sessionId)
        
        # Verifica che il pagamento sia completato
        if session.payment_status != 'paid':
            return JSONResponse(content={
                "success": False,
                "paid": False,
                "message": "Pagamento non completato"
            })
        
        # Verifica che il tipo di documento corrisponda
        if session.metadata.get('document_type') != request.documentType:
            return JSONResponse(content={
                "success": False,
                "paid": False,
                "message": "Tipo documento non corrispondente"
            })
        
        # Verifica se include upsell
        include_upsell = session.metadata.get('include_upsell') == 'true'
        upsell_type = session.metadata.get('upsell_type') if include_upsell else None
        
        return JSONResponse(content={
            "success": True,
            "paid": True,
            "sessionId": request.sessionId,
            "includeUpsell": include_upsell,
            "upsellType": upsell_type
        })
    except stripe.error.StripeError as e:
        print(f"Errore Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Errore verifica pagamento: {str(e)}")
    except Exception as e:
        print(f"Errore verifica pagamento: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@app.post("/api/generate-pdf")
async def generate_pdf(request: PDFRequest, user: dict = Depends(verify_firebase_token)):
    """Genera il PDF dal JSON del business plan (richiede autenticazione e pagamento verificato)"""
    try:
        # Verifica che ci sia sessionId nel request (opzionale per retrocompatibilità)
        # In produzione, dovresti sempre richiedere la verifica del pagamento
        session_id = request.businessPlanJson.get('_payment_session_id')
        
        if session_id and STRIPE_SECRET_KEY:
            # Verifica il pagamento
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status != 'paid':
                    raise HTTPException(status_code=402, detail="Pagamento non completato")
            except stripe.error.StripeError as e:
                raise HTTPException(status_code=402, detail=f"Errore verifica pagamento: {str(e)}")
        
        # Rimuovi il campo temporaneo dal JSON prima di generare il PDF
        pdf_json = {k: v for k, v in request.businessPlanJson.items() if k != '_payment_session_id'}
        
        pdf_path = await pdf_generator.create_pdf_from_json(pdf_json)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF non generato correttamente")
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="business-plan.pdf",
            headers={"Content-Disposition": "attachment; filename=business-plan.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Errore generazione PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-pdf-analysis")
async def generate_pdf_analysis(request: PDFAnalysisRequest, user: dict = Depends(verify_firebase_token)):
    """Genera PDF dall'analisi di mercato (richiede autenticazione e pagamento verificato)"""
    try:
        # Verifica che ci sia sessionId nel request (opzionale per retrocompatibilità)
        session_id = request.marketAnalysisJson.get('_payment_session_id')
        
        if session_id and STRIPE_SECRET_KEY:
            # Verifica il pagamento
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status != 'paid':
                    raise HTTPException(status_code=402, detail="Pagamento non completato")
            except stripe.error.StripeError as e:
                raise HTTPException(status_code=402, detail=f"Errore verifica pagamento: {str(e)}")
        
        # Rimuovi il campo temporaneo dal JSON prima di generare il PDF
        pdf_json = {k: v for k, v in request.marketAnalysisJson.items() if k != '_payment_session_id'}
        
        print("=== INIZIO GENERAZIONE PDF ANALISI DI MERCATO ===")
        output_path = await pdf_generator_analysis.create_pdf_from_market_analysis(pdf_json)
        
        if not Path(output_path).exists():
            raise HTTPException(status_code=500, detail="File PDF non generato correttamente")
        
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="analisi-mercato.pdf"
        )
    except HTTPException:
        raise
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
            model="gpt-3.5-turbo",  # Modello veloce per suggerimenti
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
