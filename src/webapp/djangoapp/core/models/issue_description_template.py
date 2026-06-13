from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class IssueDescriptionTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description_markdown = models.TextField()
    collection = models.ForeignKey(
        "core.Collection",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="issue_description_templates",
        help_text=_("Limit this template to one collection."),
    )
    category = models.ForeignKey(
        "core.IssueCategory",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="issue_description_templates",
        help_text=_("Limit this template to one issue category."),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Issue description template")
        verbose_name_plural = _("Issue description templates")

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.collection_id or self.category_id:
            return

        raise ValidationError({
            "collection": _("Select a collection or an issue category."),
            "category": _("Select a collection or an issue category."),
        })
