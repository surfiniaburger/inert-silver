# BARRED — Con Receipt Quality Plan v2

**Status:** Plan (not yet implemented). Derived from the Track 2 Replicate 1 Con-path audit, the review feedback, and the Qwen smoke run findings.
**Required result:** A Con outcome is accepted and can halt only when a machine-verifiable, seed-appropriate proof exists; otherwise the run records an explicit unresolved/unsupported result—never a fabricated Pro win or a prompt-shaped fake receipt.

---

## 1. Define one authoritative outcome contract

Replace the current independent fields:

```json
{
  "winner": "con_debater",
  "counter_evidence": null
}
```

with a discriminated decision contract:

```json
{
  "outcome": "pro_win | con_win | unresolved",
  "con_candidate_id": "C1 | null",
  "... common adjudication fields ...": "..."
}
```

Rules:

- `outcome=con_win` requires a non-null `con_candidate_id`.
- `con_candidate_id` must be one of the server-generated candidates for that exact code slice and seed.
- `outcome=pro_win` has no Con candidate.
- `outcome=unresolved` is required when the code/predicate is outside the currently supported deterministic proof domain. Use a dedicated `unresolved_reason` field to distinguish unsupported proof domains (`unsupported_proof_domain`) from ordinary inconclusive runs (`inconclusive`). Downstream metrics must treat these as distinct categories.
- The model never supplies guard anchors, operation anchors, value relations, enforcement, or a defense kind for a Con result. It selects an ID only.
- The runtime reconstructs the receipt from the selected immutable candidate, then validates it.

This removes the present failure mode where Qwen invents a plausible-looking but unsupported structure.

## 2. Make the candidate extractor the source of truth

Change the extractor output from prompt guidance into an executable proof object:

```python
CandidateReceipt(
    candidate_id="C1",
    obligation_kind="upper_bound",
    defense_kind="upper_bound_reject",
    guard_anchor="if (len > cap) return;",
    protected_operation_anchor="memcpy(dst, src, len)",
    guarded_value="len",
    operation_value="len",
    enforcement="reject_before_operation",
    value_relation="guarded_value_equals_operation_value",
    bound_relation="guarded_value_less_than_or_equal_capacity",
    capacity_relation="capacity_is_size_of_destination",
    proof_capability="deterministic_v1",
)
```

At runtime:

1. Slice code for the judge.
2. Extract candidates from that exact slice.
3. Filter candidates to only those the deterministic validator can actually prove.
4. Give the model a compact numbered list:
   ```text
   Con options:
   - C1: proven upper-bound rejection protecting memcpy(..., len)
   - No valid deterministic Con receipt is available.
   ```
5. If the model selects `C1`, resolve the complete receipt locally.
6. Do not accept copied or free-text receipt content from the model.

The current code says "select a candidate by ID," but does not include `candidate_id` in the template or wire the allowed IDs into validation. Those three parts need to become one mechanism.

## 3. Stop claiming support for proof families that are not implemented

The code currently advertises three families:

- `upper_bound`
- `null_dereference`
- `identity_mismatch`

But extraction supports only `upper_bound`.

The first implementation should make this explicit:

| Obligation | Candidate extraction | Deterministic validation | Runtime result today |
|---|---:|---:|---|
| `upper_bound` | supported | supported when parser and sink semantics exist | eligible |
| `null_dereference` | not implemented | partial/inconsistent | unresolved |
| `identity_mismatch` | not implemented | partial/inconsistent | unresolved |

The prompt must not tell the model to return Pro simply because there is no candidate. "No candidate" may mean "unsupported proof domain," not "the vulnerability is true."

Later, if needed, add each family end-to-end:

- Null dereference: null guard, alias/value identity, dereference or call requiring non-null.
- Identity mismatch: equality/identity comparison, rejected mismatch path, protected use.
- Upper-bound: guard operand, bound operand, operation operand, dominance.

Each family gets its own extractor, proof semantics, fixtures, and negative cases before being enabled for real seeds.

## 4. Replace keyword-derived obligations with reviewed seed metadata

