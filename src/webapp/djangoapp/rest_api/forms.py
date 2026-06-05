from django import forms

from djangoapp.core.models import Collection, IssueAttachment, IssueCategory, IssueComment


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
