import json
from io import BytesIO

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, QueryDict
from django.http.multipartparser import MultiPartParser, MultiPartParserError
from ninja import NinjaAPI, Query, Schema
from ninja.security import HttpBasicAuth
from pydantic import Field

from djangoapp.core.controllers import (
    CollectionController,
    GroupController,
    IssueAttachmentController,
    IssueCategoryController,
    IssueCommentController,
    UserController,
)
from djangoapp.core.models import Collection, IssueAttachment, IssueCategory, IssueComment
from djangoapp.rest_api.forms import (
    CollectionForm,
    GroupManagementForm,
    IssueAttachmentForm,
    IssueCategoryForm,
    IssueCommentUpdateForm,
    UserManagementForm,
)
from djangoapp.user_interface import controllers
from djangoapp.user_interface.forms import (
    IssueArchiveForm,
    IssueCommentForm,
    IssueCreateForm,
    IssueUpdateForm,
    UserProfileForm,
)


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
    avatar_type: str = Field(description="Stored avatar type for the profile.")
    is_system_user: bool = Field(description="Whether the profile is flagged as a system user.")
    avatar_text: str = Field(description="Short fallback text rendered when no avatar image is used.")
    avatar_image_url: str | None = Field(
        description="Resolved URL of the configured or default avatar image, when present."
    )


class ManagedGroupSchema(GroupSchema):
    users: list[UserSummarySchema] = Field(description="Users who currently belong to the group.")


class ManagedUserSchema(Schema):
    id: int = Field(description="Unique identifier of the managed user.")
    username: str = Field(description="Login name of the managed user.")
    first_name: str = Field(description="Stored first name of the managed user.")
    last_name: str = Field(description="Stored last name of the managed user.")
    display_name: str = Field(description="Preferred display name shown for the managed user.")
    is_active: bool = Field(
        description="Whether the managed user may authenticate and appear in assignable user lists."
    )
    is_staff: bool = Field(description="Whether the managed user may access staff-only administration features.")
    is_superuser: bool = Field(description="Whether the managed user has unrestricted Django superuser privileges.")
    language_preference: str = Field(description="Stored language preference code for the managed user's profile.")
    avatar_type: str = Field(description="Stored avatar type for the managed user's profile.")
    is_system_user: bool = Field(description="Whether the managed user's profile is flagged as a system user.")
    avatar_text: str = Field(description="Short fallback text rendered when no avatar image is used.")
    avatar_image_url: str | None = Field(
        description="Resolved URL of the configured or default avatar image, when present."
    )
    groups: list[GroupSchema] = Field(description="Groups that currently include the managed user.")


class GroupListResponseSchema(Schema):
    data: list[GroupSchema] = Field(description="Groups that can be used to dispatch or assign issues.")


class CollectionListResponseSchema(Schema):
    data: list[CollectionSchema] = Field(description="Active collections that may own new issue numbers.")


class IssueCategoryListResponseSchema(Schema):
    data: list[IssueCategorySchema] = Field(description="Active issue categories that may be assigned to issues.")


class UserListResponseSchema(Schema):
    data: list[UserSummarySchema] = Field(
        description="Users that may be assigned to issues, optionally filtered to one group."
    )


class UserProfileSchema(Schema):
    user: UserSummarySchema = Field(description="User who owns the profile.")
    language_preference: str = Field(description="Stored language preference code for the profile.")
    language_preference_label: str = Field(description="Human-readable label for the configured language preference.")
    avatar_type: str = Field(description="Stored avatar type for the profile.")
    avatar_type_label: str = Field(description="Human-readable label for the configured avatar type.")
    is_system_user: bool = Field(description="Whether the profile is flagged as a system user.")
    avatar_text: str = Field(description="Resolved avatar text rendered when no avatar image is used.")
    avatar_image_url: str | None = Field(
        description="Resolved URL of the configured or default avatar image, when present."
    )
    assigned_issue_count: int = Field(description="Number of active issues currently assigned to the profile owner.")
    can_edit: bool = Field(description="Whether the authenticated API caller may edit this profile.")


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


