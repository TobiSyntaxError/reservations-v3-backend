from django.http import JsonResponse

from __future__ import annotations
from typing import Any
from django.http import JsonResponse, HttpRequest
from django.views import View

class StatusView(View):
    AUTHORS = ["Tobias Kipping", "Daniel Lohrengel"]
    API_VESION = "3.0.0"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        return JsonResponse (
            {
                "authors": self.AUTHORS,
                "api_version": self.API_VESION
            }

        )


#def status(request):
#    return JsonResponse({"authors": ["Tobias", "Daniel", "TestUser"]})
#
#def health(request):
#    return JsonResponse({"live": True, "ready": True})