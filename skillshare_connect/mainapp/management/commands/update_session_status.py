# mainapp/management/commands/update_session_status.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from mainapp.models import Session

class Command(BaseCommand):
    help = "Update session statuses (scheduled → completed if end_time <= now)."

    def handle(self, *args, **options):
        now = timezone.now()
        sessions = Session.objects.filter(status="scheduled")
        updated = 0

        for s in sessions:
            if s.end_time and s.end_time <= now:
                # Force update with model's save logic
                s.status = "completed"
                s.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated} sessions"))
