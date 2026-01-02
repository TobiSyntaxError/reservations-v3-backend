from __future__ import annotations

from typing import Any
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views import View
from django.db import connection
from django.utils import timezone
from django.db.utils import OperationalError

import json
from datetime import date
from uuid import UUID

from models import Reservation

class StatusView(View):
    AUTHORS = ["Tobias Kipping", "Daniel Lohrengel"]
    API_VERSION = "3.0.0"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        return JsonResponse (
            {
                "authors": self.AUTHORS,
                "api_version": self.API_VERSION
            }

        )

class HealthView(View):
    action: str = "summary" # "summary" | "live" | "ready"

    def _db_ready(self) -> bool:
        try:
            connection.ensure_connection()
            with connection.cursor() as c:
                c.execute("SELECT 1")
                c.fetchone()
            return True
        except OperationalError:
            return False
        
    def _error(message: str, *, status: int = 503, code: str = "bad_request") -> JsonResponse:
        return JsonResponse(
            {"errors": [{"code": code, "message": message}]},
            status=status
        )
        
    def get(self, requst: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        if self.action == "live":
            return JsonResponse({"live": True}, status=200)
        
        if self.action == "ready":
            ready = self._db_ready()
            if ready == True:
                return JsonResponse({"ready": True}, status=200)
            return self._error("Service not ready (database connection failed).", status=503)
            
        ready = self._db_ready()
        live = True
        return JsonResponse(
            {
                "live": live,
                "ready": ready,
                "databases": {"reservations": {"connected": ready}},
            },
            status=200
        )
    

class ReservationView(View):
    def get(self, requst: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        pass

    def post(self, requst: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        pass

class ReservationDetailView(View):
    def get() -> JsonResponse:
        pass

    def put() -> JsonResponse:
        pass
    
    def put() -> JsonResponse | HttpResponse:
        pass