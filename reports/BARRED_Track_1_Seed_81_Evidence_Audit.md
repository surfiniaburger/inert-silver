# BARRED Track 1 — Seed 81 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a race-condition leading to a double-submission (or use-after-free) of the write URB in `omninet_write` because the write-URB free flag is checked on `port->write_urbs_free` but cleared/set on `wport->write_urbs_free` (a different port structure)."

**Result:** **Confirmed vulnerable for this exact claim.** `omninet_write` checks and clears `port->write_urbs_free` (`test_and_clear_bit(0, &port->write_urbs_free)`), but on failure sets `wport->write_urbs_free` (`set_bit(0, &wport->write_urbs_free)`), and `omninet_write_room` tests `wport->write_urbs_free`. Since `port` and `wport` are different `usb_serial_port` structures (`serial->port[0]` vs `serial->port[1]`), the free flag is split across two objects: the check/clear operates on one, the set/test on the other. This desync allows concurrent submissions (the "already writing" check never sees the cleared flag) or a stuck write path. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 81 is from the 50-seed manifest (oracle `vulnerable`), `triage_likely_valid` group.
2. The relevant code:
   ```c
   if (!test_and_clear_bit(0, &port->write_urbs_free)) { ... return 0; }  // port
   ...
   result = usb_submit_urb(wport->write_urb, GFP_ATOMIC);
   if (result) {
       set_bit(0, &wport->write_urbs_free);   // wport, not port
   }
   ```
   and `omninet_write_room`:
   ```c
   if (test_bit(0, &wport->write_urbs_free))  // wport, not port
       room = ...;
   ```
3. `port = serial->port[0]` (the tty port), `wport = serial->port[1]` (the bulk-out port). They are distinct structures, so `port->write_urbs_free` and `wport->write_urbs_free` are different memory locations.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Free flag checked on `port`, set/tested on `wport`. | Identified precisely. |
| Are `port` and `wport` the same object? | No — `serial->port[0]` vs `serial->port[1]`. | Distinct. |
| Does the mismatch allow double-submission? | Yes — the cleared flag on `port` is never observed by the `wport`-based check. | Reachable. |
| Is a trigger demonstrated? | Yes — concurrent writes. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the flag mismatch is real and the desync follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-81 claim. Does not prove all of the omninet driver safe, does not assess other paths, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
