import json
from io import BytesIO

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.http import FileResponse, QueryDict
from django.http.multipartparser import MultiPartParser, MultiPartParserError
from ninja import NinjaAPI, Query, Schema
from ninja.security import HttpBasicAuth
from pydantic import Field

from djangoapp.core.controllers import (
    CollectionController,
    IssueAttachmentController,
    IssueCategoryController,
    IssueCommentController,
)
from djangoapp.core.models import Collection, IssueAttachment, IssueCategory, IssueComment
from djangoapp.rest_api.forms import CollectionForm, IssueAttachmentForm, IssueCategoryForm, IssueCommentUpdateForm
from djangoapp.user_interface import controllers
from djangoapp.user_interface.forms import IssueArchiveForm, IssueCommentForm, IssueCreateForm, IssueUpdateForm


class DjangoBasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            return user
        return None


class AuthenticatedUserSchema(Schema):
    id: int = Field(description="Unique identifier of the authenticated user.")
    username: str = Field(description="Login name used to authenticate the user.")
    display_name: str = Field(description="Preferred display name shown for the authenticated user.")
    is_staff: bool = Field(description="Whether the user can access staff-only administration features.")
    is_superuser: bool = Field(description="Whether the user has unrestricted Django superuser privileges.")


class ChoiceSchema(Schema):
    value: str = Field(description="Stored value for the selectable option.")
    label: str = Field(description="Human-readable label for the selectable option.")


class GroupSchema(Schema):
    id: int = Field(description="Unique identifier of the group.")
    name: str = Field(description="Display name of the group that can own issues.")


class CollectionSchema(Schema):
    id: int = Field(description="Unique identifier of the collection.")
    name: str = Field(description="Display name of the collection.")
    prefix: str = Field(description="Identifier prefix used when generating issue numbers in this collection.")
    description: str = Field(description="Operational purpose of the collection.")


class IssueCategorySchema(Schema):
    id: int = Field(description="Unique identifier of the issue category.")
    name: str = Field(description="Display name of the issue category.")
    code: str = Field(description="Stable short code used to identify the issue category.")
    description: str = Field(description="Operational meaning of the issue category.")


class UserSummarySchema(Schema):
    id: int = Field(description="Unique identifier of the user.")
    username: str = Field(description="Login name of the user.")
    display_name: str = Field(description="Preferred display name shown in issue and comment payloads.")


class IssueAttachmentSchema(Schema):
    id: int = Field(description="Unique identifier of the issue attachment.")
    original_filename: str = Field(
        description="Original client-side filename supplied when the attachment was uploaded."
    )
    description: str = Field(description="Optional description entered for the attachment.")
    content_type: str = Field(description="Detected MIME type of the stored attachment.")
    file_size: int = Field(description="Attachment size in bytes.")
    uploaded_at: str = Field(description="Timestamp when the attachment was uploaded, encoded as ISO 8601.")
    file_url: str = Field(description="API URL used to download the attachment content.")
    uploaded_by_user: UserSummarySchema = Field(description="User who uploaded the attachment.")


class IssueCommentSchema(Schema):
    id: int = Field(description="Unique identifier of the issue comment.")
    body: str = Field(description="Markdown or text body of the comment.")
    visibility: str = Field(description="Stored visibility code that determines who may see the comment.")
    visibility_label: str = Field(description="Human-readable label for the current comment visibility.")
    created_at: str = Field(description="Timestamp when the comment was created, encoded as ISO 8601.")
    author_user: UserSummarySchema = Field(description="User who authored the comment.")


class IssueTransitionSchema(Schema):
    id: int = Field(description="Unique identifier of the recorded issue state transition.")
    from_state: str = Field(description="Stored workflow state code before the transition.")
    from_state_label: str = Field(description="Human-readable label for the previous workflow state.")
    to_state: str = Field(description="Stored workflow state code after the transition.")
    to_state_label: str = Field(description="Human-readable label for the new workflow state.")
    changed_at: str = Field(description="Timestamp when the workflow state changed, encoded as ISO 8601.")
    reason: str = Field(description="Optional reason recorded for the workflow state change.")
    changed_by_user: UserSummarySchema = Field(description="User who performed the workflow state change.")


