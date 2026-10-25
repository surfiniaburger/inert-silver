"""Semantic Predicate Validator and Benchmark Audit Tool.

Audits whether vulnerability predicates and proof requirements are mathematically
and semantically sound under C/POSIX semantics, independent of historical oracle labels.

Identifies:
1. Flawed Exploit Mechanisms (e.g. asserting rename() overwrites symlink targets)
2. Upstream Preempted Conditions (e.g. integer overflow blocked by upstream INT_MAX guards)
3. Context Deficiencies (missing struct definitions, macros, or caller guarantees)
4. Label/Code Discrepancies (historical CVE tags with non-vulnerable code slices)
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field

# Ensure project root is in sys.path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
debate_dir = str(Path(__file__).resolve().parent)
if debate_dir not in sys.path:
    sys.path.insert(0, debate_dir)

from agentbeats.replay import ReplayManager
from agentbeats.structured_output import call_structured

os.environ.setdefault("VERTEXAI_LOCATION", "global")
if not os.environ.get("VERTEXAI_PROJECT"):
    try:
        import subprocess
        _proj = subprocess.check_output(["gcloud", "config", "get-value", "project"], text=True, stderr=subprocess.DEVNULL).strip()
        if _proj:
            os.environ["VERTEXAI_PROJECT"] = _proj
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("audit_predicates")


class PredicateSoundnessCategory(str, Enum):
    SOUND = "sound"
    """The predicate describes a valid, technically sound mechanism that is reproducible in the code."""

    FLAWED_MECHANISM = "flawed_mechanism"
    """The file may be historically vulnerable or flawed, but the specific predicate mechanism
    is technically invalid, impossible, or contrary to language/POSIX semantics (e.g. Seed 51 rename)."""

    UPSTREAM_PREEMPTED = "upstream_preempted"
    """The claimed vulnerability cannot be triggered because an upstream guard, bounds check,
    or validation check neutralizes the precondition (e.g. Seed 46 INT_MAX check)."""

    CONTEXT_DEFICIENT = "context_deficient"
    """The snippet is truncated or missing external caller context, types, or macro definitions,
    making it impossible to definitively prove or refute from the code provided."""

    LABEL_MISMATCH = "label_mismatch"
    """The code is safe but labelled vulnerable, or vulnerable but labelled safe, with no ambiguity."""


class PredicateAuditResult(BaseModel):
    category: PredicateSoundnessCategory = Field(
        description="The primary classification of the predicate's technical validity."
    )
    is_sound: bool = Field(
        description="True ONLY if the exact predicate mechanism is technically valid and satisfiable."
    )
    precondition_satisfiable: bool = Field(
        description="Whether an attacker or caller can satisfy the input preconditions to reach the flaw."
    )
    upstream_guards_found: List[str] = Field(
        default_factory=list,
        description="List of specific code expressions, if-guards, or sanitizers that neutralize or affect the claim."
    )
    semantic_flaw_analysis: str = Field(
        description="Detailed technical breakdown of why the predicate is sound or flawed under C/POSIX standards."
    )
    recommended_predicate: Optional[str] = Field(
        default=None,
        description="If flawed or preempted, the corrected technical predicate reflecting actual code behavior."
    )
    grounded_oracle: str = Field(
        description="'vulnerable' if the code contains a demonstrable flaw; 'safe' if the code is secure against the claim."
    )


AUDITOR_SYSTEM_PROMPT = """<role>You are a Principal Security Researcher and Formal Verification Specialist.</role>
<task>
You are conducting a strict, adversarial semantic audit of a vulnerability benchmark seed.
You are given:
1. Target C/C++ source code.
2. The benchmark oracle label ('vulnerable' or 'safe').
3. The exact claimed vulnerability predicate.
4. Proof requirements and evidence hooks supplied to the debater agents.

Your mission is NOT to simply agree with the benchmark label.
You must determine whether the EXACT PREDICATE MECHANISM is technically sound, provable, and defensible under C language and POSIX specifications.

