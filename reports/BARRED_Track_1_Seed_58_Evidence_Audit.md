# BARRED Track 1 — Seed 58 Evidence Audit

## Question audited

**Claim:** "The code is **not** vulnerable to out-of-bounds reads in `frag6_print`."

**Result:** **Proved safe for this exact claim (negated).** `frag6_print` begins with `ND_TCHECK(*dp)`, which verifies that the `ip6_frag` header (pointed to by `bp`) lies within the captured packet. All subsequent reads (`dp->ip6f_ident`, `dp->ip6f_offlg`) are on that guarded structure. The `ip6` pointer (`bp2`) is the packet-base pointer supplied by the caller and is assumed valid by the standard tcpdump calling convention; the arithmetic on `ip6->ip6_plen` is used only for display, not for memory access. The negated claim holds.

## What was examined

1. Seed 58 is from the 50-seed manifest (oracle `safe`), `triage_ambiguous` group.
2. The relevant code:
   ```c
   dp = (const struct ip6_frag *)bp;
   ip6 = (const struct ip6_hdr *)bp2;
   ND_TCHECK(*dp);   /* guards dp access */
   ... EXTRACT_32BITS(&dp->ip6f_ident), EXTRACT_16BITS(&dp->ip6f_offlg) ...
   /* display-only arithmetic on ip6->ip6_plen */
   ```

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged (non-)vulnerability? | OOB reads in `frag6_print`. | Identified precisely. |
| Is `dp` guarded? | Yes — `ND_TCHECK(*dp)`. | Guard present. |
| Is `ip6` (bp2) a valid packet base? | Yes — supplied by caller per tcpdump convention. | Valid. |
| Is a trigger demonstrated? | No — no OOB read path. | Negated claim holds. |

## Why the model results

The GEPA predicate asserted a (negated) non-vulnerability; the code's `ND_TCHECK` guard and standard calling convention support it. The benchmark `safe` label agrees.

This is **RFC Axis E: predicate validity** (the negated claim is correct).

## Audit boundary

Limited to the exact seed-58 claim. Does not prove all of tcpdump safe, does not assess other callers or protocols, and does not depend on the CVEFixes `safe` label.
