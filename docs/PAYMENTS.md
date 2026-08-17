# Paiements

Le projet contient maintenant une frontière de paiement prête à être reliée à Stripe ou à un autre prestataire, mais elle est **désactivée par défaut**.

## Garanties actuelles

- `PAYMENT_PROVIDER=disabled` en local et dans Docker.
- aucune donnée de carte bancaire n'est collectée ni stockée par IARH ;
- les montants ne sont pas acceptés depuis le navigateur : seul un `plan_code` est transmis ;
- les webhooks sont refusés tant qu'un prestataire n'est pas activé et vérifié ;
- les abonnements sont conservés dans une table interne avec un identifiant externe, jamais avec des données de carte.

## API préparée

- `GET /api/v1/billing/status` : état du paiement et abonnement de l'utilisateur connecté ;
- `POST /api/v1/billing/checkout` avec `{ "plan_code": "pro_monthly" }` ou `{ "plan_code": "pro_yearly" }` ;
- `POST /api/v1/billing/webhook` : point d'entrée réservé aux événements signés du prestataire.

En mode désactivé, le statut est disponible et la création d'une session renvoie `503 PAYMENTS_NOT_CONFIGURED`. C'est volontaire : aucune facturation réelle ne peut démarrer par erreur.

## Configuration ultérieure

Dans un environnement secret manager, définir au minimum :

```env
PAYMENT_PROVIDER=stripe
PAYMENT_CURRENCY=USD
PAYMENT_WEBHOOK_SECRET=secret-fourni-par-le-prestataire
PAYMENT_SUCCESS_URL=https://app.example.com/billing/success
PAYMENT_CANCEL_URL=https://app.example.com/billing/cancel
```

L'adaptateur Stripe et la vérification de ses événements devront être ajoutés avant d'activer `stripe`. Les prix et les plans devront alors être définis côté serveur, puis couverts par des tests d'idempotence, de signature, de renouvellement, d'annulation et de réconciliation.
