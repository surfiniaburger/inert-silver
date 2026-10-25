# BARRED Track 1 — Seed 56 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to an unchecked use-after-free / invalid pointer dereference in `gss_process_context_token` when dereferencing `ctx->internal_ctx_id`."

**Result:** **Mechanism confirmed by analogy to seed 60; reachability open.** The code is structurally identical to seed 60: `val`-style checks only `context_handle == GSS_C_NO_CONTEXT`, then casts to `gss_union_ctx_id_t` and reads `ctx->internal_ctx_id` and `ctx->mech_type` with no handle validation. A crafted handle with `internal_ctx_id != 0` and a garbage `mech_type` dereferences under `gssint_get_mechanism` and crashes (demonstrated for seed 60 via `/tmp/harness60/harness.c`). The 1998 Sun glue supplies no magic-number or registry validation. Security status depends on the caller model, which the seed does not supply.

## What was examined

1. Seed 56 is in the 50-seed manifest (oracle `safe`), `pro_claim_needs_independent_reproduction` group.
2. The relevant code in `g_process_context.c`:
   ```c
   if (context_handle == GSS_C_NO_CONTEXT) return (...);
   ...
   ctx = (gss_union_ctx_id_t) context_handle;
   if (ctx->internal_ctx_id == GSS_C_NO_CONTEXT) return (GSS_S_NO_CONTEXT);
   mech = gssint_get_mechanism(ctx->mech_type);
   ```
   Identical validation gap to seed 60.
3. The mechanism is confirmed by construction (seed-60 harness); execution of an analogous harness for 56 was not separately performed.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Cast of an unvalidated `context_handle` to `gss_union_ctx_id_t`, then dereference. | Identified precisely. |
| Is the mechanism reachable given a crafted handle? | Yes — identical to seed 60, confirmed by runtime crash. | Demonstrated by analogy. |
| Is attacker reachability established? | No — caller model unknown. | Open. |

## Why the model results

The GEPA predicate is sound on mechanism; the replicated acceptance is consistent. This is not Axis E (predicate invalidity) — the deref is real — but security relevance is unproven (Axis D on reachability).

## Audit boundary

Limited to the exact seed-56 claim. Does not prove all of GSSAPI glue safe, does not assess other entry points, and does not depend on the CVEFixes `safe` label. Security status depends on the caller model.
