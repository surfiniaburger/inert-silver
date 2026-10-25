# BARRED Track 1 — Seed 84 Evidence Audit

## Question audited

**Claim:** "The code is **not** vulnerable to a buffer-overflow or out-of-bounds write in `tcp_packet_get` (the receive loop)."

**Result:** **Proved safe for this exact claim.** The receive loop computes `want_size = packet_pending_bytes(pkt)` and calls `recv(tcp->sd, pkt->buffer + pkt->filled_size, want_size, 0)`. The destination pointer and size are derived from the packet's own accounting (`filled_size`, `pending_bytes`), which bounds the write to the allocated packet buffer. There is no unchecked length or fixed-size stack buffer. The negated claim is correct.

## What was examined

1. Seed 84 is from the 50-seed manifest (oracle `safe`), `triage_ambiguous` group.
2. The relevant code:
   ```c
   size_t want_size = packet_pending_bytes(pkt);
   if (want_size == 0) { ... return pkt; }
   while (want_size != 0 && !msg->is_completed) {
       uint8_t *subbuffer = pkt->buffer + pkt->filled_size;
       ssize_t gotten_size = recv(tcp->sd, subbuffer, want_size, 0);
       ...
       packet_mark_received(pkt, (unsigned) gotten_size);
       want_size = packet_pending_bytes(pkt);
   }
   ```
   `want_size` is bounded by `packet_pending_bytes`, which accounts for the packet's allocated buffer and filled size.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Buffer overflow in the receive loop. | Identified precisely. |
| Is the recv size bounded? | Yes — `want_size = packet_pending_bytes(pkt)`. | Bounded. |
| Is the destination bounded? | Yes — `pkt->buffer + pkt->filled_size`. | In bounds. |
| Is a trigger demonstrated? | No — no OOB write path. | Claim (negated) holds. |

## Why the model results

The GEPA predicate asserted a buffer overflow, but the receive loop uses packet-bounded sizes. The negated claim is correct.

This is **RFC Axis E: predicate validity** (the code is indeed not vulnerable).

## Audit boundary

Limited to the exact seed-84 claim. Does not prove all of the HTTP/TCP code safe, does not assess other paths, and does not depend on the CVEFixes `safe` label.
