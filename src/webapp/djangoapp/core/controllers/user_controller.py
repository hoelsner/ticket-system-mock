from django.contrib.auth import get_user_model

from djangoapp.user_interface.models import ensure_user_profile


class UserController:
    @staticmethod
    def create(cleaned_data):
        group_set = cleaned_data.pop("group_ids", [])
        password = cleaned_data.pop("password", "")
        profile_data = UserController._pop_profile_data(cleaned_data)

        user_model = get_user_model()
        user = user_model.objects.create_user(password=password, **cleaned_data)
        user.groups.set(group_set)
        UserController._update_profile(user, profile_data)
        return user

    @staticmethod
    def update(user, cleaned_data):
        group_set = cleaned_data.pop("group_ids", None)
        password = cleaned_data.pop("password", "")
        profile_data = UserController._pop_profile_data(cleaned_data)

        for field, value in cleaned_data.items():
            setattr(user, field, value)

        if password:
            user.set_password(password)

        user.save()

        if group_set is not None:
            user.groups.set(group_set)

        UserController._update_profile(user, profile_data)
        return user

    @staticmethod
    def deactivate(user):
        user.is_active = False
        user.save(update_fields=["is_active"])
        return user

    @staticmethod
    def _pop_profile_data(cleaned_data):
        return {
            "language_preference": cleaned_data.pop("language_preference", ""),
            "avatar_type": cleaned_data.pop("avatar_type", ""),
            "is_system_user": cleaned_data.pop("is_system_user", False),
        }

    @staticmethod
    def _update_profile(user, profile_data):
        profile = ensure_user_profile(user)

        if profile_data["language_preference"]:
            profile.language_preference = profile_data["language_preference"]
        if profile_data["avatar_type"]:
            profile.avatar_type = profile_data["avatar_type"]
        profile.is_system_user = profile_data["is_system_user"]
        profile.save()
        return profile
