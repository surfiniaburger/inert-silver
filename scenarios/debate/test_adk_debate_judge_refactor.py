import json
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock

from agentbeats.models import EvalRequest
from debate_judge_common import DebateEval, DebaterScore, VerifierReport
from scenarios.debate.adk_debate_judge import (
    DebateJudgeADK,
    VerifierMeta,
    _EvalContext,
    _AcceptedSamplePayload,
    _mechanism_evidence_gate,
)


def test_eval_context_initialization_and_controls():
    with tempfile.TemporaryDirectory() as td:
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-run-1",
                "seed": 42,
                "mode": "passthrough",
                "record_path": os.path.join(td, "run.json"),
                "attempts_path": os.path.join(td, "attempts.jsonl"),
                "checkpoint_path": os.path.join(td, "checkpoint.json"),
                "topic": "def foo(): pass",
            }
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)

        assert ctx.run_id == "test-run-1"
        assert ctx.seed == 42
        assert ctx.mode == "passthrough"
        assert ctx.record_path == os.path.join(td, "run.json")
        assert ctx.attempts_path == os.path.join(td, "attempts.jsonl")


@pytest.mark.asyncio
async def test_get_sample_data_refinement_without_checkpoint():
    with tempfile.TemporaryDirectory() as td:
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-run-sample",
                "seed": 42,
                "mode": "passthrough",
                "checkpoint_path": os.path.join(td, "ckpt.json"),
                "topic": "def initial(): pass",
            }
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)

        judge.generator = MagicMock()
        sample_0 = "int gen_0(char *buf) {\n    if (buf) { return 0; }\n    return -1;\n}"
        sample_1 = "int gen_1(char *buf) {\n    if (buf) { return 1; }\n    return -1;\n}"
        judge.generator.generate_boundary_sample = AsyncMock(return_value={"revised_input_block": sample_0})
        judge.generator.refine_sample = AsyncMock(return_value={"revised_input_block": sample_1})

        updater = MagicMock()
        updater.update_status = AsyncMock()

        # Pass 0: initial generation
        s_data_0, block_0 = await judge._get_sample_data(ctx, 0, None, "start", "", updater)
        assert block_0 == sample_0

        # Pass 1: refinement (no active checkpoint)
        s_data_1, block_1 = await judge._get_sample_data(ctx, 1, None, "start", "Rejected by judge", updater)
        assert block_1 == sample_1
        judge.generator.refine_sample.assert_called_once_with(
            "def initial(): pass",
            ctx.predicate,
            ctx.target_dimension,
            ctx.target_verdict,
            sample_0,
            "Rejected by judge",
            reflector_prompt=ctx.reflector_prompt,
        )


def test_mechanism_evidence_gate_refactored():
    # Test invalid non-string mechanism
    res = _mechanism_evidence_gate(123, "def foo(): pass", ["foo"])
    assert res["pass"] is False

    # Test valid mechanism with operation anchors
    input_text = "def check_auth(user):\n    if not user.is_admin:\n        raise PermissionError('Denied')"
    mechanism = "Calls check_auth(user) and raises PermissionError when not admin."
    res = _mechanism_evidence_gate(mechanism, input_text, ["check_auth(user)"])
    assert res["pass"] is True
    assert res["has_code_token"] is True
    assert res["has_operation_anchor"] is True


