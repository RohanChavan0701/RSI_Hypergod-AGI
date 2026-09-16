"""The role prompts, one file each, each priced; and the request contract.

A prompt file is Markdown with a leading ``priced_for:`` line naming the
models its replies have been read against, comma-separated (``stub`` is
the deterministic stand-in). ``prompt(role)`` returns the body; the four
contexts of the backward pass share no prompt text beyond the store's
schemas, which every role receives through :func:`schemas`. The lint warns
when a role runs on a model its prompt is not priced for (``hgi roles
pricing`` lists them); a model earns its place on the line when every
request the role answers has been read back through ``hgi roles try``.

Every request a role receives is one JSON object built by :func:`request`:
its ``request`` field names the request, its ``reply`` field states the
exact shape of the answer (:data:`REPLIES`, one entry per request), and the
rest is the request's content. The reply shape travels with the request
rather than living in the prompt, so a model that has never seen the code
answers in the shape the code reads, and the stub — which answers by the
``request`` field — is the same contract by example.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from hgi.drafting import SKETCH_REPLY

HERE = Path(__file__).parent

ROLES = ("pass", "consolidator", "examiner", "adjudicator", "coder", "reauthor")

REPLIES: dict[str, Any] = {
    "classify": {"terms": ["<a term from `terms` that at least one presentation's prompt plainly instantiates — a work-shape (the tool, the task's shape) or a convention the presentation reveals (a stated paging contract, an inspectable coded schema); the union over all tasks; a term that merely might apply, or a convention hidden until the work fails, is left out>"],
                 "escapes": ["other(<a shape a presentation has and the vocabulary lacks>)"]},
    "guard": {"passed": "<true when at least one presentation instantiates the hook's terms and is not excluded by a `not_this`; an exclusion that covers some matching presentations but not all does not fail the guard>", "why": "<one sentence naming the presentation that passed, or the exclusion that covered every match>"},
    "lens": {"answer": "<one sentence answering the lens's angle from the subject; empty string when nothing is found>",
             "findings": ["<one object per finding, with exactly the fields the lens's `product` names. File one finding per failed world-fact, carrying both halves together: `happened` states the settled world-fact in one sentence naming the task and the concrete literal (the output, the value, the route, the tool error — transcribable), and `turned_on` names the convention that world-fact turned on (the inference the same finding rests on). Do not split a world-fact into a `happened`-only finding and a separate `turned_on`-only finding on the same row — the literal and the convention it turned on belong in one record, or the drafting floor sees a token with no lesson beside a lesson with no token. `turned_on` may be null only when the world-fact genuinely carries no inference to name. An anchor is {call: <the row's `call` URI>, path: <a file path or null>}>"]},
    "dispose": {"dispositions": [{"record": "<a consulted record id>", "disposition": "<applied | considered-not-applicable | fired-off-map>",
                                  "note": "<which rows it bore on, or why it did not>"}],
                "fires": [{"fire": "<a fire id from `fires_owed`>", "outcome": "<what the pass did about the owed act, read from the rows; one sentence>"}]},
    "propose": {"drafts": [{"rung": "<a ladder rung from `rungs`>", "rung_why": "<why the cheaper rungs do not suffice>", "subject": "<one word naming the lesson>",
                            "evidence": ["<observation names from `observations`>"], "supersedes": [], "sketch": SKETCH_REPLY}]},
    "coding": {"<observation name>": ["<the convention the noticing names, as a registry term from `terms`; other(<the convention in a few words>) when no term covers it>"]},
    "cluster": {"shapes": {"<observation name, from `observations`>": ["<a convention this observation turned on — the world-fact its attempt met or missed — a `terms` convention term when one fits, else other(<the convention in a few words>); return a *set* per observation: at least one broad convention it shares with other observations and at least one specific one, never a single narrow label. Two observations group when they share a label>"]}},
    "triage": {"verdict": "<reducible when a duty the loop could have carried would have prevented the failure the rows show; irreducible when nothing any record could say would have — the endpoint failed the turn, the turn limit fell, a hidden test raised, the task had no policy to run>",
               "why": "<one sentence naming the row and the duty, or the row and why no duty reaches it>"},
    "nominate": {"nominations": [{"rung": "<a ladder rung from `rungs`>", "rung_why": "<why the cheaper rungs do not suffice>", "subject": "<one word naming the lesson>",
                                  "evidence": ["<observation names from the brief's groups>"], "supersedes": ["<accepted decision ids this retires>"],
                                  "split_from": "<the fused accepted decision this draft is one leaf of (a row of the brief's `fusion`), or null>",
                                  "folded_from": ["<the accepted decisions whose payloads this draft contracts into one (a row of the brief's `convergence`); empty unless folding>"],
                                  "edit": {"terms": ["<for hook-edit: the registered hook terms the successor's consultation hook keys on — a work-shape or the convention the lesson is about>"],
                                           "not_this": ["<for hook-edit or counterfactual-edit: the successor's exclusions>"],
                                           "counterfactual": "<for counterfactual-edit: the successor's counterfactual, anchored; else null>"},
                                  "adopts": "<the uid of a proposal from the brief's `proposals` whose draft this nomination adopts as its own, else null>",
                                  "sketch": SKETCH_REPLY}]},
    "promote": {"decision": "<the payload restated at the transferable altitude: the shape the anchored instances share, never the task, file, path or tool it was seen in; one or two sentences; the instances stay as anchors>"},
    "applies_when": {"fires_on": ["<a registered hook term from `vocabulary` the lesson fires on — a work-shape, or the convention the lesson is about; name every term it applies to, biased broad — the origin in `floor` is the lower bound on reach, never the ceiling; do not name a term in `pool_universal` (a convention is never one, so it is always safe to widen onto)>"],
                     "not_this": ["<a presentation the hook must not fire on; recover precision here, never by shaving `fires_on`>"]},
    "attack": {"claims": [{"target": "<a target in the `lens.claims` classes when a lens is named — premise:<id> | payload:abstraction; any of them when none is>",
                           "refutation": "<what reading of the evidence would show it false>",
                           "reading_taken": "<true if you took that reading>", "landed": "<true if the reading showed it false>", "evidence": ["<what you read>"]}]},
    "verdict": {"verdict": "<admit | admit-amended(<amendment>) | decline(<why>) | defer(<until>) | escalate(<why>)>", "amendment": "<the amended decision text, or null>",
                "rationale": "<one sentence weighing the attack against the evidence: which landed claim you accepted or rejected, and why>",
                "until": {"scorer": "<for defer keyed on the oracle: the scorer of `oracle.evaluation` whose next readings settle it; else null>",
                          "comparator": "<one of < <= > >= == !=; else null>", "value": "<a number; else null>", "persistence": "<consecutive runs the reading must hold; else null>",
                          "passes": "<for defer keyed on the schedule: passes to wait before re-adjudication; else null>"}},
    "credit": {"steers": [{"record": "<a record id from `applied` — each is a regression: applied, and its tasks passed no more often than before>", "slot": "<the slot indicted: payload when the content was wrong, activation when it fired where it did not bear, warrant when a premise no longer holds>",
                           "signature": "recalled-applied-still-corrected", "correction": "<what the record got wrong, from the table>", "why_not_caught": "<why no floor caught it>"}]},
    "anchor": {"anchors": [{"article": "<a C- id from `articles`>", "anchor": "<one id or URI from `instances` that exemplifies the article>",
                            "why": "<how that instance instantiates the article's claim>"}]},
    "exemplifies": {"verdict": "<still-holds if the instance exemplifies the article; reversed if it contradicts it; moot if it does not bear on it>", "why": "<one sentence>"},
    "vocabulary": {"verdict": "<admit if the escapes name one shape no registered term covers and the blind coder also escaped, and `route.route` is horizontal — a missing peer or a partition of one member; else decline(<why>)>",
                   "means": "<for admit: one sentence defining the term, as the registry will carry it>"},
    "ports": {"verdict": "<admit to widen the port's mark from forbidden to optional when the occasions' warrants name a use the declaration did not anticipate and the records are independent; else decline(<why>)>",
              "why": "<one sentence naming the warrant that earned it, or why the declaration stands>"},
    "currency": {"verdict": "<still-holds | reversed | moot>", "why": "<one sentence; a record whose cited anchor (`rotted`) retired still holds only if the anchor's successor stands for it; a pass's `finding` reverses a premise only when the evidence it cites shows that premise false; a `lens` at a door is moot when its repeated product is a cacheable answer or its seed never produced, still-holds when the question is still where judgment is needed; a record with `domain_entered` false — considered by no pass over the window — is moot only when the window's `evidence` meets its `moot_when` condition, still-holds otherwise: never fired is a count, and the killer-item is exempt regardless of count>",
                 "premise": "<for reversed: the id of the premise the reading reversed; null when the warrant as a whole is disputed>"},
    "reauthor": {"text": {"<the name of a field being re-authored, such as `angle` or `article`>": "<that field's content re-authored to condition the new model: the same claim, the wording that conditions it>"}},
}


def request(name: str, **content: Any) -> str:
    """The JSON a role receives for request ``name``: the content, and the reply shape it must answer in."""
    if name not in REPLIES:
        raise KeyError(f"no reply shape for request {name!r}; requests are {sorted(REPLIES)}")
    return json.dumps({"request": name, **content, "reply": REPLIES[name]}, default=str)


EMPTY_IS_LEGAL = "an empty list is a legal answer: refusal is a first-class outcome when nothing observed earns a rung"
"""Sent as request content, never as a list placeholder — a placeholder inside a list comes back as a literal element."""

EMPTY_STEER_IS_LEGAL = "an empty list is a legal answer: a steer is written only where the table shows a record that was applied and did not help; a regression the evidence does not attribute to the record earns none"

EMPTY_LENS_IS_LEGAL = "an empty findings list is a legal answer: a finding is filed only for something that happened in the rows; nothing is invented to have one"


def drafts_in(out: Any, key: str) -> list[dict[str, Any]]:
    """The draft-carrying objects under ``key`` of a reply; anything that is not an object is dropped."""
    items = out.get(key, []) if isinstance(out, dict) else []
    return [raw for raw in items if isinstance(raw, dict)]


def refusal(e: Exception) -> str:
    """A parse refusal that names every failing field, so a role's next draft can be corrected against it."""
    errors = getattr(e, "errors", None)
    if callable(errors):
        return "; ".join(f"{'.'.join(str(x) for x in err['loc'])}: {err['msg'].removeprefix('Value error, ')}" for err in errors())[:1000]
    return str(e).splitlines()[0]


