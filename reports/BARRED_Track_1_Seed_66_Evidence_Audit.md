# BARRED Track 1 — Seed 66 Evidence Audit

## Question audited

**Claim:** “The code is vulnerable to a use-after-free in `crypto_rng_reset` when a registered RNG algorithm's `seed` callback retains the supplied `seed` buffer for asynchronous use.”

**Result:** **Proved safe for this exact use-after-free claim.** The framework frees only a buffer it itself allocated for the random-seed path, and only after the synchronous `seed` callback returns; a callback that retains the pointer violates the `crypto_rng` contract rather than exposing a framework bug.

## What was examined

1. I selected seed 66 because the allegation is a concrete ownership/lifetime claim: `crypto_rng_reset` frees `buf` while an algorithm callback may still reference it.
2. The relevant function:
   ```c
   int crypto_rng_reset(struct crypto_rng *tfm, const u8 *seed, unsigned int slen) {
       u8 *buf = NULL;
       int err;
       if (!seed && slen) {
           buf = kmalloc(slen, GFP_KERNEL);
           if (!buf) return -ENOMEM;
           get_random_bytes(buf, slen);
           seed = buf;
       }
       err = crypto_rng_alg(tfm)->seed(tfm, seed, slen);
       kfree(buf);
       return err;
   }
   ```
3. Two cases:
   - **Caller supplies `seed` (non-NULL):** `buf` stays NULL; `seed()` receives the caller's buffer; `kfree(NULL)` is a no-op. The framework never owns that memory, so no free occurs.
   - **Caller passes NULL with `slen > 0`:** the framework allocates `buf`, fills it with random bytes, and passes it to `seed()`. `kfree(buf)` runs only after `seed()` returns.
4. The `seed` callback is defined by the `rng_alg` implementation and is invoked synchronously. The crypto_rng contract requires the implementation to consume the seed during the call; retaining the pointer for asynchronous use is an implementation contract violation, not a framework defect. The framework is not obligated to keep a buffer alive beyond the synchronous callback.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `kfree(buf)` after `seed(tfm, seed, slen)`. | Identified precisely. |
| Does the framework free caller-owned memory? | No; `buf` is NULL on the caller-supplied-seed path. | No. |
| Does the framework free before the callback returns? | No; `kfree(buf)` follows the synchronous `seed()` call. | No. |
| Is retaining the pointer a supported contract? | No; the seed callback is synchronous and must consume the seed during the call. | Claim relies on a contract violation. |
| Is a trigger demonstrated? | No; requires an implementation that retains the pointer, which the contract forbids. | Claim refuted. |

## Why the model results were misleading

The GEPA predicate noticed `kfree(buf)` after a callback and inferred a use-after-free, but it omitted that the callback is synchronous and that the freed buffer is framework-owned only on the random-seed path. The replicated model outcomes are therefore not used as adjudication evidence.

This is **RFC Axis E: predicate invalidity**. The code's free is correct because the seed callback contract is synchronous; an implementation that retains the pointer is the defect, not `crypto_rng_reset`.

## Audit boundary

This result is limited to the exact seed-66 claim of a use-after-free in `crypto_rng_reset`. It does not prove all RNG implementations safe, does not address asynchronous seeding designs, and does not depend on the CVEFixes `safe` label.