def test_evaluate_verifier_audit_passed_and_failed():
    with tempfile.TemporaryDirectory() as td:
        attempts_path = os.path.join(td, "attempts.jsonl")
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-run-2",
                "seed": 42,
                "mode": "passthrough",
                "attempts_path": attempts_path,
            }
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)

        pro = DebaterScore(technical_accuracy=1.0, logic_soundness=1.0, evidence_strength=1.0, total_score=1.0, critique="Pro critique")
        con = DebaterScore(technical_accuracy=0.5, logic_soundness=0.5, evidence_strength=0.5, total_score=0.5, critique="Con critique")
        debate_eval = DebateEval(
            thinking_process="Thinking...",
            predicate="Is vulnerable",
            anchors=["check_auth", "user"],
            support_level="supported",
            verifier_report="Audit passed",
            winner="pro_debater",
            reason="Clear vulnerability found",
            mechanism="Calls check_auth()",
            counterfactual="Fix check_auth()",
            pro_debater=pro,
            con_debater=con,
        )

        verifier_meta: VerifierMeta = {
            "called": True,
            "from_cache": False,
            "parse_ok": True,
            "passes_audit": True,
            "logic_error": None,
            "error": None,
            "raw_response": "{}",
            "llm_usage": None,
            "model": "verifier-v1",
            "url": "http://localhost:9020",
        }

        # Case 1: Passed audit
        passed_report = VerifierReport(
            thinking_process="Thinking...",
            passes_audit=True,
            anchor_analysis="Anchors verified",
            logic_error=None,
            suggested_correction=None,
        )
        ok, reason = judge._evaluate_verifier_audit(
            ctx, 0, passed_report, verifier_meta, debate_eval, ["check_auth"], {}, "def foo(): pass"
        )
        assert ok is True
        assert reason == "Clear vulnerability found"

        # Case 2: Failed audit due to logic error
        failed_report = VerifierReport(
            thinking_process="Thinking...",
            passes_audit=False,
            anchor_analysis="Anchor analysis failed",
            logic_error="Null pointer exception unhandled",
            suggested_correction="Add null check",
        )
        ok_fail, reason_fail = judge._evaluate_verifier_audit(
            ctx, 0, failed_report, verifier_meta, debate_eval, ["check_auth"], {}, "def foo(): pass"
        )
        assert ok_fail is False
        assert "VERIFIER AUDIT FAILED" in reason_fail
        assert os.path.exists(attempts_path)


@pytest.mark.asyncio
async def test_export_accepted_sample_payload():
    with tempfile.TemporaryDirectory() as td:
        output_file = os.path.join(td, "corpus.jsonl")
        attempts_path = os.path.join(td, "attempts.jsonl")
        record_path = os.path.join(td, "record.json")
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-run-3",
                "seed": 100,
                "mode": "passthrough",
                "output_file": output_file,
                "attempts_path": attempts_path,
                "record_path": record_path,
                "predicate": "Input contains SQL injection",
                "target_verdict": "True",
            }
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)

        pro = DebaterScore(technical_accuracy=1.0, logic_soundness=1.0, evidence_strength=1.0, total_score=1.0, critique="Pro critique")
        con = DebaterScore(technical_accuracy=0.5, logic_soundness=0.5, evidence_strength=0.5, total_score=0.5, critique="Con critique")
        debate_eval = DebateEval(
            thinking_process="Thinking...",
            predicate="Input contains SQL injection",
            anchors=["query", "input_str"],
            support_level="supported",
            verifier_report="Passed",
            winner="pro_debater",
            reason="Unsanitized query input",
            mechanism="Calls query()",
            counterfactual="Use parameterized query",
            pro_debater=pro,
            con_debater=con,
        )

        verifier_meta: VerifierMeta = {
            "called": True,
            "from_cache": False,
            "parse_ok": True,
            "passes_audit": True,
            "logic_error": None,
            "error": None,
            "raw_response": "{}",
            "llm_usage": None,
            "model": "verifier-v1",
            "url": "http://localhost:9020",
        }

        payload = _AcceptedSamplePayload(
            current_sample_block="db.query(input_str)",
            debate_eval=debate_eval,
            normalized_anchors=["query"],
            verifier_meta=verifier_meta,
            verifier_audit=VerifierReport(
                thinking_process="Thinking...",
                passes_audit=True,
                anchor_analysis="Anchors verified",
                logic_error=None,
                suggested_correction=None,
            ),
            sample_data={"topic": "SQLi"},
            debate={"transcript": []},
            soft_checks={"predicate_quality": True},
            anchor_stats={"hits": 1},
            last_judge_reason="Unsanitized query input",
        )

        updater = MagicMock()
        updater.update_status = AsyncMock()
        updater.add_artifact = AsyncMock()

        await judge._export_accepted_sample(ctx, 0, payload, updater)

        assert os.path.exists(output_file)
        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["input"] == "db.query(input_str)"
            assert data["output"]["verdict"] == "1"


