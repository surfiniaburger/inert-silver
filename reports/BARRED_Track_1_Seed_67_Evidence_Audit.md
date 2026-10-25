# BARRED Track 1 — Seed 67 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to out-of-bounds reads in `ieee802_15_4_if_print` when `ndo->ndo_vflag` is true and the frame-control field specifies an address mode that requires more bytes than the captured packet length provides."

**Result:** **Confirmed vulnerable for this exact claim.** In the verbose path, the code advances `p` by 2/8 bytes per address field (`EXTRACT_LE_16BITS`, `le64addr_string`) without checking that those bytes remain in `caplen`. For example, addressing mode `0x03` (extended) does `p += 8` unconditionally. `caplen -= hdrlen` is performed only at the end, so a truncated frame drives `p` past the captured data and the subsequent `ND_DEFAULTPRINT(p, caplen)` reads out of bounds. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 67 is from the 50-seed manifest (oracle `vulnerable`), `triage_context_deficient` group.
2. The relevant code (verbose path):
   ```c
   case 0x03:
       panid = EXTRACT_LE_16BITS(p); p += 2;
       ND_PRINT((ndo,"%04x:%s ", panid, le64addr_string(ndo, p)));
       p += 8;
       break;
   ...
   caplen -= hdrlen;   /* only at the end */
   if (!ndo->ndo_suppress_default_print)
       ND_DEFAULTPRINT(p, caplen);
   ```
   No per-field length check against `caplen` in the verbose path (the initial `caplen < 3` check covers only the 3-byte header).

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `EXTRACT_LE_16BITS`/`le64addr_string`/`p += 8` without per-field caplen check. | Identified precisely. |
| Is `caplen` checked per field? | No — only `caplen < 3` initially and `caplen -= hdrlen` at the end. | Guard absent. |
| Is a trigger demonstrated? | Yes — truncated 802.15.4 frame with extended addressing. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing per-field bounds check is real and the OOB read follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-67 claim. Does not prove all of tcpdump safe, does not assess other protocols, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
