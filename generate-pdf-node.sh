#!/bin/bash
# Script per generare PDF usando Node.js (qualità professionale)
# Requisiti: Node.js e npm installati

echo "🚀 Generazione PDF professionale con Node.js..."
echo ""

# Verifica che Node.js sia installato
if ! command -v node &> /dev/null; then
    echo "❌ Node.js non è installato!"
    echo "Installa Node.js da: https://nodejs.org/"
    exit 1
fi

# Verifica che il file JSON esista
JSON_FILE="${1:-business-plan-TechStarts.json}"
OUTPUT_FILE="${2:-business-plan-TechStarts.pdf}"

if [ ! -f "$JSON_FILE" ]; then
    echo "❌ File $JSON_FILE non trovato!"
    echo "Usage: $0 [input.json] [output.pdf]"
    exit 1
fi

# Installa le dipendenze se necessario
if [ ! -d "node_modules" ]; then
    echo "📦 Installazione dipendenze..."
    npm install puppeteer marked
fi

# Genera il PDF
echo "📄 Generazione PDF in corso..."
echo "Input: $JSON_FILE"
echo "Output: $OUTPUT_FILE"
node generate.js "$JSON_FILE" "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✅ PDF generato con successo: $OUTPUT_FILE"
    echo "📄 Il PDF è di qualità professionale con grafici e formattazione perfetta!"
else
    echo "❌ Errore nella generazione del PDF"
    exit 1
fi
