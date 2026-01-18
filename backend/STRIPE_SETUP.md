# Configurazione Stripe

Per abilitare i pagamenti Stripe, configura le seguenti variabili d'ambiente:

## Variabili d'ambiente richieste

```bash
STRIPE_SECRET_KEY=sk_test_...  # Chiave segreta Stripe (test o live)
STRIPE_PUBLISHABLE_KEY=pk_test_...  # Chiave pubblica Stripe (opzionale, per frontend)
STRIPE_WEBHOOK_SECRET=whsec_...  # Secret webhook (opzionale, per webhook)
```

## Prezzi configurabili

Puoi configurare i prezzi tramite variabili d'ambiente (in centesimi di euro):

```bash
PRICE_BUSINESS_PLAN_CENTS=1999  # 19.99€ (default)
PRICE_MARKET_ANALYSIS_CENTS=1499  # 14.99€ (default)
```

## Flusso di pagamento

1. L'utente clicca "Scarica PDF"
2. Viene creata una sessione di checkout Stripe
3. L'utente viene reindirizzato a Stripe per il pagamento
4. Dopo il pagamento, Stripe reindirizza l'utente alla pagina con `?payment=success&session_id=...`
5. Il frontend verifica il pagamento
6. Se verificato, viene generato e scaricato il PDF

## Test

Per testare in modalità test, usa le chiavi di test di Stripe (che iniziano con `sk_test_` e `pk_test_`).

Usa le carte di test di Stripe:
- Successo: `4242 4242 4242 4242`
- Rifiutata: `4000 0000 0000 0002`
