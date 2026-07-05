from __future__ import annotations

import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from goal_cli.config import load_config
from goal_cli.observability import LocalJsonlSpanExporter, plan_observability_export


class ObservabilityTests(unittest.TestCase):
    def test_unreachable_default_otlp_endpoint_uses_local_jsonl_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, "http://127.0.0.1:9/v1/traces"))

            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", None)
                os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
                plan = plan_observability_export(config)

            self.assertEqual(plan.kind, "local_jsonl")
            self.assertEqual(plan.path, config.state_dir / "observability" / "traces.jsonl")
            self.assertIn("OTLP receiver unavailable", plan.reason)

    def test_explicit_otlp_environment_endpoint_is_respected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, "http://127.0.0.1:9/v1/traces"))

            with mock.patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": "http://127.0.0.1:9/v1/traces"}):
                plan = plan_observability_export(config)

            self.assertEqual(plan.kind, "otlp")
            self.assertIsNone(plan.path)

    def test_jsonl_exporter_writes_agent_readable_spans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            trace_path = Path(temp_dir) / ".goal" / "observability" / "traces.jsonl"

            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor

            provider = TracerProvider()
            provider.add_span_processor(SimpleSpanProcessor(LocalJsonlSpanExporter(trace_path)))
            tracer = provider.get_tracer("goal_cli.tests")
            with tracer.start_as_current_span("goal_cli.test", attributes={"goal.iteration": 2}) as span:
                span.add_event("checkpoint", {"phase": "tok"})
            provider.shutdown()

            lines = trace_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["name"], "goal_cli.test")
            self.assertEqual(payload["attributes"]["goal.iteration"], 2)
            self.assertEqual(payload["events"][0]["name"], "checkpoint")
            self.assertEqual(payload["events"][0]["attributes"]["phase"], "tok")
            self.assertRegex(payload["context"]["trace_id"], r"^[0-9a-f]{32}$")

    def _write_project(self, root: Path, endpoint: str) -> Path:
        (root / "src").mkdir()
        (root / "output").mkdir()
        config = f"""
name = "observability-test"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact.txt"

[producer]
command = "true"

[tik]
provider = "oracle"
command = "true"

[tik.prompt]
text = "Evaluate {{artifact_path}}."

[tok]
provider = "codex_goal"
write_dirs = ["src"]
sandbox = "workspace-write"

[tok.prompt]
template = "Goal {{goal_name}} verdict {{tik_ledger}}"

[no_mistakes]
enabled = false

[observability]
endpoint = {json.dumps(endpoint)}
timeout_seconds = 0.01

[safety]
generated_dirs = ["output", "build"]
"""
        config_path = root / "goal.toml"
        config_path.write_text(textwrap.dedent(config).strip() + "\n", encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
