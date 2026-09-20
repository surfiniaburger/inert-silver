"""Deterministic Con counter-evidence contract and receipt validation (V1)."""

from __future__ import annotations

import hashlib
from typing import Any, Dict

from scenarios.debate.graphify_flow_extractor import extract_counter_evidence_proof

VALID_MODES = {"off", "shadow", "enforce_deterministic"}
VALID_OBLIGATIONS = {
    "upper_bound": {"upper_bound_reject", "range_guarded_operation"},
    "null_dereference": {"null_check"},
    "identity_mismatch": {"equality_reject"},
}


def _receipt(status: str, *, reason: str | None = None, evidence: Dict[str, Any] | None = None,
             checks: Dict[str, bool] | None = None) -> Dict[str, Any]:
    return {
        "status": status,
        "method": "structural_v1",
        "proof_scope": "snippet_local_mechanism",
        "checks": checks or {},
        "evidence": evidence or {},
        "failure_reasons": [reason] if reason else [],
        "validator_version": "counter_evidence_v1",
        "phase_b_ran": False,
    }


def validate_counter_evidence(code: str, predicate: str, evidence: Any,
                              defense_obligation: Any) -> Dict[str, Any]:
    """Return a durable V1 receipt. Only a structural confirmation may accept."""
    if hasattr(evidence, "model_dump"):
        evidence = evidence.model_dump()
    if not isinstance(evidence, dict):
        return _receipt("invalid_contract", reason="counter_evidence_missing")
    required = {"defense_kind", "guard_anchor", "guarded_value", "protected_operation_anchor",
                "operation_value", "enforcement", "invariant", "predicate_precondition",
                "value_relation", "counterfactual"}
    if any(not isinstance(evidence.get(k), str) or not evidence[k].strip() for k in required):
        return _receipt("invalid_contract", reason="counter_evidence_malformed")
    if evidence["guard_anchor"] == evidence["protected_operation_anchor"]:
        return _receipt("invalid_contract", reason="counter_evidence_duplicate_anchors")
    if not isinstance(defense_obligation, dict) or defense_obligation.get("version") != "v1":
        return _receipt("invalid_contract", reason="counter_evidence_missing_defense_obligation")
    obligation_kind = defense_obligation.get("kind")
    if evidence["defense_kind"] not in VALID_OBLIGATIONS.get(obligation_kind, set()):
        return _receipt("invalid_contract", reason="counter_evidence_obligation_mismatch")
    if evidence["guard_anchor"] not in code:
        return _receipt("invalid_contract", reason="counter_evidence_guard_not_found")
    if evidence["protected_operation_anchor"] not in code:
        return _receipt("invalid_contract", reason="counter_evidence_operation_not_found")
    if (evidence["guard_anchor"] not in evidence["counterfactual"]
            and evidence["operation_value"] not in evidence["counterfactual"]):
        return _receipt("invalid_contract", reason="counter_evidence_counterfactual_incoherent")
    proof = extract_counter_evidence_proof(code, evidence)
    checks = {
        "guard_anchor_exact": True,
        "operation_anchor_exact": True,
        "anchors_are_functional": proof.status not in {"invalid_contract"},
        "value_relation_valid": proof.status == "deterministically_confirmed",
        "control_flow_valid": proof.status == "deterministically_confirmed",
        "predicate_precondition_blocked": proof.status == "deterministically_confirmed",
        "counterfactual_coherent": True,
    }
    output = _receipt(proof.status, reason=proof.failure_reason, checks=checks, evidence={
        "guard_span": proof.guard_span,
        "operation_span": proof.operation_span,
        "guarded_value": proof.guarded_value,
        "operation_value": proof.operation_value,
        "relation": proof.relation,
        "parser_mode": proof.parser_mode,
        "snippet_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        "defense_obligation": defense_obligation,
        "predicate": predicate,
    })
    output["defense_kind"] = evidence["defense_kind"]
    return output
