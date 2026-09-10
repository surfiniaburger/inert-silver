# Track 3: AI for Research | Problem Type II: Open Exploration Problems
## Preliminary Problem Definition Document

**Project Title:** BARRED-Swarm: Autonomous Multi-Agent Debate & Verification Environment for Zero-Leakage Synthetic Code-Security Guardrail Training  
**Track & Problem Type:** Track 3 (AI for Research) — Problem Type II: Open Exploration Problems  
**Target Domain:** AI Safety, Self-Evolving Agent Systems, Synthetic Data Benchmarks & MLOps  
**Date:** August 2026  

---

## 1. Problem & Evidence

### 1.1 The Real-World Context & Threat Landscape
Software security operations face an accelerating asymmetry:
* **The AI Attacker Advantage**: According to the *IBM Cost of a Data Breach Report 2026*, security experts project that AI will favor attackers over defenders by **+31.7%** within two years. Frontier AI models can discover software zero-days faster than traditional human patching cycles can remediate them.
* **The Defensive Prevention Lag**: While **77%** of breached organizations use AI for reactive threat detection, front-line threat prevention lags at **69%**. Over one-third of organizations deploy zero AI in proactive prevention (input validation, patch verification, and code-security guardrails).
* **The Guardrail Bottleneck**: Generic safety models (e.g., standard Llama-Guard) fail on custom task-specific policies. Prompting proprietary cloud models for boundary cases suffers from high latency and prohibitive inference costs. Fine-tuning custom, edge-deployable Small Language Models (SLMs, 3B–7B) provides speed and privacy, but requires large volumes of high-fidelity, labeled boundary data—which is hazardous and expensive to annotate manually.

### 1.2 Why Existing Approaches Are Unstructured
Building synthetic security datasets using conventional ML or direct LLM prompting fails due to three fundamental issues:
1. **Scenario-Predicate Data Leakage**: Standard evaluation pipelines split datasets randomly line-by-line. In security scenarios, retries of the exact same vulnerability predicate flood both train and test splits. Models memorize variable names, giving inflated test scores ($95\%+$) while completely failing on unseen vulnerability scenarios.
2. **Surface Feature Collapse (Empirical Finding)**: In our baseline diagnostic experiments, simple text models (TF-IDF + XGBoost) achieved an **ROC-AUC of 0.4052** and **PR-AUC of 0.2864** on clean holdouts ($n=247$ deduplicated samples)—a performance level **statistically indistinguishable from random chance (0.50)**. Keywords like `malloc`, `free`, or `overflow` appear equally in valid and invalid code attempts. Surface text matching hits a hard ceiling because code security requires semantic data-flow reachability.
3. **Hallucinated Synthetic Consensus**: Direct LLM data generation without adversarial verification creates self-reinforcing errors ("hallucinated consensus"), where incorrect boundary interpretations enter the training corpus as positive signal.

### 1.3 Scientific Research Value & Suitable AI Scope
* **Core Research Question**:
  > *Can an autonomous exploration environment using asymmetric game-theoretic multi-agent debate and formal verifier feedback eliminate hallucinated consensus and scenario leakage in synthetic training data without human annotation?*
* **Suitable AI Scope**:
  - **Asymmetric Multi-Agent Debate Arena**: Orchestrating opposing Purple Agents (Pro vs. Con) supervised by a Green Judge and an independent Verifier Agent to stress-test boundary cases and verify label correctness.
  - **Plan-and-Act Prompt Evolution (GEPA)**: Utilizing a decoupled Planner-Executor reflection loop guided by paired-seed statistical hypothesis testing to evolve debater and verifier prompts over generations without context bloat.

---

## 2. Environment Interface

