#!/usr/bin/env python3
"""Sample Docker cgroup v2 working set for 24 hours without changing the bot."""
import argparse
import json
import re
from decimal import Decimal
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

def docker(*args):
    result = subprocess.run(["rtk", "proxy", "docker", *args], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Docker observation failed")
    return result.stdout, result.stderr

def sample(container):
    state, _ = docker("inspect", "--format", "{{json .State}}", container)
    state = json.loads(state)
    if not state["Running"]:
        raise RuntimeError("candidate container stopped")
    # Docker reports Linux working set (usage minus inactive file cache).
    # Observe from the host: a scratch image has no cat or shell.
    usage, _ = docker("stats", "--no-stream", "--format", "{{.MemUsage}}", container)
    amount = usage.split("/", 1)[0].strip()
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*(B|kB|MB|GB|KiB|MiB|GiB)", amount)
    if not match:
        raise ValueError("Unrecognised Docker memory units")
    units = {"B": 1, "kB": 1000, "MB": 1000000, "GB": 1000000000,
             "KiB": 1024, "MiB": 1048576, "GiB": 1073741824}
    working_set = int(Decimal(match[1]) * units[match[2]])
    stdout, stderr = docker("logs", "--tail", "100", container)
    phase = None
    success = None
    latest_poll = None
    for line in (stdout + "\n" + stderr).splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        fields = entry.get("fields", {})
        if fields.get("phase"):
            phase = fields["phase"]
        if fields.get("message") == "poll completed":
            success = fields.get("success")
            latest_poll = entry.get("timestamp")
        if fields.get("message") == "poll failed":
            success = False
            latest_poll = entry.get("timestamp")
    return {
        "at": datetime.now(timezone.utc).isoformat(),
        "working_set_bytes": working_set, "phase": phase,
        "latest_poll_success": success, "latest_poll_at": latest_poll,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("container")
    parser.add_argument("output", type=Path)
    parser.add_argument("--hours", type=float, default=24)
    args = parser.parse_args()
    if args.hours <= 0:
        parser.error("--hours must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    image, _ = docker("inspect", "--format", "{{.Image}}", args.container)
    started = time.monotonic()
    samples = 0
    peak = idle_peak = 0
    failures = []
    successful_polls = set()
    with (args.output / "samples.ndjson").open("x") as evidence:
        try:
            while True:
                observed = sample(args.container)
                observed["elapsed_seconds"] = time.monotonic() - started
                evidence.write(json.dumps(observed) + "\n")
                evidence.flush()
                samples += 1
                peak = max(peak, observed["working_set_bytes"])
                if observed["phase"] == "idle" and observed["elapsed_seconds"] >= 60:
                    idle_peak = max(idle_peak, observed["working_set_bytes"])
                if observed["latest_poll_success"] and observed["latest_poll_at"]:
                    successful_polls.add(observed["latest_poll_at"])
                elif observed["latest_poll_success"] is False:
                    failures.append("poll failure observed")
                    break
                if peak > 64 * 1024 * 1024 or idle_peak > 32 * 1024 * 1024:
                    failures.append("memory threshold exceeded")
                    break
                if observed["elapsed_seconds"] >= args.hours * 3600:
                    break
                time.sleep(15)
        except (RuntimeError, subprocess.TimeoutExpired, ValueError, KeyError) as error:
            failures.append(str(error))
    elapsed = time.monotonic() - started
    passed = (not failures and elapsed >= 86400 and idle_peak > 0 and len(successful_polls) >= 140)
    summary = {
        "container": args.container, "image_id": image.strip(), "duration_seconds": elapsed,
        "samples": samples, "successful_polls": len(successful_polls),
        "idle_peak_bytes": idle_peak, "peak_bytes": peak, "failures": failures,
        "passed_24h_gate": passed,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
