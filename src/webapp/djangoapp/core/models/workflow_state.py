from django.db import models
from django.utils.translation import gettext_lazy as _


class WorkflowState(models.TextChoices):
    NEW = "NEW", _("New")
    TRIAGE = "TRIAGE", _("Triage")
    ASSIGNED = "ASSIGNED", _("Assigned")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    WAITING = "WAITING", _("Waiting")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")
    REJECTED = "REJECTED", _("Rejected")
