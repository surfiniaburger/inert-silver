import argparse
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()

import litellm
import litellm.constants
import litellm.utils
litellm.num_retries = int(os.getenv("LITELLM_NUM_RETRIES", "6"))
litellm.request_timeout = float(os.getenv("LITELLM_REQUEST_TIMEOUT", "300.0"))
litellm.constants.INITIAL_RETRY_DELAY = float(os.getenv("INITIAL_RETRY_DELAY", "5.0"))
litellm.utils.INITIAL_RETRY_DELAY = float(os.getenv("INITIAL_RETRY_DELAY", "5.0"))
litellm.constants.MAX_RETRY_DELAY = float(os.getenv("MAX_RETRY_DELAY", "60.0"))
litellm.utils.MAX_RETRY_DELAY = float(os.getenv("MAX_RETRY_DELAY", "60.0"))

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.models.lite_llm import LiteLlm

from a2a.types import (
    AgentCapabilities,
    AgentCard,
)

def main():
    parser = argparse.ArgumentParser(description="Run the A2A debater agent.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9019, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="External URL to provide in the agent card")
    parser.add_argument("--model", type=str, default=os.getenv("DEBATER_MODEL", "ollama/gpt-oss:20b-cloud"), help="LiteLLM model string to use for the debater")
    parser.add_argument("--instruction", type=str, default="You are a professional debater.", help="System instruction for the debater agent")
    args = parser.parse_args()

    retries = int(os.getenv("LITELLM_NUM_RETRIES", "6"))
    timeout = float(os.getenv("LITELLM_REQUEST_TIMEOUT", "300.0"))
    llm_kwargs = {"model": args.model, "num_retries": retries, "timeout": timeout}
    explicit_api_base = os.getenv("DEBATER_API_BASE")
    api_base = explicit_api_base or (os.getenv("OPENAI_API_BASE") if args.model.startswith("openai/") else None)
    if api_base:
        llm_kwargs["api_base"] = api_base
    explicit_api_key = os.getenv("DEBATER_API_KEY")
    api_key = explicit_api_key or (os.getenv("OPENAI_API_KEY") if args.model.startswith("openai/") else None)
    if api_key:
        llm_kwargs["api_key"] = api_key

    root_agent = Agent(
        name="debater",
        model=LiteLlm(**llm_kwargs),
        description="Participates in a debate.",
        instruction=args.instruction,
    )

    agent_card = AgentCard(
        name="debater",
        description='Participates in a debate.',
        url=args.card_url or f'http://{args.host}:{args.port}/',  # NOSONAR
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[],
    )

    a2a_app = to_a2a(root_agent, agent_card=agent_card)
    uvicorn.run(a2a_app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
