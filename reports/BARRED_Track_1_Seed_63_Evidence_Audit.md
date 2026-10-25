# BARRED Track 1 — Seed 63 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a denial-of-service via unbounded iteration in `ip6_finddst` when processing a malformed IPv6 Routing Header Type 0 with an inflated `ip6r_len` field."

**Result:** **Proved safe for this exact unbounded-iteration claim.** `dp->ip6r_len` is an 8-bit field (`uint8_t`), so `len` is at most 255 and `len >>= 1` caps the loop to at most 127 iterations. 127 iterations is strictly bounded and cannot cause unbounded execution or CPU exhaustion. The predicate's "unbounded iteration" mechanism is impossible. (A separate, narrower out-of-bounds read may exist — the per-iteration check `(addr + 1) > ndo_snapend` is weaker than `addr + sizeof(in6_addr)` — but that is not the claim audited here.)

## What was examined

1. Seed 63 is from the 50-seed manifest (oracle `vulnerable`), `triage_likely_valid` group.
2. The relevant code:
   ```c
   len = dp->ip6r_len;          /* uint8_t: 0..255 */
   ...
   len >>= 1;                   /* 0..127 */
   addr = &dp0->ip6r0_addr[0];
   for (i = 0; i < len; i++) {  /* at most 127 iterations */
       if ((const u_char *)(addr + 1) > ndo->ndo_snapend) goto trunc;
       dst_addr = (const void *)addr;
       addr++;
   }
   ```

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Unbounded loop on inflated `ip6r_len`. | Identified precisely. |
| Is `ip6r_len` bounded? | Yes — 8-bit, max 255; `len >>= 1` → max 127. | Bounded. |
| Can iteration be unbounded? | No — at most 127 iterations. | Claim refuted. |

## Why the model results

The GEPA predicate assumed `ip6r_len` was unbounded, but it is an 8-bit field. The benchmark `vulnerable` label is wrong for this predicate.

This is **RFC Axis E: predicate invalidity** (for the unbounded-iteration claim).

## Audit boundary

Limited to the exact seed-63 claim of unbounded iteration. Does not prove all of tcpdump safe, does not assess the narrower OOB-read possibility (weaker per-iteration check), and does not depend on the CVEFixes `vulnerable` label (which is wrong for this predicate).
