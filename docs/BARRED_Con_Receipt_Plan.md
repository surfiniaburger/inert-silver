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

## 2.5 Validation-mode behavior (off / shadow / enforce_deterministic)

The current `_process_verifier_audit` skips `validate_counter_evidence` when `counter_evidence_validation_mode == "off"`. The discriminated-union change (Step 1) makes `counter_evidence` required for Con, but the validator call is still mode-gated. Define explicit behavior:

- **`off`:** Con receipts are not validated. A Con verdict with a structurally complete `counter_evidence` is accepted as `con_win` without deterministic confirmation. This mode is for development/exploration only and must not be used in scored runs. Receipts produced in off mode are labeled `con_win_unvalidated`.
- **`shadow`:** `validate_counter_evidence` runs and its result is recorded, but does not gate acceptance. Con wins are accepted regardless of receipt status. Used for calibration and funnel measurement.
- **`enforce_deterministic`:** `validate_counter_evidence` runs and gates acceptance. Con is accepted only if `status == deterministically_confirmed`. This is the scored mode.

The `con_win` receipt requirement (Step 1) applies in all modes: off mode permits `con_win` without a confirmed receipt, but labels it unvalidated. Shadow and enforce modes require the receipt attempt; only enforce mode requires confirmation.

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

**Protocol invariant (R1):** The discriminated union must be enforced by the inference interface and repair loop, not just by schema. A schema that permits `null` in every case would still allow the same failure. Use a discriminated union if the structured-output backend supports it reliably; otherwise use separate output schemas or an explicit post-generation repair step. In either case, retain runtime validation because schema validity is not proof validity.

**No-valid-receipt output:** The plan also requires the extractor or judge to return "no valid receipt" or abstain. That state has no valid output representation today: a Con verdict with null evidence violates Step 1, while a Pro verdict changes the adjudication. Add an explicit third adjudication state:

```text
outcome: pro_win | con_win | unresolved
```

- `con_win` requires complete counter-evidence and a confirmed receipt.
- `pro_win` keeps the existing exploit-verification route.
- `unresolved` may retain the debate scores/reasoning but cannot export a training sample, trigger a Con halt, or be silently recast as Pro.

**Unresolved branch handling (CodeRabbit finding):** Downstream logic currently branches on only two winners (Pro/Con). An unresolved result must enter an explicit branch, not fall through to Pro mechanism checks or become Pro. Specify handling at each point:
- **Gates (`_collect_soft_checks`):** unresolved does not receive Pro mechanism checks (mechanism_grounding, mechanism_evidence, mechanism_template) and does not produce a `con_win_counter_evidence` gate. It records `counter_evidence: null` and `outcome: unresolved`.
- **Verifier flow (`_process_verifier_audit`):** unresolved skips the verifier audit (no verifier call). Returns `is_valid=False`, `verifier_meta["error"]="unresolved_no_valid_receipt"`.
- **Export/acceptance (`_export_accepted_sample`):** unresolved is **not** exported as a training sample. No consensus verdict is produced.
- **Checkpoint phase:** written as `"phase": "unresolved"` with `last_judge_reason="unresolved_no_valid_receipt"`.
- **Failure reporting:** counted as a distinct outcome in the funnel (not a rejection, not an acceptance).
- **Halt policy:** unresolved does **not** trigger `--halt-on-con-win` (only confirmed Con wins halt).

A nullable `winner` can work, but an explicit `outcome` field is clearer operationally. Downstream logic must branch on `outcome`, not `winner`.

**Files:** `debate_judge_common.py` (DebateEval schema), `adk_debate_judge.py` (judge prompt / schema).

**Checkpoint compatibility (CodeRabbit finding):** `_get_judge_eval` rehydrates `DebateEval` from `active_checkpoint["judge_eval"]`. If the implementation replaces `winner` with `outcome` or changes required receipt fields, existing checkpoints may fail validation. Define a checkpoint version (`schema_version`), migration, or explicit invalidation rule:
- Bump `schema_version` when the DebateEval schema changes.
- On resume, if `checkpoint.schema_version < current`, either migrate (map `winner` → `outcome`) or invalidate and re-run from R0.
- Log the invalidation reason; do not silently skip.

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

