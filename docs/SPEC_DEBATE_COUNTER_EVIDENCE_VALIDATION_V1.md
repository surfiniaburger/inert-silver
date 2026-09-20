# Specification: Debate Counter-Evidence Validation v1

## Status

Implemented for deterministic slices 1--3 behind
`counter_evidence_validation_mode` (default: `shadow`). Phase B's dedicated
LLM defense auditor remains intentionally deferred and shadow-only by design.

## Decision Summary

When `con_debater` wins, the system must not run the current Predictive
Verifier as if a Con defense were an exploit claim. `passes_audit=True` in the
current verifier means that a vulnerability mechanism is technically grounded;
that semantics is appropriate for a Pro win and inverted for a Con win.

Instead, a Con win may bypass the exploit verifier only after it has produced a
`counter_evidence_validated` receipt. The receipt must establish the following
claim:

> This exact, executable defense constrains the value or state used by this
> exact protected operation on every relevant path, so the exploit precondition
> stated by the predicate cannot hold.

This is a policy separation, not a polarity conversion:

| Outcome | Claim being tested | Required validator |
| --- | --- | --- |
| Pro win | The proposed vulnerability mechanism is possible. | Existing Predictive Verifier / exploit audit. |
| Con win | A concrete defense prevents the proposed mechanism. | Counter-evidence validator defined here. |

No implementation may treat `VerifierReport.passes_audit=False` as a generic
Con success. It is a result from an attack-shaped prompt and can contain
attack-specific `logic_error` text that does not evaluate the Con proof.

## Context and Problem

The current Con gate accepts a guard-like word in judge prose and the presence
of one supplied anchor in that prose. It proves that an LLM mentioned a
plausible defense; it does not prove that the defense blocks the alleged
mechanism. Conversely, the existing verifier's contract asks whether a proposed
vulnerability mechanism is grounded. Applying that contract after a valid Con
decision produces a polarity mismatch.

The judge and B-gate are critical-path harness code. This specification follows
the repository engineering principles:

- use deterministic validators for hard facts and LLMs for nuanced judgment;
- validate and translate at LLM, artifact, and report boundaries;
- preserve why an outcome was accepted, rejected, or uncertain;
- do not weaken a gate merely to remove an observed failure mode.

## Goals

1. Accept a Con conclusion only when evidence shows that a defense blocks the
   mechanism relevant to the seed predicate.
2. Eliminate the current exploit-audit polarity mismatch without changing Pro
   verifier semantics.
3. Make the validation evidence reproducible from the code snippet and emitted
   artifact.
4. Distinguish deterministic proof, defense-auditor confirmation, refutation,
   and inconclusive validation in telemetry and exports.
5. Start with a narrow, testable set of defense patterns. Unknown patterns must
   fail closed as `inconclusive`, not pass from textual plausibility.

## Non-Goals

- Proving arbitrary security properties for C, C++, or every other supported
  language.
- Replacing the debate judge or the existing Pro exploit verifier.
- Inferring security guarantees from comments, names, or an unrelated check.
- Changing target-verdict polarity or silently relabeling historical artifacts.
- Requiring a full compiler or whole-program analysis in v1.

## Proposed Contract

### New judge output field

Extend `DebateEval` with an optional `counter_evidence` object. It is required
when `winner == "con_debater"`; it must be absent or `null` for a Pro win.

```json
{
  "defense_kind": "upper_bound_reject",
  "guard_anchor": "if (bpp > 32) return AVERROR(EINVAL);",
  "guarded_value": "bpp",
  "protected_operation_anchor": "1U << bpp",
  "operation_value": "bpp",
  "enforcement": "reject_before_operation",
  "invariant": "0 <= bpp <= 32 before the shift",
  "predicate_precondition": "bpp exceeds the permitted uint32_t shift width",
  "value_relation": "guarded_value_equals_operation_value",
  "counterfactual": "Removing the rejection allows bpp > 32 to reach the shift."
}
```

All fields are strings except the fixed enumerations below. The prompt must
require that `guard_anchor` and `protected_operation_anchor` are verbatim,
functional substrings of the code snippet.

### Enumerations

`defense_kind` in v1:

