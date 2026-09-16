"""§ 8.1 — boot assembly. ``hgi boot --session S-nnnn --pass n`` performs, in order:

1. constitution — every live article loads unconditionally, under the cap;
2. carry-forward — the previous attached session's ``carry_forward`` and the
   undischarged fires whose disposer is the working pass;
3. work-shape classification — a model call whose output is parsed against
   the registry; escapes are recorded on the session;
4. stage-one selection — the hook-major index matched against the work-shape
   terms; the lexical nominator over summaries logs its hits as considered
   with the guard failed unless a registered term also matched; the guard
   evaluator decides each fire; records whose hooks share every term with no
   lineage edge between them co-apply with no specificity order, and the plan
   says so on one line rather than ranking or dropping one;
5. composition — the boot lenses walk, one context per angle, and the
   consultation plan prints: the count and the ids entering context, each
   with its owed act.

The assembled window is the query's result set. A consultation is presumed,
never hedged: the pass's only degree of freedom is what the store holds.
"""

from __future__ import annotations

import json
from typing import Any

from hgi import coder as _coder
from hgi import index as _index
from hgi import lint as _lint
from hgi import model as _model
from hgi import roles
from hgi import tracing
from hgi.store import Store, now
from hgi.types import HOOK_AXES, Considered, Consulted, Decision, LensAnswer, Session, WorkShape
import suite as _suite

WORKING_PASS = "the working pass"


def previous_session(store: Store, pass_: int) -> Session | None:
    earlier = [s for s in store.all("session") if s.attached and s.closed_at is not None and s.pass_ < pass_]  # type: ignore[attr-defined]
    return max(earlier, key=lambda s: s.pass_) if earlier else None


def classify(store: Store, session: Session) -> WorkShape:
    """Step 3: the pass names the terms its presentations exhibit, in registry terms; anything the vocabulary lacks is an escape.

    The vocabulary offered spans both hook axes (:data:`hgi.types.HOOK_AXES`): the tasks' declared work-shapes floor the
    result, and the model's classification adds the work-shapes *and* the conventions it reads on top — a paged listing, a
    coded value, a versioned route the presentation reveals — so a consultation hook keyed on that convention can fire.
    Mirrors ``consolidate.anchor_terms`` seeding a record's hook on the write side. A convention hidden in the presentation
    (visible only once the work fails) is left unnamed, and its hook simply does not fire — the honest floor, no worse than
    a work-shape the prompt does not reveal.
    """
    terms = store.registry.terms_over(*HOOK_AXES)
    c = _model.complete("pass", roles.request("classify", presentations=_suite.current().presentations(), terms=terms), session=session.id, pass_=session.pass_)
    out = c.json_or({})  # a garbled classify reply reads as no added terms; the tasks' declared shapes still floor the presented terms
    declared = {sh for t in _suite.current().tasks for sh in t.shapes if sh in terms}
    registered = sorted(declared | {t for t in out.get("terms", []) if t in terms})
    escapes = [t for t in out.get("terms", []) if t not in terms and t.startswith("other(")] + list(out.get("escapes", []))
    return WorkShape(terms=registered, escapes=escapes)


def select(store: Store, session: Session) -> list[Considered]:
    """Step 4: stage one. Exact match over registered terms; the lexical nominator only nominates."""
    hooks = _index.read(store, "hooks")
    shape = session.work_shape.model_dump()
    considered: dict[str, Considered] = {}
    for term in session.work_shape.terms:
        for cell in hooks.get(term, []):
            c = considered.setdefault(cell["record"], Considered(record=cell["record"], via="index", guard_passed=False, owed_act=cell["owed_act"]))
            c.terms_matched.append(term)
    for c in considered.values():
        d: Decision = store.read("decision", c.record)  # type: ignore[assignment]
        passed, why, _ = _coder.guard(shape, {"terms": d.consultation_terms, "not_this": d.consultation_not_this}, _suite.current().presentations(),
                                      session=session.id, pass_=session.pass_)
        c.guard_passed = passed
    presented = _index.tokens(" ".join(p["prompt"] for p in _suite.current().presentations()))
    for row in _index.read(store, "summaries"):
        if row["record"] in considered or row["status"] != "accepted":
            continue
        overlap = presented & _index.tokens(row["latch"])
        if len(overlap) >= 2:
            considered[row["record"]] = Considered(record=row["record"], via="lexical", guard_passed=False, owed_act="apply",
                                                   terms_matched=sorted(overlap))
    return sorted(considered.values(), key=lambda c: c.record)


def walk_lenses(store: Store, session: Session, host: str, subject_for) -> list[LensAnswer]:
    """One context per angle and per item: ``subject_for(lens)`` returns the subject, or a list of subjects each walked in
    its own context (a lens that touches the item is walked once per item). The adjudicator is never the answerer; a
    finding with no id or anchor is not filed."""
    answers = []
    for lens in store.registry.lenses(host):
        subjects = subject_for(lens)
        for subject in (subjects if isinstance(subjects, list) else [subjects]):
            payload = roles.request("lens", lens={"id": lens.id, "angle": lens.angle, "counterfactual": lens.counterfactual, "product": lens.product},
                                    subject=subject, empty_is_legal=roles.EMPTY_LENS_IS_LEGAL)
            c = _model.complete("pass", payload, session=session.id, pass_=session.pass_,
                                records_in_context=[x.record for x in session.considered if x.guard_passed])
            out = c.json_or({})  # a garbled lens reply is a legal empty answer (item 34), not a crash: it files no finding
            answers.append(LensAnswer(lens=lens.id, answer=str(out.get("answer", "")), findings=[f for f in out.get("findings", []) if isinstance(f, dict)], call=c.call))
    return answers


