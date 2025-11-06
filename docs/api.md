# API interne Project Empathy (v1)

Base URL : `https://{host}/api/v1`

## Authentification

Les routes scellées par `/restaurants/{id}/...` exigent l'en-tête `X-API-Key` associé au restaurant ciblé. Les clés sont générées/rotées via la CLI (`python -m project_empathy.cli create-token`) ou via les endpoints décrits ci-dessous. Une réponse `401` est renvoyée si l'en-tête est absent ou invalide, `403` si la clé ne correspond pas au restaurant.

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

## Clés API

### GET `/restaurants/{id}/api-tokens`
Liste les clés actives associées au restaurant.

### POST `/restaurants/{id}/api-tokens`
Crée une nouvelle clé (retourne la valeur en clair une seule fois).

```json
{
  "name": "Dashboard",
  "token": "..."
}
```

### POST `/restaurants/{id}/api-tokens/{token_id}/rotate`
Invalide la clé actuelle et retourne la nouvelle valeur.

### DELETE `/restaurants/{id}/api-tokens/{token_id}`
Révoque la clé.

## Notifications webhook

### GET `/restaurants/{id}/notifications/`
Liste les endpoints configurés pour le restaurant.

### POST `/restaurants/{id}/notifications/`
Crée un nouvel endpoint. Les événements disponibles sont `orders.created`, `orders.updated`, `reservations.created` et `calls.created`.

```json
{
  "name": "Zapier",
  "target_url": "https://hooks.zapier.com/...",
  "events": ["orders.created", "reservations.created"],
  "secret": "optionnel-pour-HMAC"
}
```

### PATCH `/restaurants/{id}/notifications/{notification_id}`
Met à jour le nom, l'URL, la liste d'événements ou active/désactive l'endpoint (`{"is_active": false}`).

### POST `/restaurants/{id}/notifications/{notification_id}/test`
Déclenche une notification test avec un payload personnalisé.

### DELETE `/restaurants/{id}/notifications/{notification_id}`
Supprime l'endpoint.

## Webhooks Twilio

- `POST /twilio/voice` : réponse initiale (TwiML).
- `POST /twilio/handle-input` : boucle sur les transcriptions.

Configurez Twilio Voice URL -> `https://{host}/api/v1/twilio/voice` et la transcription -> `https://{host}/api/v1/twilio/handle-input`.
