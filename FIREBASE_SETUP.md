# Configurazione Firebase Authentication

Questa guida ti aiuterà a configurare Firebase Authentication per il progetto SeedWise.

## Passo 1: Crea un progetto Firebase

1. Vai su [Firebase Console](https://console.firebase.google.com/)
2. Clicca su "Aggiungi progetto" o seleziona un progetto esistente
3. Segui la procedura guidata per creare/configurare il progetto

## Passo 2: Abilita Authentication

1. Nel tuo progetto Firebase, vai su **Authentication** nel menu laterale
2. Clicca su **Get Started**
3. Vai alla tab **Sign-in method**
4. Abilita **Email/Password** come provider di autenticazione
5. Clicca su **Email/Password** e attiva "Enable"

## Passo 3: Ottieni le credenziali del progetto

1. Vai su **Project Settings** (icona ingranaggio accanto a "Project Overview")
2. Scorri fino a **Your apps** e clicca sull'icona web (`</>`)
3. Registra un'app web (se non l'hai già fatto)
4. Copia le credenziali di configurazione che appaiono

## Passo 4: Configura il Frontend

Apri `index.html` e sostituisci la configurazione Firebase con le tue credenziali:

```javascript
const firebaseConfig = {
    apiKey: "TUA_API_KEY",
    authDomain: "TUO_PROJECT_ID.firebaseapp.com",
    projectId: "TUO_PROJECT_ID",
    storageBucket: "TUO_PROJECT_ID.appspot.com",
    messagingSenderId: "TUO_MESSAGING_SENDER_ID",
    appId: "TUO_APP_ID"
};
```

## Passo 5: Configura il Backend

### Opzione A: Usando variabile d'ambiente (Consigliato per produzione)

1. Vai su **Project Settings** > **Service accounts**
2. Clicca su **Generate new private key**
3. Scarica il file JSON
4. Converti il contenuto del JSON in una stringa (puoi usare un tool online o Python)
5. Aggiungi la variabile d'ambiente `FIREBASE_CREDENTIALS_JSON` con il contenuto del JSON come stringa

Esempio con Python:
```python
import json
with open('firebase-credentials.json', 'r') as f:
    creds = json.load(f)
    print(json.dumps(creds))  # Copia questo output
```

### Opzione B: Usando file locale (Solo per sviluppo)

1. Scarica il file JSON delle credenziali come sopra
2. Rinominalo in `firebase-credentials.json`
3. Posizionalo nella cartella `backend/`
4. Aggiungi la variabile d'ambiente `FIREBASE_CREDENTIALS_PATH=firebase-credentials.json`

**⚠️ IMPORTANTE**: Non committare mai il file `firebase-credentials.json` nel repository! Aggiungilo a `.gitignore`.

## Passo 6: Installa le dipendenze del backend

```bash
cd backend
pip install -r requirements.txt
```

Questo installerà `firebase-admin` che è necessario per verificare i token.

## Passo 7: Testa l'autenticazione

1. Avvia il backend
2. Apri l'applicazione nel browser
3. Clicca su "Registrati" nell'header
4. Crea un account di test
5. Prova a creare un business plan - dovresti essere reindirizzato al login se non sei autenticato

## Funzionalità implementate

- ✅ Registrazione utenti con email/password
- ✅ Login utenti
- ✅ Logout
- ✅ Verifica autenticazione prima del pagamento
- ✅ UI che mostra lo stato di autenticazione
- ✅ Verifica token Firebase nel backend

## Sicurezza

- I token Firebase vengono verificati lato server prima di creare sessioni di pagamento
- Le password sono gestite da Firebase (hashing sicuro)
- I token scadono automaticamente e devono essere rinnovati

## Troubleshooting

### "Firebase non inizializzato"
- Verifica che le credenziali in `index.html` siano corrette
- Controlla la console del browser per errori

### "Token non valido" nel backend
- Verifica che Firebase Admin sia configurato correttamente
- Controlla che le credenziali del service account siano valide
- Verifica i log del backend per dettagli sull'errore

### L'autenticazione non funziona
- Verifica che Email/Password sia abilitato in Firebase Console
- Controlla che il dominio sia autorizzato in Firebase (per produzione)