### 2.1 Environment Overview Schematic

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                BARRED-SWARM ENVIRONMENT                                          │
└───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ 1. INPUT: Vulnerability Predicate + Code Snippet + Seed Metadata                            │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ 2. ASYMMETRIC DEBATE: Purple Pro vs Purple Con + Green Judge Adjudication                    │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ 3. FORMAL VERIFIER AUDIT: Static/Symbolic Code Anchor Verification                           │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ 4. OFFLINE QUALITY AUDIT GATE (4 Quality Floor Invariants):                                  │
 │  - accepted_logic_error_rate == 0.0          - b2_anchor_match_rate >= 0.80                   │
 │  - verifier_parse_ok_rate >= 0.95            - Stratified Scenario-Grouped Partitioning        │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ 5. TELEMETRY & REFLECTION (Statistical Hypothesis Engine + GEPA Plan-and-Act Loop):         │
 │  - Paired t-Test / Wilcoxon Signed-Rank Test  - Hodges-Lehmann 95% Confidence Intervals       │
 │  - Holm Step-Down Multiplicity Adjustment    - p50 / p95 / p99 Latency & Token Budget Router   │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
                                                ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
 │ OUTPUT: Verified Synthetic Corpus & Fine-Tuned Edge Small Language Model (SLM)                │
 └───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Fixed Rules & Stable Constraints
The environment is governed by four non-negotiable **Anti-Gaming Quality Floor Invariants** enforced by the Offline Quality Audit Gate:

1. **Zero Logic Error Rate (`accepted_logic_error_rate == 0.0`)**: No attempt containing a verifier logic error may enter the accepted corpus.
2. **Strict Anchor Grounding (`b2_anchor_match_rate >= 0.80`)**: At least 80% of accepted corpus rows must contain verified code anchors present in the input text.
3. **Verifier Parse Success (`verifier_parse_ok_rate >= 0.95`)**: At least 95% of verifier reports must parse cleanly into structured schema fields.
4. **Stratified Scenario-Grouped Partitioning**: All scenario records sharing a vulnerability predicate hash (`HASH-{sha256(predicate)[:10]}`) must reside strictly in the same split (100% train OR 100% test), preventing prompt bleeding.

### 2.3 Observation / Action / Feedback Space
* **Observation ($O_t$)**: Vulnerability predicate, code anchors, attempt execution log, active system prompt $P_g$, and quantitative telemetry summary (paired-seed $p$-values, 95% CIs, `p50`/`p95`/`p99` latencies).
* **Action ($A_t$)**:
  - *Purple Debaters*: Generate Pro/Con boundary arguments and counterfactual code scenarios.
  - *Verifier Agent*: Execute static/symbolic code anchor verification.
  - *Planner Agent*: Formulate high-level prompt mutation directives based on statistical failure buckets.
  - *Executor Agent*: Mutate System Prompt $P_g \rightarrow P_{g+1}$ and strip raw attempt logs to prevent context bloat.
* **Feedback ($F_t$)**: Audit gate acceptance verdict (PASS/FAIL), verifier logic error flags, paired-seed statistical significance ($p < \alpha_{\text{adjusted}}$), and Pareto frontier non-dominance status.

### 2.4 Logging, Infrastructure & Resource Budget
* **Current Model Setup**: Cloud LLM endpoints (`gpt-oss:120b` and `gemma4:31b`) orchestrating debate, verification, and adjudication.
* **Roadmap Local Setup (Stage 2)**: Transitioning candidate debate generation and pre-filtering to dedicated local serving (vLLM / Ollama with prefix caching) to optimize TTFT and token throughput.
* **Audit Logs**: OpenTelemetry trace spans, complete multi-agent debate logs, quality audit metrics, and paired-seed statistical telemetry reports.
* **Resource Budget**: Maximum 6 Million total tokens per evaluation batch; $N \ge 5$ paired seed runs per strategy comparison (`--seed 42, 1337, 2026`).

---

## 3. Discovery Signals & Reference Frames

### 3.1 What Counts as a Discovery
In this exploration environment, a **Discovery Signal** is defined across three explicit outcomes:

