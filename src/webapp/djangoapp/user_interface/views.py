import json
import uuid

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views import View
from django.views.generic import FormView, TemplateView

from . import controllers
from .board_events import board_event_broker
from .forms import IssueArchiveForm, IssueCommentForm, IssueCreateForm, IssueDescriptionForm, IssueUpdateForm
from .templatetags.issue_markdown import render_issue_markdown

BOARD_COLUMN_STATES_SESSION_KEY = "user_interface.board_column_states"
ISSUE_CREATE_DRAFT_TOKEN_SESSION_KEY = "user_interface.issue_create_attachment_draft"


def _parse_issue_move_payload(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None, JsonResponse({"error": "Invalid request payload."}, status=400)

    target_state = str(payload.get("target_state", "")).strip().upper()
    if not controllers.is_board_state(target_state):
        return None, JsonResponse({"error": "Invalid workflow state."}, status=400)

    try:
        position_index = int(payload.get("position_index", 0))
    except TypeError, ValueError:
        return None, JsonResponse({"error": "Invalid target position."}, status=400)

    return {
        "target_state": target_state,
        "position_index": max(0, position_index),
    }, None


def _issue_move_response(issue):
    return JsonResponse({
        "status": "ok",
        "issue_id": issue.pk,
        "workflow_state": issue.workflow_state,
        "board_position": issue.board_position,
    })


def _get_issue_create_draft_token(request):
    draft_token = request.session.get(ISSUE_CREATE_DRAFT_TOKEN_SESSION_KEY, "")
    if draft_token:
        return draft_token

    draft_token = uuid.uuid4().hex
    request.session[ISSUE_CREATE_DRAFT_TOKEN_SESSION_KEY] = draft_token
    request.session.modified = True
    return draft_token


def _clear_issue_create_draft_token(request):
    request.session.pop(ISSUE_CREATE_DRAFT_TOKEN_SESSION_KEY, None)
    request.session.modified = True


def _serialize_draft_attachment(attachment):
    return {
        "id": attachment.pk,
        "label": attachment.original_filename,
        "description": attachment.description,
        "token": f"{{{{attachment:draft-{attachment.pk}}}}}",
    }


def _get_query_value(request):
    return request.GET.get("query", "").strip()


def _get_uploaded_attachment_files(request):
    return request.FILES.getlist("attachment_file") or request.FILES.getlist("files")


def _results_response(attachments):
    return JsonResponse({"results": [_serialize_draft_attachment(attachment) for attachment in attachments]})


def _upload_response(attachments):
    return JsonResponse({"attachments": [_serialize_draft_attachment(attachment) for attachment in attachments]})


def _render_preview_html(body, **kwargs):
    return str(render_issue_markdown(body, **kwargs))


class AppLoginRequiredMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        return super().handle_no_permission()


class SessionLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Signed in successfully.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Username and password did not match. Please try again.")
        return super().form_invalid(form)


class SessionLogoutView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        auth_logout(request)
        messages.info(request, "Signed out successfully.")
        return redirect("login")


class AuthenticatedTemplateView(AppLoginRequiredMixin, TemplateView):
    pass


class AuthenticatedFormView(AppLoginRequiredMixin, FormView):
    invalid_message = "Review the highlighted fields and try again."

    def form_invalid(self, form):
        messages.error(self.request, self.invalid_message)
        return super().form_invalid(form)


class IssueContextMixin:
    issue = None

    def get_issue(self):
        if self.issue is None:
            self.issue = controllers.get_issue(self.kwargs["pk"])
        return self.issue


class HomeView(AuthenticatedTemplateView):
    template_name = "core/home.html"

    def _is_fullscreen_mode(self):
        return self.request.GET.get("fullscreen") == "1"

    def _build_board_querystring(self, *, fullscreen):
        params = self.request.GET.copy()
        if fullscreen:
            params["fullscreen"] = "1"
        else:
            params.pop("fullscreen", None)
        querystring = params.urlencode()
        if not querystring:
            return ""
        return f"?{querystring}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            controllers.build_board_context(
                self.request.GET,
                self.request.session.get(BOARD_COLUMN_STATES_SESSION_KEY),
            )
        )
        context["board_fullscreen_mode"] = self._is_fullscreen_mode()
        context["board_fullscreen_querystring"] = self._build_board_querystring(fullscreen=True)
        context["board_standard_querystring"] = self._build_board_querystring(fullscreen=False)
        return context


