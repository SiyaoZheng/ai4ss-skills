from __future__ import annotations

import atexit
import importlib.metadata
import json
import os
import socket
import threading
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, cast
from urllib.parse import urlparse

from .config import GoalConfig


_INITIALIZED = False
_PROVIDER: Any | None = None
_TRACER: Any | None = None
_OTLP_CONNECT_TIMEOUT_SECONDS = 0.5


@dataclass(frozen=True)
class GoalTelemetry:
    enabled: bool
    reason: str = ""
    tracer: Any | None = None
    exporter: str = "none"
    trace_path: Path | None = None

    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        if not self.enabled or self.tracer is None:
            return nullcontext(_NoopSpan())
        return _span(self.tracer, name, attributes or {})

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        if not self.enabled:
            return
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and span.is_recording():
                span.add_event(name, _otel_attributes(attributes or {}))
        except Exception:
            return

    def pulse(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        if not self.enabled or self.tracer is None:
            return
        try:
            with _span(self.tracer, name, attributes or {}):
                pass
            self.flush()
        except Exception:
            return

    def flush(self) -> None:
        if not self.enabled or _PROVIDER is None:
            return
        try:
            _PROVIDER.force_flush()
        except Exception:
            return


class _NoopSpan:
    def set_attribute(self, key: str, value: Any) -> None:
        return None

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        return None

    def record_exception(self, exception: BaseException) -> None:
        return None

    def set_status(self, status: Any) -> None:
        return None


def disabled_telemetry(reason: str = "disabled") -> GoalTelemetry:
    return GoalTelemetry(False, reason, None)


@dataclass(frozen=True)
class TelemetryExportPlan:
    kind: str
    reason: str = ""
    path: Path | None = None
    endpoint: str = ""
    host: str | None = None
    port: int | None = None
    endpoint_valid: bool = True
    reachable: bool = False
    explicit_env: bool = False


def configure_observability(config: GoalConfig) -> GoalTelemetry:
    if not config.observability.enabled:
        return disabled_telemetry("disabled by config")
    if _otel_disabled_by_env():
        return disabled_telemetry("disabled by OpenTelemetry environment")

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter
    except ImportError as exc:
        return disabled_telemetry(f"OpenTelemetry package missing: {exc}")

    global _INITIALIZED, _PROVIDER, _TRACER
    plan = plan_observability_export(config)
    if not _INITIALIZED:
        resource = Resource.create(
            {
                "service.name": os.environ.get("OTEL_SERVICE_NAME") or config.observability.service_name,
                "service.version": _package_version(),
                "goal.name": config.name,
                "goal.root": str(config.root),
                "goal.config": str(config.path),
                "goal.observability.exporter": plan.kind,
                "goal.observability.local_path": str(plan.path or ""),
            }
        )
        provider = TracerProvider(resource=resource)
        if plan.kind == "local_jsonl":
            exporter: SpanExporter = cast(SpanExporter, LocalJsonlSpanExporter(plan.path or _local_trace_path(config)))
            provider.add_span_processor(SimpleSpanProcessor(exporter))
        else:
            exporter = OTLPSpanExporter(**_exporter_kwargs(config))
            provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _PROVIDER = provider
        _TRACER = trace.get_tracer("goal_cli")
        _INITIALIZED = True
        atexit.register(_shutdown_provider)
    return GoalTelemetry(True, plan.reason, _TRACER or trace.get_tracer("goal_cli"), plan.kind, plan.path)


def set_span_attributes(span: Any, attributes: dict[str, Any]) -> None:
    for key, value in _otel_attributes(attributes).items():
        span.set_attribute(key, value)


def record_exception(span: Any, exception: BaseException) -> None:
    try:
        from opentelemetry.trace import Status, StatusCode

        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))
    except Exception:
        return


def record_run_result(span: Any, result: Any) -> None:
    set_span_attributes(
        span,
        {
            "goal.result.exit_code": getattr(result, "exit_code", None),
            "goal.result.status": getattr(result, "status", None),
            "goal.result.run_dir": str(getattr(result, "run_dir", "") or ""),
            "goal.result.message": getattr(result, "message", None),
        },
    )
    if getattr(result, "exit_code", 0) != 0:
        _mark_error(span, str(getattr(result, "message", None) or getattr(result, "status", "failed")))


def record_no_mistakes_result(span: Any, result: Any) -> None:
    set_span_attributes(
        span,
        {
            "goal.no_mistakes.ok": getattr(result, "ok", None),
            "goal.no_mistakes.status": getattr(result, "status", None),
            "goal.no_mistakes.detail": getattr(result, "detail", None),
            "goal.no_mistakes.repo_root": str(getattr(result, "repo_root", "") or ""),
            "goal.no_mistakes.branch": getattr(result, "branch", None),
            "goal.no_mistakes.commit": getattr(result, "commit", None),
            "goal.no_mistakes.log_path": str(getattr(result, "log_path", "") or ""),
            "goal.no_mistakes.skipped": getattr(result, "skipped", None),
        },
    )
    if getattr(result, "ok", True) is not True:
        _mark_error(span, getattr(result, "detail", None) or "no-mistakes failed")


@contextmanager
def _span(tracer: Any, name: str, attributes: dict[str, Any]) -> Iterator[Any]:
    with tracer.start_as_current_span(name, attributes=_otel_attributes(attributes)) as span:
        try:
            yield span
        except BaseException as exc:
            record_exception(span, exc)
            raise


