import json
import re
from typing import Dict, List, Any, Tuple

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

def count_words(text: str) -> int:
    """Conta le parole in un testo"""
    if not text or not isinstance(text, str):
        return 0
    # Rimuove HTML tags se presenti e conta le parole
    text_clean = re.sub(r'<[^>]+>', '', text)
    words = re.findall(r'\b\w+\b', text_clean)
    return len(words)

def validate_market_analysis_word_count(market_analysis_json: dict) -> Tuple[bool, Dict[str, Any]]:
    """
    Valida che l'analisi di mercato rispetti i requisiti minimi di parole.
    Restituisce (is_valid, validation_report)
    """
    report = {
        "valid": True,
        "warnings": [],
        "details": {}
    }
    
    # Requisiti minimi
    min_requirements = {
        "executive_summary.sintesi": 600,
        "market_size.tam.descrizione": 200,
        "market_size.sam.descrizione": 200,
        "market_size.som.descrizione": 200,
        "market_size.trend_crescita.descrizione": 150,
        "market_size.segmentazione.geografica": 75,
        "market_size.segmentazione.per_prodotto": 75,
        "market_size.segmentazione.per_canale": 75,
        "competitor_analysis.quote_mercato": 250,
        "competitor_analysis.posizionamento": 250,
        "competitor_analysis.punti_forza_debolezza": 500,
        "swot_analysis.strengths": 200,  # Totale per categoria
        "swot_analysis.weaknesses": 200,
        "swot_analysis.opportunities": 200,
        "swot_analysis.threats": 200,
        "positioning_strategy.posizionamento_raccomandato": 200,
    }
    
    # Valida executive_summary
    exec_summary = market_analysis_json.get("executive_summary", {})
    sintesi = exec_summary.get("sintesi", "")
    sintesi_words = count_words(sintesi)
    report["details"]["executive_summary.sintesi"] = {
        "words": sintesi_words,
        "required": 600,
        "valid": sintesi_words >= 600
    }
    if sintesi_words < 600:
        report["valid"] = False
        report["warnings"].append(f"executive_summary.sintesi: {sintesi_words} parole (minimo 600)")
    
    # Valida market_size
    market_size = market_analysis_json.get("market_size", {})
    for field in ["tam", "sam", "som"]:
        if field in market_size:
            desc = market_size[field].get("descrizione", "")
            words = count_words(desc)
            key = f"market_size.{field}.descrizione"
            report["details"][key] = {
                "words": words,
                "required": 200,
                "valid": words >= 200
            }
            if words < 200:
                report["valid"] = False
                report["warnings"].append(f"{key}: {words} parole (minimo 200)")
    
    if "trend_crescita" in market_size:
        desc = market_size["trend_crescita"].get("descrizione", "")
        words = count_words(desc)
        key = "market_size.trend_crescita.descrizione"
        report["details"][key] = {
            "words": words,
            "required": 150,
            "valid": words >= 150
        }
        if words < 150:
            report["valid"] = False
            report["warnings"].append(f"{key}: {words} parole (minimo 150)")
    
    if "segmentazione" in market_size:
        seg = market_size["segmentazione"]
        for field in ["geografica", "per_prodotto", "per_canale"]:
            if field in seg:
                text = seg[field]
                words = count_words(text)
                key = f"market_size.segmentazione.{field}"
                report["details"][key] = {
                    "words": words,
                    "required": 75,
                    "valid": words >= 75
                }
                if words < 75:
                    report["valid"] = False
                    report["warnings"].append(f"{key}: {words} parole (minimo 75)")
    
    # Valida competitor_analysis
    comp_analysis = market_analysis_json.get("competitor_analysis", {})
    for field in ["quote_mercato", "posizionamento", "punti_forza_debolezza"]:
        if field in comp_analysis:
            text = comp_analysis[field]
            words = count_words(text)
            key = f"competitor_analysis.{field}"
            required = 250 if field != "punti_forza_debolezza" else 500
            report["details"][key] = {
                "words": words,
                "required": required,
                "valid": words >= required
            }
            if words < required:
                report["valid"] = False
                report["warnings"].append(f"{key}: {words} parole (minimo {required})")
    
    # Valida swot_analysis
    swot = market_analysis_json.get("swot_analysis", {})
    for category in ["strengths", "weaknesses", "opportunities", "threats"]:
        if category in swot:
            items = swot[category]
            total_words = sum(count_words(item.get("descrizione", "")) for item in items if isinstance(item, dict))
            key = f"swot_analysis.{category}"
            report["details"][key] = {
                "words": total_words,
                "required": 200,
                "valid": total_words >= 200
            }
            if total_words < 200:
                report["valid"] = False
                report["warnings"].append(f"{key}: {total_words} parole totali (minimo 200)")
    
    # Valida positioning_strategy
    positioning = market_analysis_json.get("positioning_strategy", {})
    if "posizionamento_raccomandato" in positioning:
        text = positioning["posizionamento_raccomandato"]
        words = count_words(text)
        key = "positioning_strategy.posizionamento_raccomandato"
        report["details"][key] = {
            "words": words,
            "required": 200,
            "valid": words >= 200
        }
        if words < 200:
            report["valid"] = False
            report["warnings"].append(f"{key}: {words} parole (minimo 200)")
    
    return report["valid"], report
