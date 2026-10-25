# BARRED Track 1 — Seed 62 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a Use-After-Free race condition in `sock_diag_lock_handler` / `sock_diag_unregister`."

**Result:** **Proved safe for this exact Use-After-Free race claim.** `sock_diag_unregister` only nullifies the handler slot under `sock_diag_table_mutex`; it performs no deallocation, and the mutex is held across `hndl->dump()` in `__sock_diag_rcv_msg`, so an unregister cannot run concurrently with a dump and no freed handler is ever dereferenced. The lock-free `NULL` check and `request_module` call outside the lock are a benign TOCTOU on a pointer word, not a memory-safety defect.

## What was examined

1. I selected seed 62 from the replicated Gemma/Gemini persistent-disagreement queue because it carries an accepted Pro claim (2/5 Gemma escalation acceptances) with status `conflicting_unadjudicated_model_outcomes`, and the allegation is a concrete ownership/lifetime claim in kernel netlink glue.
2. The relevant functions in the supplied `net/sock_diag.c` excerpt:
   ```c
   static const inline struct sock_diag_handler *sock_diag_lock_handler(int family)
   {
       if (sock_diag_handlers[family] == NULL)
           request_module("net-pf-%d-proto-%d-type-%d", PF_NETLINK,
                   NETLINK_SOCK_DIAG, family);

       mutex_lock(&sock_diag_table_mutex);
       return sock_diag_handlers[family];
   }

   static inline void sock_diag_unlock_handler(const struct sock_diag_handler *h)
   {
       mutex_unlock(&sock_diag_table_mutex);
   }

   void sock_diag_unregister(const struct sock_diag_handler *hnld)
   {
       int family = hnld->family;

       if (family >= AF_MAX)
           return;

       mutex_lock(&sock_diag_table_mutex);
       BUG_ON(sock_diag_handlers[family] != hnld);
       sock_diag_handlers[family] = NULL;
       mutex_unlock(&sock_diag_table_mutex);
   }

   static int __sock_diag_rcv_msg(struct sk_buff *skb, struct nlmsghdr *nlh)
   {
       ...
       if (req->sdiag_family >= AF_MAX)
           return -EINVAL;

       hndl = sock_diag_lock_handler(req->sdiag_family);
       if (hndl == NULL)
           err = -ENOENT;
       else
           err = hndl->dump(skb, nlh);
       sock_diag_unlock_handler(hndl);
       return err;
   }
   ```
3. I checked deallocation: `sock_diag_unregister` contains no `kfree`, `vfree`, or module-unload call. It sets `sock_diag_handlers[family] = NULL` and returns. The handler object's lifetime is owned by the registering module and is released only when that module unloads, which cannot occur while the mutex is held.
4. I checked the lock scope: `__sock_diag_rcv_msg` holds `sock_diag_table_mutex` from `sock_diag_lock_handler`'s `mutex_lock` through `sock_diag_unlock_handler`, i.e. across the entire `hndl->dump(skb, nlh)` call. `sock_diag_unregister` requires the same mutex before it can nullify the slot, so it cannot run concurrently with a dump on the same or any family.
5. I checked the lock-free pre-check: the `sock_diag_handlers[family] == NULL` test and the subsequent `request_module` run outside the mutex. This is a data race on a pointer word, but the value actually used is re-read under the lock (`return sock_diag_handlers[family]`), so a stale non-NULL observation cannot lead to dereferencing a freed or nullified handler: if unregister ran in between, the under-lock read yields `NULL` and the dump is skipped.
6. I checked bounds: `__sock_diag_rcv_msg` rejects `req->sdiag_family >= AF_MAX` before calling `sock_diag_lock_handler`, and `sock_diag_unregister` rejects `family >= AF_MAX`. Within this slice, `family` is always in range before any array access; `sock_diag_lock_handler` relies on its callers, which is a latent fragility but not a reachable defect here.
7. I checked CVEFixes provenance: the supplied topic matches a Linux kernel `net/sock_diag.c` excerpt (CVEFixes row for the CVE-2013-1763 family). As with seeds 42, 46, 50, 66, and 68, the corpus row retains only `code`, `language`, and `safety` fields — no version/commit metadata. The `safe` label is consistent with this result, but the locking contract — not the label — settles it.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `sock_diag_lock_handler` returns a handler pointer that `sock_diag_unregister` later nullifies, allegedly leaving a dangling reference. | Identified precisely. |
| Does `sock_diag_unregister` free the handler? | No; it only sets `sock_diag_handlers[family] = NULL`. No `kfree`/`vfree`/unload call. | No deallocation by the framework. |
| Can unregister run while a dump uses the handler? | No; `__sock_diag_rcv_msg` holds `sock_diag_table_mutex` across `hndl->dump()`, and `sock_diag_unregister` acquires the same mutex. | Serialized by the mutex. |
| Can a stale pointer from the lock-free NULL check be dereferenced? | No; the returned value is re-read under the lock, so a concurrent unregister yields `NULL` and skips the dump. | No dangling dereference. |
| Is the race attacker-triggerable? | No; `sock_diag_unregister` is invoked by module exit, not by netlink input, and requires a privileged module unload. | Not reachable by an unprivileged caller. |
| Is a trigger demonstrated? | No; no sequence of netlink messages or module operations produces a dereference of freed handler memory. | Claim refuted. |

## Why the model results were misleading

The GEPA predicate noticed the NULL check and the nullification and inferred a Use-After-Free, but it omitted three decisive facts: `sock_diag_unregister` performs no deallocation, the mutex is held across the entire `dump()` call, and the pointer used is re-read under the lock. The replicated model outcomes are therefore not used as adjudication evidence. The con-side argument recorded in the run ("pointer is only nullified, not the underlying memory") is technically correct and is adopted here; its `invalid_contract` receipt reflects a missing machine-checkable defense obligation, not a semantic error.

This is **RFC Axis E: predicate invalidity**. The handler's lifetime is serialized by `sock_diag_table_mutex` and is never released by the framework, so the alleged UAF cannot occur. The lock-free pre-check and out-of-lock `request_module` are real code characteristics worth hardening, but they do not constitute a vulnerability under the supplied contract.

## Audit boundary

This result is limited to the exact seed-62 claim of a Use-After-Free race in `sock_diag_lock_handler` / `sock_diag_unregister`. It checks the locking contract visible in this excerpt; it does not prove all of `net/sock_diag.c` safe, does not assess other entry points or families, does not address hypothetical future callers that bypass the `AF_MAX` check, and does not depend on the CVEFixes `safe` label. It makes no claim about the separate CVE-2013-1763 out-of-bounds issue, which is already guarded by the `>= AF_MAX` check present in this slice.
