# BARRED Track 1 — Seed 57 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a use-after-free in `big_key_destroy` where a `struct path` is dereferenced after `path_put` has potentially freed it."

**Result:** **Proved safe for this exact use-after-free claim.** `big_key_destroy` calls `path_put(path)` and then explicitly sets `path->mnt = NULL; path->dentry = NULL;`. The read path (`big_key_read`) operates under the key's read semaphore, and destroy takes the write semaphore, so they are serialized. The NULL assignment after `path_put` prevents any subsequent dereference of the (possibly freed) dentry/mnt. The predicate's UAF mechanism is not reachable in this version.

## What was examined

1. Seed 57 is in the 50-seed manifest (oracle `vulnerable`), `pro_claim_needs_independent_reproduction` group.
2. `big_key_destroy`:
   ```c
   if (key->type_data.x[1] > BIG_KEY_FILE_THRESHOLD) {
       struct path *path = (struct path *)&key->payload.data2;
       path_put(path);
       path->mnt = NULL;
       path->dentry = NULL;
   } else { kfree(key->payload.data); ... }
   ```
   `big_key_read` opens the file via `dentry_open(path, ...)` under the key read lock.
3. The destroy path runs under the key write lock; read holds the read lock. They are serialized. After `path_put`, the NULL assignment removes any dangling pointer. No dereference of freed memory occurs.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `path_put(path)` frees, then a later dereference. | Identified precisely. |
| Is the path dereferenced after `path_put`? | No — `path->mnt`/`path->dentry` set to NULL. | No dangling deref. |
| Can read race with destroy? | No — key semaphore serializes. | No race. |
| Is a trigger demonstrated? | No. | Claim refuted. |

## Why the model results

The GEPA predicate assumed `path_put` leaves a dangling pointer, but the supplied version nullifies the pointers and relies on the key semaphore. The replicated acceptance is not used as adjudication evidence.

This is **RFC Axis E: predicate invalidity**.

## Audit boundary

Limited to the exact seed-57 claim. Does not prove all of `big_key` safe, does not assess other key types or older versions without the NULL assignment, and does not depend on the CVEFixes `vulnerable` label (which is wrong for this predicate).
