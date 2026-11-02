"""Shell-free action-selection probe; no API mutation is executed.

Splits use disjoint operation names and prompt templates. This synthetic probe
validates measurement plumbing, not generalization to production workflows.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from suite.families import family
from suite.tasks import Task


SCHEMA = {
    "type": "object", "required": ["result"], "additionalProperties": False,
    "properties": {"result": {
        "type": "object", "required": ["action", "arguments", "missing"],
        "additionalProperties": False,
        "properties": {
            "action": {"enum": ["execute", "clarify", "confirm"]},
            "arguments": {"type": "object"},
            "missing": {"type": "array", "items": {"type": "string"}},
        },
    }},
}


@dataclass(frozen=True)
class Case:
    split: str
    operation: str
    required: tuple[str, ...]
    supplied: dict[str, str]
    confirmation_required: bool
    confirmed: bool

    def expected(self) -> dict[str, Any]:
        missing = sorted(set(self.required) - self.supplied.keys())
        action = "clarify" if missing else (
            "confirm" if self.confirmation_required and not self.confirmed else "execute"
        )
        return {"action": action, "arguments": dict(self.supplied), "missing": missing}


OPERATIONS = {
    "experience": [("send_invoice", "customer", "amount"), ("book_room", "room", "date")],
    "selection": [("ship_order", "order", "address"), ("schedule_backup", "volume", "time")],
    "test": [("publish_release", "project", "version"), ("transfer_inventory", "item", "destination")],
}
TEMPLATES = {
    "experience": "Choose the next action for this API request: {operation}.",
    "selection": "An operator requests {operation}. Decide what should happen next.",
    "test": "Handle the pending {operation} request by proposing exactly one next step.",
}


def cases(split: str) -> list[Case]:
    result = []
    for operation, first, second in OPERATIONS[split]:
        for missing in (False, True):
            for requires_confirmation, confirmed in ((False, False), (True, False), (True, True)):
                supplied = {first: f"{first}-17"}
                if not missing:
                    supplied[second] = f"{second}-29"
                result.append(Case(split, operation, (first, second), supplied,
                                   requires_confirmation, confirmed))
    return result


def accepts(value: Any, expected: dict[str, Any]) -> bool:
    """Exact structured decision; reject invented arguments and duplicate omissions."""
    return isinstance(value, dict) and value == expected


def tasks_for(split: str) -> list[Task]:
    tasks = []
    for index, case in enumerate(cases(split)):
        request = {
            "operation": case.operation, "required_arguments": list(case.required),
            "supplied_arguments": case.supplied,
            "confirmation_required": case.confirmation_required,
            "user_confirmed": case.confirmed,
        }
        prompt = TEMPLATES[split].format(operation=case.operation) + (
            " Return action, arguments, and missing inside result. Preserve supplied arguments;"
            " never invent a missing value. If required arguments are absent, clarify first"
            " and list missing names in sorted order. Otherwise request confirmation only"
            " when required and not already given; otherwise execute. This is a plan only;"
            " do not call an API. Request: " + json.dumps(request, sort_keys=True)
        )
        expected = case.expected()
        tasks.append(Task(
            f"workflow-{split}/{index:03d}", prompt,
            ("task-planning", "output-schema"), SCHEMA,
            lambda value, workdir, gold=expected: accepts(value, gold),
        ))
    return tasks


for _split in OPERATIONS:
    family(f"workflow-{_split}", source="synthetic conditional action-selection probe")(
        lambda split=_split: tasks_for(split)
    )
