"""The sketch: what a drafting role judges, and the record body derived from it.

A decision record's body is mostly mechanism — latch objects, owed acts,
lifecycles, a retirement guard copied from the bars — and only partly
judgment: the payload, its named overshoot, the cue and its exclusions, the
premises as falsifiers, the watch, the residue. A model asked for the whole
body fills the mechanism with placeholders and the judgment thins out. So
the drafting roles (the consolidator at nomination, the pass at close)
return a :class:`Sketch` — the five slots as judgment, nothing derivable —
and :func:`body` derives the :class:`hgi.types.DecisionBody` from it under
the store's bars. The stub answers in the same shape. The floor still runs
over the derived body; the examiner and adjudicator still read the full
draft. A sketch is not a record: it has no envelope and is never stored.
"""

from __future__ import annotations

import operator
import re
from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from hgi import registry as _registry
from hgi.types import HOOK_AXES, Option, Strict, Term

EVALUATION = "suite-v1"
WATCH_PERSISTENCE = 2
"""Runs a watch predicate must hold over before it fires; the bar for a revisit."""

IDEAL_SCORE = 1.0
FAILURE_SCORE = 0.0
"""The oracle's scorers are success rates in ``[0, 1]``: ``1.0`` is the ideal, ``0.0`` is total failure (``suite/scorers.py``)."""

_COMPARATORS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq, "!=": operator.ne}


def _holds(comparator: str, observed: float, value: float) -> bool:
    return _COMPARATORS[comparator](observed, value)


def fires_on_success(comparator: str, value: float, *, ideal: float = IDEAL_SCORE, failure: float = FAILURE_SCORE) -> bool:
    """Whether a revisit watch on a higher-is-better scorer would fire when the record *works*.

    A decision's stakes are a failure the record forestalls, so its revisit
    latch must fire when the oracle shows that failure returning — a low
    score — never when the record succeeds. A watch fires on success when the
    ideal score satisfies its predicate but a failing score does not: the
    latch would then re-adjudicate a record that is working and stay silent
    when it regresses (``task_pass_rate == 1.0`` is the case seen in a
    nominate try). A predicate a failing score also satisfies (``>= 0.0``,
    ``!= 1.0``) still catches the regression and is not a success-watch.
    """
    return _holds(comparator, ideal, value) and not _holds(comparator, failure, value)


def revisit_watch(body: dict[str, Any]) -> dict[str, Any] | None:
    """The world-state watch predicate on a draft body, as the examiner reads it off the revisit latch; ``None`` when the draft sets none."""
    for latch in body.get("latches", []) or []:
        if latch.get("type") == "revisit" and latch.get("key_space") == "world-state":
            predicate = (latch.get("edge") or {}).get("predicate")
            if isinstance(predicate, dict) and predicate.get("comparator") in _COMPARATORS and predicate.get("value") is not None:
                return predicate
    return None


# --- falsifiability: a decision must name a checkable fact about the world, not an instruction (carry-forward item 49a) ---

_GENERIC_FRAGMENTS = frozenset({"task", "test", "output", "plan", "planning"})
"""Work-shape term fragments too generic to be falsifiable world-content on their own: a decision naming only these ("the
task's requirements", "the output") still names no concrete value, column or command. The specific fragments (tool, call,
budget, retry, error, schema, http, shell, file, failure, triage, wrapping) stay — a decision naming one names a
world-mechanism the lesson is about."""

_GENERIC_ACRONYMS = frozenset({"SQL", "HTTP", "API", "JSON", "CSV", "XML", "URL", "URI", "HTML", "REST", "SQLITE", "DB", "ID"})
"""All-caps category names that are not, by themselves, falsifiable content: "a SQL solution" names a category, where
"STRFTIME", "EXISTS" or a status code names a checkable token."""

_QUOTED = re.compile(r"""(['"`])[^'"`]+\1""")
_OPERATOR = re.compile(r"(==|!=|<=|>=|(?<![<>=!])=(?!=))")
_CALL = re.compile(r"[A-Za-z_][\w.]*\s*\(")
_PATH = re.compile(r"[\w.*-]*/[\w./*-]+")
_IDENTIFIER = re.compile(r"[A-Za-z]\w*[._]\w+")
_ALLCAPS = re.compile(r"\b[A-Z][A-Z0-9]{2,}\b")


