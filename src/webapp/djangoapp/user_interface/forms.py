from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from djangoapp.core.models import (
    Collection,
    Issue,
    IssueCategory,
    IssueComment,
    IssueDescriptionTemplate,
    WorkflowState,
)
from djangoapp.user_interface.models import UserProfile


def _get_user_queryset(group_id=None):
    user_model = get_user_model()
    queryset = user_model.objects.order_by("username")
    if group_id:
        return queryset.filter(groups__id=group_id).distinct()
    return queryset


def _missing_group_for_user(group, user):
    return bool(user and not group)


def _user_not_in_group(group, user):
    return bool(group and user and not user.groups.filter(pk=group.pk).exists())


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_file_clean(file_item, initial) for file_item in data]
        return [single_file_clean(data, initial)]


class IssueBaseForm(forms.ModelForm):
    attachment_file = forms.FileField(required=False)
    attachment_description = forms.CharField(max_length=255, required=False)

    class Meta:
        model = Issue
        fields = [
            "title",
            "description_markdown",
            "collection",
            "category",
            "priority",
            "group",
            "user",
            "is_escalated",
        ]
        widgets = {
            "description_markdown": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collection"].queryset = Collection.objects.filter(is_active=True).order_by("name")
        self.fields["category"].queryset = IssueCategory.objects.filter(is_active=True).order_by("name")
        self.fields["group"].queryset = Group.objects.order_by("name")
        self.fields["user"].queryset = _get_user_queryset(self._get_group_id())

    def _get_group_id(self):
        if self.is_bound:
            return self.data.get("group")
        if self.instance.pk and self.instance.group_id:
            return self.instance.group_id
        return self.initial.get("group")

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get("group")
        user = cleaned_data.get("user")
        attachment_file = cleaned_data.get("attachment_file")
        attachment_description = cleaned_data.get("attachment_description")

        self._add_assignment_errors(group, user)
        self._add_attachment_errors(attachment_file, attachment_description)

        return cleaned_data

    def _add_assignment_errors(self, group, user):
        if _missing_group_for_user(group, user):
            self.add_error("group", _("A group is required when a user is assigned."))
            return

        if _user_not_in_group(group, user):
            self.add_error("user", _("The assigned user must belong to the assigned group."))

    def _add_attachment_errors(self, attachment_file, attachment_description):
        if attachment_description and not attachment_file:
            self.add_error("attachment_file", _("Select a file when providing an attachment description."))


class IssueCreateForm(IssueBaseForm):
    attachment_file = MultipleFileField(required=False)
    attachment_draft_token = forms.CharField(required=False, widget=forms.HiddenInput)
    description_template = forms.ChoiceField(required=False, label=_("Description template"))
    workflow_state = forms.ChoiceField(choices=WorkflowState.choices, initial=WorkflowState.NEW, required=False)

    def __init__(self, *args, show_workflow_state=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.description_template_queryset = list(
            IssueDescriptionTemplate.objects
            .filter(is_active=True)
            .select_related("collection", "category")
            .order_by("name")
        )
        self.fields["description_template"].choices = [("", _("Select a template"))] + [
            (str(template.pk), template.name) for template in self.description_template_queryset
        ]
        self.fields["description_template"].help_text = _(
            "Choose a predefined template. You can edit the description before creating the issue."
        )
        if not show_workflow_state:
            self.fields["workflow_state"].widget = forms.HiddenInput()

    def get_description_template_metadata(self):
        return [
            {
                "id": str(template.pk),
                "name": template.name,
                "description_markdown": template.description_markdown,
                "collection_id": str(template.collection_id) if template.collection_id else "",
                "category_id": str(template.category_id) if template.category_id else "",
            }
            for template in self.description_template_queryset
        ]


class IssueUpdateForm(IssueBaseForm):
    workflow_state = forms.ChoiceField(choices=WorkflowState.choices)
    transition_reason = forms.CharField(max_length=255, required=False)

    class Meta(IssueBaseForm.Meta):
        fields = IssueBaseForm.Meta.fields + ["workflow_state"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["workflow_state"].initial = self.instance.workflow_state


class IssueDescriptionForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ["description_markdown"]
        widgets = {
            "description_markdown": forms.Textarea(attrs={"rows": 8}),
        }


class IssueCommentForm(forms.ModelForm):
    attachment_file = forms.FileField(required=False)
    attachment_description = forms.CharField(max_length=255, required=False)

    class Meta:
        model = IssueComment
        fields = ["body", "visibility"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }


class IssueArchiveForm(forms.Form):
    confirm_archive = forms.BooleanField(label=_("I understand this issue will be archived."))


class UserProfileForm(forms.ModelForm):
    clear_avatar_image = forms.BooleanField(required=False, label=_("Remove current avatar image"))

    class Meta:
        model = UserProfile
        fields = ["language_preference", "avatar_type", "is_system_user", "avatar_image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["language_preference"].label = _("Language preference")
        self.fields["language_preference"].choices = [
            (code, code.upper()) for code, _label in UserProfile.LANGUAGE_PREFERENCE_CHOICES
        ]
        self.fields["avatar_type"].label = _("Avatar type")
        self.fields["is_system_user"].label = _("System user")
        self.fields["avatar_image"].label = _("Avatar image")
