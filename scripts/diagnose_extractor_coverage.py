"""Diagnostic: record why candidate generation fails for each obligation-bearing seed.

Instruments the actual rejection branches (not post-hoc approximation).
Outputs a JSONL file with per-seed failure reasons and a summary.
"""
import json
from collections import Counter
from scenarios.debate.con_receipt_extractor import (
    extract_upper_bound_candidates_ts_with_diagnostics,
    extract_candidates,
    _ts_find_guards, _ts_find_operations,
)

def main():
    seeds = [json.loads(l) for l in open("scenarios/debate/cve_seeds_benchmark_50.jsonl")]
    import tree_sitter, tree_sitter_c
    lang = tree_sitter.Language(tree_sitter_c.language())
    parser = tree_sitter.Parser(lang)

    results = []
    reasons = Counter()
    rej_reasons = Counter()
    for i, s in enumerate(seeds):
        sid = 42 + i
        obl = s.get("defense_obligation")
        if not obl:
            continue
        code = s.get("topic", "")
        cands, rejs = extract_upper_bound_candidates_ts_with_diagnostics(code)
        actual_cands = extract_candidates(code, obl)

        if actual_cands:
            reason = "candidate_found"
        elif not rejs:
            reason = "no_pairs_evaluated"
        else:
            # aggregate rejection reasons
            r = Counter(r["reason"] for r in rejs)
            reason = r.most_common(1)[0][0] if r else "unknown"

        for r in rejs:
            rej_reasons[r["reason"]] += 1

        reasons[reason] += 1
        results.append({
            "seed": sid,
            "obligation_kind": obl.get("kind"),
            "num_candidates_diag": len(cands),
            "num_candidates_actual": len(actual_cands),
            "failure_reason": reason,
            "rejection_counts": dict(Counter(r["reason"] for r in rejs)),
            "candidate_ids": [c.candidate_id for c in actual_cands],
            "broad_detected": sum(1 for c in actual_cands if "operation_not_recognized_sink" in c.unsupported_conditions),
        })

    with open("artifacts/extractor_diagnostic.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print("Per-seed failure reason distribution:")
    for r, c in reasons.most_common():
        print(f"  {r}: {c}")

    print("\nRejection branch counts (across all guard-op pairs):")
    for r, c in rej_reasons.most_common():
        print(f"  {r}: {c}")

    print(f"\nTotal obligation-bearing seeds: {len(results)}")
    print(f"Seeds with candidates (actual): {sum(1 for r in results if r['num_candidates_actual']>0)}")
    print(f"Total candidates (actual): {sum(r['num_candidates_actual'] for r in results)}")
    print(f"Broad-detected candidates (actual): {sum(r['broad_detected'] for r in results)}")
    print("\nNOTE: 'actual' counts reflect production extract_candidates() output.")
    print("      'diag' counts reflect the unfiltered instrumented extractor (more candidates, no limit).")
    print("      Rejection reasons are from the instrumented version (actual rejection branches).")
    mismatch = [r for r in results if r['num_candidates_diag'] != r['num_candidates_actual']]
    if mismatch:
        print(f"NOTE: {len(mismatch)} seeds have diag/actual candidate count mismatch (expected: diagnostic finds more, production filters by recognized-sink preference + 5-candidate limit)")
    print("Written to artifacts/extractor_diagnostic.jsonl")

if __name__ == "__main__":
    main()
