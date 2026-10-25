# BARRED Track 1 — Seed 71 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a path-traversal (zip-slip) arbitrary-file-write vulnerability in `create_output_name`/`ensure_filepath` because filenames from the CHM archive are not validated for `..` components or symlink tricks before being used to create files on disk."

**Result:** **Confirmed vulnerable for this exact claim.** `create_output_name` builds the output path by concatenating `dir` and the (possibly attacker-controlled) archive filename, converting separators but never rejecting `..` components. `ensure_filepath` then creates intermediate directories along that path via `mkdir`. A CHM entry named `../../etc/foo` therefore escapes the output directory and writes to an attacker-chosen location. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 71 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. `create_output_name`: copies `fname` into `name` (prefixed with `dir`), converting slashes; no `..` / path-traversal check.
3. `ensure_filepath`: walks `path` creating each directory component with `mkdir`; follows whatever traversal the name contains.
4. A crafted CHM entry with `../` components escapes the output root.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Archive filename used in output path without `..`/symlink validation. | Identified precisely. |
| Is traversal possible? | Yes — no rejection of `..` components. | Reachable. |
| Is arbitrary file write reachable? | Yes — via a crafted CHM entry. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing validation is real and zip-slip follows. Replicated acceptance is consistent.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-71 claim. Does not prove all of the CHM extractor safe, does not assess symlink handling at extraction time, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
