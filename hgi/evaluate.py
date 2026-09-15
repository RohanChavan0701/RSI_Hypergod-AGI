"""§ 9.2 — the oracle runs the pass's evaluation.

The task suite is a ``weave.Dataset``; each scorer is a fact series named
``<evaluation>/<scorer>``; the results land on the session as facts with
``as_of`` and the evaluation-run URI as ``source``. Then the watch evaluator
walks every live revisit latch over the last *persistence* attached runs and
emits a fire, naming its disposer, for every predicate that holds.

Absent data reads ``unevaluable``, never zero.
"""

from __future__ import annotations

import asyncio
import operator
from datetime import datetime
from typing import Any

import weave
from pydantic import PrivateAttr

from hgi import index as _index
from hgi import model as _model
from hgi import tracing
from hgi.store import Store, now
import suite as _suite
from hgi.types import Decision, EvaluationResult, Fact, Fire, Session
from suite import EVALUATION
from suite.agent import Agent
from suite.scorers import SCORERS

COMPARATORS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq, "!=": operator.ne}


def context_records(store: Store, session: Session) -> list[dict[str, Any]]:
    """The decisions the boot selected and whose guard passed — what the agent is conditioned on."""
    out = []
    for c in session.considered:
        if c.via == "constitution" or not c.guard_passed:
            continue
        d: Decision = store.read("decision", c.record)  # type: ignore[assignment]
        out.append({"id": d.id, "decision": d.decision, "terms": d.consultation_terms, "scopes": d.scopes, "stakes": d.summary.stakes})
    return out


class Evaluation(weave.Evaluation):
    """A Weave evaluation whose summary is the scorers' alone: task outputs are heterogeneous by design and carry no mean.

    The per-row scores are kept aside (``row_scores``, by task id) so the
    session's rows can carry the oracle's verdict on each task — the hidden
    test's outcome is disclosed after the fact; the test itself is not.
    """

    _row_scores: dict[str, dict[str, Any]] = PrivateAttr(default_factory=dict)

    @property
    def row_scores(self) -> dict[str, dict[str, Any]]:
        return self._row_scores

    @weave.op
    async def summarize(self, eval_table) -> dict:
        from weave.flow.scorer import get_scorer_attributes
        from weave.flow.util import transpose

        rows = list(eval_table.rows)
        for row in rows:
            output = row.get("output") or {}
            if isinstance(output, dict) and output.get("task"):
                self._row_scores[output["task"]] = {k: v for k, v in (row.get("scores") or {}).items() if isinstance(v, dict)}
        scores = transpose(transpose(rows).get("scores", []))
        summary = {}
        for scorer in self.scorers or []:
            attrs = get_scorer_attributes(scorer)
            summary[attrs.scorer_name] = attrs.summarize_fn(scores.get(attrs.scorer_name, []))
        return summary


async def _evaluate(evaluation: Evaluation, agent: Agent):
    return await evaluation.evaluate.call(evaluation, agent)


def facts_from(summary: dict[str, Any] | None, as_of: datetime, source: str | None) -> dict[str, Fact]:
    summary = summary if isinstance(summary, dict) else {}  # a None or malformed (non-dict) summary reads as no evaluable series, never an AttributeError (item 34)
    facts = {}
    for scorer in SCORERS:
        name = scorer.model_fields["name"].default
        block = summary.get(name) or summary.get(scorer.__name__) or {}
        mean = (block.get("value") or {}).get("mean") if isinstance(block, dict) else None
        series = f"{EVALUATION}/{name}"
        facts[name] = Fact(series=series, value=mean, as_of=as_of, source=source) if mean is not None else \
            Fact(series=series, unevaluable="no row was evaluable on this series", as_of=as_of, source=source)
    return facts


