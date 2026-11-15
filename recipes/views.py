import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Recipe
from .permissions import IsAdminOrReadOnly
from .serializers import (
    CategoryDetailSerializer,
    CategorySerializer,
    ProductSerializer,
    RecipeDetailSerializer,
    RecipeFilterSerializer,
    RecipeInputSerializer,
    RecipeShortSerializer,
)

logger = logging.getLogger(__name__)
BAD_REQUEST = OpenApiResponse(description="Некоректні дані")
UNAUTHORIZED = OpenApiResponse(description="Немає токена або він недійсний")
FORBIDDEN = OpenApiResponse(description="Дія доступна лише адміністратору")
NOT_FOUND = OpenApiResponse(description="Об'єкта з таким id немає")
CONFLICT = OpenApiResponse(description="Видалити не можна: є пов'язані рецепти")
DELETED = OpenApiResponse(description="Видалено, тіло відповіді порожнє")

RECIPE_EXAMPLE = OpenApiExample(
    "Яєчня",
    value={
        "name": "Яєчня",
        "description": "",
        "cooking_time_min": 5,
        "category_id": 1,
        "steps": ["Розігріти сковорідку", "Розбити яйця"],
        "ingredients": [{"product_id": 1, "quantity": 2}],
    },
    request_only=True,
)


def error_response(message, http_status, errors=None):
    body = {"detail": message}
    if errors:
        body["errors"] = errors
    return Response(body, status=http_status)


def invalid_data(serializer):
    logger.warning("Некоректні дані, помилки в полях: %s", list(serializer.errors))
    return error_response(
        "Некоректні дані.", status.HTTP_400_BAD_REQUEST, serializer.errors
    )


def filter_by_name(items, search):
    search = search.casefold()
    return [item for item in items if search in item.name.casefold()]


