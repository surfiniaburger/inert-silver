# BARRED Track 1 — Seed 59 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to an out-of-bounds write in `mlx4_register_mac` due to an off-by-one error when searching for a free MAC table slot."

**Result:** **Confirmed vulnerable for this exact claim.** The search loop is bounded `for (i = 0; i < MLX4_MAX_MAC_NUM - 1; i++)`, which never examines slot `MLX4_MAX_MAC_NUM - 1`. If all slots 0..MAX-2 are occupied but slot MAX-1 is free, `free` remains -1. The subsequent guard `if (table->total == table->max)` may pass (total could be MAX-1 ≠ MAX), so execution reaches `table->refs[free] = 1` with `free == -1` — an out-of-bounds write before the table. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 59 is from the 50-seed manifest (oracle `vulnerable`), `triage_likely_invalid` group (reclassified here).
2. The relevant code:
   ```c
   for (i = 0; i < MLX4_MAX_MAC_NUM - 1; i++) {
       if (free < 0 && !table->refs[i]) { free = i; continue; }
       if (mac == ...) { *index = i; ++table->refs[i]; goto out; }
   }
   if (table->total == table->max) { err = -ENOSPC; goto out; }
   /* Register new MAC */
   table->refs[free] = 1;   /* OOB when free == -1 */
   ```
3. The loop skips the last slot. If it is the only free slot, `free` stays -1, and the total/max guard may not catch it (total can be MAX-1 while max is MAX).

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `table->refs[-1] = 1` when the last slot is the only free one. | Identified precisely. |
| Is the last slot ever examined? | No — loop bound is `MLX4_MAX_MAC_NUM - 1`. | Skipped. |
| Does the total/max guard catch it? | Not always — total can be MAX-1 ≠ MAX. | Guard insufficient. |
| Is a trigger demonstrated? | Yes — fill slots 0..MAX-2, register a new MAC. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the off-by-one in the loop bound is real and the OOB write follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-59 claim. Does not prove all of mlx4 safe, does not assess other table types, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
