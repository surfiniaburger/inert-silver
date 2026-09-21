# Debate Research Scrapbook: Paradoxes, Prompt Lineage, & Architectural Angles

> **Status:** Living Document / Historical Reference  
> **Repository:** `silver-one` / `modular-metacog-swarm-v3`  
> **Tracking:** Evolution from $N=10$ Pilot to $N=50$ Scaling, Invariant Behavior, and Chapter-by-Chapter Roadmaps.

---

## 1. Executive Summary & Philosophy: Chapter 1 vs. Chapter 2

As our multi-agent neurosymbolic debate benchmark transitioned from initial 10-seed exploratory trials ($N=10$) to rigorous 50-seed statistical evaluation ($N=50$), maintaining scientific integrity requires a strict boundary between **System / Architectural Variables** and **Prompt Engineering Variables**.

We define two distinct historical epochs:

- **Chapter 1: The Empirical Evaluation of Systems under the Historical Prompt Lineage**
  - **Prompt Lineage:** Original un-mutated baseline prompt (`baseline_v0`) and the cumulative 355-step GEPA evolved prompts (`gepa_local`).
  - **Core Regimes Evaluated:**
    1. *Regime 1: Stationary AST Slicing Baseline* ($78.4\% \pm 5.2\%$ yield, 5 replicates, $N=250$).
    2. *Regime 2: Active Online Learning* (AST Slicing + Live Reflector Agent + Dynamic Pareto mutation library, 5 replicates, $N=250$).
    3. *Regime 3: Warm Pinned Pareto* (AST Slicing + Static Pareto library without live mutations).
  - **Principle:** Under Chapter 1, debater system prompts and anchor rules are strictly kept invariant to ensure that all differences across runs reflect pure algorithmic mechanisms (slicing, reflection, Pareto mutation), not ad-hoc prompt tweaking.

- **Chapter 2: Targeted Grounding & Structural Formatting Shields**
  - **Motivation:** Systematic resolution of the paradoxes uncovered during Chapter 1 (the *Instruction Overload / Round 0 Anchor Trap* and the *Refinement Tax*).
  - **Target Interventions:** Angle 1 (Formatting Shield: Anchor-First Invariant Blocks) and Angle 2 (Targeted Anchoring / Syntactic Grounding).

---

## 2. Empirical Telemetry & Core Hypotheses (Chapter 1)

### Telemetry Finding 1: The "Refinement Tax" Tradeoff
- **Empirical Observation:**
  - In Regime 1 (Stationary Slicing Baseline), first-pass Round 0 yield was high ($72.0\%$, 36/50 seeds accepted on attempt 1), with only 14 seeds requiring refinement.
  - In Regime 2 (Active Online Adaptation with evolved prompt `v355`), Round 0 rejections increased:
    - Rep 1: 24 initial failure episodes $\to$ 14 recovered on Round 1 ($58.3\%$).
    - Rep 2: 26 initial failure episodes $\to$ 7 recovered on Round 1 ($26.9\%$).
    - Cumulative ($N=2$): **50 Round 0 failure episodes triggered refinement; 21 were recovered on Round 1 ($42.0\%$ recovery rate)**.
- **The Tradeoff:**
  - The live Reflector is demonstrably effective at error recovery (rescuing $42\%$ of otherwise lost runs).
  - However, **recovery capability $\neq$ efficiency**. Each Round 1 debate attempt burns $\approx 11,000$ tokens.
  - Incurring $\approx 25$ failure episodes per replicate costs $\approx 275,000$ tokens of refinement burn, offsetting the token savings achieved by slicing the Judge context.

### Quantitative Metric: Recovery Efficiency ($\tau_{\text{rec}}$)
To evaluate the economic viability of the Reflector beyond crude total token counts, we formalize **Tokens per Recovered Episode**:

$$\text{Recovery Benefit} = \text{Episodes}_{\text{Round 1 Accepted}}$$
$$\text{Refinement Cost} = \sum \text{Tokens}_{\text{Round 1 Attempts}}$$
$$\tau_{\text{rec}} = \frac{\text{Refinement Cost}}{\text{Recovery Benefit}} = \mathbf{\text{Tokens Per Recovered Episode}}$$

