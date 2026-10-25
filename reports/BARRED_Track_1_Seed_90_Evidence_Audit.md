# BARRED Track 1 — Seed 90 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to out-of-bounds memory access in `gdImageJpegPtr` when the image width (`sx`) is artificially set to zero."

**Result:** **Proved safe for this exact out-of-bounds claim.** The implementation of `_gdImageJpegCtx` (upstream libgd `src/gd_jpeg.c`, master) contains no out-of-bounds access on a zero-width image: the row buffer is sized to `cinfo.image_width * input_components * sizeof(JSAMPLE)` (0 bytes when `sx == 0`), and every pixel loop is bounded by `j < im->sx` (zero iterations when `sx == 0`). The claim is refuted; the test's `NULL` expectation holds via the `gdCalloc(1, 0) == NULL` path or libjpeg's rejection of a zero-width compress.

## What was examined

1. I selected seed 90 from the replicated Gemma/Gemini persistent-disagreement queue because it carries an accepted Pro claim (1/5 Gemma escalation acceptances) with status `conflicting_unadjudicated_model_outcomes`, and the allegation is a concrete bounds claim in image encoding.
2. The supplied seed is a test harness (`gdImageCreateTrueColor(1, 10)`; `src->sx = 0`; `gdImageJpegPtr(src, &size, 0)`; assert `dst == NULL`). It contains no library code.
3. I resolved the implementation from upstream libgd (`src/gd_jpeg.c`, master). The relevant write path is `_gdImageJpegCtx`:
   ```c
   cinfo.image_width = im->sx;                       /* 0 when sx == 0 */
   ...
   row = (JSAMPROW)gdCalloc(1, cinfo.image_width * cinfo.input_components * sizeof(JSAMPLE));
   /* size == 0 when sx == 0 */
   if (row == 0) { ... return 1; }                  /* NULL -> fail, returns NULL to caller */
   ...
   for (i = 0; i < im->sy; i++) {
       for (jidx = 0, j = 0; j < im->sx; j++) {   /* zero iterations when sx == 0 */
           int val = im->tpixels[i][j];
           row[jidx++] = gdTrueColorGetRed(val);
           ...
       }
       nlines = jpeg_write_scanlines(&cinfo, rowptr, 1);
       ...
   }
   ```
4. I checked the buffer: `row` is allocated to `sx * 3 * sizeof(JSAMPLE)` bytes (0 bytes when `sx == 0`). No access is made beyond `j < sx` (0 iterations), so even a non-NULL zero-size allocation is never dereferenced out of bounds by gd's code.
5. I checked the return: on `sx == 0`, either `gdCalloc(1, 0)` returns `NULL` (caught by `if (row == 0)`) or libjpeg rejects the zero-width compress during `jpeg_start_compress`/`jpeg_write_scanlines`, both of which route through `fatal_jpeg_error` -> `longjmp` -> `return 1`, yielding `NULL` from `gdImageJpegPtr`. Either way the test's `dst == NULL` holds and no out-of-bounds access occurs in gd's code.
6. I checked CVEFixes provenance: as with seeds 42, 46, 50, 60, 62, 66, 68, 70, 72, 80, and 86, the corpus row retains only `code`, `language`, and `safety` fields — no version/commit metadata. The `safe` label is consistent with this result, but the implementation — not the label — settles it.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Out-of-bounds memory access in `gdImageJpegPtr` when `sx == 0`. | Identified precisely. |
| Is the implementation supplied? | Yes — resolved from upstream libgd `src/gd_jpeg.c` (master). | Implementation available. |
| Can the index/loop exceed the buffer when `sx == 0`? | No; all pixel access is gated by `j < im->sx` (0 iterations) and `row` is sized to `sx * 3` bytes. | In bounds by construction. |
| Does `gdImageJpegPtr` return `NULL` on `sx == 0`? | Yes — via `gdCalloc(1, 0) == NULL` or libjpeg rejecting the zero-width compress. | Test expectation met. |
| Is a trigger demonstrated? | No; no path reaches an out-of-bounds access for any value of `sx`. | Claim refuted. |

## Why the model results are not used as proof

The GEPA predicate asserts an OOB from a zero width, but the seed does not contain the function it names; the only artifact is a test that expects failure. The replicated model outcomes are therefore not used as adjudication evidence.

This is **RFC Axis E: predicate invalidity**. The claimed out-of-bounds access cannot occur because every pixel access is gated by `j < im->sx` (zero iterations when `sx == 0`) and the row buffer is sized to `sx * 3` bytes; the zero-width case returns `NULL` through the `gdCalloc(1, 0) == NULL` path or libjpeg's rejection. The `safe` label is consistent with this result but is not its basis.

## Required next evidence

**Resolved.** The matching implementation was obtained from upstream libgd (`src/gd_jpeg.c`, master). `_gdImageJpegCtx` sizes `row` to `cinfo.image_width * input_components * sizeof(JSAMPLE)` (0 bytes at `sx == 0`) and gates all pixel access on `j < im->sx` (zero iterations). The zero-width case yields `NULL` via the `gdCalloc(1, 0) == NULL` path or libjpeg's rejection of a zero-width compress. No memory sanitizer run was needed: the bounds are established by construction from the source. (A sanitizer run would be a confirmatory witness only.)

## Audit boundary

This result is limited to the exact seed-90 claim of an out-of-bounds access in `gdImageJpegPtr` on zero width. It does not prove all of libgd's JPEG path safe, does not assess other image dimensions or formats, and does not depend on the CVEFixes `safe` label. The missing implementation is the decisive gap.
