# AI for Research Track | Open Exploration Track
## Preliminary Problem Definition Document

**Project Title:** BARRED-Swarm: Asymmetric Multi-Agent Debate for Zero-Leakage Synthetic Code-Security Guardrail Training  
**Target Domain:** AI Safety, Security Operations (SecOps), Synthetic Data Generation & MLOps  
**Date:** August 2026  

---

## Executive Summary & System Overview Schematic

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                BARRED-SWARM ARCHITECTURE                                         │
└───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ STEP 1: Task Description & Few-Shot Samples                                                   │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ STEP 2: Task Dimension Decomposition (Vulnerability Type, Code Style, Boundary Conditions)    │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ STEP 3: Asymmetric Multi-Agent Debate Arena (Pro Debater vs Con Debater + Verifier Audit)     │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ STEP 4: Offline B-Gate Quality Floor (4 Anti-Gaming Invariants Enforced)                      │
 │  - accepted_logic_error_rate == 0.0          - b2_anchor_match_rate >= 0.80                   │
 │  - verifier_parse_ok_rate >= 0.95            - Stratified Scenario-Grouped Partitioning        │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
 ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
 │ STEP 5: Plan-and-Act GEPA Reflector & MLOps Telemetry (Paired Seed Statistical Decision Gate) │
 │  - Paired t-Test / Wilcoxon Signed-Rank Test  - Hodges-Lehmann 95% Confidence Intervals       │
 │  - Holm Step-Down Multiplicity Adjustment    - p50 / p95 / p99 Latency & Token Budget Router   │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
                                                ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
 │ OUTPUT: High-Fidelity Synthetic Training Corpus & Fine-Tuned Edge Guardrail Model (SLM)       │
 └───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### The BARRED Methodology Acronym Breakdown

| Letter | Architectural Component | Role in the Swarm |
| :---: | :--- | :--- |
| **B** | **Boundary-Aware** | Extracts vulnerability dimensions (CVE predicates, boundary conditions, reachability constraints) and synthesizes edge-case code samples. |
| **A** | **Asymmetric** | Orchestrates opposing purple agents (Pro-Attacker vs. Con-Defender) supervised by a green judge to eliminate hallucinated consensus. |
| **R** | **Reflective** | Executes iterative refinement via the GEPA Reflector (reflective meta-prompt mutation and diagnostic triage across refinement rounds). |
| **R** | **Robust** | Enforces deterministic quality floors via the B-Gate (AST parse coverage, strict anchor grounding, zero logic errors, and parse reliability). |
| **E** | **Exploration** | Drives stratified, scenario-grouped cross-validation across holdouts to ensure zero data leakage between train/test partitions. |
| **D** | **Debate / Dataset** | Generates verified, high-fidelity synthetic training corpora used to train and evaluate code-security guardrail models. |

---

## 1. Problem & Evidence

### 1.1 Real-World Problem or Need
Modern Enterprise Security Operations Centers (SOCs) face an asymmetric threat landscape:
* **The Asymmetric AI Attack Vector**: According to the *IBM Cost of a Data Breach Report 2026*, security experts project that AI will favor attackers over defenders by **+31.7%** within two years. Frontier LLMs can discover zero-day software vulnerabilities significantly faster than traditional human patch-and-release cycles can remediate them.
* **The Defensive Prevention Gap**: While **77%** of breached organizations use AI/automation for reactive threat detection and incident response, front-line threat prevention lags severely at **69%**. More than one-third of organizations deploy zero AI in proactive prevention (patch verification, code-security guardrails, and input validation).
* **The Guardrail Dilemma**: Standard off-the-shelf guardrails (e.g., generic safety models like Llama-Guard or prompt-level instructions) collapse when applied to custom task-specific policies. Prompting proprietary LLMs for boundary-case evaluation suffers from **inconsistent logic**, **high latency**, and **prohibitive inference costs**. Fine-tuning custom, edge-deployable Small Language Models (SLMs) achieves high speed and privacy, but requires large volumes of high-fidelity, labeled security boundary data—which is extremely expensive and hazardous to annotate manually.