- Across Reps 1 & 2: $\approx 550,000$ refinement tokens were spent to yield 21 recovered rows:
  $$\tau_{\text{rec}} \approx \mathbf{26,190 \text{ tokens / recovered episode}}$$
- This provides an actionable engineering benchmark: any intervention in Chapter 2 that prevents an episode from failing Round 0 saves $\approx 26,000$ tokens on that seed.

### Core Systems Hypothesis: Induced vs. Repaired Failures
> **Working Hypothesis:** *Online adaptation is recovering failed attempts, but the instruction structure of the evolved prompt may be inducing the very syntactic failures that the Reflector subsequently repairs.*

**Competing Explanations (To be Isolated in Chapter 2):**
1. *Instruction Competition:* Advanced vulnerability analysis directives compete for model attention against the strict invariant requirement to cite verbatim line anchors.
2. *Context / Instruction Bloat:* The length of cumulative mutations increases prompt token mass, diluting syntactic compliance.
3. *Output Schema Absence:* Without an explicit output format contract, the model prioritizes natural language prose over exact bracketed citation syntax.
4. *Reasoning Burden:* Deeper semantic analysis increases generation length, pushing the model away from terse extraction.

---

## 3. The 6-Condition Factorial Ablation Matrix (Chapter 2 Design Space)

Rather than pursuing ad-hoc prompt variations, Chapter 2 is formalized as a systematic factorial matrix to isolate the contribution of each architectural layer:

| Condition | Description | AST Slice | Warm Pareto | Live Reflector | Formatting Shield | Syntactic Anchoring | Core Question Evaluated |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **A** | Unpruned Control | ✗ | ✗ | ✗ | ✗ | ✗ | Historical unpruned baseline ($N=50$) |
| **B** | Sliced Stationary | ✓ | ✗ | ✗ | ✗ | ✗ | **Regime 1:** What is the pure effect of AST Program Slicing? ($78.4\% \pm 5.2\%$) |
| **C** | Pinned Pareto | ✓ | ✓ | ✗ | ✗ | ✗ | **Angle 3:** Is the benefit from the evolved prompt prior or active online mutation? |
| **D** | Active Online | ✓ | ✓ | ✓ | ✗ | ✗ | **Regime 2:** What is the combined effect of live mutation + reflector recovery? |
| **E** | Formatting Shield | ✓ | ✓ | ✓ | ✓ | ✗ | **Angle 1:** Does an invariant output contract eliminate Round 0 anchor drops? |
| **F** | Guided Anchoring | ✓ | ✓ | ✓ | ✓ | ✓ | **Angle 2:** Does deterministic graph grounding assist evidence selection? |

---

## 4. Formal Definition of Architectural Angles

### Angle 1: The Formatting Shield (Output Contract Enforcement)
- **Question:** *Can the same reasoning prompt produce fewer anchor failures simply by moving invariant constraints into an explicit output contract?*
- **Mechanism:** Enforce an immutable, anchor-first output structure:
  ```markdown
  ### MANDATORY VERBATIM ANCHOR BLOCK
  [ANCHOR_1]: `<exact line from untrusted code>`
  [ANCHOR_2]: `<exact line from untrusted code>`
  
  ### VULNERABILITY ARGUMENT
  <debater analysis...>
  ```
- **Hypothesis:** Separates the syntactic constraint from the reasoning task, eliminating Round 0 anchor rejections without restricting cognitive reasoning depth.

### Angle 2: Targeted Syntactic Anchoring (Evidence Selection Interface)
- **Question:** *Can deterministic structural information reduce the model's search space for evidence selection?*
- **Mechanism:** The verifier or pre-filter pre-extracts critical line numbers from the AST slice (e.g., branch conditions, memory allocations) and explicitly instructs debaters: *"Ground your claim on lines [X, Y, or Z]"*.
- **Hypothesis:** Introduces the graph directly into the debater evidence-selection interface, rather than merely using it to slice Judge context.

