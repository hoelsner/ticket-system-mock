import re

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from djangoapp.core.controllers import IssueController
from djangoapp.core.models import (
    Collection,
    DraftIssueAttachment,
    Issue,
    IssueAttachment,
    IssueCategory,
    IssueComment,
    IssuePriority,
    WorkflowState,
)

BOARD_STATES = (
    WorkflowState.BACKLOG,
    WorkflowState.NEW,
    WorkflowState.TRIAGE,
    WorkflowState.ASSIGNED,
    WorkflowState.IN_PROGRESS,
    WorkflowState.WAITING,
    WorkflowState.RESOLVED,
    WorkflowState.CLOSED,
)

BOARD_PRIORITIES = (
    IssuePriority.CRITICAL,
    IssuePriority.HIGH,
    IssuePriority.MEDIUM,
    IssuePriority.LOW,
)

PRIORITY_RANKS = {priority: index for index, priority in enumerate(BOARD_PRIORITIES)}
BOARD_STATE_VALUES = {state.value for state in BOARD_STATES}
DRAFT_ATTACHMENT_TOKEN_RE = re.compile(r"\{\{\s*attachment\s*:\s*draft-(\d+)\s*\}\}")


def build_board_context(params, column_states=None):
    filters = _get_filter_values(params)
    issues = _get_filtered_issues(filters)
    column_states = normalize_board_column_states(column_states)

    return {
        **filters,
        "active_nav": "board",
        "assignee_options": _get_assignee_options(),
        "priority_options": _get_priority_options(),
        "collection_options": Collection.objects.filter(is_active=True).order_by("name"),
        "category_options": IssueCategory.objects.filter(is_active=True).order_by("name"),
        "board_columns": _build_board_columns(issues, column_states),
        "board_issue_count": len(issues),
    }


def build_dashboard_context(user):
    return {
        "active_nav": "dashboard",
        "assigned_issues": list(
            _get_issue_queryset().filter(user=user, archived_at__isnull=True).order_by("-updated_at")
        ),
        "mentioned_comments": list(
            IssueComment.objects
            .select_related("issue", "author_user")
            .prefetch_related("mentions__mentioned_user")
            .filter(mentions__mentioned_user=user, issue__archived_at__isnull=True)
            .distinct()
            .order_by("-created_at")
        ),
    }


def get_issue(issue_id):
    return get_object_or_404(
        _get_issue_queryset(),
        pk=issue_id,
        archived_at__isnull=True,
    )


def build_issue_detail_context(issue):
    return {
        "active_nav": "board",
        "issue_comments": list(issue.comments.all()),
        "issue_attachments": list(issue.attachments.all()),
        "issue_transitions": list(issue.state_transitions.all()),
    }


def normalize_board_column_states(raw_states):
    if not isinstance(raw_states, dict):
        return {}

    return {state.value: bool(raw_states[state.value]) for state in BOARD_STATES if state.value in raw_states}


def create_issue(cleaned_data, created_by_user):
    with transaction.atomic():
        issue = Issue(**_get_issue_payload(cleaned_data))
        issue.save()
        _sync_attachments(issue, cleaned_data, created_by_user)
        draft_token_mapping = _materialize_draft_attachments(issue, cleaned_data, created_by_user)
        if draft_token_mapping:
            issue.description_markdown = _rewrite_draft_attachment_tokens(
                issue.description_markdown,
                draft_token_mapping,
            )
            issue.save(update_fields=["description_markdown", "updated_at"])
    return issue


def update_issue(issue, cleaned_data, changed_by_user):
    original_issue = Issue.objects.only("workflow_state", "priority").get(pk=issue.pk)
    original_state = original_issue.workflow_state
    original_priority = original_issue.priority
    target_state = cleaned_data["workflow_state"]
    transition_reason = cleaned_data.get("transition_reason", "").strip()
    _apply_issue_payload(issue, cleaned_data)
    issue.workflow_state = original_state
    issue.save()

    if target_state != original_state:
        issue, _transition = IssueController.update_workflow_state(
            issue,
            target_state,
            changed_by_user,
            transition_reason,
        )

    IssueController.sync_board_position(issue, original_state, original_priority)

    _sync_attachments(issue, cleaned_data, changed_by_user)
    return issue


def update_issue_description(issue, cleaned_data):
    issue.description_markdown = cleaned_data["description_markdown"]
    issue.save(update_fields=["description_markdown", "updated_at"])
    return issue


def archive_issue(issue, archived_by_user):
    return IssueController.archive(issue, archived_by_user)


def add_issue_comment(issue, cleaned_data, author_user):
    comment = IssueComment.objects.create(
        issue=issue,
        author_user=author_user,
        body=cleaned_data["body"],
        visibility=cleaned_data["visibility"],
    )
    IssueController.touch(issue)
    _sync_attachments(issue, cleaned_data, author_user)
    return comment


