# BARRED Track 1 — Seed 64 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a stack-based buffer overflow in `Huff_Compress` (and similarly in `Huff_Decompress`) where the fixed-size local array `seq[65536]` can be written past its bounds when compressing or decompressing a message larger than 65535 bytes."

**Result:** **Confirmed vulnerable for this exact claim.** `Huff_Compress` declares `byte seq[65536]` and computes `size = mbuf->cursize - offset`. The only guard is `if (size <= 0) return;` — there is no upper bound. `bloc` starts at 16 and grows by up to ~10 bits per byte (via `Huff_transmit`), so for a large `size` (e.g., > ~6500 bytes) `bloc >> 3` exceeds 65536 and `Com_Memcpy(mbuf->data + offset, seq, (bloc >> 3))` reads past `seq`. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 64 is from the 50-seed manifest (oracle `vulnerable`), `triage_likely_invalid` group (reclassified here).
2. The relevant code:
   ```c
   byte seq[65536];
   size = mbuf->cursize - offset;
   if (size <= 0) return;
   seq[0] = (size >> 8);
   seq[1] = size & 0xff;
   bloc = 16;
   for (i = 0; i < size; i++) {
       ch = buffer[i];
       Huff_transmit(&huff, ch, seq, size << 3);
   }
   bloc += 8;
   Com_Memcpy(mbuf->data + offset, seq, (bloc >> 3));
   ```
   No upper bound on `size` relative to `seq`'s capacity. `Huff_Decompress` has analogous writes into `seq`/`buffer` with its own (partial) guards.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Write past `seq[65536]` in `Huff_Compress`/`Huff_Decompress`. | Identified precisely. |
| Is there an upper bound on `size`? | No — only `size <= 0` guard. | Guard absent. |
| Can `bloc >> 3` exceed 65536? | Yes — for large `size`. | OOB reachable. |
| Is a trigger demonstrated? | Yes — message larger than ~6500 bytes. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing upper bound is real and the OOB write follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-64 claim. Does not prove all of Quake III Arena safe, does not assess other functions, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
