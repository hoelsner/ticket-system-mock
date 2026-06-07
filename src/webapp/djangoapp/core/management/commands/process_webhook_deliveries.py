from django.core.management.base import BaseCommand
from djangoapp.core.controllers import WebhookDeliveryController


class Command(BaseCommand):
    help = "Process pending and retryable webhook deliveries."

    def handle(self, *args, **options):
        processed_event_ids = WebhookDeliveryController.process_pending_events()
        if not processed_event_ids:
            self.stdout.write("No webhook deliveries were processed.")
            return

        self.stdout.write(self.style.SUCCESS(f"Processed webhook deliveries for {len(processed_event_ids)} event(s)."))