def test_merge_usage_summaries():
    from scenarios.debate.adk_debate_judge import _merge_usage_summaries

    primary = {
        "totals": {"calls": 2, "prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150, "cost_usd": 0.01},
        "by_stage": {"judge": {"calls": 1, "prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70, "cost_usd": 0.005}},
        "by_model": {"m1": {"calls": 2, "prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150, "cost_usd": 0.01}},
        "events": [{"event": "e1"}],
        "models": {"judge": "m1"},
        "generation_config": {"temp": 0.2},
        "notes": {},
    }

    secondary = {
        "totals": {"calls": 1, "prompt_tokens": 40, "completion_tokens": 10, "total_tokens": 50, "cost_usd": 0.002},
        "by_stage": {"verifier": {"calls": 1, "prompt_tokens": 40, "completion_tokens": 10, "total_tokens": 50, "cost_usd": 0.002}},
        "by_model": {"m2": {"calls": 1, "prompt_tokens": 40, "completion_tokens": 10, "total_tokens": 50, "cost_usd": 0.002}},
        "events": [{"event": "e2"}],
        "models": {"verifier": "m2"},
        "generation_config": {"verifier_temp": 0.0},
    }

    merged = _merge_usage_summaries(primary, secondary)

    assert merged["totals"]["calls"] == 3
    assert merged["totals"]["prompt_tokens"] == 140
    assert merged["totals"]["completion_tokens"] == 60
    assert merged["totals"]["total_tokens"] == 200
    assert abs(merged["totals"]["cost_usd"] - 0.012) < 1e-6
    assert "judge" in merged["by_stage"]
    assert "verifier" in merged["by_stage"]
    assert len(merged["events"]) == 2
    assert merged["models"]["verifier"] == "m2"


@pytest.mark.asyncio
async def test_asymmetric_reflector_injection_in_debate():
    with tempfile.TemporaryDirectory() as td:
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-asymm",
                "seed": 42,
                "mode": "passthrough",
                "reflector_prompt": "[Topological Repair Directive]\nApply valid bounds check.",
                "reflector_mode": "pro_only",
                "predicate": "Vulnerable to buffer overflow",
                "target_verdict": "True",
                "topic": "test",
                "record_path": os.path.join(td, "run.json"),
                "num_rounds": 1,
            },
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)

        captured_pro = ""
        captured_con = ""

        async def mock_orchestrate(replay_mgr, participants, sample_block, num_rounds, updater, **kwargs):
            nonlocal captured_pro, captured_con
            captured_pro = kwargs.get("pro_mission", "")
            captured_con = kwargs.get("con_mission", "")
            return {"pro_debater": [], "con_debater": []}

        judge.orchestrate_debate = mock_orchestrate
        updater = MagicMock()
        updater.update_status = AsyncMock()

        await judge._get_debate_transcript(ctx, 0, req, "sample", {}, None, "start", "", updater)

        # Pro mission MUST contain the reflector prompt
        assert "[Topological Repair Directive]" in captured_pro
        assert "PRO MISSION: Prove that the predicate 'Vulnerable to buffer overflow' is True" in captured_pro

        # Con mission MUST NOT contain the reflector prompt (neutral auditor)
        assert "[Topological Repair Directive]" not in captured_con
        assert "CON MISSION: Prove that the predicate 'Vulnerable to buffer overflow' is False" in captured_con


def test_resolve_target_verdict_polarities():
    from scenarios.debate.run_batch import resolve_target_verdict

    # Explicit override takes precedence
    assert resolve_target_verdict({"target_verdict": "False"}) == "False"
    assert resolve_target_verdict({"target_verdict": "True"}) == "True"

    # Safe seed with positive predicate ("is vulnerable") -> False
    safe_pos = {"original_safety": "safe", "predicate": "The code is vulnerable to SQL injection"}
    assert resolve_target_verdict(safe_pos) == "False"

    # Safe seed with negative predicate ("is not vulnerable") -> True
    safe_neg = {"original_safety": "safe", "predicate": "The code is not vulnerable to buffer overflow"}
    assert resolve_target_verdict(safe_neg) == "True"

    # Vulnerable seed with positive predicate ("is vulnerable") -> True
    vuln_pos = {"original_safety": "vulnerable", "predicate": "The code is vulnerable to buffer overflow"}
    assert resolve_target_verdict(vuln_pos) == "True"

    # Vulnerable seed with negative predicate ("is **not** vulnerable") -> False
    vuln_neg = {"original_safety": "vulnerable", "predicate": "The code is **not** vulnerable to OOB read"}
    assert resolve_target_verdict(vuln_neg) == "False"


@pytest.mark.asyncio
async def test_con_win_validated_receipt_acceptance():
    with tempfile.TemporaryDirectory() as td:
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-con-win",
                "seed": 42,
                "mode": "passthrough",
                "topic": "test",
                "predicate": "Vulnerable to heap overflow",
                "target_verdict": "True",
                "record_path": os.path.join(td, "run.json"),
                "attempts_path": os.path.join(td, "attempts.jsonl"),
                "defense_obligation": {"version": "v1", "kind": "upper_bound"},
            },
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)
        from scenarios.debate.con_receipt_extractor import extract_candidates
        ctx.last_con_candidates = extract_candidates("void f(char *dst, char *src, int len, int cap) {\n    if (len > cap) return;\n    memcpy(dst, src, len);\n}", {"version": "v1", "kind": "upper_bound"})
        ctx.defense_obligation = {"version": "v1", "kind": "upper_bound"}

        pro = DebaterScore(technical_accuracy=0.3, logic_soundness=0.3, evidence_strength=0.3, total_score=0.3, critique="Pro argued")
        con = DebaterScore(technical_accuracy=0.9, logic_soundness=0.9, evidence_strength=0.9, total_score=0.9, critique="Con proved bounds check")
        ce = {
            "defense_kind": "upper_bound_reject",
            "guard_anchor": "if (len > capacity) return;",
            "guarded_value": "len",
            "protected_operation_anchor": "memcpy(dst, src, len)",
            "operation_value": "len",
            "enforcement": "reject_before_operation",
            "invariant": "len <= capacity before copy",
            "predicate_precondition": "len exceeds capacity",
            "value_relation": "guarded_value_equals_operation_value",
            "counterfactual": "Removing guard lets len reach memcpy.",
        }
        debate_eval = DebateEval(
            thinking_process="Thinking...",
            predicate="Vulnerable to heap overflow",
            anchors=["len < max_len", "char buf[10];"],
            winner="con_debater",
            reason="Code contains a strict bounds check preventing overflow on len < max_len.",
            mechanism="bounds check guard anchor: len < max_len",
            counterfactual="If len check removed",
            support_level="supported",
            verifier_report="Passed",
            pro_debater=pro,
            con_debater=con,
            con_candidate_id="C1",
        )
        from scenarios.debate.con_receipt_extractor import extract_candidates
        ctx.last_con_candidates = extract_candidates("void f(char *dst, char *src, int len, int cap) {\n    if (len > cap) return;\n    memcpy(dst, src, len);\n}", {"version": "v1", "kind": "upper_bound"})
        normalized_anchors = ["len < max_len", "char buf[10];"]
        soft_checks = {
            "con_win_counter_evidence": {"pass": True, "applicable": True},
        }

        updater = MagicMock()
        updater.update_status = AsyncMock()

        # Mock verifier call
        mock_audit = VerifierReport(
            thinking_process="Checked bounds",
            passes_audit=True,
            anchor_analysis="Anchors verified",
            logic_error=None,
            suggested_correction=None,
        )
        judge._restore_or_call_verifier = AsyncMock()

        from scenarios.debate.adk_debate_judge import _collect_soft_checks
        sc, as_ = _collect_soft_checks(ctx, debate_eval, "void f(char *dst, char *src, int len, int cap) {\n    if (len > cap) return;\n    memcpy(dst, src, len);\n}", normalized_anchors)
        soft_checks = sc

        is_valid, report, meta, reason = await judge._process_verifier_audit(
            ctx, 0, debate_eval, "void f(char *dst, char *src, int len, int cap) {\n    if (len > cap) return;\n    memcpy(dst, src, len);\n}", normalized_anchors, soft_checks, {}, {}, None, "start", updater
        )

        assert is_valid is True
        assert report is None
        assert meta["error"] == "validated_con_counter_evidence"
        judge._restore_or_call_verifier.assert_not_called()


@pytest.mark.asyncio
async def test_con_win_gate_only_does_not_accept():
    """Regression: a Con win with only a passing gate (no valid receipt) must NOT be accepted."""
    with tempfile.TemporaryDirectory() as td:
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-con-win-gate-only",
                "seed": 42,
                "mode": "passthrough",
                "topic": "test",
                "predicate": "Vulnerable to heap overflow",
                "target_verdict": "True",
                "record_path": os.path.join(td, "run.json"),
                "attempts_path": os.path.join(td, "attempts.jsonl"),
            },
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)
        from scenarios.debate.con_receipt_extractor import extract_candidates
        ctx.last_con_candidates = extract_candidates("void f(char *dst, char *src, int len, int cap) {\n    if (len > cap) return;\n    memcpy(dst, src, len);\n}", {"version": "v1", "kind": "upper_bound"})

        pro = DebaterScore(technical_accuracy=0.3, logic_soundness=0.3, evidence_strength=0.3, total_score=0.3, critique="Pro argued")
        con = DebaterScore(technical_accuracy=0.9, logic_soundness=0.9, evidence_strength=0.9, total_score=0.9, critique="Con proved bounds check")
        ce = {
            "defense_kind": "upper_bound_reject",
            "guard_anchor": "if (len > capacity) return;",
            "guarded_value": "len",
            "protected_operation_anchor": "memcpy(dst, src, len)",
            "operation_value": "len",
            "enforcement": "reject_before_operation",
            "invariant": "len <= capacity before copy",
            "predicate_precondition": "len exceeds capacity",
            "value_relation": "guarded_value_equals_operation_value",
            "counterfactual": "Removing guard lets len reach memcpy.",
        }
        debate_eval = DebateEval(
            thinking_process="Thinking...",
            predicate="Vulnerable to heap overflow",
            anchors=["len < max_len", "char buf[10];"],
            winner="con_debater",
            reason="Code contains a strict bounds check preventing overflow on len < max_len.",
            mechanism="bounds check guard anchor: len < max_len",
            counterfactual="If len check removed",
            support_level="supported",
            verifier_report="Passed",
            pro_debater=pro,
            con_debater=con,
            counter_evidence=ce,
        )
        normalized_anchors = ["len < max_len", "char buf[10];"]
        soft_checks = {
            "con_win_counter_evidence": {"pass": True, "applicable": True},
            # no counter_evidence_validation receipt
        }

        updater = MagicMock()
        updater.update_status = AsyncMock()

        judge._restore_or_call_verifier = AsyncMock()

        is_valid, report, meta, reason = await judge._process_verifier_audit(
            ctx, 0, debate_eval, "char buf[10];", normalized_anchors, soft_checks, {}, {}, None, "start", updater
        )

        assert is_valid is False
        assert meta["error"] != "validated_con_counter_evidence"
        judge._restore_or_call_verifier.assert_not_called()


