import time
import uuid
from dataclasses import dataclass
from urllib import error, request

from django.core.cache import caches
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils.translation import gettext_lazy as _
from djangoapp.core.models import WebhookEndpoint


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    status: str
    duration_ms: int
    message: str | None = None
    exception_type: str | None = None

    def to_dict(self):
        payload = {
            "status": self.status,
            "duration_ms": self.duration_ms,
        }
        if self.message:
            payload["message"] = self.message
        return payload


@dataclass(frozen=True)
class HealthCheckSummary:
    status: str
    duration_ms: int
    checks: dict[str, HealthCheckResult]

    def to_dict(self):
        return {
            "status": self.status,
            "duration_ms": self.duration_ms,
            "checks": {name: result.to_dict() for name, result in self.checks.items()},
        }


class HealthcheckService:
    CHECK_NAMES = ("database", "migrations", "cache", "webhooks")

    @staticmethod
    def run_all_checks():
        started_at = time.perf_counter()
        checks = {check_name: HealthcheckService.run_check(check_name) for check_name in HealthcheckService.CHECK_NAMES}
        return HealthCheckSummary(
            status=HealthcheckService._overall_status(checks),
            duration_ms=HealthcheckService._duration_ms(started_at),
            checks=checks,
        )

    @staticmethod
    def run_check(check_name):
        check_map = {
            "database": HealthcheckService.run_database_check,
            "migrations": HealthcheckService.run_migration_check,
            "cache": HealthcheckService.run_cache_check,
            "webhooks": HealthcheckService.run_webhook_check,
        }
        return check_map[check_name]()

    @staticmethod
    def run_database_check():
        started_at = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as exc:
            return HealthcheckService._unhealthy_result(
                "database",
                started_at,
                _("Database connectivity check failed."),
                exc,
            )
        return HealthcheckService._healthy_result("database", started_at)

    @staticmethod
    def run_migration_check():
        started_at = time.perf_counter()
        try:
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        except Exception as exc:
            return HealthcheckService._unhealthy_result(
                "migrations",
                started_at,
                _("Migration status check failed."),
                exc,
            )

        if plan:
            return HealthcheckService._unhealthy_result(
                "migrations",
                started_at,
                _("Pending migrations detected."),
            )

        return HealthcheckService._healthy_result("migrations", started_at)

    @staticmethod
    def run_cache_check():
        started_at = time.perf_counter()
        cache = caches["default"]
        cache_key = f"healthchecks:cache:{uuid.uuid4()}"
        expected_value = uuid.uuid4().hex

        try:
            cache.set(cache_key, expected_value, timeout=5)
            cached_value = cache.get(cache_key)
        except Exception as exc:
            return HealthcheckService._unhealthy_result(
                "cache",
                started_at,
                _("Cache connectivity check failed."),
                exc,
            )
        finally:
            try:
                cache.delete(cache_key)
            except Exception:
                pass

        if cached_value != expected_value:
            return HealthcheckService._unhealthy_result(
                "cache",
                started_at,
                _("Cache read/write verification failed."),
            )

        return HealthcheckService._healthy_result("cache", started_at)

    @staticmethod
    def run_webhook_check():
        started_at = time.perf_counter()
        enabled_endpoints = list(WebhookEndpoint.objects.filter(enabled=True).order_by("name"))
        enabled_endpoint_count = len(enabled_endpoints)

        if enabled_endpoint_count == 0:
            return HealthcheckService._warning_result(
                "webhooks",
                started_at,
                _("No enabled webhook endpoints are configured."),
            )

        unreachable_endpoint_names = [
            endpoint.name
            for endpoint in enabled_endpoints
            if not HealthcheckService._is_webhook_endpoint_reachable(endpoint)
        ]

        if unreachable_endpoint_names:
            return HealthcheckService._unhealthy_result(
                "webhooks",
                started_at,
                _("Webhook endpoints unreachable: %(endpoint_names)s.")
                % {"endpoint_names": ", ".join(unreachable_endpoint_names)},
            )

        return HealthCheckResult(
            name="webhooks",
            status="healthy",
            duration_ms=HealthcheckService._duration_ms(started_at),
            message=_("%(endpoint_count)s enabled webhook endpoint reachable.")
            % {"endpoint_count": enabled_endpoint_count}
            if enabled_endpoint_count == 1
            else _("%(endpoint_count)s enabled webhook endpoints reachable.")
            % {"endpoint_count": enabled_endpoint_count},
        )

    @staticmethod
    def _is_webhook_endpoint_reachable(webhook_endpoint):
        http_request = request.Request(
            webhook_endpoint.target_url,
            method="HEAD",
        )

        try:
            with request.urlopen(http_request, timeout=webhook_endpoint.timeout_seconds):  # nosec B310
                return True
        except error.HTTPError:
            return True
        except Exception:
            return False

    @staticmethod
    def _healthy_result(name, started_at):
        return HealthCheckResult(
            name=name,
            status="healthy",
            duration_ms=HealthcheckService._duration_ms(started_at),
        )

    @staticmethod
    def _unhealthy_result(name, started_at, message, exc=None):
        return HealthCheckResult(
            name=name,
            status="unhealthy",
            duration_ms=HealthcheckService._duration_ms(started_at),
            message=message,
            exception_type=type(exc).__name__ if exc is not None else None,
        )

    @staticmethod
    def _warning_result(name, started_at, message):
        return HealthCheckResult(
            name=name,
            status="warning",
            duration_ms=HealthcheckService._duration_ms(started_at),
            message=message,
        )

    @staticmethod
    def _duration_ms(started_at):
        return max(0, int((time.perf_counter() - started_at) * 1000))

    @staticmethod
    def _overall_status(checks):
        if any(result.status == "unhealthy" for result in checks.values()):
            return "unhealthy"
        if any(result.status == "warning" for result in checks.values()):
            return "warning"
        if all(result.status == "healthy" for result in checks.values()):
            return "healthy"
        return "warning"
