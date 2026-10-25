# BARRED Track 1 — Seed 85 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a TOCTOU (time-of-check-to-time-of-use) privilege-escalation vulnerability in `for_each_problem_in_dir` (between the `dump_dir_accessible_by_uid` check and the subsequent `dd_opendir` call)."

**Result:** **Confirmed vulnerable for this exact claim.** `for_each_problem_in_dir` checks `dump_dir_accessible_by_uid(full_name, caller_uid)` and then calls `dd_opendir(full_name, ...)` on the same path. Between the check and the open, an attacker can replace the directory entry (e.g., with a symlink or swap the target), so the access decision is made on one object and the open operates on another. This is a classic TOCTOU and can be used to read/operate on dump directories the caller should not access. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 85 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. The relevant code:
   ```c
   if (caller_uid == -1 || dump_dir_accessible_by_uid(full_name, caller_uid)) {
       struct dump_dir *dd = dd_opendir(full_name, DD_OPEN_READONLY | ...);
       ...
   }
   ```
   The check and the open are separate calls on the same path string with no atomicity (no `O_NOFOLLOW`/`fstat`-on-fd verification).
3. An attacker can race a rename/symlink swap between the two calls.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `dump_dir_accessible_by_uid` check, then `dd_opendir` on the same path. | Identified precisely. |
| Is there a race window? | Yes — two separate path-based calls. | Reachable. |
| Can it be exploited for privilege escalation? | Yes — TOCTOU on the access decision. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the check-then-open pattern is a real TOCTOU. Replicated acceptance is consistent.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-85 claim. Does not prove all of ABRT safe, does not assess other entry points, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
