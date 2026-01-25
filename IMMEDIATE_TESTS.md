# 🧪 Test Immediati per Risolvere "Load failed"

**Errore**: `TypeError: Load failed`  
**Tempo**: 5 minuti per fare tutti i test

---

## ✅ Test 1: Server Online? (1 minuto)

### Apri terminale e esegui:
```bash
curl -I https://getbusinessplan.onrender.com/health
```

### Risultato Atteso:
```
HTTP/2 200
...
{"status": "healthy"}
```

### Se Vedi:
- ✅ **HTTP/2 200** → Server è online
- ❌ **Connection refused** → Server offline
- ❌ **Timeout** → Server non risponde

---

## ✅ Test 2: CORS Funziona? (1 minuto)

### Apri terminale e esegui:
```bash
curl -s https://getbusinessplan.onrender.com/api/cors-test | jq .
```

### Risultato Atteso:
```json
{
  "status": "ok",
  "cors_enabled": true,
  "message": "CORS è abilitato"
}
```

### Se Vedi:
- ✅ **"cors_enabled": true** → CORS OK
- ❌ **Access-Control-Allow-Origin missing** → CORS problema
- ❌ **Timeout** → Server non raggiungibile

---

## ✅ Test 3: Da Browser Console (2 minuti)

### Apri il sito e premi F12 per aprire Developer Tools

### Vai al tab "Console"

### Copia e incolla questo codice:
```javascript
// Test 1: Verifica URL API
console.log('API_BASE_URL:', window.API_BASE_URL || API_BASE_URL)

// Test 2: Prova fetch semplice
console.log('\n🧪 Test CORS...');
fetch('https://getbusinessplan.onrender.com/api/cors-test')
  .then(r => {
    console.log('Status:', r.status);
    console.log('Headers:', {
      'Content-Type': r.headers.get('Content-Type'),
      'CORS-Allow-Origin': r.headers.get('Access-Control-Allow-Origin')
    });
    return r.json();
  })
  .then(d => console.log('✅ CORS OK:', d))
  .catch(e => console.error('❌ CORS FALLITO:', e.message))
```

### Guarda l'output:
```
API_BASE_URL: https://getbusinessplan.onrender.com
Status: 200
Headers: { Content-Type: 'application/json', CORS-Allow-Origin: '*' }
✅ CORS OK: { status: 'ok', cors_enabled: true }
```

### Se Vedi:
- ✅ **Status 200 + CORS OK** → Connessione funziona
- ❌ **Status 0** → CORS bloccato dal browser
- ❌ **Network error** → Connessione fallita
- ❌ **Timeout** → Server troppo lento

---

## ✅ Test 4: Network Tab (1 minuto)

### Nel sito, apri F12 > Network tab

### Prova a fare il pagamento

### Cerca la richiesta `/api/create-checkout-session`

### Guarda il Status:
- ✅ **200** → Request OK, problema probabilmente nel processing
- ❌ **0** → CORS bloccato
- ❌ **503** → Server in maintenance
- ❌ **Timeout** → Server lento
- ❌ **CORS error in console** → CORS problema

---

## 🎯 Interpretazione Risultati

### **Tutti i Test Passano (✅✅✅✅)?**
→ Il problema non è di connessione. Potrebbe essere:
- Cache del browser non aggiornata
- Token Firebase scaduto
- Bug nel pagamento stesso

**Soluzione**:
1. Hard refresh: `Ctrl+Shift+R` (Windows) o `Cmd+Shift+R` (Mac)
2. Svuota cache: F12 > Right-click refresh > "Empty cache and hard refresh"
3. Prova da Incognito: `Ctrl+Shift+N`

### **Test 1 o 2 Fallisce (❌)?**
→ Problema di server o rete

**Soluzione**:
1. Verifica Internet: Apri google.com - funziona?
2. Attendi 5 minuti: Server Render potrebbe essere in cold start
3. Prova da un'altra rete: WiFi → Mobile data

### **Test 3 Fallisce ma 1-2 Passano (❌)?**
→ Possibile problema CORS da browser, ma è raro

**Soluzione**:
1. Prova da Incognito
2. Svuota cache estensioni browser
3. Disabilita VPN se la usi

---

## 📋 Checklist Test

- [ ] Test 1: Server online? (curl /health)
- [ ] Test 2: CORS funziona? (curl /api/cors-test)
- [ ] Test 3: Browser console funziona? (fetch test)
- [ ] Test 4: Network tab mostra status 200? 

---

## 🔄 Se Vuoi Testare il Pagamento Completo

### Nel Browser Console:
```javascript
// Simula quello che fa il pagamento
const testPayment = async () => {
  try {
    const response = await fetch('https://getbusinessplan.onrender.com/api/health-full', {
      method: 'GET'
    });
    const data = await response.json();
    console.log('✅ Health check:', data);
    
    if (data.payment_ready) {
      console.log('✅ Pagamento PRONTO');
    } else {
      console.log('❌ Pagamento NON pronto:', data.warnings);
    }
  } catch (e) {
    console.error('❌ Errore:', e.message);
  }
};

testPayment();
```

---

## 📞 Raccogli Risultati Test

Se il problema persiste, raccogli:

1. **Output Test 1**: `curl -I https://getbusinessplan.onrender.com/health`
2. **Output Test 2**: `curl https://getbusinessplan.onrender.com/api/cors-test`
3. **Screenshot Console**: F12 > Console dopo aver eseguito codice Test 3
4. **Screenshot Network Tab**: F12 > Network > Richiesta fallita
5. **Qual è il tuo dominio frontend**: (es: seedwise.it.com)
6. **La tua rete**: (ISP, WiFi, Ufficio, Mobile)

Invia tutto a supporto per debug avanzato.

---

*Tempo totale per tutti i test: ~5 minuti*

Se tutti i test passano ma pagamento ancora fallisce, contatta supporto con i risultati.
