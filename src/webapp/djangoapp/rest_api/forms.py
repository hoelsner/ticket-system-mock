from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from djangoapp.core.models import Collection, IssueAttachment, IssueCategory, IssueComment
from djangoapp.user_interface.models import UserProfile


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["name", "prefix", "description", "is_active", "next_issue_sequence"]


class IssueCategoryForm(forms.ModelForm):
    class Meta:
        model = IssueCategory
        fields = ["name", "code", "description", "is_active"]


class IssueCommentUpdateForm(forms.ModelForm):
    class Meta:
        model = IssueComment
        fields = ["body", "visibility"]


class IssueAttachmentForm(forms.ModelForm):
    class Meta:
        model = IssueAttachment
        fields = ["file", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["file"].required = False


class UserManagementForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    password = forms.CharField(required=False, strip=False)
    is_active = forms.BooleanField(required=False)
    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)
    language_preference = forms.ChoiceField(choices=settings.LANGUAGES, required=False)
    avatar_type = forms.ChoiceField(choices=UserProfile.AVATAR_TYPE_CHOICES, required=False)
    is_system_user = forms.BooleanField(required=False)
    group_ids = forms.ModelMultipleChoiceField(queryset=Group.objects.order_by("name"), required=False)

    def __init__(self, *args, instance=None, require_password=False, **kwargs):
        self.instance = instance
        self.require_password = require_password
        super().__init__(*args, **kwargs)
        if require_password:
            self.fields["password"].required = True

        if instance is not None:
            profile = instance.profile
            self.initial.setdefault("username", instance.username)
            self.initial.setdefault("first_name", instance.first_name)
            self.initial.setdefault("last_name", instance.last_name)
            self.initial.setdefault("is_active", instance.is_active)
            self.initial.setdefault("is_staff", instance.is_staff)
            self.initial.setdefault("is_superuser", instance.is_superuser)
            self.initial.setdefault("language_preference", profile.language_preference)
            self.initial.setdefault("avatar_type", profile.avatar_type)
            self.initial.setdefault("is_system_user", profile.is_system_user)
            self.initial.setdefault("group_ids", instance.groups.order_by("name").values_list("pk", flat=True))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        user_model = get_user_model()
        queryset = user_model.objects.filter(username=username)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        if self.require_password and not password:
            raise forms.ValidationError("This field is required.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("is_superuser"):
            cleaned_data["is_staff"] = True
        return cleaned_data


class GroupManagementForm(forms.Form):
    name = forms.CharField(max_length=150)
    user_ids = forms.ModelMultipleChoiceField(queryset=get_user_model().objects.order_by("username"), required=False)

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is not None:
            self.initial.setdefault("name", instance.name)
            self.initial.setdefault("user_ids", instance.user_set.order_by("username").values_list("pk", flat=True))

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        queryset = Group.objects.filter(name=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("A group with that name already exists.")
        return name
