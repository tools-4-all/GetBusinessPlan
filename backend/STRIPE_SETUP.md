# Configurazione Stripe

Per abilitare i pagamenti Stripe, configura le seguenti variabili d'ambiente:

## Variabili d'ambiente richieste

```bash
STRIPE_SECRET_KEY=sk_test_...  # Chiave segreta Stripe (test o live)
STRIPE_PUBLISHABLE_KEY=pk_test_...  # Chiave pubblica Stripe (opzionale, per frontend)
STRIPE_WEBHOOK_SECRET=whsec_...  # Secret webhook (opzionale, per webhook)
```

## Configurazione Price ID (Raccomandato)

**Il modo migliore è creare i Price direttamente in Stripe Dashboard e usare i Price ID.**

### Passo 1: Crea i prodotti e Price in Stripe Dashboard

1. Vai su https://dashboard.stripe.com/products
2. Clicca "Add product" e crea i seguenti 4 prodotti:

   **Prodotto 1: Business Plan (prezzo normale)**
   - Nome: "Business Plan Professionale"
   - Prezzo: 19.99€ (EUR)
   - Tipo: One-time payment
   - Copia il **Price ID** (inizia con `price_...`)

   **Prodotto 2: Analisi di Mercato (prezzo normale)**
   - Nome: "Analisi di Mercato"
   - Prezzo: 14.99€ (EUR)
   - Tipo: One-time payment
   - Copia il **Price ID**

   **Prodotto 3: Business Plan Upsell (30% sconto)**
   - Nome: "Business Plan Professionale (Offerta Speciale)"
   - Prezzo: 13.99€ (EUR) - questo è il 70% di 19.99€ (30% di sconto)
   - Tipo: One-time payment
   - Copia il **Price ID**

   **Prodotto 4: Analisi di Mercato Upsell (30% sconto)**
   - Nome: "Analisi di Mercato (Offerta Speciale)"
   - Prezzo: 10.49€ (EUR) - questo è il 70% di 14.99€ (30% di sconto)
   - Tipo: One-time payment
   - Copia il **Price ID**

### Passo 2: Aggiungi i Price ID alle variabili d'ambiente

Aggiungi questi Price ID alle variabili d'ambiente del tuo server (Render, Heroku, ecc.):

```bash
# Price ID Stripe (sostituisci con i tuoi Price ID reali)
STRIPE_PRICE_BUSINESS_PLAN=price_xxxxxxxxxxxxx
STRIPE_PRICE_MARKET_ANALYSIS=price_xxxxxxxxxxxxx
STRIPE_PRICE_BUSINESS_PLAN_UPSELL=price_xxxxxxxxxxxxx
STRIPE_PRICE_MARKET_ANALYSIS_UPSELL=price_xxxxxxxxxxxxx
```

### Passo 3: Come trovare i Price ID

1. Vai su https://dashboard.stripe.com/products
2. Clicca sul prodotto che hai creato
3. Nella sezione "Pricing", vedrai il Price ID accanto al prezzo
4. Copia l'ID (inizia con `price_...`)

### Fallback ai prezzi dinamici

Se non configuri i Price ID, il sistema userà automaticamente `price_data` con i prezzi configurati tramite:

```bash
PRICE_BUSINESS_PLAN_CENTS=1999  # 19.99€ (default)
PRICE_MARKET_ANALYSIS_CENTS=1499  # 14.99€ (default)
```

**Nota:** Usare Price ID è raccomandato perché:
- Gestione centralizzata dei prezzi in Stripe Dashboard
- Possibilità di modificare i prezzi senza cambiare il codice
- Migliore tracciabilità delle vendite
- Supporto per sconti e promozioni gestiti da Stripe

## Flusso di pagamento

1. L'utente clicca "Scarica PDF"
2. Viene creata una sessione di checkout Stripe
3. L'utente viene reindirizzato a Stripe per il pagamento
4. Dopo il pagamento, Stripe reindirizza l'utente alla pagina con `?payment=success&session_id=...`
5. Il frontend verifica il pagamento
6. Se verificato, viene generato e scaricato il PDF

## Configurazione Webhook

1. Vai su https://dashboard.stripe.com/webhooks
2. Clicca "Add endpoint"
3. Inserisci l'URL del tuo backend:
   ```
   https://getbusinessplan.onrender.com/api/webhook/stripe
   ```
4. Seleziona gli eventi da ascoltare:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Clicca "Add endpoint"
6. Copia il **Webhook Signing Secret** (inizia con `whsec_...`)
7. Aggiungilo alle variabili d'ambiente:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
   ```

**Nota:** L'endpoint webhook deve essere implementato nel backend. Vedi la sezione "Implementazione Webhook" nella documentazione.

## Test

Per testare in modalità test, usa le chiavi di test di Stripe (che iniziano con `sk_test_` e `pk_test_`).

Usa le carte di test di Stripe:
- Successo: `4242 4242 4242 4242`
- Rifiutata: `4000 0000 0000 0002`

## Esempio completo di configurazione

Ecco un esempio completo di tutte le variabili d'ambiente da configurare:

```bash
# Chiavi Stripe (obbligatorie)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Price ID Stripe (raccomandato)
STRIPE_PRICE_BUSINESS_PLAN=price_xxxxxxxxxxxxx
STRIPE_PRICE_MARKET_ANALYSIS=price_xxxxxxxxxxxxx
STRIPE_PRICE_BUSINESS_PLAN_UPSELL=price_xxxxxxxxxxxxx
STRIPE_PRICE_MARKET_ANALYSIS_UPSELL=price_xxxxxxxxxxxxx

# Prezzi fallback (usati solo se Price ID non configurati)
PRICE_BUSINESS_PLAN_CENTS=1999
PRICE_MARKET_ANALYSIS_CENTS=1499
```
