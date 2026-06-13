import json
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import FileResponse, Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views import View
from django.views.generic import FormView, TemplateView
from django.views.i18n import set_language as django_set_language

from djangoapp.core.models import WorkflowState

from . import controllers
from .board_events import board_event_broker
from .forms import (
    IssueArchiveForm,
    IssueCommentForm,
    IssueCreateForm,
    IssueDescriptionForm,
    IssueUpdateForm,
    UserProfileForm,
)
from .templatetags.issue_markdown import render_issue_markdown

BOARD_COLUMN_STATES_SESSION_KEY = "user_interface.board_column_states"
ISSUE_CREATE_DRAFT_TOKEN_SESSION_KEY = "user_interface.issue_create_attachment_draft"


def _parse_issue_move_payload(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None, JsonResponse({"error": _("Invalid request payload.")}, status=400)

    target_state = str(payload.get("target_state", "")).strip().upper()
    if not controllers.is_board_state(target_state):
        return None, JsonResponse({"error": _("Invalid workflow state.")}, status=400)

    try:
        position_index = int(payload.get("position_index", 0))
    except TypeError, ValueError:
        return None, JsonResponse({"error": _("Invalid target position.")}, status=400)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("active_nav", "")
        context.setdefault("board_fullscreen_mode", False)
        context.setdefault("board_fullscreen_querystring", "?fullscreen=1")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Signed in successfully."))
        return response

    def form_invalid(self, form):
        messages.error(self.request, _("Username and password did not match. Please try again."))
        return super().form_invalid(form)


class SessionLogoutView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        auth_logout(request)
        messages.info(request, _("Signed out successfully."))
        return redirect("login")


class SessionLanguageView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        language = str(request.POST.get("language", "")).strip()
        supported_languages = {code for code, _label in settings.LANGUAGES}

        if request.user.is_authenticated and language in supported_languages:
            profile = controllers.get_user_profile(request.user)
            if profile.language_preference != language:
                profile.language_preference = language
                profile.save(update_fields=["language_preference", "updated_at"])

        return django_set_language(request)


class AuthenticatedTemplateView(AppLoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("active_nav", "")
        context.setdefault("board_fullscreen_mode", False)
        context.setdefault("board_fullscreen_querystring", "?fullscreen=1")
        return context


class AuthenticatedFormView(AppLoginRequiredMixin, FormView):
    invalid_message = gettext_lazy("Review the highlighted fields and try again.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("active_nav", "")
        context.setdefault("board_fullscreen_mode", False)
        context.setdefault("board_fullscreen_querystring", "?fullscreen=1")
        return context

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


class IntegrationsView(AuthenticatedTemplateView):
    template_name = "core/integrations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(controllers.build_integrations_context())
        return context


class N8nNodePackageDownloadView(AppLoginRequiredMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        package = controllers.get_n8n_node_package()
        if package is None:
            raise Http404(_("The n8n integration package is not available."))

        return FileResponse(
            package["path"].open("rb"),
            as_attachment=True,
            filename=package["filename"],
            content_type="application/gzip",
        )


class UserProfileDetailView(AuthenticatedTemplateView):
    template_name = "core/profile_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = controllers.get_user_profile_by_username(self.kwargs["username"])
        context.update(controllers.build_user_profile_context(profile, self.request.user))
        return context


class UserProfileSettingsView(AuthenticatedFormView):
    template_name = "core/profile_settings.html"
    form_class = UserProfileForm
    success_message = gettext_lazy("Your profile settings were updated.")

    def get_profile(self):
        return controllers.get_user_profile(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_profile()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(controllers.build_user_profile_context(self.get_profile(), self.request.user))
        return context

    def form_valid(self, form):
        controllers.update_user_profile(self.get_profile(), form.cleaned_data)
        messages.success(self.request, self.success_message)
        return redirect("profile-settings")


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
            "board_fullscreen_mode": False,
            "board_fullscreen_querystring": "?fullscreen=1",
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

    def _get_requested_workflow_state(self):
        requested_state = self.request.GET.get("workflow_state")
        valid_states = {state.value for state in WorkflowState}
        if requested_state in valid_states:
            return requested_state
        return None

    def get_initial(self):
        initial = super().get_initial()
        requested_state = self._get_requested_workflow_state()
        if requested_state:
            initial["workflow_state"] = requested_state
        initial["attachment_draft_token"] = _get_issue_create_draft_token(self.request)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["show_workflow_state"] = self._get_requested_workflow_state() is not None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        context.update({
            "active_nav": "create-issue",
            "issue": None,
            "issue_create_draft_token": _get_issue_create_draft_token(self.request),
            "issue_description_templates": form.get_description_template_metadata() if form else [],
            "form_title": _("Create New Issue"),
            "submit_label": _("Create issue"),
        })
        return context

    def form_valid(self, form):
        issue = controllers.create_issue(form.cleaned_data, self.request.user)
        _clear_issue_create_draft_token(self.request)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(self.request, _("Issue %(issue_number)s was created.") % {"issue_number": issue.issue_number})
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
            "form_title": _("Update Existing Issue"),
            "submit_label": _("Save changes"),
        })
        return context

    def form_valid(self, form):
        issue = controllers.update_issue(self.get_issue(), form.cleaned_data, self.request.user)
        board_event_broker.publish("kanban.board.updated", {"scope": "board"})
        messages.success(self.request, _("Issue %(issue_number)s was updated.") % {"issue_number": issue.issue_number})
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
        messages.success(
            self.request, _("Issue %(issue_number)s description was updated.") % {"issue_number": issue.issue_number}
        )
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
        messages.success(self.request, _("Issue %(issue_number)s was archived.") % {"issue_number": issue.issue_number})
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
        messages.success(
            self.request, _("A new issue comment was added to %(issue_number)s.") % {"issue_number": issue.issue_number}
        )
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
        messages.success(
            request,
            _("Attachment %(attachment_name)s was removed from %(issue_number)s.")
            % {"attachment_name": attachment_name, "issue_number": issue.issue_number},
        )
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
