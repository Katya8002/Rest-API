from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=100,
        validators=[
            UniqueValidator(
                queryset=Category.objects.all(),
                message="Категорія з такою назвою вже існує.",
            )
        ],
    )

    class Meta:
        model = Category
        fields = ["id", "name"]


class CategoryDetailSerializer(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "recipes"]

    def get_recipes(self, category):
        recipes = category.recipes.order_by("id")
        return [
            {"id": r.id, "name": r.name, "cooking_time_min": r.cooking_time_min}
            for r in recipes
        ]

class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=100,
        validators=[
            UniqueValidator(
                queryset=Product.objects.all(),
                message="Продукт з такою назвою вже існує.",
            )
        ],
    )

    class Meta:
        model = Product
        fields = ["id", "name", "unit"]