def summary_from_rows(row_scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Rebuild the scorers' summary from the per-row scores kept on the evaluation, for when the traced summary did not
    come back. A Weave flush/pairing timeout returns a ``None`` summary (carry-forward item 34) even though every row was
    scored and :attr:`Evaluation.row_scores` holds the results; each series is the mean of its evaluable rows, the same
    shape weave's own auto-summary produces, so :func:`facts_from` reads it unchanged."""
    summary: dict[str, Any] = {}
    for scorer in SCORERS:
        name = scorer.model_fields["name"].default
        values = [row.get(name, {}).get("value") for row in row_scores.values() if isinstance(row.get(name), dict)]
        evaluable = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
        summary[name] = {"value": {"mean": sum(evaluable) / len(evaluable) if evaluable else None}}
    return summary


def run(store: Store, session: Session) -> Session:
    """Run the suite for ``session``, write its facts, and return the session with ``evaluation`` set."""
    tracing.init()
    agent = Agent(session=session.id, pass_=session.pass_, attached=session.attached,
                  records=context_records(store, session) if session.attached else [],
                  articles=[a.article for a in store.articles()] if session.attached else [],
                  policy="stub" if isinstance(_model.backend("pass"), _model.Stub) else "model")
    world = _suite.current()
    dataset = weave.Dataset(name=world.dataset_name(), rows=world.rows())
    evaluation = Evaluation(name=EVALUATION, dataset=dataset, scorers=[s() for s in SCORERS],
                                  evaluation_name=f"{tracing.run_label()}{EVALUATION} pass {session.pass_} {'attached' if session.attached else 'detached'}")
    with tracing.attributes(session=session.id, pass_=session.pass_, role="pass", attached=session.attached,
                            records_in_context=[r["id"] for r in agent.records]):
        summary, call = asyncio.run(_evaluate(evaluation, agent))
    if not isinstance(summary, dict):  # a Weave flush/pairing timeout returns no summary; rebuild it from the rows already scored (item 34)
        summary = summary_from_rows(evaluation.row_scores)
    stamp = now()
    session.model_id = _model.model_id("pass")
    rows = [{**row, "scores": evaluation.row_scores.get(row["task"], {})} for row in agent.outputs]
    session.evaluation = EvaluationResult(evaluation=EVALUATION, run=tracing.call_uri(call), suite_hash=world.hash,
                                          scores=facts_from(summary, stamp, tracing.call_uri(call)), rows=rows)
    if session.trace_root is None:
        session.trace_root = tracing.call_uri(call)
    return session


# --- the watch evaluator -----------------------------------------------------------------------

def series_values(store: Store, scorer: str, upto: Session, persistence: int) -> list[float | None]:
    """The last ``persistence`` attached runs' values on a scorer, ending at ``upto`` (``None`` where unevaluable)."""
    runs = [s for s in store.all("session") if s.attached and s.evaluation is not None and s.pass_ <= upto.pass_ and s.id != upto.id]  # type: ignore[attr-defined]
    runs = sorted(runs, key=lambda s: s.pass_)[-(persistence - 1):] if persistence > 1 else []
    runs.append(upto)
    return [r.evaluation.scores[scorer].value if scorer in r.evaluation.scores else None for r in runs]


def emit_fires(store: Store, session: Session) -> list[Fire]:
    """Walk every live revisit latch; emit a fire, naming its disposer, where the predicate holds over its persistence window."""
    fires = []
    pending = {(f["record"], f["latch_index"]) for f in _index.undischarged_fires(store)}
    for trigger in _index.triggers(store):
        pred = trigger["predicate"]
        if pred["evaluation"] != EVALUATION or (trigger["record"], trigger["latch_index"]) in pending:
            continue
        values = series_values(store, pred["scorer"], session, pred["persistence"])
        if len(values) < pred["persistence"] or any(v is None for v in values):
            continue  # unevaluable never fires; it reads unevaluable, loudly, on the projection
        if all(COMPARATORS[pred["comparator"]](v, pred["value"]) for v in values):
            fire = Fire(id=store.mint("fire"), fired_at=now(), latch={"record": trigger["record"], "index": trigger["latch_index"]},
                        edge_event={"evaluation": EVALUATION, "pass": session.pass_, "scorer": pred["scorer"], "observed": values[-1],
                                    "source": session.evaluation.run if session.evaluation else None},
                        guard_result=True, disposer=trigger["disposer"], disposition={"act": trigger["owed_act"]})
            store.write(fire)
            fires.append(fire)
            session.fires_seen.append(fire.id)
    return fires


# --- the command --------------------------------------------------------------------------------

def evaluate_session(store: Store, session_id: str | None, pass_: int | None, detached: bool) -> Session:
    if detached:
        if pass_ is None:
            raise SystemExit("a detached pass names its pass number")
        session = Session(id=store.mint("session"), pass_=pass_, started_at=now(), attached=False)
    else:
        if session_id is None:
            raise SystemExit("--session names the booted session")
        session = store.read("session", session_id)  # type: ignore[assignment]
        if session.closed_at is not None:
            raise SystemExit(f"{session_id} is closed")
    session = run(store, session)
    fires = emit_fires(store, session) if session.attached else []
    if detached:
        session.closed_at = now()
        session.carry_forward = "detached pass: no boot, no close; the evaluation is the whole record"
    store.write(session)
    scores = ", ".join(f"{k}={'unevaluable' if f.value is None else f'{f.value:.2f}'}" for k, f in session.evaluation.scores.items())
    print(f"{session.id} pass {session.pass_} {'attached' if session.attached else 'detached'}: {scores}")
    for f in fires:
        print(f"  fire {f.id}: {f.latch.record} latch {f.latch.index} on {f.edge_event.scorer}={f.edge_event.observed}; owed {f.disposition.act} by {f.disposer}")
    return session


def register(add, store_of, finish) -> None:
    p = add("evaluate", "run the oracle; write facts; emit fires")
    p.add_argument("--session", help="the booted session to evaluate")
    p.add_argument("--pass", dest="pass_", type=int, help="the pass number (detached runs)")
    p.add_argument("--detached", action="store_true", help="an ablation pass: same agent, same suite, no boot or close")
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))
    from hgi import lens_battery
    lens_battery.register(add, store_of, finish)


def _cmd(args, store_of, finish) -> int:
    store = store_of(args)
    session = evaluate_session(store, args.session, args.pass_, args.detached)
    fired = " ".join(session.fires_seen)
    finish(store, args, f"Evaluate {session.id} pass {session.pass_}" + (f": fired {fired}" if fired else ""))
    return 0
