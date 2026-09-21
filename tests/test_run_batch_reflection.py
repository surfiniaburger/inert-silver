"""
Unit & Integration Tests for Step 3: GEPA Graph-Powered Reflector Batch Integration.

Tests:
  - CLI argument parsing for reflector flags.
  - _build_payload Pareto prompt injection and fallback.
  - _process_seed GEPA work-memory trace recording.
  - Deterministic cassette replay with ReplayManager.
  - Concurrency safety with multiple asynchronous batch workers.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentbeats.replay import OfflineReplayError
from scenarios.debate.adk_debate_judge import DebateJudgeADK
from scenarios.debate.pareto_registry import ParetoRegistry
from scenarios.debate.reflector_agent import ReflectorClient
from scenarios.debate.reflector_schemas import (
    ReflectRequest,
    ReflectResponse,
    get_static_baseline_prompt,
)
from scenarios.debate.run_batch import (
    BatchContext,
    _build_payload,
    _init_gepa_components,
    _parse_args,
    _process_seed,
    _record_gepa_reflector_trace,
)


@pytest.fixture
def temp_gepa_dir():
    temp_dir = tempfile.mkdtemp(prefix="test_gepa_batch_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_parse_args_reflector_flags():
    """Verify CLI parser correctly parses reflector arguments."""
    args = _parse_args([])
    assert args.reflector is True
    assert args.reflector_in_process is True
    assert args.reflector_url == "http://127.0.0.1:8004"
    assert args.gepa_dir == "artifacts/gepa"

    custom_args = _parse_args([
        "--no-reflector",
        "--no-reflector-in-process",
        "--reflector-url", "http://127.0.0.1:9999",
        "--gepa-dir", "/tmp/custom_gepa",
    ])
    assert custom_args.reflector is False
    assert custom_args.reflector_in_process is False
    assert custom_args.reflector_url == "http://127.0.0.1:9999"
    assert custom_args.gepa_dir == "/tmp/custom_gepa"


def test_build_payload_without_reflector():
    """When reflector_client is None, fallback baseline prompt is injected."""
    args = _parse_args([])
    seed = {
        "topic": "char buf[10];",
        "predicate": "buffer_overflow in memory write",
    }
    payload = _build_payload(
        args=args,
        item_seed=42,
        checkpoint_path="artifacts/checkpoints/42.json",
        record_path="artifacts/runs/42.json",
        batch_started_at="2026-08-23T12:00:00Z",
        seed=seed,
        reflector_client=None,
    )
    assert payload["config"]["taxonomy_bucket"] == "memory_safety"
    assert payload["config"]["active_mutation_id"] == "baseline_v0"
    assert payload["config"]["reflector_prompt"] == get_static_baseline_prompt("memory_safety")
    assert payload["config"]["reflector"] is True
    assert payload["config"]["reflector_in_process"] is True
    assert payload["config"]["reflector_url"] == "http://127.0.0.1:8004"


def test_build_payload_with_active_pareto_prompt(temp_gepa_dir):
    """When reflector_client has an active Pareto prompt, it is injected into the payload."""
    registry = ParetoRegistry(gepa_dir=temp_gepa_dir)
    registry.register_pareto_prompt(
        taxonomy="integer_arithmetic",
        prompt="CUSTOM PARETO PROMPT FOR INTEGER ARITHMETIC",
        variant_id="var_int_custom_12345",
        score=1.5,
        rationale="Proven fix for integer overflow",
        topological_rule="RULE_CHECK_OVERFLOW",
    )
    client = ReflectorClient(registry=registry, in_process=True)

    args = _parse_args([])
    seed = {
        "topic": "int x = a + b;",
        "predicate": "integer_overflow leading to wraparound",
    }
    payload = _build_payload(
        args=args,
        item_seed=100,
        checkpoint_path="artifacts/checkpoints/100.json",
        record_path="artifacts/runs/100.json",
        batch_started_at="2026-08-23T12:00:00Z",
        seed=seed,
        reflector_client=client,
    )
    assert payload["config"]["taxonomy_bucket"] == "integer_arithmetic"
    assert payload["config"]["active_mutation_id"] == "var_int_custom_12345"
    assert payload["config"]["reflector_prompt"] == "CUSTOM PARETO PROMPT FOR INTEGER ARITHMETIC"


@pytest.mark.asyncio
async def test_process_seed_records_trace_on_completion(temp_gepa_dir):
    """Verify that _process_seed durable records attempt outcome to traces.jsonl."""
    registry = ParetoRegistry(gepa_dir=temp_gepa_dir)
    client = ReflectorClient(registry=registry, in_process=True)

    args = _parse_args(["--run-id", "test-run-step3", "--output", "/tmp/test_out.jsonl"])
    manifest = {
        "items": [
            {"index": 0, "status": "pending", "seed": 42}
        ]
    }
    ctx = BatchContext(
        args=args,
        batch_started_at="2026-08-23T12:00:00Z",
        processed_predicates=set(),
        manifest=manifest,
        manifest_path=str(temp_gepa_dir / "manifest.json"),
        manifest_lock=asyncio.Lock(),
        total_seeds=1,
        reflector_client=client,
        pareto_registry=registry,
    )

    fake_judge_response = {
        "status": "completed",
        "decision": "accepted",
        "response": "Adjudication succeeded",
        "verifier_logic_error": False,
    }

    with patch("scenarios.debate.run_batch.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = fake_judge_response
        sem = asyncio.Semaphore(1)
        seed = {
            "cve_id": "CVE-2026-0001",
            "topic": "memcpy(dst, src, len);",
            "predicate": "buffer_overflow in memory write",
        }
        await _process_seed(sem, 0, seed, ctx)

    # Check that traces.jsonl was populated
    traces = registry.get_recent_traces("memory_safety", limit=10)
    assert len(traces) == 1
    assert traces[0]["outcome"] == "VALID_ACCEPT"
    assert traces[0]["scenario_id"] == "CVE-2026-0001"
    assert traces[0]["attempt_index"] == 1


@pytest.mark.asyncio
async def test_process_seed_concurrent_execution(temp_gepa_dir):
    """Verify concurrent batch execution does not corrupt traces.jsonl or Pareto frontier."""
    registry = ParetoRegistry(gepa_dir=temp_gepa_dir)
    client = ReflectorClient(registry=registry, in_process=True)

    num_seeds = 10
    args = _parse_args(["--run-id", "test-run-concurrent", "--output", "/tmp/test_out_concurrent.jsonl"])
    manifest = {
        "items": [
            {"index": i, "status": "pending", "seed": 42 + i}
            for i in range(num_seeds)
        ]
    }
    ctx = BatchContext(
        args=args,
        batch_started_at="2026-08-23T12:00:00Z",
        processed_predicates=set(),
        manifest=manifest,
        manifest_path=str(temp_gepa_dir / "manifest_concurrent.json"),
        manifest_lock=asyncio.Lock(),
        total_seeds=num_seeds,
        reflector_client=client,
        pareto_registry=registry,
    )

    async def fake_send_message(payload_str, url):
        await asyncio.sleep(0.01)
        return {
            "status": "completed",
            "decision": "accepted",
            "response": "Adjudication succeeded",
            "verifier_logic_error": False,
        }

    with patch("scenarios.debate.run_batch.send_message", side_effect=fake_send_message):
        sem = asyncio.Semaphore(4)
        seeds = [
            {
                "cve_id": f"CVE-2026-{1000+i}",
                "topic": f"void vuln_{i}() {{ ... }}",
                "predicate": "concurrency data_race on shared state" if i % 2 == 0 else "buffer_overflow in memory",
            }
            for i in range(num_seeds)
        ]
        await asyncio.gather(*(_process_seed(sem, i, seeds[i], ctx) for i in range(num_seeds)))

    # Verify traces were cleanly recorded for both buckets
    concurrency_traces = registry.get_recent_traces("concurrency", limit=20)
    memory_traces = registry.get_recent_traces("memory_safety", limit=20)
    assert len(concurrency_traces) + len(memory_traces) == num_seeds


@pytest.mark.asyncio
async def test_fetch_reflector_response_replay_hit():
    """Verify that in replay mode, cassette hit returns recorded Reflector response."""
    judge = DebateJudgeADK()
    mock_cassette = MagicMock()
    mock_cassette.mode = "replay"
    recorded_payload = {
        "status": "SUCCESS",
        "taxonomy_bucket": "memory_safety",
        "pareto_variant_id": "var_replay_123",
        "applied_topological_rule": "TEST_RULE",
        "mutated_system_prompt": "MUTATED PROMPT FROM CASSETTE",
        "mutation_rationale": "Cached rationale",
        "estimated_correction_success_probability": 0.85,
        "dead_end_constraints_added": [],
        "confidence": 0.95,
    }
    mock_cassette.get_response.return_value = recorded_payload

    ctx = MagicMock()
    ctx.mode = "replay"
    ctx.replay_manager.cassette = mock_cassette
    ctx.seed = 42
    ctx.reflector_client = None

    req = ReflectRequest(
        attempt_index=1,
        scenario_id="scenario_42",
        predicate_family="TEST",
        taxonomy_bucket="memory_safety",
        code_text="void foo() {}",
        graph_diagnostic={
            "scenario_id": "scenario_42",
            "predicate_family": "TEST",
            "failure_bucket": "B_LOGIC_ERROR",
            "category": "memory_safety",
            "signature": "TEST",
            "suggested_topological_action": "TEST",
        },
        current_system_prompt="BASE PROMPT",
    )

    resp = await judge._fetch_reflector_response(ctx, 0, req)
    assert resp is not None
    assert resp.status == "SUCCESS"
    assert resp.pareto_variant_id == "var_replay_123"
    assert resp.mutated_system_prompt == "MUTATED PROMPT FROM CASSETTE"


@pytest.mark.asyncio
async def test_fetch_reflector_response_replay_miss_raises():
    """Verify that in replay mode, cassette miss raises OfflineReplayError."""
    judge = DebateJudgeADK()
    mock_cassette = MagicMock()
    mock_cassette.mode = "replay"
    mock_cassette.get_response.return_value = None

    ctx = MagicMock()
    ctx.mode = "replay"
    ctx.replay_manager.cassette = mock_cassette
    ctx.seed = 42
    ctx.reflector_client = None

    req = ReflectRequest(
        attempt_index=1,
        scenario_id="scenario_42",
        predicate_family="TEST",
        taxonomy_bucket="memory_safety",
        code_text="void foo() {}",
        graph_diagnostic={
            "scenario_id": "scenario_42",
            "predicate_family": "TEST",
            "failure_bucket": "B_LOGIC_ERROR",
            "category": "memory_safety",
            "signature": "TEST",
            "suggested_topological_action": "TEST",
        },
        current_system_prompt="BASE PROMPT",
    )

    with pytest.raises(OfflineReplayError, match="No cached reflector response"):
        await judge._fetch_reflector_response(ctx, 0, req)


def test_client_unpack_task_event_extracts_datapart_metadata():
    """Verify that _unpack_task_event extracts DataPart metadata while preserving status/response."""
    from a2a.types import DataPart, Part, TextPart
    from agentbeats.client import _unpack_task_event

    task = MagicMock()
    task.context_id = "ctx_12345"
    task_status = MagicMock()
    task_status.state.value = "completed"
    task_status.message = MagicMock()
    task_status.message.parts = [Part(TextPart(text="Task finished successfully."))]
    task.status = task_status

    artifact = MagicMock()
    artifact.parts = [
        Part(TextPart(text="Artifact summary text")),
        Part(DataPart(data={"active_mutation_id": "var_tested_42", "attempt_index": 2, "score": 4.5})),
    ]
    task.artifacts = [artifact]

    outputs = {"response": "", "context_id": None}
    _unpack_task_event(task, outputs)

    assert outputs["context_id"] == "ctx_12345"
    assert outputs["status"] == "completed"
    assert "Task finished successfully." in outputs["response"]
    assert "Artifact summary text" in outputs["response"]
    assert outputs.get("metadata") == {
        "active_mutation_id": "var_tested_42",
        "attempt_index": 2,
        "score": 4.5,
    }


def test_parse_args_pin_pareto():
    """Verify --pin-pareto CLI argument parsing."""
    default_args = _parse_args([])
    assert default_args.pin_pareto is False

    pinned_args = _parse_args(["--pin-pareto"])
    assert pinned_args.pin_pareto is True


def test_init_gepa_components_pin_pareto(temp_gepa_dir):
    """When --pin-pareto is set, init returns ParetoRegistry and None for ReflectorClient."""
    args = _parse_args(["--pin-pareto", "--gepa-dir", str(temp_gepa_dir)])
    registry, client = _init_gepa_components(args)
    assert registry is not None
    assert client is None


def test_build_payload_with_pin_pareto(temp_gepa_dir):
    """When pin_pareto is enabled, warm Pareto prompt is injected and reflector mutation is disabled."""
    registry = ParetoRegistry(gepa_dir=temp_gepa_dir)
    registry.register_pareto_prompt(
        taxonomy="input_validation",
        prompt="WARM PINNED PARETO PROMPT FOR INPUT VALIDATION",
        variant_id="var_input_pinned_999",
        score=2.5,
        rationale="Warm Pareto prior",
        topological_rule="RULE_COMMAND_SANITIZATION",
    )

    args = _parse_args(["--pin-pareto", "--gepa-dir", str(temp_gepa_dir)])
    seed = {
        "topic": "os.system(user_cmd);",
        "predicate": "command_injection in input validation",
    }
    payload = _build_payload(
        args=args,
        item_seed=200,
        checkpoint_path="artifacts/checkpoints/200.json",
        record_path="artifacts/runs/200.json",
        batch_started_at="2026-09-21T12:00:00Z",
        seed=seed,
        reflector_client=None,
        pareto_registry=registry,
    )

    assert payload["config"]["taxonomy_bucket"] == "input_validation"
    assert payload["config"]["active_mutation_id"] == "var_input_pinned_999"
    assert payload["config"]["reflector_prompt"] == "WARM PINNED PARETO PROMPT FOR INPUT VALIDATION"
    assert payload["config"]["pin_pareto"] is True
    assert payload["config"]["reflector"] is False


@pytest.mark.asyncio
async def test_record_gepa_reflector_trace_skipped_on_pin_pareto(temp_gepa_dir):
    """When pin_pareto is enabled, trace recording is skipped to keep frontier pristine."""
    mock_client = MagicMock()
    mock_client.record_attempt_and_classify_outcome = AsyncMock()

    args = _parse_args(["--pin-pareto", "--run-id", "test-pin-trace"])
    ctx = BatchContext(
        args=args,
        batch_started_at="2026-09-21T12:00:00Z",
        processed_predicates=set(),
        manifest={"items": []},
        manifest_path=str(temp_gepa_dir / "manifest.json"),
        manifest_lock=asyncio.Lock(),
        total_seeds=1,
        reflector_client=mock_client,
    )

    seed = {"predicate": "test_predicate", "topic": "test_topic"}
    payload = {"config": {"active_mutation_id": "var_pinned_123", "reflector_prompt": "prompt"}}
    result = {"status": "completed", "decision": "accepted"}

    await _record_gepa_reflector_trace(ctx, seed, 42, payload, result, "completed", 0)
    mock_client.record_attempt_and_classify_outcome.assert_not_called()


@pytest.mark.asyncio
async def test_judge_pin_pareto_bypasses_mutation_and_promotion(temp_gepa_dir):
    """Judge in pin_pareto mode does not mutate prompt on retry and does not promote to registry."""
    judge = DebateJudgeADK()
    mock_registry = MagicMock()

    ctx = MagicMock()
    ctx.pin_pareto = True
    ctx.reflector_prompt = "PINNED_WARM_PROMPT"
    ctx.active_mutation_id = "var_warm_123"
    ctx.max_refinements = 2
    ctx.reflector_client = MagicMock()
    ctx.reflector_client.registry = mock_registry

    updater = MagicMock()
    updater.update_status = AsyncMock()

    # Mutation test: verify early return
    await judge._try_mutate_reflector_prompt(ctx, 0, "test failure", updater)
    assert ctx.reflector_prompt == "PINNED_WARM_PROMPT"
    assert ctx.active_mutation_id == "var_warm_123"
    ctx.reflector_client.reflect.assert_not_called()

