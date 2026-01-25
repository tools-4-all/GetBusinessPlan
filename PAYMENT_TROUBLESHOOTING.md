# Troubleshooting: Errore "Impossibile connettersi al server" nel Pagamento

## 🎯 Passi per Risolvere il Problema

### **STEP 1: Verificare la Configurazione Server (5 minuti)**

Apri il browser e accedi a questi endpoint:

#### A. Health Check Completo
```
https://getbusinessplan.onrender.com/api/health-full
```

**Cosa cercare:**
- `"status": "ok"` - Tutto OK
- `"status": "warning"` - Ci sono problemi (vedi sezione `warnings`)
- `"payment_ready": true` - Pagamento pronto
- `"payment_ready": false` - Manca una configurazione critica

**Se vedi problemi**, vai alla sezione [Soluzioni per Configurazione](#soluzioni-per-configurazione)

#### B. Test Stripe
```
https://getbusinessplan.onrender.com/api/test
```

**Cosa cercare:**
- `"stripe_configured": true` - Stripe è configurato
- `"stripe_configured": false` - STRIPE_SECRET_KEY manca!

#### C. Test Firebase
```
https://getbusinessplan.onrender.com/api/test-firebase
```

**Cosa cercare:**
- `"success": true` - Firebase OK
- `"success": false` - Firebase non inizializzato

#### D. Test OpenAI
```
https://getbusinessplan.onrender.com/api/test-openai
```

**Cosa cercare:**
- `"openai_working": true` - OpenAI OK
- `"is_auth_error": true` - API key non valida

---

### **STEP 2: Verificare la Connessione Internet (2 minuti)**

Nel browser, apri la **Developer Console** (F12):

1. Vai alla tab **Network**
2. Prova a fare il pagamento
3. Guarda le richieste:
   - Cerca `/api/create-checkout-session`
   - Guarda **Status Code**: deve essere 200
   - Se è **500** → Vai a [Errore 500](#errore-500-server-interno)
   - Se è **401** → Vai a [Errore 401](#errore-401-autenticazione)
   - Se c'è **❌ ERROR** → Connessione internet problema

---

### **STEP 3: Leggere il Messaggio di Errore nel Browser (1 minuto)**

L'app ora mostra messaggi più specifici:

| Messaggio | Causa | Soluzione |
|-----------|-------|----------|
| **⏱️ TIMEOUT** | Server in sleep (cold start) | Attendi 30 sec, riprova |
| **❌ Impossibile connettersi** | Internet offline o server offline | Verifica connessione internet e URL |
| **❌ Autenticazione fallita (401)** | Token Firebase non valido | Logout → Login di nuovo |
| **❌ Errore del server (500)** | Problema interno del server | Contatta supporto con codice errore |
| **⚠️ Problemi di configurazione** | Manca Stripe/Firebase/OpenAI | Configurare variabili d'ambiente |

---

## 🔧 Soluzioni per Configurazione

### **SOLUZIONE 1: Stripe non Configurato**

Se vedi "STRIPE_SECRET_KEY non configurata":

1. Accedi a [Render Dashboard](https://dashboard.render.com)
2. Vai al servizio "getbusinessplan"
3. Clicca su "Environment"
4. Verifica che esista: `STRIPE_SECRET_KEY` con un valore che inizia con `sk_live_` o `sk_test_`
5. Se non esiste:
   - Vai su [Stripe Dashboard](https://dashboard.stripe.com)
   - Seleziona la API key dal tab "Developers" > "API Keys"
   - Copia la "Secret key"
   - Torna su Render e aggiungi la variabile

```bash
# Debug locale: verifica con questo comando
echo $STRIPE_SECRET_KEY
```

### **SOLUZIONE 2: Firebase non Configurato**

Se vedi "Firebase Admin non inizializzato":

1. Accedi a [Render Dashboard](https://dashboard.render.com)
2. Vai al servizio "getbusinessplan"
3. Clicca su "Environment"
4. Verifica che esista: `FIREBASE_CREDENTIALS_JSON` (dovrebbe essere una stringa JSON)

Se non esiste:
1. Vai su [Firebase Console](https://console.firebase.google.com)
2. Seleziona il progetto
3. Vai su "Project Settings" > "Service Accounts"
4. Clicca "Generate New Private Key"
5. Copia il contenuto del JSON
6. Aggiungi la variabile su Render: `FIREBASE_CREDENTIALS_JSON` = "{content}"

**Attenzione**: Deve essere **una riga unica** senza newline!

```bash
# Verifica che Firebase sia configurato
curl https://getbusinessplan.onrender.com/api/test-firebase
```

### **SOLUZIONE 3: OpenAI non Configurato**

Se vedi "OPENAI_API_KEY non configurata":

1. Accedi a [Render Dashboard](https://dashboard.render.com)
2. Vai al servizio "getbusinessplan"
3. Clicca su "Environment"
4. Verifica che esista: `OPENAI_API_KEY` con un valore che inizia con `sk-`

Se non esiste:
1. Vai su [OpenAI Platform](https://platform.openai.com)
2. Vai su "API keys"
3. Crea una nuova key
4. Copia e aggiungi su Render

```bash
# Verifica che OpenAI sia configurato
curl https://getbusinessplan.onrender.com/api/test-openai
```

---

## 🐛 Debug Errori Specifici

### **Errore 500 (Server Interno)**

```
SERVER_ERROR_500: [Dettaglio specifico]
```

**Cause comuni:**
1. Stripe non configurato
2. Token Firebase scaduto
3. Limite API raggiunto

**Debug:**
```bash
# Visualizza i log del server
# 1. Vai su Render Dashboard
# 2. Seleziona il servizio
# 3. Vai su "Logs"
# 4. Cerca messaggi di errore

# O esegui il test su Render
curl -v https://getbusinessplan.onrender.com/api/test
```

### **Errore 401 (Autenticazione)**

```
AUTH_TOKEN_401: Token non valido
```

**Cause:**
1. Token Firebase scaduto
2. Firebase Admin non inizializzato
3. Project ID mismatch

**Soluzione:**
1. Logout dal sito
2. Login di nuovo
3. Se il problema persiste: Svuota cache browser (Ctrl+Shift+Del)

### **TIMEOUT (120 secondi)**

```
TIMEOUT_120S: Il server non risponde
```

**Cause:**
1. Server Render.com in sleep (cold start)
2. Connessione internet lenta
3. Server sovraccarico

**Soluzioni:**
1. Attendi 30 secondi che il server si avvii
2. Verifica la connessione internet (speed.cloudflare.com)
3. Riprova il pagamento
4. Se il problema persiste, contatta il supporto

---

## 📋 Checklist di Debugging

- [ ] Ho verificato `/api/health-full` e vede tutto OK?
- [ ] Ho verificato la tab Network della console e il status è 200?
- [ ] Ho fatto logout/login di recente?
- [ ] La mia connessione internet funziona (prova con google.com)?
- [ ] È la prima volta che accedo oggi (potrebbe essere cold start)?
- [ ] Ho atteso almeno 30 secondi dal primo tentativo?
- [ ] Ho svuotato la cache del browser?
- [ ] Ho provato da un browser diverso?

---

## 🆘 Contatti Supporto

Se il problema persiste dopo questi passi, raccogli questi dati:

1. **Screenshot dell'errore** - Mostra esattamente cosa vedi
2. **Codice errore** - Quello visualizzato nel messaggio (es: TIMEOUT_120S)
3. **Tab Network** - Uno screenshot della console Developer
4. **Link dell'endpoint diagnostico** - Il JSON da `/api/health-full`
5. **Ora dell'errore** - Quando è accaduto (per cercare nei log)

Invia tutto a: **[supporto@getbusinessplan.com]**

---

## 🔍 Diagnostica Avanzata

### **Per Sviluppatori:**

#### 1. Verificare i Log del Backend (Render)

```bash
# Nel terminale (se hai SSH su Render)
ssh user@getbusinessplan.onrender.com
tail -f /var/log/app.log | grep -i "stripe\|firebase\|payment"
```

#### 2. Testare l'API localmente

```bash
# Test checkout session
curl -X POST http://localhost:8000/api/create-checkout-session \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"documentType":"market-analysis","successUrl":"http://localhost:3000/success","cancelUrl":"http://localhost:3000/cancel"}'
```

#### 3. Verificare le Variabili d'Ambiente

```bash
# Nel backend Python
import os
print("STRIPE_SECRET_KEY:", "✅" if os.getenv("STRIPE_SECRET_KEY") else "❌")
print("FIREBASE_CREDENTIALS_JSON:", "✅" if os.getenv("FIREBASE_CREDENTIALS_JSON") else "❌")
print("OPENAI_API_KEY:", "✅" if os.getenv("OPENAI_API_KEY") else "❌")
```

#### 4. Test di Connessione a Stripe

```python
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

try:
    # Verifica che la key sia valida
    stripe.Account.retrieve()
    print("✅ Stripe connesso correttamente")
except stripe.error.AuthenticationError:
    print("❌ Stripe key non valida")
except Exception as e:
    print(f"❌ Errore Stripe: {e}")
```

---

## ✅ Se tutto funziona:

Congratulazioni! Il pagamento dovrebbe funzionare. Se hai ancora problemi:

1. Verifica che l'URL di Stripe Checkout si apra correttamente
2. Verifica che il pagamento sia stato completato su Stripe Dashboard
3. Verifica che l'email di conferma sia arrivata

Se nulla funziona, contatta il supporto con i dati di debug sopra.