The current loader infers obligations from words such as "overflow," "null," and "identity." That is too broad: a word in a predicate does not establish which deterministic proof family applies.

Change seed metadata to carry an explicit reviewed contract, for example:

```json
{
  "seed_id": "barred-0047",
  "predicate": "...",
  "defense_contract": {
    "version": "v1",
    "kind": "upper_bound",
    "operation_class": "memory_copy",
    "eligibility": "supported_v1"
  }
}
```

or:

```json
{
  "seed_id": "barred-0050",
  "predicate": "...",
  "defense_contract": {
    "eligibility": "unsupported_v1",
    "reason": "timer lifecycle semantics are not modeled"
  }
}
```

No reviewed contract means `unresolved`, not an inferred obligation. The runtime must return `unresolved` for missing or unsupported contracts **before** evaluating the legacy `con_win_gate`. An unsupported seed must never become a Con win through the legacy gate.

This also fixes the current mismatch between the smoke result narrative and the actual run's seed predicates.

## 5. Align extractor and validator capabilities

Today the extractor can surface broad function calls, while the validator rejects anything outside a small recognized sink list. That guarantees apparently valid candidates which can never pass.

Establish an explicit operation taxonomy:

```python
SUPPORTED_OPERATION_CLASSES = {
    "memory_copy": {"memcpy", "memmove", ...},
    "memory_write": {"memset", ...},
    "memory_free": {"free", "kfree"},
    "array_subscript": "AST-backed",
    "pointer_dereference": "AST-backed",
}
```

For a candidate to reach the model, all three must agree:

1. extractor recognizes the operation;
2. the seed contract permits that operation class;
3. validator has deterministic proof semantics for it.

Unknown wrappers such as `setobj2s`, `get_desc_base`, or `gdImageJpegPtr` must be classified as `unsupported_v1`, unless a reviewed semantic adapter is added for that specific operation family. They should not be shown as selectable "candidates."

## 6. Make parser availability a startup requirement

A valid receipt is currently impossible when Tree-sitter C support is absent. That must fail early, before a smoke run starts.

Add a preflight such as:

```text
BARRED deterministic Con receipts enabled:
- tree_sitter import: PASS
- tree_sitter_c import: PASS
- C parser construction: PASS
- known valid guard fixture: PASS
```

If any check fails:

- refuse `--counter-evidence-validation-mode enforce_deterministic`; or
- run in explicit `shadow/unresolved-only` mode.

It must never run as though deterministic Con confirmation is available when it is not.

## 7. Tighten prompt structure without relying on it for proof

The Claude-style structure is broadly retained: role, task, context, thinking, constraints, and strict JSON output are already present.

Simplify the Con portion to this:

```text
For a Con result, select exactly one listed candidate ID.
Do not create or modify a receipt.
If no listed candidate proves the defense, return outcome="unresolved".
```

Then include one or two concise examples inside the system prompt:

```json
{"outcome":"con_win","con_candidate_id":"C1"}
```

```json
{"outcome":"unresolved","con_candidate_id":null}
```

The examples are useful for Qwen protocol compliance, but correctness remains in the candidate resolver and validator.

## 8. Preserve complete evidence in attempt artifacts

Rejected attempts should retain:

- raw parsed judge outcome;
- selected candidate ID;
- complete model-emitted receipt only for diagnosis;
- generated candidate IDs and their capability status;
- validator status and exact rejection reason;
- code-slice hash;
- input seed ID and seed-file hash;
- model and prompt-contract version.

This is needed to answer "did the model omit the receipt, choose an invalid candidate, or was the candidate unsupported?" without mining the cassette.

## 9. Make the run provenance unambiguous

The smoke manifest should record:

```json
{
  "run_id": "q9-smoke-armC-struct-esc",
  "seed_file": ".../cve_seeds_smoke_2.jsonl",
  "seed_file_sha256": "...",
  "seed_ids": ["barred-0042", "..."],
  "prompt_contract_version": "con-candidate-v2",
  "validator_version": "counter-evidence-v2",
  "parser_preflight": "passed"
}
```

