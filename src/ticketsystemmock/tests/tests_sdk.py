from __future__ import annotations

import asyncio
import json
import unittest
from dataclasses import dataclass
from unittest.mock import patch

import httpx
from ticketsystemmock.client import AsyncTicketSystemClient, TicketSystemClient
from ticketsystemmock.exceptions import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ValidationError,
)
from ticketsystemmock.models import IssueAttachment, IssueSummary
from ticketsystemmock.models.base import ApiModel, _convert_value
from ticketsystemmock.resources import __all__ as resource_exports
from ticketsystemmock.transport import normalize_base_url

from ticketsystemmock import AvatarType, CommentVisibility, IssuePriority, LanguagePreference, WorkflowState

_DEFAULT_CATEGORY = object()


def make_sync_client(handler):
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://example.test")
    return TicketSystemClient("http://example.test", "demo", "password", client=client)


def make_async_client(handler):
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://example.test")
    return AsyncTicketSystemClient("http://example.test", "demo", "password", client=client)


def make_user_summary(*, user_id: int = 4, username: str = "demo", display_name: str = "Demo User"):
    return {
        "id": user_id,
        "username": username,
        "display_name": display_name,
        "avatar_type": "initials",
        "is_system_user": False,
        "avatar_text": "DU",
        "avatar_image_url": None,
    }


def make_collection(*, collection_id: int = 1, name: str = "Tasks"):
    return {
        "id": collection_id,
        "name": name,
        "prefix": name[:4].upper(),
        "description": f"{name} description",
    }


def make_category(*, category_id: int = 2, name: str = "Network", code: str = "NETWORK"):
    return {
        "id": category_id,
        "name": name,
        "code": code,
        "description": f"{name} description",
    }


def make_group(*, group_id: int = 3, name: str = "Network Operations"):
    return {"id": group_id, "name": name, "description": f"{name} description"}


def make_issue_summary(
    *, issue_id: int = 5, workflow_state: str = "NEW", category=_DEFAULT_CATEGORY, group=None, user=None
):
    return {
        "id": issue_id,
        "issue_number": f"TASK-{issue_id}",
        "title": "Router outage",
        "description_markdown": "Details",
        "priority": "HIGH",
        "priority_label": "High",
        "workflow_state": workflow_state,
        "workflow_state_label": workflow_state.replace("_", " ").title(),
        "board_position": 0,
        "is_escalated": False,
        "created_at": "2026-06-13T10:00:00+00:00",
        "updated_at": "2026-06-13T10:05:00+00:00",
        "resolved_at": None,
        "closed_at": None,
        "archived_at": None,
        "collection": make_collection(),
        "category": make_category() if category is _DEFAULT_CATEGORY else category,
        "group": group,
        "user": user,
    }


def make_issue_detail(*, issue_id: int = 5, workflow_state: str = "NEW"):
    payload = make_issue_summary(issue_id=issue_id, workflow_state=workflow_state)
    payload.update({
        "attachments": [],
        "comments": [],
        "history": [],
        "transitions": [],
    })
    return payload


def make_attachment(*, attachment_id: int = 7, filename: str = "trace.txt"):
    return {
        "id": attachment_id,
        "original_filename": filename,
        "description": "Traceroute output",
        "content_type": "text/plain",
        "file_size": 9,
        "uploaded_at": "2026-06-13T10:06:00+00:00",
        "file_url": f"/api/issues/5/attachments/{attachment_id}/download",
        "uploaded_by_user": make_user_summary(user_id=1),
    }


def make_comment(*, comment_id: int = 4, body: str = "updated body"):
    return {
        "id": comment_id,
        "body": body,
        "visibility": "INTERNAL",
        "visibility_label": "Internal",
        "created_at": "2026-06-13T10:05:00+00:00",
        "author_user": make_user_summary(user_id=1),
    }


def make_profile(*, username: str = "demo"):
    return {
        "user": make_user_summary(username=username, display_name="Demo User"),
        "language_preference": "de",
        "language_preference_label": "Deutsch",
        "avatar_type": "initials",
        "avatar_type_label": "Initials",
        "is_system_user": False,
        "avatar_text": "DU",
        "avatar_image_url": None,
        "assigned_issue_count": 2,
        "can_edit": username == "demo",
    }


def make_managed_user(*, user_id: int = 8, username: str = "coordinator"):
    return {
        "id": user_id,
        "username": username,
        "first_name": "Case",
        "last_name": "Coordinator",
        "display_name": "Case Coordinator",
        "is_active": True,
        "is_staff": True,
        "is_superuser": False,
        "language_preference": "de",
        "avatar_type": "image",
        "is_system_user": True,
        "avatar_text": "CC",
        "avatar_image_url": None,
        "groups": [make_group()],
    }


def make_managed_group(*, group_id: int = 3, name: str = "Network Operations"):
    return {
        "id": group_id,
        "name": name,
        "description": f"{name} description",
        "users": [make_user_summary(user_id=8, username="coordinator", display_name="Case Coordinator")],
    }


def make_workflow_state_auto_assignment_rule(
    *,
    rule_id: int = 2,
    workflow_state: str = "ASSIGNED",
    group=None,
    user=None,
    is_active: bool = True,
):
    return {
        "id": rule_id,
        "workflow_state": workflow_state,
        "workflow_state_label": workflow_state.replace("_", " ").title(),
        "group": group or make_group(),
        "user": user or make_user_summary(user_id=8, username="coordinator", display_name="Case Coordinator"),
        "is_active": is_active,
        "created_at": "2026-06-13T10:00:00+00:00",
        "updated_at": "2026-06-13T10:05:00+00:00",
    }


