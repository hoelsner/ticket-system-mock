from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Collection(models.Model):
    name = models.CharField(max_length=100, unique=True)
    prefix = models.CharField(
        max_length=16,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z][A-Z0-9]*$",
                message=_("Use uppercase letters and digits only, starting with a letter."),
            )
        ],
        help_text=_("Prefix used for issue identifiers, for example TASK."),
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    next_issue_sequence = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.prefix})"
