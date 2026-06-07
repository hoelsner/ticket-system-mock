from django.urls import path

from .views import (
    HealthcheckApiView,
    HealthcheckCheckPartialView,
    HealthcheckStatusView,
    HealthcheckSummaryPartialView,
)

urlpatterns = [
    path("", HealthcheckApiView.as_view(), name="healthcheck-api"),
    path("status/", HealthcheckStatusView.as_view(), name="healthcheck-status"),
    path("status/summary/", HealthcheckSummaryPartialView.as_view(), name="healthcheck-status-summary"),
    path("status/<slug:check_name>/", HealthcheckCheckPartialView.as_view(), name="healthcheck-status-check"),
]