@dataclass(slots=True)
class ExampleNestedModel(ApiModel):
    value: str


@dataclass(slots=True)
class ExampleContainerModel(ApiModel):
    nested: ExampleNestedModel | None
    values: list[int]
    metadata: dict[str, str]


class TicketSystemSdkTests(unittest.TestCase):
    def test_public_enums_expose_current_api_values(self):
        self.assertEqual(IssuePriority.HIGH.value, "HIGH")
        self.assertEqual(WorkflowState.IN_PROGRESS.value, "IN_PROGRESS")
        self.assertEqual(CommentVisibility.INTERNAL.value, "INTERNAL")
        self.assertEqual(LanguagePreference.DE.value, "de")
        self.assertEqual(AvatarType.IMAGE.value, "image")

    def test_sync_auth_and_issue_list_requests_match_contract(self):
        def handler(request):
            self.assertEqual(request.headers["authorization"], "Basic ZGVtbzpwYXNzd29yZA==")
            if request.url.path == "/api/auth/me":
                return httpx.Response(
                    200,
                    json={
                        "id": 1,
                        "username": "demo",
                        "display_name": "Demo User",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                )

            self.assertEqual(request.url.path, "/api/issues")
            self.assertEqual(request.url.params["search"], "router")
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 5,
                            "issue_number": "TASK-5",
                            "title": "Router outage",
                            "description_markdown": "Details",
                            "priority": "HIGH",
                            "priority_label": "High",
                            "workflow_state": "NEW",
                            "workflow_state_label": "New",
                            "board_position": 0,
                            "is_escalated": True,
                            "created_at": "2026-06-13T10:00:00+00:00",
                            "updated_at": "2026-06-13T10:05:00+00:00",
                            "resolved_at": None,
                            "closed_at": None,
                            "archived_at": None,
                            "collection": {"id": 1, "name": "Tasks", "prefix": "TASK", "description": "Ops"},
                            "category": {"id": 2, "name": "Network", "code": "NETWORK", "description": "Net"},
                            "group": {"id": 3, "name": "Network Operations"},
                            "user": {
                                "id": 4,
                                "username": "demo",
                                "display_name": "Demo User",
                                "avatar_type": "initials",
                                "is_system_user": False,
                                "avatar_text": "DU",
                                "avatar_image_url": None,
                            },
                        }
                    ]
                },
            )

        sdk = make_sync_client(handler)
        self.assertEqual(sdk.auth.me().username, "demo")
        issues = sdk.issues.list(search="router")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].issue_number, "TASK-5")
        sdk.close()

    def test_sync_issue_create_uses_multipart_and_validation_errors_are_normalized(self):
        def handler(request):
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/issues")
            self.assertIn("multipart/form-data", request.headers["content-type"])
            return httpx.Response(400, json={"errors": {"title": [{"message": "This field is required."}]}})

        sdk = make_sync_client(handler)
        with self.assertRaises(ValidationError) as raised:
            sdk.issues.create(collection=1, category=2, priority="HIGH", files={"attachment_file": ("a.txt", b"x")})
        self.assertIn("title", raised.exception.errors)
        sdk.close()

    def test_issue_summary_allows_missing_category(self):
        summary = IssueSummary.from_dict(make_issue_summary(category=None))

        self.assertIsNone(summary.category)

    def test_sync_admin_errors_are_typed(self):
        responses = {
            "/api/users/7": httpx.Response(403, json={"error": "Superuser access required."}),
            "/api/groups/3": httpx.Response(409, json={"error": "Group is still assigned to one or more issues."}),
        }

        def handler(request):
            return responses[request.url.path]

        sdk = make_sync_client(handler)
        with self.assertRaises(AuthorizationError):
            sdk.admin.users.get(7)
        with self.assertRaises(ConflictError):
            sdk.admin.groups.delete(3)
        sdk.close()

    def test_attachment_resolves_relative_download_url(self):
        attachment = IssueAttachment.from_dict({
            "id": 1,
            "original_filename": "report.txt",
            "description": "Report",
            "content_type": "text/plain",
            "file_size": 10,
            "uploaded_at": "2026-06-13T10:00:00+00:00",
            "file_url": "/api/issues/1/attachments/1/download",
            "uploaded_by_user": {
                "id": 4,
                "username": "demo",
                "display_name": "Demo User",
                "avatar_type": "initials",
                "is_system_user": False,
                "avatar_text": "DU",
                "avatar_image_url": None,
            },
        })
        self.assertEqual(
            attachment.resolved_file_url("http://example.test"),
            "http://example.test/api/issues/1/attachments/1/download",
        )

    def test_comment_and_attachment_facades_delegate_to_nested_issue_routes(self):
        def handler(request):
            if request.url.path == "/api/issues/5/comments":
                self.assertEqual(request.method, "POST")
                return httpx.Response(
                    201,
                    json={
                        "status": "comment-added",
                        "issue": {
                            "id": 5,
                            "issue_number": "TASK-5",
                            "title": "Router outage",
                            "description_markdown": "Details",
                            "priority": "HIGH",
                            "priority_label": "High",
                            "workflow_state": "NEW",
                            "workflow_state_label": "New",
                            "board_position": 0,
                            "is_escalated": False,
                            "created_at": "2026-06-13T10:00:00+00:00",
                            "updated_at": "2026-06-13T10:05:00+00:00",
                            "resolved_at": None,
                            "closed_at": None,
                            "archived_at": None,
                            "collection": {"id": 1, "name": "Tasks", "prefix": "TASK", "description": "Ops"},
                            "category": {"id": 2, "name": "Network", "code": "NETWORK", "description": "Net"},
                            "group": None,
                            "user": None,
                            "attachments": [],
                            "comments": [],
                            "history": [],
                            "transitions": [],
                        },
                    },
                )

            self.assertEqual(request.url.path, "/api/issues/5/attachments/7/download")
            return httpx.Response(200, content=b"file-bytes")

        sdk = make_sync_client(handler)
        comment_result = sdk.comments.add(5, body="hello", visibility="INTERNAL")
        self.assertEqual(comment_result.status, "comment-added")
        attachment_bytes = sdk.attachments.download(5, 7)
        self.assertEqual(attachment_bytes, b"file-bytes")
        sdk.close()

    def test_admin_mutations_use_json_and_parse_responses(self):
        responses = iter([
            httpx.Response(
                201,
                json={
                    "status": "created",
                    "user": {
                        "id": 8,
                        "username": "coordinator",
                        "first_name": "Case",
                        "last_name": "Coordinator",
                        "display_name": "Case Coordinator",
                        "is_active": True,
                        "is_staff": True,
                        "is_superuser": False,
                        "language_preference": "de",
                        "avatar_type": "image",
                        "is_system_user": True,
                        "avatar_text": "CC",
                        "avatar_image_url": None,
                        "groups": [{"id": 3, "name": "Network Operations"}],
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    "status": "updated",
                    "group": {
                        "id": 3,
                        "name": "Escalation Desk",
                        "users": [
                            {
                                "id": 8,
                                "username": "coordinator",
                                "display_name": "Case Coordinator",
                                "avatar_type": "image",
                                "is_system_user": True,
                                "avatar_text": "CC",
                                "avatar_image_url": None,
                            }
                        ],
                    },
                },
            ),
        ])

        def handler(request):
            body = json.loads(request.content.decode())
            self.assertEqual(request.headers["content-type"], "application/json")
            if request.url.path == "/api/users":
                self.assertEqual(request.method, "POST")
                self.assertEqual(body["username"], "coordinator")
                self.assertEqual(body["group_ids"], [3])
            else:
                self.assertEqual(request.method, "PUT")
                self.assertEqual(request.url.path, "/api/groups/3")
                self.assertEqual(body["name"], "Escalation Desk")
                self.assertEqual(body["user_ids"], [8])
            return next(responses)

        sdk = make_sync_client(handler)
        created_user = sdk.admin.users.create(username="coordinator", password="secret", group_ids=[3])
        self.assertEqual(created_user.user.username, "coordinator")
        updated_group = sdk.admin.groups.update(3, name="Escalation Desk", user_ids=[8])
        self.assertEqual(updated_group.group.name, "Escalation Desk")
        self.assertEqual(updated_group.group.users[0].username, "coordinator")
        sdk.close()

    def test_admin_workflow_rule_mutations_use_json_and_parse_responses(self):
        responses = iter([
            httpx.Response(200, json={"data": [make_workflow_state_auto_assignment_rule()]}),
            httpx.Response(
                201,
                json={
                    "status": "created",
                    "rule": make_workflow_state_auto_assignment_rule(),
                },
            ),
            httpx.Response(200, json=make_workflow_state_auto_assignment_rule()),
            httpx.Response(
                200,
                json={
                    "status": "updated",
                    "rule": make_workflow_state_auto_assignment_rule(workflow_state="WAITING", is_active=False),
                },
            ),
            httpx.Response(200, json={"status": "deleted", "rule_id": 2}),
        ])

        def handler(request):
            body = json.loads(request.content.decode()) if request.content else None
            if request.url.path == "/api/workflow-state-auto-assignment-rules":
                if request.method == "GET":
                    return next(responses)
                self.assertEqual(request.method, "POST")
                self.assertEqual(body["workflow_state"], "ASSIGNED")
                self.assertEqual(body["group"], 3)
                self.assertEqual(body["user"], 8)
                self.assertTrue(body["is_active"])
                return next(responses)

            self.assertEqual(request.url.path, "/api/workflow-state-auto-assignment-rules/2")
            if request.method == "GET":
                return next(responses)
            if request.method == "PUT":
                self.assertEqual(body["workflow_state"], "WAITING")
                self.assertFalse(body["is_active"])
                return next(responses)
            self.assertEqual(request.method, "DELETE")
            return next(responses)

        sdk = make_sync_client(handler)
        self.assertEqual(sdk.admin.workflow_state_auto_assignment_rules.list()[0].workflow_state, "ASSIGNED")
        created_rule = sdk.admin.workflow_state_auto_assignment_rules.create(
            workflow_state=WorkflowState.ASSIGNED,
            group=3,
            user=8,
            is_active=True,
        )
        self.assertEqual(created_rule.rule.group.name, "Network Operations")
        self.assertEqual(sdk.admin.workflow_state_auto_assignment_rules.get(2).workflow_state_label, "Assigned")
        updated_rule = sdk.admin.workflow_state_auto_assignment_rules.update(
            2,
            workflow_state=WorkflowState.WAITING,
            group=3,
            user=8,
            is_active=False,
        )
        self.assertEqual(updated_rule.rule.workflow_state, "WAITING")
        self.assertEqual(sdk.admin.workflow_state_auto_assignment_rules.delete(2).rule_id, 2)
        sdk.close()

    def test_admin_instance_reset_uses_json_and_parses_response(self):
        def handler(request):
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/instance-reset")
            self.assertEqual(json.loads(request.content.decode()), {"confirm_reset": True})
            return httpx.Response(
                200,
                json={
                    "status": "reset",
                    "preserved_user_id": 1,
                    "deleted_counts": {"issues": 4, "users": 2},
                },
            )

        sdk = make_sync_client(handler)
        reset_result = sdk.admin.reset_instance(confirm_reset=True)
        self.assertEqual(reset_result.status, "reset")
        self.assertEqual(reset_result.preserved_user_id, 1)
        self.assertEqual(reset_result.deleted_counts["issues"], 4)
        sdk.close()

    def test_issue_update_partial_and_comment_update_use_expected_payload_types(self):
        responses = iter([
            httpx.Response(
                200,
                json={
                    "status": "updated",
                    "issue": {
                        "id": 5,
                        "issue_number": "TASK-5",
                        "title": "Router outage",
                        "description_markdown": "Details",
                        "priority": "HIGH",
                        "priority_label": "High",
                        "workflow_state": "IN_PROGRESS",
                        "workflow_state_label": "In Progress",
                        "board_position": 0,
                        "is_escalated": False,
                        "created_at": "2026-06-13T10:00:00+00:00",
                        "updated_at": "2026-06-13T10:05:00+00:00",
                        "resolved_at": None,
                        "closed_at": None,
                        "archived_at": None,
                        "collection": {"id": 1, "name": "Tasks", "prefix": "TASK", "description": "Ops"},
                        "category": {"id": 2, "name": "Network", "code": "NETWORK", "description": "Net"},
                        "group": None,
                        "user": None,
                        "attachments": [],
                        "comments": [],
                        "history": [],
                        "transitions": [],
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    "status": "updated",
                    "comment": {
                        "id": 4,
                        "body": "updated body",
                        "visibility": "INTERNAL",
                        "visibility_label": "Internal",
                        "created_at": "2026-06-13T10:05:00+00:00",
                        "author_user": {
                            "id": 1,
                            "username": "demo",
                            "display_name": "Demo User",
                            "avatar_type": "initials",
                            "is_system_user": False,
                            "avatar_text": "DU",
                            "avatar_image_url": None,
                        },
                    },
                },
            ),
        ])

        def handler(request):
            if request.url.path == "/api/issues/5":
                self.assertEqual(request.method, "PUT")
                self.assertEqual(request.headers["content-type"], "application/x-www-form-urlencoded")
                self.assertEqual(request.content.decode(), "workflow_state=IN_PROGRESS")
            else:
                self.assertEqual(request.url.path, "/api/issues/5/comments/4")
                self.assertEqual(request.method, "PUT")
                self.assertEqual(request.headers["content-type"], "application/json")
                body = json.loads(request.content.decode())
                self.assertEqual(body, {"body": "updated body", "visibility": "INTERNAL"})
            return next(responses)

        sdk = make_sync_client(handler)
        updated_issue = sdk.issues.update(5, workflow_state="IN_PROGRESS")
        self.assertEqual(updated_issue.issue.workflow_state, "IN_PROGRESS")
        updated_comment = sdk.comments.update(5, 4, body="updated body", visibility="INTERNAL")
        self.assertEqual(updated_comment.comment.body, "updated body")
        sdk.close()

    def test_comment_and_attachment_upload_facades_use_multipart_routes(self):
        responses = iter([
            httpx.Response(
                201,
                json={
                    "status": "comment-added",
                    "issue": {
                        "id": 5,
                        "issue_number": "TASK-5",
                        "title": "Router outage",
                        "description_markdown": "Details",
                        "priority": "HIGH",
                        "priority_label": "High",
                        "workflow_state": "NEW",
                        "workflow_state_label": "New",
                        "board_position": 0,
                        "is_escalated": False,
                        "created_at": "2026-06-13T10:00:00+00:00",
                        "updated_at": "2026-06-13T10:05:00+00:00",
                        "resolved_at": None,
                        "closed_at": None,
                        "archived_at": None,
                        "collection": {"id": 1, "name": "Tasks", "prefix": "TASK", "description": "Ops"},
                        "category": {"id": 2, "name": "Network", "code": "NETWORK", "description": "Net"},
                        "group": None,
                        "user": None,
                        "attachments": [],
                        "comments": [],
                        "history": [],
                        "transitions": [],
                    },
                },
            ),
            httpx.Response(
                201,
                json={
                    "status": "created",
                    "attachment": {
                        "id": 7,
                        "original_filename": "trace.txt",
                        "description": "Traceroute output",
                        "content_type": "text/plain",
                        "file_size": 9,
                        "uploaded_at": "2026-06-13T10:06:00+00:00",
                        "file_url": "/api/issues/5/attachments/7/download",
                        "uploaded_by_user": {
                            "id": 1,
                            "username": "demo",
                            "display_name": "Demo User",
                            "avatar_type": "initials",
                            "is_system_user": False,
                            "avatar_text": "DU",
                            "avatar_image_url": None,
                        },
                    },
                },
            ),
        ])

        def handler(request):
            self.assertIn("multipart/form-data", request.headers["content-type"])
            if request.url.path == "/api/issues/5/comments":
                self.assertEqual(request.method, "POST")
                self.assertIn(b'name="attachment_file"', request.content)
            else:
                self.assertEqual(request.url.path, "/api/issues/5/attachments")
                self.assertEqual(request.method, "POST")
                self.assertIn(b'name="file"', request.content)
            return next(responses)

        sdk = make_sync_client(handler)
        comment_result = sdk.comments.add(
            5,
            body="Traceroute attached",
            visibility="INTERNAL",
            files={"attachment_file": ("trace.txt", b"hop1\nhop2", "text/plain")},
        )
        self.assertEqual(comment_result.status, "comment-added")
        attachment_result = sdk.attachments.add(
            5,
            description="Traceroute output",
            files={"file": ("trace.txt", b"hop1\nhop2", "text/plain")},
        )
        self.assertEqual(attachment_result.attachment.original_filename, "trace.txt")
        sdk.close()

    def test_async_health_and_move_paths(self):
        async def runner():
            def handler(request):
                if request.url.path == "/api/health":
                    return httpx.Response(200, json={"status": "ok"})

                self.assertEqual(request.url.path, "/api/issues/9/move")
                self.assertEqual(request.method, "POST")
                return httpx.Response(
                    200,
                    json={
                        "status": "ok",
                        "issue_id": 9,
                        "workflow_state": "IN_PROGRESS",
                        "board_position": 2,
                    },
                )

            sdk = make_async_client(handler)
            health = await sdk.system.health()
            self.assertEqual(health.status, "ok")
            result = await sdk.issues.move(9, target_state="IN_PROGRESS", position_index=2)
            self.assertEqual(result.workflow_state, "IN_PROGRESS")
            await sdk.aclose()

        asyncio.run(runner())

    def test_sync_resource_wrappers_cover_remaining_public_contracts(self):
        def handler(request):
            match (request.method, request.url.path):
                case ("GET", "/api/health"):
                    return httpx.Response(200, json={"status": "ok"})
                case ("GET", "/api/profile/me"):
                    return httpx.Response(200, json=make_profile())
                case ("GET", "/api/users/demo/profile"):
                    return httpx.Response(200, json=make_profile(username="demo"))
                case ("PUT", "/api/profile/me"):
                    self.assertEqual(
                        request.content.decode(),
                        "language_preference=en&avatar_type=image&is_system_user=false&group_ids=3&group_ids=5",
                    )
                    return httpx.Response(200, json={"status": "updated", "profile": make_profile()})
                case ("GET", "/api/board"):
                    self.assertEqual(request.url.params["group_id"], "3")
                    self.assertEqual(request.url.params["search"], "router")
                    return httpx.Response(
                        200,
                        json={
                            "search_query": "router",
                            "selected_assignee": "",
                            "selected_priority": "",
                            "selected_collection": "",
                            "selected_category": "",
                            "selected_group": "3",
                            "selected_is_escalated": None,
                            "selected_updated_within_seconds": None,
                            "assignee_options": [make_user_summary()],
                            "priority_options": [{"value": "HIGH", "label": "High"}],
                            "collection_options": [make_collection()],
                            "category_options": [make_category()],
                            "board_columns": [
                                {
                                    "value": "NEW",
                                    "label": "New",
                                    "is_open": True,
                                    "issue_count": 1,
                                    "issues": [make_issue_summary(group=make_group(), user=make_user_summary())],
                                }
                            ],
                            "board_issue_count": 1,
                        },
                    )
                case ("GET", "/api/dashboard"):
                    return httpx.Response(
                        200,
                        json={
                            "assigned_issues": [make_issue_summary(user=make_user_summary())],
                            "mentioned_comments": [
                                {
                                    "id": 6,
                                    "issue": make_issue_summary(issue_id=6),
                                    "body": "Ping @demo",
                                    "visibility": "INTERNAL",
                                    "visibility_label": "Internal",
                                    "created_at": "2026-06-13T10:08:00+00:00",
                                    "author_user": make_user_summary(
                                        user_id=9, username="lead", display_name="Team Lead"
                                    ),
                                }
                            ],
                        },
                    )
                case ("GET", "/api/groups"):
                    return httpx.Response(200, json={"data": [make_group()]})
                case ("GET", "/api/users"):
                    self.assertEqual(request.url.params["group_id"], "3")
                    return httpx.Response(200, json={"data": [make_user_summary()]})
                case ("GET", "/api/collections"):
                    return httpx.Response(200, json={"data": [make_collection()]})
                case ("GET", "/api/categories"):
                    return httpx.Response(200, json={"data": [make_category()]})
                case ("POST", "/api/collections"):
                    self.assertEqual(json.loads(request.content.decode()), {"name": "Services", "prefix": "SRV"})
                    return httpx.Response(
                        201, json={"status": "created", "collection": make_collection(collection_id=9, name="Services")}
                    )
                case ("PUT", "/api/collections/9"):
                    self.assertEqual(json.loads(request.content.decode()), {"description": "Updated collection"})
                    return httpx.Response(
                        200, json={"status": "updated", "collection": make_collection(collection_id=9, name="Services")}
                    )
                case ("POST", "/api/categories"):
                    self.assertEqual(json.loads(request.content.decode()), {"name": "Incidents", "code": "INC"})
                    return httpx.Response(
                        201,
                        json={
                            "status": "created",
                            "category": make_category(category_id=7, name="Incidents", code="INC"),
                        },
                    )
                case ("PUT", "/api/categories/7"):
                    self.assertEqual(json.loads(request.content.decode()), {"description": "Updated category"})
                    return httpx.Response(
                        200,
                        json={
                            "status": "updated",
                            "category": make_category(category_id=7, name="Incidents", code="INC"),
                        },
                    )
                case ("GET", "/api/issues/11"):
                    return httpx.Response(200, json=make_issue_detail(issue_id=11))
                case ("POST", "/api/issues/11/archive"):
                    self.assertEqual(json.loads(request.content.decode()), {"confirm_archive": False})
                    return httpx.Response(
                        200, json={"status": "archived", "issue_id": 11, "archived_at": "2026-06-13T10:10:00+00:00"}
                    )
                case ("PUT", "/api/issues/11/attachments/7"):
                    self.assertEqual(request.content.decode(), "description=Updated+trace")
                    return httpx.Response(200, json={"status": "updated", "attachment": make_attachment()})
                case ("DELETE", "/api/issues/11/attachments/7"):
                    return httpx.Response(200, json={"status": "deleted", "attachment_id": 7})
                case ("GET", "/api/users/8"):
                    return httpx.Response(200, json=make_managed_user())
                case ("PUT", "/api/users/8"):
                    self.assertEqual(json.loads(request.content.decode()), {"display_name": "Updated Coordinator"})
                    return httpx.Response(200, json={"status": "updated", "user": make_managed_user()})
                case ("DELETE", "/api/users/8"):
                    return httpx.Response(200, json={"status": "deactivated", "user_id": 8, "is_active": False})
                case ("POST", "/api/groups"):
                    self.assertEqual(json.loads(request.content.decode()), {"name": "Escalation Desk", "user_ids": [8]})
                    return httpx.Response(
                        201, json={"status": "created", "group": make_managed_group(name="Escalation Desk")}
                    )
                case ("GET", "/api/groups/3"):
                    return httpx.Response(200, json=make_managed_group())
                case ("DELETE", "/api/groups/3"):
                    return httpx.Response(200, json={"status": "deleted", "group_id": 3})
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        with make_sync_client(handler) as sdk:
            self.assertEqual(sdk.system.health().status, "ok")
            self.assertEqual(sdk.profiles.me().user.username, "demo")
            self.assertTrue(sdk.profiles.get("demo").can_edit)
            updated_profile = sdk.profiles.update(
                language_preference="en",
                avatar_type="image",
                is_system_user=False,
                group_ids=[3, 5],
                ignored=None,
            )
            self.assertEqual(updated_profile.status, "updated")
            board = sdk.board.get(group_id=3, search="router", ignored="")
            self.assertEqual(board.board_columns[0].issues[0].issue_number, "TASK-5")
            dashboard = sdk.dashboard.get()
            self.assertEqual(dashboard.mentioned_comments[0].issue.issue_number, "TASK-6")
            self.assertEqual(sdk.reference.list_groups()[0].name, "Network Operations")
            self.assertEqual(sdk.reference.list_users(group_id=3)[0].username, "demo")
            self.assertEqual(sdk.reference.list_collections()[0].name, "Tasks")
            self.assertEqual(sdk.reference.list_categories()[0].code, "NETWORK")
            self.assertEqual(sdk.reference.create_collection(name="Services", prefix="SRV").collection.id, 9)
            self.assertEqual(sdk.reference.update_collection(9, description="Updated collection").collection.id, 9)
            self.assertEqual(sdk.reference.create_category(name="Incidents", code="INC").category.id, 7)
            self.assertEqual(sdk.reference.update_category(7, description="Updated category").category.id, 7)
            self.assertEqual(sdk.issues.get(11).issue_number, "TASK-11")
            self.assertEqual(sdk.issues.archive(11, confirm_archive=False).status, "archived")
            self.assertEqual(sdk.attachments.update(11, 7, description="Updated trace").attachment.id, 7)
            self.assertEqual(sdk.attachments.delete(11, 7)["status"], "deleted")
            self.assertEqual(sdk.admin.users.get(8).username, "coordinator")
            self.assertEqual(sdk.admin.users.update(8, display_name="Updated Coordinator").status, "updated")
            self.assertFalse(sdk.admin.users.deactivate(8).is_active)
            self.assertEqual(
                sdk.admin.groups.create(name="Escalation Desk", user_ids=[8]).group.name, "Escalation Desk"
            )
            self.assertEqual(sdk.admin.groups.get(3).users[0].username, "coordinator")
            self.assertEqual(sdk.admin.groups.delete(3).group_id, 3)

    def test_async_client_surface_covers_remaining_async_wrappers(self):
        async def runner():
            def handler(request):
                match (request.method, request.url.path):
                    case ("GET", "/api/auth/me"):
                        return httpx.Response(
                            200,
                            json={
                                "id": 1,
                                "username": "demo",
                                "display_name": "Demo User",
                                "is_staff": False,
                                "is_superuser": False,
                            },
                        )
                    case ("GET", "/api/profile/me"):
                        return httpx.Response(200, json=make_profile())
                    case ("PUT", "/api/profile/me"):
                        self.assertEqual(request.content.decode(), "avatar_type=initials")
                        return httpx.Response(200, json={"status": "updated", "profile": make_profile()})
                    case ("GET", "/api/board"):
                        return httpx.Response(
                            200,
                            json={
                                "search_query": "",
                                "selected_assignee": "",
                                "selected_priority": "HIGH",
                                "selected_collection": "",
                                "selected_category": "",
                                "selected_group": None,
                                "selected_is_escalated": "true",
                                "selected_updated_within_seconds": "3600",
                                "assignee_options": [make_user_summary()],
                                "priority_options": [{"value": "HIGH", "label": "High"}],
                                "collection_options": [make_collection()],
                                "category_options": [make_category()],
                                "board_columns": [],
                                "board_issue_count": 0,
                            },
                        )
                    case ("GET", "/api/dashboard"):
                        return httpx.Response(200, json={"assigned_issues": [], "mentioned_comments": []})
                    case ("GET", "/api/groups"):
                        return httpx.Response(200, json={"data": [make_group()]})
                    case ("GET", "/api/users"):
                        return httpx.Response(200, json={"data": [make_user_summary()]})
                    case ("GET", "/api/collections"):
                        return httpx.Response(200, json={"data": [make_collection()]})
                    case ("GET", "/api/categories"):
                        return httpx.Response(200, json={"data": [make_category()]})
                    case ("POST", "/api/collections"):
                        return httpx.Response(
                            201,
                            json={"status": "created", "collection": make_collection(collection_id=12, name="Backlog")},
                        )
                    case ("PUT", "/api/collections/12"):
                        return httpx.Response(
                            200,
                            json={"status": "updated", "collection": make_collection(collection_id=12, name="Backlog")},
                        )
                    case ("POST", "/api/categories"):
                        return httpx.Response(
                            201,
                            json={
                                "status": "created",
                                "category": make_category(category_id=13, name="Change", code="CHG"),
                            },
                        )
                    case ("PUT", "/api/categories/13"):
                        return httpx.Response(
                            200,
                            json={
                                "status": "updated",
                                "category": make_category(category_id=13, name="Change", code="CHG"),
                            },
                        )
                    case ("GET", "/api/issues"):
                        return httpx.Response(200, json={"data": [make_issue_summary(user=make_user_summary())]})
                    case ("GET", "/api/issues/5"):
                        return httpx.Response(200, json=make_issue_detail())
                    case ("POST", "/api/issues"):
                        return httpx.Response(201, json={"status": "created", "issue": make_issue_detail()})
                    case ("PUT", "/api/issues/5"):
                        return httpx.Response(
                            200, json={"status": "updated", "issue": make_issue_detail(workflow_state="IN_PROGRESS")}
                        )
                    case ("POST", "/api/issues/5/archive"):
                        return httpx.Response(
                            200, json={"status": "archived", "issue_id": 5, "archived_at": "2026-06-13T10:10:00+00:00"}
                        )
                    case ("POST", "/api/issues/5/comments"):
                        return httpx.Response(201, json={"status": "comment-added", "issue": make_issue_detail()})
                    case ("PUT", "/api/issues/5/comments/4"):
                        return httpx.Response(200, json={"status": "updated", "comment": make_comment()})
                    case ("POST", "/api/issues/5/attachments"):
                        return httpx.Response(201, json={"status": "created", "attachment": make_attachment()})
                    case ("PUT", "/api/issues/5/attachments/7"):
                        return httpx.Response(200, json={"status": "updated", "attachment": make_attachment()})
                    case ("DELETE", "/api/issues/5/attachments/7"):
                        return httpx.Response(200, json={"status": "deleted", "attachment_id": 7})
                    case ("GET", "/api/issues/5/attachments/7/download"):
                        return httpx.Response(200, content=b"trace")
                    case ("POST", "/api/users"):
                        return httpx.Response(201, json={"status": "created", "user": make_managed_user()})
                    case ("GET", "/api/users/8"):
                        return httpx.Response(200, json=make_managed_user())
                    case ("PUT", "/api/users/8"):
                        return httpx.Response(200, json={"status": "updated", "user": make_managed_user()})
                    case ("DELETE", "/api/users/8"):
                        return httpx.Response(200, json={"status": "deactivated", "user_id": 8, "is_active": False})
                    case ("POST", "/api/groups"):
                        return httpx.Response(201, json={"status": "created", "group": make_managed_group()})
                    case ("GET", "/api/groups/3"):
                        return httpx.Response(200, json=make_managed_group())
                    case ("PUT", "/api/groups/3"):
                        return httpx.Response(
                            200, json={"status": "updated", "group": make_managed_group(name="Escalation Desk")}
                        )
                    case ("DELETE", "/api/groups/3"):
                        return httpx.Response(200, json={"status": "deleted", "group_id": 3})
                    case ("GET", "/api/workflow-state-auto-assignment-rules"):
                        return httpx.Response(200, json={"data": [make_workflow_state_auto_assignment_rule()]})
                    case ("POST", "/api/workflow-state-auto-assignment-rules"):
                        return httpx.Response(
                            201, json={"status": "created", "rule": make_workflow_state_auto_assignment_rule()}
                        )
                    case ("GET", "/api/workflow-state-auto-assignment-rules/2"):
                        return httpx.Response(200, json=make_workflow_state_auto_assignment_rule())
                    case ("PUT", "/api/workflow-state-auto-assignment-rules/2"):
                        return httpx.Response(
                            200,
                            json={
                                "status": "updated",
                                "rule": make_workflow_state_auto_assignment_rule(
                                    workflow_state="WAITING", is_active=False
                                ),
                            },
                        )
                    case ("DELETE", "/api/workflow-state-auto-assignment-rules/2"):
                        return httpx.Response(200, json={"status": "deleted", "rule_id": 2})
                    case ("POST", "/api/instance-reset"):
                        return httpx.Response(
                            200,
                            json={
                                "status": "reset",
                                "preserved_user_id": 1,
                                "deleted_counts": {"issues": 4, "users": 2},
                            },
                        )
                raise AssertionError(f"Unexpected async request: {request.method} {request.url}")

            async with make_async_client(handler) as sdk:
                self.assertEqual((await sdk.auth.me()).username, "demo")
                self.assertEqual((await sdk.profiles.me()).user.username, "demo")
                self.assertEqual((await sdk.profiles.update(avatar_type="initials")).status, "updated")
                self.assertEqual((await sdk.board.get(priority="HIGH")).selected_priority, "HIGH")
                self.assertEqual(len((await sdk.dashboard.get()).assigned_issues), 0)
                self.assertEqual((await sdk.reference.list_groups())[0].id, 3)
                self.assertEqual((await sdk.reference.list_users())[0].username, "demo")
                self.assertEqual((await sdk.reference.list_collections())[0].prefix, "TASK")
                self.assertEqual((await sdk.reference.list_categories())[0].code, "NETWORK")
                self.assertEqual((await sdk.reference.create_collection(name="Backlog")).collection.id, 12)
                self.assertEqual((await sdk.reference.update_collection(12, description="Later")).collection.id, 12)
                self.assertEqual((await sdk.reference.create_category(name="Change", code="CHG")).category.id, 13)
                self.assertEqual((await sdk.reference.update_category(13, description="Later")).category.id, 13)
                self.assertEqual((await sdk.issues.list())[0].issue_number, "TASK-5")
                self.assertEqual((await sdk.issues.get(5)).issue_number, "TASK-5")
                self.assertEqual(
                    (await sdk.issues.create(title="Router outage", collection=1, category=2)).status, "created"
                )
                self.assertEqual(
                    (await sdk.issues.update(5, workflow_state="IN_PROGRESS")).issue.workflow_state, "IN_PROGRESS"
                )
                self.assertEqual((await sdk.issues.archive(5)).issue_id, 5)
                self.assertEqual((await sdk.comments.add(5, body="async comment")).status, "comment-added")
                self.assertEqual((await sdk.comments.update(5, 4, body="updated body")).comment.id, 4)
                self.assertEqual((await sdk.attachments.add(5, description="trace")).attachment.id, 7)
                self.assertEqual((await sdk.attachments.update(5, 7, description="trace")).attachment.id, 7)
                self.assertEqual((await sdk.attachments.delete(5, 7))["attachment_id"], 7)
                self.assertEqual(await sdk.attachments.download(5, 7), b"trace")
                self.assertEqual((await sdk.admin.users.create(username="coordinator")).user.id, 8)
                self.assertEqual((await sdk.admin.users.get(8)).username, "coordinator")
                self.assertEqual((await sdk.admin.users.update(8, display_name="Case Coordinator")).status, "updated")
                self.assertFalse((await sdk.admin.users.deactivate(8)).is_active)
                self.assertEqual((await sdk.admin.groups.create(name="Escalation Desk")).group.id, 3)
                self.assertEqual((await sdk.admin.groups.get(3)).users[0].username, "coordinator")
                self.assertEqual(
                    (await sdk.admin.groups.update(3, name="Escalation Desk")).group.name, "Escalation Desk"
                )
                self.assertEqual((await sdk.admin.groups.delete(3)).group_id, 3)
                self.assertEqual(
                    (await sdk.admin.workflow_state_auto_assignment_rules.list())[0].workflow_state, "ASSIGNED"
                )
                self.assertEqual(
                    (
                        await sdk.admin.workflow_state_auto_assignment_rules.create(workflow_state="ASSIGNED", group=3)
                    ).rule.id,
                    2,
                )
                self.assertEqual((await sdk.admin.workflow_state_auto_assignment_rules.get(2)).group.id, 3)
                self.assertEqual(
                    (
                        await sdk.admin.workflow_state_auto_assignment_rules.update(
                            2, workflow_state="WAITING", group=3
                        )
                    ).rule.workflow_state,
                    "WAITING",
                )
                self.assertEqual((await sdk.admin.workflow_state_auto_assignment_rules.delete(2)).rule_id, 2)
                self.assertEqual((await sdk.admin.reset_instance(confirm_reset=True)).deleted_counts["issues"], 4)

        asyncio.run(runner())

    def test_transport_helpers_and_model_conversion_cover_remaining_branches(self):
        self.assertEqual(normalize_base_url(" http://example.test/ "), "http://example.test")

        with self.assertRaisesRegex(ValueError, "base_url is required"):
            normalize_base_url("   ")

        with self.assertRaisesRegex(ValueError, "absolute http or https URL"):
            normalize_base_url("/relative/path")

        response = httpx.Response(
            401, json={"error": "Bad credentials"}, request=httpx.Request("GET", "http://example.test/api/auth/me")
        )
        with self.assertRaises(AuthenticationError) as auth_error:
            make_sync_client(lambda request: response).auth.me()
        self.assertEqual(auth_error.exception.status_code, 401)

        text_response = httpx.Response(
            500, text="boom", request=httpx.Request("GET", "http://example.test/api/issues/5")
        )
        with self.assertRaises(ApiError) as api_error:
            make_sync_client(lambda request: text_response).issues.get(5)
        self.assertEqual(str(api_error.exception), "Ticket System Mock API request GET /api/issues/5 failed.")
        self.assertEqual(api_error.exception.payload, "boom")

        model = ExampleContainerModel.from_dict({
            "nested": {"value": "nested"},
            "values": [1, 2, 3],
            "metadata": {"env": "test"},
        })
        self.assertEqual(model.nested.value, "nested")
        self.assertEqual(model.values, [1, 2, 3])
        self.assertEqual(model.metadata, {"env": "test"})
        self.assertEqual(_convert_value(int | str, 7), 7)

    def test_sync_client_passes_ssl_verify_to_httpx_client(self):
        with patch("ticketsystemmock.transport.httpx.Client") as client_factory:
            TicketSystemClient("https://example.test", "demo", "password", ssl_verify=False)

        client_factory.assert_called_once_with(
            base_url="https://example.test",
            auth=("demo", "password"),
            timeout=10.0,
            verify=False,
        )

    def test_async_client_passes_ssl_verify_to_httpx_client(self):
        with patch("ticketsystemmock.transport.httpx.AsyncClient") as client_factory:
            AsyncTicketSystemClient("https://example.test", "demo", "password", ssl_verify=False)

        client_factory.assert_called_once_with(
            base_url="https://example.test",
            auth=("demo", "password"),
            timeout=10.0,
            verify=False,
        )

    def test_package_exports_match_expected_public_surface(self):
        self.assertIn("AsyncAdminResource", resource_exports)
        self.assertIn("SyncIssuesResource", resource_exports)
