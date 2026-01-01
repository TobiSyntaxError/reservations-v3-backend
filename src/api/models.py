import uuid
from django.db import models

class Reservations(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_id = models.UUIDField()
    from_date = models.DateField()
    to_date = models.DateField()
    delete_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["room_id", "from_date", "to_date"]),
            models.Index(fields=["delete_at"])
        ]

    def __str__(self) -> str:
        return f"Reservatio({self.id})"