class CategoryListView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(
        tags=["Категорії"],
        summary="Список категорій",
        responses=CategorySerializer(many=True),
    )
    def get(self, request):
        categories = Category.objects.order_by("id")
        return Response(CategorySerializer(categories, many=True).data)

    @extend_schema(
        tags=["Категорії"],
        summary="Створити категорію (лише адміністратор)",
        request=CategorySerializer,
        responses={
            201: CategorySerializer,
            400: BAD_REQUEST,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        category = serializer.save()
        logger.info(
            "Створено категорію id=%s, user_id=%s", category.id, request.user.id
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_category(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    @extend_schema(
        tags=["Категорії"],
        summary="Категорія з її рецептами",
        responses={200: CategoryDetailSerializer, 404: NOT_FOUND},
    )
    def get(self, request, pk):
        category = self.get_category(pk)
        if category is None:
            return error_response("Категорію не знайдено.", status.HTTP_404_NOT_FOUND)
        return Response(CategoryDetailSerializer(category).data)

    @extend_schema(
        tags=["Категорії"],
        summary="Змінити категорію (лише адміністратор)",
        request=CategorySerializer,
        responses={
            200: CategorySerializer,
            400: BAD_REQUEST,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def put(self, request, pk):
        category = self.get_category(pk)
        if category is None:
            return error_response("Категорію не знайдено.", status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        serializer.save()
        logger.info("Змінено категорію id=%s, user_id=%s", category.id, request.user.id)
        return Response(serializer.data)

    @extend_schema(
        tags=["Категорії"],
        summary="Видалити категорію (лише адміністратор)",
        responses={
            204: DELETED,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
            409: CONFLICT,
        },
    )
    def delete(self, request, pk):
        category = self.get_category(pk)
        if category is None:
            return error_response("Категорію не знайдено.", status.HTTP_404_NOT_FOUND)
        recipes_count = category.recipes.count()
        if recipes_count > 0:
            logger.warning(
                "Видалення категорії id=%s заблоковано: рецептів %s",
                category.id,
                recipes_count,
            )
            return error_response(
                f"Неможливо видалити категорію «{category.name}», оскільки "
                f"в ній є рецепти: {recipes_count}. Спершу видаліть їх "
                "або перенесіть в іншу категорію.",
                status.HTTP_409_CONFLICT,
            )
        category.delete()
        logger.info("Видалено категорію id=%s, user_id=%s", pk, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(
        tags=["Продукти"],
        summary="Список продуктів з пошуком за назвою",
        responses=ProductSerializer(many=True),
    )
    def get(self, request):
        products = Product.objects.order_by("id")
        search = request.query_params.get("search")
        if search:
            products = filter_by_name(products, search)
        return Response(ProductSerializer(products, many=True).data)

    @extend_schema(
        tags=["Продукти"],
        summary="Створити продукт (лише адміністратор)",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: BAD_REQUEST,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        product = serializer.save()
        logger.info("Створено продукт id=%s, user_id=%s", product.id, request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_product(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    @extend_schema(
        tags=["Продукти"],
        summary="Продукт за id",
        responses={200: ProductSerializer, 404: NOT_FOUND},
    )
    def get(self, request, pk):
        product = self.get_product(pk)
        if product is None:
            return error_response("Продукт не знайдено.", status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

    @extend_schema(
        tags=["Продукти"],
        summary="Змінити продукт (лише адміністратор)",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: BAD_REQUEST,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def put(self, request, pk):
        product = self.get_product(pk)
        if product is None:
            return error_response("Продукт не знайдено.", status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        serializer.save()
        logger.info("Змінено продукт id=%s, user_id=%s", product.id, request.user.id)
        return Response(serializer.data)

    @extend_schema(
        tags=["Продукти"],
        summary="Видалити продукт (лише адміністратор)",
        responses={
            204: DELETED,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
            409: CONFLICT,
        },
    )
    def delete(self, request, pk):
        product = self.get_product(pk)
        if product is None:
            return error_response("Продукт не знайдено.", status.HTTP_404_NOT_FOUND)
        recipes_count = product.recipe_ingredients.count()
        if recipes_count > 0:
            logger.warning(
                "Видалення продукту id=%s заблоковано: рецептів %s",
                product.id,
                recipes_count,
            )
            return error_response(
                f"Неможливо видалити продукт «{product.name}», оскільки він "
                f"використовується в рецептах: {recipes_count}.",
                status.HTTP_409_CONFLICT,
            )
        product.delete()
        logger.info("Видалено продукт id=%s, user_id=%s", pk, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Рецепти"],
        summary="Список рецептів з пошуком і фільтрами",
        parameters=[RecipeFilterSerializer],
        responses={200: RecipeShortSerializer(many=True), 400: BAD_REQUEST},
    )
    def get(self, request):
        filters = RecipeFilterSerializer(data=request.query_params)
        if not filters.is_valid():
            return invalid_data(filters)
        params = filters.validated_data
        logger.debug("Список рецептів, фільтри: %s", dict(params))

        recipes = Recipe.objects.select_related("category").order_by("id")
        if "category_id" in params:
            recipes = recipes.filter(category_id=params["category_id"])
        if "max_time" in params:
            recipes = recipes.filter(cooking_time_min__lte=params["max_time"])
        if "product_id" in params:
            recipes = recipes.filter(ingredients__product_id=params["product_id"])
        if "search" in params:
            recipes = filter_by_name(recipes, params["search"])
        return Response(RecipeShortSerializer(recipes, many=True).data)

    @extend_schema(
        tags=["Рецепти"],
        summary="Створити рецепт",
        request=RecipeInputSerializer,
        examples=[RECIPE_EXAMPLE],
        responses={
            201: RecipeDetailSerializer,
            400: BAD_REQUEST,
            401: UNAUTHORIZED,
        },
    )
    def post(self, request):
        serializer = RecipeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        recipe = serializer.save()
        logger.info("Створено рецепт id=%s, user_id=%s", recipe.id, request.user.id)
        return Response(
            RecipeDetailSerializer(recipe).data, status=status.HTTP_201_CREATED
        )


class RecipeDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_recipe(self, pk):
        try:
            return Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return None

    @extend_schema(
        tags=["Рецепти"],
        summary="Рецепт з кроками й інгредієнтами",
        responses={200: RecipeDetailSerializer, 404: NOT_FOUND},
    )
    def get(self, request, pk):
        recipe = self.get_recipe(pk)
        if recipe is None:
            return error_response("Рецепт не знайдено.", status.HTTP_404_NOT_FOUND)
        return Response(RecipeDetailSerializer(recipe).data)

    @extend_schema(
        tags=["Рецепти"],
        summary="Змінити рецепт повністю",
        request=RecipeInputSerializer,
        examples=[RECIPE_EXAMPLE],
        responses={
            200: RecipeDetailSerializer,
            400: BAD_REQUEST,
            401: UNAUTHORIZED,
            404: NOT_FOUND,
        },
    )
    def put(self, request, pk):
        recipe = self.get_recipe(pk)
        if recipe is None:
            return error_response("Рецепт не знайдено.", status.HTTP_404_NOT_FOUND)
        serializer = RecipeInputSerializer(recipe, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        recipe = serializer.save()
        logger.info("Змінено рецепт id=%s, user_id=%s", recipe.id, request.user.id)
        return Response(RecipeDetailSerializer(recipe).data)

    @extend_schema(
        tags=["Рецепти"],
        summary="Видалити рецепт",
        responses={204: DELETED, 401: UNAUTHORIZED, 404: NOT_FOUND},
    )
    def delete(self, request, pk):
        recipe = self.get_recipe(pk)
        if recipe is None:
            return error_response("Рецепт не знайдено.", status.HTTP_404_NOT_FOUND)
        recipe.delete()
        logger.info("Видалено рецепт id=%s, user_id=%s", pk, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
