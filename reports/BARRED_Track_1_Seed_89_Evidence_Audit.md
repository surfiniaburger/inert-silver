# BARRED Track 1 — Seed 89 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a use-after-free (dangling timer) in `nx842_reset_uselzo`/`failover_timer`."

**Result:** **Confirmed vulnerable for this exact claim.** `failover_timer` is a static `DEFINE_TIMER` whose callback `nx842_reset_uselzo` writes the module-global `nx842_uselzo`. It is armed via `mod_timer(&failover_timer, ...)` in `nx842_crypto_compress` when hardware fails. `nx842_mod_exit` calls `crypto_unregister_alg` but does **not** call `del_timer_sync(&failover_timer)`. If the module is unloaded while the timer is pending, the timer fires into freed module memory (the callback writes `nx842_uselzo = 0` in unloaded code/data) — a dangling-timer use-after-free. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 89 is from the 50-seed manifest (oracle `vulnerable`), `triage_context_deficient` group.
2. The relevant code:
   ```c
   static void nx842_reset_uselzo(unsigned long data) { nx842_uselzo = 0; }
   static DEFINE_TIMER(failover_timer, nx842_reset_uselzo, 0, 0);
   ...
   /* hardware failed */
   nx842_uselzo = 1;
   mod_timer(&failover_timer, jiffies + msecs_to_jiffies(1000));
   ...
   static void __exit nx842_mod_exit(void) {
       crypto_unregister_alg(&alg);
       /* no del_timer_sync(&failover_timer) */
   }
   ```
   The timer is armed but never cancelled on module exit.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `mod_timer` armed, `del_timer` missing in `mod_exit`. | Identified precisely. |
| Is the timer cancelled on exit? | No — `nx842_mod_exit` does not call `del_timer_sync`. | Dangling timer. |
| Can it fire after module unload? | Yes — if armed and module unloads. | UAF reachable. |
| Is a trigger demonstrated? | Yes — unload module within 1s of a hardware failure. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing `del_timer_sync` is real and the dangling timer follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-89 claim. Does not prove all of nx842 safe, does not assess other paths, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