- `upper_bound_reject`
- `lower_bound_reject`
- `range_guarded_operation`
- `null_check`
- `equality_reject`
- `lock_before_shared_access`

`enforcement` in v1:

- `reject_before_operation`
- `operation_inside_safe_branch`
- `validated_value_forwarded`
- `lock_held_at_operation`

`value_relation` in v1:

- `guarded_value_equals_operation_value`
- `guarded_value_bounds_offset_plus_width`
- `guarded_value_matches_compared_identity`
- `guarded_value_protects_shared_state`

The closed vocabulary is intentional. A novel pattern must be added by a later
version together with its validator and regression fixtures, rather than being
accepted by generic wording.

### Con-specific mechanism format

The current attack-shaped mechanism template (`Source anchor`, `Sink anchor`,
and `Missing guard anchor`) must not be used as the proof format for a Con win.
For `winner == "con_debater"`, the judge prompt must instead require:

```text
Guard anchor: <verbatim executable check or lock>
Protected operation anchor: <verbatim use protected by the defense>
Value-flow relation: <which value/state connects guard and operation>
Established invariant: <predicate-specific fact true at operation>
```

The guard data fields, not this prose, are the validator input. The prose is
retained for human review only.

## Validator Design

### Parser and proof-layer decision

V1 extends `scenarios/debate/graphify_flow_extractor.py` as a separate,
proof-oriented layer. It reuses its Tree-sitter C parser, fragment recovery,
source/sink taxonomy, and `FlowGraphSnapshot` provenance. It does **not** use
the existing `FlowSignature.sanitizer_type` or `guarded_target` as sufficient
acceptance proof.

The existing extractor is a discovery and diagnostic component: it identifies
candidate sinks and records that a recognized sanitizer appears in an enclosing
branch. The counter-evidence layer has the narrower job of proving the defense
relationship asserted by a Con win. It must retain, in a new proof record:

- the guard AST node and its original-code span;
- the guard condition operator and polarity;
- guarded operand(s);
- protected-operation AST node and its original-code span;
- the operation operand(s) relevant to the vulnerability class; and
- the recognized control-flow and value-flow relationship.

Fragment wrapping and semicolon repair remain permitted for AST recovery, but
the receipt must locate every anchor in the original unmodified snippet. A span
from a synthetic candidate is never exportable as proof.

V1 supports only these deterministic proof patterns:

1. Safe-branch bounds check: `if (len <= capacity) memcpy(..., len);` where the
   exact checked value is the size operand at the protected operation.
2. Rejecting bounds check: `if (len > capacity) return; memcpy(..., len);`
   where the rejecting branch dominates the subsequent operation.
3. Non-null safe branch that dominates the exact pointer dereference.
4. Equality mismatch rejection that occurs before accepting or using the
   compared identity.

All other forms, including aliases, arithmetic not covered by a declared proof
pattern, transformed values, interprocedural relations, and unparseable code,
are `inconclusive`; they are never inferred safe from text or a generic
sanitizer label. A deliberately narrow lexical recognizer is not a primary
parser and may only be used later as a recovery aid whose result remains
inconclusive unless Tree-sitter-backed proof checks succeed.

### Result model

The validator returns a structured receipt rather than a boolean:

```json
{
  "status": "deterministically_confirmed",
  "method": "structural_v1",
  "defense_kind": "upper_bound_reject",
  "checks": {
    "guard_anchor_exact": true,
    "operation_anchor_exact": true,
    "anchors_are_functional": true,
    "value_relation_valid": true,
    "control_flow_valid": true,
    "predicate_precondition_blocked": true,
    "counterfactual_coherent": true
  },
  "evidence": {
    "guard_span": {"start_line": 11, "end_line": 11},
    "operation_span": {"start_line": 14, "end_line": 14},
    "guarded_value": "bpp",
    "operation_value": "bpp"
  },
  "failure_reasons": [],
  "validator_version": "counter_evidence_v1"
}
```

Permitted statuses:

