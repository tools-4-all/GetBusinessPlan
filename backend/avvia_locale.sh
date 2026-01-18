#!/bin/bash
# Avvia il backend in locale sulla porta 8000.
# Richiede: backend/.env con OPENAI_API_KEY configurata

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
    echo "❌ File .env non trovato in backend/"
    echo ""
    echo "Crea backend/.env con la tua chiave API:"
    echo "  OPENAI_API_KEY=<tua-chiave-api>"
    echo ""
    echo "Puoi copiare .env.example:"
    echo "  cp .env.example .env"
    echo "Poi modifica .env e inserisci la chiave API."
    exit 1
fi

if ! grep -q 'OPENAI_API_KEY=' .env 2>/dev/null; then
    echo "⚠️  In .env OPENAI_API_KEY non è impostata"
    echo "   Modifica backend/.env e inserisci la tua chiave API."
    exit 1
fi

echo "Avvio backend su http://localhost:8000 ..."
echo "Ferma con Ctrl+C. Per test: curl http://localhost:8000/health"
echo ""
exec uvicorn app:app --reload --port 8000