class IssueSummarySchema(Schema):
    id: int = Field(description="Unique identifier of the issue.")
    issue_number: str = Field(
        description="Human-facing issue number composed from the collection prefix and local sequence."
    )
    title: str = Field(description="Short summary of the issue.")
    description_markdown: str = Field(description="Detailed markdown description of the issue.")
    priority: str = Field(description="Stored priority code for the issue.")
    priority_label: str = Field(description="Human-readable label for the issue priority.")
    workflow_state: str = Field(
        description="Stored workflow state code that currently governs the issue lifecycle position."
    )
    workflow_state_label: str = Field(description="Human-readable label for the current workflow state.")
    board_position: int = Field(
        description="Zero-based position of the issue inside its current workflow state column."
    )
    is_escalated: bool = Field(description="Whether the issue is marked for elevated handling.")
    created_at: str = Field(description="Timestamp when the issue was created, encoded as ISO 8601.")
    updated_at: str = Field(description="Timestamp when the issue was last updated, encoded as ISO 8601.")
    resolved_at: str | None = Field(description="Timestamp when the issue reached a resolved state, if available.")
    closed_at: str | None = Field(description="Timestamp when the issue was closed, if available.")
    archived_at: str | None = Field(description="Timestamp when the issue was archived, if available.")
    collection: CollectionSchema = Field(description="Collection that owns the issue number sequence.")
    category: IssueCategorySchema = Field(description="Issue category assigned to the issue.")
    group: GroupSchema | None = Field(description="Group currently associated with the issue for dispatching, if any.")
    user: UserSummarySchema | None = Field(description="User currently assigned to the issue, if any.")


class IssueDetailSchema(IssueSummarySchema):
    attachments: list[IssueAttachmentSchema] = Field(description="Attachments currently associated with the issue.")
    comments: list[IssueCommentSchema] = Field(description="Comments recorded on the issue.")
    transitions: list[IssueTransitionSchema] = Field(description="Workflow state transition history for the issue.")


class BoardColumnSchema(Schema):
    value: str = Field(description="Stored workflow state code represented by this board column.")
    label: str = Field(description="Human-readable label for the workflow state column.")
    is_open: bool = Field(description="Whether the workflow state is considered open work.")
    issue_count: int = Field(description="Number of issues currently present in the column.")
    issues: list[IssueSummarySchema] = Field(description="Issues currently present in the workflow state column.")


class BoardResponseSchema(Schema):
    search_query: str = Field(description="Current free-text search filter applied to the board projection.")
    selected_assignee: str = Field(description="Current assignee filter value.")
    selected_priority: str = Field(description="Current priority filter value.")
    selected_collection: str = Field(description="Current collection filter value.")
    selected_category: str = Field(description="Current issue category filter value.")
    assignee_options: list[UserSummarySchema] = Field(description="Available assignee filter options.")
    priority_options: list[ChoiceSchema] = Field(description="Available priority filter options.")
    collection_options: list[CollectionSchema] = Field(description="Available collection filter options.")
    category_options: list[IssueCategorySchema] = Field(description="Available issue category filter options.")
    board_columns: list[BoardColumnSchema] = Field(description="Board columns grouped by workflow state.")
    board_issue_count: int = Field(description="Total number of issues included across all returned board columns.")


class MentionedCommentSchema(Schema):
    id: int = Field(description="Unique identifier of the mentioned comment.")
    issue: IssueSummarySchema = Field(description="Issue that contains the comment mention.")
    body: str = Field(description="Comment body that mentioned the current user.")
    visibility: str = Field(description="Stored visibility code of the mentioned comment.")
    visibility_label: str = Field(description="Human-readable label for the comment visibility.")
    created_at: str = Field(description="Timestamp when the mentioned comment was created, encoded as ISO 8601.")
    author_user: UserSummarySchema = Field(description="User who authored the mentioned comment.")


class DashboardResponseSchema(Schema):
    assigned_issues: list[IssueSummarySchema] = Field(
        description="Issues currently assigned to the authenticated user."
    )
    mentioned_comments: list[MentionedCommentSchema] = Field(
        description="Comments that mention the authenticated user."
    )


class MutationStatusSchema(Schema):
    status: str = Field(description="Mutation result code for the issue operation.")
    issue: IssueDetailSchema = Field(description="Refreshed issue payload after the mutation completed.")


class ArchiveStatusSchema(Schema):
    status: str = Field(description="Mutation result code for the archive operation.")
    issue_id: int = Field(description="Identifier of the archived issue.")
    archived_at: str = Field(description="Timestamp when the issue was archived, encoded as ISO 8601.")


class MoveStatusSchema(Schema):
    status: str = Field(description="Mutation result code for the move operation.")
    issue_id: int = Field(description="Identifier of the moved issue.")
    workflow_state: str = Field(description="Workflow state code after the move completed.")
    board_position: int = Field(description="Zero-based board position after the move completed.")


class CollectionMutationSchema(Schema):
    status: str = Field(description="Mutation result code for the collection operation.")
    collection: CollectionSchema = Field(description="Collection payload after the mutation completed.")


class IssueCategoryMutationSchema(Schema):
    status: str = Field(description="Mutation result code for the issue category operation.")
    category: IssueCategorySchema = Field(description="Issue category payload after the mutation completed.")


class IssueCommentMutationSchema(Schema):
    status: str = Field(description="Mutation result code for the issue comment operation.")
    comment: IssueCommentSchema = Field(description="Issue comment payload after the mutation completed.")


class IssueAttachmentMutationSchema(Schema):
    status: str = Field(description="Mutation result code for the attachment operation.")
    attachment: IssueAttachmentSchema = Field(description="Attachment payload after the mutation completed.")


