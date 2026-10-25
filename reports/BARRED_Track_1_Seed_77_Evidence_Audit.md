# BARRED Track 1 — Seed 77 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a use of an uninitialized pointer in `ipv6_exthdrs_len` which can lead to a kernel crash or memory corruption in `ipv6_gro_complete`."

**Result:** **Confirmed vulnerable for this exact claim.** In `ipv6_exthdrs_len`, `*opps` is assigned only inside the `if (proto != NEXTHDR_HOP)` block. When the first extension header is a hop-by-hop header (`proto == NEXTHDR_HOP`), that block is skipped, so `*opps` is never written and retains whatever value the caller's variable held. The caller (`ipv6_gro_receive`) then tests `if (!ops || !ops->callbacks.gro_receive)` on an uninitialized pointer, which can crash or read arbitrary memory. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 77 is from the 50-seed manifest (oracle `vulnerable`), `triage_context_deficient` group.
2. The relevant code:
   ```c
   static int ipv6_exthdrs_len(struct ipv6hdr *iph, const struct net_offload **opps) {
       ...
       proto = iph->nexthdr;
       for (;;) {
           if (proto != NEXTHDR_HOP) {
               *opps = rcu_dereference(inet6_offloads[proto]);
               if (unlikely(!(*opps))) break;
               if (!((*opps)->flags & INET6_PROTO_GSO_EXTHDR)) break;
           }
           opth = (void *)opth + optlen;
           optlen = ipv6_optlen(opth);
           len += optlen;
           proto = opth->nexthdr;
       }
       return len;
   }
   ```
   When `proto == NEXTHDR_HOP` on the first iteration, `*opps` is never assigned.
3. Caller (`ipv6_gro_receive`): `ops = rcu_dereference(inet6_offloads[proto]); ... if (!ops || !ops->callbacks.gro_receive)` — but if `ipv6_exthdrs_len` was called first and left `*opps` uninitialized, the caller reads garbage.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `*opps` left uninitialized when first header is NEXTHDR_HOP. | Identified precisely. |
| Is `*opps` assigned in all paths? | No — skipped when `proto == NEXTHDR_HOP`. | Uninitialized in that path. |
| Is the uninitialized value used by caller? | Yes — `if (!ops || !ops->callbacks.gro_receive)`. | Crash/memory corruption reachable. |
| Is a trigger demonstrated? | Yes — IPv6 packet starting with a hop-by-hop extension header. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the missing `*opps` initialization is real and the uninitialized dereference follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-77 claim. Does not prove all of IPv6 offload safe, does not assess other paths, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
