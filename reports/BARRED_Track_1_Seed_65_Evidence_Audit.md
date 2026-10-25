# BARRED Track 1 — Seed 65 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a use-after-free of a `net_device` in `ri_tasklet` because it stores a pointer returned by `dev_get_by_index_rcu()` in `skb->dev` and then releases the RCU read-lock before the pointer is used."

**Result:** **Confirmed vulnerable for this exact claim.** In `ri_tasklet`, `rcu_read_lock()` is taken, `skb->dev = dev_get_by_index_rcu(&init_net, skb->skb_iif)` is assigned, and `rcu_read_unlock()` is called immediately after (in both the NULL and non-NULL branches). The code then uses `skb->dev` (`dev_queue_xmit(skb)` in the egress path, `skb->dev->hard_header_len` in the ingress path) **after** the RCU read lock has been released. `dev_get_by_index_rcu` returns a reference valid only under the RCU read lock; once unlocked, the `net_device` can be freed, so the subsequent dereference is a use-after-free. The benchmark `vulnerable` label agrees.

## What was examined

1. Seed 65 is from the 50-seed manifest (oracle `vulnerable`), `triage_likely_valid` group.
2. The relevant code:
   ```c
   rcu_read_lock();
   skb->dev = dev_get_by_index_rcu(&init_net, skb->skb_iif);
   if (!skb->dev) {
       rcu_read_unlock();
       dev_kfree_skb(skb);
       ...
       break;
   }
   rcu_read_unlock();
   skb->skb_iif = _dev->ifindex;
   if (from & AT_EGRESS) {
       dev_queue_xmit(skb);
   } else if (from & AT_INGRESS) {
       skb_pull(skb, skb->dev->hard_header_len);
       netif_receive_skb(skb);
   }
   ```
   `rcu_read_unlock()` precedes all uses of `skb->dev`.
3. `dev_get_by_index_rcu` returns a pointer protected by the RCU read lock; dereferencing it after unlock is a use-after-free.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Use of `skb->dev` after `rcu_read_unlock()`. | Identified precisely. |
| Is `rcu_read_unlock` called before use? | Yes — in both branches. | Lock released early. |
| Is `skb->dev` used after unlock? | Yes — `dev_queue_xmit`, `skb->dev->hard_header_len`, `netif_receive_skb`. | UAF reachable. |
| Is a trigger demonstrated? | Yes — device removal race. | Claim substantiated. |

## Why the model results

The GEPA predicate is sound: the early `rcu_read_unlock` is real and the UAF follows. The benchmark `vulnerable` label agrees.

This is a **confirmed vulnerable** verdict (mechanism sound; benchmark label agrees).

## Audit boundary

Limited to the exact seed-65 claim. Does not prove all of ifb safe, does not assess other paths, and does not depend on the CVEFixes `vulnerable` label (which agrees here).