def _request_body(description, content_type, properties, required_fields=None):
    schema = {
        "type": "object",
        "properties": properties,
    }
    if required_fields:
        schema["required"] = required_fields

    return {
        "requestBody": {
            "required": True,
            "description": description,
            "content": {
                content_type: {
                    "schema": schema,
                }
            },
        }
    }


COLLECTION_REQUEST_BODY = _request_body(
    "Collection data used to create or update a collection.",
    "application/json",
    {
        "name": {"type": "string", "description": "Display name of the collection."},
        "prefix": {
            "type": "string",
            "description": "Unique prefix used when generating issue numbers for this collection.",
        },
        "description": {"type": "string", "description": "Operational purpose of the collection."},
        "is_active": {"type": "boolean", "description": "Whether the collection may be used for new issues."},
        "next_issue_sequence": {
            "type": "integer",
            "description": "Next local sequence value that will be assigned inside the collection.",
        },
    },
    required_fields=["name", "prefix"],
)


CATEGORY_REQUEST_BODY = _request_body(
    "Issue category data used to create or update a category.",
    "application/json",
    {
        "name": {"type": "string", "description": "Display name of the issue category."},
        "code": {"type": "string", "description": "Stable short code used to identify the issue category."},
        "description": {"type": "string", "description": "Operational meaning of the issue category."},
        "is_active": {"type": "boolean", "description": "Whether the issue category may be used for new issues."},
    },
    required_fields=["name", "code"],
)


ISSUE_CREATE_REQUEST_BODY = _request_body(
    "Multipart payload used to create a new issue, optionally with attachments.",
    "multipart/form-data",
    {
        "title": {"type": "string", "description": "Short summary of the issue."},
        "description_markdown": {"type": "string", "description": "Detailed markdown description of the issue."},
        "collection": {
            "type": "integer",
            "description": "Identifier of the collection that will own the issue number.",
        },
        "category": {"type": "integer", "description": "Identifier of the issue category assigned to the issue."},
        "priority": {
            "type": "string",
            "description": "Priority code to assign to the issue.",
            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        },
        "group": {"type": "integer", "description": "Identifier of the group assigned to the issue, when present."},
        "user": {"type": "integer", "description": "Identifier of the user assigned to the issue, when present."},
        "is_escalated": {"type": "boolean", "description": "Whether the issue should be marked for elevated handling."},
        "attachment_file": {
            "type": "array",
            "description": "One or more files to attach during issue creation.",
            "items": {"type": "string", "format": "binary"},
        },
        "attachment_description": {
            "type": "string",
            "description": "Shared description to apply when attachment files are uploaded in the same request.",
        },
        "attachment_draft_token": {
            "type": "string",
            "description": "Optional draft token that links previously staged attachment uploads.",
        },
    },
    required_fields=["title", "collection", "category", "priority"],
)


ISSUE_UPDATE_REQUEST_BODY = _request_body(
    "Multipart payload used to update an existing issue, optionally including one attachment update.",
    "multipart/form-data",
    {
        "title": {"type": "string", "description": "Short summary of the issue."},
        "description_markdown": {"type": "string", "description": "Detailed markdown description of the issue."},
        "collection": {"type": "integer", "description": "Identifier of the collection assigned to the issue."},
        "category": {"type": "integer", "description": "Identifier of the issue category assigned to the issue."},
        "priority": {
            "type": "string",
            "description": "Priority code assigned to the issue.",
            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        },
        "group": {"type": "integer", "description": "Identifier of the group assigned to the issue, when present."},
        "user": {"type": "integer", "description": "Identifier of the user assigned to the issue, when present."},
        "is_escalated": {"type": "boolean", "description": "Whether the issue is marked for elevated handling."},
        "workflow_state": {
            "type": "string",
            "description": "Workflow state code to apply to the issue.",
            "enum": [
                "BACKLOG",
                "NEW",
                "TRIAGE",
                "ASSIGNED",
                "IN_PROGRESS",
                "WAITING",
                "RESOLVED",
                "CLOSED",
                "REJECTED",
                "DUPLICATE",
            ],
        },
        "transition_reason": {
            "type": "string",
            "description": "Optional reason recorded when the workflow state changes.",
        },
        "attachment_file": {
            "type": "string",
            "format": "binary",
            "description": "Optional file to attach as part of the update request.",
        },
        "attachment_description": {
            "type": "string",
            "description": "Description for the attachment supplied in the same request.",
        },
    },
    required_fields=["title", "collection", "category", "priority", "workflow_state"],
)


ARCHIVE_REQUEST_BODY = _request_body(
    "Confirmation payload required before an issue is archived.",
    "application/json",
    {
        "confirm_archive": {
            "type": "boolean",
            "description": "Must be true to confirm that the issue should be archived.",
        }
    },
    required_fields=["confirm_archive"],
)


