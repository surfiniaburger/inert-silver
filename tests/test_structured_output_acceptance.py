from typing import Any, Optional
import pytest
from pydantic import BaseModel, Field

from src.agentbeats.structured_output import call_structured


class SampleSchema(BaseModel):
    verdict: str = Field(description="Decision verdict")
    score: int = Field(default=0, description="Score 0-10")


class MockChoiceMessage:
    def __init__(self, content: Optional[str] = "", reasoning_content: Optional[str] = ""):
        self.content = content
        self.reasoning_content = reasoning_content


class MockChoice:
    def __init__(self, message: MockChoiceMessage):
        self.message = message


class MockResponse:
    def __init__(self, content: Optional[str] = "", reasoning_content: Optional[str] = ""):
        self.choices = [MockChoice(MockChoiceMessage(content, reasoning_content))]


class MockReplayManager:
    def __init__(self, responses: list[Any]):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def acompletion(self, **kwargs) -> Any:
        self.calls.append(kwargs)
        if not self.responses:
            raise RuntimeError("No more mock responses available")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def record_event(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_call_structured_primary_success():
    """Characterization Test: Valid JSON in primary call parses without repair."""
    replay = MockReplayManager([
        MockResponse('{"verdict": "ACCEPTED", "score": 9}')
    ])
    result = await call_structured(
        replay_manager=replay,
        model="mock-model",
        messages=[{"role": "user", "content": "test"}],
        schema_name="SampleSchema",
        schema_model=SampleSchema,
    )
    assert result.verdict == "ACCEPTED"
    assert result.score == 9
    assert len(replay.calls) == 1


@pytest.mark.asyncio
async def test_call_structured_extracts_from_reasoning_content():
    """Characterization Test: When content is empty but reasoning_content has JSON, parses it."""
    replay = MockReplayManager([
        MockResponse(content="", reasoning_content='{"verdict": "REASONING_OK", "score": 8}')
    ])
    result = await call_structured(
        replay_manager=replay,
        model="mock-model",
        messages=[{"role": "user", "content": "test"}],
        schema_name="SampleSchema",
        schema_model=SampleSchema,
    )
    assert result.verdict == "REASONING_OK"
    assert result.score == 8


@pytest.mark.asyncio
async def test_call_structured_handles_none_content_without_attribute_error():
    """Characterization Test: content=None must not crash with AttributeError."""
    replay = MockReplayManager([
        MockResponse(content=None, reasoning_content='{"verdict": "NONE_CONTENT_OK", "score": 7}')
    ])
    result = await call_structured(
        replay_manager=replay,
        model="mock-model",
        messages=[{"role": "user", "content": "test"}],
        schema_name="SampleSchema",
        schema_model=SampleSchema,
    )
    assert result.verdict == "NONE_CONTENT_OK"
    assert result.score == 7


@pytest.mark.asyncio
async def test_call_structured_repair_succeeds_on_malformed_primary():
    """Characterization Test: Primary returns markdown text; repair converts to valid JSON."""
    replay = MockReplayManager([
        MockResponse(content="I think the verdict is ACCEPTED with score 10 but not json"),
        MockResponse(content='{"verdict": "REPAIRED", "score": 10}'),
    ])
    result = await call_structured(
        replay_manager=replay,
        model="mock-model",
        messages=[{"role": "user", "content": "test"}],
        schema_name="SampleSchema",
        schema_model=SampleSchema,
        repair_on_fail=True,
    )
    assert result.verdict == "REPAIRED"
    assert result.score == 10
    assert len(replay.calls) == 2


@pytest.mark.asyncio
async def test_call_structured_repair_empty_schema_falls_back_unconstrained():
    """
    Acceptance Test for Trailing Bug:
    When Ollama schema mode returns empty string on repair,
    system must fall back to unconstrained repair rather than crashing Pydantic with EOF.
    """
    replay = MockReplayManager([
        MockResponse(content="Not valid json"),  # Primary call
        MockResponse(content=""),                 # Repair with response_format=schema returns empty
        MockResponse(content='{"verdict": "UNCONSTRAINED_REPAIRED", "score": 5}'),  # Unconstrained fallback
    ])
    result = await call_structured(
        replay_manager=replay,
        model="mock-model",
        messages=[{"role": "user", "content": "test"}],
        schema_name="SampleSchema",
        schema_model=SampleSchema,
        repair_on_fail=True,
    )
    assert result.verdict == "UNCONSTRAINED_REPAIRED"
    assert result.score == 5
    assert len(replay.calls) == 3
    # Check that the 3rd call did not have response_format
    assert "response_format" not in replay.calls[2]


@pytest.mark.asyncio
async def test_call_structured_all_empty_raises_descriptive_error():
    """
    Acceptance Test for Trailing Bug:
    If primary and all repair retries return empty strings,
    raise a descriptive ValueError instead of Pydantic EOF validation error.
    """
    replay = MockReplayManager([
        MockResponse(content=""),  # Primary empty
        MockResponse(content=""),  # Retry empty
        MockResponse(content=""),  # Repair empty
        MockResponse(content=""),  # Unconstrained repair empty
    ])
    with pytest.raises(ValueError) as excinfo:
        await call_structured(
            replay_manager=replay,
            model="mock-model",
            messages=[{"role": "user", "content": "test"}],
            schema_name="SampleSchema",
            schema_model=SampleSchema,
            repair_on_fail=True,
        )
    assert "empty completion" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_call_structured_salvages_truncated_json():
    """Acceptance Test: If completion is truncated before closing braces, balances and validates."""
    truncated = '{"verdict": "ACCEPTED", "score": 9'  # missing closing brace
    replay = MockReplayManager([
        MockResponse(content=truncated)
    ])
    result = await call_structured(
        replay_manager=replay,
        model="mock-model",
        messages=[{"role": "user", "content": "test"}],
        schema_name="SampleSchema",
        schema_model=SampleSchema,
    )
    assert result.verdict == "ACCEPTED"
    assert result.score == 9


@pytest.mark.asyncio
async def test_call_structured_extracts_from_thinking():
    """Acceptance Test: If content is empty but message.thinking has JSON, parses it."""
    class MockThinkingMessage:
        def __init__(self, content="", thinking=""):
            self.content = content
            self.reasoning_content = ""
            self.thinking = thinking

    class MockThinkingResponse:
        def __init__(self, thinking=""):
            self.choices = [MockChoice(MockThinkingMessage(content="", thinking=thinking))]

    replay = MockReplayManager([
        MockThinkingResponse(thinking='{"verdict": "THINKING_OK", "score": 10}')
    ])
    result = await call_structured(
        replay_manager=replay,
        model="mock-model",
        messages=[{"role": "user", "content": "test"}],
        schema_name="SampleSchema",
        schema_model=SampleSchema,
    )
    assert result.verdict == "THINKING_OK"
    assert result.score == 10