def draft_of(store, raw: dict[str, Any], *, proposed_by: str, name: str, model_id: str | None):
    """A :class:`hgi.types.Draft` from a drafting reply's item: the sketch parsed, the body derived under the store's bars.

    Raises ``ValueError`` naming every failing field when the item does not
    carry what a draft needs; a missing sketch is a failing field too.
    """
    from hgi.drafting import body, sketch_of
    from hgi.store import now
    from hgi.types import Draft

    if "sketch" not in raw:
        raise ValueError("sketch: a drafting reply carries a `sketch` object")
    sketch = sketch_of(raw.get("sketch"), store.registry)
    evidence = [e for e in raw.get("evidence", []) if isinstance(e, str)]
    return store.parse_as(Draft, {
        "uid": store.new_uid(), "name": name, "kind": "decision", "drafted_at": now().isoformat(), "proposed_by": proposed_by,
        "rung": raw.get("rung"), "rung_why": raw.get("rung_why") or "", "evidence": evidence,
        "supersedes": [x for x in raw.get("supersedes", []) if isinstance(x, str)], "body": body(sketch, evidence, store.registry.bars, model_id),
    })


REPLY_RULE = ("Every request is one JSON object whose `reply` field states the exact shape of your answer: reply with one JSON object of that "
              "shape and nothing else, every angle-bracketed placeholder replaced by a value, no field added or renamed.")


