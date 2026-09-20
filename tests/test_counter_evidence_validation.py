from scenarios.debate.counter_evidence_validation import validate_counter_evidence
from scripts.evaluate_step4_acceptance import _compute_counter_evidence_metrics


OBLIGATION = {"version": "v1", "kind": "upper_bound"}
EVIDENCE = {
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
CODE = "void copy(char *dst, char *src, int len, int capacity) {\nif (len > capacity) return;\nmemcpy(dst, src, len);\n}"


def test_counter_evidence_requires_versioned_seed_obligation():
    receipt = validate_counter_evidence(CODE, "copy can overflow", EVIDENCE, None)
    assert receipt["status"] == "invalid_contract"
    assert receipt["failure_reasons"] == ["counter_evidence_missing_defense_obligation"]


def test_counter_evidence_never_confirms_without_tree_sitter():
    receipt = validate_counter_evidence(CODE, "copy can overflow", EVIDENCE, OBLIGATION)
    assert receipt["status"] in {"deterministically_confirmed", "inconclusive"}
    assert receipt["validator_version"] == "counter_evidence_v1"
    assert receipt["proof_scope"] == "snippet_local_mechanism"


def test_b_gate_separates_validated_con_verifier_skip():
    metrics = _compute_counter_evidence_metrics([
        {"decision": "accepted", "acceptance_basis": "validated_con_counter_evidence",
         "verifier": {"called": False},
         "counter_evidence_validation": {"status": "deterministically_confirmed"}},
        {"decision": "rejected", "counter_evidence_validation": {"status": "inconclusive"}},
    ])
    assert metrics["validated_con_accepts"] == 1
    assert metrics["verifier_skipped_intentionally_for_validated_con"] == 1
    assert metrics["con_inconclusive"] == 1