The current numbered smoke rows cannot safely be interpreted as canonical-ledger IDs. This is why the pasted analysis attributes different predicates to several seed numbers than the actual artifact contains.

## 10. Test plan before another model smoke

First, no model calls.

### A. Schema tests

- A `con_win` without `con_candidate_id` must fail schema validation.
- A `pro_win` with a candidate ID must fail.
- `unresolved` with no candidate must pass.

### B. Candidate-resolution tests

- Candidate `C1` resolves to exactly its immutable receipt.
- Unknown `C99` is rejected.
- A valid-looking model-supplied anchor cannot replace candidate `C1`'s anchor.
- Candidate IDs are scoped to the exact code-slice hash.

### C. Parser preflight tests

- Missing `tree_sitter_c` causes deterministic mode startup failure.
- A valid C `memcpy` guarded by `if (len > cap) return;` passes parser preflight and confirms.
- Unparseable C yields `unresolved/inconclusive`, never `con_win`.

### D. Proof-family fixtures

For each enabled family, include:

| Fixture | Expected result |
|---|---|
| Guard dominates a recognized sink and protects same value | `deterministically_confirmed` |
| Guard occurs after operation | rejected/refuted |
| Negative length (len < 0) | rejected/refuted |
| Guard checks a different value | rejected/refuted |
| Operation is an unknown wrapper | unsupported/unresolved |
| Model selects non-existent candidate | invalid contract |
| Model chooses "Con" with no candidates | schema/runtime rejection |

### E. End-to-end deterministic walk-through

Use this controlled fixture:

```c
void f(char *dst, char *src, int len, int cap) {
    if (len < 0) return;
    if (len > cap) return;
    memcpy(dst, src, len);
}
```

Expected execution:

1. Reviewed metadata assigns `upper_bound` plus `memory_copy`.
2. Extractor returns `C1`.
3. Validator proves `C1` independently before the model is involved.
4. Prompt exposes only `C1` or `unresolved`.
5. Model returns `con_win/C1`.
6. Runtime resolves `C1`, confirms it, emits `validated_con_counter_evidence`.
7. `--halt-on-con-win` halts.
8. Artifact records candidate, proof trace, parser state, and provenance.

Then run the negative fixture where `memcpy` occurs before the guard. The extractor must produce no valid selectable candidate, and a model's attempted Con must end as `unresolved`, never accepted.

## 11. Only then rerun the Qwen smoke

The rerun should report separate measures:

- parser/preflight health;
- seeds eligible for deterministic Con adjudication;
- candidate extraction coverage;
- model candidate-selection accuracy;
- deterministic receipt confirmations;
- unresolved/unsupported seeds;
- Pro acceptance quality.

The success criterion should be:

```text
Every accepted Con has a local deterministic proof.
Every unsupported seed is explicitly unresolved.
No invalid receipt can halt or contaminate training output.
```

It should not be "the funnel has more Con wins." A larger Con count without that contract would be a regression.

---

## Relationship to existing tracks

- **Track 1 (predicate audit):** Complete. All 50 seeds adjudicated. The `defense_obligation` field (Step 6) has been added to 30 seeds.
- **Track 2 (experiment spec):** v2, ready for freeze. The Con receipt plan does not change the four-arm design.
- **Track 3 (evidence sufficiency):** The `unsupported_v1` classification and `callee_contract_required` distinction extend Track 3's Axis D (evidence insufficiency) into the receipt pipeline.
- **Track 4 (Muse/Qwen evaluation):** Deferred. The receipt plan is model-agnostic and can be evaluated on any available model.

## What this does NOT change

- The halt-on-con-win flag (`--halt-on-con-win`) stays as implemented. It halts on any Con win, including a Con win without a `deterministically_confirmed` receipt. This is an explicit exception to "No invalid receipt can halt" until the flag consumes only validated outcomes. Until Step 10 is complete, treat halt-on-con-win as an engineering mechanism, not a measured policy.
- The Track 2 experiment spec (four-arm factorial) is unchanged.
- The Track 1 audit ledger is unchanged.
- The canonical adjudication ledger is unchanged.
