import json
from typing import Dict, List, Any

def prepare_user_input_json(form_data: dict) -> str:
    """Prepara i dati utente in formato JSON (equivalente a prepareUserInputJSON in script.js)"""
    user_data = {}
    
    # Mappa settori
    industry_map = {
        'ristorazione': 'Ristorazione e Food & Beverage',
        'tech': 'Tecnologia e Software',
        'retail': 'Vendita al Dettaglio',
        'ecommerce': 'E-commerce',
        'servizi': 'Servizi Professionali',
        'manufacturing': 'Produzione e Manifattura',
        'healthcare': 'Sanità e Benessere',
        'education': 'Educazione e Formazione',
        'realestate': 'Immobiliare',
        'finance': 'Finanza e Investimenti',
        'altro': 'Altro'
    }
    
    # Gestione settore
    if form_data.get('industry'):
        user_data['settore'] = industry_map.get(form_data['industry'], form_data['industry'])
    
    # Mappa i campi del form ai campi del JSON
    field_mapping = {
        'companyName': 'nome_azienda',
        'location': 'localita',
        'foundingYear': 'anno_fondazione',
        'description': 'descrizione',
        'businessModel': 'modello_business',
        'targetMarket': 'mercato_target',
        'competitiveAdvantage': 'vantaggio_competitivo',
        'pricing': 'strategia_pricing',
        'employees': 'numero_dipendenti',
        'revenue': 'fatturato_attuale_previsto',
        'costs': 'costi_operativi',
        'initialInvestment': 'investimento_iniziale',
        'fundingNeeds': 'esigenze_finanziamento',
        'channels': 'canali_vendita',
        'goals': 'obiettivi'
    }
    
    # Mappa gli altri campi
    for form_key, json_key in field_mapping.items():
        if form_key in form_data and form_data[form_key]:
            value = form_data[form_key]
            
            # Conversione tipi
            if form_key == 'foundingYear' or form_key == 'employees':
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    continue
            elif form_key in ['revenue', 'initialInvestment']:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue
            elif form_key == 'targetMarket' and value == 'AUTO_DETECT':
                value = '[DA IDENTIFICARE AUTOMATICAMENTE IN BASE ALLE INFORMAZIONI FORNITE]'
            
            user_data[json_key] = value
    
    return json.dumps(user_data, ensure_ascii=False, indent=2)

def build_messages_from_prompt(prompt_config: dict, user_data_json: str, horizon_months: int) -> List[Dict]:
    """Costruisce i messaggi per OpenAI dal prompt config"""
    messages = []
    
    for msg in prompt_config["input"]:
        content_parts = []
        for content_item in msg["content"]:
            if content_item["type"] == "text":
                text = content_item["text"]
                # Sostituisci i placeholder
                text = text.replace("{{USER_DATA_JSON}}", user_data_json)
                text = text.replace("{{HORIZON_MONTHS}}", str(horizon_months))
                content_parts.append(text)
        
        messages.append({
            "role": msg["role"],
            "content": "".join(content_parts)
        })
    
    return messages

def sanitize_italia_regime_note(business_plan_json: dict):
    """Sanitizza il campo regime_fiscale_note (equivalente a sanitizeItaliaRegimeNote)"""
    it = business_plan_json.get("data", {}).get("italia")
    if not it:
        return
    
    if isinstance(it.get("regime_fiscale_note"), list):
        it["regime_fiscale_note"] = [
            x for x in it["regime_fiscale_note"]
            if isinstance(x, str) and len(x.strip()) >= 8 and "adempimenti_checklist" not in x
        ]
    elif isinstance(it.get("regime_fiscale_note"), str):
        it["regime_fiscale_note"] = [it["regime_fiscale_note"].strip()] if it["regime_fiscale_note"].strip() else []
    else:
        it["regime_fiscale_note"] = []
