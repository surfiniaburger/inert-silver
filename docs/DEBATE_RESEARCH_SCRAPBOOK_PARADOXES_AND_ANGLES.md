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

## 2. Empirical Findings & Paradoxes Uncovered in Chapter 1

### Paradox 1: The "Instruction Overload / Round 0 Anchor Trap"
- **Observation:**
  - In Regime 1 (`baseline_v0`), Gemma-4-E4B debaters receive a concise, uncluttered prompt. They immediately focus on verbatim code extraction from `<Untrusted_Code>`. The **Round 0 first-pass yield was $72.0\%$** (36/50 accepted on attempt 1). Only 14 seeds required Round 1 refinement.
  - In Regime 2 (GEPA evolved prompt `v355`), debaters undergo instruction bloat. The mutated prompts emphasize complex vulnerability reasoning (memory layout invariants, race windows, sanitization bypassing).
  - **The Maladaptive Behavior:** The 4B debaters become "verbose security essayists." They produce elaborate multi-paragraph explanations of vulnerability theory, but in doing so, they frequently **fail to quote two verbatim lines from `<Untrusted_Code>`**.
  - **The Consequence:** Round 0 anchor normalization rejections doubled (from 3–4 up to 8–10 per run). First-pass yield dropped from $72.0\%$ to **$52.0\% - 62.0\%$**, forcing almost half the seeds into Round 1 refinements.

### Paradox 2: The "Refinement Tax" vs. Slicing Token Efficiency
- **Observation:**
  - Slicing code down to the semantic dependency graph saves $\approx 3,000$ to $4,000$ tokens per row at the Judge turn ($21,411$ tokens/row in Regime 1 vs. $25,300$ in unpruned baseline).
  - The live Reflector Agent in Regime 2 is remarkably competent at error recovery: it pinpoints the missing anchors and rescues $42.0\%$ of failed seeds on Round 1.
  - **The Hidden Cost:** Each second-round debate attempt burns $\approx 11,000$ tokens (Pro argument + Con rebuttal + Judge evaluation + Verifier run).
  - **The Net Effect:** Incurring 24 to 26 refinements per run adds $\approx 260,000$ to $286,000$ tokens of overhead, completely consuming the token savings achieved by slicing the Judge context.
  ```
  Regime 1 (Stationary Slicing): 21,411 tokens/accepted row (14 refinements)
  Regime 2 (Online Learning):   23,086 tokens/accepted row (25 refinements)
  Net Delta:                   +1,675 tokens/row due to Refinement Tax
  ```

### Paradox 3: The Non-Monotonic Score Dip ($5.12 \to 4.86 \to 5.79$)
- **Observation:**
  - In `integer_arithmetic`, the Pareto frontier score dropped from $5.12$ (baseline) to $4.86$ (Rep 1) before recovering to $5.79$ (Rep 2).
  - **Mechanism Explanation:** The score is calculated by the GEPA Pareto ledger using `outcome_sign()`:
    $$\text{Reward} = +1.0 \quad (\text{VALID\_ACCEPT}), \quad -0.5 \quad (\text{RETRYABLE\_FAILURE})$$
  - When an evolved prompt causes an initial Round 0 failure on a seed, it incurs a $-0.5$ penalty. Even if the Reflector recovers the seed on Round 1 ($+1.0$), the net episode gain is dampened. Only when subsequent replicates validate the mutation across multiple seeds does the score surge past the baseline.

---

## 3. The Three Architectural Angles (Chapter 2 Design Space)

To systematically eliminate the Round 0 Anchor Trap without sacrificing the cognitive depth of evolved debater prompts, we have formulated three distinct architectural angles:

### Angle 1: The Formatting Shield (Structural Ordering)
- **Hypothesis:** Small 4B models allocate attention primarily to the initial and trailing tokens of their prompt. If the anchor requirement is buried in paragraph 3 of an evolved prompt, it suffers from attention decay.
- **Implementation:** Prepend an immutable, invariant header to all debater outputs before argument generation:
  ```markdown
  ### MANDATORY VERBATIM ANCHOR BLOCK
  [ANCHOR_1]: `<exact line from untrusted code>`
  [ANCHOR_2]: `<exact line from untrusted code>`
  
  ### VULNERABILITY ARGUMENT
  <debater analysis...>
  ```
- **Goal:** Drive Round 0 anchor rejections to 0 without altering the security reasoning text.

### Angle 2: Targeted Syntactic Anchoring
- **Hypothesis:** Debaters fail anchor validation not because they cannot quote code, but because they quote lines outside the AST slice or summarize lines instead of quoting verbatim.
- **Implementation:** The verifier pre-extracts top candidate line numbers from the AST slice (e.g., branch conditions, memory allocations) and explicitly instructs debaters: "Ground your claim on lines [X, Y, or Z]".

### Angle 3: True Pinned Pareto (`--pin-pareto`)
- **Hypothesis:** The live Reflector introduces exploratory noise during production runs. The highest-performing static configuration may be a *frozen snapshot* of the best evolved prompt, operating in zero-mutation stationary inference mode.
- **Implementation:** Benchmark the frozen Pareto frontier ledger across 5 replicates without initializing `ReflectorAgent` or logging mutations to the database.

---

## 4. Current Experimental Lineage Tracker

| Epoch | Replicate / Run ID | Date | Seed | Prompts Used | Yield (%) | Accept/Attempts | Tokens / Accepted Row | Accepted Logic Errors (INV-1) |
|---|---|---|---|---|---|---|---|---|
| **$N=10$ Pilot** | `baseline-001..005` | 2026-09-08 | 42..46 | `baseline_v0` | 74.0% | 37/50 | 25,300 | 0/37 (0.0%) |
| **$N=10$ Pilot** | `pareto-001..005` | 2026-09-09 | 42..46 | GEPA Online | 88.0% | 44/50 | 19,850 | 0/44 (0.0%) |
| **Regime 1 ($N=50$)** | `unrun-sliced-baseline-rep1..5` | 2026-09-11 | 42..46 | `baseline_v0` (Sliced) | 78.4% | 196/250 | 21,411 | 0/196 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep1` | 2026-09-13 | 42 | GEPA Live (Sliced) | 80.0% | 40/50 | 21,844 | 0/40 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep2` | 2026-09-14 | 43 | GEPA Live (Sliced) | 76.0% | 38/50 | 24,329 | 0/38 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep3` | PENDING | 44 | GEPA Live (Sliced) | TBD | TBD | TBD | TBD |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep4` | PENDING | 45 | GEPA Live (Sliced) | TBD | TBD | TBD | TBD |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep5` | PENDING | 46 | GEPA Live (Sliced) | TBD | TBD | TBD | TBD |

---

## 5. Execution Roadmap

1. **Phase 1: Complete Chapter 1 Dataset (Immediate)**
   - Complete Replicates 3, 4, and 5 of Regime 2 (Active Online Learning) using seeds 44, 45, and 46.
   - Total episodes across Regime 2 will reach $N=250$, matching Regime 1 exactly.
   - Generate comparative meta-analysis: Stationary Baseline vs. Active Online Learning.
   - Commit and push all data to `origin/feat/asymmetric-injection-seed-safety`.

2. **Phase 2: Launch Chapter 2 (Interventions)**
   - Implement Angle 1 (Formatting Shield) in debater template generation.
   - Run benchmark on Angle 1 + Angle 3 (True Pinned Pareto).
   - Measure reduction in the Refinement Tax and Round 0 Anchor drop rate.
