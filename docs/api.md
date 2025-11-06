# API interne Project Empathy (v1)

Base URL : `https://{host}/api/v1`

## Authentification

L'API s'appuie sur les abonnements Flexprice/Stripe. Chaque requête doit inclure un token d'API (non implémenté dans l'exemple). Ajoutez un proxy/API Gateway pour la gestion des clés.

## Restaurants

### GET `/restaurants/`
Liste des restaurants.

### POST `/restaurants/`
Crée un restaurant.

```json
{
  "name": "Chez Léa",
  "email": "lea@example.com",
  "phone_number": "+33102030405",
  "timezone": "Europe/Paris",
  "address": "12 rue des Fleurs, Paris"
}
```

## Menu

### GET `/restaurants/{id}/menu/items`
Liste les plats.

### POST `/restaurants/{id}/menu/items`
Crée un plat.

```json
{
  "name": "Pizza Margherita",
  "description": "Tomate, mozzarella, basilic",
  "price": 12.90,
  "category_id": 1
}
```

### PATCH `/restaurants/{id}/menu/items/{item_id}`
Met à jour un plat (partiel).

## Commandes

### GET `/restaurants/{id}/orders/`
Commandes triées par date décroissante.

### POST `/restaurants/{id}/orders/`
Crée une commande et décrémente les crédits d'abonnement.

```json
{
  "customer_name": "Alice",
  "customer_phone": "+33601020304",
  "delivery_address": "15 avenue Victor Hugo, Paris",
  "items": [
    {"menu_item_id": 3, "quantity": 2},
    {"menu_item_id": 5, "quantity": 1, "notes": "Sans oignons"}
  ]
}
```

### POST `/restaurants/{id}/orders/{order_id}/status`
Met à jour le statut (`pending`, `confirmed`, `delivered`, etc.).

```json
{
  "status": "confirmed"
}
```

## Réservations

### POST `/restaurants/{id}/reservations/`
Crée une réservation.

```json
{
  "guest_name": "Karim",
  "guest_count": 4,
  "reservation_time": "2024-09-15T20:00:00Z",
  "notes": "Allergie aux arachides"
}
```

## Appels

### POST `/restaurants/{id}/calls/`
Enregistre une session d'appel (call SID Twilio, statut, transcript).

## Abonnements

### GET `/subscriptions/plans`
Liste des plans disponibles.

### POST `/subscriptions/plans`
Crée/synchronise un plan (depuis Flexprice/Stripe).

```json
{
  "external_id": "plan_standard",
  "name": "Standard",
  "monthly_price": 149.00,
  "call_quota": 500
}
```

### POST `/subscriptions/restaurants/{id}`
Associe un restaurant à un plan et met à jour la période de facturation.

## Dashboard

### GET `/restaurants/{id}/dashboard/stats`
Retourne :

```json
{
  "total_calls": 42,
  "total_orders": 18,
  "average_order_value": 32.5,
  "total_revenue": 585.0
}
```

## Webhooks Twilio

- `POST /twilio/voice` : réponse initiale (TwiML).
- `POST /twilio/handle-input` : boucle sur les transcriptions.

Configurez Twilio Voice URL -> `https://{host}/api/v1/twilio/voice` et la transcription -> `https://{host}/api/v1/twilio/handle-input`.
