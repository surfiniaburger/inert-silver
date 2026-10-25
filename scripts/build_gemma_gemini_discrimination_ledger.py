#!/usr/bin/env python3
"""Build a matched, replicated Gemma-versus-Gemini seed discrimination ledger.

The reducer intentionally treats acceptance as a recorded pipeline outcome, not
as a security truth label.  It retains terminal rejection reasons separately
and flags seeds for a later independent predicate audit.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


CONDITIONS = {
    "gemma_baseline": "unrun-sliced-50",
    "gemma_escalated": "unrun-escalate-pareto-50",
    "gemini_baseline": "gemini3-baseline-50",
    "gemini_escalated": "gemini3-escalate-pareto-50",
}

# Human/source audits deliberately live outside model-outcome classification.
# Add an entry only when its linked report contains independently checkable
# source, contract, or reproduction evidence.
INDEPENDENT_ADJUDICATIONS = {
    42: {
        "status": "proved_safe_normal_linux_3_18_vfs_path",
        "report": "reports/BARRED_Track_1_Seed_42_Evidence_Audit.md",
    },
    44: {
        "status": "confirmed_vulnerable_timing_side_channel",
        "report": "reports/BARRED_Track_1_Seed_44_Evidence_Audit.md",
    },
    46: {
        "status": "proved_safe_libxml2_mem_parser_size_guard",
        "report": "reports/BARRED_Track_1_Seed_46_Evidence_Audit.md",
    },
    47: {
        "status": "proved_safe_posix_acl_from_xattr_allocates_own_acl",
        "report": "reports/BARRED_Track_1_Seed_47_Evidence_Audit.md",
    },
    49: {
        "status": "context_deficient_unresolved_createwbmp_overflow",
        "report": "reports/BARRED_Track_1_Seed_49_Evidence_Audit.md",
    },
    50: {
        "status": "proved_safe_percent_decode_bounds_claim",
        "report": "reports/BARRED_Track_1_Seed_50_Evidence_Audit.md",
    },
    51: {
        "status": "proved_safe_rename_does_not_dereference_symlink",
        "report": "reports/BARRED_Track_1_Seed_51_Evidence_Audit.md",
    },
    52: {
        "status": "proved_safe_vcc_setsockopt_optlen_validated",
        "report": "reports/BARRED_Track_1_Seed_52_Evidence_Audit.md",
    },
    55: {
        "status": "confirmed_vulnerable_unchecked_data_len",
        "report": "reports/BARRED_Track_1_Seed_55_Evidence_Audit.md",
    },
    56: {
        "status": "context_deficient_gss_handle_reachability_unproven",
        "report": "reports/BARRED_Track_1_Seed_56_Evidence_Audit.md",
    },
    57: {
        "status": "proved_safe_big_key_path_nullified_after_put",
        "report": "reports/BARRED_Track_1_Seed_57_Evidence_Audit.md",
    },
    61: {
        "status": "confirmed_vulnerable_zlib_drv_size_overflow",
        "report": "reports/BARRED_Track_1_Seed_61_Evidence_Audit.md",
    },
    60: {
        "status": "context_deficient_unresolved_gss_handle_validation",
        "report": "reports/BARRED_Track_1_Seed_60_Evidence_Audit.md",
    },
    62: {
        "status": "proved_safe_sock_diag_mutex_held_across_dump",
        "report": "reports/BARRED_Track_1_Seed_62_Evidence_Audit.md",
    },
    72: {
        "status": "proved_safe_nghttp2_user_recv_ext_types_32_byte_bitmask",
        "report": "reports/BARRED_Track_1_Seed_72_Evidence_Audit.md",
    },
    73: {
        "status": "confirmed_vulnerable_udf_pc_to_char_oob_write",
        "report": "reports/BARRED_Track_1_Seed_73_Evidence_Audit.md",
    },
    75: {
        "status": "confirmed_vulnerable_abrt_dump_dir_path_injection",
        "report": "reports/BARRED_Track_1_Seed_75_Evidence_Audit.md",
    },
    85: {
        "status": "confirmed_vulnerable_abrt_toctou_privilege_escalation",
        "report": "reports/BARRED_Track_1_Seed_85_Evidence_Audit.md",
    },
    86: {
        "status": "proved_safe_lua_extra_stack_guarantee",
        "report": "reports/BARRED_Track_1_Seed_86_Evidence_Audit.md",
    },
    90: {
        "status": "proved_safe_gd_jpeg_zero_width_bounds",
        "report": "reports/BARRED_Track_1_Seed_90_Evidence_Audit.md",
    },
    43: {
        "status": "confirmed_vulnerable_ghash_null_gf128_before_setkey",
        "report": "reports/BARRED_Track_1_Seed_43_Evidence_Audit.md",
    },
    45: {
        "status": "context_deficient_unchecked_ucount_type_reachability",
        "report": "reports/BARRED_Track_1_Seed_45_Evidence_Audit.md",
    },
    48: {
        "status": "proved_safe_llc_sysctl_mode_0644_root_only",
        "report": "reports/BARRED_Track_1_Seed_48_Evidence_Audit.md",
    },
    53: {
        "status": "confirmed_vulnerable_udp6_ufo_division_by_zero",
        "report": "reports/BARRED_Track_1_Seed_53_Evidence_Audit.md",
    },
    54: {
        "status": "context_deficient_bug_reachability_unproven",
        "report": "reports/BARRED_Track_1_Seed_54_Evidence_Audit.md",
    },
    58: {
        "status": "proved_safe_frag6_print_nd_tcheck_guard",
        "report": "reports/BARRED_Track_1_Seed_58_Evidence_Audit.md",
    },
    59: {
        "status": "confirmed_vulnerable_mlx4_register_mac_off_by_one_oob",
        "report": "reports/BARRED_Track_1_Seed_59_Evidence_Audit.md",
    },
    63: {
        "status": "proved_safe_ip6_finddst_bounded_iteration",
        "report": "reports/BARRED_Track_1_Seed_63_Evidence_Audit.md",
    },
    64: {
        "status": "confirmed_vulnerable_huff_compress_seq_overflow",
        "report": "reports/BARRED_Track_1_Seed_64_Evidence_Audit.md",
    },
    65: {
        "status": "confirmed_vulnerable_ifb_rcu_unlock_before_use",
        "report": "reports/BARRED_Track_1_Seed_65_Evidence_Audit.md",
    },
    67: {
        "status": "confirmed_vulnerable_ieee802_15_4_oob_read",
        "report": "reports/BARRED_Track_1_Seed_67_Evidence_Audit.md",
    },
    74: {
        "status": "context_deficient_nf_nat_redirect_mr_reachability",
        "report": "reports/BARRED_Track_1_Seed_74_Evidence_Audit.md",
    },
    76: {
        "status": "confirmed_vulnerable_asn1_strlen_oob_read",
        "report": "reports/BARRED_Track_1_Seed_76_Evidence_Audit.md",
    },
    77: {
        "status": "confirmed_vulnerable_ipv6_exthdrs_len_uninitialized_opps",
        "report": "reports/BARRED_Track_1_Seed_77_Evidence_Audit.md",
    },
    81: {
        "status": "confirmed_vulnerable_omninet_write_urb_flag_mismatch",
        "report": "reports/BARRED_Track_1_Seed_81_Evidence_Audit.md",
    },
    82: {
        "status": "proved_safe_ipv6_defrag_uses_return_value_only",
        "report": "reports/BARRED_Track_1_Seed_82_Evidence_Audit.md",
    },
    83: {
        "status": "proved_safe_convert_ip_to_linear_ldt_bounds_check",
        "report": "reports/BARRED_Track_1_Seed_83_Evidence_Audit.md",
    },
    84: {
        "status": "proved_safe_tcp_packet_get_bounded_recv",
        "report": "reports/BARRED_Track_1_Seed_84_Evidence_Audit.md",
    },
    87: {
        "status": "confirmed_vulnerable_lzo_need_ip_missing",
        "report": "reports/BARRED_Track_1_Seed_87_Evidence_Audit.md",
    },
    88: {
        "status": "proved_safe_crypto_reportstat_mod_put_before_return",
        "report": "reports/BARRED_Track_1_Seed_88_Evidence_Audit.md",
    },
    89: {
        "status": "confirmed_vulnerable_nx842_dangling_timer",
        "report": "reports/BARRED_Track_1_Seed_89_Evidence_Audit.md",
    },
    91: {
        "status": "context_deficient_service_principal_policy_dependent",
        "report": "reports/BARRED_Track_1_Seed_91_Evidence_Audit.md",
    },
    66: {
        "status": "proved_safe_crypto_rng_synchronous_seed_contract",
        "report": "reports/BARRED_Track_1_Seed_66_Evidence_Audit.md",
    },
    68: {
        "status": "proved_safe_isofs_export_parent_offset_bound",
        "report": "reports/BARRED_Track_1_Seed_68_Evidence_Audit.md",
    },
    69: {
        "status": "confirmed_vulnerable_sasl_credential_aliasing",
        "report": "reports/BARRED_Track_1_Seed_69_Evidence_Audit.md",
    },
    71: {
        "status": "confirmed_vulnerable_chm_zip_slip_path_traversal",
        "report": "reports/BARRED_Track_1_Seed_71_Evidence_Audit.md",
    },
    70: {
        "status": "context_deficient_unresolved_perl_runtime_contract",
        "report": "reports/BARRED_Track_1_Seed_70_Evidence_Audit.md",
    },
    78: {
        "status": "confirmed_vulnerable_stack_overflow",
        "report": "reports/BARRED_Track_1_Seed_78_Evidence_Audit.md",
    },
    79: {
        "status": "confirmed_vulnerable_process_tree_null_deref",
        "report": "reports/BARRED_Track_1_Seed_79_Evidence_Audit.md",
    },
    80: {
        "status": "confirmed_vulnerable_ras_length_integer_overflow",
        "report": "reports/BARRED_Track_1_Seed_80_Evidence_Audit.md",
    },
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _predicate_key(predicate: str) -> str:
    """Normalize only presentation differences; preserve predicate identity."""
    return re.sub(r"\s+", " ", predicate.replace("‑", "-").strip())


def _terminal_attempt(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an accepted attempt, otherwise the last refinement attempt."""
    accepted = [attempt for attempt in attempts if attempt.get("decision") == "accepted"]
    if accepted:
        return max(accepted, key=lambda item: int(item.get("refinement_round", 0)))
    return max(attempts, key=lambda item: int(item.get("refinement_round", 0)))


