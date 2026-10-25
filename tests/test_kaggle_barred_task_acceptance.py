import ast
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


TASK_PATH = Path(__file__).resolve().parents[1] / "scripts" / "kaggle_barred_task.py"


def _load_task_module():
    source = TASK_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TASK_PATH))
    tree.body = [
        node for node in tree.body
        if not (
            (
                isinstance(node, ast.For)
                and isinstance(node.iter, ast.Name)
                and node.iter.id in {"BARRED_SEEDS", "_seeds_to_run"}
            )
            or (
                isinstance(node, ast.Import)
                and any(alias.name == "kaggle_benchmarks" for alias in node.names)
            )
            or (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.startswith("kaggle_benchmarks")
            )
        )
    ]
    module_ast = ast.fix_missing_locations(tree)
    fake_kbench = SimpleNamespace(
        task=lambda **_kwargs: lambda function: function,
        LLMChat=object,
        ChatRoom=object,
    )
    fake_assertions = SimpleNamespace(
        assert_true=lambda condition, message="": None if condition else (_ for _ in ()).throw(
            AssertionError(message)
        ),
    )
    module = ModuleType("kaggle_barred_task_acceptance_test")
    module.__file__ = str(TASK_PATH)
    module.kbench = fake_kbench
    module.assertions = fake_assertions

    exec(compile(module_ast, str(TASK_PATH), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def task():
    with pytest.MonkeyPatch.context() as patch:
        patch.delenv("BARRED_SEED_LIMIT", raising=False)
        return _load_task_module()


def _con_evidence():
    return {
        "defense_kind": "upper_bound_reject",
        "guard_anchor": "if (len > capacity) return;",
        "guarded_value": "len",
        "protected_operation_anchor": "memcpy(dst, src, len)",
        "operation_value": "len",
        "enforcement": "reject_before_operation",
        "invariant": "len <= capacity before copy",
        "predicate_precondition": "len exceeds capacity",
        "value_relation": "guarded_value_equals_operation_value",
        "counterfactual": "Removing if (len > capacity) return; lets len reach memcpy.",
    }


def _code():
    return (
        "void copy(char *dst, char *src, int len, int capacity) {\n"
        "  if (len > capacity) return;\n"
        "  memcpy(dst, src, len);\n"
        "  return;\n"
        "}\n"
    )


def test_embedded_kaggle_seeds_match_first_ten_canonical_records(task):
    canonical_path = TASK_PATH.parents[1] / "scenarios" / "debate" / "cve_seeds_500_clean.jsonl"
    canonical = [
        json.loads(line)
        for line in canonical_path.read_text(encoding="utf-8").splitlines()[:10]
    ]
    expected_verdicts = ["True", "True", "True", "False", "True", "True", "False", "True", "False", "True"]

    assert len(task.BARRED_SEEDS) == 10
    for index, (embedded, source, verdict) in enumerate(
        zip(task.BARRED_SEEDS, canonical, expected_verdicts), start=1
    ):
        assert embedded["source_index"] == index
        assert embedded["predicate"] == source["predicate"]
        assert embedded["topic"] == source["topic"]
        assert embedded["anchors"] == source["anchors"]
        assert embedded["original_safety"] == source["original_safety"]
        assert embedded["target_verdict"] == verdict


def test_seed_limit_is_opt_in_and_validated(monkeypatch):
    monkeypatch.delenv("BARRED_SEEDS_FILE", raising=False)
    monkeypatch.delenv("BARRED_SEED_LIMIT", raising=False)
    default_module = _load_task_module()
    assert len(default_module._seeds_to_run) == default_module.DEFAULT_SEED_LIMIT == 1

    monkeypatch.setenv("BARRED_SEED_LIMIT", "1")
    module = _load_task_module()
    assert len(module._seeds_to_run) == 1
    assert module._seeds_to_run[0]["source_index"] == 1

    monkeypatch.setenv("BARRED_SEED_LIMIT", "11")
    with pytest.raises(ValueError, match="BARRED_SEED_LIMIT"):
        _load_task_module()


def test_attached_seed_file_loading_and_default_limit(monkeypatch, tmp_path):
    seed_file = tmp_path / "seeds.jsonl"
    seeds = [
        {
            "topic": f"int seed_{index}(void) {{ return {index}; }}",
            "predicate": (
                "The code is not vulnerable to buffer overflow"
                if index == 0
                else "The code is vulnerable to buffer overflow"
            ),
            "original_safety": "safe" if index == 0 else "vulnerable",
            "anchors": ["return"],
            "language": "c",
        }
        for index in range(12)
    ]
    seed_file.write_text(
        "\n".join(json.dumps(seed) for seed in seeds) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BARRED_SEEDS_FILE", str(seed_file))
    monkeypatch.delenv("BARRED_SEED_LIMIT", raising=False)

    module = _load_task_module()
    assert len(module.BARRED_SEEDS) == 12
    assert len(module._seeds_to_run) == 1
    assert module.BARRED_SEEDS[0]["target_verdict"] == "True"
    assert module.BARRED_SEEDS[1]["target_verdict"] == "True"
    assert module.BARRED_SEEDS[0]["target_dimension"] == "Security Invariants"
    assert module.BARRED_SEEDS[0]["source_index"] == 1

    monkeypatch.setenv("BARRED_SEED_LIMIT", "11")
    assert len(_load_task_module()._seeds_to_run) == 11


def test_attached_seed_file_rejects_invalid_source_rows(monkeypatch, tmp_path):
    seed_file = tmp_path / "invalid-seeds.jsonl"
    seed_file.write_text(
        json.dumps({
            "topic": "int f(void) { return 0; }",
            "predicate": "The code is vulnerable",
            "original_safety": "unknown",
            "anchors": [],
        }) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BARRED_SEEDS_FILE", str(seed_file))
    with pytest.raises(ValueError, match="original_safety"):
        _load_task_module()


def test_acceptance_resolver_requires_verifier_for_pro_and_proof_for_formal_con(task):
    assert task._resolve_acceptance("True", "pro_debater", True, None, None)["accepted"]
    assert not task._resolve_acceptance("True", "pro_debater", False, None, None)["accepted"]

    obligation = {"version": "v1", "kind": "upper_bound"}
    assert not task._resolve_acceptance(
        "True", "con_debater", False, {"status": "inconclusive"}, obligation
    )["accepted"]
    assert not task._resolve_acceptance(
        "True", "con_debater", False, {"status": "deterministically_confirmed"}, None
    )["accepted"]
    accepted = task._resolve_acceptance(
        "True",
        "con_debater",
        False,
        {"status": "deterministically_confirmed"},
        obligation,
    )
    assert accepted["accepted"]
    assert accepted["consensus_verdict"] == "False"
    assert accepted["acceptance_basis"] == "validated_con_counter_evidence"


def test_counter_evidence_requires_formal_obligation_and_fails_closed_without_parser(task):
    evidence = _con_evidence()
    assert task._validate_counter_evidence(_code(), "copy can overflow", evidence, None)[
        "status"
    ] == "invalid_contract"

    receipt = task._validate_counter_evidence(
        _code(), "copy can overflow", evidence, {"version": "v1", "kind": "upper_bound"}
    )
    assert receipt["status"] in {"deterministically_confirmed", "inconclusive"}
    if task.tree_sitter is None or task.tree_sitter_c is None:
        assert receipt["status"] != "deterministically_confirmed"


def test_counter_evidence_unavailable_or_unparseable_parser_is_inconclusive(monkeypatch, task):
    tree_sitter_module = task.tree_sitter
    monkeypatch.setattr(task, "tree_sitter", None)
    receipt = task._validate_counter_evidence(
        _code(), "copy can overflow", _con_evidence(), {"version": "v1", "kind": "upper_bound"}
    )
    assert receipt["status"] == "inconclusive"

    if tree_sitter_module is not None and task._C_LANGUAGE is not None:
        monkeypatch.setattr(task, "tree_sitter", tree_sitter_module)
        proof = task._counter_evidence_proof("void copy( {", _con_evidence())
        assert proof.status == "inconclusive"


def test_output_contract_records_verdict_and_acceptance_basis(monkeypatch, task):
    writes = []
    monkeypatch.setattr(task, "CORPUS_FILE", "corpus.jsonl")
    monkeypatch.setattr(task, "_append_jsonl", lambda path, item: writes.append((path, item)))
    judge = task._JudgeResult(
        predicate="A grounded vulnerability predicate",
        target_verdict="True",
        target_dimension="memory_safety",
        code=_code(),
        winner="con_debater",
        reason="guard prevents operation",
        mechanism="Source anchor: len\nSink anchor: memcpy\nMissing guard anchor: none",
        counterfactual="Remove guard",
        support_level="supported",
        normalized_anchors=["if (len > capacity) return;", "memcpy(dst, src, len)"],
        adjudication_pro="",
        adjudication_con="",
        counter_evidence=_con_evidence(),
    )
    task._export_result(
        True,
        judge,
        task._GateResults({}, {}, {}, {}, {}, {}),
        task._VerifierInfo(passes=False, skip_reason="con_decision_uses_counter_evidence"),
        "False",
        "validated_con_counter_evidence",
        {"status": "deterministically_confirmed"},
    )
    row = writes[0][1]
    assert row["output"]["verdict"] == "0"
    assert row["output"]["consensus_verdict"] == "False"
    assert row["output"]["acceptance_basis"] == "validated_con_counter_evidence"
    assert row["output"]["counter_evidence_validation"]["status"] == "deterministically_confirmed"


def test_escalation_is_cold_first_and_adds_context_only_on_retry(task):
    assert task._escalation_prompt(0, "ignored") == ""
    prompt = task._escalation_prompt(1, "verifier_failed")
    assert "Progressive Escalation" in prompt
    assert "verifier_failed" in prompt
    assert task._escalation_prompt(2, "retry_failed")


@pytest.mark.parametrize(
    ("results", "expected_attempts"),
    [([True], [0]), ([False, True], [0, 1]), ([False, False], [0, 1])],
)
def test_seed_escalation_retries_only_once_after_failure(task, results, expected_attempts):
    calls = []

    class FakeTask:
        def run(self, *_args, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(passed=results[len(calls) - 1])

    task.run_barred_debate = FakeTask()
    seed = {
        "topic": _code(),
        "predicate": "copy can overflow",
        "target_verdict": "True",
        "target_dimension": "memory_safety",
    }
    task._run_seed_with_escalation(seed, object())

    assert [call["attempt_index"] for call in calls] == expected_attempts
    if len(calls) == 2:
        assert "previous_failure" not in calls[0]
        assert "previous_failure" in calls[1]


def test_malformed_verifier_response_fails_closed(monkeypatch, task):
    monkeypatch.setattr(task, "_parse_llm_json", lambda _response: None)
    llm = SimpleNamespace(prompt=lambda *_args, **_kwargs: "not json")
    passes, data, error = task._run_verifier_audit(llm, _code(), "predicate", "mechanism", [])
    assert not passes
    assert data is None
    assert error == "verifier_response_parse_failed"


def test_judge_json_parser_accepts_text_and_rejects_empty_response(task):
    assert task._parse_llm_json('{"winner": "pro_debater"}') == {
        "winner": "pro_debater"
    }
    assert task._parse_llm_json("") is None


def test_empty_debate_transcript_stops_before_judge(monkeypatch, tmp_path):
    task = _load_task_module()

    class FakeRoom:
        def add_participant(self, *_args, **_kwargs):
            return object()

    monkeypatch.setattr(task.kbench, "ChatRoom", lambda **_kwargs: FakeRoom())
    monkeypatch.setattr(
        task,
        "_run_debate_room",
        lambda *_args: ("opening", "opening", "rebuttal", "rebuttal", []),
    )
    task.ATTEMPTS_FILE = str(tmp_path / "attempts.jsonl")
    llm_calls = []
    llm = SimpleNamespace(
        prompt=lambda *_args, **_kwargs: llm_calls.append("called")
    )

    with pytest.raises(AssertionError, match="Judge not invoked: debate transcript is empty"):
        task.run_barred_debate(llm, _code(), "copy can overflow")

    assert llm_calls == []
