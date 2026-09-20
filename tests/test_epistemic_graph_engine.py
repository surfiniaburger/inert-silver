"""
Comprehensive Contract & Property Tests for the Epistemic Change Impact Graph Engine.
Validates:
  1. Tri-State Reachability (PROVEN_REACHABLE, UNKNOWN_REACHABLE, PROVEN_UNREACHABLE).
  2. Proof obligations (entrypoint witness verification & exhaustive unreachability proof).
  3. Guard verification promotion (CANDIDATE_ONLY vs VERIFIED_COMPLETE).
  4. Decoupled operational exposure scoring (CVSS_base * omega * gamma).
  5. Curiosity Bucket emission (Bucket A: structural callers; Bucket B: semantic contracts).
  6. Tree-sitter AST static linkage & caller resolution.
  7. Swarm reflector prompt mutation with curiosity directives.
"""

import pytest
from scenarios.debate.graph_dataflow import (
    AssetExposureState,
    EpistemicEvaluationResult,
    FlowGraphSnapshot,
    FlowSignature,
    GuardVerificationState,
    ReachabilityState,
    compute_operational_exposure,
    evaluate_epistemic_graph,
    evaluate_graph_reachability,
    gamma_asset_exposure,
    omega_reachability,
)
from scenarios.debate.graphify_flow_extractor import (
    extract_graphify_flow_snapshot,
)
from scenarios.debate.reflector_agent import mutate_system_prompt
from scenarios.debate.pareto_registry import ParetoRegistry
from scenarios.debate.reflector_schemas import (
    CuriosityDirective,
    GraphDiagnosticSignature,
    ReflectRequest,
    classify_graph_diagnostic,
)


# ---------------------------------------------------------------------------
# 1. Multiplier & Operational Exposure Contract Tests
# ---------------------------------------------------------------------------


def test_omega_reachability_multipliers():
    assert omega_reachability(ReachabilityState.PROVEN_REACHABLE) == 1.0
    assert omega_reachability(ReachabilityState.UNKNOWN_REACHABLE) == 1.0  # Fail closed
    assert omega_reachability(ReachabilityState.PROVEN_UNREACHABLE) == 0.0


def test_gamma_asset_exposure_multipliers():
    assert gamma_asset_exposure(AssetExposureState.EXPOSED) == 1.0
    assert gamma_asset_exposure(AssetExposureState.UNKNOWN) == 1.0  # Fail closed
    assert gamma_asset_exposure(AssetExposureState.ISOLATED) == 0.0


def test_compute_operational_exposure_formula_and_short_circuit():
    # Proven reachable on exposed asset with CVSS 9.8
    assert compute_operational_exposure(
        reachability=ReachabilityState.PROVEN_REACHABLE,
        guard_verification=GuardVerificationState.ABSENT,
        asset_exposure=AssetExposureState.EXPOSED,
        cvss_base=9.8,
    ) == 9.8

    # Unknown reachability fails closed to omega=1.0
    assert compute_operational_exposure(
        reachability=ReachabilityState.UNKNOWN_REACHABLE,
        guard_verification=GuardVerificationState.CANDIDATE_ONLY,
        asset_exposure=AssetExposureState.UNKNOWN,
        cvss_base=7.5,
    ) == 7.5

    # Isolated asset (gamma = 0.0) -> exposure drops to 0.0
    assert compute_operational_exposure(
        reachability=ReachabilityState.PROVEN_REACHABLE,
        guard_verification=GuardVerificationState.ABSENT,
        asset_exposure=AssetExposureState.ISOLATED,
        cvss_base=8.0,
    ) == 0.0

    # Proven unreachable (omega = 0.0) -> exposure drops to 0.0
    assert compute_operational_exposure(
        reachability=ReachabilityState.PROVEN_UNREACHABLE,
        guard_verification=GuardVerificationState.ABSENT,
        asset_exposure=AssetExposureState.EXPOSED,
        cvss_base=10.0,
    ) == 0.0

    # Verified complete guard short-circuits exposure to 0.0 regardless of CVSS
    assert compute_operational_exposure(
        reachability=ReachabilityState.PROVEN_REACHABLE,
        guard_verification=GuardVerificationState.VERIFIED_COMPLETE,
        asset_exposure=AssetExposureState.EXPOSED,
        cvss_base=10.0,
    ) == 0.0


# ---------------------------------------------------------------------------
# 2. Tri-State Reachability & Proof Obligation Tests
# ---------------------------------------------------------------------------


