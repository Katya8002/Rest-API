from recipes.models import Category

URL = "/api/v1/categories"


def test_create_without_token_returns_401(api_client, db):
    response = api_client.post(URL, {"name": "Супи"}, format="json")

    assert response.status_code == 401


def test_create_as_user_returns_403(user_client):
    response = user_client.post(URL, {"name": "Супи"}, format="json")

    assert response.status_code == 403
    assert Category.objects.count() == 0


def test_create_as_admin_returns_201(staff_client):
    response = staff_client.post(URL, {"name": "Супи"}, format="json")

    assert response.status_code == 201
    assert Category.objects.filter(name="Супи").exists()


def test_create_duplicate_name_returns_400(staff_client, category):
    response = staff_client.post(URL, {"name": "Сніданки"}, format="json")

    assert response.status_code == 400
    assert Category.objects.count() == 1


def test_update_as_admin_returns_200(staff_client, category):
    response = staff_client.put(
        f"{URL}/{category.id}", {"name": "Обіди"}, format="json"
    )

    category.refresh_from_db()
    assert response.status_code == 200
    assert category.name == "Обіди"


def test_delete_as_admin_returns_204(staff_client, category):
    response = staff_client.delete(f"{URL}/{category.id}")

    assert response.status_code == 204
    assert not Category.objects.filter(pk=category.id).exists()


def test_delete_category_with_recipes_returns_409(staff_client, recipe):
    response = staff_client.delete(f"{URL}/{recipe.category.id}")

    assert response.status_code == 409
    assert Category.objects.filter(pk=recipe.category.id).exists()
