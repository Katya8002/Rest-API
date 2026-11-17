import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from recipes.models import Category, Product, Recipe, RecipeIngredient, RecipeStep

PASSWORD = "Str0ng-pass-2026"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="user", email="user@example.com", password=PASSWORD
    )


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password=PASSWORD
    )


@pytest.fixture
def user_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def staff_client(admin):
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


@pytest.fixture
def category(db):
    return Category.objects.create(name="Сніданки")


@pytest.fixture
def product(db):
    return Product.objects.create(name="Яйця", unit="pcs")


@pytest.fixture
def recipe(category, product):
    recipe = Recipe.objects.create(
        name="Омлет",
        description="Швидкий сніданок",
        cooking_time_min=10,
        category=category,
    )
    RecipeStep.objects.create(recipe=recipe, step_number=1, text="Збити яйця")
    RecipeIngredient.objects.create(recipe=recipe, product=product, quantity=3)
    return recipe


@pytest.fixture
def recipe_payload(category, product):
    return {
        "name": "Яєчня",
        "description": "",
        "cooking_time_min": 5,
        "category_id": category.id,
        "steps": ["Смажити на сковорідці"],
        "ingredients": [{"product_id": product.id, "quantity": 2}],
    }