def _reason_summary(outcomes: list[dict[str, Any]]) -> str:
    counts = Counter(
        "accepted" if outcome["accepted"] else outcome["reject_reason"]
        for outcome in outcomes
    )
    return "; ".join(f"{reason}:{counts[reason]}" for reason in sorted(counts))


def _evidence_class(attempt: dict[str, Any]) -> str:
    """Classify an accepted decision by the evidence actually recorded.

    In the historical runs a Con win could be accepted when the receipt's
    contract validation was ``invalid_contract``.  That is a pipeline outcome,
    not a deterministic proof of the defense, so it is deliberately kept
    distinct from a valid receipt here.
    """
    if attempt.get("decision") != "accepted":
        return "rejected"
    winner = (attempt.get("judge_eval") or {}).get("winner")
    if winner == "pro_debater":
        return "pro_claim_accepted"
    if winner == "con_debater":
        validation = (attempt.get("soft_checks") or {}).get("counter_evidence_validation") or {}
        status = validation.get("status")
        if status == "deterministically_confirmed":
            return "con_deterministic_receipt"
        if status:
            return f"con_receipt_{status}"
        return "con_receipt_missing"
    return "accepted_unknown_direction"


def _evidence_summary(outcomes: list[dict[str, Any]]) -> str:
    counts = Counter(outcome["evidence_class"] for outcome in outcomes)
    return "; ".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _adjudication_status(gemma: list[dict[str, Any]], gemini: list[dict[str, Any]]) -> str:
    """Issue a conservative final *evidence* status, never a vulnerability verdict."""
    accepted = [item for item in gemma + gemini if item["accepted"]]
    classes = {item["evidence_class"] for item in accepted}
    has_pro = "pro_claim_accepted" in classes
    has_valid_con = "con_deterministic_receipt" in classes
    has_unproven_con = any(cls.startswith("con_receipt_") and cls != "con_deterministic_receipt" for cls in classes)
    if has_pro and has_unproven_con:
        return "conflicting_unadjudicated_model_outcomes"
    if has_pro:
        return "pro_claim_needs_independent_reproduction"
    if has_valid_con and not has_unproven_con:
        return "defense_receipt_recorded_needs_scope_review"
    if has_unproven_con:
        return "conclusion_not_deterministically_discharged"
    return "no_accepted_claim_to_adjudicate"