| Status | Meaning | May accept Con win? |
| --- | --- | --- |
| `deterministically_confirmed` | A recognized structural pattern proves the required relationship. | Yes. |
| `defense_auditor_confirmed` | Static checks passed; a dedicated defense auditor confirmed the unresolved semantic relation. | Not in V1; shadow-only until separately promoted. |
| `refuted` | Evidence contradicts the asserted defense. | No. |
| `inconclusive` | The pattern is unsupported or available evidence cannot establish the relationship. | No; retry/refine or route for human review. |
| `invalid_contract` | Missing, malformed, non-verbatim, or contradictory counter-evidence. | No. |

### Phase A: deterministic evidence checks

These checks have no LLM dependency.

1. **Shape and verdict checks**
   - Require `counter_evidence` for a Con win.
   - Reject unknown enumerations, blank fields, duplicate anchors, or a
     counter-evidence object on a Pro win.
   - Require at least two normalized code anchors in addition to the two named
     proof anchors, preserving the existing minimum-evidence policy.

2. **Exact-anchor checks**
   - Locate each named anchor exactly in the candidate code.
   - Reject anchors found only in comments or strings when code syntax can
     distinguish them.
   - Persist byte/line spans and a snippet hash in the receipt.
   - When parsing used a recovered candidate, verify these spans against the
     original snippet before emitting the receipt.

3. **Value-link checks**
   - Parse identifier tokens from `guarded_value` and `operation_value`.
   - For `guarded_value_equals_operation_value`, require the same normalized
     identifier at the guard and protected operation.
   - For `guarded_value_bounds_offset_plus_width`, require all declared terms in
     the guard and operation and a recognized sufficient comparison.
   - Do not accept semantic equivalence inferred from names such as `len` and
     `payload_len`; that requires an explicit supported relation or Phase B.

4. **Control-flow checks**
   - Recognize only the four proof patterns in the parser decision above.
   - A guard after the operation, in a sibling branch, another unrelated
   function, or a path that continues after failed validation is `refuted`.
   - A relationship that cannot be established with the available parser is
     `inconclusive`, not accepted.

5. **Predicate-precondition checks**
   - Require a versioned, seed-level `defense_obligation` / vulnerability
     subtype that maps to an explicit precondition template. This field is the
     authority for acceptance; predicate text is retained as human-readable
     context only.
   - Reuse `reflector_schemas.py` taxonomy buckets only for routing and metrics.
     A bucket such as `memory_safety` is too broad to select a proof rule.
   - The established invariant must negate that precondition at the protected
     operation. Examples:

| Category | Exploit precondition | Required defense relationship |
| --- | --- | --- |
| OOB read/write | `offset + width > available_length` | An earlier check proves `offset + width <= available_length`. |
| invalid shift | count is negative or not less than width | An earlier check bounds the exact shift count. |
| null dereference | pointer is null at dereference | A non-null branch dominates the exact dereference. |
| hostname identity spoofing | untrusted resolved identity is accepted | An equality mismatch rejects before acceptance/use. |
| race | shared state accessed without required synchronization | The same lock protects acquisition through access. |

6. **Counterfactual coherence**
   - Require a nonempty, predicate-specific statement naming the asserted guard
     and operation.
   - The deterministic checker need only verify those anchor/value references;
     it must not treat prose alone as proof.

The first failed check must be recorded by a stable machine reason, for example
`counter_evidence_guard_not_found`, `counter_evidence_unrelated_value`,
`counter_evidence_guard_after_operation`, or
`counter_evidence_unsupported_pattern`.

### Phase B: dedicated defense auditor

Phase B is used only in shadow mode when Phase A validates anchors and basic
structural integrity but cannot establish a semantic relation such as an alias,
conversion, or interprocedural forwarding. It must use a separate schema and
prompt from the existing Predictive Verifier.

Input is limited to:

- code snippet;
- predicate and its explicit exploit precondition;
- structured `counter_evidence`;
- Phase A receipt and unresolved check names.

Output schema:

```json
{
  "outcome": "defense_confirmed",
  "unresolved_relation": "payload_len is the exact input to copy_len after normalization",
  "reasoning": "...",
  "contradicting_anchor": null,
  "logic_error": null
}
```

Allowed `outcome` values are `defense_confirmed`, `defense_refuted`, and
`inconclusive`. It must never use `passes_audit`, which remains reserved for
the exploit verifier.

