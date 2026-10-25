# BARRED Gemma/Gemini Replicated Discrimination Ledger

This ledger has 50 canonical seeds × 5 replicates × 4 matched conditions = 1000 recorded condition outcomes. Acceptance is a pipeline outcome, not a correctness verdict.

The four conditions are Gemma sliced baseline, Gemma progressive escalation, Gemini baseline, and Gemini escalation. Gemma's per-run `seed` identifiers are offset by replicate, so attempts are joined to the canonical manifest by normalized predicate text rather than transient run ID.

| Seed | Oracle | Gemma B/E | Gemini B/E | Gemma Δ | Gemini Δ | Family discrimination | Audit priority |
|---:|---|---:|---:|---:|---:|---|---|
| 42 | safe | 5/5 → 4/5 | 0/5 → 0/5 | -1 | +0 | persistent_gemma_only | high |
| 43 | vulnerable | 5/5 → 3/5 | 5/5 → 5/5 | -2 | +0 | mixed_family_split | medium |
| 44 | safe | 5/5 → 5/5 | 3/5 → 1/5 | +0 | -2 | persistent_gemma_only | high |
| 45 | vulnerable | 4/5 → 5/5 | 3/5 → 3/5 | +1 | +0 | mixed_family_split | medium |
| 46 | safe | 5/5 → 4/5 | 0/5 → 0/5 | -1 | +0 | persistent_gemma_only | high |
| 47 | vulnerable | 4/5 → 5/5 | 5/5 → 5/5 | +1 | +0 | no_persistent_family_split | medium |
| 48 | safe | 1/5 → 1/5 | 0/5 → 0/5 | +0 | +0 | no_persistent_family_split | low |
| 49 | vulnerable | 4/5 → 4/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 50 | safe | 5/5 → 4/5 | 0/5 → 1/5 | -1 | +1 | persistent_gemma_only | high |
| 51 | vulnerable | 4/5 → 5/5 | 3/5 → 5/5 | +1 | +2 | no_persistent_family_split | medium |
| 52 | safe | 4/5 → 5/5 | 1/5 → 1/5 | +1 | +0 | persistent_gemma_only | high |
| 53 | vulnerable | 5/5 → 5/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 54 | safe | 3/5 → 3/5 | 0/5 → 1/5 | +0 | +1 | mixed_family_split | medium |
| 55 | vulnerable | 0/5 → 4/5 | 3/5 → 3/5 | +4 | +0 | no_persistent_family_split | medium |
| 56 | safe | 5/5 → 3/5 | 1/5 → 0/5 | -2 | -1 | mixed_family_split | medium |
| 57 | vulnerable | 3/5 → 5/5 | 5/5 → 5/5 | +2 | +0 | no_persistent_family_split | medium |
| 58 | safe | 3/5 → 5/5 | 5/5 → 5/5 | +2 | +0 | no_persistent_family_split | medium |
| 59 | vulnerable | 5/5 → 3/5 | 5/5 → 5/5 | -2 | +0 | mixed_family_split | medium |
| 60 | safe | 5/5 → 5/5 | 0/5 → 1/5 | +0 | +1 | persistent_gemma_only | high |
| 61 | vulnerable | 4/5 → 5/5 | 4/5 → 5/5 | +1 | +1 | no_persistent_family_split | medium |
| 62 | safe | 4/5 → 5/5 | 0/5 → 0/5 | +1 | +0 | persistent_gemma_only | high |
| 63 | vulnerable | 3/5 → 4/5 | 3/5 → 5/5 | +1 | +2 | no_persistent_family_split | medium |
| 64 | safe | 2/5 → 5/5 | 0/5 → 2/5 | +3 | +2 | mixed_family_split | medium |
| 65 | vulnerable | 5/5 → 5/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 66 | safe | 4/5 → 5/5 | 0/5 → 1/5 | +1 | +1 | persistent_gemma_only | high |
| 67 | vulnerable | 4/5 → 4/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 68 | safe | 5/5 → 4/5 | 1/5 → 1/5 | -1 | +0 | persistent_gemma_only | high |
| 69 | vulnerable | 5/5 → 5/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 70 | safe | 4/5 → 4/5 | 0/5 → 0/5 | +0 | +0 | persistent_gemma_only | high |
| 71 | vulnerable | 3/5 → 5/5 | 5/5 → 5/5 | +2 | +0 | no_persistent_family_split | medium |
| 72 | safe | 4/5 → 5/5 | 0/5 → 1/5 | +1 | +1 | persistent_gemma_only | high |
| 73 | vulnerable | 1/5 → 3/5 | 5/5 → 5/5 | +2 | +0 | mixed_family_split | medium |
| 74 | safe | 3/5 → 3/5 | 1/5 → 0/5 | +0 | -1 | mixed_family_split | medium |
| 75 | vulnerable | 5/5 → 4/5 | 4/5 → 5/5 | -1 | +1 | no_persistent_family_split | medium |
| 76 | safe | 4/5 → 5/5 | 2/5 → 3/5 | +1 | +1 | mixed_family_split | medium |
| 77 | vulnerable | 3/5 → 4/5 | 5/5 → 5/5 | +1 | +0 | no_persistent_family_split | medium |
| 78 | safe | 4/5 → 4/5 | 0/5 → 0/5 | +0 | +0 | persistent_gemma_only | high |
| 79 | vulnerable | 4/5 → 4/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 80 | safe | 4/5 → 5/5 | 2/5 → 0/5 | +1 | -2 | persistent_gemma_only | high |
| 81 | vulnerable | 5/5 → 5/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 82 | safe | 2/5 → 2/5 | 0/5 → 0/5 | +0 | +0 | mixed_family_split | medium |
| 83 | vulnerable | 5/5 → 5/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 84 | safe | 5/5 → 5/5 | 4/5 → 4/5 | +0 | +0 | no_persistent_family_split | low |
| 85 | vulnerable | 5/5 → 5/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 86 | safe | 5/5 → 4/5 | 0/5 → 0/5 | -1 | +0 | persistent_gemma_only | high |
| 87 | vulnerable | 3/5 → 5/5 | 5/5 → 5/5 | +2 | +0 | no_persistent_family_split | medium |
| 88 | safe | 4/5 → 5/5 | 5/5 → 5/5 | +1 | +0 | no_persistent_family_split | medium |
| 89 | vulnerable | 5/5 → 5/5 | 5/5 → 5/5 | +0 | +0 | no_persistent_family_split | low |
| 90 | safe | 5/5 → 4/5 | 0/5 → 0/5 | -1 | +0 | persistent_gemma_only | high |
| 91 | vulnerable | 2/5 → 2/5 | 5/5 → 5/5 | +0 | +0 | mixed_family_split | medium |

