from django.contrib.auth.models import Group

from djangoapp.core.models import GroupDetails


class GroupController:
    @staticmethod
    def get_description(group):
        details = getattr(group, "core_details", None)
        return details.description if details is not None else ""

    @staticmethod
    def create(cleaned_data):
        user_set = cleaned_data.pop("user_ids", [])
        description = cleaned_data.pop("description", "")
        group = Group.objects.create(**cleaned_data)
        GroupController._set_description(group, description)
        group.user_set.set(user_set)
        return group

    @staticmethod
    def update(group, cleaned_data):
        user_set = cleaned_data.pop("user_ids", None)
        description = cleaned_data.pop("description", "")

        for field, value in cleaned_data.items():
            setattr(group, field, value)

        group.save()
        GroupController._set_description(group, description)

        if user_set is not None:
            group.user_set.set(user_set)

        return group

    @staticmethod
    def delete(group):
        group.delete()

    @staticmethod
    def _set_description(group, description):
        details, _created = GroupDetails.objects.get_or_create(group=group)
        details.description = description
        details.save(update_fields=["description"])
        group.core_details = details
