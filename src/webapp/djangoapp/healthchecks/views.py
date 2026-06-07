import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.template.response import TemplateResponse
from django.views import View
from django.views.generic import TemplateView

from .checks import HealthcheckService

logger = logging.getLogger(__name__)

CHECK_LABELS = {
    "database": "Database",
    "migrations": "Migrations",
    "cache": "Cache",
    "webhooks": "Webhook endpoints",
}

CHECK_SEQUENCE = ("database", "migrations", "cache", "webhooks")


def _response_status(summary):
    if summary.status in {"healthy", "warning"}:
        return 200
    return 503


def _log_unhealthy_summary(summary, request_path):
    for check_name, result in summary.checks.items():
        if result.status == "healthy":
            continue

        log_method = logger.error if result.exception_type else logger.warning
        log_method(
            "healthcheck failed status=%s check=%s reason=%s exception_type=%s check_duration_ms=%s total_duration_ms=%s path=%s",
            summary.status,
            check_name,
            result.message,
            result.exception_type,
            result.duration_ms,
            summary.duration_ms,
            request_path,
        )


class HealthcheckApiView(View):
    def get(self, request, *args, **kwargs):
        summary = HealthcheckService.run_all_checks()
        if summary.status != "healthy":
            _log_unhealthy_summary(summary, request.path)
        return JsonResponse(summary.to_dict(), status=_response_status(summary))


class FrontendAccessMixin(LoginRequiredMixin):
    pass


class HealthcheckStatusView(FrontendAccessMixin, TemplateView):
    template_name = "healthchecks/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_nav"] = "healthcheck"
        context["check_names"] = CHECK_SEQUENCE
        return context


class HealthcheckSummaryPartialView(FrontendAccessMixin, View):
    def get(self, request, *args, **kwargs):
        summary = HealthcheckService.run_all_checks()
        if summary.status != "healthy":
            _log_unhealthy_summary(summary, request.path)
        return TemplateResponse(
            request,
            "healthchecks/partials/summary.html",
            {"summary": summary},
        )


class HealthcheckCheckPartialView(FrontendAccessMixin, View):
    def get(self, request, *args, **kwargs):
        check_name = kwargs["check_name"]
        if check_name not in CHECK_LABELS:
            raise Http404("Unknown healthcheck.")

        result = HealthcheckService.run_check(check_name)
        if result.status != "healthy":
            summary = type(
                "HealthSummary",
                (),
                {
                    "status": "unhealthy",
                    "duration_ms": result.duration_ms,
                    "checks": {check_name: result},
                },
            )()
            _log_unhealthy_summary(summary, request.path)

        response = TemplateResponse(
            request,
            "healthchecks/partials/check_card.html",
            {
                "check_name": check_name,
                "check_label": CHECK_LABELS[check_name],
                "result": result,
            },
        )
        next_event = _next_check_event(check_name)
        if next_event:
            response.headers["HX-Trigger"] = next_event
        return response


def _next_check_event(check_name):
    try:
        current_index = CHECK_SEQUENCE.index(check_name)
    except ValueError:
        return None

    if current_index + 1 >= len(CHECK_SEQUENCE):
        return "healthcheck:run-summary"

    return f"healthcheck:run-{CHECK_SEQUENCE[current_index + 1]}"