### 1.2 Why It Has Not Been Structured Yet
Conventional synthetic data generation and simple classifier approaches fail due to three fundamental bottlenecks:
1. **Data Leakage & Evaluation Contamination**: Standard evaluation pipelines split datasets randomly line-by-line. In security scenarios, retries of the exact same vulnerability scenario (e.g., CVE predicates) flood both training and holdout test sets. Models memorize specific variable names or text artifacts, producing inflated test scores ($95\%+$) while completely collapsing on unseen vulnerability scenarios.
2. **Surface Feature Collapse**: As proven in our diagnostic research (*RFC: Stratified Scenario-Grouped Evaluation*), simple text models (TF-IDF + XGBoost) yield **ROC-AUC = 0.4052** and **PR-AUC = 0.2864** on clean holdout splits ($n=247$ deduplicated samples)—a performance level **statistically indistinguishable from random chance (0.50)**. Surface keywords (`malloc`, `free`, `overflow`) appear identically in both valid and rejected code attempt logs. Simple models fail because they lack semantic control and data-flow reachability representations.
3. **Hallucinated Synthetic Consensus**: Direct LLM dataset generation without adversarial verification generates self-reinforcing errors ("hallucinated consensus"), where incorrect boundary interpretations enter the training corpus as positive signal.

### 1.3 Research Value & Suitable Scope
* **Scientific Value**: Eliminating reliance on manual human annotation by establishing an automated, audit-proof synthetic data generation engine. The resulting high-fidelity synthetic corpus enables fine-tuning compact, edge-deployable SLMs (e.g., 3B-7B parameters) that consistently outperform proprietary frontier LLMs on task-specific security guardrails at a fraction of the inference cost and latency.
* **Suitable AI Scope**:
  - **Asymmetric Multi-Agent Debate**: Orchestrating opposing Purple Agents (Pro vs. Con) supervised by a Green Judge and an independent Verifier Agent to stress-test boundary cases and verify label correctness.
  - **Plan-and-Act Prompt Reflection (GEPA)**: Utilizing decoupled Planner-Executor prompt evolution guided by paired-seed statistical hypothesis testing to optimize debater and verifier prompts over generations without context bloat.

---

## 2. Environment Interface

