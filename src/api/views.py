from __future__ import annotations

#from typing import Any
#from django.http import JsonResponse, HttpRequest, HttpResponse
#from django.views import View
#from django.db import connection
#from datetime import date, timezone as dt_timezone
#from django.utils import timezone
#from django.db.utils import OperationalError
#
#import json
#from datetime import date
#from uuid import UUID
#
#from .models import Reservation

from __future__ import annotations

import json
from datetime import date, timezone as dt_timezone
from typing import Any
from uuid import UUID

from django.db import connection
from django.db.utils import OperationalError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views import View

from .models import Reservation

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
        
    def _error(self, message: str, *, status: int = 503, code: str = "bad_request") -> JsonResponse:
        return JsonResponse(
            {"errors": [{"code": code, "message": message}]},
            status=status
        )
        
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
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



def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

def _parse_uuid(value: str) -> UUID:
    return UUID(value)

def _parse_date(value: str) -> date:
    return date.fromisoformat(value)

def _error_container(message: str, *, status: int, code: str = "bad_request", more_info: str | None = None) -> JsonResponse:
    payload: dict[str, Any] = {
        "errors": [{"code": code, "message": message}],
        "trace": str(__import__("uuid").uuid4()),
    }
    if more_info is not None:
        payload["errors"][0]["more_info"] = more_info
    return JsonResponse(payload, status=status)

def _rfc3339(dt) -> str:
    if dt is None:
        return ""
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    dt_utc = dt.astimezone(dt_timezone.utc)
    s = dt_utc.isoformat(timespec="milliseconds")
    return s.replace("+00:00", "Z")

def _reservations_to_dict(r: Reservation) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": str(r.id),
        "from": r.from_date.isoformat(),
        "to": r.to_date.isoformat(),
        "room_id": str(r.room_id),
    }
    if r.deleted_at is not None:
        data["deleted_at"] = _rfc3339(r.deleted_at)
    return data

def _validate_prototype(payload: dict[str, Any]) -> tuple[date, date, UUID] | JsonResponse:
    for k in ("from", "to", "room_id"):
        if k not in payload:
            return _error_container(f'Missing required property "{k}".', status=400)
        
    try:
        from_d = _parse_date(payload["from"])
        to_d = _parse_date(payload["to"])
        room_id = _parse_uuid(payload["room_id"])
    except Exception:
        return _error_container("Invalid Input (date/uuid parsing failed).", status=400)
    
    if not (from_d < to_d):
        return _error_container('Invalid Input: "from" must be < "to".', status=400) 
    
    return from_d, to_d, room_id

def _overlaps_exists(*, room_id: UUID, from_d: date, to_d: date, exclude_id: UUID | None = None) -> bool:
    qs = Reservation.objects.filter(room_id=room_id, deleted_at__isnull=True)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)

    return qs.filter(from_date__lt=to_d, to_date__gt=from_d).exists()

class ReservationView(View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        include_deleted = _parse_bool(value=request.GET.get("include_deleted"))
        
        qs = Reservation.objects.all()
        if not include_deleted:
            qs = qs.filter(deleted_at__isnull=True)

        room_id_raw = request.GET.get("room_id")
        if room_id_raw:
            try:
                room_id = _parse_uuid(room_id_raw)
            except Exception:
                return _error_container("Invalid room_id (must be uuid).", status=400)
            qs = qs.filter(room_id=room_id)

        before_raw = request.GET.get("before")
        if before_raw:
            try:
                before_d = _parse_date(before_raw)
            except Exception:
                return _error_container("Invalid before (must be date YYYY-MM-DD)", status=400)
            qs = qs.filter(from_date__lte=before_d)

        after_raw = request.GET.get("after")
        if after_raw:
            try:
                after_d = _parse_date(after_raw)
            except Exception:
                return _error_container("Invalid after (must be date YYYY-MM-DD)", status=400)
            qs = qs.filter(to_date__gte=after_d)

        qs = qs.order_by("from_date", "to_date", "id")

        return JsonResponse({"reservations": [_reservations_to_dict(r) for r in qs]}, status=200)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            payload= json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return _error_container("Invalid JSON body.", status=400)
        
        if not isinstance(payload, dict):
            return _error_container("Invalid JSON body (must be object)", status=400)
        validated = _validate_prototype(payload)
        if isinstance(validated, JsonResponse):
            return validated
        
        from_d, to_d, room_id = validated

        if _overlaps_exists(room_id=room_id, from_d=from_d, to_d=to_d):
            return _error_container(
                "Invalid input: reservation overlaps with an existing reservation.",
                status=400,
                more_info="Reservations on rooms MUST NOT overlap"
            )
        reservation = Reservation.objects.create(room_id=room_id, from_date=from_d, to_date=to_d)

        return JsonResponse(_reservations_to_dict(reservation), status=201)


class ReservationDetailView(View):
    def _get_uuid(self, raw_id: str) -> UUID | None:
        try:
            return _parse_uuid(raw_id)
        except Exception:
            return None
        
    def get(self, request: HttpRequest, id: str, *args: Any, **kwargs: Any) -> JsonResponse:
        rid = self._get_uuid(id)
        if rid is None:
            return _error_container("invalid id (must be uuid).", status=400)
        
        reservation = Reservation.objects.filter(id=rid).first()
        if reservation is None:
            return _error_container("Reservation not found.", status=404, code="no_need_to_know")
        return JsonResponse(_reservations_to_dict(reservation), status=200)

    def put() -> JsonResponse:
        pass
    
    def delete() -> JsonResponse | HttpResponse:
        pass