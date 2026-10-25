import asyncio
import time
from uzu import (
    ChatConfig,
    ChatMessage,
    ChatReplyConfig,
    ChatSessionStreamChunk,
    Engine,
    EngineConfig,
)

async def main():
    print("Creating EngineConfig and Engine...")
    engine = await Engine.create(EngineConfig.create())

    print("Locating model trymirai/Qwen3.5-4B-M...")
    model = await engine.model("trymirai/Qwen3.5-4B-M")
    if model is None:
        raise RuntimeError("Model trymirai/Qwen3.5-4B-M not found")

    print("Downloading / Verifying cached model weights (in ~/.cache/mirai)...")
    downloader = await engine.download(model)
    async for update in downloader.iterator():
        pct = int(update.progress * 100)
        if pct % 20 == 0:
            print(f"Progress: {pct}%")

    print("\nStarting Chat Session with C Vulnerability Analysis prompt...")
    session = await engine.chat(model, ChatConfig.create())

    test_prompt = """
Analyze the following C function for security vulnerabilities:
void process_packet(char *data, int len) {
    char buffer[64];
    if (len > 0) {
        strcpy(buffer, data);
    }
}
Identify the vulnerability, source anchor, and sink anchor. Keep your response brief.
"""
    messages = [
        ChatMessage.system().with_text("You are an expert security auditor and formal verification debater."),
        ChatMessage.user().with_text(test_prompt.strip()),
    ]

    t_start = time.time()
    stream = await session.reply_with_stream(messages, ChatReplyConfig.create())
    output_tokens = 0
    latest_text = ""

    async for chunk in stream.iterator():
        if isinstance(chunk, ChatSessionStreamChunk.Replies):
            for reply in chunk.replies:
                if reply.message and reply.message.text:
                    latest_text = reply.message.text
                if hasattr(reply, "stats") and reply.stats:
                    output_tokens = getattr(reply.stats, "tokens_count_output", output_tokens)
        elif isinstance(chunk, ChatSessionStreamChunk.Error):
            print(f"Stream error: {chunk.error}")

    elapsed = time.time() - t_start
    print("\n--- MODEL RESPONSE ---")
    print(latest_text)
    print("----------------------")
    print(f"Elapsed: {elapsed:.3f}s")
    if output_tokens > 0:
        print(f"Output tokens: {output_tokens}")
        print(f"Throughput: {output_tokens / elapsed:.1f} tokens/sec")

if __name__ == "__main__":
    asyncio.run(main())
