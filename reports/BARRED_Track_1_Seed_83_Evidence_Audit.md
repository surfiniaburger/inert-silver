# BARRED Track 1 — Seed 83 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to out-of-bounds kernel memory read in `convert_ip_to_linear()` when handling LDT selectors."

**Result:** **Proved safe for this exact claim.** When the segment selector refers to the LDT (`seg & SEGMENT_TI_MASK == SEGMENT_LDT`), the code checks `if (unlikely((seg >> 3) >= child->mm->context.size))` and, if true, sets `addr = -1L` ("bogus selector, access would fault") without dereferencing `context.ldt`. Only in-range indices (`seg >> 3 < context.size`) access `context.ldt + seg`. The bounds check prevents any out-of-bounds read. The benchmark `vulnerable` label is wrong for this predicate.

## What was examined

1. Seed 83 is from the 50-seed manifest (oracle `vulnerable`), `triage_likely_invalid` group.
2. The relevant code:
   ```c
   if ((seg & SEGMENT_TI_MASK) == SEGMENT_LDT) {
       seg &= ~7UL;
       mutex_lock(&child->mm->context.lock);
       if (unlikely((seg >> 3) >= child->mm->context.size))
           addr = -1L; /* bogus selector, access would fault */
       else {
           desc = child->mm->context.ldt + seg;
           base = get_desc_base(desc);
           ...
           addr += base;
       }
       mutex_unlock(&child->mm->context.lock);
   }
   ```
   The bounds check `(seg >> 3) >= context.size` guards the `context.ldt + seg` access.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | OOB read from LDT via `context.ldt + seg`. | Identified precisely. |
| Is there a bounds check? | Yes — `(seg >> 3) >= context.size` → `addr = -1L`. | Guard present. |
| Can the index exceed the buffer? | No — out-of-range returns -1L without dereferencing. | Claim refuted. |

## Why the model results

The GEPA predicate assumed the LDT index was unchecked, but the code explicitly bounds-checks it. The benchmark `vulnerable` label is wrong for this predicate.

This is **RFC Axis E: predicate invalidity**.

## Audit boundary

Limited to the exact seed-83 claim. Does not prove all of ptrace safe, does not assess other paths, and does not depend on the CVEFixes `vulnerable` label (which is wrong for this predicate).