The allowed `defense_kind` values are **obligation-specific**, not universal:

| Obligation | Allowed defense_kind |
|---|---|
| `upper_bound` | `upper_bound_reject` or `range_guarded_operation` (two forms) |
| `null_dereference` | `null_check` (one form) |
| `identity_mismatch` | `equality_reject` (one form) |

For each, list the compatible `enforcement`/`value_relation` pairings explicitly. Do not make the model infer this from a generic schema.

**Contract mismatch note:** `CounterEvidence` currently admits more values than V1 can prove (e.g., `lower_bound_reject`, `lock_before_shared_access`, `validated_value_forwarded`, `lock_held_at_operation`). Either declare those intentionally unsupported in V1 or implement them; do not expose them as apparently valid receipt options to the judge.

**Files:** `adk_debate_judge.py` (judge prompt construction), `data_generator.py` (if evidence packet includes obligation).

### Step 3 — Create one deterministic receipt extractor before the judge

**Canonical code block (CodeRabbit finding):** The judge may receive `judge_code_block` from `slice_code_for_judge`, while validation receives `current_sample_block`. The extractor must define one canonical code block shared by extractor, judge, and validator, or preserve a verified mapping between the two. Candidate source spans must resolve consistently in both contexts. Recommended: the extractor runs on `current_sample_block` (the full seed code) and produces spans as `(start_offset, end_offset)` into that block; the judge receives the same block plus the candidate list; the validator re-resolves spans against `current_sample_block`.

The code can identify candidate `if` guards, operations, value uses, branch containment, and return/goto behavior. Let that component emit a small set of valid receipt candidates. The judge should select among candidates — or return "no valid receipt" — rather than inventing anchors, values, and labels from scratch.

That turns the task from:
> generate a proof object perfectly

into:
> choose candidate C2, or state that none proves the defense

It is much better matched to a small model and preserves the validator's authority.

**Candidate selection contract (CodeRabbit finding):** Each extractor candidate receives an immutable ID (e.g., `C1`, `C2`). The judge's selection must reference that ID. The validator then checks that the returned `counter_evidence` exactly matches the extractor output for the selected candidate (same anchors, same values, same structural relation) before proceeding to structural proof. If the returned receipt does not match any candidate, it is rejected as `unsupported_candidate`. This prevents the judge from inventing anchors or values while still allowing it to abstain ("no valid receipt").

**Extractor must not manufacture proof (R2):** The extractor should discover plausible structural relationships, not label every syntactic guard as a valid defense. A guard may check `len`, while the dangerous operation uses a transformed value, a different variable, or a value that can change between the check and use. A matching string or nearby `if` is not sufficient.

The extractor produces candidate evidence with source spans, variable identities, branch relationships, and explicit unsupported conditions. Then:
1. The judge selects a candidate or abstains.
2. The validator checks the required structural relation.
3. The final outcome records whether the receipt was confirmed, rejected, or unsupported.

If the V1 validator only supports specific AST/CFG patterns, anything outside those patterns should remain **unresolved** — not silently classified as safe.

**Files:** new module (e.g., `con_receipt_extractor.py`) or extension of `adk_debate_verifier.py`. Called before `_get_judge_eval`.

### Step 4 — Keep the current validator strict, but instrument its reasons

**Complete V1 compatibility matrix (CodeRabbit finding):** Define and enforce exact supported `enforcement`/`value_relation` tuples for each `defense_kind`. Replace the vague "compatible relation" allowance with precise tuples:

