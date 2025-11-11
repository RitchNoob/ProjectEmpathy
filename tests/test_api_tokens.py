def test_api_token_lifecycle(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    headers = seeded_restaurant["headers"]

    list_response = test_client.get(
        f"/api/v1/restaurants/{restaurant_id}/api-tokens",
        headers=headers,
    )
    assert list_response.status_code == 200
    existing_tokens = list_response.json()
    assert len(existing_tokens) >= 1

    create_response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/api-tokens",
        json={"name": "Integration"},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert "token" in created
    assert created["token"]
    assert created["metadata"]["name"] == "Integration"

    rotate_response = test_client.post(
        f"/api/v1/restaurants/{restaurant_id}/api-tokens/{created['metadata']['id']}/rotate",
        headers=headers,
    )
    assert rotate_response.status_code == 200
    rotated = rotate_response.json()
    assert rotated["token"] != created["token"]

    delete_response = test_client.delete(
        f"/api/v1/restaurants/{restaurant_id}/api-tokens/{created['metadata']['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 204
