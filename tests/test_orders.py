from datetime import datetime, timedelta


def test_create_order_success(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    headers = seeded_restaurant["headers"]

    item_response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu/items",
        json={
            "name": "Pizza Test",
            "price": "12.50",
            "description": "Tomate et fromage",
        },
        headers=headers,
    )
    assert item_response.status_code == 201
    menu_item = item_response.json()

    order_response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/orders/",
        json={
            "customer_name": "Alice",
            "items": [{"menu_item_id": menu_item["id"], "quantity": 2}],
        },
        headers=headers,
    )
    assert order_response.status_code == 201
    payload = order_response.json()
    assert payload["total_amount"] == "25.00"
    assert payload["items"][0]["quantity"] == 2


def test_order_requires_authentication(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    response = test_client.get(f"/api/v1/restaurants/{restaurant_id}/orders/")
    assert response.status_code == 401


def test_reservation_flow(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    headers = seeded_restaurant["headers"]
    reservation_time = (datetime.utcnow() + timedelta(days=1)).isoformat()

    response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/reservations/",
        json={
            "guest_name": "Bob",
            "guest_count": 4,
            "reservation_time": reservation_time,
            "notes": "Allergie",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["guest_name"] == "Bob"
    assert data["guest_count"] == 4

    list_response = test_client.get(
        f"/api/v1/restaurants/{restaurant_id}/reservations/",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
