# 🔑 Come Configurare la Chiave API OpenAI su Render

## Problema
Se vedi l'errore `401 - Incorrect API key provided`, significa che la chiave API di OpenAI non è configurata correttamente su Render.

## Soluzione

### 1. Ottieni la tua chiave API OpenAI
1. Vai su https://platform.openai.com/account/api-keys
2. Accedi al tuo account OpenAI
3. Clicca su "Create new secret key"
4. Copia la chiave (inizia con `sk-...`)
   - ⚠️ **IMPORTANTE**: Salvala subito, non potrai vederla di nuovo!

### 2. Configura la chiave su Render

#### Opzione A: Tramite Dashboard Render (Consigliato)
1. Vai su https://dashboard.render.com
2. Seleziona il servizio `getbusinessplan-api`
3. Vai alla sezione **"Environment"** (nel menu laterale)
4. Cerca la variabile `OPENAI_API_KEY`
5. Se non esiste, clicca su **"Add Environment Variable"**
6. Inserisci:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: Incolla la tua chiave API (es. `sk-proj-...`)
7. Clicca su **"Save Changes"**
8. Render riavvierà automaticamente il servizio

#### Opzione B: Tramite Render CLI
```bash
render env:set OPENAI_API_KEY=sk-proj-tua-chiave-qui --service getbusinessplan-api
```

### 3. Verifica la configurazione

Dopo aver configurato la chiave, testa l'endpoint:

```bash
# Test generale
curl https://getbusinessplan.onrender.com/api/test

# Test OpenAI (verifica che la chiave funzioni)
curl https://getbusinessplan.onrender.com/api/test-openai
```

Se tutto funziona, vedrai:
```json
{
  "status": "ok",
  "openai_working": true,
  "response": "OK"
}
```

### 4. Riavvia il servizio (se necessario)

Se dopo aver configurato la chiave non funziona ancora:
1. Vai su https://dashboard.render.com
2. Seleziona il servizio `getbusinessplan-api`
3. Clicca su **"Manual Deploy"** → **"Deploy latest commit"**

## ⚠️ Note Importanti

- **Non committare mai la chiave API nel codice!**
- La chiave è già nel `.gitignore`
- Su Render, usa sempre le variabili d'ambiente
- Se la chiave è scaduta o revocata, devi crearne una nuova

## 🔍 Debug

Se continui ad avere problemi:

1. **Verifica che la chiave sia corretta:**
   - Deve iniziare con `sk-`
   - Non deve avere spazi o caratteri extra
   - Deve essere completa (non troncata)

2. **Controlla i log su Render:**
   - Dashboard → Servizio → Logs
   - Cerca errori relativi a `OPENAI_API_KEY`

3. **Testa la chiave localmente:**
   ```bash
   # Crea un file .env nella cartella backend/
   echo "OPENAI_API_KEY=sk-proj-tua-chiave-qui" > backend/.env
   
   # Testa localmente
   cd backend
   python3 -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print(client.chat.completions.create(model='gpt-3.5-turbo', messages=[{'role': 'user', 'content': 'test'}]).choices[0].message.content)"
   ```

## 📝 Modello OpenAI

Nota: Il modello `gpt-5-nano-2025-08-07` nel `prompt.json` potrebbe non esistere. Considera di cambiarlo con:
- `gpt-4o-mini` (consigliato, veloce ed economico)
- `gpt-4o` (più potente)
- `gpt-4-turbo` (alternativa)
