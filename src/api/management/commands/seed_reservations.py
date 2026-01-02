from __future__ import annotations

import uuid
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Reservation

class Command(BaseCommand):
    help = "Seed database with sample reservations (5 rooms) for development/testing."

    ROOMS = {
        uuid.UUID("11111111-1111-1111-1111-111111111111"),
        uuid.UUID("22222222-2222-2222-2222-222222222222"),
        uuid.UUID("33333333-3333-3333-3333-333333333333"),
        uuid.UUID("44444444-4444-4444-4444-444444444444"),
        uuid.UUID("55555555-5555-5555-5555-555555555555"),
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all reservations before seeding."
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Reservation.objects.all().delete()
            self.stdout.write(self.style.WARNING("Deleted all reservations"))

        created = 0

        #3 aktive + 1 deleted
        for idx, room_id in enumerate(self.ROOMS, start=1):
            base_month = idx
            samples = [
                (room_id, date(2026, base_month, 1),  date(2026, base_month, 3),  None),
                (room_id, date(2026, base_month, 10), date(2026, base_month, 12), None),
                (room_id, date(2026, base_month, 20), date(2026, base_month, 22), None),
                (room_id, date(2026, base_month, 25), date(2026, base_month, 26), timezone.now()),
            ]

            for room_id, frm, to, deleted_at in samples:
                Reservation.objects.create(
                    room_id = room_id,
                    from_date = frm,
                    to_date = to,
                    deleted_at = deleted_at
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeding done. Created {created} reservations"))
        self.stdout.write("Room IDs:")
        for r in self.ROOMS:
            self.stdout.write(f" - {r}")