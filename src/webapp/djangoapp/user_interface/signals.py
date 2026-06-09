from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ensure_user_profile


@receiver(post_save, sender=get_user_model())
def ensure_profile_for_user(sender, instance, **kwargs):
    ensure_user_profile(instance)
