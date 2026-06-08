import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from django.utils import formats, timezone

from djangoapp.core.models import (
    Collection,
    DraftIssueAttachment,
    Issue,
    IssueAttachment,
    IssueCategory,
    IssueComment,
    IssueHistoryEvent,
    IssuePriority,
    IssueStateTransition,
    WorkflowState,
)
from djangoapp.user_interface.forms import IssueCreateForm, IssueDescriptionForm
from djangoapp.user_interface.views import ISSUE_CREATE_DRAFT_TOKEN_SESSION_KEY


class UserInterfaceTests(TestCase):
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
        self.collection = Collection.objects.get(prefix="TASK")
        self.category = IssueCategory.objects.create(name="Network", code="NETWORK")

    def test_home_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("home"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("login"))
        self.assertNotContains(response, "Sign in to continue in the user frontend.")

    def test_login_page_shows_top_navigation_for_guests(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket System Mock")
        self.assertContains(response, "default_app_logo.png")
        self.assertContains(response, "default_app_hero_image.png")
        self.assertContains(response, reverse("home"))
        self.assertContains(response, reverse("login"))
        self.assertContains(response, "Sign in")
        self.assertContains(response, "Login using your credentials.")
        self.assertContains(response, "auth-layout__illustration-panel")
        self.assertNotContains(response, "Operational overview")
        self.assertNotContains(response, "Django")
        self.assertContains(response, "app-icon")

    def test_login_view_uses_message_panel_for_failed_authentication(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": self.user.username,
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username and password did not match. Please try again.")
        self.assertContains(response, "message-panel__item--error")

    def test_login_and_logout_use_messages_framework(self):
        login_response = self.client.post(
            reverse("login"),
            {
                "username": self.user.username,
                "password": "demo-password-123",
                "next": reverse("home"),
            },
            follow=True,
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "Signed in successfully.")
        self.assertContains(login_response, "message-panel__item--success")

        logout_response = self.client.post(reverse("logout"), follow=True)

        self.assertEqual(logout_response.status_code, 200)
        self.assertContains(logout_response, "Signed out successfully.")
        self.assertContains(logout_response, "message-panel__item--info")

    def test_home_is_available_to_authenticated_users(self):
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
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="app-surface app-surface--filters board-filters-panel"')
        self.assertContains(response, 'class="board-filters-panel__summary"')
        self.assertContains(response, "Toggle filters")
        self.assertContains(response, 'aria-label="Open board fullscreen"')
        self.assertContains(response, f'href="{reverse("home")}?fullscreen=1"', html=False)
        self.assertContains(response, "Primary uplink outage")
        self.assertContains(response, reverse("issue-detail", args=[issue.pk]))
        self.assertContains(response, "Board")
        self.assertContains(response, "/admin/")
        self.assertContains(response, "/api/docs")
        self.assertContains(response, "Demo User")
        self.assertContains(response, "Sign out")
        self.assertContains(response, "Ticket System Mock")
        self.assertContains(response, "default_app_logo.png")
        self.assertContains(response, reverse("dashboard"))
        self.assertContains(response, reverse("issue-create"))
        self.assertContains(response, "kanban-board-shell")
        self.assertContains(response, "data-kanban-board-shell")
        self.assertContains(response, "data-kanban-card-wrapper")
        self.assertContains(response, "Backlog")
        self.assertNotContains(response, "Personal Dashboard")
        self.assertNotContains(response, "Create New Issue")
        self.assertNotContains(response, "kanban-priority-pane")
        self.assertContains(response, "side-navigation__panel")
        self.assertContains(response, "side-navigation__list")
        self.assertContains(response, "side-navigation__item", count=7)
        self.assertContains(response, "side-navigation__action")
        self.assertContains(response, "data-side-navigation")
        self.assertContains(response, "data-side-navigation-close", count=7)
        self.assertContains(response, reverse("healthcheck-status"))
        self.assertContains(response, "data-app-content")
        self.assertContains(response, "app-shell.js")
        self.assertContains(response, 'class="top-navigation__brand contrast"')
        self.assertContains(response, 'class="contrast app-inline-icon-link"')
        self.assertContains(response, "app-inline-icon-link")
        self.assertNotContains(response, "Signed in as")
        self.assertNotContains(response, "Operations board")
        self.assertNotContains(response, "Track workload by Workflow State and adjust the active filters in one place.")

    def test_home_supports_fullscreen_board_mode(self):
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
        self.client.force_login(self.user)

        response = self.client.get(f"{reverse('home')}?fullscreen=1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Primary uplink outage")
        self.assertContains(response, reverse("issue-detail", args=[issue.pk]))
        self.assertContains(response, "board-fullscreen-mode")
        self.assertContains(response, "app-main--fullscreen")
        self.assertContains(response, "Exit fullscreen")
        self.assertContains(response, "kanban-board-shell")
        self.assertNotContains(response, "<h1>Instance Kanban Board</h1>", html=True)
        self.assertNotContains(response, "Search issues by title or description")
        self.assertNotContains(response, "top-navigation-shell")
        self.assertNotContains(response, "top-navigation__brand")

    def test_issue_card_component_renders_issue_summary(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="**Line one**\n\n- Line two\n- Line three",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            priority=IssuePriority.CRITICAL,
            is_escalated=True,
        )
        IssueComment.objects.create(
            issue=issue,
            author_user=self.user,
            body="Investigating the uplink issue.",
        )

        rendered = render_to_string("cotton/issue/card.html", {"issue": issue})
        expected_created_at = formats.date_format(
            timezone.localtime(issue.created_at),
            "SHORT_DATETIME_FORMAT",
            use_l10n=True,
        )
        expected_updated_at = formats.date_format(
            timezone.localtime(issue.updated_at),
            "SHORT_DATETIME_FORMAT",
            use_l10n=True,
        )

        self.assertIn(issue.issue_number, rendered)
        self.assertIn(issue.title, rendered)
        self.assertIn(reverse("issue-detail", args=[issue.pk]), rendered)
        self.assertIn("<h3", rendered)
        self.assertIn(
            "Critical" if issue.priority == IssuePriority.CRITICAL else issue.get_priority_display(), rendered
        )
        self.assertNotIn("Priority:", rendered)
        self.assertIn("Open in New Window", rendered)
        self.assertIn("<strong>Line one</strong>", rendered)
        self.assertIn("Network Operations", rendered)
        self.assertIn(reverse("issue-comment-create", args=[issue.pk]), rendered)
        self.assertIn("Demo User", rendered)
        self.assertIn("Assignee", rendered)
        self.assertIn("issue-card__avatar issue-card__avatar--title", rendered)
        self.assertIn("issue-card__labels", rendered)
        self.assertIn("issue-card__tag--priority-critical", rendered)
        self.assertIn("issue-card__tag--escalated", rendered)
        self.assertIn("issue-card__eyebrow", rendered)
        self.assertLess(rendered.index("issue-card__eyebrow"), rendered.index("issue-card__title-row"))
        self.assertLess(rendered.index(issue.issue_number), rendered.index("issue-card__labels"))
        self.assertLess(rendered.index("issue-card__labels"), rendered.index("issue-card__title-row"))
        self.assertIn("issue-card__actions", rendered)
        self.assertIn("issue-card__details", rendered)
        self.assertIn("Details and activity", rendered)
        self.assertIn("issue-card__comments", rendered)
        self.assertIn("Investigating the uplink issue.", rendered)
        self.assertNotIn(f"{issue.issue_number}: {issue.title}", rendered)
        self.assertIn(expected_created_at, rendered)
        self.assertIn(expected_updated_at, rendered)
        self.assertNotIn(issue.created_at.strftime("%Y-%m-%d %H:%M"), rendered)
        self.assertIn('data-tooltip="Open issue details"', rendered)
        self.assertNotIn('title="Open issue details"', rendered)
        self.assertIn("app-icon", rendered)

    def test_issue_detail_view_supports_modal_fragment(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="# Heading\n\nBody text.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.IN_PROGRESS,
            priority=IssuePriority.HIGH,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("issue-detail", args=[issue.pk]), {"modal": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-issue-detail-modal-content")
        self.assertContains(response, reverse("issue-detail", args=[issue.pk]))
        self.assertContains(response, "Open Full Page")

    def test_issue_detail_view_supports_page_fragment(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="# Heading\n\nBody text.",
            collection=self.collection,
            category=self.category,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("issue-detail", args=[issue.pk]), {"fragment": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-issue-detail-page")
        self.assertNotContains(response, "data-issue-detail-modal-content")

    def test_board_column_state_persists_in_session(self):
        Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )
        self.client.force_login(self.user)

        save_response = self.client.post(
            reverse("board-column-state"),
            data=json.dumps({"states": {"NEW": False, "BACKLOG": True}}),
            content_type="application/json",
        )
        response = self.client.get(reverse("home"))
        rendered = response.content.decode("utf-8")

        self.assertEqual(save_response.status_code, 200)
        self.assertRegex(rendered, r'<details class="kanban-column"(?![^>]* open)[^>]*data-workflow-state="NEW"')
        self.assertRegex(rendered, r'<details class="kanban-column"[^>]* open[^>]*data-workflow-state="BACKLOG"')

    def test_empty_board_columns_are_collapsed_by_default(self):
        Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.HIGH,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))
        rendered = response.content.decode("utf-8")

        self.assertRegex(rendered, r'<details class="kanban-column"(?![^>]* open)[^>]*data-workflow-state="BACKLOG"')
        self.assertRegex(rendered, r'<details class="kanban-column"[^>]* open[^>]*data-workflow-state="NEW"')

    def test_home_filters_board_by_search(self):
        Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Branch connectivity failed.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
        )
        Issue.objects.create(
            title="Printer toner low",
            description_markdown="Office printer needs attention.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.WAITING,
            priority=IssuePriority.LOW,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"), {"search": "uplink"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Primary uplink outage")
        self.assertNotContains(response, "Printer toner low")

    def test_dashboard_shows_assigned_issues_and_mentions(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.IN_PROGRESS,
            priority=IssuePriority.HIGH,
        )
        IssueComment.objects.create(
            issue=issue,
            author_user=self.observer,
            body="Please review this @demo before closure.",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Personal Dashboard")
        self.assertContains(response, 'aria-label="Open board fullscreen"')
        self.assertContains(response, f'href="{reverse("home")}?fullscreen=1"', html=False)
        self.assertContains(response, issue.title)
        self.assertContains(response, "Please review this @demo before closure.")

    def test_issue_detail_is_available_to_authenticated_users(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.IN_PROGRESS,
            priority=IssuePriority.HIGH,
        )
        IssueComment.objects.create(
            issue=issue,
            author_user=self.user,
            body="Working on switch replacement.",
        )
        IssueStateTransition.objects.create(
            issue=issue,
            from_state=WorkflowState.NEW,
            to_state=WorkflowState.IN_PROGRESS,
            changed_by_user=self.user,
            reason="Assigned to the network team.",
        )
        IssueAttachment.objects.create(
            issue=issue,
            file=SimpleUploadedFile("network-log.txt", b"link down"),
            original_filename="network-log.txt",
            content_type="text/plain",
            file_size=9,
            uploaded_by_user=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("issue-detail", args=[issue.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, issue.issue_number)
        self.assertContains(response, issue.title)
        self.assertContains(response, "Back to board")
        self.assertContains(response, "Working on switch replacement.")
        self.assertContains(response, "network-log.txt")
        self.assertContains(response, reverse("issue-attachment-delete", args=[issue.pk, issue.attachments.get().pk]))
        self.assertContains(response, 'target="_blank"', html=False)
        self.assertContains(response, reverse("issue-comment-create", args=[issue.pk]))
        self.assertContains(response, "Issue history")
        self.assertContains(response, "Assigned to the network team.")
        self.assertContains(response, "data-issue-detail-refresh-url")
        self.assertNotContains(response, 'class="issue-card"', html=False)

        response_content = response.content.decode()
        self.assertLess(response_content.index("Issue Details"), response_content.index("Issue Description"))
        self.assertLess(response_content.index("Issue Description"), response_content.index("Related records"))
        self.assertLess(response_content.index("Related records"), response_content.index("Comments"))
        self.assertLess(response_content.index("Comments"), response_content.index("Attachments"))
        self.assertLess(response_content.index("Attachments"), response_content.index("Issue history"))

    def test_issue_detail_renders_description_and_comment_tokens(self):
        referenced_issue = Issue.objects.create(
            title="Referenced issue",
            description_markdown="Body",
            collection=self.collection,
            category=self.category,
        )
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown=f"See {{{{issue:{referenced_issue.issue_number}}}}}.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
        )
        attachment = IssueAttachment.objects.create(
            issue=issue,
            file=SimpleUploadedFile("network-log.txt", b"link down"),
            original_filename="network-log.txt",
            content_type="text/plain",
            file_size=9,
            uploaded_by_user=self.user,
            description="Diagnostic log",
        )
        IssueComment.objects.create(
            issue=issue,
            author_user=self.user,
            body=f"Review {{{{attachment:{attachment.pk}}}}} with {{{{user:observer}}}}.",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("issue-detail", args=[issue.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "detail-token--issue")
        self.assertContains(response, reverse("issue-detail", args=[referenced_issue.pk]))
        self.assertContains(response, attachment.file.url)
        self.assertContains(response, "detail-token--user")

    def test_issue_description_update_view_saves_inline_description_changes(self):
        referenced_issue = Issue.objects.create(
            title="Referenced issue",
            description_markdown="Body",
            collection=self.collection,
            category=self.category,
        )
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Initial text.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-description-update", args=[issue.pk]),
            {
                "description_markdown": f"Updated {{{{issue:{referenced_issue.issue_number}}}}}",
            },
            follow=True,
        )

        issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.description_markdown, f"Updated {{{{issue:{referenced_issue.issue_number}}}}}")
        self.assertContains(response, f"Issue {issue.issue_number} description was updated.")

    def test_issue_description_update_view_renders_invalid_form_on_detail_page(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Initial text.",
            collection=self.collection,
            category=self.category,
        )
        self.client.force_login(self.user)

        with patch.object(IssueDescriptionForm, "clean", side_effect=ValidationError("forced failure")):
            response = self.client.post(
                reverse("issue-description-update", args=[issue.pk]),
                {"description_markdown": "Updated text"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Review the highlighted fields and try again.", status_code=400)
        self.assertContains(response, "forced failure", status_code=400)

    def test_markdown_preview_returns_rendered_html(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Initial text.",
            collection=self.collection,
            category=self.category,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-markdown-preview", args=[issue.pk]),
            {"body": "**Bold**"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("<strong>Bold</strong>", response.json()["html"])

    def test_generic_markdown_preview_returns_rendered_html(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("markdown-preview"),
            {"body": "**Bold** {{issue:TASK-999}}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("<strong>Bold</strong>", response.json()["html"])
        self.assertIn("{{issue:TASK-999}}", response.json()["html"])

    def test_editor_suggestion_endpoints_return_tokens(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Initial text.",
            collection=self.collection,
            category=self.category,
        )
        attachment = IssueAttachment.objects.create(
            issue=issue,
            file=SimpleUploadedFile("network-log.txt", b"link down"),
            original_filename="network-log.txt",
            content_type="text/plain",
            file_size=9,
            uploaded_by_user=self.user,
            description="Diagnostic log",
        )
        self.client.force_login(self.user)

        user_response = self.client.get(reverse("user-suggestions"), {"query": "obs"})
        issue_response = self.client.get(reverse("issue-suggestions"), {"query": issue.issue_number})
        attachment_response = self.client.get(reverse("attachment-suggestions", args=[issue.pk]), {"query": "network"})

        self.assertEqual(user_response.status_code, 200)
        self.assertEqual(issue_response.status_code, 200)
        self.assertEqual(attachment_response.status_code, 200)
        self.assertEqual(user_response.json()["results"][0]["token"], "{{user:observer}}")
        self.assertEqual(issue_response.json()["results"][0]["token"], f"{{{{issue:{issue.issue_number}}}}}")
        self.assertEqual(attachment_response.json()["results"][0]["token"], f"{{{{attachment:{attachment.pk}}}}}")

    def test_issue_comment_create_view_renders_invalid_form_on_detail_page(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Initial text.",
            collection=self.collection,
            category=self.category,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-comment-create", args=[issue.pk]),
            {
                "body": "",
                "visibility": "INTERNAL",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Review the highlighted fields and try again.", status_code=400)
        self.assertContains(response, "This field is required.", status_code=400)

    def test_issue_attachment_media_url_is_served_in_debug(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
        )
        attachment = IssueAttachment.objects.create(
            issue=issue,
            file=SimpleUploadedFile("network-log.txt", b"link down"),
            original_filename="network-log.txt",
            content_type="text/plain",
            file_size=9,
            uploaded_by_user=self.user,
        )
        resolver_match = resolve(attachment.file.url)
        response = resolver_match.func(
            self.request_factory.get(attachment.file.url),
            **resolver_match.kwargs,
        )

        self.assertEqual(resolver_match.func.__name__, "serve")
        self.assertEqual(response.status_code, 200)

    def test_issue_create_view_creates_issue_and_attachment(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-create"),
            {
                "title": "Database latency spike",
                "description_markdown": "Observed during backup window.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": self.support_group.pk,
                "user": self.user.pk,
                "is_escalated": "on",
                "attachment_file": SimpleUploadedFile("latency.txt", b"slow query"),
                "attachment_description": "Initial evidence",
            },
            follow=True,
        )

        issue = Issue.objects.get(title="Database latency spike")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.workflow_state, WorkflowState.BACKLOG)
        self.assertTrue(issue.is_escalated)
        self.assertEqual(issue.attachments.count(), 1)
        self.assertContains(response, f"Issue {issue.issue_number} was created.")

    def test_issue_create_view_allows_multiple_attachments(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-create"),
            {
                "title": "Database latency spike",
                "description_markdown": "Observed during backup window.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": self.support_group.pk,
                "user": self.user.pk,
                "attachment_file": [
                    SimpleUploadedFile("latency.txt", b"slow query"),
                    SimpleUploadedFile("graph.png", b"png-binary", content_type="image/png"),
                ],
                "attachment_description": "Initial evidence",
            },
            follow=True,
        )

        issue = Issue.objects.get(title="Database latency spike")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.attachments.count(), 2)
        self.assertQuerySetEqual(
            issue.attachments.order_by("original_filename").values_list("original_filename", flat=True),
            ["graph.png", "latency.txt"],
            transform=lambda value: value,
        )
        self.assertTrue(all(attachment.description == "Initial evidence" for attachment in issue.attachments.all()))

    def test_home_orders_issues_by_priority_before_board_position(self):
        low_issue = Issue.objects.create(
            title="Low priority backlog item",
            description_markdown="Low priority work.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.BACKLOG,
            priority=IssuePriority.LOW,
        )
        critical_issue = Issue.objects.create(
            title="Critical backlog item",
            description_markdown="Critical work.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.BACKLOG,
            priority=IssuePriority.CRITICAL,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))
        rendered = response.content.decode("utf-8")

        self.assertLess(rendered.index(critical_issue.title), rendered.index(low_issue.title))

    def test_issue_move_view_updates_state_and_position(self):
        first_issue = Issue.objects.create(
            title="First backlog issue",
            description_markdown="Backlog work.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.BACKLOG,
            priority=IssuePriority.HIGH,
        )
        second_issue = Issue.objects.create(
            title="Second backlog issue",
            description_markdown="Backlog work.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.BACKLOG,
            priority=IssuePriority.HIGH,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-move", args=[second_issue.pk]),
            data=json.dumps({
                "target_state": WorkflowState.BACKLOG,
                "position_index": 0,
            }),
            content_type="application/json",
        )

        first_issue.refresh_from_db()
        second_issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(second_issue.workflow_state, WorkflowState.BACKLOG)
        self.assertEqual(second_issue.board_position, 1)
        self.assertEqual(first_issue.board_position, 2)

    def test_issue_create_view_uses_message_panel_for_invalid_submission(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-create"),
            {
                "title": "Database latency spike",
                "description_markdown": "Observed during backup window.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": "",
                "user": self.user.pk,
                "attachment_description": "Initial evidence",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review the highlighted fields and try again.")
        self.assertContains(response, "message-panel__item--error")

    def test_issue_form_pages_render_expected_context(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
            group=self.support_group,
            user=self.user,
        )
        self.client.force_login(self.user)

        create_response = self.client.get(reverse("issue-create"))
        update_response = self.client.get(reverse("issue-update", args=[issue.pk]))
        archive_response = self.client.get(reverse("issue-archive", args=[issue.pk]))
        comment_response = self.client.get(reverse("issue-comment-create", args=[issue.pk]))

        self.assertContains(create_response, "Create New Issue")
        self.assertContains(create_response, "Create issue")
        self.assertContains(create_response, "Initial attachments")
        self.assertContains(create_response, reverse("markdown-preview"))
        self.assertContains(create_response, "data-markdown-editor")
        self.assertContains(create_response, reverse("draft-attachment-suggestions"))
        self.assertContains(create_response, reverse("draft-attachment-upload"))
        self.assertContains(create_response, "Drop files here to upload immediately")
        self.assertContains(create_response, "Upload attachment")
        self.assertContains(create_response, "{{user:username}}")
        self.assertContains(create_response, "data-markdown-preview-details")
        self.assertContains(create_response, "Toggle preview")
        self.assertContains(create_response, "data-markdown-preview-details open")
        self.assertContains(update_response, "Update Existing Issue")
        self.assertContains(update_response, issue.title)
        self.assertContains(update_response, reverse("issue-markdown-preview", args=[issue.pk]))
        self.assertContains(update_response, reverse("attachment-suggestions", args=[issue.pk]))
        self.assertContains(update_response, "data-markdown-preview-details")
        self.assertNotContains(update_response, "data-markdown-preview-details open")
        self.assertContains(archive_response, "Archive")
        self.assertContains(archive_response, issue.title)
        self.assertContains(comment_response, "Add comment")
        self.assertContains(comment_response, issue.title)
        self.assertContains(comment_response, reverse("issue-markdown-preview", args=[issue.pk]))
        self.assertContains(comment_response, reverse("attachment-suggestions", args=[issue.pk]))

    def test_session_expires_when_browser_closes(self):
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

    def test_issue_create_form_validates_assignment_and_attachment_rules(self):
        other_group = Group.objects.create(name="Field Services")

        initial_form = IssueCreateForm(initial={"group": self.support_group.pk})
        self.assertIn(self.user, initial_form.fields["user"].queryset)

        missing_group_form = IssueCreateForm(
            data={
                "title": "Database latency spike",
                "description_markdown": "Observed during backup window.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": "",
                "user": self.user.pk,
                "attachment_description": "Initial evidence",
            }
        )
        wrong_group_form = IssueCreateForm(
            data={
                "title": "Database latency spike",
                "description_markdown": "Observed during backup window.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": other_group.pk,
                "user": self.user.pk,
                "attachment_description": "Initial evidence",
            }
        )
        wrong_group_form.fields["user"].queryset = get_user_model().objects.order_by("username")

        self.assertFalse(missing_group_form.is_valid())
        self.assertIn(
            "A group is required when a user is assigned.",
            missing_group_form.errors["group"],
        )
        self.assertIn(
            "Select a file when providing an attachment description.",
            missing_group_form.errors["attachment_file"],
        )

        self.assertFalse(wrong_group_form.is_valid())
        self.assertIn(
            "The assigned user must belong to the assigned group.",
            wrong_group_form.errors["user"],
        )
        self.assertIn(
            "Select a file when providing an attachment description.",
            wrong_group_form.errors["attachment_file"],
        )

    def test_issue_create_form_accepts_multiple_files(self):
        attachment_form = IssueCreateForm(
            data={
                "title": "Database latency spike",
                "description_markdown": "Observed during backup window.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": self.support_group.pk,
                "user": self.user.pk,
                "attachment_description": "Initial evidence",
            },
            files={
                "attachment_file": [
                    SimpleUploadedFile("latency.txt", b"slow query"),
                    SimpleUploadedFile("graph.png", b"png-binary", content_type="image/png"),
                ]
            },
        )

        self.assertTrue(attachment_form.is_valid())
        self.assertEqual(len(attachment_form.cleaned_data["attachment_file"]), 2)

    def test_draft_attachment_upload_and_preview_work_for_issue_create_page(self):
        self.client.force_login(self.user)
        self.client.get(reverse("issue-create"))

        upload_response = self.client.post(
            reverse("draft-attachment-upload"),
            {
                "files": SimpleUploadedFile("network-log.txt", b"link down"),
            },
        )

        self.assertEqual(upload_response.status_code, 200)
        self.assertEqual(DraftIssueAttachment.objects.count(), 1)
        attachment_token = upload_response.json()["attachments"][0]["token"]

        preview_response = self.client.post(
            reverse("markdown-preview"),
            {"body": attachment_token},
        )

        self.assertEqual(preview_response.status_code, 200)
        self.assertIn("network-log.txt", preview_response.json()["html"])

    def test_issue_create_view_materializes_draft_attachments_and_rewrites_tokens(self):
        self.client.force_login(self.user)
        self.client.get(reverse("issue-create"))
        draft_token = self.client.session[ISSUE_CREATE_DRAFT_TOKEN_SESSION_KEY]

        upload_response = self.client.post(
            reverse("draft-attachment-upload"),
            {
                "files": SimpleUploadedFile("network-log.txt", b"link down"),
            },
        )
        attachment_token = upload_response.json()["attachments"][0]["token"]

        response = self.client.post(
            reverse("issue-create"),
            {
                "title": "Database latency spike",
                "description_markdown": f"Evidence:\n{attachment_token}",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "group": self.support_group.pk,
                "user": self.user.pk,
                "attachment_draft_token": draft_token,
                "attachment_description": "",
            },
            follow=True,
        )

        issue = Issue.objects.get(title="Database latency spike")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.attachments.count(), 1)
        self.assertEqual(DraftIssueAttachment.objects.count(), 0)
        self.assertNotIn("draft-", issue.description_markdown)
        self.assertIn(f"{{{{attachment:{issue.attachments.first().pk}}}}}", issue.description_markdown)

    def test_issue_update_view_records_transition(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-update", args=[issue.pk]),
            {
                "title": "Primary uplink outage",
                "description_markdown": "Assigned to network operations.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "workflow_state": WorkflowState.ASSIGNED,
                "transition_reason": "Triaged and dispatched.",
                "group": self.support_group.pk,
                "user": self.user.pk,
                "is_escalated": "",
                "attachment_description": "",
            },
            follow=True,
        )

        issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.workflow_state, WorkflowState.ASSIGNED)
        self.assertEqual(issue.state_transitions.count(), 1)
        self.assertEqual(issue.state_transitions.get().reason, "Triaged and dispatched.")
        self.assertContains(response, f"Issue {issue.issue_number} was updated.")

    def test_issue_update_view_without_state_change_keeps_transition_history_empty(self):
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
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-update", args=[issue.pk]),
            {
                "title": "Primary uplink outage",
                "description_markdown": "Still assigned to network operations.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "workflow_state": WorkflowState.ASSIGNED,
                "transition_reason": "No workflow change.",
                "group": self.support_group.pk,
                "user": self.user.pk,
                "is_escalated": "",
                "attachment_description": "",
            },
        )

        issue.refresh_from_db()

        self.assertRedirects(response, reverse("issue-detail", args=[issue.pk]))
        self.assertEqual(issue.workflow_state, WorkflowState.ASSIGNED)
        self.assertEqual(issue.state_transitions.count(), 0)
        self.assertEqual(issue.history_events.count(), 1)
        history_event = issue.history_events.get()
        self.assertEqual(history_event.event_type, IssueHistoryEvent.FIELD_CHANGED)
        self.assertEqual(history_event.field_name, "description")

    def test_issue_update_view_without_state_change_records_issue_history(self):
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
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-update", args=[issue.pk]),
            {
                "title": "Primary uplink outage",
                "description_markdown": "Still assigned to network operations.",
                "collection": self.collection.pk,
                "category": self.category.pk,
                "priority": IssuePriority.HIGH,
                "workflow_state": WorkflowState.ASSIGNED,
                "transition_reason": "No workflow change.",
                "group": self.support_group.pk,
                "user": self.user.pk,
                "is_escalated": "on",
                "attachment_description": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Issue history")
        self.assertContains(response, "Issue description changed")
        self.assertContains(response, "Escalation enabled")

    def test_issue_comment_create_view_persists_comment(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-comment-create", args=[issue.pk]),
            {
                "body": "Looping in @observer for validation.",
                "visibility": "INTERNAL",
                "attachment_description": "",
            },
            follow=True,
        )

        comment = issue.comments.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(comment.author_user, self.user)
        self.assertEqual(comment.mentions.count(), 1)
        self.assertEqual(comment.mentions.get().mentioned_as, "observer")
        self.assertContains(response, f"A new issue comment was added to {issue.issue_number}.")

    def test_issue_attachment_delete_view_removes_attachment_and_records_history(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
        )
        attachment = IssueAttachment.objects.create(
            issue=issue,
            file=SimpleUploadedFile("network-log.txt", b"link down"),
            original_filename="network-log.txt",
            content_type="text/plain",
            file_size=9,
            description="Diagnostic log",
            uploaded_by_user=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-attachment-delete", args=[issue.pk, attachment.pk]),
            follow=True,
        )

        issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(issue.attachments.count(), 0)
        self.assertContains(response, "Attachment removed")
        self.assertContains(
            response, f"Attachment {attachment.original_filename} was removed from {issue.issue_number}."
        )

    def test_issue_archive_view_archives_issue(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.NEW,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-archive", args=[issue.pk]),
            {"confirm_archive": "on"},
            follow=True,
        )

        issue.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(issue.archived_at)
        self.assertContains(response, f"Issue {issue.issue_number} was archived.")

    def test_issue_comment_create_view_supports_user_tokens(self):
        issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Core switch unreachable from branch office.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issue-comment-create", args=[issue.pk]),
            {
                "body": "Looping in {{user:observer}} before closure.",
                "visibility": "INTERNAL",
                "attachment_description": "",
            },
            follow=True,
        )

        comment = issue.comments.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(comment.mentions.count(), 1)
        self.assertEqual(comment.mentions.get().mentioned_as, "observer")
        self.assertContains(response, "detail-token--user")

    def test_home_filters_board_by_assignee_priority_and_category(self):
        matching_issue = Issue.objects.create(
            title="Primary uplink outage",
            description_markdown="Branch connectivity failed.",
            collection=self.collection,
            category=self.category,
            group=self.support_group,
            user=self.user,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.CRITICAL,
        )
        Issue.objects.create(
            title="Secondary uplink outage",
            description_markdown="Another issue for a different team.",
            collection=self.collection,
            category=self.category,
            workflow_state=WorkflowState.NEW,
            priority=IssuePriority.LOW,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("home"),
            {
                "assignee": str(self.user.pk),
                "priority": IssuePriority.CRITICAL,
                "collection": str(self.collection.pk),
                "category": str(self.category.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, matching_issue.title)
        self.assertNotContains(response, "Secondary uplink outage")

    def test_board_column_state_rejects_invalid_json_payload(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("board-column-state"),
            data="{invalid",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid request payload.")
