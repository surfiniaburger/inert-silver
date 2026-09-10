# Spec: Evidence-Selected Allocation Size Graph Tranche

**Status:** Draft / requires human approval before implementation  
**Target Component:** `scenarios/debate/graph_extractor.py`  
**Primary Tests:** `tests/test_graph_extractor.py`  
**Evaluation Artifact:** `artifacts/metrics/graph_pre_filter_cv_report_next.json`  
**Related Spec:** `docs/SPEC_GRAPH_EXTRACTOR.md`

## Assumptions
1. The next graph-extractor tranche should optimize accepted-positive recall without weakening the current `FP=0` safety constraint.
2. The current 5-fold artifact is the baseline: `ROC-AUC=0.5571`, `PR-AUC=0.3357`, `TP=4`, `FP=0`, parser coverage `15.71%`.
3. The next tranche should be evidence-selected from current miss buckets, not broad taxonomy expansion.
4. Project-specific macros, wildcard allocator names, and domain-specific callees remain out of scope unless separately approved.
5. Implementation should remain deterministic and fail closed on unsupported or malformed syntax.

## Objective
Build a narrow graph-extractor extension for accepted-positive allocation-size vulnerabilities where the corpus shows an obvious standard allocation-size reachability relation:

- Integer arithmetic feeds an allocation size.
- The allocation or downstream memory operation is reached without a proven overflow/bounds guard.
- The extractor can produce positive evidence without relying on benchmark-specific names.
- The signal is the graph edge from size arithmetic to allocation argument, not the presence of an allocator keyword.

Success means lifting true positives from the current `TP=4` baseline while preserving `FP=0`.

## Evidence Baseline
Current 5-fold evaluation:

```text
total_samples = 140
positive_samples = 35
negative_samples = 105
parse_complete_count = 22
parse_failed_count = 118
parser_coverage = 0.1571
positive_evidence_count = 4
proof_state_counts = {
  "proven_unsafe": 4,
  "unsupported_or_unproven": 136
}
confusion_matrix = {
  "tn": 105,
  "fp": 0,
  "fn": 31,
  "tp": 4
}
```

Current accepted misses after near-duplicate collapse:

```text
accepted unsupported_syntax = 28
accepted missing_source = 3
accepted missing_sink = 0
```

Candidate allocation-size rows:

```text
HASH-313fcb9f42
array_size * data_size pb_realloc(ptr, array_size * data_size)

HASH-313fcb9f42
size_t data_size, size_t array_size pb_realloc(ptr, array_size * data_size) if (data_size > check_limit && array_size > check_limit)

HASH-401e5833cb
long nbItems nbItems * sizeof(RECTANGLE_16) malloc(allocSize)

HASH-401e5833cb
long allocSize = sizeof(REGION16_DATA) + (nbItems * sizeof(RECTANGLE_16)); dstRect->top = rect->top;
```

## Tech Stack
- Python project using `uv`.
- Parser stack: Python `ast` plus `tree-sitter-c`.
- Data model: `FlowGraphSnapshot` and `FlowSignature` from `scenarios/debate/graph_dataflow.py`.
- Evaluation: `scripts/evaluate_graph_pre_filter.py`.

## Commands
Focused graph tests:

```bash
uv run python -m pytest tests/test_graph_extractor.py tests/test_graph_dataflow_schema.py -q
```

Regression tests including graph bucket logic:

```bash
uv run python -m pytest tests/test_graph_extractor.py tests/test_graph_dataflow_schema.py tests/test_train_pre_filter.py -k 'graph' -q
```

5-fold graph evaluation:

```bash
uv run python -m scripts.evaluate_graph_pre_filter \
  --attempts-dir artifacts/attempts \
  --output-file artifacts/metrics/graph_pre_filter_cv_report_next.json \
  --bucket-examples-file artifacts/metrics/graph_pre_filter_bucket_examples_next.json \
  --bucket-example-limit 8 \
  --k-folds 5
```

## Project Structure
```text
scenarios/debate/graph_extractor.py
  Deterministic AST and Tree-sitter C extraction logic.

scenarios/debate/graph_dataflow.py
  FlowGraphSnapshot, FlowSignature, and reachability evaluation.

tests/test_graph_extractor.py
  Corpus fixtures and adversarial extractor regressions.

tests/test_graph_dataflow_schema.py
  Schema and evaluator invariants.

scripts/evaluate_graph_pre_filter.py
  5-fold graph pre-filter artifact generation.

artifacts/metrics/graph_pre_filter_cv_report_next.json
  Current metric baseline and regenerated evaluation output.
```

## Code Style
Prefer small predicates and proof-specific helpers over broad keyword rules:

