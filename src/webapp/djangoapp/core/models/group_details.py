from django.contrib.auth.models import Group
from django.db import models


class GroupDetails(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="core_details")
    description = models.TextField(blank=True, default="")
