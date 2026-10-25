# BARRED Track 1 — Seed 73 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to an out-of-bounds write (buffer overflow) in `udf_pc_to_char` when processing a symlink stored in an UDF filesystem."

**Result:** **Confirmed vulnerable for this exact claim.** `udf_pc_to_char` writes into the output buffer `to` (sized to a page) via pointer `p`, with `case 3` doing `memcpy(p, "../", 3); p += 3;` and `case 5` calling `udf_get_filename(sb, pc->componentIdent, p, pc->lengthComponentIdent)` (copying `lengthComponentIdent` bytes) followed by `*p++ = '/'`. Neither the component lengths nor the running `p` are checked against the output buffer size. A crafted UDF symlink with a large `lengthComponentIdent` or many components overflows `to`. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 73 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. The relevant writes:
   ```c
   case 3: memcpy(p, "../", 3); p += 3; break;
   case 5: p += udf_get_filename(sb, pc->componentIdent, p, pc->lengthComponentIdent); *p++ = '/'; break;
   ```
   `elen += sizeof(struct pathComponent) + pc->lengthComponentIdent;` advances by attacker-controlled length. No bounds check on `p` vs. `to`/page size.
3. A crafted symlink with inflated `lengthComponentIdent` drives `p` past the page-sized `to` buffer.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Unbounded `memcpy`/`udf_get_filename` into `to` via `p`. | Identified precisely. |
| Is the write bounded by buffer size? | No. | Reachable. |
| Is a trigger demonstrated? | Yes — crafted UDF symlink with large component length. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing bounds check is real and the OOB write follows. Replicated acceptance is consistent.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-73 claim. Does not prove all of UDF safe, does not assess other UDF paths, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
