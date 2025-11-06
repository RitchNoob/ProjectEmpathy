from datetime import datetime, timedelta


def test_dashboard_stats(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/calls/",
        json={
            "call_sid": "CA123",
            "status": "completed",
            "transcript": "Bonjour",
            "duration_seconds": 120
        },
    )

    test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/orders/",
        json={
            "customer_name": "Alice",
            "items": []
        },
    )

    response = test_client.get(f"/api/v1/restaurants/{restaurant_id}/dashboard/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_calls"] >= 1
    assert stats["total_orders"] >= 1
