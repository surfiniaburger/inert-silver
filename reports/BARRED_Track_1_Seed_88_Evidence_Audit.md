# BARRED Track 1 — Seed 88 Evidence Audit

## Question audited

**Claim:** "The code is **not** vulnerable to use-after-free in `crypto_reportstat` (the reference to the matched `struct crypto_alg` is correctly released with `crypto_mod_put` before any early return)."

**Result:** **Proved safe for this exact claim.** `crypto_reportstat` obtains `alg` via `crypto_alg_match`, then uses a `drop_alg:` cleanup label that calls `crypto_mod_put(alg)` on every exit path: the skb-allocation-failure path jumps to `drop_alg`, and the normal path falls through to it. Thus the reference is released before any return, whether success or error. No use-after-free occurs; the negated claim is correct.

## What was examined

1. Seed 88 is from the 50-seed manifest (oracle `safe`), `conclusion_not_deterministically_discharged` group.
2. The relevant code:
   ```c
   alg = crypto_alg_match(p, 0);
   if (!alg) return -ENOENT;
   err = -ENOMEM;
   skb = nlmsg_new(NLMSG_DEFAULT_SIZE, GFP_ATOMIC);
   if (!skb) goto drop_alg;
   ...
   err = crypto_reportstat_alg(alg, &info);
   drop_alg:
   crypto_mod_put(alg);
   if (err) { kfree_skb(skb); return err; }
   return nlmsg_unicast(...);
   ```
   `crypto_mod_put(alg)` is on the `drop_alg` label, reached by both the failure goto and the fall-through.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged defense? | `crypto_mod_put(alg)` before any return. | Present. |
| Is the reference released on all paths? | Yes — `drop_alg:` label reached by goto and fall-through. | No leak, no UAF. |
| Is a trigger demonstrated? | N/A — code is correct. | Claim (negated vulnerability) holds. |

## Why the model results

The GEPA predicate is sound in the negative: the code correctly releases the reference. The replicated model outcomes are not used as adjudication evidence.

This is **RFC Axis E: predicate validity** (the claim that the code is NOT vulnerable is correct).

## Audit boundary

Limited to the exact seed-88 claim. Does not prove all of crypto user API safe, does not assess other paths, and does not depend on the CVEFixes `safe` label.
