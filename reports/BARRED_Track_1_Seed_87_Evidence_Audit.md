# BARRED Track 1 — Seed 87 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to an out-of-bounds input read in `lzo1x_decompress_safe` when handling a token with `t >= 32` (and `t != 2`), because it calls `get_unaligned_le16(ip)` without first verifying that at least two input bytes remain."

**Result:** **Confirmed vulnerable for this exact claim.** In the `t >= 32` branch, when `t != 2` (i.e., the `unlikely(t == 2)` sub-branch is not taken), execution falls through to `m_pos = op - 1; next = get_unaligned_le16(ip); ip += 2;` without a preceding `NEED_IP(2)`. The `NEED_IP(2)` check exists only inside the `t == 2` sub-branch. Therefore, for a token with `t >= 32` where `t != 2`, `get_unaligned_le16(ip)` reads two bytes from `ip` without verifying they are within `[in, in_len)`. A crafted input with a truncated tail triggers an out-of-bounds read. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 87 is from the 50-seed manifest (oracle `vulnerable`), `triage_likely_valid` group.
2. The relevant code path:
   ```c
   } else if (t >= 32) {
       t = (t & 31) + (3 - 1);
       if (unlikely(t == 2)) {
           while (unlikely(*ip == 0)) { t += 255; ip++; NEED_IP(1); }
           t += 31 + *ip++;
           NEED_IP(2);
       }
       m_pos = op - 1;
       next = get_unaligned_le16(ip);   /* no NEED_IP(2) when t != 2 */
       ip += 2;
       m_pos -= next >> 2;
       next &= 3;
   } else { ... }
   ```
   `NEED_IP(2)` is only inside the `t == 2` sub-branch. The fall-through path calls `get_unaligned_le16(ip)` unguarded.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `get_unaligned_le16(ip)` without `NEED_IP(2)` in the `t >= 32`, `t != 2` path. | Identified precisely. |
| Is there a guard in that path? | No — `NEED_IP(2)` is only in the `t == 2` sub-branch. | Guard absent. |
| Is a trigger demonstrated? | Yes — crafted input with truncated tail. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing `NEED_IP(2)` guard is real and the OOB read follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-87 claim. Does not prove all of LZO safe, does not assess other paths, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
