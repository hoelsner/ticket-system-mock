from django.conf import settings
from django.utils import translation

from .controllers import get_user_profile


class UserProfileLocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        active_language = None
        original_language = translation.get_language()
        supported_languages = {code for code, _label in settings.LANGUAGES}

        if getattr(request, "user", None) and request.user.is_authenticated:
            profile = get_user_profile(request.user)
            if profile.language_preference in supported_languages:
                active_language = profile.language_preference
                translation.activate(active_language)
                request.LANGUAGE_CODE = active_language

        response = self.get_response(request)

        if active_language:
            response.headers.setdefault("Content-Language", active_language)
            translation.activate(original_language)

        return response