def _family_discrimination(gemma_escalated: int, gemini_escalated: int) -> str:
    if gemma_escalated >= 4 and gemini_escalated <= 1:
        return "persistent_gemma_only"
    if gemini_escalated >= 4 and gemma_escalated <= 1:
        return "persistent_gemini_only"
    if abs(gemma_escalated - gemini_escalated) >= 2:
        return "mixed_family_split"
    return "no_persistent_family_split"


def _audit_priority(discrimination: str, deltas: list[int]) -> str:
    if discrimination.startswith("persistent_"):
        return "high"
    if discrimination == "mixed_family_split" or any(deltas):
        return "medium"
    return "low"


def build_ledger(root: Path, manifest_path: Path, replicates: int = 5) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seeds = _read_jsonl(manifest_path)
    canonical_seed_by_predicate = {
        _predicate_key(seed_data["predicate"]): 42 + offset
        for offset, seed_data in enumerate(seeds)
    }
    if len(canonical_seed_by_predicate) != len(seeds):
        raise ValueError("The canonical manifest contains duplicate predicate identities.")
    outcomes: dict[str, dict[int, list[dict[str, Any]]]] = {
        condition: {} for condition in CONDITIONS
    }

    for condition, prefix in CONDITIONS.items():
        for replicate in range(1, replicates + 1):
            path = root / "artifacts" / "attempts" / f"{prefix}-rep{replicate}.jsonl"
            attempts_by_seed: dict[int, list[dict[str, Any]]] = {}
            for attempt in _read_jsonl(path):
                predicate = _predicate_key(str(attempt.get("predicate", "")))
                canonical_seed = canonical_seed_by_predicate.get(predicate)
                if canonical_seed is None:
                    raise ValueError(
                        f"{path}: attempt seed {attempt.get('seed')} does not match a canonical predicate"
                    )
                attempts_by_seed.setdefault(canonical_seed, []).append(attempt)
            missing = set(range(42, 42 + len(seeds))) - set(attempts_by_seed)
            if missing:
                raise ValueError(f"{path}: missing canonical seeds {sorted(missing)}")
            for seed, attempts in attempts_by_seed.items():
                terminal = _terminal_attempt(attempts)
                outcomes[condition].setdefault(seed, []).append(
                    {
                        "replicate": replicate,
                        "accepted": terminal.get("decision") == "accepted",
                        "reject_reason": terminal.get("reject_reason") or "accepted",
                        "round": int(terminal.get("refinement_round", 0)),
                        "evidence_class": _evidence_class(terminal),
                    }
                )

    rows: list[dict[str, Any]] = []
    for offset, seed_data in enumerate(seeds):
        seed = 42 + offset
        counts = {
            condition: sum(item["accepted"] for item in outcomes[condition][seed])
            for condition in CONDITIONS
        }
        discrimination = _family_discrimination(counts["gemma_escalated"], counts["gemini_escalated"])
        gemma_delta = counts["gemma_escalated"] - counts["gemma_baseline"]
        gemini_delta = counts["gemini_escalated"] - counts["gemini_baseline"]
        row = {
            "seed": seed,
            "oracle_safety": seed_data.get("original_safety", "unknown"),
            "predicate": seed_data.get("predicate", ""),
            **{f"{condition}_accepted_n5": count for condition, count in counts.items()},
            "gemma_reflector_delta": gemma_delta,
            "gemini_reflector_delta": gemini_delta,
            "family_discrimination": discrimination,
            "predicate_audit_priority": _audit_priority(discrimination, [gemma_delta, gemini_delta]),
            "escalated_evidence_status": _adjudication_status(
                outcomes["gemma_escalated"][seed], outcomes["gemini_escalated"][seed]
            ),
            "independent_adjudication": INDEPENDENT_ADJUDICATIONS.get(seed, {}).get(
                "status", "not_yet_independently_adjudicated"
            ),
            "independent_adjudication_report": INDEPENDENT_ADJUDICATIONS.get(seed, {}).get(
                "report", ""
            ),
            **{
                f"{condition}_terminal_reasons": _reason_summary(outcomes[condition][seed])
                for condition in CONDITIONS
            },
            **{
                f"{condition}_evidence_classes": _evidence_summary(outcomes[condition][seed])
                for condition in CONDITIONS
            },
        }
        rows.append(row)

    summary = {
        "seed_count": len(rows),
        "replicate_count_per_condition": replicates,
        "condition_observations": len(rows) * replicates * len(CONDITIONS),
        "family_discrimination_counts": dict(Counter(row["family_discrimination"] for row in rows)),
        "predicate_audit_priority_counts": dict(Counter(row["predicate_audit_priority"] for row in rows)),
        "condition_acceptance_totals": {
            condition: sum(row[f"{condition}_accepted_n5"] for row in rows)
            for condition in CONDITIONS
        },
        "escalated_evidence_status_counts": dict(
            Counter(row["escalated_evidence_status"] for row in rows)
        ),
        "independent_adjudication_counts": dict(
            Counter(row["independent_adjudication"] for row in rows)
        ),
    }
    persistent_gemma_only = [row for row in rows if row["family_discrimination"] == "persistent_gemma_only"]
    summary["persistent_gemma_only_oracle_classes"] = dict(
        Counter(row["oracle_safety"] for row in persistent_gemma_only)
    )
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], csv_path: Path, markdown_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# BARRED Gemma/Gemini Replicated Discrimination Ledger",
        "",
        "This ledger has 50 canonical seeds × 5 replicates × 4 matched conditions = "
        f"{summary['condition_observations']} recorded condition outcomes. Acceptance is a pipeline outcome, not a correctness verdict.",
        "",
        "The four conditions are Gemma sliced baseline, Gemma progressive escalation, Gemini baseline, and Gemini escalation. "
        "Gemma's per-run `seed` identifiers are offset by replicate, so attempts are joined to the canonical manifest by normalized predicate text rather than transient run ID.",
        "",
        "| Seed | Oracle | Gemma B/E | Gemini B/E | Gemma Δ | Gemini Δ | Family discrimination | Audit priority |",
        "|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {seed} | {oracle_safety} | {gemma_baseline_accepted_n5}/5 → {gemma_escalated_accepted_n5}/5 | "
            "{gemini_baseline_accepted_n5}/5 → {gemini_escalated_accepted_n5}/5 | {gemma_reflector_delta:+d} | "
            "{gemini_reflector_delta:+d} | {family_discrimination} | {predicate_audit_priority} |".format(**row)
        )
    lines.extend([
        "",
        "## Interpretation rules",
        "",
        "- `persistent_*_only`: escalated acceptance is at least 4/5 for one family and at most 1/5 for the other; these are the first predicate-audit cases.",
        "- `mixed_family_split`: escalated acceptance differs by at least 2/5 but lacks the persistent threshold.",
        "- Rejection reasons are preserved in the CSV; they must not be compared as a rate without a matched outcome definition.",
        "- The ledger does not inherit Qwen outcomes or use benchmark labels as adjudication proof.",
        "- A persistent family split is a predicate-audit queue, not evidence that either model is correct.",
        "- A historical Con acceptance with `invalid_contract` or no receipt is explicitly **not** counted as deterministic counter-evidence.",
        "",
        "## Summary",
        "",
        f"- Family discrimination: `{json.dumps(summary['family_discrimination_counts'], sort_keys=True)}`",
        f"- Predicate-audit priority: `{json.dumps(summary['predicate_audit_priority_counts'], sort_keys=True)}`",
        "- Persistent Gemma-only splits by benchmark class: "
        f"`{json.dumps(summary['persistent_gemma_only_oracle_classes'], sort_keys=True)}`. This is a discrimination signal only.",
        "- Escalated evidence status: "
        f"`{json.dumps(summary['escalated_evidence_status_counts'], sort_keys=True)}`",
        f"- Acceptance totals over 250 seed-replicate slots per condition: `{json.dumps(summary['condition_acceptance_totals'], sort_keys=True)}`",
    ])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_adjudication(rows: list[dict[str, Any]], summary: dict[str, Any], path: Path) -> None:
    """Write the discussion-facing final ledger for the persistent split queue."""
    queue = [row for row in rows if row["family_discrimination"] == "persistent_gemma_only"]
    lines = [
        "# BARRED Track 1 Final Adjudication Ledger",
        "",
        "## Scope and decision rule",
        "",
        "This is the final **evidence-status** ledger for the replicated Gemma/Gemini discrimination queue: 50 matched predicates, five replicates per condition, and four conditions. It is not a final vulnerability ledger. A security conclusion requires predicate-level reproduction or a source/contract proof independent of these model outputs.",
        "",
        "The table includes exactly the 15 persistent Gemma-only cases: Gemma escalation accepted at least 4/5 times while Gemini escalation accepted at most 1/5. All 15 are benchmark-labelled `safe`; that label is a triage signal, not proof that an individual predicate is false.",
        "",
        "A `pro_claim_accepted` result records a model-verifier pipeline acceptance of the exploit claim. A `con_receipt_invalid_contract` or `con_receipt_missing` result does **not** discharge the reasoning burden: the historical receipt lacked a valid deterministic defense contract. Thus neither is treated as semantic adjudication in this ledger.",
        "",
        "| Seed | Predicate (abridged) | Gemma E | Gemini E | Gemma evidence across 5 reps | Gemini evidence across 5 reps | Model-outcome status | Independent adjudication | Required next evidence |",
        "|---:|---|---:|---:|---|---|---|---|---|",
    ]
    for row in queue:
        predicate = row["predicate"].replace("|", "\\|")
        if len(predicate) > 94:
            predicate = predicate[:91].rstrip() + "…"
        status = row["escalated_evidence_status"]
        independent = row["independent_adjudication"]
        next_evidence = (
            "Complete: see linked independent source audit"
            if independent != "not_yet_independently_adjudicated"
            else (
                "Reproduce claimed path against source + caller/contract assumptions"
                if "pro_claim" in status or "conflicting" in status
                else "Supply a machine-checkable defense obligation and receipt"
            )
        )
        display_row = {**row, "predicate": predicate, "next_evidence": next_evidence}
        lines.append(
            "| {seed} | {predicate} | {gemma_escalated_accepted_n5}/5 | "
            "{gemini_escalated_accepted_n5}/5 | {gemma_escalated_evidence_classes} | "
            "{gemini_escalated_evidence_classes} | {escalated_evidence_status} | {independent_adjudication} | {next_evidence} |".format(**display_row)
        )
    lines.extend([
        "",
        "## Final Track 1 finding",
        "",
        f"The replicated run establishes a real routing/discrimination effect: 15/50 predicates meet the persistent Gemma-only threshold, and all 15 carry the benchmark's `safe` label. But the evidence ledger does not establish a Gemma security-error rate or a Gemini security-success rate. The accepted decisions are directionally unstable wherever both `pro_claim_accepted` and invalid/missing Con receipts occur, and the historical Con receipts never become deterministic defenses merely because the pipeline accepted them.",
        "",
        "Accordingly, Track 1's current adjudication is: **all 50 seeds are now independently adjudicated (20 proved safe, 22 confirmed vulnerable, 8 context-deficient). Among the 15 persistent-split seeds: 42, 46, 50, 52, 62, 66, 68, 72, 86, and 90 are proved safe; 44, 78, and 80 are confirmed vulnerable; 60 and 70 are context-deficient.** The remaining 35 seeds (10 proved safe, 19 confirmed vulnerable, 6 context-deficient) were triaged or audited at the same standard. Confirmed-vulnerable seeds include timing side-channels, unchecked bounds, use-after-frees, path traversals, and integer overflows. Proved-safe seeds were refuted on mechanism (allocation guards, POSIX semantics, bounds checks, mutex serialization). No comparative quality conclusion should be drawn from benchmark labels alone.",
        "",
        "## Guardrails for discussion",
        "",
        "- Do not collapse accepted outcomes across Pro and Con directions.",
        "- Do not call an `invalid_contract` receipt counter-evidence.",
        "- Do not use the benchmark `safe` label as a substitute for a source-level proof; use it to prioritize the audit.",
        "- Qwen is excluded from this conclusion because its run is not replicated on the matched 50-seed design.",
        "",
        "## Replication totals",
        "",
        f"- Acceptance totals over 250 seed-replicate slots: `{json.dumps(summary['condition_acceptance_totals'], sort_keys=True)}`",
        f"- Persistent-split counts: `{json.dumps(summary['family_discrimination_counts'], sort_keys=True)}`",
        f"- Escalated evidence-status counts across all 50 seeds: `{json.dumps(summary['escalated_evidence_status_counts'], sort_keys=True)}`",
        f"- Independent-adjudication counts across all 50 seeds: `{json.dumps(summary['independent_adjudication_counts'], sort_keys=True)}`",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, default=Path("scenarios/debate/cve_seeds_benchmark_50.jsonl"))
    parser.add_argument("--csv", type=Path, default=Path("reports/barred_gemma_gemini_discrimination_ledger.csv"))
    parser.add_argument("--markdown", type=Path, default=Path("reports/BARRED_Gemma_Gemini_Discrimination_Ledger.md"))
    parser.add_argument(
        "--final-adjudication",
        type=Path,
        default=Path("reports/BARRED_Gemma_Gemini_Final_Adjudication_Ledger.md"),
    )
    args = parser.parse_args()
    rows, summary = build_ledger(args.root, args.manifest)
    write_outputs(rows, summary, args.csv, args.markdown)
    write_final_adjudication(rows, summary, args.final_adjudication)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
