# BARRED Track 1 — Seed 72 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to an out-of-bounds write (buffer overflow) in `nghttp2_option_set_user_recv_extension_type` via `set_ext_type` when a large `type` value is supplied."

**Result:** **Proved safe for this exact out-of-bounds-write claim.** `type` is a `uint8_t` (0–255), and `set_ext_type` indexes `ext_types[type / 8]`; with the real `nghttp2_option` layout, `user_recv_ext_types` is a 32-byte bitmask, so every possible index (0–31) is in bounds. The `type < 10` guard rejects the standard frame types but is not what makes the write safe — the 32-byte array does.

## What was examined

1. I selected seed 72 from the replicated Gemma/Gemini persistent-disagreement queue because it carries an accepted Pro claim (2/5 Gemma escalation acceptances) with status `conflicting_unadjudicated_model_outcomes`, and the allegation is a concrete arithmetic/bounds claim.
2. The relevant functions in the supplied `lib/nghttp2_option.c` excerpt:
   ```c
   static void set_ext_type(uint8_t *ext_types, uint8_t type) {
     ext_types[type / 8] = (uint8_t)(ext_types[type / 8] | (1 << (type & 0x7)));
   }

   void nghttp2_option_set_user_recv_extension_type(nghttp2_option *option,
                                                    uint8_t type) {
     if (type < 10) {
       return;
     }
     option->opt_set_mask |= NGHTTP2_OPT_USER_RECV_EXT_TYPES;
     set_ext_type(option->user_recv_ext_types, type);
   }
   ```
3. I checked the index domain: `type` is `uint8_t`, so `type ∈ [0, 255]` and `type / 8 ∈ [0, 31]`. The shift `1 << (type & 0x7)` is `1 << [0,7]`, i.e. at most 128, which fits in the `(uint8_t)` cast.
4. I resolved the buffer size against the upstream nghttp2 source. In `lib/nghttp2_session.h` (master), `nghttp2_option` contains `uint8_t user_recv_ext_types[32];`, with the comment: "To designate the bit of given frame type i, use `user_recv_ext_types[i / 8] & (1 << (i & 0x7))`. First 10 frame types are standard frame types and not used in this bitfield." Thus 32 bytes cover all 256 possible frame-type values.
5. Therefore `ext_types[type / 8]` for any `type ∈ [0,255]` addresses indices 0–31, all within the 32-byte allocation. The `type < 10` guard is a semantic filter (standard vs. extension frame types), not the bounds protection.
6. I checked CVEFixes provenance: as with seeds 42, 46, 50, 62, 66, and 68, the corpus row retains only `code`, `language`, and `safety` fields — no version/commit metadata. The `safe` label is consistent with this result, but the upstream struct layout — not the label — settles it.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `ext_types[type / 8] = ...` in `set_ext_type`, called with an attacker-supplied `uint8_t type`. | Identified precisely. |
| What is the maximum index? | `type / 8` for `type ∈ [0,255]` is at most 31. | Bounded by the type's width. |
| What is the buffer size? | `user_recv_ext_types[32]` in the upstream `nghttp2_option` struct (32 bytes = 256 bits). | Sufficient for all indices. |
| Can the index exceed the buffer? | No: 31 < 32. | The alleged OOB write cannot occur. |
| Is the `type < 10` guard the protection? | No; it filters standard frame types. Safety follows from the 32-byte array. | Guard is semantic, not a bounds check. |
| Is a trigger demonstrated? | No; every `uint8_t` value maps to an in-bounds slot. | Claim refuted. |

## Why the model results were misleading

The GEPA predicate noticed the absence of an explicit bounds check on `type` and inferred an out-of-bounds write, but it omitted two decisive facts: `type` is an 8-bit value (so `type / 8 ≤ 31`) and `user_recv_ext_types` is a 32-byte bitmask in the upstream struct. The replicated model outcomes are therefore not used as adjudication evidence.

This is **RFC Axis E: predicate invalidity**. The write is in bounds for every representable input because the bitmask is sized to the full frame-type space; no explicit check is required for memory safety.

## Audit boundary

This result is limited to the exact seed-72 claim of an out-of-bounds write in `nghttp2_option_set_user_recv_extension_type` via `set_ext_type`. It verifies only the bitmask indexing for `user_recv_ext_types`; it does not prove all of nghttp2 safe, does not assess other option fields or entry points, and does not depend on the CVEFixes `safe` label.
