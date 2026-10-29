# BARRED: Evidence-Gated Security Fix Review

> **Track:** Push the Frontier  
> **Model:** Meta Muse-Glimmer-30B (`trymirai/Muse-Glimmer-30B-M`)  
> **Architecture:** Open-weight 30B multimodal dense transformer with Llama BPE tokenizer, optimized for autonomous agentic code workflows  
> **Core Innovation:** Transforming probabilistic AI security opinions into deterministic, machine-verifiable evidence decisions  

---

## The Problem
Every AI coding assistant today suffers from a fatal flaw: **it produces persuasive, authoritative-sounding explanations whether it is right or wrong.**

When reviewing a security fix, an LLM might declare code "Safe" because the developer added a superficial check or an irrelevant comment. To protect themselves, platforms slap broad legal disclaimers on coding agents (*"Verify all actions taken by the agent"*).

**BARRED replaces disclaimers with deterministic proof.**

Instead of letting an LLM generate ungrounded prose, BARRED pairs **Meta's Muse-Glimmer-30B** with **deterministic AST evidence gates**. The model is constrained to select machine-extracted candidates ($C_1 \dots C_n$), while the deterministic engine mathematically verifies control-flow dominance and value relations.

The result is a clean tri-state security review:
1. **`PASS`**: Machine-verified invariant proof attached (guard dominates sink on all paths).
2. **`BLOCKED`**: Plausible model hallucination caught and rejected by AST gate.
3. **`UNRESOLVED`**: Explicit epistemic refusal when outside the verified proof domain (no fake safety claims).

---

## Quickstart & Evaluation Modes

BARRED offers two ways to evaluate the system:

### Option A: 30-Second Instant Visual Demo (Offline Replay)
Inspect the three canonical outcomes without needing a 20GB+ GPU running:
```bash
uv run python -m hackathon.cli demo --offline
```

---

### Option B: Full Live Multi-Agent Pipeline (Real Meta Muse-Glimmer-30B)

This runs the complete end-to-end multi-agent debate and deterministic evidence gating pipeline.

#### Terminal 1 — Download & Launch Mirai Model:
```bash
brew install mirai
mirai --model trymirai/Muse-Glimmer-30B-M
```

#### Terminal 2 — Start Uzu OpenAI-Compatible Proxy (Python 3.12):
```bash
# If .venv-uzu is not already initialized:
# uv venv .venv-uzu --python 3.12 && uv pip install --python .venv-uzu/bin/python uzu
MODEL=trymirai/Muse-Glimmer-30B-M ./scripts/start_uzu_proxy.sh
```

#### Terminal 3 — Launch the Multi-Agent Debate Stack:
Spins up the Pro debater, Con debater, Verifier, and Judge microservices:
```bash
./scenarios/debate/start_all_muse_stack.sh
```

#### Terminal 4 — Execute the Evidence-Gated Batch Review:
```bash
uv run python scenarios/debate/run_batch.py \
  --seeds scenarios/debate/cve_seeds_smoke_2gate.jsonl \
  --run-id m9bol-gate-smoke-v10 \
  --output artifacts/factorial/corpus_gateol_smoke_v10.jsonl \
  --gepa-dir artifacts/gepa_m9dl_pareto_smoke \
  --attempts-out artifacts/attempts/gateol-smoke-v10.jsonl \
  --manifest-out artifacts/runs/gateol-smoke-v10/batch_manifest.json \
  --seed 42 --mode record --slice-judge --reflector --reflector-in-process \
  --reflector-mode symmetric --escalate-pareto --max-concurrency 1 \
  --counter-evidence-validation-mode enforce_deterministic --halt-on-con-win
```

#### Inspect Live Run Results via CLI:
Render the human-readable tri-state decision cards directly from the live attempt logs:
```bash
uv run python -m hackathon.cli inspect artifacts/attempts/gateol-smoke-v10.jsonl
```

---

## Detailed Explanation of Pipeline Flags

| Flag | Purpose & Impact |
| :--- | :--- |
| `--seeds cve_seeds_smoke_2gate.jsonl` | Loads the two test cases: Seed 42 (Supported memcpy guard) and Seed 43 (Unsupported wrapper). |
| `--counter-evidence-validation-mode enforce_deterministic` | **The Core Innovation**: Engages the AST evidence gate. Blocks any model claim lacking an invariant proof. |
| `--halt-on-con-win` | **Efficiency & Proof**: Halts execution the instant deterministic proof is confirmed (Seed 42 halts on Round 0). |
| `--slice-judge` | Slices code context specifically for judge adjudication, stripping misleading context. |
| `--reflector --reflector-mode symmetric --escalate-pareto` | **Multi-Turn Epistemic Escalation**: When the gate catches a hallucination in Round 0 (Seed 43), reflection forces the model to re-evaluate and admit `unresolved` in Round 1. |
| `--mode record` | Records bit-for-bit LLM prompt/response cassettes and attempt telemetry for auditability. |

---

## The Three Canonical Cases

| Case | Scenario | Model Action | Deterministic Gate Action | Final Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Case 1 (Seed 42)** | `safe_copy`: upper-bound guard (`len >= cap`) protecting `memcpy(dst, src, len)` | Selects Candidate `C1` | **Confirmed**: 7/7 AST checks verify guard dominates sink | **`PASS`** |
| **Case 2 (Seed 43 R1)** | `gdImageJpegPtr`: zero-width test on 3rd-party wrapper | Model refrains (`candidate_id: null`) | **Epistemic Bound**: AST domain refuses to certify unknown sinks | **`UNRESOLVED`** |
| **Case 3 (Seed 43 R0)** | Superficial/ungrounded check before memory operation | Model attempts hallucination (`C1`) | **Blocked**: Gate rejects ungrounded candidate | **`BLOCKED`** |

---

## Verification & Evidence Pack

- **Live Audit Trace**: Generated during real execution in [`hackathon/evidence_pack/audit_m9bol_gate_smoke_v10.json`](evidence_pack/audit_m9bol_gate_smoke_v10.json).
- **TDD Test Suite**: 34 focused unit and replay tests covering failure modes and receipt contracts:
  ```bash
  uv run pytest tests/test_con_receipt_e2e.py tests/test_con_receipt_extractor.py tests/test_counter_evidence_fixtures.py tests/test_failure_modes_replay.py
  ```

---

## 3-Minute Video Beat Sheet

- **0:00 - 0:30 (The Hook):** Show the IDE security disclaimer: *"AI coding agents have limitations; verify all actions."* Explain that developers cannot trust probabilistic LLM text for memory safety.
- **0:30 - 1:15 (The Supported Case):** Run `run_batch.py` (or `hackathon.cli inspect`). Show Muse-Glimmer-30B selecting candidate `C1` and the AST gate validating control-flow dominance (`PASS`).
- **1:15 - 2:00 (The Contrast Case):** Show Seed 43 Round 0. The model tries to claim `C1` on code with no bounding guard. Show the gate blocking it cold (`BLOCKED`).
- **2:00 - 2:30 (The Honest Boundary):** Show Seed 43 Round 1. Under reflection, Muse Glimmer concedes and returns `UNRESOLVED`. Explain why an AI that knows when it lacks proof is the holy grail.
- **2:30 - 3:00 (The Conclusion):** Summarize how pairing Meta models with deterministic evidence gates turns AI coding assistants into verified security reviewers.