An auditor result is eligible for measurement only if its structured response
parses and all Phase A exact-anchor checks passed. `defense_refuted` produces a
rejection; parse failure, provider failure, or `inconclusive` produces an
inconclusive Con result. `defense_confirmed` is recorded in the receipt but
does not authorize acceptance in V1. No repair/default value can be reported as
a confirmed defense.

## Acceptance Decision

The judge decision is deliberately simple:

```text
if winner == pro_debater:
    require existing exploit verifier: passes_audit and no logic error
elif winner == con_debater:
    receipt = validate_counter_evidence(...)
    accept only receipt.status == deterministically_confirmed
else:
    reject invalid winner
```

`inconclusive` must retain the retry/refinement behavior rather than export a
safe sample. This maintains the distinction between a claim that is safe and a
claim the system could not substantiate.

## Artifact and B-Gate Contract

### Exported row

For a validated Con win, export the full receipt under
`output.counter_evidence_validation`. Preserve the existing verifier status but
make its intentional absence explicit:

```json
{
  "verifier_status": {
    "called": false,
    "skip_reason": "validated_con_counter_evidence"
  },
  "verifier_report": "not_applicable",
  "counter_evidence_validation": {
    "status": "deterministically_confirmed",
    "validator_version": "counter_evidence_v1"
  },
  "acceptance_basis": "validated_con_counter_evidence"
}
```

`not_applicable` remains backward compatible but is not itself evidence of a
valid Con win. The new `acceptance_basis` is mandatory for every accepted row:

- `pro_exploit_verifier_confirmed`
- `validated_con_counter_evidence`
- a documented legacy value for pre-v1 artifacts only

### Attempts and metrics

Attempt records must include the receipt, rejection reason, validator version,
and whether Phase B ran. The B-gate must separately report:

- validated Con acceptance count/rate;
- deterministic versus defense-auditor confirmed rate;
- Con refuted rate;
- Con inconclusive and invalid-contract rate;
- verifier skipped intentionally for validated Con wins;
- verifier missing/parse-failed unexpectedly for Pro wins.

Do not count intentional Con skips as the existing generic
`judge_accept_but_verifier_missing_or_parse_fail` disagreement. Historical
rows remain readable; their provenance is reported as legacy/unknown rather
than backfilled as validated.

## Implementation Slices

### Slice 1: pure deterministic contract

- Add Pydantic models for `CounterEvidence` and `CounterEvidenceReceipt`.
- Add a pure `validate_counter_evidence(code, predicate, evidence)` helper.
- Extend Graphify with a proof-oriented extraction API that retains guard and
  operation AST nodes, original-code spans, condition polarity, operands, and
  proven relation; keep the current FlowSignature API unchanged for diagnostic
  compatibility.
- Implement shape, exact-anchor, and the four supported proof patterns only.
- Keep the live decision path unchanged behind a feature flag.
- Add unit tests only; no live baseline rerun.

### Slice 2: judge contract and Con routing

- Add Con-specific prompt/schema requirements.
- Replace the current textual Con gate with the receipt-based validator.
- Route only validated Con wins around the exploit verifier.
- Emit explicit acceptance provenance and checkpoint data.

### Slice 3: B-gate and reporting

- Add v1 provenance validation and separate Con metrics.
- Preserve legacy `not_applicable` compatibility without classifying it as a
  validated defense.
- Add corpus fixtures for legacy, Pro, deterministic Con, and inconclusive Con
  rows.

### Slice 4: defense auditor

- Add a separate prompt/schema/client only for Phase A semantic gaps.
- Run it in shadow-only measurement mode.
- Report agreement, refutation, and inconclusive rates by vulnerability subtype.
- Do not add an accepting mode for `defense_auditor_confirmed` in V1; a future
  specification may promote it only after benchmark review.

## Feature Flag and Rollout

Introduce `counter_evidence_validation_mode` with these modes:

| Mode | Behavior |
| --- | --- |
| `off` | Current behavior; used only for baseline comparison. |
| `shadow` | Produce receipts and telemetry but retain current routing. |
| `enforce_deterministic` | Permit Con bypass only for deterministic confirmations. |

Rollout starts in `shadow`, using the cited safe seeds plus a broader,
pre-registered corpus. Report both old and new outcomes. Do not claim that a
single successful rerun proves the generalized policy. Promotion requires
regression tests, artifact compatibility tests, and a measured false-accept /
false-reject review. The defense auditor may run alongside these modes, but its
outcome is telemetry only in V1.

