from django.db import models
from django.utils.translation import gettext_lazy as _


class IssueCommentVisibility(models.TextChoices):
    INTERNAL = "INTERNAL", _("Internal")
    CUSTOMER_VISIBLE = "CUSTOMER_VISIBLE", _("Customer visible")
