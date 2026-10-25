"""
OpenAI-Compatible FastAPI Proxy for Uzu Engine (Apple Silicon / Metal accelerated).
Exposes /v1/chat/completions and /v1/models for LiteLLM, AgentBeats, and OpenAI clients.
"""

import argparse
import asyncio
from contextlib import asynccontextmanager
import json
import logging
import os
import sys
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

import uzu

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("uzu_proxy")

# Global engine and session state
engine: uzu.Engine | None = None
active_model = None
active_session: uzu.ChatSession | None = None
inference_lock = asyncio.Lock()
DEFAULT_MODEL_NAME = "trymirai/Qwen3.5-4B-M"
CHAT_COMPLETION_CHUNK = "chat.completion.chunk"


class ChatMessageIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: str
    content: str | List[Dict[str, Any]] | Any
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str = DEFAULT_MODEL_NAME
    messages: List[ChatMessageIn]
    temperature: float | None = 0.7
    top_p: float | None = 0.9
    top_k: int | None = 40
    max_tokens: int | None = Field(default=None, alias="max_tokens")
    max_completion_tokens: int | None = Field(default=None, alias="max_completion_tokens")
    stream: bool | None = False
    reasoning_effort: str | None = None
    response_format: Any | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, active_model, active_session
    model_id = os.getenv("UZU_MODEL", DEFAULT_MODEL_NAME)
    logger.info("Initializing Uzu Engine on Apple Silicon Metal...")
    engine = await uzu.Engine.create(uzu.EngineConfig.create())

    logger.info("Resolving model: %s", model_id)
    active_model = await engine.model(model_id)
    if active_model is None:
        logger.error("Failed to resolve model '%s' in Uzu registry", model_id)
        sys.exit(1)

    logger.info("Ensuring model weights are cached/ready...")
    downloader = await engine.download(active_model)
    async for update in downloader.iterator():
        pct = int(update.progress * 100)
        if pct % 25 == 0:
            logger.info("Download/Cache verification progress: %d%%", pct)

    ctx_len = int(os.getenv("UZU_CONTEXT_LENGTH", "6144"))
    logger.info("Pre-allocating Uzu ChatSession context with context length: %d...", ctx_len)
    chat_cfg = uzu.ChatConfig.create().with_context_length(uzu.ContextLength.Custom(ctx_len))
    active_session = await engine.chat(active_model, chat_cfg)
    logger.info("Uzu ChatSession pre-allocated successfully. Ready for inference!")
    yield
    logger.info("Shutting down Uzu proxy...")