ISSUE_COMMENT_REQUEST_BODY = _request_body(
    "Multipart payload used to add a comment to an issue, optionally with one attachment.",
    "multipart/form-data",
    {
        "body": {"type": "string", "description": "Markdown or text body of the comment."},
        "visibility": {
            "type": "string",
            "description": "Visibility code that determines which audiences may see the comment.",
        },
        "attachment_file": {
            "type": "string",
            "format": "binary",
            "description": "Optional file to attach to the comment.",
        },
        "attachment_description": {
            "type": "string",
            "description": "Description for the optional comment attachment.",
        },
    },
    required_fields=["body", "visibility"],
)


ISSUE_COMMENT_UPDATE_REQUEST_BODY = _request_body(
    "Payload used to update the body or visibility of an existing issue comment.",
    "application/json",
    {
        "body": {"type": "string", "description": "Updated markdown or text body of the comment."},
        "visibility": {
            "type": "string",
            "description": "Updated visibility code for the comment.",
        },
    },
    required_fields=["body", "visibility"],
)


ATTACHMENT_CREATE_REQUEST_BODY = _request_body(
    "Multipart payload used to add a new issue attachment.",
    "multipart/form-data",
    {
        "file": {
            "type": "string",
            "format": "binary",
            "description": "Attachment file content.",
        },
        "description": {"type": "string", "description": "Description of the attachment."},
    },
    required_fields=["file"],
)


ATTACHMENT_UPDATE_REQUEST_BODY = _request_body(
    "Multipart payload used to update an existing issue attachment.",
    "multipart/form-data",
    {
        "file": {
            "type": "string",
            "format": "binary",
            "description": "Optional replacement file content for the attachment.",
        },
        "description": {"type": "string", "description": "Updated description of the attachment."},
    },
)


MOVE_REQUEST_BODY = _request_body(
    "Payload used to move an issue to a different workflow state and position.",
    "application/json",
    {
        "target_state": {
            "type": "string",
            "description": "Destination workflow state code for the move operation.",
            "enum": [
                "BACKLOG",
                "NEW",
                "TRIAGE",
                "ASSIGNED",
                "IN_PROGRESS",
                "WAITING",
                "RESOLVED",
                "CLOSED",
                "REJECTED",
                "DUPLICATE",
            ],
        },
        "position_index": {
            "type": "integer",
            "description": "Zero-based target position inside the destination workflow state column.",
        },
    },
    required_fields=["target_state", "position_index"],
)


INVALID_PAYLOAD_ERROR = (400, {"error": "Invalid request payload."})


api = NinjaAPI(
    title="IT Operation Ticketing Demo Service API",
    version="1.0.0",
    description=(
        "Machine-facing REST API for reading issue data, reference data, dashboard projections, "
        "and issue workflow mutations in the IT Operation Ticketing Demo Service."
    ),
    auth=DjangoBasicAuth(),
)


@api.get(
    "/health",
    summary="Check API health",
    description="Confirm that the authenticated REST API surface is reachable.",
    tags=["System"],
)
def health(request):
    return {"status": "ok"}


@api.get(
    "/auth/me",
    response=AuthenticatedUserSchema,
    summary="Get authenticated user",
    description="Return the currently authenticated user together with staff and superuser flags.",
    tags=["Authentication"],
)
def current_user(request):
    return {
        "id": request.auth.pk,
        "username": request.auth.get_username(),
        "display_name": request.auth.get_full_name() or request.auth.get_username(),
        "is_staff": request.auth.is_staff,
        "is_superuser": request.auth.is_superuser,
    }


def _serialize_user(user):
    return {
        "id": user.pk,
        "username": user.get_username(),
        "display_name": user.get_full_name() or user.get_username(),
    }


def _serialize_group(group):
    return {
        "id": group.pk,
        "name": group.name,
    }


def _serialize_collection(collection):
    return {
        "id": collection.pk,
        "name": collection.name,
        "prefix": collection.prefix,
        "description": collection.description,
    }


def _serialize_category(category):
    return {
        "id": category.pk,
        "name": category.name,
        "code": category.code,
        "description": category.description,
    }


def _get_issue_comment(issue_id, comment_id):
    return IssueComment.objects.select_related("author_user").get(issue_id=issue_id, pk=comment_id)


def _get_issue_attachment(issue_id, attachment_id):
    return IssueAttachment.objects.select_related("uploaded_by_user").get(issue_id=issue_id, pk=attachment_id)


def _attachment_download_url(attachment):
    return f"/api/issues/{attachment.issue_id}/attachments/{attachment.pk}/download"


def _serialize_attachment(attachment):
    return {
        "id": attachment.pk,
        "original_filename": attachment.original_filename,
        "description": attachment.description,
        "content_type": attachment.content_type,
        "file_size": attachment.file_size,
        "uploaded_at": attachment.uploaded_at.isoformat(),
        "file_url": _attachment_download_url(attachment),
        "uploaded_by_user": _serialize_user(attachment.uploaded_by_user),
    }


def _serialize_comment(comment):
    return {
        "id": comment.pk,
        "body": comment.body,
        "visibility": comment.visibility,
        "visibility_label": str(comment.get_visibility_display()),
        "created_at": comment.created_at.isoformat(),
        "author_user": _serialize_user(comment.author_user),
    }


