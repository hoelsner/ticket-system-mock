from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .controllers import IssueController, WebhookController
from .models import (
    Collection,
    GroupDetails,
    Issue,
    IssueAttachment,
    IssueCategory,
    IssueComment,
    IssueCommentMention,
    IssueDescriptionTemplate,
    IssueHistoryEvent,
    IssueStateTransition,
    WebhookDeliveryAttempt,
    WebhookEndpoint,
    WebhookEvent,
    WebhookEventType,
    WorkflowStateAutoAssignmentRule,
)


class WebhookEndpointEventTypeFilter(admin.SimpleListFilter):
    title = "subscribed event type"
    parameter_name = "subscribed_event_type"

    def lookups(self, request, model_admin):
        return WebhookEventType.choices

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        matching_ids = [endpoint.pk for endpoint in queryset if value in endpoint.subscribed_event_types]
        return queryset.filter(pk__in=matching_ids)


class WebhookEndpointAdminForm(forms.ModelForm):
    subscribed_event_types = forms.MultipleChoiceField(
        choices=WebhookEventType.choices,
        required=False,
    )
    secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the existing signing secret.",
    )

    class Meta:
        model = WebhookEndpoint
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["subscribed_event_types"].initial = self.instance.subscribed_event_types

    def clean_secret(self):
        secret = self.cleaned_data.get("secret", "")
        if secret:
            return secret
        if self.instance.pk:
            return self.instance.secret
        return ""


class GroupAdminForm(forms.ModelForm):
    description = forms.CharField(
        required=False,
        label=_("description"),
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    class Meta:
        model = Group
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            details = getattr(self.instance, "core_details", None)
            self.fields["description"].initial = details.description if details is not None else ""


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin):
    form = GroupAdminForm
    fieldsets = (
        (None, {"fields": ("name", "permissions")}),
        (_("Ticket System Mock"), {"fields": ("description",)}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("name", "permissions", "description")}),)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        details, _created = GroupDetails.objects.get_or_create(group=obj)
        details.description = form.cleaned_data["description"]
        details.save(update_fields=["description"])
        obj.core_details = details


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


class IssueHistoryEventInline(admin.TabularInline):
    model = IssueHistoryEvent
    extra = 0
    fields = ("event_type", "field_name", "old_value", "new_value", "changed_by_user", "changed_at")
    readonly_fields = ("event_type", "field_name", "old_value", "new_value", "changed_by_user", "changed_at")
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


@admin.register(IssueDescriptionTemplate)
class IssueDescriptionTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "collection_name",
        "collection_id_value",
        "category_name",
        "category_id_value",
        "has_collection_scope",
        "has_category_scope",
        "active_status",
    )
    list_filter = ("is_active", "collection", "category")
    search_fields = ("name", "description_markdown")
    ordering = ("name",)

    @admin.display(ordering="collection__name", description="collection")
    def collection_name(self, obj):
        return getattr(obj.collection, "name", "")

    @admin.display(ordering="collection", description="collection id")
    def collection_id_value(self, obj):
        return obj.collection_id

    @admin.display(ordering="category__name", description="category")
    def category_name(self, obj):
        return getattr(obj.category, "name", "")

    @admin.display(ordering="category", description="category id")
    def category_id_value(self, obj):
        return obj.category_id

    @admin.display(boolean=True, description="collection scoped")
    def has_collection_scope(self, obj):
        return obj.collection_id is not None

    @admin.display(boolean=True, description="category scoped")
    def has_category_scope(self, obj):
        return obj.category_id is not None

    @admin.display(boolean=True, ordering="is_active", description="active")
    def active_status(self, obj):
        return obj.is_active