class DashboardView(AuthenticatedTemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(controllers.build_dashboard_context(self.request.user))
        return context


class IssueDetailView(IssueContextMixin, AuthenticatedTemplateView):
    template_name = "core/issue_detail.html"

    def get_template_names(self):
        if self.request.GET.get("modal") == "1":
            return ["core/partials/issue_detail_modal.html"]
        if self.request.GET.get("fragment") == "1":
            return ["core/partials/issue_detail_page.html"]
        return [self.template_name]

    def get_issue_detail_context(self, form=None, description_form=None, description_edit_open=False):
        issue = self.get_issue()
        context = {
            "issue": issue,
            "comment_form": form or IssueCommentForm(),
            "description_form": description_form or IssueDescriptionForm(instance=issue),
            "description_edit_open": description_edit_open,
            "modal_mode": self.request.GET.get("modal") == "1",
        }
        context.update(controllers.build_issue_detail_context(issue))
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_issue_detail_context())
        return context


class IssueCreateView(AuthenticatedFormView):
    template_name = "core/issue_form.html"
    form_class = IssueCreateForm

    def get_initial(self):
        initial = super().get_initial()
        initial["attachment_draft_token"] = _get_issue_create_draft_token(self.request)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "active_nav": "create-issue",
            "issue": None,
            "issue_create_draft_token": _get_issue_create_draft_token(self.request),
            "form_title": "Create New Issue",
            "submit_label": "Create issue",
        })
        return context

    def form_valid(self, form):
        issue = controllers.create_issue(form.cleaned_data, self.request.user)
        _clear_issue_create_draft_token(self.request)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(self.request, f"Issue {issue.issue_number} was created.")
        return redirect("issue-detail", pk=issue.pk)


class IssueUpdateView(IssueContextMixin, AuthenticatedFormView):
    template_name = "core/issue_form.html"
    form_class = IssueUpdateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_issue()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "active_nav": "board",
            "issue": self.get_issue(),
            "form_title": "Update Existing Issue",
            "submit_label": "Save changes",
        })
        return context

    def form_valid(self, form):
        issue = controllers.update_issue(self.get_issue(), form.cleaned_data, self.request.user)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(self.request, f"Issue {issue.issue_number} was updated.")
        return redirect("issue-detail", pk=issue.pk)


class IssueDescriptionUpdateView(IssueContextMixin, AuthenticatedFormView):
    template_name = "core/issue_detail.html"
    form_class = IssueDescriptionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_issue()
        return kwargs

    def form_valid(self, form):
        issue = controllers.update_issue_description(self.get_issue(), form.cleaned_data, self.request.user)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(self.request, f"Issue {issue.issue_number} description was updated.")
        return redirect("issue-detail", pk=issue.pk)

    def form_invalid(self, form):
        messages.error(self.request, self.invalid_message)
        detail_view = IssueDetailView()
        detail_view.request = self.request
        detail_view.kwargs = self.kwargs
        context = {
            **detail_view.get_issue_detail_context(
                description_form=form,
                description_edit_open=True,
            ),
            "active_nav": "board",
        }
        return TemplateResponse(self.request, self.template_name, context, status=400)


class IssueArchiveView(IssueContextMixin, AuthenticatedFormView):
    template_name = "core/issue_archive_confirm.html"
    form_class = IssueArchiveForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_nav"] = "board"
        context["issue"] = self.get_issue()
        return context

    def form_valid(self, form):
        issue = controllers.archive_issue(self.get_issue(), self.request.user)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(self.request, f"Issue {issue.issue_number} was archived.")
        return redirect("dashboard")


class IssueCommentCreateView(IssueContextMixin, AuthenticatedFormView):
    template_name = "core/issue_comment_form.html"
    form_class = IssueCommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_nav"] = "board"
        context["issue"] = self.get_issue()
        return context

    def form_valid(self, form):
        issue = self.get_issue()
        controllers.add_issue_comment(issue, form.cleaned_data, self.request.user)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(self.request, f"A new issue comment was added to {issue.issue_number}.")
        return redirect("issue-detail", pk=issue.pk)

    def form_invalid(self, form):
        messages.error(self.request, self.invalid_message)
        detail_view = IssueDetailView()
        detail_view.request = self.request
        detail_view.kwargs = self.kwargs
        context = {**detail_view.get_issue_detail_context(form), "active_nav": "board"}
        return TemplateResponse(self.request, "core/issue_detail.html", context, status=400)


