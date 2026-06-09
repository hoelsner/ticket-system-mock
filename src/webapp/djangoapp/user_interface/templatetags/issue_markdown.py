import re

from django import template
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from djangoapp.core.models import DraftIssueAttachment, Issue

register = template.Library()

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LIST_RE = re.compile(r"^[-*]\s+(.*)$")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
TOKEN_RE = re.compile(r"\{\{\s*(user|issue|attachment)\s*:\s*([^}]+?)\s*\}\}")
STRONG_RE = re.compile(r"\*\*(.+?)\*\*")
EM_RE = re.compile(r"(?<!\*)\*(.+?)\*(?!\*)")
CODE_RE = re.compile(r"`([^`]+)`")


def _build_user_token(username):
    user = get_user_model().objects.filter(username=username, is_active=True).only("username").first()
    if user is None:
        return f'<span class="detail-token detail-token--user">@{escape(username)}</span>'

    return (
        f'<a href="{escape(reverse("user-profile-detail", args=[user.username]))}" '
        f'class="detail-token detail-token--user">@{escape(username)}</a>'
    )


def _build_issue_token(issue_number):
    issue = Issue.objects.filter(issue_number=issue_number, archived_at__isnull=True).only("pk", "issue_number").first()
    if issue is None:
        return escape(f"{{{{issue:{issue_number}}}}}")

    return (
        f'<a href="{escape(reverse("issue-detail", args=[issue.pk]))}" '
        f'class="detail-token detail-token--issue">{escape(issue.issue_number)}</a>'
    )


def _build_attachment_token(attachment_key, issue=None, draft_token=None, uploaded_by_user=None):
    if issue is None:
        if not str(attachment_key).startswith("draft-"):
            return escape(f"{{{{attachment:{attachment_key}}}}}")

        if not draft_token or uploaded_by_user is None:
            return escape(f"{{{{attachment:{attachment_key}}}}}")

        draft_attachment = (
            DraftIssueAttachment.objects
            .filter(
                pk=str(attachment_key).removeprefix("draft-"),
                draft_token=draft_token,
                uploaded_by_user=uploaded_by_user,
            )
            .only("pk", "original_filename", "file", "description")
            .first()
        )
        if draft_attachment is None:
            return escape(f"{{{{attachment:{attachment_key}}}}}")

        description = f" <span>{escape(draft_attachment.description)}</span>" if draft_attachment.description else ""
        return (
            f'<a href="{escape(draft_attachment.file.url)}" target="_blank" rel="noopener noreferrer" '
            f'class="detail-token detail-token--attachment">{escape(draft_attachment.original_filename)}</a>{description}'
        )

    attachment = (
        issue.attachments
        .filter(pk=attachment_key)
        .only(
            "pk",
            "original_filename",
            "file",
            "description",
        )
        .first()
    )
    if attachment is None:
        return escape(f"{{{{attachment:{attachment_key}}}}}")

    description = f" <span>{escape(attachment.description)}</span>" if attachment.description else ""
    return (
        f'<a href="{escape(attachment.file.url)}" target="_blank" rel="noopener noreferrer" '
        f'class="detail-token detail-token--attachment">{escape(attachment.original_filename)}</a>{description}'
    )


def _render_token(match, issue=None):
    token_type = match.group(1).lower()
    token_value = match.group(2).strip()

    if token_type == "user" and token_value:
        return _build_user_token(token_value)
    if token_type == "issue" and token_value:
        return _build_issue_token(token_value)
    if token_type == "attachment" and token_value:
        if token_value.isdigit():
            return _build_attachment_token(int(token_value), issue=issue)
        if token_value.startswith("draft-"):
            return _build_attachment_token(
                token_value,
                issue=issue,
                draft_token=_render_token.draft_token,
                uploaded_by_user=_render_token.uploaded_by_user,
            )

    return escape(match.group(0))


