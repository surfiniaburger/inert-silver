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

Instead of letting an LLM generate ungrounded prose, BARRED pairs **Meta's Muse-Glimmer-30B** with **deterministic AST evidence gates**. The model is constrained to select machine-extracted candidates ($C_1 \dots C_n$), while the deterministic engine mathematically verifies control flow dominance and value relations.

The result is a clean tri-state security review:
1. **`PASS`**: Machine-verified invariant proof attached (guard dominates sink on all paths).
2. **`BLOCKED`**: Plausible model hallucination caught and rejected by AST gate.
3. **`UNRESOLVED`**: Explicit epistemic refusal when outside the verified proof domain (no fake safety claims).

---

## 90-Second Quickstart (Judge Runbook)

### 1. Instant Canonical Demo (Offline / Audit Replay)
To see the complete 3-case workflow without needing 20GB+ VRAM booted:
```bash
uv run python -m hackathon.cli demo --offline
```

### 2. Live Meta Model Stack Setup (Apple Silicon / Linux)
To run live with Meta's Muse-Glimmer-30B:

**Terminal 1 — Download & Launch Mirai Model:**
```bash
brew install mirai
mirai --model trymirai/Muse-Glimmer-30B-M
```

**Terminal 2 — Start Uzu OpenAI-Compatible Proxy (Python 3.12):**
```bash
# If .venv-uzu is not already initialized:
# uv venv .venv-uzu --python 3.12 && uv pip install --python .venv-uzu/bin/python uzu
./scripts/start_uzu_proxy.sh
```

**Terminal 3 — Run Live Review CLI:**
```bash
uv run python -m hackathon.cli demo
```

Or review any custom C code snippet:
```bash
uv run python -m hackathon.cli review hackathon/fixtures/case1_supported_upper_bound.json
```

---

## The Three Canonical Cases

| Case | Scenario | Model Action | Deterministic Gate Action | Final Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Case 1** | `safe_copy`: upper-bound guard (`len >= cap`) protecting `memcpy(dst, src, len)` | Selects Candidate `C1` | **Confirmed**: 7/7 AST checks verify guard dominates sink | **`PASS`** |
| **Case 2** | `gdImageJpegPtr`: zero-width test on 3rd-party wrapper | Model refrains (`candidate_id: null`) | **Epistemic Bound**: AST domain refuses to certify unknown sinks | **`UNRESOLVED`** |
| **Case 3** | Superficial check (`if (len == 0) return;`) before `memcpy` | Model claims safety (`C1`) | **Blocked**: Gate rejects ungrounded candidate | **`BLOCKED`** |

---

## Verification & Evidence Pack

- **Audit Trace**: Detailed in [`hackathon/evidence_pack/audit_m9bol_gate_smoke_v10.json`](evidence_pack/audit_m9bol_gate_smoke_v10.json) from the live `m9bol-gate-smoke-v10` run.
- **TDD Test Suite**: 34 focused unit and replay tests covering failure modes and receipt contracts:
  ```bash
  uv run pytest tests/test_con_receipt_e2e.py tests/test_con_receipt_extractor.py tests/test_counter_evidence_fixtures.py tests/test_failure_modes_replay.py
  ```

---

## 3-Minute Video Beat Sheet

- **0:00 - 0:30 (The Hook):** Show the IDE security disclaimer: *"AI coding agents have limitations; verify all actions."* Show that developers cannot trust probabilistic LLM text for memory safety.
- **0:30 - 1:15 (The Supported Case):** Run `python -m hackathon.cli review case1`. Show Muse-Glimmer-30B identifying candidate `C1` and the AST gate printing green checkmarks for control-flow dominance.
- **1:15 - 2:00 (The Contrast Case):** Run `case3` where code has an irrelevant `len == 0` check. Show the deterministic gate blocking the claim cold with red crosses (`BLOCKED`).
- **2:00 - 2:30 (The Honest Boundary):** Run `case2` (library wrapper). Explain why `UNRESOLVED` is a victory: an AI that admits when it lacks proof instead of lying to the user.
- **2:30 - 3:00 (The Conclusion):** Summarize how pairing Meta models with deterministic evidence gates turns AI coding assistants into verified security reviewers.

