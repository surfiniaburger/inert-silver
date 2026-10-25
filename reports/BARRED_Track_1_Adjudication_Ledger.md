# BARRED Qwen Pilot Appendix: Case-Level Evidence and Adjudication

**Status:** Supporting appendix only. This covers the ten-seed Qwen pilot's disputed predicates and terminal failures; it is not the primary Track 1 Gemma/Gemini discrimination ledger.

**Scope:** `scenarios/debate/cve_seeds_pilot_10.jsonl` (run seeds 42–51) and `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl`.

## Method and decision rule

Each row keeps four things separate:

1. The benchmark oracle label.
2. The exact predicate supplied to the agents.
3. The historical pipeline outcome.
4. This audit's case verdict.

`passes_audit: false`, an unvalidated Con win, and an oracle label are not independent security proof.  A predicate is marked **invalid** only when the supplied code plus a stable language/OS contract refutes its claimed mechanism.  It is marked **context deficient** when the decisive implementation or runtime contract is absent.  No context-deficient row is re-labelled safe.

The RFC buckets are: **A** model utilization, **B** evidence coverage, **C** parser/interface, **D** evidence sufficiency, and **E** predicate invalidity.  A row can have a primary pipeline bucket and a distinct predicate verdict.

## Predicate adjudication

| Seed | Oracle | Exact mechanism under audit | Historical outcome | Independent verdict | RFC bucket | Supporting evidence | Consequence |
|---|---|---|---|---|---|---|---|
| 46 | Safe | `RSTRING_LEN(content)` narrows to `int` before `xmlSchemaNewMemParserCtxt`, allegedly causing a heap overflow | R0 rejected; R1 accepted through `validated_con_counter_evidence` | **Context deficient — unresolved.** The narrowing conversion is present, but neither the relevant libxml2 implementation/version nor an `INT_MAX` guard is in the supplied snippet. The historical Con receipt is `invalid_contract` (`counter_evidence_missing`), so it cannot prove safety. | **D** | Seed code contains `(int)RSTRING_LEN(content)` and the call site only. Current libxml2 has explicit large-buffer limits, but that does not establish the version embedded by the seed. | Do not count this as a confirmed safe-oracle agreement or an invalid predicate. Pin the libxml2 revision and reproduce with a bounded large-input harness before scoring it. |
| 47 | Vulnerable | `posix_acl_from_xattr()` retains `data`, then `kfree(data)` creates UAF | R1 rejected: `verifier_failed` | **Invalid predicate.** The conversion constructs a `struct posix_acl`; callers are expected to free their input buffer after conversion. The claimed retained-pointer mechanism needs evidence contrary to that allocation/copy contract and none is present. | **E** | The seed shows `acl = posix_acl_from_xattr(..., data, len); kfree(data); return acl;`. Linux's implementation allocates a POSIX ACL during decoding rather than making the returned ACL alias the xattr buffer. | Re-label the exact predicate as invalid. This does not make a claim about unrelated GFS2 defects. |
| 49 | Vulnerable | `createwbmp()` allocation / `pos` overflow leads to `wbmp->bitmap[pos]` OOB write | R0 accepted through `validated_con_counter_evidence` | **Context deficient — unresolved.** Checking `wbmp == NULL` only handles a NULL-returning allocator. The snippet omits `createwbmp()` and its size arithmetic, so it cannot establish whether overflow is detected, wraps, or returns a usable undersized allocation. The historical Con receipt is `invalid_contract` (`counter_evidence_missing`). | **D** | The caller has `if ((wbmp = createwbmp(...)) == NULL) return;` followed by `wbmp->bitmap[pos]`; the size calculation is not supplied. | Withdraw the previous “guard is sufficient” conclusion. Obtain the exact `createwbmp()` implementation and exercise dimensions around multiplication/index limits. |
| 51 | Vulnerable | A symlink at `PASSWD_FILE` makes `rename(tmpname, PASSWD_FILE)` overwrite the symlink's target arbitrarily | R0 rejected for logic error; R1 accepted through `validated_con_counter_evidence` | **Invalid predicate.** POSIX rename replaces the directory entry at the destination; it does not follow a destination symlink to overwrite its target. The destination is also a fixed `PASSWD_FILE`, not an attacker-selected path. | **E** | The seed creates `tmpname` under `/etc` then calls `rename(tmpname, PASSWD_FILE)`. POSIX `rename()` specifies replacement of the destination path entry; a symbolic link at that path is replaced rather than dereferenced. | Re-label this exact symlink-target overwrite predicate invalid. Do not infer that the program has no other file-handling flaw. |

## Qwen terminal-failure classification

| Seed | Round outcomes | Primary terminal bucket | Predicate verdict | Why this is the right classification | Fixability |
|---|---|---|---|---|---|
| 47 | R0 `judge_parse_failed`; R1 `verifier_failed` | **E — predicate invalidity** | Invalid (above) | R1 reached a structured judge result and verifier. The pipeline had enough code anchors to test the claimed ownership chain; the claim itself fails. | Not a plumbing repair; correct/remove the predicate. |
| 48 | R0 `predicate_quality_failed`; R1 `judge_parse_failed` | **C — parser/interface** | Invalid | R1 failed Pydantic JSON decoding (`expected ',' or ']'`). Separately, `mode = 0644` gives write permission to the owner, not unprivileged users, so the supplied privilege-escalation mechanism is false. | Yes. The parse failure is independent of missing semantic evidence. The R0 predicate-quality issue also needs prompt/anchor alignment. |
| 50 | R0 `judge_parse_failed`; R1 `judge_parse_failed` | **C — parser/interface** | Invalid | R0 produced `counter_evidence` as a list where the schema required an object; R1 was malformed JSON. The code itself first copies `length` bytes into a NUL-terminated `g_strndup()` buffer. With a trailing `%`, `s[1]` reads the terminator and short-circuiting prevents `s[2]`; with `%F`, `s[2]` reads the terminator. | Yes. A lossless single-item compatibility normalizer handles the observed R0 schema shape; malformed JSON remains subject to the existing repair/retry path. |

## Axis C conclusion

The two terminal `judge_parse_failed` cases are **plumbing**, not evidence-sufficiency failures:

- Seed 48's recorded error is syntactically invalid JSON. Its R0 `predicate_quality_failed` is a separate grounding/prompt issue.
- Seed 50's R0 error is a response-shape mismatch and its R1 error is malformed JSON. Neither failure reached a semantic verifier.

Accordingly, no Axis-C Qwen failure may be used to estimate a deterministic-evidence ceiling.  Track 2 may use the Qwen pilot only after parser recovery is measured separately and only rows with durable, versioned receipts are treated as Con-backed.

## Evidence references

- Seed manifest: `scenarios/debate/cve_seeds_pilot_10.jsonl`.
- Attempt ledger: `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl`.
- [Linux `posix_acl_from_xattr` implementation](https://github.com/torvalds/linux/blob/master/fs/posix_acl.c) (the current implementation is corroborative source evidence, not a substitute for pinning a historical kernel revision).
- [POSIX `rename()` specification](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html).
- [Current libxml2 buffer overflow-limit handling](https://github.com/GNOME/libxml2/blob/master/buf.c) (corroborative only; seed 46 remains unresolved without the historical dependency revision).

## Appendix conclusion

The Qwen case classification and Axis-C diagnosis are complete. It cannot establish a Gemma/Gemini model-family discrimination claim because it contains one compact-model run with ten seeds. The primary Track 1 artifact is `reports/BARRED_Gemma_Gemini_Discrimination_Ledger.md`; Qwen results remain useful only as a parser-contract regression appendix.
