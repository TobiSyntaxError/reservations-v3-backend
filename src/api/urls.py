from django.urls import path
from . import views

urlpatterns = [
    path("api/v3/reservations/status", views.StatusView.as_view())
    #path("api/v3/reservations/health", views.health),
]