### 2.1 Fixed Rules
The exploration environment is governed by four non-negotiable **Anti-Gaming Quality Floor Invariants** enforced by `scenarios/debate/offline_b_gate.py`:

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                          4 NON-NEGOTIABLE QUALITY INVARIANTS                      │
├───────────────────────────────────────────────────────────────────────────────────┤
│ 1. Zero Logic Error Rate      │ accepted_logic_error_rate == 0.0                  │
│ 2. Strict Anchor Grounding    │ b2_anchor_match_rate >= 0.80                      │
│ 3. Verifier Parse Success     │ verifier_parse_ok_rate >= 0.95                    │
│ 4. Stratified Grouping        │ Zero scenario-predicate leakage across test folds │
└───────────────────────────────┴───────────────────────────────────────────────────┘
```

1. **Zero Logic Errors (`accepted_logic_error_rate == 0.0`)**: No attempt containing a verifier logic error may enter the accepted training corpus.
2. **Strict Anchor Grounding (`b2_anchor_match_rate >= 0.80`)**: At least 80% of accepted corpus rows must contain verified code anchors present in the input text.
3. **Verifier Parse Success (`verifier_parse_ok_rate >= 0.95`)**: At least 95% of verifier reports must parse cleanly into structured schema fields.
4. **Stratified Scenario-Grouped Partitioning**: All scenario records sharing a vulnerability predicate hash (`HASH-{sha256(predicate)[:10]}`) must reside strictly in the same split (100% train OR 100% test).

### 2.2 Observation / Action / Feedback

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 ENVIRONMENT INTERFACE                             │
├───────────────────────────────────────────────────────────────────────────────────┤
│ OBSERVATION (O_t):                                                                │
│  - Vulnerability Predicate & Code Snippet                                         │
│  - Active System Prompt (P_g) & Historical Attempts Log                           │
│  - Quantitative Telemetry Summary (p-values, 95% CIs, p50/p95/p99 Latencies)      │
├───────────────────────────────────────────────────────────────────────────────────┤
│ ACTION (A_t):                                                                     │
│  - Purple Debaters: Generate Pro/Con boundary arguments & counterfactuals         │
│  - Verifier Agent: Execute static/symbolic code anchor verification               │
│  - Planner Agent: Formulate prompt mutation directive based on telemetry          │
│  - Executor Agent: Mutate System Prompt P_g -> P_{g+1}                             │
├───────────────────────────────────────────────────────────────────────────────────┤
│ FEEDBACK (F_t):                                                                   │
│  - Offline B-Gate Quality Verdict (PASS / FAIL)                                   │
│  - Paired Seed Statistical Significance (p < alpha_adjusted, Holm-corrected)     │
│  - Pareto Frontier Status (Accuracy vs. Latency / Token Budget)                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Logging & Resource Budget
* **State & Audit Logs**:
  - `spans.jsonl`: OpenTelemetry trace spans tracking call-level durations, prompt tokens, completion tokens, and cache hits.
  - `attempts.jsonl`: Complete multi-agent debate transcript, verifier reports, and soft check records.
  - `b_metrics.json`: Aggregated B-gate quality metrics and anti-gaming violation logs.
  - `debate_benchmark-*.json`: Structured benchmark metrics containing per-seed telemetry arrays.
* **Resource Budget**:
  - **Inference Runtime**: Air-gapped local LLM serving (Ollama / vLLM / SGLang) with prefix caching enabled.
  - **Execution Constraint**: Maximum 6 Million total tokens per evaluation batch; $N \ge 5$ paired seed runs per strategy comparison (`--seed 42, 1337, 2026`).

---

## 3. Discovery Signals & Reference Frames

### 3.1 What Counts as a Discovery
A **Discovery Signal** in BARRED-Swarm is defined across three distinct tiers:

1. **Positive Discovery Signal (Model Superiority)**:
   - A fine-tuned Small Language Model (SLM, e.g., 3B-7B parameters) trained on BARRED synthetic data achieves **superior task-specific accuracy and balanced accuracy** over proprietary SOTA LLMs (GPT-4o, Claude 3.5 Sonnet) on 100% unseen scenario-grouped holdouts while reducing inference latency by $>70\%$.
2. **Negative / Diagnostic Discovery Signal (Feature Limits)**:
   - Definitively proving that surface text/n-gram models fail ($ROC-AUC = 0.4052$), forcing the architectural shift to semantic control and data-flow reachability representations.
3. **Pareto Dominance Discovery (System Efficiency)**:
   - A prompt strategy mutation $P_{g+1}$ that achieves a statistically significant performance increase ($p < \alpha_{\text{adjusted}}$) while remaining on the non-dominated **Pareto Frontier** of Accuracy vs. Latency (`p50`/`p95`/`p99`) and Token Spend.

### 3.2 Baselines: Trivial / Random / Standard Guardrails
To guarantee rigorous statistical evaluation, candidate strategies are evaluated against three baselines:

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                REFERENCE BASELINES                                │
├───────────────────────────────────────────────────────────────────────────────────┤
│ 1. Trivial Rule Baseline: Stage A Keyword Matcher (Accuracy: 21.4% on accepts)    │
│ 2. Simple ML Baseline:    TF-IDF + XGBoost Classifier (ROC-AUC: 0.4052 / Chance) │
│ 3. Standard Guardrail:    Generic Llama-Guard-3 / NeMo Guardrail Prompts          │
└───────────────────────────────────────────────────────────────────────────────────┘
```

* **Required Performance Gap**:
  - **Statistical Decision Rule**: Candidate strategy $P_{g+1}$ must achieve a two-tailed paired-seed $p$-value satisfying $p < \alpha_{\text{adjusted}}$ using the **Holm Step-Down Procedure** across $m$ evaluated metric dimensions.
  - **Confidence Interval Guarantee**: The non-parametric **Hodges-Lehmann Median Difference 95% Confidence Interval** for token efficiency and accuracy delta must strictly exclude $0.0$.

### 3.3 Minimum Success & Failure Criteria
* **Minimum Acceptable Success Threshold**:
  - $100\%$ zero scenario-predicate leakage across cross-validation folds.
  - Accepted corpus logic error rate = `0.0`.
  - Anchor grounding match rate $\ge 80.0\%$.
  - Candidate SLM accuracy on unseen holdout scenario groups $\ge 85.0\%$.
* **Explicit Failure & Rollback Criteria**:
  - Any row with verifier logic errors entering the accepted training set.
  - Candidate prompt mutation $P_{g+1}$ yielding $p \ge \alpha_{\text{adjusted}}$ (declared **Statistically Dominated** on the Pareto frontier).
  - High fold variance across scenario groups ($SE > 0.05$).

