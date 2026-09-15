"""The deterministic stand-in for the frozen model.

Every role request is a JSON object with a ``request`` field; the handler for
that field answers by fixed rules stated here. The stub exists so the loop's
mechanics — boot, evaluate, close, consolidate, the four-role adjudication —
run and are testable without an inference endpoint. Its answers are keyword
rules over the same inputs the model would read; they are not evidence that
anything learned.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable


HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {}


def handles(name: str):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco


def answer(messages: list[dict[str, Any]], tools: list[dict] | None = None) -> str:
    user = messages[-1]["content"]
    try:
        req = json.loads(user)
    except (json.JSONDecodeError, TypeError):
        req = {"request": "free"}
    handler = HANDLERS.get(req.get("request"), HANDLERS["free"])
    return json.dumps(handler(req))


@handles("free")
def _free(req):
    return {}


# --- the pass ---------------------------------------------------------------------

KEYWORDS: dict[str, tuple[str, ...]] = {
    "http-tool": ("get /", "http", "api", "502"),
    "shell-tool": ("shell", "wc -l"),
    "tool-budget": ("budget",),
    "file-tool": ("read config", "write report", "file"),
    "output-schema": ("schema", "exactly", "object"),
    "error-wrapping": ("error", "fail", "cause"),
    "tool-call-retry": ("retr", "transient"),
    "test-failure-triage": ("failing test",),
    "task-planning": ("plan",),
}


def terms_for(text: str, allowed: list[str]) -> list[str]:
    text = text.lower()
    return [t for t in allowed if any(k in text for k in KEYWORDS.get(t, ()))]


# The convention-major shapes the blind coder groups observations by, keyed off the world-fact the noticing names —
# distinct from KEYWORDS, which the boot classify reads over the *task prompt* (where the convention is hidden, so a
# prompt keys only the tool cue). These words appear in the noticing the blind close writes, never in the lesson label
# the coder is denied. The stub is a lexical proxy for the model's convention inference; a live re-score is what confirms it.
CONVENTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "route-versioned": ("/v2", "410", "versioned", "moved", "gone", "successor route", "retired route"),
    "listing-paged": ("page", "paging", "paginat", "next page", "one page", "first page"),
    "route-guarded": ("token", "401", "unauthor", "secure route", "authorize", "authoriz"),
    "field-quoted": ("quoted", "quoted field", "quoted comma", "comma inside", "embedded comma"),
    "summary-row": ("footer", "total row", "summary row", "footer row", "trailer", "total line", "totals row"),
    "line-unterminated": ("newline", "no trailing", "unterminated", "not terminated"),
    "byte-order-mark": ("byte order mark", "byte-order mark", "bom", "utf-8-sig", "u+feff"),
    "schema-coded-value": ("coded value", "coded literal", "coded status", "status char", "single-letter code", "categorical code",
                           "stored as text", "text date", "date is text", "strftime", "date function", "integer division",
                           "integer-divide", "cast to real", "needs a cast", "reserved word", "backtick"),
    "pool-exhausted": ("pool exhaust", "pool is exhausted", "in_use", "backends busy", "waiting for a connection",
                       "undersized pool", "pool max", "pool saturated by load"),
    "dependency-stalled": ("provider", "upstream", "dependency latency", "idle in transaction", "held across",
                           "geocod", "third-party", "slow dependency"),
    "release-regressed": ("deploy", "release", "regression", "rolled out", "since the deploy", "bad deploy",
                          "version bump"),
}


def conventions_for(text: str, allowed: list[str]) -> list[str]:
    """The registered convention-major terms whose world-fact the noticing names — the blind coder's finer shape."""
    text = text.lower()
    return [t for t in allowed if t in CONVENTION_KEYWORDS and any(k in text for k in CONVENTION_KEYWORDS[t])]


@handles("classify")
def _classify(req):
    text = " ".join(p["prompt"] for p in req["presentations"])
    return {"terms": terms_for(text, req["terms"]), "escapes": []}