def _content_fragments(registry: _registry.Registry) -> set[str]:
    """The world-mechanism words a decision may name, derived from the registered hook vocabulary (not a hand list): each
    work-shape and convention term's fragments, minus the generic ones. So the predicate tracks the vocabulary the store
    actually carries, across both hook axes — a decision naming a registered convention (``listing-paged``,
    ``schema-coded-value``) names a checkable world-mechanism exactly as one naming a work-shape does."""
    frags: set[str] = set()
    for term in registry.terms_over(*HOOK_AXES):
        frags |= {f for f in re.split(r"[-_]", term) if f}
    return frags - _GENERIC_FRAGMENTS


def names_world_content(decision: str, registry: _registry.Registry | None) -> bool:
    """Whether a decision sentence names a falsifiable fact about the world — a quoted literal, a path/route, a comparison,
    a command/call token, a code identifier, an all-caps code, or a registered world-mechanism term — rather than a bare
    instruction to do the task right. A decision with none ("correctly translate the logical requirements", "consult the
    store's rules first") is an instruction, not a lesson (carry-forward item 49a). The check errs toward admitting: any one
    concrete signal passes it, so a borderline sketch is kept — a false refusal costs a lesson."""
    text = decision or ""
    if _QUOTED.search(text) or _OPERATOR.search(text) or _CALL.search(text) or _PATH.search(text) or _IDENTIFIER.search(text):
        return True
    if any(tok not in _GENERIC_ACRONYMS for tok in _ALLCAPS.findall(text)):
        return True
    words = set(re.findall(r"[a-z]+", text.lower()))
    return bool(words & _content_fragments(registry)) if registry is not None else False


class PremiseSketch(Strict):
    id: str
    statement: str
    falsifier: str
    """What reading of the evidence would refute the statement; the complement law's member for the warrant."""


class WatchSketch(Strict):
    """A world-state watch on an oracle series: the revisit latch's predicate."""

    scorer: str
    comparator: Literal["<", "<=", ">", ">=", "==", "!="]
    value: float
    persistence: int = Field(default=WATCH_PERSISTENCE, ge=1)


class Sketch(Strict):
    """The judgment in a decision, one field per slot member; everything mechanical is derived."""

    decision: str
    """The payload, object-decoupled: the transferable shape, never the instance."""
    counterfactual: str
    """The named overshoot — a concrete, plausible alternative failure — citing an observation it was seen in."""
    latch: str
    """The cue: when this record enters context, as prose the router shows before the record opens."""
    terms: list[Term(*HOOK_AXES)] = Field(min_length=1)
    """The hook: registered terms the consultation latch keys on, from either hook axis (:data:`hgi.types.HOOK_AXES`) — a
    work-shape (the task's shape, the tool it calls) or a convention (the world-fact the work exhibits). A lesson about a
    convention keys on that convention, so it is recalled when the convention recurs, not only when the same tool does."""
    not_this: list[str] = Field(default_factory=list)
    """The router's declared exclusions: presentations the hook must not fire on. Empty at first draft — precision review grows it from ``not_applicable`` notes, so a floor refusal here would only keep the record out of the store where it can be corrected."""
    stakes: str
    context: str
    """The fork as it was observed: which passes, which anchors."""
    options: list[Option] = Field(min_length=1)
    premises: list[PremiseSketch] = Field(min_length=1)
    watch: WatchSketch | None = None
    residue: list[str] = Field(default_factory=list)
    """What no floor checks; judgment the record leaves to its reader."""
    moot_when: str
    scopes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _decision_names_world_content(self, info: ValidationInfo):
        """The payload must name a falsifiable fact about the world (:func:`names_world_content`); a decision that names none
        is an instruction, not a lesson, and the sketch is refused (carry-forward item 49a)."""
        registry = (info.context or {}).get("registry")
        if not names_world_content(self.decision, registry):
            raise ValueError("decision: names no falsifiable world-content — no value, column, dialect token, command, path "
                             f"or world-mechanism term; a decision with no checkable fact about the world is an instruction, "
                             f"not a lesson: {self.decision!r}")
        return self


