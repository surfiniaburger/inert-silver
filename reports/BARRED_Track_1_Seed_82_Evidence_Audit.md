# BARRED Track 1 — Seed 82 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a use-after-free race condition in `ipv6_defrag` when calling `nf_ct_frag6_gather`."

**Result:** **Proved safe for this exact claim.** `ipv6_defrag` calls `nf_ct_frag6_gather(state->net, skb, ...)` and uses **only** the integer return value `err`. It does not dereference `skb` after the call — it returns `NF_STOLEN` if `err == -EINPROGRESS`, otherwise `NF_ACCEPT`/`NF_DROP` based on `err`. Any use-after-free would have to occur inside `nf_ct_frag6_gather` (defined in `nf_conntrack_reasm.c`, not in this seed), not in `ipv6_defrag` itself. The benchmark `vulnerable` label is wrong for this predicate.

## What was examined

1. Seed 82 is from the 50-seed manifest (oracle `vulnerable`), `triage_context_deficient` group.
2. The relevant code:
   ```c
   err = nf_ct_frag6_gather(state->net, skb, nf_ct6_defrag_user(state->hook, skb));
   /* queued */
   if (err == -EINPROGRESS)
       return NF_STOLEN;
   return err == 0 ? NF_ACCEPT : NF_DROP;
   ```
   `skb` is passed to the callee but not dereferenced by `ipv6_defrag` after the call.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | UAF in `ipv6_defrag` via `nf_ct_frag6_gather`. | Identified precisely. |
| Does `ipv6_defrag` dereference `skb` after the call? | No — only the return value `err` is used. | No deref. |
| Can UAF occur in this function? | No. | Claim refuted for this code. |

## Why the model results

The GEPA predicate attributed the UAF to `ipv6_defrag`, but the function only uses the return value. The benchmark `vulnerable` label is wrong for this predicate.

This is **RFC Axis E: predicate invalidity** (for this code; the callee is a separate question).

## Audit boundary

Limited to the exact seed-82 claim of a UAF in `ipv6_defrag`. Does not assess `nf_ct_frag6_gather` (in `nf_conntrack_reasm.c`), does not prove all of IPv6 defrag safe, and does not depend on the CVEFixes `vulnerable` label (which is wrong for this predicate).
