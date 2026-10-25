import asyncio
import subprocess
import sys
import time
from uzu import (
    ChatConfig,
    ChatMessage,
    ChatReplyConfig,
    ChatSessionStreamChunk,
    Engine,
    EngineConfig,
)

MODEL_ID = "trymirai/Muse-Glimmer-30B-M"


async def main():
    print("Creating EngineConfig and Engine...")
    engine = await Engine.create(EngineConfig.create())

    print(f"Locating model {MODEL_ID}...")
    model = await engine.model(MODEL_ID)
    if model is None:
        raise RuntimeError(
            f"Model '{MODEL_ID}' not found. "
            "Ensure 'brew install mirai' ran successfully and uzu is up to date."
        )

    print(
        "Downloading / Verifying cached model weights "
        "(~16.6 GB in ~/.cache/mirai — first run may take several minutes)..."
    )
    # The uzu SDK download iterator silently exits early for models not yet cached.
    # Pre-flight with the mirai CLI, which handles chunked HTTP download correctly.
    # stderr is suppressed: older mirai builds print "unrecognized subcommand" noise.
    try:
        result = subprocess.run(
            ["mirai", "download", "--model", MODEL_ID],
            check=False,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            # Older mirai versions don't have a 'download' subcommand; fall back
            # to the SDK iterator which at least verifies an already-cached model.
            print("  (using SDK iterator — model already cached or download not needed)")
            downloader = await engine.download(model)
            last_pct = -1
            t_dl = time.time()
            async for update in downloader.iterator():
                pct = int(update.progress * 100)
                if pct != last_pct and pct % 5 == 0:
                    print(f"  Progress: {pct}%  ({time.time() - t_dl:.0f}s)", flush=True)
                    last_pct = pct
            print(f"  SDK iterator done in {time.time() - t_dl:.1f}s")
    except FileNotFoundError:
        print(
            "ERROR: 'mirai' CLI not found. Install it first:\n"
            "  brew install mirai\n"
            "Then re-run this script.",
            file=sys.stderr,
        )
        sys.exit(1)


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