def test_proven_reachable_with_entrypoint_witness():
    sig = FlowSignature(
        source_id="src_1",
        sink_id="sink_1",
        source_type="UNTRUSTED_INPUT",
        sink_type="MEMORY_WRITE",
        flow_type="CALL_ARGUMENT",
        is_entrypoint_reachable=True,
    )
    snap = FlowGraphSnapshot(
        snapshot_id="snap_witness",
        scenario_id="sc_witness",
        version=1,
        created_at=100.0,
        nodes={"src_1": {}, "sink_1": {}},
        signatures=[sig],
        has_unresolved_callers=False,
    )

    res = evaluate_epistemic_graph(snap, cvss_base=8.5, asset_exposure=AssetExposureState.EXPOSED)
    assert res.reachability == ReachabilityState.PROVEN_REACHABLE
    assert res.witness_path == ["src_1", "sink_1"]
    assert res.guard_verification == GuardVerificationState.ABSENT
    assert res.operational_exposure == 8.5
    assert res.risk_score == 1.0


def test_unknown_reachable_on_unresolved_callers_emits_bucket_a():
    sig = FlowSignature(
        source_id="src_1",
        sink_id="sink_1",
        source_type="UNTRUSTED_INPUT",
        sink_type="MEMORY_WRITE",
        flow_type="CALL_ARGUMENT",
        is_entrypoint_reachable=False,
    )
    snap = FlowGraphSnapshot(
        snapshot_id="snap_unresolved",
        scenario_id="sc_unresolved",
        version=1,
        created_at=100.0,
        nodes={"src_1": {}, "sink_1": {}},
        signatures=[sig],
        has_unresolved_callers=True,
    )

    res = evaluate_epistemic_graph(snap)
    assert res.reachability == ReachabilityState.UNKNOWN_REACHABLE
    assert res.witness_path is None
    assert res.risk_score == 1.0
    assert res.curiosity_bucket == "BUCKET_A_CALLER_STRUCTURAL"
    assert "Investigate callers" in (res.curiosity_directive or "")


def test_proven_unreachable_exhaustive_proof_obligation():
    # Complete snapshot with no untrusted flows to sinks -> PROVEN_UNREACHABLE
    snap_clean = FlowGraphSnapshot(
        snapshot_id="snap_clean",
        scenario_id="sc_clean",
        version=1,
        created_at=100.0,
        nodes={"src_1": {}, "sink_1": {}},
        signatures=[
            FlowSignature(
                source_id="src_1",
                sink_id="sink_1",
                source_type="INTERNAL_CONST",
                sink_type="MEMORY_WRITE",
                flow_type="CONST_ASSIGN",
            )
        ],
        is_complete=True,
        has_unresolved_callers=False,
    )

    res_clean = evaluate_epistemic_graph(snap_clean)
    assert res_clean.reachability == ReachabilityState.PROVEN_UNREACHABLE
    assert res_clean.operational_exposure == 0.0
    assert res_clean.risk_score == 0.05

    # Incomplete AST cannot satisfy exhaustive proof obligation -> fails closed to UNKNOWN_REACHABLE
    snap_incomplete = FlowGraphSnapshot(
        snapshot_id="snap_incomp",
        scenario_id="sc_incomp",
        version=1,
        created_at=100.0,
        nodes={"src_1": {}, "sink_1": {}},
        signatures=[],
        is_complete=False,
        parse_error="Truncated function body",
    )
    res_incomp = evaluate_epistemic_graph(snap_incomplete)
    assert res_incomp.reachability == ReachabilityState.UNKNOWN_REACHABLE
    assert res_incomp.risk_score == 1.0


# ---------------------------------------------------------------------------
# 3. Guard Verification Promotion (CANDIDATE_ONLY vs VERIFIED_COMPLETE)
# ---------------------------------------------------------------------------