@cache
def _load(role: str) -> tuple[str | None, str]:
    text = (HERE / f"{role}.md").read_text()
    priced = None
    if text.startswith("priced_for:"):
        head, _, text = text.partition("\n")
        priced = head.split(":", 1)[1].strip() or None
    return priced, text.strip()


def prompt(role: str) -> str:
    if role not in ROLES:
        raise KeyError(f"no role prompt for {role!r}; roles are {ROLES}")
    return _load(role)[1] + "\n\n" + REPLY_RULE + "\n\n" + schemas(role)


def priced_for(role: str) -> str | None:
    return _load(role)[0]


def priced_models(role: str) -> list[str]:
    head = priced_for(role)
    return [m.strip() for m in head.split(",") if m.strip()] if head else []


def is_priced_for(role: str, model_id: str | None) -> bool:
    return model_id is None or model_id in priced_models(role)


def role_models(role: str) -> list[type]:
    """The record shapes a role reads or writes: the drafting roles the sketch, the judging roles the draft and the ledger entry."""
    from hgi.drafting import Sketch
    from hgi.types import Draft, LedgerEntry, Observation

    return {"pass": [Observation, Sketch], "consolidator": [Sketch], "examiner": [Draft, LedgerEntry], "adjudicator": [Draft, LedgerEntry], "coder": [], "reauthor": []}[role]


@cache
def schemas(role: str = "examiner") -> str:
    """The record shapes the role reads and writes, derived from the declarations — never a second copy."""
    parts = ["## Record shapes (JSON Schema, derived from hgi/types.py and hgi/drafting.py)"]
    for model in role_models(role):
        parts.append(f"### {model.__name__}\n```json\n{_compact(model)}\n```")
    return "\n\n".join(parts) if len(parts) > 1 else ""


def _compact(model) -> str:
    """The whole schema, nested definitions included: a body drafted against a schema with its definitions stripped comes back in an invented shape."""
    return json.dumps(model.model_json_schema(by_alias=True), separators=(",", ":"))
