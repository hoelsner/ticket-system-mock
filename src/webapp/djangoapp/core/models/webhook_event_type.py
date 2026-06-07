from django.db import models
from django.utils.translation import gettext_lazy as _


class WebhookEventType(models.TextChoices):
    ISSUE_CREATED = "issue.created", _("Issue created")
    ISSUE_UPDATED = "issue.updated", _("Issue updated")
    ISSUE_QUEUE_ASSIGNED = "issue.queue_assigned", _("Issue queue assigned")
    ISSUE_COMMENTED = "issue.commented", _("Issue commented")
    ISSUE_CLOSED = "issue.closed", _("Issue closed")