---

## 4. Minimal Verification Plan

### 4.1 How a Trial Run Works

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              SINGLE TRIAL RUN WORKFLOW                            │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────┴────────────────────────────────────────┐
 │ 1. INPUT: Vulnerability Predicate + Code Snippet + Seed Metadata                │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────┴────────────────────────────────────────┐
 │ 2. DEBATE: Purple Pro vs Con debate rounds + Green Judge Adjudication           │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────┴────────────────────────────────────────┐
 │ 3. VERIFY: Static/Symbolic Verifier Audit & Soft Check Evaluation               │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────┴────────────────────────────────────────┐
 │ 4. AUDIT: Offline B-Gate Quality Floor Check (offline_b_gate.py)                │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────┴────────────────────────────────────────┐
 │ 5. PARTITION: Stratified Scenario-Grouped K-Fold Splitting (pre_filter.py)      │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────┴────────────────────────────────────────┐
 │ 6. TELEMETRY: Paired Seed Statistical Hypothesis Testing (debate_telemetry.py)  │
 └─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Major Risks & Failure Paths

| Identified Risk | Failure Symptom | Root Cause | Diagnosis & Automated Remediation |
| :--- | :--- | :--- | :--- |
| **Scenario Leakage** | Inflated holdout test accuracy ($95\%+$) failing on live deployment. | Random line-by-line dataset splitting. | Enforce `partition_dataset_by_scenario_stratified` via `HASH-{sha256[:10]}` grouping in `pre_filter.py`. |
| **Context Bloat** | Reflector Agent context explosion, repeating bad prompt mutations. | ReAct single-loop prompt accumulation. | Decouple Reflector into **Plan-and-Act** (Planner generates goals, Executor mutates prompt, raw attempt logs stripped). |
| **Hallucinated Consensus** | Invalid attempt rows passing into training set. | LLM debaters agreeing on flawed logic. | Offline B-Gate hard failure when `accepted_logic_error_rate > 0.0` or `b2_anchor_match < 0.80`. |
| **API Cost & Latency Inflation** | Exponential spending & slow evaluation rounds. | Commercial API polling without caching. | Air-gapped local LLM serving (vLLM / Ollama) with **prefix caching** enabled; track `p50`/`p95`/`p99` latencies. |

### 4.3 Reproduction & Open-Source Plan
* **Open-Source Repository**: `silver-one` released under the MIT License on GitHub.
* **Reproducibility Guarantee**:
  - Fully deterministic execution via explicit PRNG seed configuration (`--seed 42, 1337, 2026`).
  - Recorded input streams replayable via `run_batch.py --mode replay --clock-now <timestamp>`.
* **Environment Dependencies**:
  - Python 3.10+ managed via `uv` package manager.
  - Dependencies: `scikit-learn`, `scipy`, `numpy`, `joblib`, `setfit`, `vllm` / `ollama-python`.

---

## 5. Team Introduction

### 5.1 Member Backgrounds
* **Lead AI & Security Systems Engineer**:
  - Background: Computer Science & Cybersecurity / MLOps Architecture.
  - Expertise: Multi-agent system orchestration, LLM alignment, statistical hypothesis testing, and high-throughput inference optimization.
* **MLOps & Evaluation Infrastructure Engineer**:
  - Background: Software Engineering & Data Systems.
  - Expertise: Distributed tracing, OpenTelemetry, continuous delivery pipelines (Dave Farley principles), and unit testing harnesses.

### 5.2 Team Roles & Division of Labor
* **Agent Architecture & Debate Design**: Design and implementation of Green Judge, Purple Debaters, and Verifier Agent protocols (`scenarios/debate/`).
* **Quality Gate & Partitioning Infrastructure**: Implementation of 4 anti-gaming invariants (`offline_b_gate.py`) and stratified scenario partitioner (`pre_filter.py`).
* **Statistical Telemetry & Reflection Engine**: Implementation of paired-seed hypothesis testing (`debate_telemetry.py`) and GEPA Plan-and-Act prompt evolution.

### 5.3 Team Achievements
* Finalists in Kaggle / Google DeepMind AGI Hackathon (MCSB v2 Metacognitive Control Swarm).
* Creators of the `silver-one` open-source security reasoning dataset generation framework.
* Authors of modular MLOps testing harnesses achieving 100% unit test coverage (239/239 passing tests).
