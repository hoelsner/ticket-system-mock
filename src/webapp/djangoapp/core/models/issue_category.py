from django.db import models
from django.utils.translation import gettext_lazy as _


class IssueCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Issue category")
        verbose_name_plural = _("Issue categories")

    def __str__(self):
        return self.name
