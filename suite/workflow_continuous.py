"""Matched A-B-A pilot with shared conversation and graded feedback."""

import argparse
import json
import os
from pathlib import Path

import httpx

from hgi.cli import load_env
from suite.workflow_hosted import MAX_TURNS, MODEL, TASKS, evaluate
from suite.workflow_stateful import Request


def run_episode(client, key, arm):
    conversation = []
    learned = {}
    rows = []
    for phase, (version, destination) in zip(("A_initial", "B_switch", "A_return"), TASKS):
        lesson = ""
        if arm == "fixed":
            lesson = " Stored lesson: execute once the destination is known."
        elif arm == "updated" and version in learned:
            lesson = " Stored lesson: " + learned[version]
        row = evaluate(client, key, version, destination, lesson, conversation)
        probe = Request(version, "reference")
        probe.call("execute")
        rule = ("Execute once the destination is known." if probe.executed
                else "Obtain approval after resolving the destination, then execute.")
        conversation.append({"role": "user", "content": json.dumps({
            "feedback_version": version, "outcome": row["outcome"], "rule": rule,
        })})
        if arm == "updated":
            learned[version] = rule
        rows.append(dict(row, phase=phase, lesson=lesson.strip(), feedback=rule))
        print(f"{arm} {phase}: {row['outcome']}", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    load_env()
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        parser.error("Configure NVIDIA_API_KEY locally")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {"model": MODEL, "max_turns_per_phase": MAX_TURNS, "arms": {}}
    with args.out.open("x", encoding="utf-8") as stream, httpx.Client(timeout=45) as client:
        for arm in ("history", "fixed", "updated"):
            report["arms"][arm] = run_episode(client, key, arm)
        json.dump(report, stream, indent=2)


if __name__ == "__main__":
    main()
