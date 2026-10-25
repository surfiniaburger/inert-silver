# BARRED Track 1 — Seed 80 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to 32-bit integer overflow in the header-writing path (`ras_puthdr` / `ras_putint`) when encoding images with sufficiently large dimensions, which can truncate the `length` field and corrupt the generated RAS file."

**Result:** **Confirmed vulnerable for this exact integer-overflow claim.** Unlike seeds 42, 46, 50, 62, 66, 68, 72, and 86, the supplied source does contain the unchecked arithmetic the predicate describes: `hdr->length = rowsize * hdr->height` (both `int`) and `hdr->length = hdr->height * rowsize` are computed without any range check, and `ras_putint` writes the resulting (possibly wrapped) 32-bit value. The benchmark `safe` label is wrong for this predicate (label mismatch).

## What was examined

1. I selected seed 80 as the last unaudited persistent-split seed (no accepted Pro claims; status `conclusion_not_deterministically_discharged`).
2. The relevant computations in the supplied `ras_enc.c` excerpt:
   ```c
   rowsize = RAS_ROWSIZE(&hdr);
   hdr.length = rowsize * hdr.height;   /* int * int, no overflow check */

   ...

   rowsize = RAS_ROWSIZE(hdr);
   pad = rowsize - (hdr->width * hdr->depth + 7) / 8;
   hdr->length = hdr->height * rowsize; /* int * int, no overflow check */

   static int ras_puthdr(jas_stream_t *out, ras_hdr_t *hdr) {
       ...
       ras_putint(out, hdr->length);    /* writes 4 bytes of the (possibly wrapped) int */
       ...
   }

   static int ras_putint(jas_stream_t *out, int val) {
       int x = val;
       for (i = 0; i < 4; i++) {
           c = (x >> 24) & 0xff;
           if (jas_stream_putc(out, c) == EOF) return -1;
           x <<= 8;
       }
       return 0;
   }
   ```
3. I checked the arithmetic: `rowsize` and `hdr->height` are both `int` (32-bit on the relevant targets). For sufficiently large dimensions, `rowsize * hdr->height` exceeds `INT_MAX` and wraps; the wrapped value is stored in `hdr->length` (also `int`) and emitted verbatim by `ras_putint`. The written `length` field no longer matches the bytes actually emitted, corrupting the RAS header.
4. I checked the write path: `ras_putint` is bounded to exactly four `jas_stream_putc` calls, so there is no out-of-bounds memory write; the defect is a truncated/corrupt length field plus the downstream `ras_putdatastd` loop iterating over the (possibly huge) original `hdr->width`/`hdr->height`, which is a denial-of-service/corruption hazard rather than memory corruption.
5. I checked the allocation: `ras_putdatastd` calls `jas_matrix_create(jas_image_height, jas_image_width)` before writing; for enormous dimensions this allocation fails and the function returns `-1`, but `ras_puthdr` has already written the (overflowed) header, so the output is already corrupt.
6. I checked CVEFixes provenance: as with seeds 42, 44, 46, 50, 52, 60, 62, 66, 68, 70, 72, 86, and 90, the corpus row retains only `code`, `language`, and `safety` fields — no version/commit metadata. The `safe` label disagrees with the demonstrable, source-level integer overflow; the label is a triage signal, not proof.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `hdr->length = rowsize * hdr->height` / `hdr->height * rowsize` with `int` operands, then `ras_putint(out, hdr->length)`. | Identified precisely. |
| Is the multiplication checked? | No; no `INT_MAX` guard or 64-bit intermediate appears. | Unchecked. |
| Can the product overflow? | Yes, for sufficiently large (but representable) dimensions. | Reachable. |
| Is the overflowed value written? | Yes; `ras_putint` emits all four bytes of the `int` without masking/validating. | Length field corrupted. |
| Is there a memory-safety impact? | No OOB write — `ras_putint` is bounded to 4 bytes; the impact is file corruption and a DoS via the large-dimension loops. | Low-severity, but real. |
| Is a trigger demonstrated? | Reachability shown by dimension argument; the overflow and truncation follow from the arithmetic. | Claim substantiated. |
| Benchmark label | CVEFixes labels this variant `safe`, but the source performs the unchecked multiplication. | Label mismatch (benchmark wrong). |

## Why the model results were misleading

The GEPA predicate correctly identified a real, source-level integer overflow; it is not a false mechanism. The replicated model disagreement is best explained by the benchmark label being wrong for this predicate. The model outcomes are process evidence only; the source settles the result.

This is a **label mismatch** (the predicate is sound and the code overflows; the `safe` oracle label is incorrect), not Axis E predicate invalidity and not Axis D evidence insufficiency. The missing `RAS_ROWSIZE` definition (in `ras_cod.h`, not included) does not change the conclusion, because the overflow follows from the `int` multiplication regardless of the exact row-size formula. The `safe` label must not be used as a correctness oracle for this seed.

## Audit boundary

This result is limited to the exact seed-80 claim of a 32-bit integer overflow in `ras_puthdr`/`ras_putint` truncating the `length` field. It does not prove all of the JasPer RAS encoder safe, does not assess other components or formats, does not constitute a full vulnerability report or exploitability assessment (the impact is file corruption/DoS, not memory corruption), and does not depend on the CVEFixes `safe` label, which is incorrect for this predicate.
