# 🔧 Quick Fix: Errore "Load failed" nel Pagamento

**Errore Ricevuto**: `TypeError: Load failed`  
**Causa**: Frontend su `seedwise.it.com` non riesce a connettersi a backend su `getbusinessplan.onrender.com`  
**Soluzione**: Vedi sotto

---

## ⚡ Quick Test (2 minuti)

### Test 1: Server Online?
```bash
curl https://getbusinessplan.onrender.com/health
```
✅ Deve mostrare: `{"status": "healthy"}`

### Test 2: CORS Funziona?
```bash
curl https://getbusinessplan.onrender.com/api/cors-test
```
✅ Deve mostrare: `{"status": "ok", "cors_enabled": true}`

### Test 3: Da Browser Console (F12)
```javascript
// Apri F12 Console e esegui:
fetch('https://getbusinessplan.onrender.com/api/cors-test')
  .then(r => r.json())
  .then(d => console.log('✅ OK:', d))
  .catch(e => console.error('❌ FAIL:', e.message))
```

---

## 🛠️ Soluzioni

### **Se tutti i test passano ma pagamento ancora fallisce:**

#### **Soluzione 1: Hard Refresh Browser**
```
Windows: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

#### **Soluzione 2: Svuota Cache**
1. Apri DevTools (F12)
2. Right-click su refresh button
3. Seleziona "Empty cache and hard refresh"

#### **Soluzione 3: Prova da Incognito**
- Apri window incognita/privata (Ctrl+Shift+N)
- Accedi di nuovo
- Prova pagamento

#### **Soluzione 4: Cambia Rete**
- Prova da WiFi diversa
- Prova da mobile data
- Se funziona, è un problema di firewall/ISP

### **Se i test falliscono:**

#### **Problema: "Load failed" persiste**
Possibili cause:
1. **Firewall blocca `getbusinessplan.onrender.com`**
   - Soluzione: Usare VPN o cambiare rete
   
2. **CORS ancora non funziona**
   - Soluzione: Contattami con risultati test

3. **Certificato HTTPS problematico**
   - Soluzione: Verifica che sia HTTPS (non HTTP)

---

## 📋 Miglioramenti Implementati

Ho fatto questi miglioramenti al codice:

1. **✅ Endpoint `/api/cors-test`** - Per testare CORS
2. **✅ Dettagli diagnostici migliori** - Quando "Load failed" accade
3. **✅ Logging dettagliato** - Origin, URL, Online status
4. **✅ Messaggi di errore HTML formattati** - Con possibili cause

---

## 📞 Se il Problema Persiste

Raccogli questi dati e contatta il supporto:

1. **Output di**: `curl https://getbusinessplan.onrender.com/health`
2. **Output di**: `curl https://getbusinessplan.onrender.com/api/cors-test`
3. **Screenshot di F12 Network tab** mostrando la richiesta che fallisce
4. **Il tuo dominio frontend** (es: seedwise.it.com)
5. **Il tuo ISP/Rete** (es: Vodafone, ufficio, etc.)

---

## 🎯 Prossimi Passi

1. ✅ Esegui i 3 test rapidi sopra
2. ✅ Se tutti passano, fai hard refresh del browser
3. ✅ Se ancora fallisce, contatta supporto con i dati sopra

---

*Ultimo aggiornamento: 25 gennaio 2026*