1. **Positive Discovery Signal (Model Superiority)**:
   - A fine-tuned Small Language Model (SLM, e.g., 3B-7B parameters) trained on BARRED synthetic data achieves superior task-specific accuracy and balanced accuracy over proprietary SOTA LLMs (GPT-4o, Claude 3.5 Sonnet) on 100% unseen scenario-grouped holdouts while reducing inference latency by $>70\%$.
2. **Negative / Diagnostic Discovery Signal (Explicitly Permitted)**:
   - Quantifying the exact failure modes of simple text models ($ROC-AUC = 0.4052$), proving that surface n-grams fail without data-flow reachability representations.
3. **Pareto Dominance Discovery (System Efficiency)**:
   - A prompt strategy mutation $P_{g+1}$ that achieves a statistically significant performance increase ($p < \alpha_{\text{adjusted}}$) while remaining on the non-dominated Pareto Frontier of Accuracy vs. Latency (`p50`/`p95`/`p99`) and Token Spend.

### 3.2 Baselines & Required Performance Gap
To rule out random luck and trivial solutions, candidate strategies are evaluated against three baselines:
* **Trivial Rule Baseline**: Stage A keyword matcher (Accuracy: 21.4% on accepted candidates).
* **Simple ML Baseline**: TF-IDF + XGBoost classifier (ROC-AUC: 0.4052).
* **Standard Guardrail Baseline**: Generic Llama-Guard-3 / NeMo Guardrail prompts.
* **Required Performance Gap**: Candidate strategy $P_{g+1}$ must achieve a two-tailed paired-seed $p$-value satisfying $p < \alpha_{\text{adjusted}}$ using the **Holm Step-Down Procedure**, and the **Hodges-Lehmann 95% Confidence Interval** for accuracy delta must strictly exclude $0.0$.

### 3.3 Minimum Success & Failure Criteria
* **Minimum Success Criteria**: Zero scenario leakage across cross-validation folds, accepted corpus logic error rate = `0.0`, anchor match rate $\ge 80.0\%$, and fine-tuned SLM accuracy $\ge 85.0\%$ on unseen holdouts.
* **Explicit Failure Criteria**: Any verifier logic error entering the accepted corpus, or candidate prompt mutation $P_{g+1}$ yielding $p \ge \alpha_{\text{adjusted}}$ (declared statistically dominated).

---

## 4. Minimal Verification Plan

### 4.1 Staged Evolution & Trial Run Workflow
Following disciplined MLOps practices, our exploration evolves in five clear phases:

```text
Phase 1: Rule-Based Sanity Floor
Sub-millisecond rule check (NEGATIVE_RULES) to reject obvious junk inputs before calling any model.

Phase 2 & 3: Simple ML Models (Testing the Floor)
Tested shallow TF-IDF n-gram models (XGBoost).
Result: ROC-AUC collapsed to 0.4052 on unseen scenario holdouts.
Lesson: Keywords like malloc or overflow appear in both good and bad code. Simple text matching hits a ceiling because code security requires data-flow reachability.

Phase 4: Asymmetric Multi-Agent Debate (Corpus Generation)
With simple models exhausted, we deploy cloud models (gpt-oss:120b, gemma4:31b) in an asymmetric debate arena.
Purple debaters argue boundary cases, Green judge adjudicates, Verifier audits code anchors. If a verifier logic error is caught, the row is discarded by the quality audit gate.

Phase 5: Local Serving & Plan-and-Act Reflection (Roadmap)
Transitioning candidate runs to local serving (vLLM / Ollama with prefix caching) to track p50/p95/p99 latencies, run GEPA Plan-and-Act prompt evolution, and fine-tune compact 3B-7B edge SLMs.
```

### 4.2 Major Risks & Automated Remediation

