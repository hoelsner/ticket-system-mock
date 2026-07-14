import hashlib
import hmac
import json
import logging
import ssl
import threading
import time
from urllib import error, parse, request

from django.db import close_old_connections
from django.utils import timezone

from djangoapp.core.models import WebhookDeliveryAttempt, WebhookDeliveryStatus, WebhookEndpoint, WebhookEvent

logger = logging.getLogger(__name__)


class WebhookDeliveryController:
    @staticmethod
    def dispatch_event_async(webhook_event_id):
        worker = threading.Thread(
            target=WebhookDeliveryController._deliver_event_in_thread,
            args=(str(webhook_event_id),),
            daemon=True,
        )
        worker.start()

    @staticmethod
    def process_pending_events():
        processed_event_ids = []
        queryset = WebhookEvent.objects.exclude(delivery_status=WebhookDeliveryStatus.SUCCESS).order_by("occurred_at")
        for webhook_event in queryset:
            attempted = WebhookDeliveryController.deliver_event(webhook_event.pk)
            if attempted:
                processed_event_ids.append(str(webhook_event.pk))
        return processed_event_ids

    @staticmethod
    def deliver_event(webhook_event_id):
        webhook_event = WebhookEvent.objects.get(pk=webhook_event_id)
        attempted = False

        for webhook_endpoint in WebhookDeliveryController._get_target_endpoints(webhook_event):
            if not WebhookDeliveryController._should_attempt_delivery(webhook_event, webhook_endpoint):
                continue

            attempted = True
            WebhookDeliveryController._deliver_to_endpoint(webhook_event, webhook_endpoint)

        WebhookDeliveryController._refresh_event_delivery_status(webhook_event)
        return attempted

    @staticmethod
    def _deliver_event_in_thread(webhook_event_id):
        close_old_connections()
        try:
            WebhookDeliveryController.deliver_event(webhook_event_id)
        except Exception:
            logger.exception("Webhook delivery failed for event %s", webhook_event_id)
        finally:
            close_old_connections()

    @staticmethod
    def _get_target_endpoints(webhook_event):
        if not webhook_event.target_endpoint_ids:
            return []

        endpoints_by_id = WebhookDeliveryController._get_enabled_target_endpoints_by_id(webhook_event)
        return WebhookDeliveryController._get_ordered_target_endpoints(
            webhook_event.target_endpoint_ids,
            endpoints_by_id,
        )

    @staticmethod
    def _should_attempt_delivery(webhook_event, webhook_endpoint):
        latest_attempt = WebhookDeliveryController._get_latest_attempt(webhook_event, webhook_endpoint)
        if latest_attempt is None:
            return True

        if latest_attempt.success:
            return False

        if latest_attempt.attempt_number >= webhook_endpoint.max_retries + 1:
            return False

        retry_at = latest_attempt.attempted_at + timezone.timedelta(seconds=webhook_endpoint.retry_backoff_seconds)
        return retry_at <= timezone.now()

    @staticmethod
    def _deliver_to_endpoint(webhook_event, webhook_endpoint):
        request_body = json.dumps(webhook_event.payload, sort_keys=True).encode("utf-8")
        timestamp = str(int(time.time()))
        request_headers = WebhookDeliveryController._build_request_headers(
            webhook_event,
            webhook_endpoint,
            request_body,
            timestamp,
        )
        latest_attempt = WebhookDeliveryController._get_latest_attempt(webhook_event, webhook_endpoint)
        attempt_number = WebhookDeliveryController._get_attempt_number(latest_attempt)

        started_at = time.monotonic()
        status_code = None
        response_body = ""
        error_message = ""
        success = False

        WebhookDeliveryController._validate_target_url(webhook_endpoint.target_url)
        http_request = WebhookDeliveryController._build_http_request(
            webhook_endpoint,
            request_body,
            request_headers,
        )
        urlopen_kwargs = WebhookDeliveryController._build_urlopen_kwargs(webhook_endpoint)

        try:
            with request.urlopen(http_request, **urlopen_kwargs) as response:  # nosec B310
                status_code = response.status
                response_body = response.read().decode("utf-8", errors="replace")
                success = 200 <= status_code < 300
        except error.HTTPError as exc:
            status_code = exc.code
            response_body = exc.read().decode("utf-8", errors="replace")
            error_message = str(exc)
        except Exception as exc:
            error_message = str(exc)

        duration_ms = int((time.monotonic() - started_at) * 1000)

        WebhookDeliveryController._create_delivery_attempt(
            webhook_endpoint,
            webhook_event,
            attempt_number,
            request_headers,
            request_body,
            status_code,
            response_body,
            error_message,
            success,
            duration_ms,
        )

        WebhookDeliveryController._update_endpoint_delivery_status(webhook_endpoint, success)

        if not success:
            logger.warning(
                "Webhook delivery failed for event %s to endpoint %s with status %s",
                webhook_event.pk,
                webhook_endpoint.pk,
                status_code,
            )

    @staticmethod
    def _build_request_headers(webhook_event, webhook_endpoint, request_body, timestamp):
        request_headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": webhook_event.event_type,
            "X-Webhook-Event-Id": str(webhook_event.pk),
            "X-Webhook-Timestamp": timestamp,
        }
        if webhook_endpoint.secret:
            request_headers["X-Webhook-Signature"] = WebhookDeliveryController._sign_payload(
                webhook_endpoint.secret,
                timestamp,
                request_body,
            )
        return request_headers

    @staticmethod
    def _get_attempt_number(latest_attempt):
        if latest_attempt is None:
            return 1
        return latest_attempt.attempt_number + 1

    @staticmethod
    def _build_http_request(webhook_endpoint, request_body, request_headers):
        return request.Request(
            webhook_endpoint.target_url,
            data=request_body,
            headers=request_headers,
            method="POST",
        )

    @staticmethod
    def _build_urlopen_kwargs(webhook_endpoint):
        urlopen_kwargs = {"timeout": webhook_endpoint.timeout_seconds}
        if webhook_endpoint.disable_ssl_certificate_validation:
            urlopen_kwargs["context"] = WebhookDeliveryController._build_unverified_ssl_context()
        return urlopen_kwargs

    @staticmethod
    def _build_unverified_ssl_context():
        return ssl._create_unverified_context()  # nosec B323,B501

    @staticmethod
    def _create_delivery_attempt(
        webhook_endpoint,
        webhook_event,
        attempt_number,
        request_headers,
        request_body,
        status_code,
        response_body,
        error_message,
        success,
        duration_ms,
    ):
        WebhookDeliveryAttempt.objects.create(
            webhook_endpoint=webhook_endpoint,
            webhook_event=webhook_event,
            attempt_number=attempt_number,
            request_headers=request_headers,
            request_body=request_body.decode("utf-8"),
            response_status_code=status_code,
            response_body=response_body,
            error_message=error_message,
            success=success,
            duration_ms=duration_ms,
        )

    @staticmethod
    def _update_endpoint_delivery_status(webhook_endpoint, success):
        webhook_endpoint.last_delivery_status = WebhookDeliveryController._status_from_success(success)
        webhook_endpoint.last_delivery_attempt_at = timezone.now()
        webhook_endpoint.save(update_fields=["last_delivery_status", "last_delivery_attempt_at", "updated_at"])

    @staticmethod
    def _refresh_event_delivery_status(webhook_event):
        target_endpoints = WebhookDeliveryController._get_target_endpoints(webhook_event)
        if not target_endpoints:
            webhook_event.delivery_status = WebhookDeliveryStatus.SUCCESS
            webhook_event.save(update_fields=["delivery_status"])
            return

        successful_endpoint_ids = WebhookDeliveryController._get_successful_endpoint_ids(
            webhook_event,
            target_endpoints,
        )
        webhook_event.delivery_status = WebhookDeliveryController._determine_delivery_status(
            webhook_event,
            target_endpoints,
            successful_endpoint_ids,
        )
        webhook_event.save(update_fields=["delivery_status"])

    @staticmethod
    def _sign_payload(secret, timestamp, request_body):
        digest = hmac.new(
            secret.encode("utf-8"),
            f"{timestamp}.".encode("utf-8") + request_body,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"

    @staticmethod
    def _status_from_success(success):
        if success:
            return WebhookDeliveryStatus.SUCCESS
        return WebhookDeliveryStatus.FAILED

    @staticmethod
    def _get_successful_endpoint_ids(webhook_event, target_endpoints):
        return set(
            webhook_event.delivery_attempts.filter(
                success=True, webhook_endpoint_id__in=[endpoint.pk for endpoint in target_endpoints]
            ).values_list("webhook_endpoint_id", flat=True)
        )

    @staticmethod
    def _determine_delivery_status(webhook_event, target_endpoints, successful_endpoint_ids):
        if WebhookDeliveryController._all_target_endpoints_succeeded(target_endpoints, successful_endpoint_ids):
            return WebhookDeliveryStatus.SUCCESS

        remaining_endpoints = WebhookDeliveryController._get_remaining_endpoints(
            target_endpoints,
            successful_endpoint_ids,
        )
        if WebhookDeliveryController._remaining_endpoints_are_exhausted(
            webhook_event,
            remaining_endpoints,
        ):
            return WebhookDeliveryStatus.FAILED

        if WebhookDeliveryController._has_attempts_for_target_endpoints(webhook_event, target_endpoints):
            return WebhookDeliveryStatus.PARTIAL_FAILURE

        return WebhookDeliveryStatus.PENDING

    @staticmethod
    def _all_remaining_endpoints_exhausted(webhook_event, remaining_endpoints):
        return all(
            WebhookDeliveryController._is_endpoint_exhausted(webhook_event, endpoint)
            for endpoint in remaining_endpoints
        )

    @staticmethod
    def _get_latest_attempt(webhook_event, webhook_endpoint):
        return (
            webhook_event.delivery_attempts
            .filter(webhook_endpoint=webhook_endpoint)
            .order_by("-attempt_number")
            .first()
        )

    @staticmethod
    def _get_enabled_target_endpoints_by_id(webhook_event):
        return {
            endpoint.pk: endpoint
            for endpoint in WebhookEndpoint.objects.filter(pk__in=webhook_event.target_endpoint_ids, enabled=True)
        }

    @staticmethod
    def _get_ordered_target_endpoints(target_endpoint_ids, endpoints_by_id):
        return [endpoints_by_id[endpoint_id] for endpoint_id in target_endpoint_ids if endpoint_id in endpoints_by_id]

    @staticmethod
    def _all_target_endpoints_succeeded(target_endpoints, successful_endpoint_ids):
        return len(successful_endpoint_ids) == len(target_endpoints)

    @staticmethod
    def _get_remaining_endpoints(target_endpoints, successful_endpoint_ids):
        return [endpoint for endpoint in target_endpoints if endpoint.pk not in successful_endpoint_ids]

    @staticmethod
    def _remaining_endpoints_are_exhausted(webhook_event, remaining_endpoints):
        if not remaining_endpoints:
            return False
        return WebhookDeliveryController._all_remaining_endpoints_exhausted(webhook_event, remaining_endpoints)

    @staticmethod
    def _has_attempts_for_target_endpoints(webhook_event, target_endpoints):
        return webhook_event.delivery_attempts.filter(
            webhook_endpoint_id__in=[endpoint.pk for endpoint in target_endpoints]
        ).exists()

    @staticmethod
    def _validate_target_url(target_url):
        parsed_url = parse.urlsplit(target_url)
        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError("Webhook target URLs must use http or https.")

    @staticmethod
    def _is_endpoint_exhausted(webhook_event, webhook_endpoint):
        latest_attempt = WebhookDeliveryController._get_latest_attempt(webhook_event, webhook_endpoint)
        if latest_attempt is None or latest_attempt.success:
            return False
        return latest_attempt.attempt_number >= webhook_endpoint.max_retries + 1
