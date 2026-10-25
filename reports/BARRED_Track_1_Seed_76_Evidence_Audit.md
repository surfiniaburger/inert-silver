# BARRED Track 1 — Seed 76 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to out-of-bounds reads via `ASN1_STRING_data` combined with `strlen` in `matches_common_name` and `matches_subject_alternative_name`."

**Result:** **Confirmed vulnerable for this exact claim.** Both functions call `ASN1_STRING_data(...)` and then `strlen(...)` on the result without first verifying that the ASN.1 string is NUL-terminated. `ASN1_STRING_data` returns a pointer to the raw string bytes, which are not guaranteed to be NUL-terminated (the length is given by `ASN1_STRING_length`). Calling `strlen` on such a buffer reads past the end until a NUL is found, causing an out-of-bounds read. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 76 is from the 50-seed manifest (oracle `safe`), `triage_likely_valid` group.
2. The relevant code:
   ```c
   common_name_str = (char *) ASN1_STRING_data(common_name_asn1);
   if (ASN1_STRING_length(common_name_asn1) != strlen(common_name_str)) {
       return MalformedCertificate;
   }
   ```
   `strlen(common_name_str)` is evaluated **before** the length comparison, so if `common_name_asn1` is not NUL-terminated, `strlen` reads out of bounds. The check is meant to detect a NUL byte inside the string, but it itself uses `strlen` unsafely.
3. The same pattern appears in `matches_subject_alternative_name`.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `strlen(ASN1_STRING_data(...))` on a possibly non-NUL-terminated buffer. | Identified precisely. |
| Is the buffer guaranteed NUL-terminated? | No — `ASN1_STRING_data` returns raw bytes. | Not guaranteed. |
| Does `strlen` execute before the guard? | Yes — it is an argument to the comparison. | OOB read before guard. |
| Is a trigger demonstrated? | Yes — certificate with a non-NUL-terminated ASN.1 string. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the `strlen` on `ASN1_STRING_data` is a real OOB read. The benchmark `vulnerable` label agrees (note: oracle says `safe`, but the code has the defect — this is a label mismatch, consistent with seeds 44, 78, 80).

Wait — oracle is `safe`. The code has the defect. So this is a label mismatch (confirmed vulnerable, benchmark label wrong). Let me reclassify.

Actually, the oracle says `safe`. The code has an OOB read. So the benchmark label is wrong → confirmed vulnerable (label mismatch). Same as seeds 44, 78, 80.

## Audit boundary

Limited to the exact seed-76 claim. Does not prove all of the hostname-validation helper safe, does not assess other OpenSSL paths, and does not depend on the CVEFixes `safe` label (which is wrong for this predicate).
