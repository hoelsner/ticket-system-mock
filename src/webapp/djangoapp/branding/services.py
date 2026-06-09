from dataclasses import dataclass

from django.conf import settings
from django.templatetags.static import static

from .models import AppBranding


@dataclass(frozen=True)
class BrandingSnapshot:
    display_name: str
    logo_url: str
    login_background_url: str
    login_message_text: str
    login_message_level: str
    light_primary_color: str
    light_primary_hover_color: str
    dark_primary_color: str
    dark_primary_hover_color: str


def get_branding_snapshot():
    branding = AppBranding.objects.first()
    display_name = settings.PRODUCT_DISPLAY_NAME
    logo_url = static("img/default_app_logo.png")
    login_background_url = static("img/default_app_hero_image.png")
    login_message_text = ""
    login_message_level = "info"
    light_primary_color = "#0172ad"
    light_primary_hover_color = "#015887"
    dark_primary_color = "#01aaff"
    dark_primary_hover_color = "#79c0ff"

    if not branding:
        return BrandingSnapshot(
            display_name=display_name,
            logo_url=logo_url,
            login_background_url=login_background_url,
            login_message_text=login_message_text,
            login_message_level=login_message_level,
            light_primary_color=light_primary_color,
            light_primary_hover_color=light_primary_hover_color,
            dark_primary_color=dark_primary_color,
            dark_primary_hover_color=dark_primary_hover_color,
        )

    if branding.display_name_override:
        display_name = branding.display_name_override
    if branding.logo_image:
        logo_url = branding.logo_image.url
    if branding.login_background_image:
        login_background_url = branding.login_background_image.url
    if branding.login_message_text:
        login_message_text = branding.login_message_text
    login_message_level = branding.login_message_level
    light_primary_color = branding.light_primary_color
    light_primary_hover_color = branding.light_primary_hover_color
    dark_primary_color = branding.dark_primary_color
    dark_primary_hover_color = branding.dark_primary_hover_color

    return BrandingSnapshot(
        display_name=display_name,
        logo_url=logo_url,
        login_background_url=login_background_url,
        login_message_text=login_message_text,
        login_message_level=login_message_level,
        light_primary_color=light_primary_color,
        light_primary_hover_color=light_primary_hover_color,
        dark_primary_color=dark_primary_color,
        dark_primary_hover_color=dark_primary_hover_color,
    )