def test_guard_verification_promotion_contract():
    # Syntactic guard present, but is_guard_verified=False -> CANDIDATE_ONLY
    sig_candidate = FlowSignature(
        source_id="src_1",
        sink_id="sink_1",
        source_type="UNTRUSTED_INPUT",
        sink_type="MEMORY_WRITE",
        flow_type="CALL_ARGUMENT",
        sanitizer_type="BOUNDS_CHECK",
        guarded_target="dest_buf",
        is_guard_verified=False,
    )
    snap_cand = FlowGraphSnapshot(
        snapshot_id="snap_cand",
        scenario_id="sc_cand",
        version=1,
        created_at=100.0,
        nodes={"src_1": {}, "sink_1": {"target_var": "dest_buf"}},
        signatures=[sig_candidate],
    )

    res_cand = evaluate_epistemic_graph(snap_cand, cvss_base=9.0)
    assert res_cand.guard_verification == GuardVerificationState.CANDIDATE_ONLY
    # Legacy risk score passes (0.05), but operational exposure remains active
    assert res_cand.risk_score == 0.05
    assert res_cand.operational_exposure == 9.0
    assert res_cand.curiosity_bucket == "BUCKET_B_CONTRACT_SEMANTIC"
    assert "Verify candidate guard" in (res_cand.curiosity_directive or "")

    # Promoted with symbolic/runtime verification proof -> VERIFIED_COMPLETE
    sig_verified = FlowSignature(
        source_id="src_1",
        sink_id="sink_1",
        source_type="UNTRUSTED_INPUT",
        sink_type="MEMORY_WRITE",
        flow_type="CALL_ARGUMENT",
        sanitizer_type="BOUNDS_CHECK",
        guarded_target="dest_buf",
        is_guard_verified=True,
        guard_proof_type="SYMBOLIC_COMPLETE",
    )
    snap_ver = FlowGraphSnapshot(
        snapshot_id="snap_ver",
        scenario_id="sc_ver",
        version=1,
        created_at=100.0,
        nodes={"src_1": {}, "sink_1": {"target_var": "dest_buf"}},
        signatures=[sig_verified],
    )

    res_ver = evaluate_epistemic_graph(snap_ver, cvss_base=9.0)
    assert res_ver.guard_verification == GuardVerificationState.VERIFIED_COMPLETE
    assert res_ver.reachability == ReachabilityState.PROVEN_UNREACHABLE
    assert res_ver.operational_exposure == 0.0
    assert res_ver.risk_score == 0.05
    assert res_ver.curiosity_bucket is None


# ---------------------------------------------------------------------------
# 4. AST Extractor Linkage & Unresolved Caller Detection
# ---------------------------------------------------------------------------


def test_ast_extractor_static_linkage_routes_to_bucket_a():
    # Static function without local callers
    code = """
    static void handle_packet(char *payload, int len) {
        char buf[64];
        memcpy(buf, payload, len);
    }
    """
    snapshot = extract_graphify_flow_snapshot(code, scenario_id="test_static_func")
    assert snapshot.has_unresolved_callers is True

    # Sinks emitted inside static function have is_entrypoint_reachable == False
    assert len(snapshot.signatures) >= 1
    assert snapshot.signatures[0].is_entrypoint_reachable is False

    res = evaluate_epistemic_graph(snapshot)
    assert res.reachability == ReachabilityState.UNKNOWN_REACHABLE
    assert res.curiosity_bucket == "BUCKET_A_CALLER_STRUCTURAL"


def test_ast_extractor_public_entrypoint_reaches_proven_reachable():
    code = """
    int main(int argc, char **argv) {
        char buf[64];
        memcpy(buf, argv[1], 100);
        return 0;
    }
    """
    snapshot = extract_graphify_flow_snapshot(code, scenario_id="test_main_entrypoint")
    assert snapshot.has_unresolved_callers is False
    assert snapshot.signatures[0].is_entrypoint_reachable is True

    res = evaluate_epistemic_graph(snapshot)
    assert res.reachability == ReachabilityState.PROVEN_REACHABLE
    assert res.witness_path is not None


# ---------------------------------------------------------------------------
# 5. Reflector Agent Curiosity Directive Integration
# ---------------------------------------------------------------------------


def test_reflector_agent_injects_curiosity_directive(tmp_path):
    registry = ParetoRegistry(tmp_path)
    directive = CuriosityDirective(
        bucket="BUCKET_A_CALLER_STRUCTURAL",
        target_symbol="handle_packet",
        reason="Static function has no callers in snippet",
        directive_text="Investigate callers of handle_packet before modifying buffer size.",
    )

    diag = GraphDiagnosticSignature(
        scenario_id="sc_test",
        predicate_family="BUFFER_OVERFLOW",
        failure_bucket="B_SINK_MISSING",
        curiosity_directive=directive,
    )

    req = ReflectRequest(
        attempt_index=1,
        scenario_id="sc_test",
        predicate_family="BUFFER_OVERFLOW",
        taxonomy_bucket="memory_safety",
        code_text="static void handle_packet() {}",
        graph_diagnostic=diag,
        current_system_prompt="Analyze code safety.",
        curiosity_directive=directive,
    )

    resp = mutate_system_prompt(req, registry)
    assert resp.status == "SUCCESS"
    assert "[Curiosity Directive - BUCKET_A_CALLER_STRUCTURAL]" in resp.mutated_system_prompt
    assert directive.directive_text in resp.mutated_system_prompt
    assert resp.curiosity_directive == directive
