from django.contrib.auth.models import Group


class GroupController:
    @staticmethod
    def create(cleaned_data):
        user_set = cleaned_data.pop("user_ids", [])
        group = Group.objects.create(**cleaned_data)
        group.user_set.set(user_set)
        return group

    @staticmethod
    def update(group, cleaned_data):
        user_set = cleaned_data.pop("user_ids", None)

        for field, value in cleaned_data.items():
            setattr(group, field, value)

        group.save()

        if user_set is not None:
            group.user_set.set(user_set)

        return group

    @staticmethod
    def delete(group):
        group.delete()