Check for these specific defect categories:
1. FLAWED_MECHANISM: The code may have historical bugs, but the CLAIMED mechanism is physically or semantically impossible (e.g., claiming rename() follows destination symlinks, or claiming NULL dereference on guaranteed non-NULL pointers).
2. UPSTREAM_PREEMPTED: An upstream check (e.g., `if (len > INT_MAX) error()`) neutralizes the flaw before arithmetic or memory operations occur.
3. CONTEXT_DEFICIENT: Missing definitions, types, or external caller contracts make it unprovable from the provided snippet.
4. LABEL_MISMATCH: The oracle label directly contradicts the demonstrable behavior of the snippet.
5. SOUND: The exact vulnerability mechanism described in the predicate is technically defensible, reachable, and provable from this code.

Be extremely rigorous. Cite exact language specifications (ISO C99/C11), POSIX system call semantics, and verbatim code lines.
</task>
"""


async def audit_predicate(
    code: str,
    predicate: str,
    original_safety: str,
    gepa_info: Optional[Dict[str, Any]] = None,
    language: str = "c",
    model: str = "vertex_ai/gemini-3.8-flash",
    replay_manager: Optional[ReplayManager] = None,
) -> PredicateAuditResult:
    """Audit a single seed predicate against source code and language semantics."""
    if replay_manager is None:
        # Default ephemeral replay manager in record mode
        replay_manager = ReplayManager.from_config(
            run_id="audit-ephemeral",
            seed=42,
            cassette_path="artifacts/cassettes/predicate_audit.json",
            mode="record",
        )

    hooks = (gepa_info or {}).get("evidence_hooks", [])
    proof_reqs = (gepa_info or {}).get("proof_requirements", "")

    user_prompt = f"""Language: {language}
Benchmark Oracle Label: {original_safety.upper()}

Claimed Predicate:
"{predicate}"

Evidence Hooks:
{json.dumps(hooks, indent=2)}

Proof Requirements:
{proof_reqs}

Source Code:
```c
{code}
```
"""

    return await call_structured(
        replay_manager=replay_manager,
        model=model,
        messages=[
            {"role": "system", "content": AUDITOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        schema_name="predicate_audit_result",
        schema_model=PredicateAuditResult,
        stage="predicate_audit",
    )


def _read_seed_lines(path: str) -> List[str]:
    """Read non-empty stripped lines from a seed JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    """Synchronously serialize records to a JSONL file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as out_f:
        for r in records:
            out_f.write(json.dumps(r) + "\n")


def _write_report(path: str, content: str) -> None:
    """Synchronously write markdown report content to file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as rf:
        rf.write(content)


async def run_audit_batch(
    seeds_path: str,
    output_path: str,
    model: str,
    indices: Optional[List[int]] = None,
    limit: Optional[int] = None,
    cassette_path: str = "artifacts/cassettes/predicate_audit_batch.json",
) -> List[Dict[str, Any]]:
    """Run predicate audit over a batch of seeds from a JSONL file."""
    replay_mgr = ReplayManager.from_config(
        run_id="audit-batch-001",
        seed=42,
        cassette_path=cassette_path,
        mode="record",
    )

    if not os.path.exists(seeds_path):
        raise FileNotFoundError(f"Seeds file not found at: {seeds_path}")

    lines = await asyncio.to_thread(_read_seed_lines, seeds_path)

    target_lines = []
    for idx, line in enumerate(lines, start=1):
        if indices and idx not in indices:
            continue
        target_lines.append((idx, line))
        if limit and len(target_lines) >= limit:
            break

    logger.info(f"Loaded {len(target_lines)} target seeds for predicate audit using model: {model}")

    results = []
    for idx, line_str in target_lines:
        seed_data = json.loads(line_str)
        code = seed_data.get("topic", "")
        predicate = seed_data.get("predicate", "")
        original_safety = seed_data.get("original_safety", "unknown")
        gepa_info = seed_data.get("gepa_info", {})
        language = seed_data.get("language", "c")

        logger.info(f"Auditing Seed {idx} [Oracle: {original_safety}] | Predicate: {predicate[:60]}...")
        try:
            audit_result = await audit_predicate(
                code=code,
                predicate=predicate,
                original_safety=original_safety,
                gepa_info=gepa_info,
                language=language,
                model=model,
                replay_manager=replay_mgr,
            )
            entry = {
                "seed_index": idx,
                "original_safety": original_safety,
                "predicate": predicate,
                "audit": audit_result.model_dump(),
                "topic": code,
                "anchors": seed_data.get("anchors", []),
                "gepa_info": gepa_info,
            }
            results.append(entry)
            logger.info(
                f"-> Seed {idx} Result: {audit_result.category.value.upper()} "
                f"(Sound: {audit_result.is_sound}, Grounded: {audit_result.grounded_oracle})"
            )
        except Exception as e:
            logger.error(f"Failed to audit seed {idx}: {e}")
            entry = {
                "seed_index": idx,
                "original_safety": original_safety,
                "predicate": predicate,
                "error": str(e),
            }
            results.append(entry)

    # Save to JSONL
    if output_path:
        await asyncio.to_thread(_write_jsonl, output_path, results)
        logger.info(f"Audited results saved to: {output_path}")

    return results