@handles("guard")
def _guard(req):
    hook, shape = req["hook"], req["work_shape"]
    text = " ".join(p["prompt"] for p in req.get("presentations", [])).lower()
    overlap = sorted(set(hook["terms"]) & set(shape["terms"]))
    excluded = [n for n in hook.get("not_this", []) if n.lower() in text]
    passed = bool(overlap) and not excluded
    return {"passed": passed, "why": f"terms {overlap} matched" + (f"; excluded by {excluded}" if excluded else "")}


@handles("lens")
def _lens(req):
    lens, subject = req["lens"], req["subject"]
    if lens["id"] == "L-0004":
        rows = subject.get("rows") or ([subject["row"]] if "row" in subject else [])
        return {"answer": "read from the rows' tool errors", "findings": _noticings(rows)}
    if lens["id"] == "L-0009":
        rows = subject.get("rows") or ([subject["row"]] if "row" in subject else [])
        return {"answer": "read from the passed rows' recovered faults", "findings": _recovered_misses(rows)}
    if lens["id"] == "L-0010":
        return {"answer": "read from the off-map condition", "findings": _off_map_noticings(subject)}
    return {"answer": "nothing found on this reading", "findings": []}


def _noticings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        err = row.get("error")
        if not err:
            continue
        tool_errors = row.get("tool_errors", [])
        transient = next((e for e in tool_errors if e.get("transient")), None)
        anchor = {"call": row.get("call"), "path": "suite/tools.py:54"}
        if transient and not err.get("cause"):
            out.append({"happened": f"task {row['task']} failed on a transient fault ({transient['cause']}) and the reported error named no cause",
                        "turned_on": "an error that wraps a failed tool call must carry the underlying cause",
                        "anchor": anchor, "recheck_when": "any tool call that can fail transiently"})
        elif transient and err.get("cause"):
            out.append({"happened": f"task {row['task']} named the transient cause ({transient['cause']}) and still failed: the call was not retried",
                        "turned_on": "a transient fault is retried once before it is reported",
                        "anchor": anchor, "recheck_when": "a transient fault reported without a retry"})
        elif any("budget" in (e.get("cause") or "") for e in tool_errors):
            out.append({"happened": f"task {row['task']} exceeded its shell budget: independent calls were issued one per input instead of batched",
                        "turned_on": "independent calls under a budget are issued as one batched call",
                        "anchor": anchor, "recheck_when": "a budgeted tool over several independent inputs"})
    return out


