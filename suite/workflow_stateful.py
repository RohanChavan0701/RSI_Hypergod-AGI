"""Replay a workflow switch and grade the resulting simulated API state."""

import json
from dataclasses import dataclass, field


@dataclass
class Request:
    version: str
    destination: str | None
    approved: bool = False
    executed: bool = False
    violations: int = 0
    events: list[dict] = field(default_factory=list)

    def call(self, tool: str) -> None:
        if tool == "clarify" and self.destination is None:
            self.destination = "west"
        elif tool == "request_approval" and self.version == "v2" and self.destination:
            self.approved = True
        elif (tool == "execute" and self.destination and not self.executed
              and (self.version == "v1" or self.approved)):
            self.executed = True
        else:
            self.violations += 1
        self.events.append({
            "tool": tool, "destination": self.destination, "approved": self.approved,
            "executed": self.executed, "violations": self.violations,
        })


def rollout(strategy):
    rows = []
    for version, destination in (("v1", "east"), ("v2", None), ("v1", "west")):
        request = Request(version, destination)
        for _ in range(3):
            if request.executed:
                break
            if request.destination is None:
                tool = "clarify"
            elif strategy == "version-aware" and version == "v2" and not request.approved:
                tool = "request_approval"
            else:
                tool = "execute"
            request.call(tool)
        rows.append({
            "version": version, "success": request.executed and request.violations == 0,
            "violations": request.violations, "trace": request.events,
        })
    return rows


def report():
    baseline = rollout("stale")
    candidate = rollout("version-aware")
    return {
        "kind": "scripted-stateful-controls",
        "arms": {"stale": baseline, "version-aware": candidate},
        "promotion": {
            "accepted": (
                not any(row["violations"] for row in candidate)
                and sum(row["success"] for row in candidate) > sum(row["success"] for row in baseline)
                and all(new["success"] or not old["success"] for old, new in zip(baseline, candidate))
            ),
        },
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