@admin.register(WorkflowStateAutoAssignmentRule)
class WorkflowStateAutoAssignmentRuleAdmin(admin.ModelAdmin):
    list_display = (
        "workflow_state_label",
        "workflow_state_code",
        "group_name",
        "group_id_value",
        "user_name",
        "user_id_value",
        "assigns_user",
        "active_status",
        "last_updated",
    )
    list_filter = ("workflow_state", "is_active", "group")
    search_fields = ("group__name", "user__username")
    ordering = ("workflow_state",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(ordering="workflow_state", description="workflow state")
    def workflow_state_label(self, obj):
        return obj.get_workflow_state_display()

    @admin.display(ordering="workflow_state", description="workflow state code")
    def workflow_state_code(self, obj):
        return obj.workflow_state

    @admin.display(ordering="group__name", description="group")
    def group_name(self, obj):
        return obj.group.name

    @admin.display(ordering="group", description="group id")
    def group_id_value(self, obj):
        return obj.group_id

    @admin.display(ordering="user__username", description="user")
    def user_name(self, obj):
        return getattr(obj.user, "username", "")

    @admin.display(ordering="user", description="user id")
    def user_id_value(self, obj):
        return obj.user_id

    @admin.display(boolean=True, description="assigns user")
    def assigns_user(self, obj):
        return obj.user_id is not None

    @admin.display(boolean=True, ordering="is_active", description="active")
    def active_status(self, obj):
        return obj.is_active

    @admin.display(ordering="updated_at", description="updated at")
    def last_updated(self, obj):
        return obj.updated_at


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
    inlines = (IssueAttachmentInline, IssueCommentInline, IssueStateTransitionInline, IssueHistoryEventInline)

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            WebhookController.create_issue_created_event(obj, actor=request.user)
            return

        original = Issue.objects.get(pk=obj.pk)
        original_snapshot = WebhookController.capture_issue_snapshot(original)
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
            from .controllers import IssueHistoryController

            IssueHistoryController.record_snapshot_changes(original, original_snapshot, request.user)
            WebhookController.create_issue_updated_event(original, original_snapshot, actor=request.user)
            WebhookController.create_issue_queue_assigned_event(original, original_snapshot, actor=request.user)
            return

        super().save_model(request, obj, form, change)
        from .controllers import IssueHistoryController

        IssueHistoryController.record_snapshot_changes(obj, original_snapshot, request.user)
        WebhookController.create_issue_updated_event(obj, original_snapshot, actor=request.user)
        WebhookController.create_issue_queue_assigned_event(obj, original_snapshot, actor=request.user)


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


@admin.register(IssueHistoryEvent)
class IssueHistoryEventAdmin(admin.ModelAdmin):
    list_display = ("issue", "event_type", "field_name", "changed_by_user", "changed_at")
    list_filter = ("event_type", "field_name", "changed_at")
    search_fields = ("issue__issue_number", "changed_by_user__username", "old_value", "new_value")
    readonly_fields = ("issue", "event_type", "field_name", "old_value", "new_value", "changed_by_user", "changed_at")

    def has_add_permission(self, request):
        return False


@admin.register(IssueAttachment)
class IssueAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "issue", "uploaded_by_user", "uploaded_at", "file_size")
    list_filter = ("uploaded_at",)
    search_fields = ("original_filename", "issue__issue_number", "uploaded_by_user__username")
    readonly_fields = ("uploaded_at",)


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    form = WebhookEndpointAdminForm
    list_display = (
        "name",
        "target_url",
        "enabled",
        "subscribed_event_types_summary",
        "last_delivery_status",
        "last_delivery_attempt_at",
        "created_at",
    )
    list_filter = ("enabled", WebhookEndpointEventTypeFilter, "last_delivery_status")
    search_fields = ("name", "target_url", "description")
    readonly_fields = ("last_delivery_status", "last_delivery_attempt_at", "created_at", "updated_at")

    @admin.display(description="subscribed event types")
    def subscribed_event_types_summary(self, obj):
        return obj.subscribed_event_types_display


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "issue", "occurred_at", "delivery_status")
    list_filter = ("event_type", "occurred_at", "delivery_status")
    search_fields = ("issue__issue_number",)
    readonly_fields = (
        "id",
        "event_type",
        "issue",
        "target_endpoint_ids",
        "payload",
        "occurred_at",
        "created_at",
        "delivery_status",
    )

    def has_add_permission(self, request):
        return False


@admin.register(WebhookDeliveryAttempt)
class WebhookDeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "webhook_endpoint",
        "event_type",
        "issue_reference",
        "attempt_number",
        "response_status_code",
        "success",
        "attempted_at",
        "duration_ms",
    )
    list_filter = ("success", "response_status_code", "attempted_at", "webhook_endpoint")
    search_fields = ("webhook_event__issue__issue_number", "webhook_endpoint__name")
    readonly_fields = (
        "webhook_endpoint",
        "webhook_event",
        "attempt_number",
        "request_headers",
        "request_body",
        "response_status_code",
        "response_body",
        "error_message",
        "success",
        "duration_ms",
        "attempted_at",
    )

    def event_type(self, obj):
        return obj.webhook_event.event_type

    def issue_reference(self, obj):
        return obj.webhook_event.issue.issue_number

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