class IssueAttachmentDeleteView(IssueContextMixin, AppLoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        attachment_name, issue = controllers.delete_issue_attachment(
            self.get_issue(),
            self.kwargs["attachment_pk"],
            request.user,
        )
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(request, f"Attachment {attachment_name} was removed from {issue.issue_number}.")
        return redirect("issue-detail", pk=issue.pk)


class MarkdownPreviewView(AppLoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        html = _render_preview_html(
            request.POST.get("body", ""),
            draft_token=_get_issue_create_draft_token(request),
            uploaded_by_user=request.user,
        )
        return JsonResponse({"html": html})


class IssueMarkdownPreviewView(IssueContextMixin, AppLoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        html = _render_preview_html(request.POST.get("body", ""), issue=self.get_issue())
        return JsonResponse({"html": html})


class UserSuggestionView(AppLoginRequiredMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        query = _get_query_value(request)
        results = [
            {
                "value": user.username,
                "label": user.get_full_name() or user.username,
                "token": f"{{{{user:{user.username}}}}}",
            }
            for user in controllers.search_users(query)
        ]
        return JsonResponse({"results": results})


class IssueSuggestionView(AppLoginRequiredMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        query = _get_query_value(request)
        results = [
            {
                "value": issue.issue_number,
                "label": f"{issue.issue_number}: {issue.title}",
                "token": f"{{{{issue:{issue.issue_number}}}}}",
            }
            for issue in controllers.search_issues(query)
        ]
        return JsonResponse({"results": results})


class AttachmentSuggestionView(IssueContextMixin, AppLoginRequiredMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        query = _get_query_value(request)
        results = [
            {
                "value": attachment.pk,
                "label": attachment.original_filename,
                "description": attachment.description,
                "token": f"{{{{attachment:{attachment.pk}}}}}",
            }
            for attachment in controllers.search_issue_attachments(self.get_issue(), query)
        ]
        return JsonResponse({"results": results})


class DraftAttachmentUploadView(AppLoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        attachment_files = _get_uploaded_attachment_files(request)
        if not attachment_files:
            return JsonResponse({"errors": {"attachment_file": ["Select at least one file."]}}, status=400)

        attachments = controllers.create_draft_attachments(
            _get_issue_create_draft_token(request),
            attachment_files,
            request.user,
            request.POST.get("description", ""),
        )
        return _upload_response(attachments)


class DraftAttachmentSuggestionView(AppLoginRequiredMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        query = _get_query_value(request)
        attachments = controllers.search_draft_attachments(
            _get_issue_create_draft_token(request),
            request.user,
            query,
        )
        return _results_response(attachments)


class BoardFragmentView(AuthenticatedTemplateView):
    template_name = "core/partials/kanban_board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            controllers.build_board_context(
                self.request.GET,
                self.request.session.get(BOARD_COLUMN_STATES_SESSION_KEY),
            )
        )
        return context


class BoardColumnStateView(AppLoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid request payload."}, status=400)

        request.session[BOARD_COLUMN_STATES_SESSION_KEY] = controllers.normalize_board_column_states(
            payload.get("states")
        )
        request.session.modified = True
        return JsonResponse({"status": "ok"})


class IssueBoardMoveView(IssueContextMixin, AppLoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        move_payload, error_response = _parse_issue_move_payload(request)
        if error_response is not None:
            return error_response

        issue = controllers.move_issue(
            self.get_issue(),
            move_payload["target_state"],
            move_payload["position_index"],
            request.user,
        )
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        return _issue_move_response(issue)


class BoardEventStreamView(AppLoginRequiredMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        subscriber_id, subscriber = board_event_broker.subscribe()

        def stream():
            try:
                while True:
                    event_name, event_data = board_event_broker.next_event(subscriber)
                    yield f"event: {event_name}\ndata: {event_data}\n\n"
            finally:
                board_event_broker.unsubscribe(subscriber_id)

        response = StreamingHttpResponse(stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
