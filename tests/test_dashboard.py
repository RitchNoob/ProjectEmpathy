def test_dashboard_stats(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    headers = seeded_restaurant["headers"]

    test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/calls/",
        json={
            "call_sid": "CA123",
            "status": "completed",
            "transcript": "Bonjour",
            "duration_seconds": 120,
        },
        headers=headers,
    )

    test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/orders/",
        json={
            "customer_name": "Alice",
            "items": [],
        },
        headers=headers,
    )

    response = test_client.get(
        f"/api/v1/restaurants/{restaurant_id}/dashboard/stats",
        headers=headers,
    )
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_calls"] >= 1
    assert stats["total_orders"] >= 1


def test_dashboard_requires_api_key(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    response = test_client.get(f"/api/v1/restaurants/{restaurant_id}/dashboard/stats")
    assert response.status_code == 401
