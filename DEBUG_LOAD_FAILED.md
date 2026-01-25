# 🔧 Diagnosi Errore "Load failed" nel Pagamento

**Errore**: `TypeError: Load failed`  
**Data**: 25 gennaio 2026  
**Frontend**: https://seedwise.it.com  
**Backend**: https://getbusinessplan.onrender.com

---

## 🔍 Cause Possibili

### **1. Problema di CORS** (Probabilità: MEDIA)
- Frontend su `seedwise.it.com`
- Backend su `getbusinessplan.onrender.com`
- CORS è configurato per `*`, quindi dovrebbe funzionare

**Test**: Apri F12 > Network > Network tab > Prova pagamento
- Cerca richiesta `/api/create-checkout-session`
- Guarda Response headers per CORS

### **2. Problema di Connessione di Rete** (Probabilità: MEDIA)
- ISP blocca connessione a `getbusinessplan.onrender.com`
- Firewall aziendale blocca la richiesta
- Problema di DNS

**Test**: Apri terminale:
```bash
curl https://getbusinessplan.onrender.com/health
# Deve restituire: {"status": "healthy"}
```

### **3. HTTPS/HTTP Mismatch** (Probabilità: BASSA)
- Frontend è HTTPS (`seedwise.it.com`)
- Backend potrebbe non avere HTTPS correttamente configurato

**Test**: Verifica che sia HTTPS:
```bash
curl -I https://getbusinessplan.onrender.com/health
# Deve mostrare: HTTP/2 200 (non 301 redirect)
```

### **4. Frontend Sta Usando URL Sbagliato** (Probabilità: MEDIA)
- `script.js` ha URL corretto (`getbusinessplan.onrender.com`)
- Ma HTML potrebbe sovrascrivere con URL diverso

**Test**: Apri F12 > Console > Digita:
```javascript
console.log('API_BASE_URL:', window.API_BASE_URL || 'NOT SET')
console.log('API_BASE_URL from script:', API_BASE_URL)
```

---

## ✅ Soluzione: Test di Connectivity

### **Step 1: Verifica Server è Online**
```bash
curl https://getbusinessplan.onrender.com/health
# Output: {"status": "healthy"}
```
✅ Server è online e raggiungibile

### **Step 2: Verifica CORS**
```bash
curl -H "Origin: https://seedwise.it.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -X OPTIONS \
  https://getbusinessplan.onrender.com/api/create-checkout-session -v

# Guarda headers:
# Access-Control-Allow-Origin: * ✅
# Access-Control-Allow-Methods: * ✅
# Access-Control-Allow-Headers: * ✅
```

### **Step 3: Verifica Health Check**
```bash
curl https://getbusinessplan.onrender.com/api/health-full | jq .
# Deve mostrare: "payment_ready": true
```

### **Step 4: Debug da Browser Console (F12)**

Apri F12 e esegui nel Console tab:

```javascript
// Test 1: Verifica URL impostato
console.log('API_BASE_URL:', window.API_BASE_URL || API_BASE_URL)

// Test 2: Prova fetch manuale
fetch('https://getbusinessplan.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log('✅ Fetch OK:', d))
  .catch(e => console.error('❌ Fetch fallito:', e))

// Test 3: Prova con CORS headers
fetch('https://getbusinessplan.onrender.com/api/health-full', {
  method: 'GET',
  headers: {
    'Origin': window.location.origin
  }
})
  .then(r => r.json())
  .then(d => console.log('✅ Health check OK:', d))
  .catch(e => console.error('❌ Health check fallito:', e))
```

---

## 🛠️ Soluzioni

### **Se il Test di Connectivity Fallisce:**

**Opzione A: Aggiornare CORS nel Backend**
```python
# In backend/app.py, sostituire:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seedwise.it.com",
        "https://www.seedwise.it.com",
        "https://getbusinessplan.onrender.com",
        "*"  # Permetti tutto per debugging
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Opzione B: Aggiungere Endpoint Proxy nel Frontend**
Se il problema persiste, aggiungere un endpoint proxy su `seedwise.it.com` che inoltri le richieste a `getbusinessplan.onrender.com`.

### **Se il Test di Connectivity Funziona:**

Il problema potrebbe essere nel codice JavaScript. Verificare:

1. **Timeout troppo breve?**
   - Aumentare da 120 secondi a 180 secondi
   - Render cold start potrebbe richiedere tempo

2. **AbortController non funziona?**
   - Rimuovere `signal` dal fetch per debugging

3. **Network throttling attivo?**
   - DevTools > Network > Disabilita throttling

---

## 📋 Debug Checklist

- [ ] Server online: `curl https://getbusinessplan.onrender.com/health` = 200 OK
- [ ] CORS funziona: Response ha `Access-Control-Allow-Origin: *`
- [ ] Health check: `/api/health-full` ritorna status ok
- [ ] URL corretto: F12 Console mostra `seedwise.it.com` non in API_BASE_URL
- [ ] Firebase inizializzato: F12 Console non ha errori auth
- [ ] Network tab: Vedi richiesta `/api/create-checkout-session` e status
- [ ] No throttling: DevTools > Network > Throttling = No throttling

---

## 🔧 Miglioramenti da Fare

### **PRIORITY 1: Migliorare Error Handling per "Load failed"**

Nel `script.js`, aggiungere handling specifico:

```javascript
// In fetchWithRetry, aggiungere:
if (fetchError.message === 'Load failed') {
    console.error('Load failed - Possibili cause:');
    console.error('1. Server non raggiungibile');
    console.error('2. Problema CORS');
    console.error('3. Firewall blocca la connessione');
    console.error('4. ISP blocca il dominio');
    console.error('5. Certificato HTTPS non valido');
}
```

### **PRIORITY 2: Aggiungere Endpoint Diagnostico**

Nel `backend/app.py`, aggiungere:

```python
@app.get("/api/cors-test")
async def cors_test():
    """Test CORS - Restituisce informazioni su CORS"""
    return {
        "cors_enabled": True,
        "test_origins": [
            "https://seedwise.it.com",
            "https://getbusinessplan.onrender.com"
        ]
    }
```

### **PRIORITY 3: Logging Migliore**

Aggiungere logging dettagliato quando fetch fallisce:

```javascript
console.log('Request URL:', `${API_BASE_URL}/api/create-checkout-session`);
console.log('Request Origin:', window.location.origin);
console.log('User Agent:', navigator.userAgent);
console.log('Online Status:', navigator.onLine);
```

---

## 📞 Prossimi Passi

1. **Esegui i test di connectivity** sopra
2. **Guarda il Network tab** di F12 per vedere lo status della richiesta
3. **Se vedi CORS error**: Aggiornare CORS nel backend
4. **Se vedi connection timeout**: Aumentare timeout o verificare firewall
5. **Se tutto OK ma ancora fallisce**: Contattami con risultati test

---

**Nota**: L'errore "Load failed" è generico. Potrebbe essere qualsiasi cosa da CORS a connessione di rete. Segui i test sopra per identificare il vero problema.
