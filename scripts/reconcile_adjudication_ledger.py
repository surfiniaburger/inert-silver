#!/usr/bin/env python3
"""
Canonical Adjudication Ledger Reducer for BARRED Debate Experiments.

Audits episode attempts and output corpus line-by-line to produce a reconciled,
single-source-of-truth summary and markdown table.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def reconcile_run(
    seeds_path: str = "scenarios/debate/cve_seeds_benchmark_50.jsonl",
    attempts_path: str = "artifacts/attempts/gemini3-escalate-pareto-50-rep1.jsonl",
    output_path: str = "test_corpus_gemini3_escalate_pareto_50_rep1.jsonl",
    manifest_path: str = "artifacts/runs/gemini3-escalate-pareto-50-rep1/batch_manifest.json",
) -> Dict[str, Any]:
    # 1. Load benchmark seeds
    seeds_bench: List[Dict[str, Any]] = []
    with open(seeds_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                seeds_bench.append(json.loads(line.strip()))

    # 2. Load attempts indexed by seed
    attempts_by_seed: Dict[int, List[Dict[str, Any]]] = {}
    with open(attempts_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                att = json.loads(line.strip())
                s = att.get("seed")
                attempts_by_seed.setdefault(s, []).append(att)

    # 3. Load accepted output corpus indexed by seed
    output_by_seed: Dict[int, Dict[str, Any]] = {}
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line.strip())
                s = row.get("metadata", {}).get("seed")
                output_by_seed[s] = row

    # 4. Load batch manifest
    manifest_items: Dict[int, Dict[str, Any]] = {}
    if Path(manifest_path).exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
            for item in m.get("items", []):
                manifest_items[item["seed"]] = item

    rows: List[Dict[str, Any]] = []
    r0_counts = Counter()
    r1_counts = Counter()
    verdict_counts = Counter()
    basis_counts = Counter()

    for i, s_obj in enumerate(seeds_bench):
        seed_id = 42 + i
        safety = s_obj.get("original_safety", "unknown").lower()
        topic = s_obj.get("topic", "")
        predicate = s_obj.get("predicate", "")
        
        atts = attempts_by_seed.get(seed_id, [])
        r0_att = next((a for a in atts if a.get("refinement_round") == 0), None)
        r1_att = next((a for a in atts if a.get("refinement_round") == 1), None)

        r0_decision = r0_att.get("decision") if r0_att else "no_r0"
        r0_reason = r0_att.get("reject_reason") if r0_att else ""

        r1_decision = r1_att.get("decision") if r1_att else "—"
        r1_reason = r1_att.get("reject_reason") if r1_att else ""

        is_accepted = seed_id in output_by_seed
        out_row = output_by_seed.get(seed_id)
        
        final_verdict = out_row["output"]["verdict"] if is_accepted else "—"
        support_level = out_row["output"]["support_level"] if is_accepted else "—"
        basis = out_row["output"]["acceptance_basis"] if is_accepted else (r1_reason or r0_reason or "unknown_error")

        # Accounting state
        if r0_decision == "accepted":
            stage_cleared = "Round 0"
            r0_counts[safety] += 1
        elif r1_decision == "accepted":
            stage_cleared = "Round 1 (Recovered)"
            r1_counts[safety] += 1
        else:
            stage_cleared = "Terminal Rejected"

        if is_accepted:
            verdict_counts[final_verdict] += 1
            basis_counts[basis] += 1

        rows.append({
            "index": i,
            "seed": seed_id,
            "oracle_safety": safety,
            "topic": topic,
            "predicate": predicate,
            "r0_decision": r0_decision,
            "r0_reason": r0_reason,
            "r1_decision": r1_decision,
            "r1_reason": r1_reason,
            "stage_cleared": stage_cleared,
            "is_accepted": is_accepted,
            "final_verdict": final_verdict,
            "support_level": support_level,
            "basis": basis,
        })

    summary = {
        "total_seeds": len(seeds_bench),
        "total_accepted_rows": len(output_by_seed),
        "yield_percent": (len(output_by_seed) / len(seeds_bench)) * 100.0,
        "round_0_passes": {
            "vulnerable": r0_counts["vulnerable"],
            "safe": r0_counts["safe"],
            "total": sum(r0_counts.values()),
        },
        "round_1_recoveries": {
            "vulnerable": r1_counts["vulnerable"],
            "safe": r1_counts["safe"],
            "total": sum(r1_counts.values()),
        },
        "net_accepted_by_class": {
            "vulnerable": r0_counts["vulnerable"] + r1_counts["vulnerable"],
            "safe": r0_counts["safe"] + r1_counts["safe"],
        },
        "terminal_quarantined_by_class": {
            "vulnerable": 25 - (r0_counts["vulnerable"] + r1_counts["vulnerable"]),
            "safe": 25 - (r0_counts["safe"] + r1_counts["safe"]),
        },
        "verdict_distribution_in_accepted": dict(verdict_counts),
        "acceptance_basis_distribution": dict(basis_counts),
        "rows": rows,
    }
    return summary


def generate_markdown_ledger(summary: Dict[str, Any]) -> str:
    lines = [
        "| Idx | Seed | Oracle Class | Codebase & Predicate | Round 0 Status | Round 1 Escalation | Final Status | Adjudication Verdict | Acceptance Basis / Failure Cause |",
        "| :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :--- |",
    ]
    for r in summary["rows"]:
        idx = r["index"]
        seed = r["seed"]
        cls_str = "Vulnerable" if r["oracle_safety"] == "vulnerable" else "Safe"
        pred = f"`{r['topic'][:22]}`: {r['predicate'][:45]}..."
        
        r0 = "Accepted" if r["r0_decision"] == "accepted" else f"Rejected ({r['r0_reason'][:25]})"
        
        if r["r1_decision"] == "—":
            r1 = "—"
        elif r["r1_decision"] == "accepted":
            r1 = "Accepted"
        else:
            r1 = f"Rejected ({r['r1_reason'][:25]})"
            
        status = "**ACCEPTED**" if r["is_accepted"] else "QUARANTINED"
        verdict = f"`{r['final_verdict']}`" if r["is_accepted"] else "—"
        cause = f"`{r['basis']}`"

        lines.append(f"| **{idx}** | **{seed}** | {cls_str} | {pred} | {r0} | {r1} | {status} | {verdict} | {cause} |")
    return "\n".join(lines)


if __name__ == "__main__":
    summ = reconcile_run()
    out_json = Path("reports/gemini3_escalate_pareto_50_summary.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=2)
    print(f"Summary written to {out_json}")
    print(f"Total accepted: {summ['total_accepted_rows']} / {summ['total_seeds']}")
    print(f"Vuln: {summ['net_accepted_by_class']['vulnerable']} / 25 | Safe: {summ['net_accepted_by_class']['safe']} / 25")
    print(f"R0 Passes: {summ['round_0_passes']['total']} | R1 Recoveries: {summ['round_1_recoveries']['total']}")