def body(sketch: Sketch, anchors: list[str], bars: dict[str, Any], model_id: str | None) -> dict[str, Any]:
    """The decision body a sketch stands for, under ``bars``: the consultation latch from the hook, the revisit latch from
    the watch, the retirement latch from the bars' window, the enforcement floor by check name."""
    retirement = bars["retirement"]
    latches: list[dict[str, Any]] = [{
        "type": "consultation", "slot": "payload", "key_space": "work-shape", "edge": {"kind": "level", "at": "boot"},
        "guard": {"terms": list(sketch.terms), "not_this": list(sketch.not_this)}, "consumer": "the working pass",
        "owed_act": {"class": "apply", "role": "dispositive"}, "lifecycle": {"status": "live"},
    }]
    if sketch.watch is not None:
        latches.append({
            "type": "revisit", "slot": "warrant", "key_space": "world-state",
            "edge": {"kind": "edge", "predicate": {"evaluation": EVALUATION, **sketch.watch.model_dump()}},
            "guard": {}, "consumer": "the backward pass", "owed_act": {"class": "re-adjudicate", "role": "dispositive"}, "lifecycle": {"status": "live"},
        })
    return {
        "scopes": list(sketch.scopes),
        "summary": {"latch": sketch.latch, "not_this": list(sketch.not_this), "stakes": sketch.stakes},
        "context": sketch.context,
        "options": [o.model_dump() for o in sketch.options],
        "decision": sketch.decision,
        "counterfactual": sketch.counterfactual,
        "warrant": {"anchors": list(anchors), "premises": [{**p.model_dump(), "status": "supported"} for p in sketch.premises],
                    "adjudication": {"ledger_entry": None, "species": "attack", "verdict": "pending"}},
        "latches": latches,
        "enforcement": {"floor": ["schema", "complement-law", "ports"], "residue": list(sketch.residue)},
        "lifecycle": {"consumer": "the working pass, at boot, on a matching work-shape", "moot_when": sketch.moot_when,
                      "retirement": {"type": "retirement", "slot": "lifecycle", "key_space": "competence",
                                     "edge": {"kind": "schedule", "at": "consolidation"},
                                     "guard": {"applied_over_considered_below": retirement["applied_over_considered_below"], "over_passes": retirement["window_passes"]},
                                     "consumer": "the lifecycle review", "owed_act": {"class": "retire", "role": "corroborating"}, "lifecycle": {"status": "live"}}},
        "priced_for": {"model_id": model_id},
    }


def sketch_of(raw: Any, registry: _registry.Registry) -> Sketch:
    """A sketch from a reply's ``sketch`` field, read defensively: a stringified object is parsed, a missing one is refused."""
    import json

    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, dict):
        raise ValueError("sketch: a JSON object is required")
    return Sketch.model_validate(raw, context={"registry": registry})


SKETCH_REPLY: dict[str, Any] = {
    "decision": "<the payload, one or two sentences, object-decoupled: the transferable shape, never a task or tool name>",
    "counterfactual": "<the overshoot: a concrete alternative failure of following the decision too far, citing an observation name it was seen in or bounded by>",
    "latch": "<the cue: when this record should enter context, as prose>",
    "terms": ["<the hook: a term from `vocabularies` the pass presents — a work-shape or the convention the lesson is about>"],
    "not_this": ["<a presentation the hook must not fire on>"],
    "stakes": "<what goes wrong without the record, in the oracle's terms>",
    "context": "<the fork as observed: which sessions, which observations>",
    "options": [{"name": "<an option>", "judged": "<chosen | rejected>", "why": "<one sentence>"}],
    "premises": [{"id": "<p1>", "statement": "<a constraining fact the decision rests on>", "falsifier": "<what reading of the evidence would refute it>"}],
    "watch": {"scorer": "<a scorer from `scorers`>", "comparator": "<one of < <= > >= == !=>", "value": "<a number>", "persistence": "<runs it must hold over; 2 unless argued>"},
    "residue": ["<what no floor checks; judgment left to the reader>"],
    "moot_when": "<the condition under which the record no longer applies>",
    "scopes": ["<a path or module the record bears on>"],
}
"""The reply shape of a sketch, one placeholder per field; ``watch`` may be ``null``."""


def schema() -> dict[str, Any]:
    return Sketch.model_json_schema()
