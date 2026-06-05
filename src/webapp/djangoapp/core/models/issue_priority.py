from django.db import models
from django.utils.translation import gettext_lazy as _


class IssuePriority(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")