def search_users(search_query, limit=10):
    user_model = get_user_model()
    queryset = user_model.objects.filter(is_active=True)
    if search_query:
        queryset = queryset.filter(
            Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )
    return list(queryset.order_by("username")[:limit])


def search_issues(search_query, limit=10):
    queryset = _get_issue_queryset().filter(archived_at__isnull=True)
    if search_query:
        queryset = queryset.filter(Q(issue_number__icontains=search_query) | Q(title__icontains=search_query))
    return list(queryset.order_by("-updated_at")[:limit])


def search_issue_attachments(issue, search_query, limit=10):
    queryset = issue.attachments.all()
    if search_query:
        queryset = queryset.filter(
            Q(original_filename__icontains=search_query) | Q(description__icontains=search_query)
        )
    return list(queryset[:limit])


def create_draft_attachments(draft_token, attachment_files, uploaded_by_user, description=""):
    cleaned_description = description.strip()
    return [
        DraftIssueAttachment.objects.create(
            draft_token=draft_token,
            file=attachment_file,
            original_filename=attachment_file.name,
            content_type=getattr(attachment_file, "content_type", "") or "",
            file_size=getattr(attachment_file, "size", 0),
            description=cleaned_description,
            uploaded_by_user=uploaded_by_user,
        )
        for attachment_file in attachment_files
        if attachment_file
    ]


def search_draft_attachments(draft_token, uploaded_by_user, search_query, limit=10):
    queryset = DraftIssueAttachment.objects.filter(
        draft_token=draft_token,
        uploaded_by_user=uploaded_by_user,
    )
    if search_query:
        queryset = queryset.filter(
            Q(original_filename__icontains=search_query) | Q(description__icontains=search_query)
        )
    return list(queryset.order_by("created_at", "pk")[:limit])


def move_issue(issue, target_state, position_index, changed_by_user):
    moved_issue, _transition = IssueController.move_on_board(
        issue,
        target_state,
        changed_by_user=changed_by_user,
        position_index=position_index,
        reason="Moved on the kanban board.",
    )
    return moved_issue


def is_board_state(value):
    return value in BOARD_STATE_VALUES


def _get_filter_values(params):
    updated_start = params.get("updated_start")
    updated_end = params.get("updated_end")

    return {
        "search_query": params.get("search", "").strip(),
        "selected_assignee": params.get("assignee", "").strip(),
        "selected_priority": params.get("priority", "").strip(),
        "selected_collection": params.get("collection", "").strip(),
        "selected_category": params.get("category", "").strip(),
        "selected_updated_start": _serialize_filter_datetime(updated_start),
        "selected_updated_end": _serialize_filter_datetime(updated_end),
        "updated_start": updated_start,
        "updated_end": updated_end,
    }


def _get_filtered_issues(filters):
    queryset = _get_issue_queryset().filter(
        archived_at__isnull=True,
        workflow_state__in=BOARD_STATES,
    )
    queryset = _apply_optional_filter(queryset, "user_id", filters["selected_assignee"])
    queryset = _apply_optional_filter(queryset, "priority", filters["selected_priority"])
    queryset = _apply_optional_filter(queryset, "collection_id", filters["selected_collection"])
    queryset = _apply_optional_filter(queryset, "category_id", filters["selected_category"])
    queryset = _apply_datetime_range(queryset, "updated_at", filters["updated_start"], filters["updated_end"])
    queryset = _apply_search(queryset, filters["search_query"])
    return _sort_issues(list(queryset))


def _apply_optional_filter(queryset, key, value):
    if value:
        return queryset.filter(**{key: value})
    return queryset


def _apply_datetime_range(queryset, key, start_value, end_value):
    if start_value is not None:
        queryset = queryset.filter(**{f"{key}__gte": start_value})
    if end_value is not None:
        queryset = queryset.filter(**{f"{key}__lte": end_value})
    return queryset


def _serialize_filter_datetime(value):
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value).strip()


def _apply_search(queryset, search_query):
    if search_query:
        return queryset.filter(Q(title__icontains=search_query) | Q(description_markdown__icontains=search_query))
    return queryset


def _get_assignee_options():
    user_model = get_user_model()
    return (
        user_model.objects
        .filter(
            assigned_issues__workflow_state__in=BOARD_STATES,
            assigned_issues__archived_at__isnull=True,
        )
        .distinct()
        .order_by("username")
    )


def _get_priority_options():
    return [{"value": priority.value, "label": priority.label} for priority in BOARD_PRIORITIES]


def _build_board_columns(issues, column_states):
    return [_build_board_column(state, issues, column_states) for state in BOARD_STATES]


