from django.urls import path

from . import views

urlpatterns = [
    path("categories", views.CategoryListView.as_view()),
    path("categories/<int:pk>", views.CategoryDetailView.as_view()),
    path("products", views.ProductListView.as_view()),
    path("products/<int:pk>", views.ProductDetailView.as_view()),
    path("recipes", views.RecipeListView.as_view()),
    path("recipes/<int:pk>", views.RecipeDetailView.as_view()),
]