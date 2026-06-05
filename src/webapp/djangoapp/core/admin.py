from django.contrib import admin

from .controllers import IssueController
from .models import (
    Collection,
    Issue,
    IssueAttachment,
    IssueCategory,
    IssueComment,
    IssueCommentMention,
    IssueStateTransition,
)


class IssueAttachmentInline(admin.TabularInline):
    model = IssueAttachment
    extra = 0


class IssueCommentInline(admin.TabularInline):
    model = IssueComment
    extra = 0
    fields = ("author_user", "visibility", "body", "created_at")
    readonly_fields = ("created_at",)


class IssueStateTransitionInline(admin.TabularInline):
    model = IssueStateTransition
    extra = 0
    fields = ("from_state", "to_state", "changed_by_user", "changed_at", "reason")
    readonly_fields = ("from_state", "to_state", "changed_by_user", "changed_at", "reason")
    can_delete = False


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "prefix", "is_active", "next_issue_sequence")
    list_filter = ("is_active",)
    search_fields = ("name", "prefix")
    ordering = ("name",)


@admin.register(IssueCategory)
class IssueCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        "issue_number",
        "collection",
        "title",
        "workflow_state",
        "priority",
        "category",
        "collection",
        "group",
        "user",
        "is_escalated",
        "archived_at",
        "updated_at",
    )
    list_filter = (
        "workflow_state",
        "priority",
        "is_escalated",
        "category",
        "group",
    )
    search_fields = ("issue_number", "title", "description_markdown")
    readonly_fields = (
        "issue_number",
        "created_at",
        "updated_at",
        "resolved_at",
        "closed_at",
        "archived_at",
        "archived_by_user",
    )
    inlines = (IssueAttachmentInline, IssueCommentInline, IssueStateTransitionInline)

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return

        original = Issue.objects.get(pk=obj.pk)
        if original.workflow_state != obj.workflow_state:
            original.title = obj.title
            original.description_markdown = obj.description_markdown
            original.collection = obj.collection
            original.category = obj.category
            original.priority = obj.priority
            original.group = obj.group
            original.user = obj.user
            original.is_escalated = obj.is_escalated
            original.escalated_at = obj.escalated_at
            IssueController.update_workflow_state(
                original,
                obj.workflow_state,
                changed_by_user=request.user,
            )
            return

        super().save_model(request, obj, form, change)


@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ("issue", "author_user", "visibility", "created_at")
    list_filter = ("visibility", "created_at")
    search_fields = ("issue__issue_number", "author_user__username", "body")
    readonly_fields = ("created_at",)


@admin.register(IssueCommentMention)
class IssueCommentMentionAdmin(admin.ModelAdmin):
    list_display = ("issue_comment", "mentioned_user", "mentioned_as", "created_at")
    list_filter = ("created_at",)
    search_fields = ("issue_comment__issue__issue_number", "mentioned_user__username", "mentioned_as")
    readonly_fields = ("created_at",)


@admin.register(IssueStateTransition)
class IssueStateTransitionAdmin(admin.ModelAdmin):
    list_display = ("issue", "from_state", "to_state", "changed_by_user", "changed_at")
    list_filter = ("from_state", "to_state", "changed_at")
    search_fields = ("issue__issue_number", "changed_by_user__username", "reason")
    readonly_fields = ("issue", "from_state", "to_state", "changed_by_user", "changed_at", "reason")

    def has_add_permission(self, request):
        return False


@admin.register(IssueAttachment)
class IssueAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "issue", "uploaded_by_user", "uploaded_at", "file_size")
    list_filter = ("uploaded_at",)
    search_fields = ("original_filename", "issue__issue_number", "uploaded_by_user__username")
    readonly_fields = ("uploaded_at",)
