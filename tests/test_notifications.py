def _create_menu_item(client, restaurant_id, headers, name_suffix):
    response = client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu/items",
        json={
            "name": f"Plat {name_suffix}",
            "price": "9.50",
            "description": "Plat de test",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_notification_endpoints_flow(test_client, seeded_restaurant, notification_events):
    restaurant_id = seeded_restaurant["id"]
    headers = seeded_restaurant["headers"]

    create_response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/notifications/",
        json={
            "name": "Webhook principal",
            "target_url": "https://example.com/hook",
            "events": ["orders.created", "reservations.created"],
            "secret": "test-secret",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    endpoint = create_response.json()
    endpoint_id = endpoint["id"]

    list_response = test_client.get(
        f"/api/v1/restaurants/{restaurant_id}/notifications/",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    test_response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/notifications/{endpoint_id}/test",
        json={"event_type": "orders.created", "payload": {"sample": True}},
        headers=headers,
    )
    assert test_response.status_code == 200
    assert notification_events[-1]["event"] == "orders.created"
    assert test_response.json()["last_status_code"] == 200

    item = _create_menu_item(test_client, restaurant_id, headers, "A")
    order_response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/orders/",
        json={
            "customer_name": "Test Client",
            "items": [{"menu_item_id": item["id"], "quantity": 1}],
        },
        headers=headers,
    )
    assert order_response.status_code == 201
    order_events = [e for e in notification_events if e["event"] == "orders.created"]
    assert len(order_events) >= 2  # includes test ping and order creation

    update_response = test_client.patch(
        f"/api/v1/restaurants/{restaurant_id}/notifications/{endpoint_id}",
        json={"is_active": False},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False

    item_b = _create_menu_item(test_client, restaurant_id, headers, "B")
    before_events = len([e for e in notification_events if e["event"] == "orders.created"])
    second_order = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/orders/",
        json={
            "customer_name": "Test Client",
            "items": [{"menu_item_id": item_b["id"], "quantity": 1}],
        },
        headers=headers,
    )
    assert second_order.status_code == 201
    after_events = len([e for e in notification_events if e["event"] == "orders.created"])
    assert after_events == before_events  # inactive endpoint should not receive events

    delete_response = test_client.delete(
        f"/api/v1/restaurants/{restaurant_id}/notifications/{endpoint_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    list_after_delete = test_client.get(
        f"/api/v1/restaurants/{restaurant_id}/notifications/",
        headers=headers,
    )
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []
