import base64
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.http.multipartparser import MultiPartParserError
from django.test import RequestFactory, TestCase
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.utils import timezone

from djangoapp.core.controllers import GroupController, UserController
from djangoapp.core.models import (
    Collection,
    Issue,
    IssueCategory,
    IssueComment,
    IssueHistoryEvent,
    IssuePriority,
    IssueStateTransition,
    WorkflowState,
    WorkflowStateAutoAssignmentRule,
)
from djangoapp.rest_api.api import (
    DjangoBasicAuth,
    _move_payload,
    _request_form_payload,
    _request_payload,
    _serialize_optional_datetime,
    _serialize_optional_relation,
    current_user,
    health,
)
from djangoapp.rest_api.forms import GroupManagementForm, UserManagementForm


class RestApiTests(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username="demo",
            password="demo-password-123",
            first_name="Demo",
            last_name="User",
        )
        self.support_group = Group.objects.create(name="Network Operations")
        self.support_group.user_set.add(self.user)
        self.observer = get_user_model().objects.create_user(
            username="observer",
            password="demo-password-123",
            first_name="Olivia",
            last_name="Observer",
        )
        self.support_group.user_set.add(self.observer)
        self.collection = Collection.objects.get(prefix="TASK")
        self.category = IssueCategory.objects.create(name="Network", code="NETWORK")

    def multipart_put(self, path, data):
        return self.client.put(
            path,
            data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
            headers=self.basic_auth_header(),
        )

    def basic_auth_header(self, username="demo", password="demo-password-123"):
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    def admin_auth_header(self):
        if not hasattr(self, "admin_user"):
            self.admin_user = get_user_model().objects.create_superuser(
                username="admin",
                password="admin-password-123",
                email="admin@example.com",
            )
        return self.basic_auth_header(username="admin", password="admin-password-123")

    def test_api_requires_http_basic_auth(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 401)

    def test_api_rejects_invalid_http_basic_auth_credentials(self):
        response = self.client.get(
            "/api/health",
            headers=self.basic_auth_header(password="wrong-password"),
        )

        self.assertEqual(response.status_code, 401)

    def test_api_health_returns_ok_with_http_basic_auth(self):
        response = self.client.get(
            "/api/health",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_api_accepts_http_basic_auth(self):
        response = self.client.get(
            "/api/auth/me",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "demo")

    def test_openapi_schema_documents_endpoint_purpose_and_payload_shapes(self):
        response = self.client.get(
            "/api/openapi.json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)

        schema = response.json()
        self.assertEqual(
            schema["info"]["description"],
            "Machine-facing REST API for reading issue data, reference data, dashboard projections, "
            "and issue workflow mutations in Ticket System Mock.",
        )
        self.assertEqual(schema["paths"]["/api/health"]["get"]["summary"], "Check API health")
        self.assertEqual(schema["paths"]["/api/auth/me"]["get"]["tags"], ["Authentication"])
        self.assertEqual(schema["paths"]["/api/profile/me"]["get"]["tags"], ["Profiles"])
        self.assertEqual(
            schema["paths"]["/api/board"]["get"]["parameters"][0]["description"],
            "Free-text filter applied to issue number, title, and description content.",
        )
        board_parameters = {
            parameter["name"]: parameter for parameter in schema["paths"]["/api/board"]["get"]["parameters"]
        }
        issue_list_parameters = {
            parameter["name"]: parameter for parameter in schema["paths"]["/api/issues"]["get"]["parameters"]
        }
        self.assertEqual(
            board_parameters["group"]["description"],
            "Optional group identifier used to limit the board projection.",
        )
        self.assertEqual(
            board_parameters["updated_within_seconds"]["description"],
            "Optional relative time window used to limit board issues to entries updated within the last X seconds.",
        )
        self.assertEqual(
            issue_list_parameters["updated_within_seconds"]["description"],
            "Optional relative time window used to limit returned issues to entries updated within the last X seconds.",
        )
        self.assertEqual(
            schema["paths"]["/api/issues"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/IssueListResponseSchema",
        )
        self.assertEqual(
            schema["paths"]["/api/issues"]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"][
                "required"
            ],
            ["title", "collection", "category", "priority"],
        )
        self.assertEqual(
            schema["paths"]["/api/issues/{issue_id}/move"]["post"]["requestBody"]["content"]["application/json"][
                "schema"
            ]["properties"]["target_state"]["enum"],
            [
                "NEW",
                "TRIAGE",
                "ASSIGNED",
                "IN_PROGRESS",
                "WAITING",
                "RESOLVED",
                "CLOSED",
                "REJECTED",
            ],
        )
        self.assertEqual(
            schema["components"]["schemas"]["IssueDetailSchema"]["properties"]["attachments"]["description"],
            "Attachments currently associated with the issue.",
        )
        self.assertEqual(
            schema["components"]["schemas"]["IssueListResponseSchema"]["properties"]["data"]["description"],
            "Issues that match the supplied board-style filters.",
        )
        self.assertEqual(
            schema["components"]["schemas"]["AuthenticatedUserSchema"]["properties"]["display_name"]["description"],
            "Preferred display name shown for the authenticated user.",
        )
        self.assertEqual(
            schema["components"]["schemas"]["UserProfileSchema"]["properties"]["is_system_user"]["description"],
            "Whether the profile is flagged as a system user.",
        )
        self.assertEqual(schema["paths"]["/api/users"]["post"]["tags"], ["Administration"])
        self.assertEqual(schema["paths"]["/api/groups/{group_id}"]["get"]["tags"], ["Administration"])
        self.assertEqual(schema["paths"]["/api/users/{user_id}"]["delete"]["summary"], "Deactivate user")
        self.assertEqual(
            schema["components"]["schemas"]["ManagedUserSchema"]["properties"]["groups"]["description"],
            "Groups that currently include the managed user.",
        )
        self.assertEqual(
            schema["components"]["schemas"]["UserProfileSchema"]["properties"]["avatar_type"]["description"],
            "Stored avatar type for the profile.",
        )
        self.assertEqual(
            schema["paths"]["/api/profile/me"]["put"]["requestBody"]["content"]["multipart/form-data"]["schema"][
                "properties"
            ]["language_preference"]["enum"],
            ["en", "de"],
        )

    def test_basic_auth_backend_returns_active_user(self):
        backend = DjangoBasicAuth()

        with patch("djangoapp.rest_api.api.authenticate", return_value=self.user):
            authenticated = backend.authenticate(
                request=None,
                username="demo",
                password="demo-password-123",
            )

        self.assertEqual(authenticated, self.user)

    def test_basic_auth_backend_rejects_inactive_or_missing_user(self):
        backend = DjangoBasicAuth()

        with patch("djangoapp.rest_api.api.authenticate", return_value=None):
            authenticated = backend.authenticate(
                request=None,
                username="demo",
                password="wrong-password",
            )

        self.assertIsNone(authenticated)

    def test_health_endpoint_returns_ok_payload(self):
        self.assertEqual(health(request=None), {"status": "ok"})

    def test_current_user_endpoint_serializes_authenticated_user(self):
        request = SimpleNamespace(auth=self.user)

        payload = current_user(request)

        self.assertEqual(payload["id"], self.user.pk)
        self.assertEqual(payload["username"], "demo")
        self.assertEqual(payload["display_name"], "Demo User")
        self.assertFalse(payload["is_staff"])
        self.assertFalse(payload["is_superuser"])

    def test_request_payload_rejects_invalid_json_and_non_object_json(self):
        invalid_request = self.request_factory.post(
            "/api/issues",
            data="{invalid",
            content_type="application/json",
        )
        list_request = self.request_factory.post(
            "/api/issues",
            data=json.dumps(["invalid"]),
            content_type="application/json",
        )

        invalid_payload, invalid_error = _request_payload(invalid_request)
        list_payload, list_error = _request_payload(list_request)

        self.assertIsNone(invalid_payload)
        self.assertEqual(invalid_error, (400, {"error": "Invalid request payload."}))
        self.assertIsNone(list_payload)
        self.assertEqual(list_error, (400, {"error": "Invalid request payload."}))

    def test_request_payload_supports_urlencoded_forms_and_invalid_multipart(self):
        urlencoded_request = self.request_factory.put(
            "/api/issues/1",
            data="priority=HIGH&workflow_state=NEW",
            content_type="application/x-www-form-urlencoded",
        )
        multipart_request = self.request_factory.put(
            "/api/issues/1",
            data=b"--invalid",
            content_type="multipart/form-data; boundary=invalid",
        )

        payload, error = _request_payload(urlencoded_request)

        self.assertEqual(payload, {"priority": "HIGH", "workflow_state": "NEW"})
        self.assertIsNone(error)

        with patch("djangoapp.rest_api.api.MultiPartParser.parse", side_effect=MultiPartParserError("bad multipart")):
            multipart_payload, multipart_files, multipart_error = _request_form_payload(multipart_request)

        self.assertIsNone(multipart_payload)
        self.assertIsNone(multipart_files)
        self.assertEqual(multipart_error, (400, {"error": "Invalid request payload."}))

    def test_request_form_payload_supports_fallback_post_data_for_other_content_types(self):
        request = SimpleNamespace(
            method="PUT",
            content_type="text/plain",
            POST=QueryDict("priority=HIGH&workflow_state=NEW"),
            FILES=None,
        )

        payload, files, error = _request_form_payload(request)

        self.assertEqual(payload, {"priority": "HIGH", "workflow_state": "NEW"})
        self.assertIsNone(files)
        self.assertIsNone(error)

    def test_serialize_optional_helpers_cover_values_and_none(self):
        now = timezone.now()

        self.assertEqual(_serialize_optional_datetime(now), now.isoformat())
        self.assertIsNone(_serialize_optional_relation(None, lambda value: value))
        self.assertEqual(
            _serialize_optional_relation(self.support_group, lambda group: group.name),
            self.support_group.name,
        )

    def test_reference_endpoints_return_metadata(self):
        response = self.client.get("/api/collections", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["prefix"], "TASK")

        response = self.client.get("/api/categories", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["code"], "NETWORK")

        response = self.client.get("/api/groups", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["name"], "Network Operations")

        response = self.client.get(
            "/api/users",
            {"group_id": self.support_group.pk},
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["username"], "demo")
        self.assertEqual(response.json()["data"][0]["avatar_type"], "initials")
        self.assertFalse(response.json()["data"][0]["is_system_user"])
        self.assertEqual(response.json()["data"][0]["avatar_text"], "DU")

        response = self.client.get("/api/users", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 2)

    def test_profile_endpoints_return_and_update_user_settings(self):
        profile_response = self.client.get("/api/profile/me", headers=self.basic_auth_header())

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["user"]["username"], "demo")
        self.assertTrue(profile_response.json()["can_edit"])

        update_response = self.multipart_put(
            "/api/profile/me",
            {
                "language_preference": "de",
                "avatar_type": "image",
                "is_system_user": "true",
            },
        )

        self.user.profile.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["profile"]["language_preference"], "de")
        self.assertEqual(update_response.json()["profile"]["avatar_type"], "image")
        self.assertTrue(update_response.json()["profile"]["is_system_user"])
        self.assertTrue(self.user.profile.is_system_user)
        self.assertEqual(self.user.profile.avatar_type, "image")
        self.assertTrue(
            update_response.json()["profile"]["avatar_image_url"].endswith("/static/img/default_avatar_agent.png")
        )

    def test_public_user_profile_endpoint_returns_public_profile_payload(self):
        response = self.client.get(f"/api/users/{self.observer.username}/profile", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.observer.username)
        self.assertFalse(response.json()["can_edit"])

    def test_collection_endpoints_support_create_and_update(self):
        create_response = self.client.post(
            "/api/collections",
            data=json.dumps({
                "name": "Incident",
                "prefix": "INC",
                "description": "Incident queue",
                "is_active": True,
                "next_issue_sequence": 4,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(create_response.status_code, 201)
        created_collection = Collection.objects.get(prefix="INC")
        self.assertEqual(create_response.json()["collection"]["prefix"], "INC")

        update_response = self.client.put(
            f"/api/collections/{created_collection.pk}",
            data=json.dumps({
                "name": "Incident Response",
                "prefix": "INC",
                "description": "Updated incident queue",
                "is_active": False,
                "next_issue_sequence": 7,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        created_collection.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(created_collection.name, "Incident Response")
        self.assertFalse(created_collection.is_active)
        self.assertEqual(created_collection.next_issue_sequence, 7)

    def test_collection_endpoints_reject_duplicate_names(self):
        existing_collection = Collection.objects.create(name="Incident", prefix="INC")

        create_response = self.client.post(
            "/api/collections",
            data=json.dumps({
                "name": existing_collection.name,
                "prefix": "OPS",
                "description": "Operations queue",
                "is_active": True,
                "next_issue_sequence": 1,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        update_response = self.client.put(
            f"/api/collections/{self.collection.pk}",
            data=json.dumps({
                "name": existing_collection.name,
                "prefix": self.collection.prefix,
                "description": self.collection.description,
                "is_active": self.collection.is_active,
                "next_issue_sequence": self.collection.next_issue_sequence,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(create_response.status_code, 400)
        self.assertIn("name", create_response.json()["errors"])
        self.assertEqual(update_response.status_code, 400)
        self.assertIn("name", update_response.json()["errors"])

    def test_category_endpoints_support_create_and_update(self):
        create_response = self.client.post(
            "/api/categories",
            data=json.dumps({
                "name": "Security",
                "code": "SECURITY",
                "description": "Security issues",
                "is_active": True,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(create_response.status_code, 201)
        created_category = IssueCategory.objects.get(code="SECURITY")
        self.assertEqual(create_response.json()["category"]["code"], "SECURITY")

        update_response = self.client.put(
            f"/api/categories/{created_category.pk}",
            data=json.dumps({
                "name": "Security Operations",
                "code": "SECURITY",
                "description": "Updated security issues",
                "is_active": False,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        created_category.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(created_category.name, "Security Operations")
        self.assertFalse(created_category.is_active)

    def test_category_endpoints_reject_duplicate_names(self):
        existing_category = IssueCategory.objects.create(name="Security", code="SEC")

        create_response = self.client.post(
            "/api/categories",
            data=json.dumps({
                "name": existing_category.name,
                "code": "OPS",
                "description": "Operations issues",
                "is_active": True,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        update_response = self.client.put(
            f"/api/categories/{self.category.pk}",
            data=json.dumps({
                "name": existing_category.name,
                "code": self.category.code,
                "description": self.category.description,
                "is_active": self.category.is_active,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(create_response.status_code, 400)
        self.assertIn("name", create_response.json()["errors"])
        self.assertEqual(update_response.status_code, 400)
        self.assertIn("name", update_response.json()["errors"])

    def test_collection_and_category_endpoints_surface_invalid_payloads_and_form_errors(self):
        collection = Collection.objects.get(prefix="TASK")

        create_collection_invalid_json = self.client.post(
            "/api/collections",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        create_collection_invalid_form = self.client.post(
            "/api/collections",
            data=json.dumps({"name": "Incident"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        update_collection_invalid_json = self.client.put(
            f"/api/collections/{collection.pk}",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        update_collection_invalid_form = self.client.put(
            f"/api/collections/{collection.pk}",
            data=json.dumps({"name": "Task", "prefix": "", "description": "", "is_active": True}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        create_category_invalid_json = self.client.post(
            "/api/categories",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        create_category_invalid_form = self.client.post(
            "/api/categories",
            data=json.dumps({"name": "Security"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        update_category_invalid_json = self.client.put(
            f"/api/categories/{self.category.pk}",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        update_category_invalid_form = self.client.put(
            f"/api/categories/{self.category.pk}",
            data=json.dumps({"name": "Network", "code": "", "description": "", "is_active": True}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(create_collection_invalid_json.status_code, 400)
        self.assertEqual(create_collection_invalid_json.json()["error"], "Invalid request payload.")
        self.assertEqual(create_collection_invalid_form.status_code, 400)
        self.assertIn("prefix", create_collection_invalid_form.json()["errors"])
        self.assertEqual(update_collection_invalid_json.status_code, 400)
        self.assertEqual(update_collection_invalid_json.json()["error"], "Invalid request payload.")
        self.assertEqual(update_collection_invalid_form.status_code, 400)
        self.assertIn("prefix", update_collection_invalid_form.json()["errors"])

        self.assertEqual(create_category_invalid_json.status_code, 400)
        self.assertEqual(create_category_invalid_json.json()["error"], "Invalid request payload.")
        self.assertEqual(create_category_invalid_form.status_code, 400)
        self.assertIn("code", create_category_invalid_form.json()["errors"])
        self.assertEqual(update_category_invalid_json.status_code, 400)
        self.assertEqual(update_category_invalid_json.json()["error"], "Invalid request payload.")
        self.assertEqual(update_category_invalid_form.status_code, 400)
        self.assertIn("code", update_category_invalid_form.json()["errors"])

    def test_admin_user_and_group_endpoints_surface_invalid_payloads_and_form_errors(self):
        invalid_user_payload = self.client.post(
            "/api/users",
            data="{invalid",
            content_type="application/json",
            headers=self.admin_auth_header(),
        )
        invalid_user_form = self.client.post(
            "/api/users",
            data=json.dumps({"username": self.user.username, "password": ""}),
            content_type="application/json",
            headers=self.admin_auth_header(),
        )
        invalid_group_payload = self.client.post(
            "/api/groups",
            data="{invalid",
            content_type="application/json",
            headers=self.admin_auth_header(),
        )
        invalid_group_form = self.client.post(
            "/api/groups",
            data=json.dumps({"name": self.support_group.name}),
            content_type="application/json",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(invalid_user_payload.status_code, 400)
        self.assertEqual(invalid_user_payload.json()["error"], "Invalid request payload.")
        self.assertEqual(invalid_user_form.status_code, 400)
        self.assertIn("username", invalid_user_form.json()["errors"])
        self.assertIn("password", invalid_user_form.json()["errors"])

        self.assertEqual(invalid_group_payload.status_code, 400)
        self.assertEqual(invalid_group_payload.json()["error"], "Invalid request payload.")
        self.assertEqual(invalid_group_form.status_code, 400)
        self.assertIn("name", invalid_group_form.json()["errors"])

    def test_user_and_group_management_forms_and_controllers_cover_optional_paths(self):
        duplicate_user_form = UserManagementForm({"username": self.user.username})
        self.assertFalse(duplicate_user_form.is_valid())
        self.assertIn("username", duplicate_user_form.errors)

        required_password_form = UserManagementForm({"username": "manager"}, require_password=True)
        self.assertFalse(required_password_form.is_valid())
        self.assertIn("password", required_password_form.errors)

        promoted_user_form = UserManagementForm(
            {"username": "manager", "password": "manager-password-123", "is_superuser": "on"},
            require_password=True,
        )
        self.assertTrue(promoted_user_form.is_valid(), promoted_user_form.errors)
        self.assertTrue(promoted_user_form.cleaned_data["is_staff"])

        managed_user = get_user_model().objects.create_user(
            username="controller-user",
            password="initial-password-123",
            first_name="Controller",
            last_name="User",
        )
        self.support_group.user_set.add(managed_user)

        updated_user = UserController.update(
            managed_user,
            {
                "username": managed_user.username,
                "first_name": "Updated",
                "last_name": "User",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "password": "new-password-123",
            },
        )

        self.assertTrue(updated_user.check_password("new-password-123"))
        self.assertEqual(list(updated_user.groups.values_list("name", flat=True)), [self.support_group.name])

        managed_group = Group.objects.create(name="Escalation")
        managed_group.user_set.add(self.user)
        updated_group = GroupController.update(managed_group, {"name": "Escalation Desk"})

        self.assertEqual(updated_group.name, "Escalation Desk")
        self.assertEqual(list(updated_group.user_set.values_list("username", flat=True)), [self.user.username])

        instance_group_form = GroupManagementForm({"name": managed_group.name}, instance=managed_group)
        self.assertTrue(instance_group_form.is_valid(), instance_group_form.errors)

    def test_superuser_user_management_endpoints_support_create_read_update_and_deactivate(self):
        other_group = Group.objects.create(name="Field Operations")

        create_response = self.client.post(
            "/api/users",
            data=json.dumps({
                "username": "coordinator",
                "first_name": "Case",
                "last_name": "Coordinator",
                "password": "coordinator-password-123",
                "is_active": True,
                "is_staff": True,
                "is_superuser": False,
                "language_preference": "de",
                "avatar_type": "image",
                "is_system_user": True,
                "group_ids": [self.support_group.pk],
            }),
            content_type="application/json",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(create_response.status_code, 201)
        managed_user = get_user_model().objects.get(username="coordinator")
        self.assertTrue(managed_user.check_password("coordinator-password-123"))
        self.assertEqual(create_response.json()["user"]["language_preference"], "de")
        self.assertTrue(create_response.json()["user"]["is_system_user"])
        self.assertEqual(create_response.json()["user"]["groups"][0]["name"], self.support_group.name)

        detail_response = self.client.get(
            f"/api/users/{managed_user.pk}",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["username"], "coordinator")

        update_response = self.client.put(
            f"/api/users/{managed_user.pk}",
            data=json.dumps({
                "username": "coordinator",
                "first_name": "Casey",
                "last_name": "Coordinator",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "language_preference": "en",
                "avatar_type": "initials",
                "is_system_user": False,
                "group_ids": [other_group.pk],
            }),
            content_type="application/json",
            headers=self.admin_auth_header(),
        )

        managed_user.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(managed_user.first_name, "Casey")
        self.assertEqual(managed_user.groups.get().name, other_group.name)
        self.assertEqual(managed_user.profile.language_preference, "en")
        self.assertEqual(managed_user.profile.avatar_type, "initials")
        self.assertFalse(managed_user.profile.is_system_user)

        deactivate_response = self.client.delete(
            f"/api/users/{managed_user.pk}",
            headers=self.admin_auth_header(),
        )

        managed_user.refresh_from_db()
        self.assertEqual(deactivate_response.status_code, 200)
        self.assertEqual(deactivate_response.json()["status"], "deactivated")
        self.assertFalse(managed_user.is_active)

        list_response = self.client.get(
            "/api/users",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertNotIn("coordinator", [item["username"] for item in list_response.json()["data"]])

    def test_superuser_group_management_endpoints_support_create_read_update_and_delete(self):
        create_response = self.client.post(
            "/api/groups",
            data=json.dumps({
                "name": "Field Operations",
                "user_ids": [self.user.pk],
            }),
            content_type="application/json",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(create_response.status_code, 201)
        managed_group = Group.objects.get(name="Field Operations")
        self.assertEqual(create_response.json()["group"]["users"][0]["username"], self.user.username)

        detail_response = self.client.get(
            f"/api/groups/{managed_group.pk}",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["name"], "Field Operations")

        update_response = self.client.put(
            f"/api/groups/{managed_group.pk}",
            data=json.dumps({
                "name": "Field Dispatch",
                "user_ids": [self.observer.pk],
            }),
            content_type="application/json",
            headers=self.admin_auth_header(),
        )

        managed_group.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(managed_group.name, "Field Dispatch")
        self.assertEqual(list(managed_group.user_set.values_list("username", flat=True)), [self.observer.username])

        delete_response = self.client.delete(
            f"/api/groups/{managed_group.pk}",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["status"], "deleted")
        self.assertFalse(Group.objects.filter(pk=managed_group.pk).exists())

    def test_user_and_group_management_requires_superuser(self):
        baseline_group_name = self.support_group.name
        create_user_response = self.client.post(
            "/api/users",
            data=json.dumps({"username": "blocked", "password": "blocked-password-123"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        get_user_response = self.client.get(
            f"/api/users/{self.user.pk}",
            headers=self.basic_auth_header(),
        )
        update_user_response = self.client.put(
            f"/api/users/{self.user.pk}",
            data=json.dumps({"username": self.user.username}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        delete_user_response = self.client.delete(
            f"/api/users/{self.user.pk}",
            headers=self.basic_auth_header(),
        )
        create_group_response = self.client.post(
            "/api/groups",
            data=json.dumps({"name": "Blocked Group"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        get_group_response = self.client.get(
            f"/api/groups/{self.support_group.pk}",
            headers=self.basic_auth_header(),
        )
        update_group_response = self.client.put(
            f"/api/groups/{self.support_group.pk}",
            data=json.dumps({"name": self.support_group.name}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        delete_group_response = self.client.delete(
            f"/api/groups/{self.support_group.pk}",
            headers=self.basic_auth_header(),
        )

        for response in [
            create_user_response,
            get_user_response,
            update_user_response,
            delete_user_response,
            create_group_response,
            get_group_response,
            update_group_response,
            delete_group_response,
        ]:
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"], "Superuser access required.")

        self.assertFalse(get_user_model().objects.filter(username="blocked").exists())
        self.user.refresh_from_db()
        self.support_group.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.support_group.name, baseline_group_name)

    def test_staff_user_without_superuser_flag_cannot_manage_users_or_groups(self):
        staff_user = get_user_model().objects.create_user(
            username="staff-operator",
            password="staff-password-123",
            first_name="Staff",
            last_name="Operator",
            is_staff=True,
        )
        baseline_group_name = self.support_group.name

        create_user_response = self.client.post(
            "/api/users",
            data=json.dumps({"username": "staff-blocked", "password": "staff-blocked-password-123"}),
            content_type="application/json",
            headers=self.basic_auth_header(username="staff-operator", password="staff-password-123"),
        )
        update_user_response = self.client.put(
            f"/api/users/{self.user.pk}",
            data=json.dumps({"username": self.user.username, "first_name": "Changed"}),
            content_type="application/json",
            headers=self.basic_auth_header(username="staff-operator", password="staff-password-123"),
        )
        delete_user_response = self.client.delete(
            f"/api/users/{self.user.pk}",
            headers=self.basic_auth_header(username="staff-operator", password="staff-password-123"),
        )
        create_group_response = self.client.post(
            "/api/groups",
            data=json.dumps({"name": "Staff Blocked Group"}),
            content_type="application/json",
            headers=self.basic_auth_header(username="staff-operator", password="staff-password-123"),
        )
        update_group_response = self.client.put(
            f"/api/groups/{self.support_group.pk}",
            data=json.dumps({"name": "Renamed By Staff"}),
            content_type="application/json",
            headers=self.basic_auth_header(username="staff-operator", password="staff-password-123"),
        )
        delete_group_response = self.client.delete(
            f"/api/groups/{self.support_group.pk}",
            headers=self.basic_auth_header(username="staff-operator", password="staff-password-123"),
        )

        for response in [
            create_user_response,
            update_user_response,
            delete_user_response,
            create_group_response,
            update_group_response,
            delete_group_response,
        ]:
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"], "Superuser access required.")

        self.assertFalse(get_user_model().objects.filter(username="staff-blocked").exists())
        self.user.refresh_from_db()
        self.support_group.refresh_from_db()
        self.assertEqual(self.user.first_name, "Demo")
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.support_group.name, baseline_group_name)

    def test_inactive_superuser_cannot_authenticate_to_management_endpoints(self):
        inactive_admin = get_user_model().objects.create_superuser(
            username="inactive-admin",
            password="inactive-admin-password-123",
            email="inactive-admin@example.com",
        )
        inactive_admin.is_active = False
        inactive_admin.save(update_fields=["is_active"])

        responses = [
            self.client.get(
                f"/api/users/{self.user.pk}",
                headers=self.basic_auth_header(username="inactive-admin", password="inactive-admin-password-123"),
            ),
            self.client.post(
                "/api/groups",
                data=json.dumps({"name": "Inactive Admin Group"}),
                content_type="application/json",
                headers=self.basic_auth_header(username="inactive-admin", password="inactive-admin-password-123"),
            ),
        ]

        for response in responses:
            self.assertEqual(response.status_code, 401)

        self.assertFalse(Group.objects.filter(name="Inactive Admin Group").exists())

    def test_group_delete_rejects_groups_still_assigned_to_issues(self):
        Issue.objects.create(
            title="Assigned group issue",
            description_markdown="Group still referenced by an issue.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        response = self.client.delete(
            f"/api/groups/{self.support_group.pk}",
            headers=self.admin_auth_header(),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "Group is still assigned to one or more issues.")
        self.assertTrue(Group.objects.filter(pk=self.support_group.pk).exists())

    def test_board_and_dashboard_endpoints_return_ui_parity_data(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
        )
        IssueComment.objects.create(
            issue=issue,
            author_user=self.observer,
            body="@demo please investigate.",
        )

        board_response = self.client.get("/api/board", headers=self.basic_auth_header())

        self.assertEqual(board_response.status_code, 200)
        self.assertEqual(board_response.json()["board_issue_count"], 1)
        self.assertEqual(board_response.json()["board_columns"][0]["issues"][0]["issue_number"], issue.issue_number)
        self.assertEqual(board_response.json()["board_columns"][0]["issues"][0]["user"]["avatar_text"], "DU")

        dashboard_response = self.client.get("/api/dashboard", headers=self.basic_auth_header())

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_response.json()["assigned_issues"][0]["issue_number"], issue.issue_number)
        self.assertEqual(dashboard_response.json()["mentioned_comments"][0]["author_user"]["avatar_text"], "OO")

    def test_board_endpoint_applies_filter_combinations(self):
        matching_issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
        )
        other_collection = Collection.objects.create(name="Incident", prefix="INC")
        other_category = IssueCategory.objects.create(name="Security", code="SECURITY")
        Issue.objects.create(
            title="Branch office malware alert",
            description_markdown="Endpoint scan flagged suspicious activity.",
            collection=other_collection,
            category=other_category,
            group=self.support_group,
            user=self.observer,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.LOW,
        )

        response = self.client.get(
            "/api/board",
            {
                "search": "uplink",
                "assignee": self.user.pk,
                "priority": IssuePriority.CRITICAL,
                "collection": self.collection.pk,
                "category": self.category.pk,
                "group": self.support_group.pk,
                "is_escalated": "false",
            },
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["board_issue_count"], 1)
        self.assertEqual(payload["selected_assignee"], str(self.user.pk))
        self.assertEqual(payload["selected_priority"], IssuePriority.CRITICAL)
        self.assertEqual(payload["selected_group"], str(self.support_group.pk))
        self.assertEqual(payload["selected_is_escalated"], "false")
        self.assertEqual(payload["board_columns"][0]["issues"][0]["issue_number"], matching_issue.issue_number)

    def test_board_endpoint_filters_by_updated_within_seconds(self):
        recent_issue = Issue.objects.create(
            title="Recent board issue",
            description_markdown="Recently updated issue.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.MEDIUM,
        )
        stale_issue = Issue.objects.create(
            title="Stale board issue",
            description_markdown="Older issue update.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.MEDIUM,
        )
        Issue.objects.filter(pk=stale_issue.pk).update(updated_at=timezone.now() - timezone.timedelta(seconds=120))

        response = self.client.get(
            "/api/board",
            {"updated_within_seconds": "30"},
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["selected_updated_within_seconds"], "30")
        self.assertEqual(payload["board_issue_count"], 1)
        self.assertEqual(payload["board_columns"][0]["issues"][0]["issue_number"], recent_issue.issue_number)

    def test_issue_list_endpoint_applies_filter_combinations(self):
        filtered_issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
        )
        other_category = IssueCategory.objects.create(name="Facilities", code="FACILITIES")
        Issue.objects.create(
            title="Cooling alert",
            description_markdown="Rack temperature exceeded threshold.",
            collection=self.collection,
            category=other_category,
            group=self.support_group,
            user=self.observer,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        response = self.client.get(
            "/api/issues",
            {
                "search": "uplink",
                "assignee": self.user.pk,
                "priority": IssuePriority.CRITICAL,
                "collection": self.collection.pk,
                "category": self.category.pk,
            },
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["data"][0]["issue_number"], filtered_issue.issue_number)

    def test_issue_list_endpoint_filters_by_workflow_state_code(self):
        matching_issue = Issue.objects.create(
            title="Awaiting vendor response",
            description_markdown="Waiting for supplier triage.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.WAITING,
            priority=IssuePriority.HIGH,
        )
        Issue.objects.create(
            title="Still new",
            description_markdown="No action started.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        response = self.client.get(
            "/api/issues",
            {"workflow_state": WorkflowState.WAITING},
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["issue_number"] for item in payload["data"]], [matching_issue.issue_number])

    def test_issue_list_endpoint_filters_by_workflow_state_label(self):
        matching_issue = Issue.objects.create(
            title="Queued for dispatch",
            description_markdown="Assignment pending.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.ASSIGNED,
            priority=IssuePriority.MEDIUM,
        )
        Issue.objects.create(
            title="Resolved already",
            description_markdown="Awaiting closeout.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.RESOLVED,
            priority=IssuePriority.MEDIUM,
        )

        response = self.client.get(
            "/api/issues",
            {"workflow_state_label": "Assigned"},
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["issue_number"] for item in payload["data"]], [matching_issue.issue_number])

    def test_issue_list_endpoint_filters_by_group_and_escalation(self):
        matching_issue = Issue.objects.create(
            title="Escalated group issue",
            description_markdown="Needs follow-up by the support group.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
            is_escalated=True,
        )
        other_group = Group.objects.create(name="Field Operations")
        Issue.objects.create(
            title="Escalated elsewhere",
            description_markdown="Assigned to another group.",
            collection=self.collection,
            category=self.category,
            group=other_group,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
            is_escalated=True,
        )
        Issue.objects.create(
            title="Not escalated",
            description_markdown="Same group without escalation.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
            is_escalated=False,
        )

        response = self.client.get(
            "/api/issues",
            {"group": self.support_group.pk, "is_escalated": "true"},
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["issue_number"] for item in payload["data"]], [matching_issue.issue_number])

    def test_issue_list_endpoint_filters_by_updated_within_seconds(self):
        recent_issue = Issue.objects.create(
            title="Recent update",
            description_markdown="Recently touched issue.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.MEDIUM,
        )
        stale_issue = Issue.objects.create(
            title="Stale update",
            description_markdown="Old issue update.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.MEDIUM,
        )
        Issue.objects.filter(pk=stale_issue.pk).update(updated_at=timezone.now() - timezone.timedelta(seconds=120))

        response = self.client.get(
            "/api/issues",
            {"updated_within_seconds": "30"},
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["issue_number"] for item in payload["data"]], [recent_issue.issue_number])

    def test_issue_detail_endpoint_includes_related_records(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
        )
        IssueComment.objects.create(
            issue=issue,
            author_user=self.user,
            body="Investigating now.",
        )

        response = self.client.get(f"/api/issues/{issue.pk}", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["issue_number"], issue.issue_number)
        self.assertEqual(response.json()["comments"][0]["body"], "Investigating now.")

    def test_issue_detail_endpoint_orders_workflow_and_field_history_newest_first(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.ASSIGNED,
            priority=IssuePriority.CRITICAL,
        )
        IssueHistoryEvent.objects.create(
            issue=issue,
            event_type=IssueHistoryEvent.FIELD_CHANGED,
            field_name="priority",
            old_value="High",
            new_value="Critical",
            changed_by_user=self.user,
            changed_at=timezone.now() - timezone.timedelta(minutes=2),
        )
        IssueStateTransition.objects.create(
            issue=issue,
            from_state=WorkflowState.NEW,
            to_state=WorkflowState.ASSIGNED,
            changed_by_user=self.user,
            reason="Triaged and dispatched.",
            changed_at=timezone.now() - timezone.timedelta(minutes=1),
        )
        IssueHistoryEvent.objects.create(
            issue=issue,
            event_type=IssueHistoryEvent.FIELD_CHANGED,
            field_name="title",
            old_value="Primary outage",
            new_value="Primary uplink outage",
            changed_by_user=self.user,
            changed_at=timezone.now(),
        )

        response = self.client.get(f"/api/issues/{issue.pk}", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [entry["field_name"] for entry in response.json()["history"][:3]],
            ["title", "workflow_state", "priority"],
        )

    def test_create_issue_endpoint_uses_same_validation_and_controller_behavior(self):
        response = self.client.post(
            "/api/issues",
            data=json.dumps({
                "title": "Primary uplink outage",
                "description_markdown": "Core switch unreachable from branch office.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": self.support_group.pk,
                "user": self.user.pk,
                "is_escalated": True,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "created")
        self.assertEqual(Issue.objects.count(), 1)
        self.assertTrue(Issue.objects.get().is_escalated)

    def test_create_issue_endpoint_accepts_multipart_attachments(self):
        response = self.client.post(
            "/api/issues",
            data={
                "title": "Primary uplink outage",
                "description_markdown": "Core switch unreachable from branch office.",
                "collection": str(self.collection.pk),
                "category": str(self.category.pk),
                "priority": IssuePriority.HIGH,
                "group": str(self.support_group.pk),
                "user": str(self.user.pk),
                "attachment_description": "Switch logs",
                "attachment_file": SimpleUploadedFile(
                    "switch-logs.txt", b"uplink timed out", content_type="text/plain"
                ),
            },
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 201)
        issue = Issue.objects.get()
        self.assertEqual(issue.attachments.count(), 1)
        self.assertEqual(issue.attachments.get().original_filename, "switch-logs.txt")
        self.assertEqual(response.json()["issue"]["attachments"][0]["original_filename"], "switch-logs.txt")

    def test_update_issue_endpoint_applies_workflow_transition(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        response = self.client.put(
            f"/api/issues/{issue.pk}",
            data=json.dumps({
                "title": issue.title,
                "description_markdown": issue.description_markdown,
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": self.support_group.pk,
                "user": self.user.pk,
                "is_escalated": False,
                "workflow_state": WorkflowState.ASSIGNED,
                "transition_reason": "Triaged and dispatched.",
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        issue.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.workflow_state, WorkflowState.ASSIGNED)
        self.assertEqual(issue.state_transitions.count(), 1)

    def test_update_issue_endpoint_applies_workflow_state_auto_assignment_rule(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )
        WorkflowStateAutoAssignmentRule.objects.create(
            workflow_state=WorkflowState.ASSIGNED,
            group=self.support_group,
            user=self.user,
        )

        response = self.client.put(
            f"/api/issues/{issue.pk}",
            data=json.dumps({
                "title": issue.title,
                "description_markdown": issue.description_markdown,
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": None,
                "user": None,
                "is_escalated": False,
                "workflow_state": WorkflowState.ASSIGNED,
                "transition_reason": "Triaged and dispatched.",
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.workflow_state, WorkflowState.ASSIGNED)
        self.assertEqual(issue.group, self.support_group)
        self.assertEqual(issue.user, self.user)

    def test_update_issue_endpoint_returns_combined_history_for_non_workflow_changes(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.ASSIGNED,
            priority=IssuePriority.HIGH,
        )

        response = self.client.put(
            f"/api/issues/{issue.pk}",
            data=json.dumps({
                "title": issue.title,
                "description_markdown": "Still assigned to network operations.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": self.support_group.pk,
                "user": self.user.pk,
                "is_escalated": True,
                "workflow_state": WorkflowState.ASSIGNED,
                "transition_reason": "",
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.history_events.count(), 2)
        self.assertEqual(response.json()["issue"]["history"][0]["message"], "Escalation enabled")
        self.assertEqual(response.json()["issue"]["history"][1]["message"], "Issue description changed")

    def test_update_issue_endpoint_supports_partial_put_payloads(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        response = self.client.put(
            f"/api/issues/{issue.pk}",
            data=json.dumps({
                "title": "Primary uplink outage updated",
                "workflow_state": WorkflowState.ASSIGNED,
                "transition_reason": "Triaged and dispatched.",
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.title, "Primary uplink outage updated")
        self.assertEqual(issue.workflow_state, WorkflowState.ASSIGNED)
        self.assertEqual(issue.description_markdown, "Core switch unreachable from branch office.")
        self.assertEqual(issue.collection_id, self.collection.pk)
        self.assertEqual(issue.category_id, self.category.pk)
        self.assertEqual(issue.priority, IssuePriority.HIGH)

    def test_update_issue_endpoint_accepts_multipart_attachments(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        response = self.multipart_put(
            f"/api/issues/{issue.pk}",
            {
                "title": issue.title,
                "description_markdown": issue.description_markdown,
                "collection": str(self.collection.pk),
                "category": str(self.category.pk),
                "priority": IssuePriority.HIGH,
                "group": str(self.support_group.pk),
                "user": str(self.user.pk),
                "is_escalated": "",
                "workflow_state": WorkflowState.NEW,
                "transition_reason": "",
                "attachment_description": "Packet capture",
                "attachment_file": SimpleUploadedFile(
                    "capture.pcap", b"pcap-bytes", content_type="application/vnd.tcpdump.pcap"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        issue.refresh_from_db()
        self.assertEqual(issue.attachments.count(), 1)
        self.assertEqual(issue.attachments.get().original_filename, "capture.pcap")
        self.assertEqual(response.json()["issue"]["attachments"][0]["original_filename"], "capture.pcap")

    def test_comment_endpoint_accepts_multipart_attachments(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        response = self.client.post(
            f"/api/issues/{issue.pk}/comments",
            data={
                "body": "Investigating now.",
                "visibility": "INTERNAL",
                "attachment_description": "Traceroute output",
                "attachment_file": SimpleUploadedFile("trace.txt", b"hop1\nhop2", content_type="text/plain"),
            },
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 201)
        issue.refresh_from_db()
        self.assertEqual(issue.comments.count(), 1)
        self.assertEqual(issue.attachments.count(), 1)
        self.assertEqual(issue.attachments.get().original_filename, "trace.txt")
        self.assertEqual(response.json()["issue"]["attachments"][0]["original_filename"], "trace.txt")

    def test_comment_move_and_archive_endpoints_mutate_issue(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        comment_response = self.client.post(
            f"/api/issues/{issue.pk}/comments",
            data=json.dumps({"body": "Investigating now.", "visibility": "INTERNAL"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(comment_response.status_code, 201)
        self.assertEqual(issue.comments.count(), 1)

        move_response = self.client.post(
            f"/api/issues/{issue.pk}/move",
            data=json.dumps({"target_state": WorkflowState.IN_PROGRESS, "position_index": 0}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        issue.refresh_from_db()
        self.assertEqual(move_response.status_code, 200)
        self.assertEqual(issue.workflow_state, WorkflowState.IN_PROGRESS)

        archive_response = self.client.post(
            f"/api/issues/{issue.pk}/archive",
            data=json.dumps({"confirm_archive": True}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        issue.refresh_from_db()
        self.assertEqual(archive_response.status_code, 200)
        self.assertIsNotNone(issue.archived_at)

    def test_comment_update_endpoint_updates_existing_comment(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )
        comment = IssueComment.objects.create(
            issue=issue,
            author_user=self.user,
            body="Initial comment",
        )

        response = self.client.put(
            f"/api/issues/{issue.pk}/comments/{comment.pk}",
            data=json.dumps({"body": "Updated for {{user:observer}}", "visibility": "CUSTOMER_VISIBLE"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        comment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(comment.body, "Updated for {{user:observer}}")
        self.assertEqual(comment.visibility, "CUSTOMER_VISIBLE")
        self.assertEqual(comment.mentions.count(), 1)
        self.assertEqual(response.json()["comment"]["body"], "Updated for {{user:observer}}")

    def test_attachment_endpoints_support_create_update_and_delete_with_history(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        create_response = self.client.post(
            f"/api/issues/{issue.pk}/attachments",
            data={
                "description": "Initial trace",
                "file": SimpleUploadedFile("trace.txt", b"hop1\nhop2", content_type="text/plain"),
            },
            headers=self.basic_auth_header(),
        )

        self.assertEqual(create_response.status_code, 201)
        attachment = issue.attachments.get()
        self.assertEqual(create_response.json()["attachment"]["original_filename"], "trace.txt")
        self.assertEqual(
            create_response.json()["attachment"]["file_url"],
            f"/api/issues/{issue.pk}/attachments/{attachment.pk}/download",
        )

        update_response = self.multipart_put(
            f"/api/issues/{issue.pk}/attachments/{attachment.pk}",
            {
                "description": "Updated trace",
                "file": SimpleUploadedFile("trace-2.txt", b"hop3\nhop4", content_type="text/plain"),
            },
        )

        attachment.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(attachment.description, "Updated trace")
        self.assertEqual(attachment.original_filename, "trace-2.txt")
        self.assertEqual(
            update_response.json()["attachment"]["file_url"],
            f"/api/issues/{issue.pk}/attachments/{attachment.pk}/download",
        )

        delete_response = self.client.delete(
            f"/api/issues/{issue.pk}/attachments/{attachment.pk}",
            headers=self.basic_auth_header(),
        )

        issue.refresh_from_db()
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["status"], "deleted")
        self.assertEqual(issue.attachments.count(), 0)

        detail_response = self.client.get(f"/api/issues/{issue.pk}", headers=self.basic_auth_header())

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(
            [entry["message"] for entry in detail_response.json()["history"][:3]],
            ["Attachment removed", "Attachment updated", "Attachment added"],
        )

    def test_attachment_download_endpoint_returns_file_response(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )
        attachment = issue.attachments.create(
            original_filename="trace.txt",
            file=SimpleUploadedFile("trace.txt", b"hop1\nhop2", content_type="text/plain"),
            content_type="text/plain",
            file_size=9,
            description="Initial trace",
            uploaded_by_user=self.user,
        )

        response = self.client.get(
            f"/api/issues/{issue.pk}/attachments/{attachment.pk}/download",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn('attachment; filename="trace.txt"', response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"hop1\nhop2")

    def test_issue_detail_exposes_relative_attachment_file_url(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )
        attachment = issue.attachments.create(
            original_filename="trace.txt",
            file=SimpleUploadedFile("trace.txt", b"hop1\nhop2", content_type="text/plain"),
            content_type="text/plain",
            file_size=9,
            description="Initial trace",
            uploaded_by_user=self.user,
        )

        response = self.client.get(f"/api/issues/{issue.pk}", headers=self.basic_auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["attachments"][0]["file_url"],
            f"/api/issues/{issue.pk}/attachments/{attachment.pk}/download",
        )
        self.assertTrue(response.json()["attachments"][0]["file_url"].startswith("/"))

    def test_create_issue_endpoint_surfaces_form_errors(self):
        response = self.client.post(
            "/api/issues",
            data=json.dumps({
                "title": "Primary uplink outage",
                "description_markdown": "Core switch unreachable from branch office.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "user": self.user.pk,
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("group", response.json()["errors"])

    def test_create_issue_endpoint_rejects_invalid_json_payload(self):
        response = self.client.post(
            "/api/issues",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid request payload.")

    def test_update_issue_archive_comment_and_move_endpoints_surface_invalid_payloads(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )

        update_response = self.client.put(
            f"/api/issues/{issue.pk}",
            data=json.dumps({
                "title": issue.title,
                "description_markdown": issue.description_markdown,
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "user": self.user.pk,
                "workflow_state": WorkflowState.NEW,
                "transition_reason": "",
            }),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        archive_response = self.client.post(
            f"/api/issues/{issue.pk}/archive",
            data=json.dumps({}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_comment_response = self.client.post(
            f"/api/issues/{issue.pk}/comments",
            data=json.dumps({"body": "", "visibility": "INTERNAL"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_move_response = self.client.post(
            f"/api/issues/{issue.pk}/move",
            data=json.dumps({"target_state": "WRONG", "position_index": 0}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_position_response = self.client.post(
            f"/api/issues/{issue.pk}/move",
            data=json.dumps({"target_state": WorkflowState.NEW, "position_index": "bad"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(update_response.status_code, 400)
        self.assertIn("group", update_response.json()["errors"])
        self.assertEqual(archive_response.status_code, 400)
        self.assertIn("confirm_archive", archive_response.json()["errors"])
        self.assertEqual(invalid_comment_response.status_code, 400)
        self.assertIn("body", invalid_comment_response.json()["errors"])
        self.assertEqual(invalid_move_response.status_code, 400)
        self.assertEqual(invalid_move_response.json()["error"], "Invalid workflow state.")
        self.assertEqual(invalid_position_response.status_code, 400)
        self.assertEqual(invalid_position_response.json()["error"], "Invalid target position.")

    def test_mutation_endpoints_surface_invalid_json_and_form_errors(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )
        comment = IssueComment.objects.create(
            issue=issue,
            author_user=self.user,
            body="Investigating now.",
        )
        attachment = issue.attachments.create(
            original_filename="trace.txt",
            file=SimpleUploadedFile("trace.txt", b"hop1\nhop2", content_type="text/plain"),
            content_type="text/plain",
            file_size=9,
            description="Initial trace",
            uploaded_by_user=self.user,
        )

        invalid_update_response = self.client.put(
            f"/api/issues/{issue.pk}",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_archive_response = self.client.post(
            f"/api/issues/{issue.pk}/archive",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_comment_add_response = self.client.post(
            f"/api/issues/{issue.pk}/comments",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_comment_update_response = self.client.put(
            f"/api/issues/{issue.pk}/comments/{comment.pk}",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_comment_update_form_response = self.client.put(
            f"/api/issues/{issue.pk}/comments/{comment.pk}",
            data=json.dumps({"body": "", "visibility": "INTERNAL"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_attachment_add_response = self.client.post(
            f"/api/issues/{issue.pk}/attachments",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_attachment_add_form_response = self.client.post(
            f"/api/issues/{issue.pk}/attachments",
            data=json.dumps({"description": "Missing file"}),
            content_type="application/json",
            headers=self.basic_auth_header(),
        )
        invalid_attachment_update_response = self.client.put(
            f"/api/issues/{issue.pk}/attachments/{attachment.pk}",
            data="{invalid",
            content_type="application/json",
            headers=self.basic_auth_header(),
        )

        self.assertEqual(invalid_update_response.status_code, 400)
        self.assertEqual(invalid_update_response.json()["error"], "Invalid request payload.")
        self.assertEqual(invalid_archive_response.status_code, 400)
        self.assertEqual(invalid_archive_response.json()["error"], "Invalid request payload.")
        self.assertEqual(invalid_comment_add_response.status_code, 400)
        self.assertEqual(invalid_comment_add_response.json()["error"], "Invalid request payload.")
        self.assertEqual(invalid_comment_update_response.status_code, 400)
        self.assertEqual(invalid_comment_update_response.json()["error"], "Invalid request payload.")
        self.assertEqual(invalid_comment_update_form_response.status_code, 400)
        self.assertIn("body", invalid_comment_update_form_response.json()["errors"])
        self.assertEqual(invalid_attachment_add_response.status_code, 400)
        self.assertEqual(invalid_attachment_add_response.json()["error"], "Invalid request payload.")
        self.assertEqual(invalid_attachment_add_form_response.status_code, 400)
        self.assertIn("file", invalid_attachment_add_form_response.json()["errors"])
        self.assertEqual(invalid_attachment_update_response.status_code, 400)
        self.assertEqual(invalid_attachment_update_response.json()["error"], "Invalid request payload.")

    def test_move_payload_returns_errors_for_invalid_requests(self):
        invalid_json_request = self.request_factory.post(
            "/api/issues/1/move",
            data="{invalid",
            content_type="application/json",
        )

        payload, error = _move_payload(invalid_json_request)

        self.assertIsNone(payload)
        self.assertEqual(error, (400, {"error": "Invalid request payload."}))
