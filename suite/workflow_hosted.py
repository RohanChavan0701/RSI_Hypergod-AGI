"""Run a paired stateful workflow evaluation on NVIDIA NIM."""

import argparse
import json
import os
from pathlib import Path

import httpx

from hgi.cli import load_env
from suite.workflow_stateful import Request


MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"
ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
TASKS = (("v1", "east"), ("v2", None), ("v1", "west"))
MAX_TURNS = 4


def evaluate(client, key, version, destination, memory):
    request = Request(version, destination)
    messages = [{"role": "system", "content": (
        "Complete the simulated shipment. Return exactly one JSON object "
        'with key "tool" and value clarify, request_approval, or execute. '
        "Clarify obtains a missing destination. Request_approval obtains approval."
        + memory
    )}]
    tokens = 0
    outcome = "turn_limit"
    for _ in range(MAX_TURNS):
        messages.append({"role": "user", "content": json.dumps({
            "version": version, "destination": request.destination, "approved": request.approved,
            "last_event": request.events[-1] if request.events else None,
        })})
        try:
            response = client.post(ENDPOINT, headers={"Authorization": f"Bearer {key}"}, json={
                "model": MODEL, "temperature": 0, "max_tokens": 1024, "messages": messages,
            })
            response.raise_for_status()
        except httpx.TimeoutException:
            outcome = "timeout"
            break
        except httpx.HTTPStatusError as error:
            outcome = f"http_{error.response.status_code}"
            break
        except httpx.RequestError:
            outcome = "transport_error"
            break
        try:
            body = response.json()
            tokens += (body.get("usage") or {}).get("total_tokens") or 0
            reply = body["choices"][0]["message"]["content"]
            parsed = json.loads(reply)
            tool = parsed["tool"]
            if set(parsed) != {"tool"} or tool not in ("clarify", "request_approval", "execute"):
                raise ValueError
        except (ValueError, KeyError, IndexError, TypeError):
            outcome = "invalid_output"
            break
        messages.append({"role": "assistant", "content": reply})
        request.call(tool)
        if request.violations:
            outcome = "invalid_action"
            break
        if request.executed:
            outcome = "success"
            break
    return {"version": version, "initial_destination": destination, "outcome": outcome,
            "violations": request.violations, "tokens": tokens, "trace": request.events}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    load_env()
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        parser.error("Configure NVIDIA_API_KEY locally")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {"model": MODEL, "max_turns": MAX_TURNS, "temperature": 0, "rows": []}
    with args.out.open("x", encoding="utf-8") as stream, httpx.Client(timeout=45) as client:
        for index, (version, destination) in enumerate(TASKS):
            for arm, memory in (
                ("stale", " Stored rule: execute once the destination is known."),
                ("version-aware", " Stored rules: v1 requires only a destination. "
                 "v2 requires a destination and approval before execution."),
            ):
                row = evaluate(client, key, version, destination, memory)
                report["rows"].append(dict(row, arm=arm, task=index))
                print(f"{arm} {version} {row['outcome']}", flush=True)
        json.dump(report, stream, indent=2)


if __name__ == "__main__":
    main()
