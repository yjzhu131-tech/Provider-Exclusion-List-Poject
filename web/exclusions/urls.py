from django.urls import path

from . import views


app_name = "exclusions"

urlpatterns = [
    path("", views.search, name="search"),
    path("results/", views.results, name="results"),
    path("party/<int:party_id>/", views.detail, name="detail"),
    path("sources/", views.sources, name="sources"),
]