def _build_board_column(state, issues, column_states):
    column_issues = _sort_issues([issue for issue in issues if issue.workflow_state == state])
    issue_count = len(column_issues)
    return {
        "value": state.value,
        "label": state.label,
        "is_open": column_states.get(state.value, issue_count > 0),
        "issue_count": issue_count,
        "issues": column_issues,
    }


def _get_issue_queryset():
    return Issue.objects.select_related("collection", "category", "group", "user").prefetch_related(
        "attachments",
        "comments__author_user",
        "comments__mentions__mentioned_user",
        "state_transitions__changed_by_user",
    )


def _sort_issues(issues):
    return sorted(
        issues,
        key=lambda issue: (
            PRIORITY_RANKS.get(issue.priority, len(PRIORITY_RANKS)),
            issue.board_position,
            issue.created_at,
            issue.pk,
        ),
    )


def _get_issue_payload(cleaned_data):
    return {
        "title": cleaned_data["title"],
        "description_markdown": cleaned_data["description_markdown"],
        "collection": cleaned_data["collection"],
        "category": cleaned_data["category"],
        "priority": cleaned_data["priority"],
        "group": cleaned_data.get("group"),
        "user": cleaned_data.get("user"),
        "is_escalated": cleaned_data.get("is_escalated", False),
        "escalated_at": _get_escalated_at(cleaned_data.get("is_escalated", False)),
    }


def _apply_issue_payload(issue, cleaned_data):
    for field, value in _get_issue_payload(cleaned_data).items():
        setattr(issue, field, value)


def _get_escalated_at(is_escalated):
    if is_escalated:
        return timezone.now()
    return None


def _sync_attachments(issue, cleaned_data, uploaded_by_user):
    attachment_files = _get_attachment_files(cleaned_data)
    if not attachment_files:
        return []

    attachment_description = cleaned_data.get("attachment_description", "").strip()
    return [
        _create_issue_attachment(issue, attachment_file, attachment_description, uploaded_by_user)
        for attachment_file in attachment_files
    ]


def _get_attachment_files(cleaned_data):
    attachment_files = cleaned_data.get("attachment_file")
    return [attachment_file for attachment_file in _normalize_attachment_files(attachment_files) if attachment_file]


def _materialize_draft_attachments(issue, cleaned_data, uploaded_by_user):
    draft_token = cleaned_data.get("attachment_draft_token", "").strip()
    if not draft_token:
        return {}

    staged_attachments = _get_staged_attachments(draft_token, uploaded_by_user)
    if not staged_attachments:
        return {}

    draft_token_mapping = {}
    for staged_attachment in staged_attachments:
        issue_attachment = _create_issue_attachment_from_draft(issue, staged_attachment, uploaded_by_user)
        draft_token_mapping[str(staged_attachment.pk)] = str(issue_attachment.pk)
        _delete_staged_attachment(staged_attachment)

    return draft_token_mapping


def _rewrite_draft_attachment_tokens(value, draft_token_mapping):
    if not value or not draft_token_mapping:
        return value

    return DRAFT_ATTACHMENT_TOKEN_RE.sub(
        lambda match: _replace_draft_attachment_token(match, draft_token_mapping),
        value,
    )


def _create_issue_attachment(issue, attachment_file, description, uploaded_by_user):
    return IssueAttachment.objects.create(
        issue=issue,
        file=attachment_file,
        original_filename=attachment_file.name,
        content_type=getattr(attachment_file, "content_type", "") or "",
        file_size=getattr(attachment_file, "size", 0),
        description=description,
        uploaded_by_user=uploaded_by_user,
    )


def _normalize_attachment_files(attachment_files):
    if not attachment_files:
        return []
    if isinstance(attachment_files, (list, tuple)):
        return attachment_files
    return [attachment_files]


def _get_staged_attachments(draft_token, uploaded_by_user):
    return list(
        DraftIssueAttachment.objects.filter(
            draft_token=draft_token,
            uploaded_by_user=uploaded_by_user,
        ).order_by("created_at", "pk")
    )


def _create_issue_attachment_from_draft(issue, staged_attachment, uploaded_by_user):
    staged_attachment.file.open("rb")
    try:
        return IssueAttachment.objects.create(
            issue=issue,
            file=ContentFile(staged_attachment.file.read(), name=staged_attachment.original_filename),
            original_filename=staged_attachment.original_filename,
            content_type=staged_attachment.content_type,
            file_size=staged_attachment.file_size,
            description=staged_attachment.description,
            uploaded_by_user=uploaded_by_user,
        )
    finally:
        staged_attachment.file.close()


def _delete_staged_attachment(staged_attachment):
    staged_attachment.file.delete(save=False)
    staged_attachment.delete()


def _replace_draft_attachment_token(match, draft_token_mapping):
    attachment_id = match.group(1)
    if attachment_id not in draft_token_mapping:
        return match.group(0)
    return f"{{{{attachment:{draft_token_mapping[attachment_id]}}}}}"