def _serialize_transition(transition):
    return {
        "id": transition.pk,
        "from_state": transition.from_state,
        "from_state_label": str(transition.get_from_state_display()),
        "to_state": transition.to_state,
        "to_state_label": str(transition.get_to_state_display()),
        "changed_at": transition.changed_at.isoformat(),
        "reason": transition.reason,
        "changed_by_user": _serialize_user(transition.changed_by_user),
    }


def _serialize_issue(issue):
    timestamps = _serialize_issue_timestamps(issue)
    return {
        "id": issue.pk,
        "issue_number": issue.issue_number,
        "title": issue.title,
        "description_markdown": issue.description_markdown,
        "priority": issue.priority,
        "priority_label": str(issue.get_priority_display()),
        "workflow_state": issue.workflow_state,
        "workflow_state_label": str(issue.get_workflow_state_display()),
        "board_position": issue.board_position,
        "is_escalated": issue.is_escalated,
        **timestamps,
        "collection": _serialize_collection(issue.collection),
        "category": _serialize_category(issue.category),
        "group": _serialize_optional_relation(issue.group, _serialize_group),
        "user": _serialize_optional_relation(issue.user, _serialize_user),
    }


def _serialize_issue_detail(issue):
    detail_context = controllers.build_issue_detail_context(issue)
    return {
        **_serialize_issue(issue),
        "attachments": [_serialize_attachment(attachment) for attachment in detail_context["issue_attachments"]],
        "comments": [_serialize_comment(comment) for comment in detail_context["issue_comments"]],
        "transitions": [_serialize_transition(transition) for transition in detail_context["issue_transitions"]],
    }


def _serialize_issue_timestamps(issue):
    return {
        "created_at": issue.created_at.isoformat(),
        "updated_at": issue.updated_at.isoformat(),
        "resolved_at": _serialize_optional_datetime(issue.resolved_at),
        "closed_at": _serialize_optional_datetime(issue.closed_at),
        "archived_at": _serialize_optional_datetime(issue.archived_at),
    }


def _serialize_optional_datetime(value):
    if value is None:
        return None
    return value.isoformat()


def _serialize_optional_relation(value, serializer):
    if value is None:
        return None
    return serializer(value)


def _serialize_board_context(context):
    return {
        "search_query": context["search_query"],
        "selected_assignee": context["selected_assignee"],
        "selected_priority": context["selected_priority"],
        "selected_collection": context["selected_collection"],
        "selected_category": context["selected_category"],
        "assignee_options": [_serialize_user(user) for user in context["assignee_options"]],
        "priority_options": [_serialize_choice(choice) for choice in context["priority_options"]],
        "collection_options": [_serialize_collection(collection) for collection in context["collection_options"]],
        "category_options": [_serialize_category(category) for category in context["category_options"]],
        "board_columns": [_serialize_board_column(column) for column in context["board_columns"]],
        "board_issue_count": context["board_issue_count"],
    }


def _serialize_choice(choice):
    return {"value": choice["value"], "label": str(choice["label"])}


def _serialize_board_column(column):
    return {
        "value": column["value"],
        "label": str(column["label"]),
        "is_open": column["is_open"],
        "issue_count": column["issue_count"],
        "issues": [_serialize_issue(issue) for issue in column["issues"]],
    }


def _serialize_dashboard_context(context):
    return {
        "assigned_issues": [_serialize_issue(issue) for issue in context["assigned_issues"]],
        "mentioned_comments": [
            {
                "id": comment.pk,
                "issue": _serialize_issue(comment.issue),
                "body": comment.body,
                "visibility": comment.visibility,
                "visibility_label": str(comment.get_visibility_display()),
                "created_at": comment.created_at.isoformat(),
                "author_user": _serialize_user(comment.author_user),
            }
            for comment in context["mentioned_comments"]
        ],
    }


def _request_payload(request):
    if _is_json_request(request.content_type):
        return _parse_json_payload(request.body)

    payload, _files, error = _request_form_payload(request)
    return payload, error


def _request_form_payload(request):
    if request.method == "POST":
        return request.POST.dict(), request.FILES or None, None

    content_type = request.content_type or ""
    parser = _request_form_parser(content_type)
    if parser is not None:
        return parser(request, content_type)

    return request.POST.dict(), request.FILES or None, None


def _form_error_response(form):
    return 400, {"errors": form.errors.get_json_data()}


def _issue_mutation_payload(request):
    if _is_json_request(request.content_type):
        payload, error = _request_payload(request)
        if error is not None:
            return None, None, error
        return payload, request.FILES or None, None

    return _request_form_payload(request)


def _move_payload(request):
    payload, error = _request_payload(request)
    if error is not None:
        return None, error

    target_state = str(payload.get("target_state", "")).strip().upper()
    if not controllers.is_board_state(target_state):
        return None, (400, {"error": "Invalid workflow state."})

    try:
        position_index = int(payload.get("position_index", 0))
    except TypeError, ValueError:
        return None, (400, {"error": "Invalid target position."})

    return {
        "target_state": target_state,
        "position_index": max(0, position_index),
    }, None