def _render_inline(value, issue=None, draft_token=None, uploaded_by_user=None):
    escaped = escape(value)
    code_tokens = []

    def replace_code(match):
        token = f"__CODE_TOKEN_{len(code_tokens)}__"
        code_tokens.append(f"<code>{escape(match.group(1))}</code>")
        return token

    rendered = CODE_RE.sub(replace_code, escaped)
    rendered = LINK_RE.sub(
        lambda match: (
            f'<a href="{escape(match.group(2))}" target="_blank" rel="noopener noreferrer">{match.group(1)}</a>'
        ),
        rendered,
    )
    _render_token.draft_token = draft_token
    _render_token.uploaded_by_user = uploaded_by_user
    rendered = TOKEN_RE.sub(lambda match: _render_token(match, issue=issue), rendered)
    rendered = STRONG_RE.sub(r"<strong>\1</strong>", rendered)
    rendered = EM_RE.sub(r"<em>\1</em>", rendered)

    for index, replacement in enumerate(code_tokens):
        rendered = rendered.replace(f"__CODE_TOKEN_{index}__", replacement)

    return rendered


def _strip_line(line):
    return line.rstrip()


def _render_heading(level, content):
    return f"<h{level}>{content}</h{level}>"


def _render_list(items):
    return f"<ul>{''.join(items)}</ul>"


def _render_paragraph(paragraph_lines, issue=None, draft_token=None, uploaded_by_user=None):
    paragraph = "<br>".join(
        _render_inline(part, issue=issue, draft_token=draft_token, uploaded_by_user=uploaded_by_user)
        for part in paragraph_lines
    )
    return f"<p>{paragraph}</p>"


def _consume_heading(lines, index, issue=None, draft_token=None, uploaded_by_user=None):
    heading_match = HEADING_RE.match(_strip_line(lines[index]))
    if not heading_match:
        return None, index

    level = len(heading_match.group(1))
    content = _render_inline(
        heading_match.group(2).strip(),
        issue=issue,
        draft_token=draft_token,
        uploaded_by_user=uploaded_by_user,
    )
    return _render_heading(level, content), index + 1


def _consume_list(lines, index, issue=None, draft_token=None, uploaded_by_user=None):
    items = []
    next_index = index

    while next_index < len(lines):
        current_match = LIST_RE.match(_strip_line(lines[next_index]))
        if not current_match:
            break
        items.append(
            f"<li>{_render_inline(current_match.group(1).strip(), issue=issue, draft_token=draft_token, uploaded_by_user=uploaded_by_user)}</li>"
        )
        next_index += 1

    if not items:
        return None, index

    return _render_list(items), next_index


def _consume_paragraph(lines, index, issue=None, draft_token=None, uploaded_by_user=None):
    paragraph_lines = [_strip_line(lines[index])]
    next_index = index + 1

    while next_index < len(lines):
        current = _strip_line(lines[next_index])
        if not current or HEADING_RE.match(current) or LIST_RE.match(current):
            break
        paragraph_lines.append(current)
        next_index += 1

    return _render_paragraph(
        paragraph_lines,
        issue=issue,
        draft_token=draft_token,
        uploaded_by_user=uploaded_by_user,
    ), next_index


def _render_blocks(value, issue=None, draft_token=None, uploaded_by_user=None):
    lines = value.splitlines()
    blocks = []
    index = 0

    while index < len(lines):
        line = _strip_line(lines[index])
        if not line:
            index += 1
            continue

        for consumer in (
            _consume_heading,
            _consume_list,
            _consume_paragraph,
        ):
            block, next_index = consumer(
                lines,
                index,
                issue=issue,
                draft_token=draft_token,
                uploaded_by_user=uploaded_by_user,
            )
            if block is None:
                continue
            blocks.append(block)
            index = next_index
            break

    return "".join(blocks)


@register.filter
def render_markdown(value):
    if not value:
        return ""

    return mark_safe(_render_blocks(value))  # nosec


@register.simple_tag
def render_issue_markdown(value, issue=None, draft_token=None, uploaded_by_user=None):
    if not value:
        return ""

    return mark_safe(
        _render_blocks(
            value,
            issue=issue,
            draft_token=draft_token,
            uploaded_by_user=uploaded_by_user,
        )
    )  # nosec