def boot(store: Store, session_id: str | None, pass_: int) -> Session:
    tracing.init()
    session = Session(id=session_id or store.mint("session"), pass_=pass_, started_at=now(), model_id=_model.model_id("pass"), attached=True)
    if store.exists("session", session.id):
        raise SystemExit(f"{session.id} already exists")

    articles = store.articles()
    prev = previous_session(store, pass_)
    owed = [f for f in _index.undischarged_fires(store) if f["disposer"] == WORKING_PASS]
    session.fires_seen = [f["id"] for f in owed]
    session.work_shape = classify(store, session)
    session.considered = [Considered(record=a.id, via="constitution", guard_passed=True, owed_act="apply") for a in articles] + select(store, session)

    consulted = [c for c in session.considered if c.guard_passed and c.via != "constitution"]
    session.lens_answers = walk_lenses(store, session, "boot", lambda lens: {
        "consulted": [{"record": c.record, "terms_matched": c.terms_matched, **_summary(store, c.record)} for c in consulted],
        "presentations": _suite.current().presentations(),
        "unreached": [row for row in _index.read(store, "summaries") if row["record"] not in {c.record for c in consulted}],
    })
    session.consulted = [Consulted(record=c.record) for c in consulted]
    store.write(session)

    print(plan(store, session, articles, prev, owed))
    for f in _lint.check_pricing(store, session.model_id):
        print(f)
    return session


def _summary(store: Store, record: str) -> dict[str, Any]:
    d: Decision = store.read("decision", record)  # type: ignore[assignment]
    return {"latch": d.summary.latch, "stakes": d.summary.stakes, "not_this": d.summary.not_this}


CO_APPLYING = "no specificity order; dispose each on its own rows"
"""What the plan and the dispose request say of an antichain: records that co-apply are never ranked or dropped (§ 16.17) —
the conflict is shown, and the pass disposes each on the rows it bore on."""


def lineage_edge(a: Decision, b: Decision) -> bool:
    """Whether a lineage edge runs between two records — one supersedes, leaves or folds the other — which is a specificity order."""
    return any(b.id in edges for edges in (a.lineage.supersedes, a.lineage.superseded_by, a.lineage.folded_from, [a.lineage.split_from])) or \
        any(a.id in edges for edges in (b.lineage.supersedes, b.lineage.superseded_by, b.lineage.folded_from, [b.lineage.split_from]))


def co_applying(store: Store, records: list[str]) -> list[list[str]]:
    """The antichains among consulted records: groups of two or more whose consultation hooks share every term and between which
    no lineage edge runs. They enter context side by side with no specificity order; nothing here ranks or drops one."""
    decisions: dict[str, Decision] = {r: store.read("decision", r) for r in records}  # type: ignore[misc]
    by_hook: dict[frozenset[str], list[str]] = {}
    for r, d in decisions.items():
        by_hook.setdefault(frozenset(d.consultation_terms), []).append(r)
    groups = []
    for ids in by_hook.values():
        ordered = {r for r in ids for other in ids if r != other and lineage_edge(decisions[r], decisions[other])}
        rest = sorted(r for r in ids if r not in ordered)
        if len(rest) >= 2:
            groups.append(rest)
    return sorted(groups)


def plan(store: Store, session: Session, articles, prev: Session | None, owed: list[dict]) -> str:
    lines = [f"== {session.id} pass {session.pass_} — consultation plan ==",
             f"constitution: {len(articles)} articles " + " ".join(a.id for a in articles),
             f"carry-forward: {prev.carry_forward if prev else '(first pass)'}",
             f"fires owed to the working pass: {len(owed)} " + " ".join(f['id'] for f in owed),
             f"work-shape: {session.work_shape.terms} escapes={session.work_shape.escapes}"]
    fired = [c for c in session.considered if c.via != "constitution" and c.guard_passed]
    failed = [c for c in session.considered if c.via != "constitution" and not c.guard_passed]
    lines.append(f"consulting {len(fired)}: " + ", ".join(f"{c.record} ({', '.join(c.terms_matched)}) owed {c.owed_act}" for c in fired))
    for group in co_applying(store, [c.record for c in fired]):
        lines.append(f"co-applying: {', '.join(group)} — {CO_APPLYING}")
    unwatched = [c.record for c in fired if _index.watch_of(store.read("decision", c.record)) == _index.UNWATCHED]  # type: ignore[arg-type]
    if unwatched:
        lines.append(f"unwatched {len(unwatched)}: " + ", ".join(unwatched) + " — no world-state watch can send the warrant back; only the ratio and propagation can")
    if failed:
        lines.append(f"considered, guard failed {len(failed)}: " + ", ".join(f"{c.record} via {c.via}" for c in failed))
    for a in session.lens_answers:
        lines.append(f"lens {a.lens}: {len(a.findings)} findings")
    return "\n".join(lines)


def register(add, store_of, finish) -> None:
    p = add("boot", "assemble context; print the consultation plan")
    p.add_argument("--session", help="the session id to open (minted when omitted)")
    p.add_argument("--pass", dest="pass_", type=int, required=True)
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))


def _cmd(args, store_of, finish) -> int:
    store = store_of(args)
    session = boot(store, args.session, args.pass_)
    finish(store, args, f"Boot {session.id} pass {session.pass_}: consulting " + (" ".join(c.record for c in session.consulted) or "nothing"))
    return 0