def _is_json_request(content_type):
    return bool(content_type and content_type.startswith("application/json"))


def _parse_json_payload(body):
    try:
        payload = json.loads(body or "{}")
    except json.JSONDecodeError:
        return None, INVALID_PAYLOAD_ERROR

    if not isinstance(payload, dict):
        return None, INVALID_PAYLOAD_ERROR

    return payload, None


def _request_form_parser(content_type):
    if content_type.startswith("multipart/form-data"):
        return _parse_multipart_form_payload
    if content_type.startswith("application/x-www-form-urlencoded"):
        return _parse_urlencoded_form_payload
    return None


def _parse_multipart_form_payload(request, content_type):
    try:
        payload, files = MultiPartParser(
            _multipart_request_meta(request, content_type),
            BytesIO(request.body),
            request.upload_handlers,
            request.encoding or "utf-8",
        ).parse()
    except MultiPartParserError:
        return None, None, INVALID_PAYLOAD_ERROR

    return payload.dict(), files or None, None


def _multipart_request_meta(request, content_type):
    meta = request.META.copy()
    meta["CONTENT_TYPE"] = request.META.get("CONTENT_TYPE", content_type)
    meta["CONTENT_LENGTH"] = str(len(request.body or b""))
    return meta


def _parse_urlencoded_form_payload(request, _content_type):
    return QueryDict(request.body, encoding=request.encoding or "utf-8").dict(), None, None


@api.get(
    "/groups",
    response=list[GroupSchema],
    summary="List groups",
    description="Return all groups that can be used to dispatch or assign issues.",
    tags=["Reference Data"],
)
def groups(request):
    return [_serialize_group(group) for group in Group.objects.order_by("name")]


@api.get(
    "/users",
    response=list[UserSummarySchema],
    summary="List users",
    description="Return users that may be assigned to issues, optionally filtered to one group.",
    tags=["Reference Data"],
)
def users(
    request,
    group_id: int | None = Query(None, description="Optional group identifier used to limit the returned users."),
):
    user_model = get_user_model()
    queryset = user_model.objects.order_by("username")
    if group_id is not None:
        queryset = queryset.filter(groups__id=group_id).distinct()
    return [_serialize_user(user) for user in queryset]


@api.get(
    "/collections",
    response=list[CollectionSchema],
    summary="List active collections",
    description="Return active collections that may own new issue numbers.",
    tags=["Reference Data"],
)
def collections(request):
    return [
        _serialize_collection(collection) for collection in Collection.objects.filter(is_active=True).order_by("name")
    ]


@api.post(
    "/collections",
    response={201: CollectionMutationSchema, 400: dict},
    summary="Create collection",
    description="Create a new collection that can own issue number sequences.",
    tags=["Reference Data"],
    openapi_extra=COLLECTION_REQUEST_BODY,
)
def create_collection(request):
    payload, error = _request_payload(request)
    if error is not None:
        return error

    form = CollectionForm(payload)
    if not form.is_valid():
        return _form_error_response(form)

    collection = CollectionController.create(form.cleaned_data)
    return 201, {"status": "created", "collection": _serialize_collection(collection)}


@api.put(
    "/collections/{collection_id}",
    response={200: CollectionMutationSchema, 400: dict},
    summary="Update collection",
    description="Update the metadata and activation state of an existing collection.",
    tags=["Reference Data"],
    openapi_extra=COLLECTION_REQUEST_BODY,
)
def update_collection(request, collection_id: int):
    collection = Collection.objects.get(pk=collection_id)
    payload, error = _request_payload(request)
    if error is not None:
        return error

    form = CollectionForm(payload, instance=collection)
    if not form.is_valid():
        return _form_error_response(form)

    updated_collection = CollectionController.update(collection, form.cleaned_data)
    return {"status": "updated", "collection": _serialize_collection(updated_collection)}


@api.get(
    "/categories",
    response=list[IssueCategorySchema],
    summary="List active issue categories",
    description="Return active issue categories that may be assigned to issues.",
    tags=["Reference Data"],
)
def categories(request):
    return [_serialize_category(category) for category in IssueCategory.objects.filter(is_active=True).order_by("name")]


@api.post(
    "/categories",
    response={201: IssueCategoryMutationSchema, 400: dict},
    summary="Create issue category",
    description="Create a new issue category used to classify issues.",
    tags=["Reference Data"],
    openapi_extra=CATEGORY_REQUEST_BODY,
)
def create_category(request):
    payload, error = _request_payload(request)
    if error is not None:
        return error

    form = IssueCategoryForm(payload)
    if not form.is_valid():
        return _form_error_response(form)

    issue_category = IssueCategoryController.create(form.cleaned_data)
    return 201, {"status": "created", "category": _serialize_category(issue_category)}