| Identified Risk | Failure Symptom | Root Cause | Diagnosis & Automated Remediation |
| :--- | :--- | :--- | :--- |
| **Scenario Leakage** | Inflated holdout test accuracy ($95\%+$) failing on live deployment. | Random line-by-line dataset splitting. | Enforce Stratified Scenario-Grouped Partitioning via SHA-256 predicate hashing (`HASH-{sha256[:10]}`). |
| **Context Bloat** | Reflector Agent context explosion, repeating bad prompt mutations. | ReAct single-loop prompt accumulation. | Decouple Reflector into **Plan-and-Act** (Planner generates goals, Executor mutates prompt, raw attempt logs stripped). |
| **Hallucinated Consensus** | Invalid attempt rows passing into training set. | LLM debaters agreeing on flawed logic. | Offline Quality Audit Gate hard failure when `accepted_logic_error_rate > 0.0` or `b2_anchor_match < 0.80`. |
| **API Cost & Latency Inflation** | Exponential spending & slow evaluation rounds. | Commercial API polling without caching. | Transition to local serving (vLLM / Ollama) with **prefix caching** enabled; track `p50`/`p95`/`p99` latencies. |

### 4.3 Reproduction & Open-Source Plan
* **Open-Source Repository**: `silver-one` released under the MIT License on GitHub.
* **Reproducibility Guarantee**: Explicit PRNG seed configuration (`--seed 42, 1337, 2026`) and replayable execution via the Deterministic Replay Engine.

---

## 5. Team Introduction & Self-Assessment Compliance

### 5.1 Team Background & Division of Labor
* **Lead AI & Security Systems Engineer**: Multi-agent system orchestration, LLM alignment, statistical hypothesis testing, and high-throughput inference optimization.
* **MLOps & Evaluation Infrastructure Engineer**: OpenTelemetry distributed tracing, continuous delivery pipelines (Dave Farley principles), and unit testing harnesses.

### 5.2 Team Achievements
* Finalists in Kaggle / Google DeepMind AGI Hackathon (MCSB v2 Metacognitive Control Swarm).
* Creators of the `silver-one` open-source security reasoning dataset generation framework (100% unit test pass rate across 241 tests).

### 5.3 Handbook Self-Assessment Checklist Verification (Page 78)
1. **If AI were removed, is the problem valid?** Yes. Verifying software boundary safety and preventing dataset leakage under cross-validation are foundational computer science research problems.
2. **Is it a genuine research question?** Yes. It investigates game-theoretic debate as a truth-seeking mechanism for calibrating LLM reasoning beliefs.
3. **Do agent actions change subsequent decisions?** Yes. Debater arguments alter judge adjudications, and telemetry changes planner prompt mutations.
4. **Is feedback rich enough to iterate?** Yes. Includes trace spans, verifier logic error reports, soft check passes, and paired-seed $p$-values.
5. **Does the baseline rule out random luck?** Yes. Paired-seed statistical testing ($t$-test, Wilcoxon, Holm step-down, Hodges-Lehmann CIs) rules out seed noise.
6. **Are results protected against leakage and hallucinations?** Yes. Enforced by Stratified Scenario-Grouped Partitioning and B-Gate quality floor invariants (`accepted_logic_error_rate == 0.0`).

---

## 6. Scientific References & Theoretical Grounding

1. A. Mazza and E. Levi, "BARRED: Synthetic Training of Custom Policy Guardrails via Asymmetric Debate," *Preprint*, Jan. 2026.  
   *Methodological Contribution*: Architectural blueprint for task-relevant dimension decomposition, opposing Purple debater strategies, Green judge adjudication protocols, and the 4 offline quality audit gate invariants.

2. L. A. Agrawal, S. Tan, D. Soylu, N. Ziems, et al., "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2026.  
   *Methodological Contribution*: Establishes the Plan-and-Act reflective execution-trace prompt adaptation paradigm, replacing scalar-reward RL and raw ReAct context accumulation with natural language failure diagnosis and Pareto frontier prompt selection.

3. IBM Security and Ponemon Institute, "Cost of a Data Breach Report 2026: The AI Tipping Point," *IBM Research Report*, 2026.  
   *Threat Landscape Data*: Establishes the real-world threat landscape, documenting the projected **+31.7% AI attacker advantage** within two years and the **69% defensive prevention adoption lag** across enterprise security operations centers.
