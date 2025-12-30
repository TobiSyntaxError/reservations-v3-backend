from django.urls import path
from . import views

urlpatterns = [
    path("api/v3/reservations/status", views.StatusView.as_view()),
    path("api/v3/reservations/health", views.HealthView.as_view(action="summary")),
    path("api/v3/reservations/health/live", views.HealthView.as_view(action="live")),
    path("api/v3/reservations/health/ready", views.HealthView.as_view(action="ready"))
]
