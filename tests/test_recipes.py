from recipes.models import Recipe

URL = "/api/v1/recipes"


def test_list_is_public(api_client, recipe):
    response = api_client.get(URL)

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Омлет"


def test_list_search_finds_nothing(api_client, recipe):
    response = api_client.get(URL, {"search": "Борщ"})

    assert response.status_code == 200
    assert response.json() == []


def test_detail_is_public(api_client, recipe):
    response = api_client.get(f"{URL}/{recipe.id}")

    assert response.status_code == 200
    assert response.json()["steps"] == ["Збити яйця"]


def test_detail_not_found_returns_404(api_client, db):
    response = api_client.get(f"{URL}/999")

    assert response.status_code == 404


def test_create_without_token_returns_401(api_client, recipe_payload):
    response = api_client.post(URL, recipe_payload, format="json")

    assert response.status_code == 401
    assert Recipe.objects.count() == 0


def test_create_as_user_returns_201(user_client, recipe_payload):
    response = user_client.post(URL, recipe_payload, format="json")

    assert response.status_code == 201
    assert response.json()["name"] == "Яєчня"
    assert Recipe.objects.count() == 1


def test_create_without_name_returns_400(user_client, recipe_payload):
    del recipe_payload["name"]

    response = user_client.post(URL, recipe_payload, format="json")

    assert response.status_code == 400
    assert Recipe.objects.count() == 0


def test_update_without_token_returns_401(api_client, recipe, recipe_payload):
    response = api_client.put(f"{URL}/{recipe.id}", recipe_payload, format="json")

    assert response.status_code == 401


def test_update_as_user_returns_200(user_client, recipe, recipe_payload):
    response = user_client.put(f"{URL}/{recipe.id}", recipe_payload, format="json")

    recipe.refresh_from_db()
    assert response.status_code == 200
    assert recipe.name == "Яєчня"


def test_delete_as_user_returns_204(user_client, recipe):
    response = user_client.delete(f"{URL}/{recipe.id}")

    assert response.status_code == 204
    assert not Recipe.objects.filter(pk=recipe.id).exists()


def test_delete_not_found_returns_404(user_client):
    response = user_client.delete(f"{URL}/999")

    assert response.status_code == 404