app = FastAPI(title="Uzu OpenAI Proxy", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _close_brace(depth: int, i: int) -> tuple[int, int | None]:
    depth -= 1
    if depth == 0:
        return depth, i + 1
    return depth, None


def _find_json_end(text: str, start: int) -> int | None:
    depth = 0
    in_string = False
    escaped = False
    for i, ch in enumerate(text[start:], start=start):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth, end = _close_brace(depth, i)
            if end is not None:
                return end
    return None


def extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    end = _find_json_end(text, start)
    return text[start:end] if end is not None else None


def _extract_text_from_list(content: list) -> str:
    parts = []
    for part in content:
        if isinstance(part, dict):
            if part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif "text" in part:
                parts.append(part["text"])
        else:
            parts.append(str(part))
    return "".join(parts)


def extract_text(content: str | List[Dict[str, Any]] | Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return _extract_text_from_list(content)
    return str(content) if content is not None else ""


def _response_format_requests_json(req: ChatCompletionRequest) -> bool:
    if not req.response_format:
        return False
    return (
        isinstance(req.response_format, dict)
        and req.response_format.get("type") in ("json_object", "json_schema")
    )


def _system_prompt_requires_json(req: ChatCompletionRequest) -> bool:
    for m in req.messages:
        if m.role.lower() in ("system", "developer"):
            txt = extract_text(m.content).lower()
            if "valid json" in txt or "output only json" in txt or "json schema" in txt:
                return True
    return False


def model_supports_reasoning_effort(model_name: str) -> bool:
    name = (model_name or "").lower()
    # Non-reasoning models (Muse, Glimmer, Gemma, Llama, Mistral) reject reasoning_effort
    if any(k in name for k in ("muse", "glimmer", "gemma", "llama", "mistral")):
        return False
    # Reasoning-capable models (Qwen, DeepSeek)
    return any(k in name for k in ("qwen", "deepseek", "reasoning"))


def determine_reasoning_effort(req: ChatCompletionRequest) -> uzu.ReasoningEffort:
    model_name = req.model or os.getenv("UZU_MODEL", DEFAULT_MODEL_NAME)
    if not model_supports_reasoning_effort(model_name):
        return uzu.ReasoningEffort.Default

    # Check explicit parameter, defaulting to "disabled" for fast swarm latency
    effort_str = (req.reasoning_effort or os.getenv("UZU_REASONING_EFFORT", "disabled")).lower().strip()
    if effort_str in ("disabled", "none", "off", "0", "false"):
        return uzu.ReasoningEffort.Disabled
    if effort_str in ("default", "enabled", "on", "true", "auto", ""):
        return uzu.ReasoningEffort.Default
    if effort_str in ("low", "medium"):
        # Qwen3.5 in Uzu raises 'Cannot map low/medium/high' on system prompt
        logger.info(f"Reasoning effort '{effort_str}' not natively supported by backend; mapping to Disabled for fast throughput")
        return uzu.ReasoningEffort.Disabled
    if effort_str in ("high", "xhigh"):
        return uzu.ReasoningEffort.Default

    # If response_format requests JSON, disable reasoning to prioritize clean JSON output
    if _response_format_requests_json(req) or _system_prompt_requires_json(req):
        return uzu.ReasoningEffort.Disabled

    return uzu.ReasoningEffort.Disabled


def _make_system_message(text: str, effort: uzu.ReasoningEffort) -> uzu.ChatMessage:
    msg = uzu.ChatMessage.system().with_text(text)
    if effort != uzu.ReasoningEffort.Default:
        msg = msg.with_reasoning_effort(effort)
    return msg


def convert_messages(req: ChatCompletionRequest, force_no_effort: bool = False) -> List[uzu.ChatMessage]:
    converted = []
    effort = uzu.ReasoningEffort.Default if force_no_effort else determine_reasoning_effort(req)
    has_system = False

    for m in req.messages:
        role = m.role.lower().strip()
        text = extract_text(m.content)
        if role in ("system", "developer"):
            has_system = True
            converted.append(_make_system_message(text, effort))
        elif role == "user":
            converted.append(uzu.ChatMessage.user().with_text(text))
        elif role == "assistant":
            converted.append(uzu.ChatMessage.assistant().with_text(text))
        elif role == "tool":
            converted.append(uzu.ChatMessage.tool().with_text(text))
        else:
            converted.append(uzu.ChatMessage.user().with_text(text))

    if not has_system and effort != uzu.ReasoningEffort.Default:
        # Prepend empty system message with specified reasoning effort
        converted.insert(0, uzu.ChatMessage.system().with_text("").with_reasoning_effort(effort))

    return converted


def prune_messages_for_context(req: ChatCompletionRequest) -> List[uzu.ChatMessage]:
    """Prune lengthy messages to recover gracefully from Context overflow."""
    pruned = []
    effort = determine_reasoning_effort(req)
    for m in req.messages:
        role = m.role.lower().strip()
        text = extract_text(m.content)
        # Keep system prompt intact, but trim overly long user/assistant turns if > 3000 chars
        if role not in ("system", "developer") and len(text) > 3000:
            text = text[:1500] + "\n\n[... content truncated to prevent context overflow ...]\n\n" + text[-1500:]

        if role in ("system", "developer"):
            pruned.append(_make_system_message(text, effort))
        elif role == "user":
            pruned.append(uzu.ChatMessage.user().with_text(text))
        elif role == "assistant":
            pruned.append(uzu.ChatMessage.assistant().with_text(text))
        elif role == "tool":
            pruned.append(uzu.ChatMessage.tool().with_text(text))
        else:
            pruned.append(uzu.ChatMessage.user().with_text(text))

    return pruned


def build_reply_config(req: ChatCompletionRequest) -> uzu.ChatReplyConfig:
    temp = req.temperature if req.temperature is not None else 0.7
    if temp <= 0.01:
        method = uzu.SamplingMethod.Greedy()
    else:
        top_p = req.top_p if req.top_p is not None else 0.9
        top_k = req.top_k if req.top_k is not None else 40
        method = uzu.SamplingMethod.Stochastic(
            temperature=float(temp),
            top_k=int(top_k),
            top_p=float(top_p),
            min_p=0.0,
            repetition_penalty=1.0,
            suffix_repetition_length=64,  # Uzu requires suffix_repetition_length >= 1
        )

    pol = uzu.SamplingPolicy.Custom(method)
    reply_cfg = uzu.ChatReplyConfig.create().with_sampling_policy(pol)

    token_limit = req.max_tokens or req.max_completion_tokens
    if token_limit and token_limit > 0:
        reply_cfg = reply_cfg.with_token_limit(int(token_limit))

    return reply_cfg


def normalize_finish_reason(reason: Any) -> str:
    if reason is None:
        return "stop"
    r_str = str(reason).lower()
    if "length" in r_str or "limit" in r_str:
        return "length"
    if "tool" in r_str:
        return "tool_calls"
    return "stop"


@app.get("/health")
@app.get("/")
async def health():
    return {
        "status": "ok",
        "engine": "uzu",
        "model": os.getenv("UZU_MODEL", DEFAULT_MODEL_NAME),
        "session_ready": active_session is not None,
    }


@app.get("/v1/models")
@app.get("/models")
async def list_models():
    model_id = os.getenv("UZU_MODEL", DEFAULT_MODEL_NAME)
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": now,
                "owned_by": "uzu",
            },
            {
                "id": "qwen3.5-4b",
                "object": "model",
                "created": now,
                "owned_by": "uzu",
            },
            {
                "id": "qwen",
                "object": "model",
                "created": now,
                "owned_by": "uzu",
            },
        ],
    }


