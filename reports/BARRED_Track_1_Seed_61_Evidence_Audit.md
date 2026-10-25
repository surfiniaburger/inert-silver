# BARRED Track 1 — Seed 61 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to an integer-overflow-induced heap buffer overflow in `ejabberd_zlib_drv_control` (DEFLATE/INFLATE paths)."

**Result:** **Confirmed vulnerable for this exact claim.** In both DEFLATE and INFLATE paths, `rlen` and `size` accumulate via `rlen += (BUF_SIZE - d->...->avail_out)` and `size += (...)` with no overflow check, and `driver_realloc_binary(b, size)` is called with the accumulated (possibly wrapped) value. On overflow, `size` wraps to a small value, `driver_realloc_binary` allocates an undersized buffer, and the next loop iteration writes through `b->orig_bytes + rlen` beyond it. The benchmark `vulnerable` label agrees (no label mismatch).

## What was examined

1. Seed 61 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. The relevant accumulation:
   ```c
   rlen += (BUF_SIZE - d->d_stream->avail_out);
   size += (BUF_SIZE - d->d_stream->avail_out);
   b = driver_realloc_binary(b, size);
   ...
   b = driver_realloc_binary(b, rlen);
   ```
   `rlen`/`size` are `ErlDrvSizeT` (size_t-class); no overflow check. `driver_realloc_binary` does not detect a wrapped size.
3. A crafted large input drives many loop iterations, overflowing `size`/`rlen`, yielding an undersized reallocation followed by an OOB write on the next iteration.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Unchecked accumulation of `rlen`/`size`, then `driver_realloc_binary(b, size)`. | Identified precisely. |
| Can `size`/`rlen` overflow? | Yes — no check, many iterations. | Reachable. |
| Does overflow lead to OOB write? | Yes — undersized realloc, then write via `b->orig_bytes + rlen`. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing overflow check is real and the OOB write follows. Replicated acceptance is consistent with the source.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-61 claim. Does not prove all of the ejabberd zlib driver safe, does not assess other commands, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