class IssueHistoryEntrySchema(Schema):
    entry_type: str = Field(description="Normalized history entry type for workflow, field, or attachment changes.")
    field_name: str = Field(description="Field or entity that changed for this history entry.")
    message: str = Field(description="Human-readable summary of the recorded change.")
    detail: str = Field(description="Optional secondary detail associated with the history entry.")
    from_value: str = Field(description="Previous human-readable value, when available.")
    to_value: str = Field(description="New human-readable value, when available.")
    changed_at: str = Field(description="Timestamp when the change was recorded, encoded as ISO 8601.")
    changed_by_user: UserSummarySchema = Field(description="User who performed the recorded change.")


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
    history: list[IssueHistoryEntrySchema] = Field(
        description="Combined issue history across workflow, field, and attachment changes."
    )
    transitions: list[IssueTransitionSchema] = Field(description="Workflow state transition history for the issue.")


class IssueListResponseSchema(Schema):
    data: list[IssueSummarySchema] = Field(description="Issues that match the supplied board-style filters.")


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
    selected_group: str = Field(description="Current group filter value.")
    selected_is_escalated: str = Field(description="Current escalation filter value.")
    selected_updated_within_seconds: str = Field(description="Current relative update window filter value.")
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


class UserProfileMutationSchema(Schema):
    status: str = Field(description="Mutation result code for the profile operation.")
    profile: UserProfileSchema = Field(description="User profile payload after the mutation completed.")


class UserMutationSchema(Schema):
    status: str = Field(description="Mutation result code for the user operation.")
    user: ManagedUserSchema = Field(description="Managed user payload after the mutation completed.")


class UserDeactivationSchema(Schema):
    status: str = Field(description="Mutation result code for the user deactivation operation.")
    user_id: int = Field(description="Identifier of the managed user that was deactivated.")
    is_active: bool = Field(description="Authentication state of the managed user after the operation completed.")


class GroupMutationSchema(Schema):
    status: str = Field(description="Mutation result code for the group operation.")
    group: ManagedGroupSchema = Field(description="Managed group payload after the mutation completed.")


class GroupDeletionSchema(Schema):
    status: str = Field(description="Mutation result code for the group deletion operation.")
    group_id: int = Field(description="Identifier of the deleted group.")


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


USER_CREATE_REQUEST_BODY = _request_body(
    "User data used to create a managed user account.",
    "application/json",
    {
        "username": {"type": "string", "description": "Login name for the user account."},
        "first_name": {"type": "string", "description": "Stored first name of the user."},
        "last_name": {"type": "string", "description": "Stored last name of the user."},
        "password": {"type": "string", "description": "Initial password for the user account."},
        "is_active": {"type": "boolean", "description": "Whether the user may authenticate."},
        "is_staff": {
            "type": "boolean",
            "description": "Whether the user may access staff-only administration features.",
        },
        "is_superuser": {
            "type": "boolean",
            "description": "Whether the user should receive unrestricted superuser privileges.",
        },
        "language_preference": {
            "type": "string",
            "description": "Language preference code for the user profile.",
            "enum": ["en", "de"],
        },
        "avatar_type": {
            "type": "string",
            "description": "Avatar mode stored on the user profile.",
            "enum": ["initials", "image"],
        },
        "is_system_user": {
            "type": "boolean",
            "description": "Whether the profile should use the system-user avatar behavior.",
        },
        "group_ids": {
            "type": "array",
            "description": "Identifiers of the groups that should include the user.",
            "items": {"type": "integer"},
        },
    },
    required_fields=["username", "password"],
)


USER_UPDATE_REQUEST_BODY = _request_body(
    "User data used to update a managed user account.",
    "application/json",
    {
        "username": {"type": "string", "description": "Login name for the user account."},
        "first_name": {"type": "string", "description": "Stored first name of the user."},
        "last_name": {"type": "string", "description": "Stored last name of the user."},
        "password": {"type": "string", "description": "Optional replacement password for the user account."},
        "is_active": {"type": "boolean", "description": "Whether the user may authenticate."},
        "is_staff": {
            "type": "boolean",
            "description": "Whether the user may access staff-only administration features.",
        },
        "is_superuser": {
            "type": "boolean",
            "description": "Whether the user should receive unrestricted superuser privileges.",
        },
        "language_preference": {
            "type": "string",
            "description": "Language preference code for the user profile.",
            "enum": ["en", "de"],
        },
        "avatar_type": {
            "type": "string",
            "description": "Avatar mode stored on the user profile.",
            "enum": ["initials", "image"],
        },
        "is_system_user": {
            "type": "boolean",
            "description": "Whether the profile should use the system-user avatar behavior.",
        },
        "group_ids": {
            "type": "array",
            "description": "Identifiers of the groups that should include the user.",
            "items": {"type": "integer"},
        },
    },
    required_fields=["username"],
)