def _recovered_misses(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A passed row that recovered from a non-transient first attempt: the noticing names the convention the first attempt
    missed, carrying the fault's cause so a later pass can group on it. A row whose only fault was transient — a 502 that
    cleared on retry — is loud but non-causal, and nothing is filed."""
    out = []
    for row in rows:
        nontransient = next((e for e in row.get("tool_errors", []) if not e.get("transient")), None)
        if nontransient is None:
            continue
        cause = nontransient.get("cause") or nontransient.get("message") or "an unstated fault"
        out.append({"happened": f"task {row['task']} passed only after its first attempt failed on {cause}",
                    "turned_on": "the convention the pass corrected on, not a transient it retried past",
                    "anchor": {"call": row.get("call"), "path": "suite/tools.py:54"}, "recheck_when": "a passed task whose first attempt hit a non-transient fault"})
    return out


def _off_map_noticings(subject: dict[str, Any]) -> list[dict[str, Any]]:
    """A pass that failed and matched no hook: the store held no rule for this work, named on a failed row's call. Empty when
    the pass is not off-map — it did consult a record, so a hook fired and this is not the missing-coverage signal."""
    if not subject.get("off_map"):
        return []
    failed = subject.get("failed", [])
    call = next((f["row"].get("call") for f in failed if isinstance(f.get("row"), dict) and f["row"].get("call")), None)
    tasks = ", ".join(f.get("task", "?") for f in failed) or "this pass"
    return [{"happened": f"work failed and matched no hook: the store holds no rule for {tasks}",
             "anchor": {"call": call, "path": None}, "recheck_when": "work that fails and consults nothing"}]


@handles("dispose")
def _dispose(req):
    applied_in = {rid for row in req["rows"] for rid in row.get("applied", [])}
    passed = sum(1 for row in req["rows"] if not row.get("error"))
    fires = [{"fire": f["id"], "outcome": f"{f['disposition']['act']}: {f['latch']['record']} read against the pass's rows; {passed}/{len(req['rows'])} tasks passed with it in context"}
             for f in req.get("fires_owed", [])]
    return {"fires": fires, "dispositions": [
        {"record": c["record"], "disposition": "applied" if c["record"] in applied_in else "considered-not-applicable",
         "note": "applied on " + ", ".join(r["task"] for r in req["rows"] if c["record"] in r.get("applied", [])) if c["record"] in applied_in
                 else "hook matched the pass's presentation and no task bore on it: " + ", ".join(r["task"] for r in req["rows"])}
        for c in req["consulted"]
    ]}


@handles("propose")
def _propose(req):
    return {"drafts": []}


# --- the coder --------------------------------------------------------------------------

@handles("coding")
def _coding(req):
    # Classify each observation against `terms` on the convention its text names; fall back to a tool-major cue present in
    # `terms`, else an escape, only when no listed convention is behind the miss — the same order the coder prompt states.
    out = {}
    for o in req["observations"]:
        text = o.get("noticed") or o.get("happened") or ""
        conv = conventions_for(text, req["terms"])
        out[o["name"]] = sorted(conv) if conv else (terms_for(text, req["terms"]) or ["other(unclassified)"])
    return out


@handles("cluster")
def _cluster(req):
    # Multi-shape (item 64): each observation gets a *set* of convention labels — every registered convention its
    # `happened` names, else the way-of-working lesson it turns on (other(<lesson>)), else other(unclassified). The stub
    # multi-selects rather than collapsing to one label, so an observation whose world-fact names two conventions carries
    # both and groups under each; grouping is per-label downstream. The shape is the convention, never the tool.
    shapes: dict[str, list[str]] = {}
    for o in req["observations"]:
        text = o.get("happened") or o.get("noticed") or ""
        labels = sorted(conventions_for(text, req["terms"]))
        if not labels:
            key = lesson_key([text])
            labels = [f"other({key})" if key else "other(unclassified)"]
        shapes[o["name"]] = labels
    return {"shapes": shapes}


# --- the consolidator ---------------------------------------------------------------------

LESSONS: dict[str, dict[str, Any]] = {
    "cause": {
        "decision": "Errors that wrap a failed tool call carry the underlying cause.",
        "latch": "a tool call that fails; an error reported from a tool failure; a wrapper that rethrows",
        "not_this": ["a failure inside the model's own reasoning, with no tool call behind it"],
        "stakes": "a silent failure hides the cause the oracle scores on; passes score green while the fault persists",
        "options": [("A — report the cause on every error", "chosen", "the scorer reads the final error's cause"),
                    ("B — report only the message", "rejected", "the cause is lost at the first rethrow")],
        "premises": [("p1", "the oracle's error_cause_present scorer reads the final error's cause", "a scorer change that grades on exit code only"),
                     ("p2", "tool failures recur across the suite", "two consecutive consolidation passes with no tool failure in the trace store")],
        "counterfactual": "The overshoot is a wrapper that reports the cause but never recovers — observed in {anchors}, where the task still failed.",
        "watch": ("error_cause_present", "<", 0.5),
        "residue": ["whether the cause named is the right one is judgment; the floor checks shape only"],
        "moot_when": "no tool in the layer can fail",
    },
    "retry": {
        "decision": "A transient tool failure is retried once before it is reported, and the report carries the cause.",
        "latch": "a tool call that can fail transiently; a 5xx from the HTTP tool; a wrapper around a flaky call",
        "not_this": ["a non-transient failure such as a 404, which a retry cannot repair"],
        "stakes": "a task that fails on a transient fault scores zero while one retry would pass",
        "options": [("A — retry once, cause preserved", "chosen", "clears the transient fault and keeps the scorer's signal"),
                    ("B — report the cause without retrying", "rejected", "the cause was named and the task still failed")],
        "premises": [("p1", "a transient fault clears on the next call", "a second consecutive 5xx on the same path in the trace store"),
                     ("p2", "task_pass_rate on faulted tasks is bounded by whether the call is retried", "faulted tasks failing after a retry")],
        "counterfactual": "The overshoot is retrying every failure including the non-transient — a retry storm — bounded by {anchors}.",
        "watch": ("task_pass_rate", "<", 0.7),
        "residue": ["whether one retry is the right number is judgment"],
        "moot_when": "the tool layer stops exposing transient failures",
    },
    "batch": {
        "decision": "Under a call budget, independent calls over known inputs are issued as one batched call.",
        "latch": "a shell tool under a call budget; several files or inputs to inspect",
        "not_this": ["calls whose inputs depend on a previous call's output"],
        "stakes": "a budget exceeded fails the task outright",
        "options": [("A — one batched call", "chosen", "fits any budget of one or more"),
                    ("B — one call per input", "rejected", "exceeds the budget whenever inputs outnumber it")],
        "premises": [("p1", "the budget is smaller than the number of independent inputs", "a budget at or above the input count")],
        "counterfactual": "The overshoot is batching dependent calls whose later inputs are unknown — bounded by {anchors}.",
        "watch": ("tool_budget_respected", "<", 0.5),
        "residue": ["whether the inputs are truly independent is judgment"],
        "moot_when": "no tool runs under a budget",
    },
}


def lesson_key(texts: list[str]) -> str | None:
    joined = " ".join(texts).lower()
    if "named no cause" in joined or "carry the underlying cause" in joined:
        return "cause"
    if "not retried" in joined or "retried once" in joined:
        return "retry"
    if "budget" in joined:
        return "batch"
    return None


def sketch(key: str, terms: list[str], anchors: list[str]) -> dict[str, Any]:
    """The lesson as a drafting reply's sketch — the judgment; the body is derived by :mod:`hgi.drafting`."""
    L = LESSONS[key]
    scorer, cmp, value = L["watch"]
    return {
        "decision": L["decision"], "counterfactual": L["counterfactual"].format(anchors=", ".join(anchors)),
        "latch": L["latch"], "terms": terms, "not_this": L["not_this"], "stakes": L["stakes"],
        "context": "the same fork was observed in independent passes: " + ", ".join(anchors),
        "options": [{"name": n, "judged": j, "why": w} for n, j, w in L["options"]],
        "premises": [{"id": i, "statement": st, "falsifier": f} for i, st, f in L["premises"]],
        "watch": {"scorer": scorer, "comparator": cmp, "value": value, "persistence": 2},
        "residue": L["residue"], "moot_when": L["moot_when"], "scopes": ["suite/tools"],
    }


NOT_APPLICABLE_ON = re.compile(r"bore on it: (.+)$")
"""How the stub's own disposition note names the presentations a record fired on and did not bear on."""


def presentations_named(note: str) -> list[str]:
    """The presentations a not-applicable disposition note names: the tasks after the stub's own marker, else the note itself."""
    m = NOT_APPLICABLE_ON.search(note or "")
    if m:
        return [x.strip() for x in m.group(1).split(",") if x.strip()]
    return [note.strip()] if note and note.strip() else []


def _leaf(parent: dict[str, Any], terms: list[str], context: str) -> dict[str, Any]:
    """A draft body derived from an accepted record's body with its consultation hook replaced — never a second copy."""
    body = json.loads(json.dumps(parent["body"]))
    for latch in body["latches"]:
        if latch["type"] == "consultation":
            latch["guard"]["terms"] = terms
    body["context"] = context
    return body


@handles("nominate")
def _nominate(req):
    brief, bars = req["brief"], req["bars"]
    accepted = brief.get("accepted", [])
    bodies = {d["id"]: d for d in accepted if d.get("body")}
    nominations = []
    for row in brief.get("fusion", []):  # § 10.6 split: one leaf per sub-shape, the parent retiring by coverage migration
        parent = bodies.get(row["record"])
        if parent is None:
            continue
        for terms in (row["applied_on"], row["never_on"]):
            nominations.append({"rung": "new-decision", "rung_why": f"dispositions on {row['record']} are bimodal across sub-shapes: applied on {row['applied_on']}, never on {row['never_on']}; a fused record splits into leaves",
                                "subject": f"split:{row['record']}", "evidence": [], "supersedes": [], "split_from": row["record"], "folded_from": [],
                                "body": _leaf(parent, terms, f"leaf of {row['record']} on the sub-shape {terms}")})
    for row in brief.get("structural_zero", []):  # activation — recall: re-key the record no registered hook reaches
        terms = terms_for(row["latch"], [t for t in row["presented"] if not t.startswith("other(")]) or [t for t in row["presented"] if not t.startswith("other(")][:1]
        if not terms:
            continue
        nominations.append({"rung": "hook-edit", "rung_why": f"{row['record']} is a structural zero: its consultation hook names {row['terms']}, which no boot classifies into; its cue names {terms}, which the window presented",
                            "subject": f"zero:{row['record']}", "evidence": [], "supersedes": [row["record"]], "split_from": None, "folded_from": [],
                            "edit": {"terms": terms}, "body": None})
    for row in brief.get("precision", []):  # activation — precision: fired-but-not-applicable dominating grows not_this by the presentations the notes name
        sessions = sorted({n["session"] for n in row.get("notes", []) if n.get("session")})
        if len(sessions) < bars["decision"]["independent_observations"]:
            continue
        named = [x for n in row.get("notes", []) for x in presentations_named(n.get("note", ""))]
        new = [x for x in dict.fromkeys(named) if x not in row.get("not_this", [])]
        if not new:
            continue
        nominations.append({"rung": "counterfactual-edit", "rung_why": f"{row['record']} fired and did not bear in {row['not_applicable']} of {row['considered']} considered passes; the hook is right and the guard is loose — precision is recovered through not_this, never by shaving the hook",
                            "subject": f"precision:{row['record']}", "evidence": sessions, "supersedes": [row["record"]], "split_from": None, "folded_from": [],
                            "edit": {"not_this": [*row.get("not_this", []), *new]}, "body": None})
    for row in brief.get("recall", []):  # activation — recall: a record the passes needed and no hook reached is re-keyed on what they presented
        if len(row.get("sessions", [])) < bars["decision"]["independent_observations"] or not row.get("missing"):
            continue
        nominations.append({"rung": "hook-edit", "rung_why": f"{row['record']} should have fired: {len(row['sessions'])} independent passes probed for it unconsulted; its hook names {row['hook']} and the passes presented {row['presented']}",
                            "subject": f"recall:{row['record']}", "evidence": [p["session"] for p in row["probes"]], "supersedes": [row["record"]], "split_from": None, "folded_from": [],
                            "edit": {"terms": sorted(set(row["hook"]) | set(row["missing"]))}, "body": None})
    for row in brief.get("convergence", []):  # § 10.6 fold: identical hooks applied together contract into one successor
        a, b = (bodies.get(r) for r in row["records"])
        if not (row["identical_hooks"] and a and b):
            continue
        body = _leaf(a, a["terms"], f"fold of {row['records'][0]} and {row['records'][1]}: applied together in {row['co_applied']} passes on {row['shared_terms']}")
        body["decision"] = f"{a['decision'].rstrip('.')}; {b['decision'][0].lower()}{b['decision'][1:]}"
        nominations.append({"rung": "new-decision", "rung_why": f"{row['records']} were applied together in {row['co_applied']} passes on the same hook; their payloads entail one another and one record carries both",
                            "subject": "fold:" + "+".join(row["records"]), "evidence": [], "supersedes": [], "split_from": None, "folded_from": list(row["records"]),
                            "body": body})
    for group in brief.get("groups", []):
        obs = group["observations"]
        sessions = {o["session"] for o in obs}
        if len(sessions) < bars["decision"]["independent_observations"]:
            continue
        key = lesson_key([o.get("happened") or o.get("noticed") or "" for o in obs])
        if key is None:
            continue
        covered = [d for d in accepted if key in d["decision"].lower() or (key == "batch" and "batched" in d["decision"].lower())]
        if covered:
            continue
        terms = [t for t in group["shape"] if not t.startswith("other(")] or ["error-wrapping"]
        names = [o["name"] for o in obs]
        supersedes = [d["id"] for d in accepted if key == "retry" and "cause" in d["decision"].lower()]
        proposal = next((p for p in brief.get("proposals", []) if lesson_key([p["decision"]]) == key and set(p["evidence"]) & set(names)), None)
        nominations.append({
            "rung": "new-decision",
            "rung_why": ("payload indicted: the superseded record was recalled and applied and the oracle still regressed on task_pass_rate; a re-derived payload supersedes it"
                         if supersedes else "no existing record's counterfactual, hook or register absorbs this fork; the fork is undecided"),
            "subject": key, "evidence": names, "supersedes": supersedes, "split_from": None, "folded_from": [],
            "adopts": proposal["uid"] if proposal else None,
            "sketch": None if proposal else sketch(key, terms, names),
        })
    return {"nominations": nominations}


ARTICLE_INSTANCES: list[tuple[str, Callable[[dict[str, Any]], str | None]]] = [
    ("backward pass admits", lambda i: next((h["id"] for h in i["hypotheses"] if (h.get("outcome") or "").startswith("admitted")), None)),
    ("count with ids", lambda i: next((u["id"] for u in i["dispositions"]), None)),
    ("hypothesis with an anchor", lambda i: next((o["name"] for o in i["observations"] if o["anchor"]), None)),
    ("no context holds two roles", lambda i: next((h["id"] for h in i["hypotheses"] if len(h["roles"]) >= 3), None)),
    ("raises abstraction", lambda i: next((h["id"] for h in i["hypotheses"] if "payload:abstraction" in h["attack_targets"]), None)),
    ("discloses its residue", lambda i: next((d["id"] for d in i["decisions"] if d["residue"]), None) or next((f["session"] for f in i["unevaluable_facts"]), None)),
    ("retirement leg", lambda i: next((d["id"] for d in i["decisions"] if d["status"] == "superseded"), None) or next((d["id"] for d in i["decisions"] if d["retirement_guard"]), None)),
]
"""What the stub consolidator reads an article's words as asking for, and where in the instances it looks."""


def task_names(task_ids: list[str]) -> list[str]:
    """A task's bare name — the suite qualifies ids by family (``genesis/sum_numbers``), and a payload that copies an instance names the task, not the family."""
    return [t.rsplit("/", 1)[-1].lower() for t in task_ids]


def promoted(decision: str, task_ids: list[str]) -> str:
    """The stub's promotion: each task the payload names becomes the shape it stands for, so the lesson no longer names the instance it was seen in."""
    out = decision
    for t in task_names(task_ids):
        out = re.sub(rf"\b{re.escape(t)}\b", "task", out, flags=re.I)
    return re.sub(r"\btask task\b", "task", out, flags=re.I)


@handles("promote")
def _promote(req):
    return {"decision": promoted(req["decision"], req.get("task_ids", []))}


@handles("applies_when")
def _applies_when(req):
    # the cross-shape applicability lens: the consolidator draws the applies-when edges. The stub is conservative — the
    # lesson fires on the terms the sketch proposed and keeps its not_this; broadening the reach beyond them is the model's
    # judgment, and the origin tasks (`floor`) are unioned in by the caller as the lower bound whatever the stub answers.
    return {"fires_on": req.get("proposed_terms", []), "not_this": req.get("not_this", [])}


@handles("anchor")
def _anchor(req):
    out = []
    for article in req["articles"]:
        for cue, pick in ARTICLE_INSTANCES:
            if cue in article["article"]:
                anchor = pick(req["instances"])
                if anchor:
                    out.append({"article": article["id"], "anchor": anchor, "why": f"the instance {anchor} is what the article's words '{cue}' name"})
                break
    return {"anchors": out}


@handles("exemplifies")
def _exemplifies(req):
    if req.get("instance"):
        return {"verdict": "still-holds", "why": f"{req['anchor']} exists in the store and is of the kind the article names"}
    return {"verdict": "moot", "why": "the anchor names nothing"}


IRREDUCIBLE = ("model call failed", "endpoint ", "turn limit", "hidden test raised", "no scripted policy", "final reply was not json")
"""What the stub adjudicator reads as a failure no record could have prevented: the harness or the model's own turn failing, not the world's convention missed."""


@handles("triage")
def _triage(req):
    texts = [str(o.get("happened") or o.get("noticed") or "").lower() for o in req.get("observations", [])]
    texts += [str((r.get("error") or {}).get("message", "")).lower() + " " + str((r.get("error") or {}).get("cause", "")).lower() for r in req.get("rows", [])]
    texts = [t for t in texts if t.strip()]
    if texts and all(any(m in t for m in IRREDUCIBLE) for t in texts):
        return {"verdict": "irreducible", "why": "every row failed in the harness or the model's own turn; no duty a record carries reaches it"}
    return {"verdict": "reducible", "why": "the rows show a convention of the world missed, which a record could carry"}


# --- the examiner ---------------------------------------------------------------------------

@handles("attack")
def _attack(req):
    draft, ev = req["draft"], req["evidence"]
    claims = []  # independence and the watch's direction are the code's readings (hgi.types.MECHANICAL), not the stub examiner's
    for p in draft["body"]["warrant"]["premises"]:
        landed = ("transient" in p["statement"] or "fault" in p["statement"]) and ev.get("fault_rate") == 0
        claims.append({"target": f"premise:{p['id']}", "refutation": p["falsifier"], "reading_taken": True, "landed": landed,
                       "evidence": [f"fault_rate={ev.get('fault_rate')}"]})
    decision = draft["body"]["decision"].lower()
    named = [t for t in task_names(ev.get("task_ids", [])) if t in decision]
    claims.append({"target": "payload:abstraction", "refutation": "the payload names a task instead of the transferable shape",
                   "reading_taken": True, "landed": bool(named), "evidence": [f"the payload names {', '.join(named)}" if named else "the payload text"]})
    lens = req.get("lens")
    if lens:  # one angle per context: the stub answers the lens's claim classes and nothing else
        claims = [c for c in claims if any(c["target"].startswith(prefix) for prefix in lens.get("claims", []))]
    return {"claims": claims}


# --- the adjudicator ----------------------------------------------------------------------------

@handles("verdict")
def _verdict(req):
    attack, oracle = req["attack"], req.get("oracle", {})
    for c in attack["claims"]:
        if c["landed"] and c["target"].startswith("premise:"):
            return {"verdict": f"decline(premise killed: {c['target']})", "amendment": None}
        if c["landed"] and c["target"] == "payload:abstraction":  # amend-only: the payload is restated, the draft is not refused
            return {"verdict": "admit-amended(the payload is restated at the transferable shape; the instances stay as anchors)",
                    "amendment": promoted(req["draft"]["body"]["decision"], req.get("task_ids", []))}
    scorer = req.get("watch_scorer")
    series = oracle.get("series", {}).get(scorer, [])
    if scorer and series and all(v is None for v in series):
        return {"verdict": f"escalate(oracle evidence unevaluable for {scorer})", "amendment": None, "until": None}
    if scorer and series and any(v is None for v in series):  # evidence partly missing and forthcoming: wait for two evaluable runs
        return {"verdict": f"defer(until {scorer} is evaluable on two consecutive runs)", "amendment": None,
                "until": {"scorer": scorer, "comparator": ">=", "value": 0.0, "persistence": 2, "passes": None}}
    return {"verdict": "admit", "amendment": None, "until": None}


@handles("credit")
def _credit(req):
    steers = []
    for a in req["applied"]:
        before, after = a.get("before"), a.get("after")
        if a["applied_count"] > 0 and before is not None and after is not None and after <= before:
            steers.append({"record": a["record"], "slot": "payload", "signature": "recalled-applied-still-corrected",
                           "correction": f"{a['record']} was applied in {a['applied_count']} dispositions and {a['scorer']} did not improve ({before} → {after})",
                           "why_not_caught": "no floor reads the payload's content; residue as disclosed"})
    return {"steers": steers}


@handles("vocabulary")
def _vocabulary(req):
    covered = [t for t in req.get("coder", []) if not t.startswith("other(")]
    if covered:
        return {"verdict": f"decline(the blind coder read the presentations as {covered}; an existing term covers the shape)", "means": None}
    return {"verdict": "admit", "means": f"the presentation {len(req['escapes'])} independent passes escaped to as other({req['term']}); minted by recurrence"}


@handles("ports")
def _ports(req):
    occasions = req.get("occasions", [])
    if len({o["record"] for o in occasions}) >= req.get("bar", 2) and all(str(o.get("warrant") or "").strip() for o in occasions):
        return {"verdict": "admit", "why": f"{len(occasions)} warranted {req['latch_type']} latches on {req['status']} {req['kind']}s from independent records; the declaration under-read the kind"}
    return {"verdict": "decline(the occasions do not meet the bar or carry no warrant)", "why": "the declaration stands"}


@handles("currency")
def _currency(req):
    if req.get("lens") is not None:  # a lens at a crystallization door: retire only a stream that repeats a non-empty product, or a seed that never produced
        if req.get("door") == "variance-collapse" and req.get("repeated_product"):
            return {"verdict": "moot", "why": f"the lens answered {req['walks']} walks with one product; the answer is cacheable and the question retires", "premise": None}
        if req.get("door") == "genesis-deadline" and not req.get("products") and req.get("walks", 0) >= 1:
            return {"verdict": "moot", "why": "walked and never produced anything a consumer took; the question was not where judgment was needed", "premise": None}
        return {"verdict": "still-holds", "why": "an empty or unwalked stream is no signal; the killer-item check keeps the question", "premise": None}
    if req.get("finding") is not None:  # a pass's close-time contradiction: it reverses a premise only when it names one
        named = [p["id"] for p in req.get("premises", []) if p["id"] in str(req["finding"].get("what_changed", "")) + str(req.get("claim", ""))]
        if str(req["finding"].get("slot", "warrant")) == "warrant" and named:
            return {"verdict": "reversed", "why": f"the pass's reading reversed premise {named[0]}", "premise": named[0]}
        return {"verdict": "still-holds", "why": "the finding names no premise of the warrant; self-noticed signal alone settles nothing", "premise": None}
    if req.get("rotted"):
        if req.get("successor"):
            return {"verdict": "still-holds", "why": f"the anchors {req['rotted']} retired into {req['successor']}, which stands for them", "premise": None}
        return {"verdict": "reversed", "why": f"the anchors {req['rotted']} retired with no successor; the warrant cites nothing that stands", "premise": None}
    if req.get("successor"):
        return {"verdict": "reversed", "why": f"the premise is superseded by {req['successor']}", "premise": None}
    if req.get("domain_entered") is False:  # never considered over the window: a count, kept unless the evidence meets the moot condition
        when, ev = str(req.get("moot_when", "")).lower(), req.get("evidence") or {}
        met = (("transient" in when or "fail" in when) and ev.get("fault_rate") == 0) or ("budget" in when and "tool-budget" not in ev.get("presented", []))
        if met and req.get("moot_evidence"):
            return {"verdict": "moot", "why": f"no pass over {req.get('window')} passes entered the domain and the window's evidence meets the moot condition ({req.get('moot_when')})", "premise": None}
        return {"verdict": "still-holds", "why": "never considered is a count; the killer-item check keeps a record whose moot condition the evidence does not meet", "premise": None}
    ratio = req.get("applied_over_considered")
    if ratio is not None and ratio < req.get("threshold", 0.1) and req.get("moot_evidence"):
        return {"verdict": "moot", "why": "the domain is no longer entered"}
    return {"verdict": "still-holds", "why": "the premise stands; the fire is corroborating evidence against the payload, not the warrant", "premise": None}


# --- the re-author ------------------------------------------------------------------------------

MARK = re.compile(r"^\[for [^\]]+\] ")


@handles("reauthor")
def _reauthor(req):
    """Re-author each field for ``model_id``. The stub cannot write for a model it is not, so it marks the
    conditioning it stands in for — enough to prove the text moved with the stamp; not evidence it reads better.
    The mark is idempotent: a re-author over already-marked text re-keys it rather than stacking marks."""
    model = req["model_id"]
    return {"text": {field: f"[for {model}] {MARK.sub('', value)}" for field, value in req["text"].items()}}