def _exporter_kwargs(config: GoalConfig) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if not os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") and not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        kwargs["endpoint"] = config.observability.endpoint
    if not os.environ.get("OTEL_EXPORTER_OTLP_TRACES_TIMEOUT") and not os.environ.get("OTEL_EXPORTER_OTLP_TIMEOUT"):
        kwargs["timeout"] = config.observability.timeout_seconds
    return kwargs


def plan_observability_export(
    config: GoalConfig,
    connect_probe: Any | None = None,
    timeout_seconds: float | None = None,
) -> TelemetryExportPlan:
    endpoint = effective_observability_endpoint(config)
    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    endpoint_valid = parsed.scheme in {"http", "https"} and host is not None
    explicit_env = _explicit_otlp_endpoint_from_env()
    if explicit_env:
        return TelemetryExportPlan(
            "otlp",
            "using OpenTelemetry endpoint from environment",
            endpoint=endpoint,
            host=host,
            port=port if endpoint_valid else None,
            endpoint_valid=endpoint_valid,
            explicit_env=True,
        )
    if not endpoint_valid:
        path = _local_trace_path(config)
        return TelemetryExportPlan(
            "local_jsonl",
            f"invalid OTLP HTTP endpoint {endpoint}; writing local traces to {path}",
            path,
            endpoint=endpoint,
            endpoint_valid=False,
        )
    timeout = timeout_seconds if timeout_seconds is not None else min(config.observability.timeout_seconds, _OTLP_CONNECT_TIMEOUT_SECONDS)
    reachable = _endpoint_reachable(endpoint, max(timeout, 0.001), connect_probe=connect_probe)
    if reachable:
        return TelemetryExportPlan(
            "otlp",
            f"OTLP receiver is reachable at {endpoint}",
            endpoint=endpoint,
            host=host,
            port=port,
            reachable=True,
        )
    path = _local_trace_path(config)
    return TelemetryExportPlan(
        "local_jsonl",
        f"OTLP receiver unavailable at {endpoint}; writing local traces to {path}",
        path,
        endpoint=endpoint,
        host=host,
        port=port,
        reachable=False,
    )


def effective_observability_endpoint(config: GoalConfig) -> str:
    return (
        os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        or config.observability.endpoint
    )


def _explicit_otlp_endpoint_from_env() -> bool:
    return bool(os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))


def _endpoint_reachable(endpoint: str, timeout_seconds: float, connect_probe: Any | None = None) -> bool:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if connect_probe is not None:
        return bool(connect_probe(parsed.hostname, port, timeout_seconds))
    try:
        with socket.create_connection((parsed.hostname, port), timeout=max(timeout_seconds, 0.001)):
            return True
    except OSError:
        return False


def _local_trace_path(config: GoalConfig) -> Path:
    return config.state_dir / "observability" / "traces.jsonl"


class LocalJsonlSpanExporter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()

    def export(self, spans: Any) -> Any:
        from opentelemetry.sdk.trace.export import SpanExportResult

        if not spans:
            return SpanExportResult.SUCCESS
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as trace_file:
                for span in spans:
                    trace_file.write(json.dumps(_span_to_json(span), ensure_ascii=False, sort_keys=True, default=str) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def _span_to_json(span: Any) -> dict[str, Any]:
    context = span.get_span_context()
    parent = getattr(span, "parent", None)
    return {
        "name": span.name,
        "context": {
            "trace_id": format(context.trace_id, "032x"),
            "span_id": format(context.span_id, "016x"),
            "trace_flags": int(context.trace_flags),
        },
        "parent": None
        if parent is None
        else {
            "span_id": format(parent.span_id, "016x"),
        },
        "start_time_unix_nano": span.start_time,
        "end_time_unix_nano": span.end_time,
        "status": _status_to_json(span.status),
        "attributes": _mapping_to_json(getattr(span, "attributes", {}) or {}),
        "events": [_event_to_json(event) for event in getattr(span, "events", ())],
        "resource": _mapping_to_json(getattr(getattr(span, "resource", None), "attributes", {}) or {}),
    }


def _status_to_json(status: Any) -> dict[str, Any]:
    status_code = getattr(status, "status_code", None)
    return {
        "status_code": getattr(status_code, "name", str(status_code)),
        "description": getattr(status, "description", None),
    }


def _event_to_json(event: Any) -> dict[str, Any]:
    return {
        "name": event.name,
        "timestamp_unix_nano": event.timestamp,
        "attributes": _mapping_to_json(getattr(event, "attributes", {}) or {}),
    }


def _mapping_to_json(mapping: Any) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in dict(mapping).items():
        converted = _attribute_value(value)
        if converted is not None:
            cleaned[str(key)] = converted
    return cleaned


def _otel_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in attributes.items():
        converted = _attribute_value(value)
        if converted is not None:
            cleaned[key] = converted
    return cleaned


def _attribute_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)) and all(isinstance(item, (str, bool, int, float)) for item in value):
        return list(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _mark_error(span: Any, description: str) -> None:
    try:
        from opentelemetry.trace import Status, StatusCode

        span.set_status(Status(StatusCode.ERROR, description))
    except Exception:
        return


def _otel_disabled_by_env() -> bool:
    if os.environ.get("OTEL_SDK_DISABLED", "").lower() == "true":
        return True
    traces_exporter = os.environ.get("OTEL_TRACES_EXPORTER", "").lower()
    return traces_exporter == "none"


def _package_version() -> str:
    try:
        return importlib.metadata.version("goal-cli")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0+local"


def _shutdown_provider() -> None:
    if _PROVIDER is None:
        return
    try:
        _PROVIDER.shutdown()
    except Exception:
        return
