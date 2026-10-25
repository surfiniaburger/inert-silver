# BARRED Track 1 — Seed 55 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to an integer-overflow-induced buffer overflow in `unix_sck_send_data` because `send->data_len` is used to compute the total message length without any bounds check against `hdl->send_buf` size."

**Result:** **Confirmed vulnerable for this exact claim.** `unix_sck_send_data` computes `total_len = sizeof(msg->common) + send->data_len` and calls `memcpy(&msg->data[0], send->buf, send->data_len)` with no validation that `send->data_len` fits in `hdl->send_buf` (or that it is non-negative). A negative or oversized `data_len` overflows/wraps `total_len` and drives an out-of-bounds write into `msg->data`/`hdl->send_buf`. The benchmark `vulnerable` label is consistent with this (no label mismatch).

## What was examined

1. Seed 55 is from the 50-seed manifest (oracle `vulnerable`), in the `pro_claim_needs_independent_reproduction` group (all conditions accepted a Pro claim, no Con receipt).
2. The relevant code in `unix_sck_send_data`:
   ```c
   msg->common.payload_len = send->data_len;
   total_len = sizeof(msg->common) + send->data_len;
   memcpy(&msg->data[0], send->buf, send->data_len);
   if (unix_sck_send_msg(hdl, hdl->send_buf, total_len, ...) != total_len) { ... }
   ```
   No check that `send->data_len >= 0`, `send->data_len <= sizeof(msg->data)`, or `total_len` does not overflow.
3. `send->data_len` is a signed `int` (via `hsm_com_datagram_t`); a negative value makes `memcpy`'s size argument a huge `size_t`, and a large positive value overflows `total_len`. Both paths write out of bounds of `hdl->send_buf`.
4. CVEFixes provenance: corpus row retains only `code`/`language`/`safety`; the `vulnerable` label agrees with the source-level defect.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `memcpy(&msg->data[0], send->buf, send->data_len)` plus `total_len = sizeof(msg->common) + send->data_len`, no bounds check. | Identified precisely. |
| Is `send->data_len` validated? | No. | Unchecked. |
| Can it be negative or oversized? | Yes — signed int, no guard. | Reachable. |
| Is the overflow/write reachable? | Yes; follows from the arithmetic. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound here: the missing bounds check is real and the overflow/write follows. The replicated model acceptance is consistent with the source (not a false-positive case).

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees). It is neither Axis E (predicate invalidity) nor Axis D (evidence insufficiency).

## Audit boundary

Limited to the exact seed-55 claim of an integer-overflow-induced buffer overflow in `unix_sck_send_data` via unchecked `send->data_len`. Does not prove all of the HSM client API safe, does not assess `unix_sck_send_msg`/read paths, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
