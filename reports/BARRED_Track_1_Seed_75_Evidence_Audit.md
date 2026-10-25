# BARRED Track 1 — Seed 75 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to directory-traversal (path injection) in the creation/renaming of the dump directory because the value retrieved from problem_data as `FILENAME_ANALYZER` (`type`) is not validated before it is concatenated into the directory name passed to `try_dd_create` and `dd_rename`."

**Result:** **Confirmed vulnerable for this exact claim.** `create_dump_dir_from_problem_data` reads `type = problem_data_get_content_or_NULL(problem_data, FILENAME_ANALYZER)` and builds `problem_id = xasprintf("%s-%s.%ld-%lu" NEW_PD_SUFFIX, type, ...)` with no sanitization. If `type` contains `/` or `..`, `problem_id` (and the path passed to `try_dd_create`/`dd_rename`) escapes the intended base directory. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 75 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. The relevant code:
   ```c
   char *type = problem_data_get_content_or_NULL(problem_data, FILENAME_ANALYZER);
   ...
   char *problem_id = xasprintf("%s-%s.%ld-%lu" NEW_PD_SUFFIX, type, ...);
   dd = try_dd_create(base_dir_name, problem_id, uid);   /* concat_path_file(base, problem_id) */
   ...
   dd_rename(dd, new_path);
   ```
   No validation that `type` is a safe single path component.
3. A `type` value like `../../etc/foo` injects traversal into the created/renamed directory path.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Unsanitized `type` concatenated into a directory path. | Identified precisely. |
| Is traversal possible? | Yes — no component validation. | Reachable. |

## Why the model results

The GEPA predicate is sound: the missing validation is real and path injection follows. Replicated acceptance is consistent.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-75 claim. Does not prove all of ABRT safe, does not assess other problem-data fields, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