## Regression and Acceptance Tests

The implementation is not complete until these tests exist.

1. **Valid upper-bound rejection**: the exact checked value reaches the shift;
   guard dominates shift; receipt is deterministic; exploit verifier is not
   called.
2. **Irrelevant guard rejection**: a valid guard protects a different value or
   operation; result is `refuted` or `inconclusive`, never accepted.
3. **Late guard rejection**: operation precedes guard; result is `refuted`.
4. **Branch bypass rejection**: guard failure path still reaches operation;
   result is `refuted`.
5. **Hostname equality defense**: mismatch rejects before use of the resolved
   identity; receipt records the identity relation.
6. **Con contract failure**: missing or non-verbatim proof anchor rejects with a
   stable reason.
7. **Pro invariance**: Pro still calls the existing verifier and rejects on
   `passes_audit=False` or a nonempty logic error.
8. **No polarity shortcut**: a Con result cannot pass merely because the exploit
   verifier returns `passes_audit=False`.
9. **Export provenance**: validated Con exports include receipt and intentional
   skip reason; B-gate does not count it as an unexpected missing verifier.
10. **Legacy compatibility**: historical `not_applicable` rows remain readable
    but are marked legacy/unknown, not validated Con evidence.
11. **Checkpoint resume**: resume after Con validation retains the receipt and
    does not make a network verifier call.
12. **Schema repair provenance**: repaired/defaulted counter-evidence can never
    be presented as deterministic confirmation without revalidation of the
    final structured value.
13. **Rejecting bound check**: `if (len > capacity) return;` followed by a copy
    using `len` is confirmed only when the reject path cannot reach the copy.
14. **Inverted/late/else guard rejection**: inverted condition, a guard after
    the operation, and an else-path operation all fail rather than inheriting a
    sanitizer label.
15. **Arithmetic and transformed-value boundary**: `offset + width`, aliases,
    and transformed lengths are inconclusive unless a specifically supported
    proof pattern proves them.
16. **Original-span fidelity**: a proof recovered from a wrapped or
    semicolon-repaired candidate exports spans and anchors verified against the
    original snippet.
17. **Unsupported syntax**: partial or unparseable code is inconclusive and
    cannot become a deterministic Con acceptance.

## Alternatives Considered

### Invert `passes_audit` for Con wins

Rejected. It reuses an attack-shaped contract for a defense claim and leaves
`logic_error` semantically ambiguous. It masks the mismatch rather than
creating an evaluable defense proof.

### Skip the verifier for every Con win after the current textual gate

Rejected. The current gate is not a mechanism-blocking proof and would permit
unrelated or decorative checks to validate a safe label.

### Run both the exploit verifier and defense validator for every Con win

Deferred. It may become useful for high-risk modes, but it adds latency and
reintroduces ambiguous policy unless both contracts are independently reported.
V1 prioritizes a clear, narrow defense contract.

### Whole-program formal verification

Deferred. It is outside the latency and operational scope of the current
harness. The v1 closed pattern set provides measurable value while failing
closed for unsupported cases.

## Measurement Before Further Expansion

No global `inconclusive`-rate threshold is chosen in V1. Inconclusive outcomes
are safely non-accepting, and a superficially low rate could be achieved by
over-broad recognition rules that raise false accepts.

The shadow rollout must first measure `inconclusive` results by defense kind,
seed-level vulnerability subtype, code language, parser/recovery mode, and
machine reason. Only after this baseline exists may a later specification set a
coverage SLO or add proof patterns. Every new pattern requires both positive
fixtures and negative fixtures demonstrating unrelated guards, late guards,
branch bypass, and operand mismatch.

The remaining implementation choice is where the versioned
`defense_obligation` is stored in the seed contract. It must be supplied by
seed metadata or an explicitly versioned compatibility adapter, never inferred
from LLM output at acceptance time.

## Completion Criteria

This specification is implemented only when a Con acceptance has a durable,
versioned receipt that answers: which guard, which protected operation, which
value/state relationship, which precondition, which validator method, and why
the result was accepted rather than merely plausible.
