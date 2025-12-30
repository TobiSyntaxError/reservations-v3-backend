from __future__ import annotations

from typing import Any
from django.http import JsonResponse, HttpRequest
from django.views import View
from django.db import connection
from django.db.utils import OperationalError

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


#def status(request):
#    return JsonResponse({"authors": ["Tobias", "Daniel", "TestUser"]})
#

class HelathView(View):
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
        
    def get(self, requst: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        if self.action == "live":
            return JsonResponse({"live": True}, status=200)
        
        if self.action == "ready":
            ready = self._db_ready()
            if ready == True:
                return JsonResponse({"ready": True}, status=200)
            return JsonResponse(
                {"errors": [{"code": "bad_request", "message": "Service not ready (database connection failed)."}]},
                status=503,
            )
        live = True
        ready = self._db_ready()
        return JsonResponse(
            {
                "live": live,
                "ready": ready,
                "databases": {"reservations": {"connected": ready}},
            },
            status=200
        )


def health(request):
    return JsonResponse({"live": True, "ready": True})