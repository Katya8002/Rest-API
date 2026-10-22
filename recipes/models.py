from django.db import models
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ("g", "грами"),
        ("ml", "мілілітри"),
        ("pcs", "штуки"),
    ]

    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cooking_time_min = models.PositiveIntegerField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="recipes"
    )

    def __str__(self):
        return self.name


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    step_number = models.PositiveIntegerField()
    text = models.TextField()

    class Meta:
        ordering = ["step_number"]

    def __str__(self):
        return self.text


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredients"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="recipe_ingredients"
    )
    quantity = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "product"], name="unique_product_in_recipe"
            )
        ]