from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from djangoapp.core.models import Collection, DraftIssueAttachment, Issue, IssueAttachment, IssueCategory
from djangoapp.user_interface.templatetags.issue_markdown import render_issue_markdown, render_markdown


class IssueMarkdownTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo",
            password="demo-password-123",
        )
        self.collection = Collection.objects.get(prefix="TASK")
        self.category = IssueCategory.objects.create(name="Network", code="NETWORK")

    def test_render_issue_markdown_supports_issue_attachment_and_user_tokens(self):
        referenced_issue = Issue.objects.create(
            title="Referenced issue",
            description_markdown="Body",
            collection=self.collection,
            category=self.category,
        )
        current_issue = Issue.objects.create(
            title="Current issue",
            description_markdown="Body",
            collection=self.collection,
            category=self.category,
        )
        attachment = IssueAttachment.objects.create(
            issue=current_issue,
            file=SimpleUploadedFile("network-log.txt", b"link down"),
            original_filename="network-log.txt",
            content_type="text/plain",
            file_size=9,
            description="Primary network log",
            uploaded_by_user=self.user,
        )

        rendered = render_issue_markdown(
            (
                f"See {{{{issue:{referenced_issue.issue_number}}}}} and "
                f"{{{{attachment:{attachment.pk}}}}}. Notify {{{{user:demo}}}}."
            ),
            current_issue,
        )

        self.assertIn(reverse("issue-detail", args=[referenced_issue.pk]), rendered)
        self.assertIn(attachment.file.url, rendered)
        self.assertIn("@demo", rendered)
        self.assertIn("Primary network log", rendered)

    def test_render_issue_markdown_preserves_unresolved_tokens(self):
        issue = Issue.objects.create(
            title="Current issue",
            description_markdown="Body",
            collection=self.collection,
            category=self.category,
        )

        rendered = render_issue_markdown(
            "{{issue:UNKNOWN-001}} {{attachment:999}} {{attachment:not-a-number}}",
            issue,
        )

        self.assertIn("{{issue:UNKNOWN-001}}", rendered)
        self.assertIn("{{attachment:999}}", rendered)
        self.assertIn("{{attachment:not-a-number}}", rendered)
        self.assertEqual(render_issue_markdown("{{attachment:1}}"), "<p>{{attachment:1}}</p>")

    def test_render_issue_markdown_supports_draft_attachment_tokens(self):
        draft_attachment = DraftIssueAttachment.objects.create(
            draft_token="draft-token-123",
            file=SimpleUploadedFile("draft-log.txt", b"draft body"),
            original_filename="draft-log.txt",
            content_type="text/plain",
            file_size=10,
            description="Draft upload",
            uploaded_by_user=self.user,
        )

        rendered = render_issue_markdown(
            f"See {{{{attachment:draft-{draft_attachment.pk}}}}}.",
            draft_token="draft-token-123",
            uploaded_by_user=self.user,
        )

        self.assertIn("draft-log.txt", rendered)
        self.assertIn("Draft upload", rendered)

    def test_render_markdown_supports_code_blank_lines_and_empty_values(self):
        rendered = render_markdown("# Heading\n\nParagraph one\nParagraph two\n\n- Item\n\n`code`")

        self.assertIn("<h1>Heading</h1>", rendered)
        self.assertIn("<p>Paragraph one<br>Paragraph two</p>", rendered)
        self.assertIn("<ul><li>Item</li></ul>", rendered)
        self.assertIn("<p><code>code</code></p>", rendered)
        self.assertEqual(render_markdown(""), "")
        self.assertEqual(render_issue_markdown(""), "")