@api.put(
    "/categories/{category_id}",
    response={200: IssueCategoryMutationSchema, 400: dict},
    summary="Update issue category",
    description="Update the metadata and activation state of an existing issue category.",
    tags=["Reference Data"],
    openapi_extra=CATEGORY_REQUEST_BODY,
)
def update_category(request, category_id: int):
    issue_category = IssueCategory.objects.get(pk=category_id)
    payload, error = _request_payload(request)
    if error is not None:
        return error

    form = IssueCategoryForm(payload, instance=issue_category)
    if not form.is_valid():
        return _form_error_response(form)

    updated_category = IssueCategoryController.update(issue_category, form.cleaned_data)
    return {"status": "updated", "category": _serialize_category(updated_category)}


@api.get(
    "/board",
    response=BoardResponseSchema,
    summary="Get board projection",
    description="Return the workflow board projection together with the available filter options.",
    tags=["Boards"],
)
def board(
    request,
    search: str = Query("", description="Free-text filter applied to issue number, title, and description content."),
    assignee: str = Query("", description="Optional user identifier used to limit the board to one assignee."),
    priority: str = Query("", description="Optional priority code used to limit the board projection."),
    collection: str = Query("", description="Optional collection identifier used to limit the board projection."),
    category: str = Query("", description="Optional issue category identifier used to limit the board projection."),
):
    context = controllers.build_board_context({
        "search": search,
        "assignee": assignee,
        "priority": priority,
        "collection": collection,
        "category": category,
    })
    return _serialize_board_context(context)


@api.get(
    "/dashboard",
    response=DashboardResponseSchema,
    summary="Get personal dashboard",
    description="Return the authenticated user's assigned issues and comment mentions.",
    tags=["Dashboard"],
)
def dashboard(request):
    return _serialize_dashboard_context(controllers.build_dashboard_context(request.auth))


@api.get(
    "/issues",
    response=list[IssueSummarySchema],
    summary="List issues",
    description="Return issues that match the supplied board-style filters as a flat collection.",
    tags=["Issues"],
)
def issue_list(
    request,
    search: str = Query("", description="Free-text filter applied to issue number, title, and description content."),
    assignee: str = Query(
        "", description="Optional user identifier used to limit the returned issues to one assignee."
    ),
    priority: str = Query("", description="Optional priority code used to limit the returned issues."),
    collection: str = Query("", description="Optional collection identifier used to limit the returned issues."),
    category: str = Query("", description="Optional issue category identifier used to limit the returned issues."),
):
    board_context = controllers.build_board_context({
        "search": search,
        "assignee": assignee,
        "priority": priority,
        "collection": collection,
        "category": category,
    })
    issues = []
    for column in board_context["board_columns"]:
        issues.extend(column["issues"])
    return [_serialize_issue(issue) for issue in issues]


@api.get(
    "/issues/{issue_id}",
    response=IssueDetailSchema,
    summary="Get issue detail",
    description="Return a complete issue including attachments, comments, and workflow transition history.",
    tags=["Issues"],
)
def issue_detail(request, issue_id: int):
    return _serialize_issue_detail(controllers.get_issue(issue_id))


@api.post(
    "/issues",
    response={201: MutationStatusSchema, 400: dict},
    summary="Create issue",
    description="Create a new issue and optionally include initial attachments in the same request.",
    tags=["Issues"],
    openapi_extra=ISSUE_CREATE_REQUEST_BODY,
)
def create_issue(request):
    payload, files, error = _issue_mutation_payload(request)
    if error is not None:
        return error

    form = IssueCreateForm(payload, files)
    if not form.is_valid():
        return _form_error_response(form)

    issue = controllers.create_issue(form.cleaned_data, request.auth)
    return 201, {"status": "created", "issue": _serialize_issue_detail(issue)}


@api.put(
    "/issues/{issue_id}",
    response={200: MutationStatusSchema, 400: dict},
    summary="Update issue",
    description="Update issue fields, workflow state, and optional attachment content for an existing issue.",
    tags=["Issues"],
    openapi_extra=ISSUE_UPDATE_REQUEST_BODY,
)
def update_issue(request, issue_id: int):
    issue = controllers.get_issue(issue_id)
    payload, files, error = _issue_mutation_payload(request)
    if error is not None:
        return error

    form = IssueUpdateForm(payload, files, instance=issue)
    if not form.is_valid():
        return _form_error_response(form)

    updated_issue = controllers.update_issue(issue, form.cleaned_data, request.auth)
    refreshed_issue = controllers.get_issue(updated_issue.pk)
    return {"status": "updated", "issue": _serialize_issue_detail(refreshed_issue)}


@api.post(
    "/issues/{issue_id}/archive",
    response={200: ArchiveStatusSchema, 400: dict},
    summary="Archive issue",
    description="Archive an issue so it leaves active views while preserving its history.",
    tags=["Issues"],
    openapi_extra=ARCHIVE_REQUEST_BODY,
)
def archive_issue(request, issue_id: int):
    issue = controllers.get_issue(issue_id)
    payload, error = _request_payload(request)
    if error is not None:
        return error

    form = IssueArchiveForm(payload)
    if not form.is_valid():
        return _form_error_response(form)

    archived_issue = controllers.archive_issue(issue, request.auth)
    return {
        "status": "archived",
        "issue_id": archived_issue.pk,
        "archived_at": archived_issue.archived_at.isoformat(),
    }