def _make_chunk_payload(chat_id: str, created_ts: int, model_name: str, delta: dict, finish_reason: str | None) -> dict:
    return {
        "id": chat_id,
        "object": CHAT_COMPLETION_CHUNK,
        "created": created_ts,
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }


async def _stream_replies(
    stream,
    chat_id: str,
    created_ts: int,
    model_name: str,
) -> AsyncGenerator[str, None]:
    prev_reasoning = ""
    prev_text = ""
    async for chunk in stream.iterator():
        if isinstance(chunk, uzu.ChatSessionStreamChunk.Error):
            logger.error("Uzu stream error: %s", chunk.error)
            break
        if not isinstance(chunk, uzu.ChatSessionStreamChunk.Replies):
            continue
        for reply in chunk.replies:
            if not reply.message:
                continue

            # Stream reasoning delta
            cur_reasoning = reply.message.reasoning or ""
            if len(cur_reasoning) > len(prev_reasoning):
                delta_r = cur_reasoning[len(prev_reasoning):]
                prev_reasoning = cur_reasoning
                delta = {"role": "assistant", "reasoning_content": delta_r}
                yield f"data: {json.dumps(_make_chunk_payload(chat_id, created_ts, model_name, delta, None))}\n\n"

            # Stream text delta
            cur_text = reply.message.text or ""
            if len(cur_text) > len(prev_text):
                delta_t = cur_text[len(prev_text):]
                prev_text = cur_text
                delta = {"role": "assistant", "content": delta_t}
                yield f"data: {json.dumps(_make_chunk_payload(chat_id, created_ts, model_name, delta, None))}\n\n"


