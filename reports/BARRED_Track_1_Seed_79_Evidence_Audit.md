# BARRED Track 1 — Seed 79 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a NULL-pointer dereference in `process_tree` when `lookup_tree(entry.sha1)` (or `lookup_blob(entry.sha1)`) returns NULL."

**Result:** **Confirmed vulnerable for this exact claim.** In `process_tree`, the loop calls `process_tree(revs, lookup_tree(entry.sha1), ...)` for directories and `process_blob(revs, lookup_blob(entry.sha1), ...)` for blobs, passing the lookup result directly without a NULL check. `lookup_tree`/`lookup_blob` can return NULL when the object is missing (and `revs->ignore_missing_links` only guards `parse_tree_gently`, not the lookup). A missing object therefore reaches `process_tree`/`process_blob`, which dereference the pointer (`tree->object`, `blob->...`) → NULL dereference. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 79 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. The relevant code:
   ```c
   if (S_ISDIR(entry.mode))
       process_tree(revs, lookup_tree(entry.sha1), show, base, entry.path, cb_data);
   else if (S_ISGITLINK(entry.mode)) ...
   else
       process_blob(revs, lookup_blob(entry.sha1), show, base, entry.path, cb_data);
   ```
   No NULL check on the lookup result. Top-level `tree` is checked (`if (!obj) die(...)`), but recursive lookups are not.
3. With a missing object (and `ignore_missing_links` not covering the lookup), the NULL propagates into `process_tree`/`process_blob` and is dereferenced.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `lookup_tree`/`lookup_blob` result used without NULL check. | Identified precisely. |
| Can the lookup return NULL? | Yes — missing object. | Reachable. |
| Is the NULL dereferenced? | Yes — `tree->object` / blob access. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing NULL check is real and the dereference follows. Replicated acceptance is consistent.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-79 claim. Does not prove all of git's revision traversal safe, does not assess other entry points, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
