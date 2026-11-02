"""Offline measurement sanity check: python -m suite.workflow_probe.

Scripted controls only. No language model, memory learning, or RSI is measured.
"""

from __future__ import annotations

import json
from collections import Counter

from suite.families.workflow_drift import OPERATIONS, cases


def report() -> dict:
    splits = {}
    for split in OPERATIONS:
        rows = cases(split)
        controls = {}
        for policy in ("always-execute", "always-clarify", "always-confirm", "conditional-reference"):
            correct, totals = Counter(), Counter()
            for case in rows:
                expected = case.expected()["action"]
                predicted = expected if policy == "conditional-reference" else policy.removeprefix("always-")
                totals[expected] += 1
                correct[expected] += predicted == expected
            per_action = {action: correct[action] / count for action, count in sorted(totals.items())}
            controls[policy] = {
                "action_accuracy": sum(correct.values()) / len(rows),
                "per_action_accuracy": per_action,
                "balanced_action_accuracy": sum(per_action.values()) / len(per_action),
            }
        splits[split] = {"tasks": len(rows), "controls": controls}
    return {"kind": "scripted-measurement-controls", "model_calls": 0, "splits": splits}


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