```python
def _is_allocation_size_expression(node: Optional[tree_sitter.Node]) -> bool:
    if not node:
        return False
    return node.type == "binary_expression" and _contains_operator(node, {"*", "+"})


def _is_standard_allocation_call(func_name: str) -> bool:
    return func_name in {"malloc", "calloc", "realloc", "aligned_alloc"}
```

Conventions:
- Keep helper names explicit about proof semantics.
- Use exact allowlists for standard C allocation functions only.
- Do not add project-specific sink names, benchmark macros, or wildcard suffixes like `*_malloc`.
- Keep parse repair helpers narrow and quote-aware.
- Return no signature when source, sink, or operand identity cannot be proven.

## Testing Strategy
Use test-first implementation.

Required positive fixtures:
- Accepted `HASH-313fcb9f42` row for multiplication-fed `pb_realloc`.
- Accepted `HASH-401e5833cb` row for `allocSize` computed from `nbItems * sizeof(...)` and used by `malloc`.

Required adversarial fixtures:
- Rejected or synthetic checked multiplication where a guard dominates allocation.
- Constant-size allocation such as `malloc(64)` with no untrusted allocation-size source.
- `malloc(size)` where `size` was not assigned from arithmetic.
- Arithmetic expression mentioning allocation terms but not feeding an allocation argument.
- Comments or text containing `malloc`, `overflow`, or `memcpy` without a graph edge.
- Project-specific macro or unknown allocator remains unsupported unless explicitly approved.

Evaluation checks:
- Focused tests pass.
- 5-fold report regenerates.
- `FP=0` remains true.
- `TP` increases by at least one before accepting the tranche.

## Boundaries
- Always:
  - Preserve fail-closed behavior for unsupported syntax.
  - Preserve `FP=0` on the 5-fold graph report.
  - Back every positive-evidence rule with a corpus fixture.
  - Add adversarial fixtures for each new rule.
  - Require arithmetic-to-allocation operand identity before emitting positive evidence.
  - Use only exact standard C allocation callees: `malloc`, `calloc`, `realloc`, and `aligned_alloc`.
- Ask first:
  - Adding project-specific allocators, allocator wrappers, suffix patterns, or macros as sinks.
  - Changing `FlowGraphSnapshot` or `FlowSignature` schema.
  - Weakening Tree-sitter `root_node.has_error` rejection.
  - Adding dependencies.
- Never:
  - Treat security words like `overflow`, `malloc`, or `memcpy` as evidence by themselves.
  - Treat allocator-call presence as evidence without an arithmetic size-flow edge.
  - Count string literals as untrusted sources.
  - Generate positive evidence when operand identity is not traceable.
  - Convert rejected negatives into accepted graph evidence to chase metric lift.

## Success Criteria
- At least one selected accepted allocation-size row moves from `unsupported_syntax` or `missing_source` into `missing_sanitizer` / `proven_unsafe`.
- `TP >= 5` on the near-duplicate-collapsed 5-fold graph report.
- `FP = 0` remains unchanged.
- `ROC-AUC` and `PR-AUC` do not regress from `0.5571` and `0.3357`.
- Parser coverage increases or remains stable; no decrease below `15.71%`.
- Focused and graph-bucket tests pass with `uv`.

## Implementation Gate Result
Initial exact-standard-allocator implementation preserved safety but did not satisfy the tranche acceptance gate:

```text
ROC-AUC = 0.5571
PR-AUC = 0.3357
TP = 4
FP = 0
parser_coverage = 15.71%
```

Reason: the near-duplicate-collapsed accepted `HASH-401e5833cb` rows do not currently contain a clean standard allocation-size graph edge:

- One row contains malformed text with `malloc(allocSize)` but no sound `allocSize = ...` assignment.
- One row contains a sound `allocSize = ...` assignment but no standard allocator sink in the same parseable fragment.

Therefore this tranche is safe but not metric-lifting under the current evidence gate. It should not be treated as accepted unless future corpus rows include a complete standard allocation-size-to-allocator edge.

## Open Questions
1. Should allocation-size arithmetic produce a new source kind such as `derived_allocation_size`, or reuse `fragment_derived_value`?
2. Should guarded multiplication checks be recognized now, or should the first tranche only detect unguarded allocation-size flows and leave guarded cases fail-closed?
3. Should this tranche update `docs/SPEC_GRAPH_EXTRACTOR.md`, or remain as a separate evidence-selected addendum until the rule proves stable?

## Out Of Scope For Tranche 1
- `pb_realloc` and other project-specific allocator wrappers.
- Wildcard allocator suffix matching such as `*_malloc` or `*_realloc`.
- Macro expansion.
- Proving guarded arithmetic safe.
