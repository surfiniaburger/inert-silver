# BARRED — Con Receipt Quality Plan

**Status:** Plan (not yet implemented). Derived from the Track 2 Replicate 1 Con-path audit and the review feedback.
**Problem:** The Con path never produces a `deterministically_confirmed` receipt (0 of 54 Con wins across all arms). The halt-on-valid-receipt policy is therefore a no-op, and the halt-on-any-Con-win policy introduces false negatives on confirmed-vulnerable seeds.

---

## 1. Correct attribution

The **judge**, not the Con debater, produces `DebateEval.counter_evidence`. Con supplies free-form argument text; the judge is asked to turn that into the machine-checkable receipt. The failure is a **judge-to-contract translation failure**, not a Con-debater failure.

The Qwen sampled data supports the broader finding: most receipts fail as `counter_evidence_missing` (null), not as nearly-valid objects with one wrong enum. One sampled case fails because the seed has no valid `defense_obligation`. That distinction matters for the fix.

## 2. The contract (intentionally narrow)

Con verdict → counter_evidence object present and complete → defense_kind fits the seed's defense_obligation → quoted guard and operation occur exactly in the code → same guarded value appears in guard and operation → AST/CFG-shaped structural relation proves either:
- a rejecting guard dominates the operation, or
- the operation lies in a safe branch
→ `deterministically_confirmed`

Three contract families:

| Obligation | Allowed defense |
|---|---|
| `upper_bound` | `upper_bound_reject` or `range_guarded_operation` |
| `null_dereference` | `null_check` |
| `identity_mismatch` | `equality_reject` |

Everything else is either unprovable under V1 or must not be treated as a valid defense receipt.

## 3. The design mismatch

The judge prompt says only "use a closed-vocabulary defense kind/enforcement/value relation." It does not give:
- the actual allowed literals,
- a concrete JSON template, or
- the seed's specific `defense_obligation`.

That obligation is passed to the validator later, but not to the model that must satisfy it. The judge is effectively asked to hit a hidden target.

## 4. Fix order (5 steps)

### Step 1 — Make receipt production structurally mandatory for Con outcomes

`counter_evidence` is `Optional` in `DebateEval`, so the model can emit a schema-valid Con verdict with `null` evidence; the validator rejects it afterwards. Model the result as a discriminated union:

- Pro verdict → `counter_evidence` must be absent/null
- Con verdict → `counter_evidence` is required and complete

This moves a large class of failures (`counter_evidence_missing`) into structured-output repair, where the model gets a precise missing-field error before the verdict is accepted.

**Files:** `debate_judge_common.py` (DebateEval schema), `adk_debate_judge.py` (judge prompt / schema).

### Step 2 — Put the exact obligation and contract template in the judge's context

For an `upper_bound` seed, tell the judge explicitly:

```json
"counter_evidence": {
  "defense_kind": "upper_bound_reject",
  "guard_anchor": "<exact code substring>",
  "guarded_value": "len",
  "protected_operation_anchor": "<exact code substring>",
  "operation_value": "len",
  "enforcement": "reject_before_operation",
  "value_relation": "guarded_value_equals_operation_value",
  "invariant": "...",
  "predicate_precondition": "...",
  "counterfactual": "..."
}
```

Then list the two allowed `defense_kind` values and their compatible `enforcement`/`value_relation`. Do not make the model infer this from a generic schema.

**Files:** `adk_debate_judge.py` (judge prompt construction), `data_generator.py` (if evidence packet includes obligation).

### Step 3 — Create one deterministic receipt extractor before the judge

The code can identify candidate `if` guards, operations, value uses, branch containment, and return/goto behavior. Let that component emit a small set of valid receipt candidates. The judge should select among candidates — or return "no valid receipt" — rather than inventing anchors, values, and labels from scratch.

That turns the task from:
> generate a proof object perfectly

into:
> choose candidate C2, or state that none proves the defense

It is much better matched to a small model and preserves the validator's authority.

**Files:** new module (e.g., `con_receipt_extractor.py`) or extension of `adk_debate_verifier.py`. Called before `_get_judge_eval`.

### Step 4 — Keep the current validator strict, but instrument its reasons

Do not weaken `deterministically_confirmed` merely to make Option B fire. Instead report the failure funnel:

```
Con wins
  → counter_evidence absent
  → malformed receipt
  → obligation mismatch
  → anchor not found
  → unrelated value
  → unsupported control-flow pattern
  → deterministically confirmed
```

At present, "invalid contract" conflates several very different remediation paths. The initial four-arm sample is dominated by absence; that calls for conditional schema/template work (Steps 1–2). Later failures may reveal missing validator coverage or genuinely unsupported defenses.

**Files:** `adk_debate_judge.py` (validator + logging), `build_track2_replicate1_ledger.py` (funnel reporting).

### Step 5 — Calibrate the validator with known-positive snippets before rerunning arms

A zero-confirmation rate can mean broken generation, but it can also mean the corpus contains no defenses that V1 can prove. Build a small fixture set with one positive example for each supported pattern, then verify the validator returns `deterministically_confirmed` for each. That separates:

- "the contract cannot recognize its own intended cases,"
- from "the model never supplies a contract-compliant proof,"
- from "the benchmark does not contain provable Con defenses."

Only after that should "halt on valid receipt" become a measured policy. It should remain gated by the deterministic receipt, not by a raw Con win or the permissive text-based `con_win_counter_evidence` gate. That text gate is a useful triage signal, but it is not a proof.

