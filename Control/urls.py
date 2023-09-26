from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_functions),
    path('update_geojson/ijpp_stations', views.update_geojson_ijppp_stations),
]