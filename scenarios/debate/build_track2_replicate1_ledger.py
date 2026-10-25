#!/usr/bin/env python3
"""
build_track2_replicate1_ledger.py

Reconciles the 50-seed benchmark with Track 1 independent adjudications
and joins against Track 2 Replicate 1 attempts for Arms A, B, C, D.
Produces:
  - reports/BARRED_Track_2_Joined_Correctness_Ledger.csv
  - Updates reports/BARRED_Track_2_Replicate_1_Correctness_Report.md
"""

import json
import csv
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path("/Users/surfiniaburger/Desktop/modular-metacog-swarm-v3/agent_training/silver-one")
SEEDS_FILE = ROOT / "scenarios/debate/cve_seeds_benchmark_50.jsonl"
OUT_CSV = ROOT / "reports/BARRED_Track_2_Joined_Correctness_Ledger.csv"
OUT_MD = ROOT / "reports/BARRED_Track_2_Replicate_1_Correctness_Report.md"

# Ground Truth Definition based on Track 1 Audits & Triage
AUDIT_VERDICTS = {
    # 28 Deep-Audited Seeds
    42: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_42_Evidence_Audit.md"),
    44: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_44_Evidence_Audit.md"),
    46: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_46_Evidence_Audit.md"),
    47: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_47_Evidence_Audit.md"),
    49: ("context_deficient", "full_audit", "reports/BARRED_Track_1_Seed_49_Evidence_Audit.md"),
    50: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_50_Evidence_Audit.md"),
    51: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_51_Evidence_Audit.md"),
    52: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_52_Evidence_Audit.md"),
    55: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_55_Evidence_Audit.md"),
    56: ("context_deficient", "full_audit", "reports/BARRED_Track_1_Seed_56_Evidence_Audit.md"),
    57: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_57_Evidence_Audit.md"),
    60: ("context_deficient", "full_audit", "reports/BARRED_Track_1_Seed_60_Evidence_Audit.md"),
    61: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_61_Evidence_Audit.md"),
    62: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_62_Evidence_Audit.md"),
    66: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_66_Evidence_Audit.md"),
    68: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_68_Evidence_Audit.md"),
    69: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_69_Evidence_Audit.md"),
    70: ("context_deficient", "full_audit", "reports/BARRED_Track_1_Seed_70_Evidence_Audit.md"),
    71: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_71_Evidence_Audit.md"),
    72: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_72_Evidence_Audit.md"),
    73: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_73_Evidence_Audit.md"),
    75: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_75_Evidence_Audit.md"),
    78: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_78_Evidence_Audit.md"),
    79: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_79_Evidence_Audit.md"),
    80: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_80_Evidence_Audit.md"),
    85: ("confirmed_vulnerable", "full_audit", "reports/BARRED_Track_1_Seed_85_Evidence_Audit.md"),
    86: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_86_Evidence_Audit.md"),
    90: ("proved_safe", "full_audit", "reports/BARRED_Track_1_Seed_90_Evidence_Audit.md"),

    # 22 Triage Seeds from BARRED_Track_1_Triage_Summary.md
    43: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    45: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    48: ("triage_likely_invalid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    53: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    54: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    58: ("ambiguous", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    59: ("triage_likely_invalid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    63: ("triage_likely_valid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    64: ("triage_likely_invalid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    65: ("triage_likely_valid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    67: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    74: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    76: ("triage_likely_valid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    77: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    81: ("triage_likely_valid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    82: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    83: ("triage_likely_invalid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    84: ("ambiguous", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    87: ("triage_likely_valid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    88: ("triage_likely_valid", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    89: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
    91: ("context_deficient", "triage", "reports/BARRED_Track_1_Triage_Summary.md"),
}

ARMS = {
    "A": ROOT / "artifacts/attempts/gemini-rep1-armA.jsonl",
    "B": ROOT / "artifacts/attempts/gemini-rep1-armB.jsonl",
    "C": ROOT / "artifacts/attempts/gemini-rep1-armC.jsonl",
    "D": ROOT / "artifacts/attempts/gemini-rep1-armD.jsonl",
}

def load_arm_attempts(path):
    outcomes = {}
    if not path.exists():
        return outcomes
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            seed = d.get("seed")
            if seed is None:
                continue
            usage = d.get("llm_usage", {}).get("totals", {})
            outcomes[seed] = {
                "decision": d.get("decision"),
                "reject_reason": d.get("reject_reason"),
                "winner": d.get("judge_eval", {}).get("winner"),
                "refinement_round": d.get("refinement_round", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost_usd": usage.get("cost_usd", 0.0),
            }
    return outcomes

def eval_correctness(verdict, decision):
    if verdict in ("proved_safe", "triage_likely_invalid"):
        # Ground truth is safe
        if decision == "rejected":
            return "TN"
        elif decision == "accepted":
            return "FP"
        else:
            return "MISSING"
    elif verdict in ("confirmed_vulnerable", "triage_likely_valid"):
        # Ground truth is vulnerable
        if decision == "accepted":
            return "TP"
        elif decision == "rejected":
            return "FN"
        else:
            return "MISSING"
    else:
        return "UNRESOLVED"

def main():
    # 1. Load benchmark seeds
    seeds = []
    with open(SEEDS_FILE) as f:
        for i, line in enumerate(f):
            d = json.loads(line)
            seed_id = 42 + i
            seeds.append({
                "index": i + 1,
                "seed_id": seed_id,
                "oracle_safety": d.get("original_safety", "").strip().lower(),
                "topic": d.get("topic", "").strip().replace("\n", " ")[:60],
                "predicate": d.get("predicate", "").strip(),
            })

    # 2. Load Arm attempts
    arm_data = {arm: load_arm_attempts(p) for arm, p in ARMS.items()}

    # 3. Build CSV Ledger rows
    rows = []
    confusion = {arm: Counter() for arm in ARMS}
    confusion_resolved = {arm: Counter() for arm in ARMS}

    for s in seeds:
        sid = s["seed_id"]
        v_info = AUDIT_VERDICTS.get(sid, ("unadjudicated", "unknown", ""))
        verdict, tier, cite = v_info

        row = {
            "seed_id": sid,
            "index": s["index"],
            "oracle_safety": s["oracle_safety"],
            "audit_verdict": verdict,
            "audit_tier": tier,
            "topic": s["topic"],
        }

        for arm in ["A", "B", "C", "D"]:
            att = arm_data[arm].get(sid)
            if att:
                row[f"{arm}_decision"] = att["decision"]
                row[f"{arm}_reject_reason"] = att["reject_reason"] or ""
                row[f"{arm}_tokens"] = att["total_tokens"]
                row[f"{arm}_cost"] = f"{att['cost_usd']:.4f}"
                eval_code = eval_correctness(verdict, att["decision"])
                row[f"{arm}_eval"] = eval_code
            else:
                row[f"{arm}_decision"] = "missing"
                row[f"{arm}_reject_reason"] = "timeout/rate_limit"
                row[f"{arm}_tokens"] = 0
                row[f"{arm}_cost"] = "0.0000"
                row[f"{arm}_eval"] = "MISSING"
                eval_code = "MISSING"

            confusion[arm][eval_code] += 1
            if tier == "full_audit" and verdict in ("proved_safe", "confirmed_vulnerable"):
                confusion_resolved[arm][eval_code] += 1

        rows.append(row)

    # 4. Write CSV
    fieldnames = [
        "seed_id", "index", "oracle_safety", "audit_verdict", "audit_tier", "topic",
        "A_decision", "A_reject_reason", "A_tokens", "A_cost", "A_eval",
        "B_decision", "B_reject_reason", "B_tokens", "B_cost", "B_eval",
        "C_decision", "C_reject_reason", "C_tokens", "C_cost", "C_eval",
        "D_decision", "D_reject_reason", "D_tokens", "D_cost", "D_eval",
    ]
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Written joined ledger to {OUT_CSV}")

    # 5. Print Metrics
    print("\n=======================================================")
    print("TRACK 2 REPLICATE 1 CORRECTNESS EVALUATION (24 RESOLVED SEEDS)")
    print("=======================================================")
    print("Cohort: 13 Proved Safe, 11 Confirmed Vulnerable\n")

    print("| Arm | TP | FN | FP | TN | Precision | Recall | F1 Score | Accuracy |")
    print("|:---:|:---:|:---:|:---:|:---:|:---------:|:------:|:--------:|:--------:|")

    metrics_resolved = {}
    for arm in ["A", "B", "C", "D"]:
        c = confusion_resolved[arm]
        tp, fn, fp, tn = c["TP"], c["FN"], c["FP"], c["TN"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
        metrics_resolved[arm] = (tp, fn, fp, tn, prec, rec, f1, acc)
        print(f"|  {arm}  | {tp:2d} | {fn:2d} | {fp:2d} | {tn:2d} |   {prec:.3f}   |  {rec:.3f} |   {f1:.3f}  |   {acc:.3f}  |")

    print("\n=======================================================")
    print("OVERALL COHORT ACCEPTANCE RATES")
    print("=======================================================")
    verdict_groups = defaultdict(lambda: {arm: [] for arm in ARMS})
    for r in rows:
        v = r["audit_verdict"]
        for arm in ARMS:
            verdict_groups[v][arm].append(r[f"{arm}_decision"])

    for v, arm_dict in sorted(verdict_groups.items()):
        total_in_v = len(arm_dict["A"])
        rates = []
        for arm in ["A", "B", "C", "D"]:
            acc = sum(1 for d in arm_dict[arm] if d == "accepted")
            rates.append(f"{acc}/{total_in_v} ({acc/total_in_v*100:.1f}%)")
        print(f"{v:<25} (n={total_in_v:2d}): A={rates[0]} | B={rates[1]} | C={rates[2]} | D={rates[3]}")

if __name__ == "__main__":
    main()
