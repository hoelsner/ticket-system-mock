from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _


def user_profile_avatar_upload_to(instance, filename):
    return f"user-profiles/{instance.user_id}/avatar/{filename}"


class UserProfile(models.Model):
    AVATAR_TYPE_INITIALS = "initials"
    AVATAR_TYPE_IMAGE = "image"

    LANGUAGE_PREFERENCE_CHOICES = list(settings.LANGUAGES)
    AVATAR_TYPE_CHOICES = [
        (AVATAR_TYPE_INITIALS, _("Initials")),
        (AVATAR_TYPE_IMAGE, _("Uploaded image")),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    language_preference = models.CharField(
        max_length=16,
        choices=LANGUAGE_PREFERENCE_CHOICES,
        default=settings.LANGUAGE_CODE,
        help_text=_("Choose one of the configured application languages."),
    )
    avatar_type = models.CharField(
        max_length=16,
        choices=AVATAR_TYPE_CHOICES,
        default=AVATAR_TYPE_INITIALS,
        help_text=_("Choose whether the profile should render initials or an image by default."),
    )
    is_system_user = models.BooleanField(
        default=False,
        help_text=_("Use the system-agent avatar when no custom avatar image is uploaded."),
    )
    avatar_image = models.FileField(
        upload_to=user_profile_avatar_upload_to,
        blank=True,
        help_text=_("Optional avatar image shown everywhere the user appears."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User profile")
        verbose_name_plural = _("User profiles")

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        previous_avatar_name = None
        if self.pk:
            previous_avatar_name = (
                type(self).objects.filter(pk=self.pk).values_list("avatar_image", flat=True).first() or None
            )

        super().save(*args, **kwargs)

        current_avatar_name = self.avatar_image.name or None
        if previous_avatar_name and previous_avatar_name != current_avatar_name:
            self.avatar_image.storage.delete(previous_avatar_name)

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.get_username()

    @property
    def avatar_image_url(self):
        if self.avatar_type != self.AVATAR_TYPE_IMAGE:
            return None
        if self.avatar_image:
            return self.avatar_image.url
        if self.is_system_user:
            return static("img/default_avatar_agent.png")
        return None

    @property
    def avatar_uses_image(self):
        return bool(self.avatar_image_url)

    @property
    def avatar_text(self):
        full_name = (self.user.get_full_name() or self.user.get_username()).strip()
        name_parts = [part[0] for part in full_name.split() if part]
        if len(name_parts) >= 2:
            return "".join(name_parts[:2]).upper()
        return full_name[:2].upper() or self.user.get_username()[:2].upper()


def ensure_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def create_missing_user_profiles():
    for user in get_user_model().objects.all().iterator():
        ensure_user_profile(user)