GROUP_REQUEST_BODY = _request_body(
    "Group data used to create or update a managed group.",
    "application/json",
    {
        "name": {"type": "string", "description": "Display name of the managed group."},
        "user_ids": {
            "type": "array",
            "description": "Identifiers of the users that should belong to the group.",
            "items": {"type": "integer"},
        },
    },
    required_fields=["name"],
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
    "Multipart payload used to update an existing issue with partial PUT semantics, optionally including one attachment update.",
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
                "NEW",
                "TRIAGE",
                "ASSIGNED",
                "IN_PROGRESS",
                "WAITING",
                "RESOLVED",
                "CLOSED",
                "REJECTED",
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


def _issue_update_payload(payload, issue):
    merged_payload = {
        "title": issue.title,
        "description_markdown": issue.description_markdown,
        "collection": issue.collection_id,
        "category": issue.category_id,
        "priority": issue.priority,
        "group": issue.group_id or "",
        "user": issue.user_id or "",
        "is_escalated": issue.is_escalated,
        "workflow_state": issue.workflow_state,
        "transition_reason": "",
    }
    merged_payload.update(payload)

    if "user" in payload and "group" not in payload:
        if payload["user"] not in (None, ""):
            merged_payload["group"] = ""

    return merged_payload


MOVE_REQUEST_BODY = _request_body(
    "Payload used to move an issue to a different workflow state and position.",
    "application/json",
    {
        "target_state": {
            "type": "string",
            "description": "Destination workflow state code for the move operation.",
            "enum": [
                "NEW",
                "TRIAGE",
                "ASSIGNED",
                "IN_PROGRESS",
                "WAITING",
                "RESOLVED",
                "CLOSED",
                "REJECTED",
            ],
        },
        "position_index": {
            "type": "integer",
            "description": "Zero-based target position inside the destination workflow state column.",
        },
    },
    required_fields=["target_state", "position_index"],
)


PROFILE_UPDATE_REQUEST_BODY = _request_body(
    "Multipart payload used to update the authenticated user's profile settings.",
    "multipart/form-data",
    {
        "language_preference": {
            "type": "string",
            "description": "Language preference code.",
            "enum": ["en", "de"],
        },
        "avatar_type": {
            "type": "string",
            "description": "Avatar type used when no new image upload overrides it.",
            "enum": ["initials", "image"],
        },
        "is_system_user": {
            "type": "boolean",
            "description": "Whether the profile should use the default agent avatar when no custom avatar image is uploaded.",
        },
        "avatar_image": {
            "type": "string",
            "format": "binary",
            "description": "Optional custom avatar image upload.",
        },
        "clear_avatar_image": {
            "type": "boolean",
            "description": "Whether the currently stored avatar image should be removed.",
        },
    },
    required_fields=["language_preference", "avatar_type"],
)


INVALID_PAYLOAD_ERROR = (400, {"error": "Invalid request payload."})


api = NinjaAPI(
    title="Ticket System Mock API",
    version="1.0.0",
    description=(
        "Machine-facing REST API for reading issue data, reference data, dashboard projections, "
        "and issue workflow mutations in Ticket System Mock."
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


@api.get(
    "/profile/me",
    response=UserProfileSchema,
    summary="Get authenticated user profile",
    description="Return the authenticated user's editable profile settings and resolved avatar state.",
    tags=["Profiles"],
)
def current_user_profile(request):
    return _serialize_user_profile(controllers.get_user_profile(request.auth), can_edit=True)


def _forbidden_response():
    return 403, {"error": "Superuser access required."}


def _require_superuser(request):
    if request.auth.is_superuser:
        return None
    return _forbidden_response()


@api.put(
    "/profile/me",
    response={200: UserProfileMutationSchema, 400: dict},
    summary="Update authenticated user profile",
    description="Update the authenticated user's language preference and avatar configuration.",
    tags=["Profiles"],
    openapi_extra=PROFILE_UPDATE_REQUEST_BODY,
)
def update_current_user_profile(request):
    payload, files, error = _request_form_payload(request)
    if error is not None:
        return error

    form = UserProfileForm(payload, files, instance=controllers.get_user_profile(request.auth))
    if not form.is_valid():
        return _form_error_response(form)

    profile = controllers.update_user_profile(form.instance, form.cleaned_data)
    return {"status": "updated", "profile": _serialize_user_profile(profile, can_edit=True)}


def _serialize_user(user):
    profile = controllers.get_user_profile(user)
    return {
        "id": user.pk,
        "username": user.get_username(),
        "display_name": user.get_full_name() or user.get_username(),
        "avatar_type": profile.avatar_type,
        "is_system_user": profile.is_system_user,
        "avatar_text": profile.avatar_text,
        "avatar_image_url": profile.avatar_image_url,
    }


def _serialize_user_profile(profile, *, can_edit):
    return {
        "user": _serialize_user(profile.user),
        "language_preference": profile.language_preference,
        "language_preference_label": str(profile.get_language_preference_display()),
        "avatar_type": profile.avatar_type,
        "avatar_type_label": str(profile.get_avatar_type_display()),
        "is_system_user": profile.is_system_user,
        "avatar_text": profile.avatar_text,
        "avatar_image_url": profile.avatar_image_url,
        "assigned_issue_count": controllers.build_user_profile_context(profile, profile.user)["assigned_issue_count"],
        "can_edit": can_edit,
    }


def _serialize_group(group):
    return {
        "id": group.pk,
        "name": group.name,
    }


def _serialize_managed_group(group):
    return {
        **_serialize_group(group),
        "users": [_serialize_user(user) for user in group.user_set.order_by("username")],
    }


def _serialize_managed_user(user):
    profile = controllers.get_user_profile(user)
    return {
        "id": user.pk,
        "username": user.get_username(),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "display_name": user.get_full_name() or user.get_username(),
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "language_preference": profile.language_preference,
        "avatar_type": profile.avatar_type,
        "is_system_user": profile.is_system_user,
        "avatar_text": profile.avatar_text,
        "avatar_image_url": profile.avatar_image_url,
        "groups": [_serialize_group(group) for group in user.groups.order_by("name")],
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
        "history": [_serialize_history_entry(history_entry) for history_entry in detail_context["issue_history"]],
        "transitions": [_serialize_transition(transition) for transition in detail_context["issue_transitions"]],
    }


def _serialize_history_entry(history_entry):
    return {
        "entry_type": history_entry["entry_type"],
        "field_name": history_entry["field_name"],
        "message": history_entry["message"],
        "detail": history_entry["detail"],
        "from_value": history_entry["from_value"],
        "to_value": history_entry["to_value"],
        "changed_at": history_entry["changed_at"].isoformat(),
        "changed_by_user": _serialize_user(history_entry["changed_by_user"]),
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
        "selected_group": context["selected_group"],
        "selected_is_escalated": context["selected_is_escalated"],
        "selected_updated_within_seconds": context["selected_updated_within_seconds"],
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


def _management_mutation_response(
    request,
    *,
    form_class,
    mutate,
    serializer,
    response_key,
    created=False,
    form_kwargs=None,
):
    forbidden = _require_superuser(request)
    if forbidden is not None:
        return forbidden

    payload, error = _request_payload(request)
    if error is not None:
        return error

    form = form_class(payload, **(form_kwargs or {}))
    if not form.is_valid():
        return _form_error_response(form)

    managed_object = mutate(form.cleaned_data)
    response = {"status": "created" if created else "updated", response_key: serializer(managed_object)}
    if created:
        return 201, response
    return response


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
    response=GroupListResponseSchema,
    summary="List groups",
    description="Return all groups under the root data key that can be used to dispatch or assign issues.",
    tags=["Reference Data"],
)
def groups(request):
    return {"data": [_serialize_group(group) for group in Group.objects.order_by("name")]}


@api.post(
    "/groups",
    response={201: GroupMutationSchema, 400: dict, 403: dict},
    summary="Create group",
    description="Create a new managed group and optionally assign users to it. Superuser access is required.",
    tags=["Administration"],
    openapi_extra=GROUP_REQUEST_BODY,
)
def create_group(request):
    return _management_mutation_response(
        request,
        form_class=GroupManagementForm,
        mutate=GroupController.create,
        serializer=_serialize_managed_group,
        response_key="group",
        created=True,
    )


@api.get(
    "/groups/{group_id}",
    response={200: ManagedGroupSchema, 403: dict},
    summary="Get managed group",
    description="Return a managed group together with its current memberships. Superuser access is required.",
    tags=["Administration"],
)
def group_detail(request, group_id: int):
    forbidden = _require_superuser(request)
    if forbidden is not None:
        return forbidden

    group = Group.objects.get(pk=group_id)
    return _serialize_managed_group(group)


@api.put(
    "/groups/{group_id}",
    response={200: GroupMutationSchema, 400: dict, 403: dict},
    summary="Update group",
    description="Update a managed group and optionally replace its memberships. Superuser access is required.",
    tags=["Administration"],
    openapi_extra=GROUP_REQUEST_BODY,
)
def update_group(request, group_id: int):
    group = Group.objects.get(pk=group_id)
    return _management_mutation_response(
        request,
        form_class=GroupManagementForm,
        mutate=lambda cleaned_data: GroupController.update(group, cleaned_data),
        serializer=_serialize_managed_group,
        response_key="group",
        form_kwargs={"instance": group},
    )


@api.delete(
    "/groups/{group_id}",
    response={200: GroupDeletionSchema, 403: dict, 409: dict},
    summary="Delete group",
    description="Delete a managed group. The operation is rejected while issues still reference the group. Superuser access is required.",
    tags=["Administration"],
)
def delete_group(request, group_id: int):
    forbidden = _require_superuser(request)
    if forbidden is not None:
        return forbidden

    group = Group.objects.get(pk=group_id)
    try:
        GroupController.delete(group)
    except ProtectedError:
        return 409, {"error": "Group is still assigned to one or more issues."}

    return {"status": "deleted", "group_id": group_id}


@api.get(
    "/users",
    response=UserListResponseSchema,
    summary="List users",
    description="Return users under the root data key that may be assigned to issues, optionally filtered to one group.",
    tags=["Reference Data"],
)
def users(
    request,
    group_id: int | None = Query(None, description="Optional group identifier used to limit the returned users."),
):
    user_model = get_user_model()
    queryset = user_model.objects.filter(is_active=True).order_by("username")
    if group_id is not None:
        queryset = queryset.filter(groups__id=group_id).distinct()
    return {"data": [_serialize_user(user) for user in queryset]}


@api.post(
    "/users",
    response={201: UserMutationSchema, 400: dict, 403: dict},
    summary="Create user",
    description="Create a new managed user account with profile settings and group memberships. Superuser access is required.",
    tags=["Administration"],
    openapi_extra=USER_CREATE_REQUEST_BODY,
)
def create_user(request):
    return _management_mutation_response(
        request,
        form_class=UserManagementForm,
        mutate=UserController.create,
        serializer=_serialize_managed_user,
        response_key="user",
        created=True,
        form_kwargs={"require_password": True},
    )


@api.get(
    "/users/{user_id}",
    response={200: ManagedUserSchema, 403: dict},
    summary="Get managed user",
    description="Return a managed user together with profile settings and current group memberships. Superuser access is required.",
    tags=["Administration"],
)
def user_detail(request, user_id: int):
    forbidden = _require_superuser(request)
    if forbidden is not None:
        return forbidden

    user_model = get_user_model()
    user = user_model.objects.get(pk=user_id)
    return _serialize_managed_user(user)


@api.put(
    "/users/{user_id}",
    response={200: UserMutationSchema, 400: dict, 403: dict},
    summary="Update user",
    description="Update a managed user account, its profile settings, and its group memberships. Superuser access is required.",
    tags=["Administration"],
    openapi_extra=USER_UPDATE_REQUEST_BODY,
)
def update_user(request, user_id: int):
    user_model = get_user_model()
    user = user_model.objects.get(pk=user_id)
    controllers.get_user_profile(user)
    return _management_mutation_response(
        request,
        form_class=UserManagementForm,
        mutate=lambda cleaned_data: UserController.update(user, cleaned_data),
        serializer=_serialize_managed_user,
        response_key="user",
        form_kwargs={"instance": user},
    )


@api.delete(
    "/users/{user_id}",
    response={200: UserDeactivationSchema, 403: dict},
    summary="Deactivate user",
    description="Deactivate a managed user account without deleting historical issue references. Superuser access is required.",
    tags=["Administration"],
)
def delete_user(request, user_id: int):
    forbidden = _require_superuser(request)
    if forbidden is not None:
        return forbidden

    user_model = get_user_model()
    user = user_model.objects.get(pk=user_id)
    user = UserController.deactivate(user)
    return {"status": "deactivated", "user_id": user.pk, "is_active": user.is_active}


@api.get(
    "/users/{username}/profile",
    response=UserProfileSchema,
    summary="Get public user profile",
    description="Return the public profile information for a user together with resolved avatar data.",
    tags=["Profiles"],
)
def user_profile(request, username: str):
    profile = controllers.get_user_profile_by_username(username)
    return _serialize_user_profile(profile, can_edit=request.auth.pk == profile.user_id)


@api.get(
    "/collections",
    response=CollectionListResponseSchema,
    summary="List active collections",
    description="Return active collections under the root data key that may own new issue numbers.",
    tags=["Reference Data"],
)
def collections(request):
    return {
        "data": [
            _serialize_collection(collection)
            for collection in Collection.objects.filter(is_active=True).order_by("name")
        ]
    }


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
    response=IssueCategoryListResponseSchema,
    summary="List active issue categories",
    description="Return active issue categories under the root data key that may be assigned to issues.",
    tags=["Reference Data"],
)
def categories(request):
    return {
        "data": [
            _serialize_category(category) for category in IssueCategory.objects.filter(is_active=True).order_by("name")
        ]
    }


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
    group: str = Query("", description="Optional group identifier used to limit the board projection."),
    is_escalated: str = Query("", description="Optional escalation flag used to limit the board projection."),
    workflow_state: str = Query("", description="Optional workflow state code used to limit the board projection."),
    workflow_state_label: str = Query(
        "",
        description="Optional workflow state label used to limit the board projection, for example New or In Progress.",
    ),
    updated_within_seconds: str = Query(
        "",
        description="Optional relative time window used to limit board issues to entries updated within the last X seconds.",
    ),
):
    context = controllers.build_board_context({
        "search": search,
        "assignee": assignee,
        "priority": priority,
        "collection": collection,
        "category": category,
        "group": group,
        "is_escalated": is_escalated,
        "workflow_state": workflow_state,
        "workflow_state_label": workflow_state_label,
        "updated_within_seconds": updated_within_seconds,
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
    response=IssueListResponseSchema,
    summary="List issues",
    description="Return issues under the root data key that match the supplied board-style filters.",
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
    group: str = Query("", description="Optional group identifier used to limit the returned issues."),
    is_escalated: str = Query("", description="Optional escalation flag used to limit the returned issues."),
    workflow_state: str = Query("", description="Optional workflow state code used to limit the returned issues."),
    workflow_state_label: str = Query(
        "",
        description="Optional workflow state label used to limit the returned issues, for example New or In Progress.",
    ),
    updated_within_seconds: str = Query(
        "",
        description="Optional relative time window used to limit returned issues to entries updated within the last X seconds.",
    ),
):
    board_context = controllers.build_board_context({
        "search": search,
        "assignee": assignee,
        "priority": priority,
        "collection": collection,
        "category": category,
        "group": group,
        "is_escalated": is_escalated,
        "workflow_state": workflow_state,
        "workflow_state_label": workflow_state_label,
        "updated_within_seconds": updated_within_seconds,
    })
    issues = []
    for column in board_context["board_columns"]:
        issues.extend(column["issues"])
    return {"data": [_serialize_issue(issue) for issue in issues]}


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

    form = IssueUpdateForm(_issue_update_payload(payload, issue), files, instance=issue)
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

    updated_attachment = IssueAttachmentController.update(issue_attachment, form.cleaned_data, request.auth)
    return {"status": "updated", "attachment": _serialize_attachment(updated_attachment)}


@api.delete(
    "/issues/{issue_id}/attachments/{attachment_id}",
    response={200: dict},
    summary="Delete issue attachment",
    description="Delete an existing attachment from an issue.",
    tags=["Issues"],
)
def delete_issue_attachment(request, issue_id: int, attachment_id: int):
    issue_attachment = _get_issue_attachment(issue_id, attachment_id)
    IssueAttachmentController.delete(issue_attachment, request.auth)
    return {"status": "deleted", "attachment_id": attachment_id}


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