| defense_kind | enforcement | value_relation |
|---|---|---|
| `upper_bound_reject` | `reject_before_operation` | `guarded_value_equals_operation_value` |
| `range_guarded_operation` | `operation_inside_safe_branch` | `guarded_value_equals_operation_value` |
| `null_check` | `reject_before_operation` | `guarded_value_equals_operation_value` |
| `equality_reject` | `reject_before_operation` | `guarded_value_equals_operation_value` |

Reject every unsupported pairing (including `guarded_value_bounds_offset_plus_width` where unsupported) before returning `deterministically_confirmed`. Add positive and negative fixtures covering the full matrix.

**Note:** `CounterEvidence` currently admits more `defense_kind` values than V1 can prove (e.g., `lower_bound_reject`, `lock_before_shared_access`, `validated_value_forwarded`, `lock_held_at_operation`). These should be declared intentionally unsupported in V1 or implemented; do not expose them as apparently valid receipt options to the judge.

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

**Compatibility checking:** `extract_counter_evidence_proof` checks `enforcement` for each structural branch, but the `null_check` branch does not validate `value_relation`. A receipt can therefore use an unrelated non-empty relation (e.g., `guarded_value_bounds_offset_plus_width`) and still receive `deterministically_confirmed` if the null check dominates the operation. Add explicit per-defense_kind compatibility checks:
- `range_guarded_operation`: requires `enforcement == operation_inside_safe_branch` AND `value_relation == guarded_value_equals_operation_value`.
- `null_check`: requires `enforcement == reject_before_operation` (or `operation_inside_safe_branch`) AND `value_relation == guarded_value_equals_operation_value` (or compatible relation).
- Reject schema-valid but incompatible pairings before returning `deterministically_confirmed`.

Invalid literals are already rejected by Pydantic `Literal` fields on the ordinary judge-output path, but negative fixtures should cover both invalid literals and incompatible pairings to protect direct validator callers.

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
2. On a small smoke run (10 seeds, Qwen or Gemma), track two linked funnels separately:
   - **Schema/protocol funnel:** Con-intended → initial schema rejection → repair attempted → repair success/exhausted. (A failed conditional-schema repair may never reach `validate_counter_evidence`, so it cannot be counted as `counter_evidence_missing` / `malformed`.)
   - **Semantic-validation funnel:** parsed Con receipt → obligation match → anchors found → value relation → control flow → confirmed/refuted/inconclusive.
   This distinguishes "Qwen omitted the object" from "the object arrived but fails the deterministic proof." (Steps 1–2 working.)
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
4. **Add candidate extraction.** Start with `upper_bound` only (the only family with V1 support). Mark `null_dereference` and `identity_mismatch` as **deferred** until their candidates and fixtures exist. Do not expose unsupported defense kinds to the judge. Produce candidates with source spans, variable identities, branch relationships, and explicit unsupported conditions (R2).
5. **Replay the same cases.** Compare receipt presence, schema validity, deterministic confirmation, false positives, false negatives, abstentions, and cost against the frozen baseline.
6. **Only then test escalation.** Evaluate halt-on-valid-receipt as a separate policy after the receipt pipeline demonstrably produces valid confirmations.

## 9. Hackathon submission framing

This gives a sharper, feasible technical story:

> BARRED exposed a failure at the boundary between adversarial reasoning and deterministic verification: a debate can produce a Con win, yet the judge fails to translate the counterargument into a valid machine-checkable receipt. We are making the contract explicit, generating structural evidence candidates, and measuring whether valid counterevidence can be admitted without weakening the verifier.

The model-dependent part can be evaluated later with an available model, provided results are clearly labeled as measured vs. planned. The schema, candidate extractor, fixture suite, and replay harness can all be built locally while Gemini credits are unavailable.

## 10. Verdict

Approve the plan. Start with the positive/negative validator fixtures and obligation-aware receipt generation. Don't change the halt policy or relax the verifier until those pieces are working. The strongest result is not simply getting Option B to fire — it's showing that the system can admit valid counterevidence and that doing so improves adjudication rather than merely changing which side wins.