@pytest.mark.asyncio
async def test_eval_context_no_reflector():
    """Verify _EvalContext and _try_mutate_reflector_prompt work safely when reflector is disabled."""
    with tempfile.TemporaryDirectory() as td:
        req = EvalRequest(
            participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
            config={
                "run_id": "test-no-reflector",
                "seed": 42,
                "mode": "passthrough",
                "reflector": False,
                "attempts_path": os.path.join(td, "attempts.jsonl"),
            }
        )
        judge = DebateJudgeADK()
        ctx = _EvalContext(req, judge)

        assert hasattr(ctx, "reflector_client")
        assert ctx.reflector_client is None

        updater = MagicMock()
        updater.update_status = AsyncMock()

        # Calling _try_mutate_reflector_prompt when reflector_client is None should return immediately without error
        await judge._try_mutate_reflector_prompt(ctx, 0, "Test reason", updater)


def test_con_mechanism_template_gate_and_gate_checks():
    """Verify _con_mechanism_template_gate accepts counter-evidence and guard/anchor reasoning."""
    from scenarios.debate.adk_debate_judge import _con_mechanism_template_gate

    # 1. Counter-evidence dict passes directly
    res1 = _con_mechanism_template_gate("", ["buf", "len"], counter_evidence={"status": "ok"})
    assert res1["pass"] is True

    # 2. Safety reason with guard and anchor passes
    res2 = _con_mechanism_template_gate(
        mechanism="",
        anchors=["buf", "len"],
        reason="The guard check if (len >= 40) protects buf from out-of-bounds access.",
    )
    assert res2["pass"] is True
    assert res2["anchor_hits_in_mechanism"] >= 1

    # 3. Missing guard fails
    res3 = _con_mechanism_template_gate(
        mechanism="",
        anchors=["buf", "len"],
        reason="buf and len are present but no explanation is given.",
    )
    assert res3["pass"] is False
    assert "guard_or_invariant" in res3["missing"]