## Interpretation rules

- `persistent_*_only`: escalated acceptance is at least 4/5 for one family and at most 1/5 for the other; these are the first predicate-audit cases.
- `mixed_family_split`: escalated acceptance differs by at least 2/5 but lacks the persistent threshold.
- Rejection reasons are preserved in the CSV; they must not be compared as a rate without a matched outcome definition.
- The ledger does not inherit Qwen outcomes or use benchmark labels as adjudication proof.
- A persistent family split is a predicate-audit queue, not evidence that either model is correct.
- A historical Con acceptance with `invalid_contract` or no receipt is explicitly **not** counted as deterministic counter-evidence.

## Summary

- Family discrimination: `{"mixed_family_split": 11, "no_persistent_family_split": 24, "persistent_gemma_only": 15}`
- Predicate-audit priority: `{"high": 15, "low": 12, "medium": 23}`
- Persistent Gemma-only splits by benchmark class: `{"safe": 15}`. This is a discrimination signal only.
- Escalated evidence status: `{"conclusion_not_deterministically_discharged": 5, "conflicting_unadjudicated_model_outcomes": 35, "pro_claim_needs_independent_reproduction": 10}`
- Acceptance totals over 250 seed-replicate slots per condition: `{"gemini_baseline": 140, "gemini_escalated": 148, "gemma_baseline": 196, "gemma_escalated": 213}`