def format_markdown_report(results: List[Dict[str, Any]]) -> str:
    """Generate a clean Markdown audit summary report from batch results."""
    md = [
        "# Predicate-Validation Audit Report",
        "",
        "| Seed | Oracle Label | Grounded Oracle | Category | Is Sound? | Upstream Guards | Key Semantic Finding |",
        "| :---: | :---: | :---: | :---: | :---: | :--- | :--- |",
    ]

    cat_counts = {}
    for r in results:
        seed_idx = r.get("seed_index")
        oracle = r.get("original_safety")
        audit = r.get("audit")
        if not audit:
            md.append(f"| **{seed_idx}** | {oracle} | ERROR | `error` | False | - | {r.get('error')} |")
            continue

        category = audit.get("category")
        cat_counts[category] = cat_counts.get(category, 0) + 1
        grounded = audit.get("grounded_oracle")
        is_sound = "✅ Yes" if audit.get("is_sound") else "❌ No"
        guards = "<br/>".join([f"`{g}`" for g in audit.get("upstream_guards_found", [])[:2]]) or "None"
        finding = audit.get("semantic_flaw_analysis", "").replace("\n", " ")
        if len(finding) > 120:
            finding = finding[:117] + "..."

        md.append(f"| **{seed_idx}** | `{oracle}` | `{grounded}` | `{category}` | {is_sound} | {guards} | {finding} |")

    md.extend([
        "",
        "### Category Breakdown",
        "",
    ])
    for cat, count in cat_counts.items():
        md.append(f"- **`{cat}`**: {count} ({count / max(len(results), 1):.1%})")

    return "\n".join(md)


async def main():
    parser = argparse.ArgumentParser(description="Audit vulnerability seed predicates against C/POSIX semantics.")
    parser.add_argument("--seeds", default="scenarios/debate/cve_seeds_benchmark_50.jsonl", help="Path to input seed JSONL")
    parser.add_argument("--output", default="artifacts/predicate_audit_results.jsonl", help="Output JSONL path")
    parser.add_argument("--report-out", default="", help="Optional Markdown report output path")
    parser.add_argument("--model", default="vertex_ai/gemini-3.8-flash", help="Auditor model")
    parser.add_argument("--indices", default="", help="Comma-separated seed indices (e.g. '46,51')")
    parser.add_argument("--limit", type=int, default=0, help="Max seeds to audit")
    parser.add_argument("--cassette", default="artifacts/cassettes/predicate_audit.json", help="Cassette path")
    args = parser.parse_args()

    target_indices = [int(i.strip()) for i in args.indices.split(",") if i.strip()] if args.indices else None
    results = await run_audit_batch(
        seeds_path=args.seeds,
        output_path=args.output,
        model=args.model,
        indices=target_indices,
        limit=args.limit or None,
        cassette_path=args.cassette,
    )

    report_md = format_markdown_report(results)
    if args.report_out:
        await asyncio.to_thread(_write_report, args.report_out, report_md)
        logger.info(f"Markdown report written to: {args.report_out}")
    else:
        print("\n" + report_md + "\n")


if __name__ == "__main__":
    asyncio.run(main())