**Files:** `tests/test_adk_debate_judge_refactor.py` (new fixture tests), `scenarios/debate/test_predicate_quality.py`.

## 5. What this does NOT change

- The halt-on-con-win flag (`--halt-on-con-win`) stays as implemented. It halts on any Con win, but the *policy decision* of when to halt should be gated on `deterministically_confirmed` receipts, not raw Con wins. Until Step 5 calibration, treat halt-on-con-win as an engineering mechanism, not a measured policy.
- The Track 2 experiment spec (four-arm factorial) is unchanged. The Con receipt fix is a prerequisite for meaningful correctness analysis, not a replacement for the experiment.
- The Track 1 audit ledger is unchanged.

## 6. Success criteria

1. The validator's failure funnel shows at least one `deterministically_confirmed` receipt on a known-positive fixture (Step 5).
2. On a small smoke run (10 seeds, Qwen or Gemma), the funnel shows movement from `counter_evidence_missing` to `malformed` or `obligation mismatch` (Steps 1–2 working).
3. On a full run, at least one Con win produces a `deterministically_confirmed` receipt on a seed independently adjudicated as proved_safe.
4. The halt-on-valid-receipt policy then shows a measurable precision improvement without increasing false negatives on confirmed-vulnerable seeds.

---

## 7. Review refinements (adopted)

The following refinements were proposed during review and are adopted into this plan.

### R1. Treat the discriminated union as a protocol invariant

The rule is:
- Pro verdict → `counter_evidence` must be absent/null.
- Con verdict → `counter_evidence` is required and complete.

But structured-output repair only helps if the inference interface and repair loop actually enforce the conditional requirement. A schema that permits `null` in every case would still allow the same failure.

**Implementation:** Use a discriminated union if the structured-output backend supports it reliably. Otherwise, use separate output schemas or an explicit post-generation repair step. In either case, retain runtime validation because schema validity is not proof validity.

### R2. Don't let the extractor manufacture proof

The candidate extractor should discover plausible structural relationships, not label every syntactic guard as a valid defense.

For example, a guard may check `len`, while the dangerous operation uses a transformed value, a different variable, or a value that can change between the check and use. A matching string or nearby `if` statement is not sufficient.

**Implementation:** The extractor produces candidate evidence with source spans, variable identities, branch relationships, and explicit unsupported conditions. Then:
1. The judge selects a candidate or abstains.
2. The validator checks the required structural relation.
3. The final outcome records whether the receipt was confirmed, rejected, or unsupported.

If the V1 validator only supports specific AST/CFG patterns, anything outside those patterns should remain **unresolved** — not silently classified as safe.

### R3. Test the validator before changing the model

A zero-confirmation rate has at least three possible explanations:
- The judge doesn't generate the required receipt.
- The validator cannot recognize a valid defense it is supposed to support.
- The evaluated cases don't contain defenses that the current validator can prove.

**Implementation:** Add negative fixtures too — superficially similar guards that fail because they protect the wrong value, occur after the operation, or do not enforce the required condition. This distinguishes "the contract cannot recognize its own intended cases" from "the model never supplies a contract-compliant proof" from "the benchmark does not contain provable Con defenses."

### R4. Caution on explanatory fields

The fields `invariant`, `predicate_precondition`, and `counterfactual` may be useful explanatory evidence, but the validator must distinguish them from the actual proof obligations. A persuasive explanation cannot compensate for an absent or invalid structural relationship.

Similarly, `deterministically_confirmed` should mean that the specified defense obligation was established under the validator's supported semantics. It should not mean the entire program is safe.

## 8. Refined implementation order (per review)

1. **Freeze the current baseline.** Preserve the 54 Con-win receipt records, exact prompts, model identifiers, schemas, validator version, and rejection reasons.
2. **Build validator fixtures.** Include known-positive and known-negative cases for each supported defense family. Confirm that the validator recognizes the former and rejects the latter.
3. **Make receipt production obligation-aware.** Add the actual obligation, compatible enums, and complete template to the judge context; make Con receipts structurally mandatory (R1).
4. **Add candidate extraction.** Start with one defense family — probably `upper_bound` — rather than attempting general-purpose C control-flow proof in one iteration. Produce candidates with source spans, variable identities, branch relationships, and explicit unsupported conditions (R2).
5. **Replay the same cases.** Compare receipt presence, schema validity, deterministic confirmation, false positives, false negatives, abstentions, and cost against the frozen baseline.
6. **Only then test escalation.** Evaluate halt-on-valid-receipt as a separate policy after the receipt pipeline demonstrably produces valid confirmations.

## 9. Hackathon submission framing

This gives a sharper, feasible technical story:

> BARRED exposed a failure at the boundary between adversarial reasoning and deterministic verification: a debate can produce a Con win, yet the judge fails to translate the counterargument into a valid machine-checkable receipt. We are making the contract explicit, generating structural evidence candidates, and measuring whether valid counterevidence can be admitted without weakening the verifier.

The model-dependent part can be evaluated later with an available model, provided results are clearly labeled as measured vs. planned. The schema, candidate extractor, fixture suite, and replay harness can all be built locally while Gemini credits are unavailable.

## 10. Verdict

Approve the plan. Start with the positive/negative validator fixtures and obligation-aware receipt generation. Don't change the halt policy or relax the verifier until those pieces are working. The strongest result is not simply getting Option B to fire — it's showing that the system can admit valid counterevidence and that doing so improves adjudication rather than merely changing which side wins.