async def stream_generator(
    req: ChatCompletionRequest,
    chat_messages: List[uzu.ChatMessage],
    reply_cfg: uzu.ChatReplyConfig,
    model_name: str,
    chat_id: str,
    created_ts: int,
) -> AsyncGenerator[str, None]:
    async with inference_lock:
        if active_session is None:
            raise RuntimeError("ChatSession not initialized")

        await active_session.reset()
        try:
            stream = await active_session.reply_with_stream(chat_messages, reply_cfg)
        except RuntimeError as e:
            err_str = str(e)
            if "reasoning_effort" in err_str:
                logger.warning("Backend rejected reasoning_effort (%s). Retrying stream with plain messages...", e)
                fallback_messages = convert_messages(req, force_no_effort=True)
                await active_session.reset()
                stream = await active_session.reply_with_stream(fallback_messages, reply_cfg)
            elif "overflow" in err_str.lower():
                logger.warning("Context overflow detected (%s). Pruning message history and retrying stream...", e)
                pruned_messages = prune_messages_for_context(req)
                await active_session.reset()
                stream = await active_session.reply_with_stream(pruned_messages, reply_cfg)
            else:
                raise

        async for payload_str in _stream_replies(stream, chat_id, created_ts, model_name):
            yield payload_str

        # Final stop chunk
        stop_payload = _make_chunk_payload(chat_id, created_ts, model_name, {}, "stop")
        yield f"data: {json.dumps(stop_payload)}\n\n"
        yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")

    chat_messages = convert_messages(req)
    reply_cfg = build_reply_config(req)
    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())
    model_name = req.model or os.getenv("UZU_MODEL", DEFAULT_MODEL_NAME)

    if req.stream:
        return StreamingResponse(
            stream_generator(req, chat_messages, reply_cfg, model_name, chat_id, created_ts),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async with inference_lock:
        if active_session is None:
            raise HTTPException(status_code=503, detail="ChatSession is not ready")

        t_start = time.time()
        await active_session.reset()
        try:
            replies = await active_session.reply(chat_messages, reply_cfg)
        except RuntimeError as e:
            err_str = str(e)
            if "reasoning_effort" in err_str:
                logger.warning("Backend rejected reasoning_effort (%s). Retrying with plain messages...", e)
                fallback_messages = convert_messages(req, force_no_effort=True)
                await active_session.reset()
                replies = await active_session.reply(fallback_messages, reply_cfg)
            elif "overflow" in err_str.lower():
                logger.warning("Context overflow detected (%s). Pruning message history and retrying...", e)
                pruned_messages = prune_messages_for_context(req)
                await active_session.reset()
                replies = await active_session.reply(pruned_messages, reply_cfg)
            else:
                raise
        elapsed = time.time() - t_start

        if not replies:
            raise HTTPException(status_code=500, detail="No replies returned from Uzu model")

        reply = replies[0]
        text_content = reply.message.text if (reply and reply.message and reply.message.text) else ""
        reasoning_content = reply.message.reasoning if (reply and reply.message and reply.message.reasoning) else ""

        # Determine final content:
        final_content = text_content
        if not final_content:
            # If text is empty (e.g. model put output in reasoning or token limit hit),
            # check if reasoning contains a JSON object
            extracted_json = extract_first_json_object(reasoning_content)
            if extracted_json:
                final_content = extracted_json
            else:
                final_content = reasoning_content or ""

        stats = getattr(reply, "stats", None)
        prompt_tokens = getattr(stats, "tokens_count_input", 0) if stats else 0
        completion_tokens = getattr(stats, "tokens_count_output", 0) if stats else 0
        total_tokens = prompt_tokens + completion_tokens

        logger.info(
            "Completion done: %d tokens in %.3fs (%.1f tok/s)",
            completion_tokens,
            elapsed,
            (completion_tokens / elapsed) if elapsed > 0 else 0,
        )

        message_obj = {
            "role": "assistant",
            "content": final_content,
        }
        if reasoning_content:
            message_obj["reasoning_content"] = reasoning_content

        return {
            "id": chat_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": message_obj,
                    "finish_reason": normalize_finish_reason(getattr(reply, "finish_reason", None)),
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
        }


def main():
    parser = argparse.ArgumentParser(description="Uzu OpenAI-compatible API Proxy")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Uzu model identifier")
    args = parser.parse_args()

    os.environ["UZU_MODEL"] = args.model
    logger.info("Starting Uzu Proxy on http://%s:%d with model %s", args.host, args.port, args.model)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
