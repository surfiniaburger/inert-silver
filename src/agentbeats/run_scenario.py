import argparse
import asyncio
import os, sys, time, subprocess, shlex, signal
from pathlib import Path
import tomllib
import httpx
from dotenv import load_dotenv

from a2a.client import A2ACardResolver


load_dotenv(override=False)


async def wait_for_agents(cfg: dict) -> None:
    """Wait for all agents to be healthy and responding."""
    endpoints = []

    # Collect all endpoints to check
    for p in cfg["participants"]:
        if p.get("cmd"):  # Only check if there's a command (agent to start)
            endpoints.append(f"http://{p['host']}:{p['port']}")  # NOSONAR

    if cfg["green_agent"].get("cmd"):  # Only check if there's a command (host to start)
        endpoints.append(f"http://{cfg['green_agent']['host']}:{cfg['green_agent']['port']}")  # NOSONAR

    if not endpoints:
        return  # No agents to wait for

    print(f"Waiting for {len(endpoints)} agent(s) to be ready...")

    async def check_endpoint(endpoint: str) -> bool:
        """Check if an endpoint is responding by fetching the agent card."""
        try:
            async with asyncio.timeout(2), httpx.AsyncClient() as client:  # NOSONAR
                resolver = A2ACardResolver(httpx_client=client, base_url=endpoint)
                await resolver.get_agent_card()
                return True
        except Exception:
            # Any exception means the agent is not ready
            return False

    while True:
        ready_count = 0
        for endpoint in endpoints:
            if await check_endpoint(endpoint):
                ready_count += 1

        if ready_count == len(endpoints):
            return

        print(f"  {ready_count}/{len(endpoints)} agents ready, waiting...")
        await asyncio.sleep(1)


def parse_toml(scenario_path: str | Path) -> dict:
    path = Path(scenario_path)
    if not path.exists():
        print(f"Error: Scenario file not found: {path}")
        sys.exit(1)

    data = tomllib.loads(path.read_text())

    def host_port(ep: str):
        s = (ep or "")
        s = s.replace("http://", "").replace("https://", "")
        s = s.split("/", 1)[0]
        host, port = s.split(":", 1)
        return host, int(port)

    green_ep = data.get("green_agent", {}).get("endpoint", "")
    g_host, g_port = host_port(green_ep)
    green_cmd = data.get("green_agent", {}).get("cmd", "")

    parts = []
    for p in data.get("participants", []):
        if isinstance(p, dict) and "endpoint" in p:
            h, pt = host_port(p["endpoint"])
            parts.append({
                "role": str(p.get("role", "")),
                "host": h,
                "port": pt,
                "cmd": p.get("cmd", "")
            })

    cfg = data.get("config", {})
    return {
        "green_agent": {"host": g_host, "port": g_port, "cmd": green_cmd},
        "participants": parts,
        "config": cfg,
    }


def _build_base_env() -> dict[str, str]:
    parent_bin = str(Path(sys.executable).parent)
    base_env = os.environ.copy()
    base_env["PATH"] = parent_bin + os.pathsep + base_env.get("PATH", "")
    return base_env


def _start_process(cmd: str, env: dict[str, str], sink: int | None) -> subprocess.Popen | None:
    cmd_args = shlex.split(cmd)
    if not cmd_args:
        return None
    return subprocess.Popen(
        cmd_args,
        env=env,
        stdout=sink,
        stderr=sink,
        text=True,
        start_new_session=True,
    )


def _start_all_agents(
    cfg: dict, env: dict[str, str], sink: int | None, procs: list[subprocess.Popen] | None = None
) -> list[subprocess.Popen]:
    if procs is None:
        procs = []
    for p in cfg["participants"]:
        if p.get("cmd"):
            print(f"Starting {p['role']} at {p['host']}:{p['port']}")
            proc = _start_process(p["cmd"], env, sink)
            if proc:
                procs.append(proc)

    green = cfg["green_agent"]
    if green.get("cmd"):
        print(f"Starting green agent at {green['host']}:{green['port']}")
        proc = _start_process(green["cmd"], env, sink)
        if proc:
            procs.append(proc)
    return procs


def _kill_processes(procs: list[subprocess.Popen], sig: int) -> None:
    for p in procs:
        try:
            os.killpg(p.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass
        if p.poll() is not None:
            try:
                p.wait(timeout=0.1)
            except Exception:
                pass


def _terminate_processes(procs: list[subprocess.Popen]) -> None:
    print("\nShutting down...")
    _kill_processes(procs, signal.SIGTERM)
    time.sleep(1)
    _kill_processes(procs, signal.SIGKILL)


def _serve_until_exit(procs: list[subprocess.Popen]) -> None:
    while True:
        for proc in procs:
            if proc.poll() is not None:
                print(f"Agent exited with code {proc.returncode}")
                return
        time.sleep(0.5)


def _run_client(scenario_path: str, env: dict[str, str], procs: list[subprocess.Popen]) -> None:
    client_proc = subprocess.Popen(
        [sys.executable, "-m", "agentbeats.client_cli", scenario_path],
        env=env,
        start_new_session=True,
    )
    procs.append(client_proc)
    client_proc.wait()


async def _ready_wrapper(cfg: dict) -> None:
    async with asyncio.timeout(30):
        await wait_for_agents(cfg)


def _wait_for_ready(cfg: dict) -> bool:
    try:
        asyncio.run(_ready_wrapper(cfg))
        return True
    except TimeoutError:
        print("Timeout: Not all agents became ready after 30s")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run agent scenario")
    parser.add_argument("scenario", help="Path to scenario TOML file")
    parser.add_argument("--show-logs", action="store_true",
                        help="Show agent stdout/stderr")
    parser.add_argument("--serve-only", action="store_true",
                        help="Start agent servers only without running evaluation")
    args = parser.parse_args()

    cfg = parse_toml(args.scenario)
    sink = None if args.show_logs or args.serve_only else subprocess.DEVNULL
    base_env = _build_base_env()

    procs: list[subprocess.Popen] = []
    try:
        _start_all_agents(cfg, base_env, sink, procs=procs)

        if not _wait_for_ready(cfg):
            print("Error: Not all agents became ready. Exiting.")
            sys.exit(1)

        print("Agents started. Press Ctrl+C to stop.")
        if args.serve_only:
            _serve_until_exit(procs)
        else:
            _run_client(args.scenario, base_env, procs)

    except KeyboardInterrupt:
        pass

    finally:
        _terminate_processes(procs)


if __name__ == "__main__":
    main()
