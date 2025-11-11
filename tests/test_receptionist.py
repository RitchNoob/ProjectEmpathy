def test_get_receptionist_profile(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    headers = seeded_restaurant["headers"]

    response = test_client.get(
        f"/api/v1/restaurants/{restaurant_id}/receptionist/profile",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["restaurant_id"] == restaurant_id
    assert payload["display_name"]
    assert payload["greeting"]
    assert payload["brand_primary_color"].startswith("#")


def test_update_receptionist_profile(test_client, seeded_restaurant):
    restaurant_id = seeded_restaurant["id"]
    headers = seeded_restaurant["headers"]

    update = {
        "display_name": "Concierge Nova",
        "tone": "Futuriste et chaleureux",
        "upsell_phrases": [
            "Proposer le dessert signature",
            "Mettre en avant le café gourmand",
        ],
        "brand_primary_color": "#3344FF",
        "brand_accent_color": "#2AF0FF",
        "custom_instructions": "Confirmer les allergènes avant validation.",
    }

    response = test_client.patch(
        f"/api/v1/restaurants/{restaurant_id}/receptionist/profile",
        json=update,
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["display_name"] == "Concierge Nova"
    assert payload["tone"] == "Futuriste et chaleureux"
    assert payload["upsell_phrases"] == update["upsell_phrases"]
    assert payload["brand_primary_color"] == "#3344FF"
    assert payload["custom_instructions"].startswith("Confirmer")

    # Vérifie que le profil mis à jour est renvoyé tel quel lors d'une nouvelle lecture.
    refreshed = test_client.get(
        f"/api/v1/restaurants/{restaurant_id}/receptionist/profile",
        headers=headers,
    )
    assert refreshed.status_code == 200
    refreshed_payload = refreshed.json()
    assert refreshed_payload["display_name"] == "Concierge Nova"
    assert refreshed_payload["upsell_phrases"] == update["upsell_phrases"]