@api.post(
    "/issues/{issue_id}/comments",
    response={201: MutationStatusSchema, 400: dict},
    summary="Add issue comment",
    description="Add a new comment to an issue and optionally include one attachment in the same request.",
    tags=["Issues"],
    openapi_extra=ISSUE_COMMENT_REQUEST_BODY,
)
def add_issue_comment(request, issue_id: int):
    issue = controllers.get_issue(issue_id)
    payload, files, error = _issue_mutation_payload(request)
    if error is not None:
        return error

    form = IssueCommentForm(payload, files)
    if not form.is_valid():
        return _form_error_response(form)

    controllers.add_issue_comment(issue, form.cleaned_data, request.auth)
    refreshed_issue = controllers.get_issue(issue_id)
    return 201, {"status": "comment-added", "issue": _serialize_issue_detail(refreshed_issue)}


@api.put(
    "/issues/{issue_id}/comments/{comment_id}",
    response={200: IssueCommentMutationSchema, 400: dict},
    summary="Update issue comment",
    description="Update the body or visibility of an existing issue comment.",
    tags=["Issues"],
    openapi_extra=ISSUE_COMMENT_UPDATE_REQUEST_BODY,
)
def update_issue_comment(request, issue_id: int, comment_id: int):
    issue_comment = _get_issue_comment(issue_id, comment_id)
    payload, error = _request_payload(request)
    if error is not None:
        return error

    form = IssueCommentUpdateForm(payload, instance=issue_comment)
    if not form.is_valid():
        return _form_error_response(form)

    updated_comment = IssueCommentController.update(issue_comment, form.cleaned_data)
    return {"status": "updated", "comment": _serialize_comment(updated_comment)}


@api.post(
    "/issues/{issue_id}/attachments",
    response={201: IssueAttachmentMutationSchema, 400: dict},
    summary="Add issue attachment",
    description="Upload a new attachment for an issue.",
    tags=["Issues"],
    openapi_extra=ATTACHMENT_CREATE_REQUEST_BODY,
)
def add_issue_attachment(request, issue_id: int):
    issue = controllers.get_issue(issue_id)
    payload, files, error = _issue_mutation_payload(request)
    if error is not None:
        return error

    form = IssueAttachmentForm(payload, files)
    if not form.is_valid():
        return _form_error_response(form)

    attachment = IssueAttachmentController.create(issue, form.cleaned_data, request.auth)
    return 201, {"status": "created", "attachment": _serialize_attachment(attachment)}


@api.put(
    "/issues/{issue_id}/attachments/{attachment_id}",
    response={200: IssueAttachmentMutationSchema, 400: dict},
    summary="Update issue attachment",
    description="Update attachment metadata and optionally replace the stored file content.",
    tags=["Issues"],
    openapi_extra=ATTACHMENT_UPDATE_REQUEST_BODY,
)
def update_issue_attachment(request, issue_id: int, attachment_id: int):
    issue_attachment = _get_issue_attachment(issue_id, attachment_id)
    payload, files, error = _issue_mutation_payload(request)
    if error is not None:
        return error

    form = IssueAttachmentForm(payload, files, instance=issue_attachment)
    if not form.is_valid():
        return _form_error_response(form)

    updated_attachment = IssueAttachmentController.update(issue_attachment, form.cleaned_data)
    return {"status": "updated", "attachment": _serialize_attachment(updated_attachment)}


@api.get(
    "/issues/{issue_id}/attachments/{attachment_id}/download",
    summary="Download issue attachment",
    description="Download the binary content of a stored issue attachment.",
    tags=["Issues"],
)
def download_issue_attachment(request, issue_id: int, attachment_id: int):
    attachment = _get_issue_attachment(issue_id, attachment_id)
    return FileResponse(
        attachment.file.open("rb"),
        as_attachment=True,
        filename=attachment.original_filename,
        content_type=attachment.content_type or "application/octet-stream",
    )


@api.post(
    "/issues/{issue_id}/move",
    response={200: MoveStatusSchema, 400: dict},
    summary="Move issue on board",
    description="Move an issue to a different workflow state column and board position.",
    tags=["Issues"],
    openapi_extra=MOVE_REQUEST_BODY,
)
def move_issue(request, issue_id: int):
    issue = controllers.get_issue(issue_id)
    payload, error = _move_payload(request)
    if error is not None:
        return error

    moved_issue = controllers.move_issue(
        issue,
        payload["target_state"],
        payload["position_index"],
        request.auth,
    )
    return {
        "status": "ok",
        "issue_id": moved_issue.pk,
        "workflow_state": moved_issue.workflow_state,
        "board_position": moved_issue.board_position,
    }
