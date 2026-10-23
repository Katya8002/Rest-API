from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Category, Product, Recipe, RecipeIngredient, RecipeStep


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

class RecipeShortSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ["id", "name", "cooking_time_min", "category"]


class IngredientOutSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ["product", "quantity"]


class RecipeDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    steps = serializers.StringRelatedField(many=True, read_only=True)
    ingredients = IngredientOutSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "description",
            "cooking_time_min",
            "category",
            "steps",
            "ingredients",
        ]


class IngredientInputSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )
    quantity = serializers.FloatField(min_value=0.01)


class RecipeInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    cooking_time_min = serializers.IntegerField(min_value=1)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category"
    )
    steps = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    ingredients = IngredientInputSerializer(many=True, allow_empty=False)

    def validate_ingredients(self, ingredients):
        product_ids = [item["product"].id for item in ingredients]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Один і той самий продукт не можна вказати двічі."
            )
        return ingredients

    def _save_steps_and_ingredients(self, recipe, steps, ingredients):
        for number, text in enumerate(steps, start=1):
            RecipeStep.objects.create(recipe=recipe, step_number=number, text=text)
        for item in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe, product=item["product"], quantity=item["quantity"]
            )

    @transaction.atomic
    def create(self, validated_data):
        steps = validated_data.pop("steps")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._save_steps_and_ingredients(recipe, steps, ingredients)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        steps = validated_data.pop("steps")
        ingredients = validated_data.pop("ingredients")
        for field, value in validated_data.items():
            setattr(recipe, field, value)
        recipe.save()
        recipe.steps.all().delete()
        recipe.ingredients.all().delete()
        self._save_steps_and_ingredients(recipe, steps, ingredients)
        return recipe


class RecipeFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    category_id = serializers.IntegerField(required=False)
    max_time = serializers.IntegerField(required=False, min_value=1)
    product_id = serializers.IntegerField(required=False)