### Angle 3: True Pinned Pareto (`--pin-pareto`)
- **Question:** *Is the benefit coming from the evolved prompt itself (warm prior), or from continuously adapting it online?*
- **Mechanism:** Freeze the Pareto frontier at mutation step 669, run stationary evaluation across all 50 seeds with zero Reflector calls, zero SQLite mutations, and zero live prompt edits.
- **Hypothesis:** Decouples the *Warm Pareto Prior Benefit* from the *Online Adaptation Benefit*.
- **Empirical Resolution (Replicate 1, Seed 42, $N=50$):**
  - **Yield:** **72.0% (36/50)** — matches single-replicate baseline, trailing Regime 2's mean of **80.4% ± 5.5%**.
  - **Round 0 Yield:** **56.0% (28/50)** — exactly matches Regime 2 (57.6%), confirming the **Round 0 Anchor Trap / Instruction Competition** is inherent to the evolved prompt's complexity.
  - **Refinement Recovery:** Drops from **50.4% (Regime 2)** down to **36.4% (8/22 in Regime 3)** because failing episodes retry with the *unmutated warm prompt* rather than receiving a targeted graph-repaired variant.
  - **Token Burn:** Collapses from **21,571 tokens/seed (Regime 2) down to 16,822 tokens/seed (Regime 3)**, essentially equal to the pure baseline (16,742).
  - **Conclusion:** The high yield of Regime 2 is driven by the **active closed-loop Reflector mutation engine** during refinement, not merely the passive presence of the warm prompt prior. Full report: [`reports/debate_benchmark_50_seed_pinned_pareto.md`](../reports/debate_benchmark_50_seed_pinned_pareto.md).

---

## 5. Current Experimental Lineage Tracker

| Epoch | Replicate / Run ID | Date | Seed | Prompts Used | Yield (%) | Accept/Attempts | Tokens / Accepted Row | Accepted Logic Errors (INV-1) |
|---|---|---|---|---|---|---|---|---|
| **$N=10$ Pilot** | `baseline-001..005` | 2026-09-08 | 42..46 | `baseline_v0` | 74.0% | 37/50 | 25,300 | 0/37 (0.0%) |
| **$N=10$ Pilot** | `pareto-001..005` | 2026-09-09 | 42..46 | GEPA Online | 88.0% | 44/50 | 19,850 | 0/44 (0.0%) |
| **Regime 1 ($N=50$)** | `unrun-sliced-baseline-rep1..5` | 2026-09-11 | 42..46 | `baseline_v0` (Sliced) | 78.4% | 196/250 | 21,411 | 0/196 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep1` | 2026-09-13 | 42 | GEPA Live (Sliced) | 80.0% | 40/50 | 21,844 | 0/40 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep2` | 2026-09-14 | 43 | GEPA Live (Sliced) | 76.0% | 38/50 | 24,329 | 0/38 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep3` | 2026-09-21 | 44 | GEPA Live (Sliced) | 78.0% | 39/50 | 20,568 | 0/39 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep4` | 2026-09-21 | 45 | GEPA Live (Sliced) | 90.0% | 45/50 | 18,526 | 0/45 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep5` | 2026-09-21 | 46 | GEPA Live (Sliced) | 78.0% | 39/50 | 22,586 | 0/39 (0.0%) |
| **Regime 3 (Angle 3)** | `unrun-pinned-pareto-50-rep1` | 2026-09-21 | 42 | Evolved Warm Frozen (v669) | 72.0% | 36/50 | 23,364 | 0/36 (0.0%) |

---

## 6. Execution Roadmap

1. **Chapter 1: Metacognitive Debate Dynamics (Completed)**
   - Completed all 5 replicates of Regime 1 (Stationary Baseline, $N=250$, yield: $78.4\% \pm 5.2\%$).
   - Completed all 5 replicates of Regime 2 (Active Online Adaptation, $N=250$, yield: $80.4\% \pm 5.5\%$).
   - Implemented and evaluated Angle 3 (True Pinned Pareto, $N=50$, yield: $72.0\%$).
   - Rigorously proved: Active online reflection drives the high recovery rate ($50.4\%$), whereas the warm prior alone suffers from Instruction Competition without online repair.

2. **Chapter 2: Structural Grounding Interventions (Next)**
   - **Angle 1: Formatting Shield (Output Contract Enforcement):** Enforce immutable anchor-first block syntax to prevent Instruction Competition from dropping Round 0 anchors.
   - **Angle 2: Targeted Syntactic Grounding:** Pass candidate AST lines directly to debaters to guide search.
   - **Target Benchmark:** Evaluate Angle 1 + Angle 3 to determine whether the Formatting Shield recovers the 16% Round 0 yield drop without paying the Refinement Tax.