@pytest.mark.asyncio
async def test_reflector_mode_mission_injection():
    """Verify that reflector_prompt is injected into pro and/or con based on reflector_mode."""
    with tempfile.TemporaryDirectory() as td:
        for mode, pro_has_reflector, con_has_reflector in [
            ("symmetric", True, True),
            ("pro_only", True, False),
            ("con_only", False, True),
        ]:
            req = EvalRequest(
                participants={"pro_debater": "http://localhost:9001", "con_debater": "http://localhost:9002"},
                config={
                    "run_id": f"test-mode-{mode}",
                    "seed": 42,
                    "mode": "passthrough",
                    "reflector_prompt": "METAPROMPT_XYZ",
                    "reflector_mode": mode,
                    "attempts_path": os.path.join(td, f"attempts_{mode}.jsonl"),
                    "topic": "int x = 0;",
                    "num_rounds": 1,
                }
            )
            judge = DebateJudgeADK()
            ctx = _EvalContext(req, judge)
            assert ctx.reflector_mode == mode

            judge.orchestrate_debate = AsyncMock(return_value={"pro_debater": [], "con_debater": []})
            updater = MagicMock()
            updater.update_status = AsyncMock()

            await judge._get_debate_transcript(
                ctx, 0, req, "int x = 0;", {}, None, "start", "", updater
            )

            call_kwargs = judge.orchestrate_debate.call_args.kwargs
            pro_mission = call_kwargs["pro_mission"]
            con_mission = call_kwargs["con_mission"]

            assert ("METAPROMPT_XYZ" in pro_mission) is pro_has_reflector
            assert ("METAPROMPT_XYZ" in con_mission) is con_has_reflector

