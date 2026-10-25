# BARRED Track 1 — Seed 91 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to service-principal spoofing (authorization bypass) in `check_rpcsec_auth`."

**Result:** **Context deficient — unresolved.** `check_rpcsec_auth` validates that the authenticated principal has exactly two components, that the first is `kadmin`, that the realm matches `handle->params.realm`, and rejects `kadmin/history`. Any other `kadmin/<x>` principal (except `history`) is accepted. Whether this constitutes spoofing depends on the deployment's intended service-principal policy (e.g., whether only `kadmin/admin` or `kadmin/changepw` should be admitted), which is not encoded in this code. The mechanism (broad acceptance of `kadmin/*`) is visible; the security relevance is policy-dependent.

## What was examined

1. Seed 91 is from the 50-seed manifest (oracle `vulnerable`), `triage_context_deficient` group.
2. The relevant checks:
   ```c
   if (krb5_princ_size(kctx, princ) != 2) goto fail_princ;
   c1 = krb5_princ_component(kctx, princ, 0);
   c2 = krb5_princ_component(kctx, princ, 1);
   realm = krb5_princ_realm(kctx, princ);
   if (strncmp(handle->params.realm, realm->data, realm->length) == 0
       && strncmp("kadmin", c1->data, c1->length) == 0) {
       if (strncmp("history", c2->data, c2->length) == 0)
           goto fail_princ;
       else
           success = 1;
   }
   ```
   Any `kadmin/<non-history>` principal in the matching realm is accepted.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Acceptance of `kadmin/<arbitrary>` principals. | Identified precisely. |
| Is the check present? | Yes — 2 components, `kadmin` first, realm match, reject `history`. | Partial. |
| Is the accepted set broader than intended? | Depends on deployment policy. | Unresolved. |
| Is a trigger demonstrated? | Depends on whether an attacker can obtain a `kadmin/<x>` principal. | Not demonstrated. |

## Why the model results are not used as proof

The GEPA predicate asserts spoofing, but the code's acceptance set is a design choice whose security relevance depends on deployment policy. The replicated model outcomes are not used as adjudication evidence.

This is **RFC Axis D: evidence insufficiency** (policy-dependent security relevance).

## Audit boundary

Limited to the exact seed-91 claim. Does not prove all of kadm5 safe, does not assess deployment policy, and does not depend on the CVEFixes `vulnerable` label.
