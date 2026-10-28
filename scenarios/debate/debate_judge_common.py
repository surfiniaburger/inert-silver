from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


class DebaterScore(BaseModel):
    technical_accuracy: float = 0.5
    logic_soundness: float = 0.5
    evidence_strength: float = 0.5
    total_score: float = 0.5
    critique: str = "Standard scorecard critique" # GEPA: Adjudication of debater performance


class CounterEvidence(BaseModel):
    """Structured, code-anchored defense claim used only for Con decisions."""

    candidate_id: Optional[str] = Field(
        default=None,
        description="Immutable ID of the extractor candidate this receipt is based on (e.g., 'C1'). "
                    "Required when a candidate extractor is used.",
    )
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
    thinking_process: str = Field(default="", description="GEPA: Step-by-step thinking before concluding")
    pro_debater: DebaterScore = Field(default_factory=DebaterScore)
    con_debater: DebaterScore = Field(default_factory=DebaterScore)
    outcome: Literal["pro_win", "con_win", "unresolved"] = "pro_win"
    winner: Optional[Literal["pro_debater", "con_debater"]] = None
    reason: str = Field(default="", description="Short summary")
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
    counter_evidence: Optional[CounterEvidence] = None  # Server-populated from candidate; model should not supply
    con_candidate_id: Optional[str] = Field(
        default=None,
        description="Candidate ID (e.g. 'C1') selected from the provided Con options list. Required if outcome is 'con_win'; must be null if outcome is 'pro_win' or 'unresolved'.",
    )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema = handler(core_schema)
        # Server-populated only: exclude counter_evidence and winner from model-facing schema.
        # The model outputs outcome + con_candidate_id; the runtime derives winner.
        for field in ("counter_evidence", "winner"):
            schema.get("properties", {}).pop(field, None)
            if "required" in schema:
                schema["required"] = [r for r in schema["required"] if r != field]
        if "required" in schema and "outcome" not in schema["required"]:
            schema["required"].append("outcome")
        return schema

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

    @model_validator(mode="before")
    @classmethod
    def _coerce_common_model_variations(cls, data):
        if not isinstance(data, dict):
            return data
        data = dict(data)

        # 1. Alias handling for reason
        if not data.get("reason"):
            for alias in ("verdict_reason", "verdict_reasoning", "reasoning", "summary"):
                if data.get(alias):
                    data["reason"] = str(data[alias])
                    break
            if not data.get("reason"):
                data["reason"] = data.get("thinking_process") or "No explicit summary provided."

        # 2. Alias handling for thinking_process
        if not data.get("thinking_process"):
            if data.get("verdict_reason"):
                data["thinking_process"] = str(data["verdict_reason"])
            elif data.get("reason"):
                data["thinking_process"] = str(data["reason"])
            else:
                data["thinking_process"] = "Adjudication completed without explicit thinking trace."
        elif isinstance(data["thinking_process"], list):
            data["thinking_process"] = " ".join(str(item) for item in data["thinking_process"])

        # 3. Default fallback for pro_debater and con_debater
        if not isinstance(data.get("pro_debater"), dict):
            data["pro_debater"] = {
                "technical_accuracy": 0.5,
                "logic_soundness": 0.5,
                "evidence_strength": 0.5,
                "total_score": 0.5,
                "critique": "Default debater assessment",
            }
        if not isinstance(data.get("con_debater"), dict):
            data["con_debater"] = {
                "technical_accuracy": 0.5,
                "logic_soundness": 0.5,
                "evidence_strength": 0.5,
                "total_score": 0.5,
                "critique": "Default debater assessment",
            }
        return data

    @model_validator(mode="after")
    def _validate_outcome_contract(self):
        # Derive outcome from winner (backward compat with old data)
        if self.outcome == "pro_win" and self.winner == "con_debater":
            self.outcome = "con_win"
        # Derive winner from outcome (new candidate-selection flow)
        if self.outcome == "con_win" and self.winner is None:
            self.winner = "con_debater"
        if self.outcome == "pro_win" and self.winner is None:
            self.winner = "pro_debater"
        if self.outcome == "unresolved":
            self.winner = None
        # Enforce: con_win requires con_candidate_id.  If the model outputs con_win
        # without a candidate ID, downgrade to unresolved (controlled abstention).
        if self.outcome == "con_win":
            if self.con_candidate_id is None:
                self.outcome = "unresolved"
                self.winner = None
                self.counter_evidence = None
        # pro_win and unresolved must not have a candidate
        if self.outcome == "pro_win":
            self.con_candidate_id = None
        if self.outcome == "unresolved":
            self.winner = None
            self.counter_evidence = None
            self.con_candidate_id = None
        return self


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
