# BARRED Track 1 — Seed 69 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a use-after-free of the SASL password (and related credential strings) in `sig_server_connect_copy` because it copies the original pointers (`sasl_username`, `sasl_password`) instead of duplicating the strings."

**Result:** **Confirmed vulnerable for this exact claim.** `sig_server_connect_copy` does `g_strdup` for `usermode` and `alternate_nick` but assigns `rec->sasl_username = src->sasl_username;` and `rec->sasl_password = src->sasl_password;` by pointer, without `g_strdup`. The copied record and its source therefore share the same credential buffers. If the source record (and its strings) is freed while the copy is still in use (reconnect path), the copy's `sasl_password`/`sasl_username` dangle — a use-after-free on subsequent use. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 69 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. The relevant code:
   ```c
   rec->usermode = g_strdup(src->usermode);
   rec->alternate_nick = g_strdup(src->alternate_nick);
   rec->sasl_mechanism = src->sasl_mechanism;
   rec->sasl_username = src->sasl_username;   /* pointer alias, no strdup */
   rec->sasl_password = src->sasl_password;   /* pointer alias, no strdup */
   ```
   Inconsistent with the `g_strdup` calls above it — a real ownership defect.
3. On the reconnect path, the original `IRC_SERVER_CONNECT_REC` can be freed while the copy persists, leaving dangling credential pointers.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Pointer aliasing of `sasl_username`/`sasl_password` without `g_strdup`. | Identified precisely. |
| Is the aliasing present? | Yes — inconsistent with the `g_strdup` calls for other fields. | Real defect. |
| Can the source be freed while the copy lives? | Yes — reconnect path. | UAF reachable. |

## Why the model results

The GEPA predicate is sound: the missing `g_strdup` is a real ownership defect and the UAF follows from the lifetime mismatch. Replicated acceptance is consistent.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-69 claim. Does not prove all of irssi safe, does not assess other credential fields, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
