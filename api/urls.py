from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_data),
    path('path/', views.get_path),
    path('autocomplete/', views.get_search_recommendations)
]