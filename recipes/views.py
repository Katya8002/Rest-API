from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product
from .serializers import (
    CategoryDetailSerializer,
    CategorySerializer,
    ProductSerializer,
)


def error_response(message, http_status, errors=None):
    body = {"detail": message}
    if errors:
        body["errors"] = errors
    return Response(body, status=http_status)


def invalid_data(serializer):
    return error_response(
        "Некоректні дані.", status.HTTP_400_BAD_REQUEST, serializer.errors
    )

def filter_by_name(items, search):
    search = search.casefold()
    return [item for item in items if search in item.name.casefold()]

class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.order_by("id")
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    def get_category(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_category(pk)
        if category is None:
            return error_response("Категорію не знайдено.", status.HTTP_404_NOT_FOUND)
        return Response(CategoryDetailSerializer(category).data)

    def put(self, request, pk):
        category = self.get_category(pk)
        if category is None:
            return error_response("Категорію не знайдено.", status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        category = self.get_category(pk)
        if category is None:
            return error_response("Категорію не знайдено.", status.HTTP_404_NOT_FOUND)
        recipes_count = category.recipes.count()
        if recipes_count > 0:
            return error_response(
                f"Неможливо видалити категорію «{category.name}», оскільки "
                f"в ній є рецепти: {recipes_count}. Спершу видаліть їх "
                "або перенесіть в іншу категорію.",
                status.HTTP_409_CONFLICT,
            )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.order_by("id")
        search = request.query_params.get("search")
        if search:
            products = filter_by_name(products, search)
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    def get_product(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_product(pk)
        if product is None:
            return error_response("Продукт не знайдено.", status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

    def put(self, request, pk):
        product = self.get_product(pk)
        if product is None:
            return error_response("Продукт не знайдено.", status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        product = self.get_product(pk)
        if product is None:
            return error_response("Продукт не знайдено.", status.HTTP_404_NOT_FOUND)
        recipes_count = product.recipe_ingredients.count()
        if recipes_count > 0:
            return error_response(
                f"Неможливо видалити продукт «{product.name}», оскільки він "
                f"використовується в рецептах: {recipes_count}.",
                status.HTTP_409_CONFLICT,
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)