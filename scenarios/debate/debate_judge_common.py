from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


class DebaterScore(BaseModel):
    technical_accuracy: float
    logic_soundness: float
    evidence_strength: float
    total_score: float
    critique: str # GEPA: Adjudication of debater performance


class CounterEvidence(BaseModel):
    """Structured, code-anchored defense claim used only for Con decisions."""

    defense_kind: Literal[
        "upper_bound_reject", "lower_bound_reject", "range_guarded_operation",
        "null_check", "equality_reject", "lock_before_shared_access",
    ]
    guard_anchor: str
    guarded_value: str
    protected_operation_anchor: str
    operation_value: str
    enforcement: Literal[
        "reject_before_operation", "operation_inside_safe_branch",
        "validated_value_forwarded", "lock_held_at_operation",
    ]
    invariant: str
    predicate_precondition: str
    value_relation: Literal[
        "guarded_value_equals_operation_value",
        "guarded_value_bounds_offset_plus_width",
        "guarded_value_matches_compared_identity",
        "guarded_value_protects_shared_state",
    ]
    counterfactual: str


class DebateEval(BaseModel):
    thinking_process: str # GEPA: Step-by-step thinking before concluding
    pro_debater: DebaterScore
    con_debater: DebaterScore
    winner: Literal["pro_debater", "con_debater"]
    reason: str # Short summary
    mechanism: str = Field(
        description=(
            "Technical mechanism of the bug. Must include three lines: "
            "'Source anchor: ...', 'Sink anchor: ...', 'Missing guard anchor: ...'"
        )
    )
    counterfactual: str # GEPA: What would change the verdict?
    predicate: str # The claim being judged (must match the run predicate)
    anchors: list[str] = Field(min_length=2) # Concrete evidence hooks (must appear in code)
    verifier_report: str = "not_applicable"
    support_level: Literal["supported", "unsupported", "inconclusive"] = "supported"
    counter_evidence: Optional[CounterEvidence] = None

    @field_validator("counter_evidence", mode="before")
    @classmethod
    def unwrap_single_counter_evidence(cls, value):
        """Accept one legacy list wrapper without weakening the evidence contract.

        Some schema-fallback providers return ``counter_evidence`` as ``[{...}]``
        even though the contract is one object.  Unwrapping exactly one item is
        lossless; empty and multi-item lists remain invalid and therefore cannot
        influence a Con acceptance decision.
        """
        if isinstance(value, list) and len(value) == 1:
            return value[0]
        return value


class VerifierReport(BaseModel):
    thinking_process: str = Field(description="Step-by-step symbolic trace of the vulnerability mechanism.")
    passes_audit: bool = Field(description="True if the mechanism is technically grounded in the anchors and code.")
    anchor_analysis: str = Field(description="Verification of each anchor's role in the exploit (e.g. Source, Sink, Guard).")
    logic_error: Optional[str] = Field(description="Detailed explanation of any hallucination or logical leap found.")
    suggested_correction: Optional[str] = Field(description="Technical advice for the Generator to fix the grounding gap.")


def debate_judge_agent_card(agent_name: str, card_url: str) -> AgentCard:
    skill = AgentSkill(
        id='moderate_and_judge_debate',
        name='Orchestrates and judges debate',
        description='Orchestrate and judge a debate between two agents on a given topic.',
        tags=['debate'],
        examples=["""
{
  "participants": {
    "pro_debater": "https://pro-debater.example.com:443",
    "con_debater": "https://con-debater.example.org:8443"
  },
  "config": {
    "topic": "Should artificial intelligence be regulated?",
    "num_rounds": 3
  }
}
"""]
    )
    agent_card = AgentCard(
        name=agent_name,
        description='Orchestrate and judge a structured debate between pro and con agents on a given topic with multiple rounds of arguments.',
        url=card_url,
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    return agent_card
