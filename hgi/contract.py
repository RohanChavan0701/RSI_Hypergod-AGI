"""``hgi roles`` — the role contracts, exercised one request at a time against a real store.

    hgi roles try <request> --store <arm store> [--session S-n] [--draft <uid>] [--out <dir>]
    hgi roles pricing                             # every role prompt's priced_for against the roster in scope

``try`` builds the named request the way the loop builds it — from the
sessions, observations and decisions of a *copy* of the store, so nothing
is written to the original — sends it to the role's backend in scope (the
environment's endpoint, or the stub), and reports the raw reply, how it
parsed, and, for a drafting request, every refusal the floor would name.
A request that needs a draft (``attack``, ``verdict``) takes one from the
store's proposals by uid, or drafts one with the stub consolidator over the
brief when none is named. Every request and reply also lands in ``--out``
(the reply log of :mod:`hgi.model`), so a contract change is measured
against the same inputs before and after.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

import suite as _suite
from hgi import boot as _boot
from hgi import close as _close
from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi import model as _model
from hgi import registry as _registry
from hgi import reviews as _reviews
from hgi import roles
from hgi.store import Store, now
from hgi.types import HOOK_AXES, Consolidation, Decision, Draft, Session

Builder = Callable[[Store, Any], tuple[str, str]]
"""(role, request json) for a request name, from the store copy and the parsed arguments."""

BUILDERS: dict[str, Builder] = {}


def builder(name: str):
    def deco(fn: Builder):
        BUILDERS[name] = fn
        return fn
    return deco


def _session(store: Store, args) -> Session:
    if args.session:
        return store.read("session", args.session)  # type: ignore[return-value]
    closed = [s for s in store.all("session") if s.attached and s.evaluation is not None]  # type: ignore[attr-defined]
    if not closed:
        raise SystemExit("the store holds no evaluated attached session; name one with --session")
    return max(closed, key=lambda s: s.pass_)  # type: ignore[return-value]


def _rows(session: Session) -> list[dict[str, Any]]:
    return session.evaluation.rows if session.evaluation else []


@builder("classify")
def _classify(store, args):
    return "pass", roles.request("classify", presentations=_suite.current().presentations(), terms=store.registry.terms_over(*HOOK_AXES))


@builder("guard")
def _guard(store, args):
    s = _session(store, args)
    decisions = store.decisions("accepted")
    if not decisions:
        raise SystemExit("guard needs an accepted decision in the store")
    d: Decision = decisions[0]
    return "coder", roles.request("guard", work_shape=s.work_shape.model_dump(), hook={"terms": d.consultation_terms, "not_this": d.consultation_not_this},
                                  presentations=_suite.current().presentations())


@builder("lens")
def _lens(store, args):
    s = _session(store, args)
    lens = next((l for l in store.registry.lenses() if l.id == (args.lens or "L-0004")), None)
    if lens is None:
        raise SystemExit(f"no lens {args.lens!r}")
    subject = {"consulted": [_close._decision_view(store, c.record) for c in s.consulted], "rows": _rows(s), "fires": s.fires_seen,
               "scores": {k: f.value for k, f in s.evaluation.scores.items()}} if lens.host == "close" else \
              {"consulted": [{"record": c.record, "terms_matched": c.terms_matched, **_boot._summary(store, c.record)} for c in s.consulted],
               "presentations": _suite.current().presentations(), "unreached": _index.read(store, "summaries")}
    return "pass", roles.request("lens", lens={"id": lens.id, "angle": lens.angle, "counterfactual": lens.counterfactual, "product": lens.product}, subject=subject)


@builder("dispose")
def _dispose(store, args):
    s = _session(store, args)
    consulted = [_close._decision_view(store, c.record) for c in s.consulted]
    if not consulted:
        raise SystemExit(f"{s.id} consulted nothing; name a session that did with --session")
    owed = _close.fires_owed(store, s)
    return "pass", roles.request("dispose", consulted=consulted, rows=_rows(s), vocabulary=store.registry.terms("use-time-disposition"),
                                 co_applying=[{"records": g, "reading": _boot.CO_APPLYING} for g in _boot.co_applying(store, [c.record for c in s.consulted])],
                                 fires_owed=[f.model_dump(by_alias=True, mode="json") for f in owed])


@builder("propose")
def _propose(store, args):
    s = _session(store, args)
    return "pass", roles.request("propose", **_close.propose_content(store, s))


@builder("coding")
def _coding(store, args):
    obs = store.observations("open") or store.observations(None)
    return "coder", roles.request("coding", observations=[{"name": o.name, "noticed": o.happened} for o in obs], terms=store.registry.terms("convention"))


def _brief(store: Store) -> tuple[Consolidation, dict[str, Any], list[Session]]:
    sessions, last = _consolidate.sessions_since_last(store)
    if not sessions:
        sessions = sorted((s for s in store.all("session") if s.attached and s.closed_at is not None), key=lambda s: s.pass_)  # type: ignore[attr-defined]
    record = Consolidation(id="K-0000", started_at=now(), after_pass=max((s.pass_ for s in sessions), default=last), sessions_read=[s.id for s in sessions])
    with _model.override("coder", _model.Stub()):  # the grouping is the stub's here; the request under test is the one named
        brief = _consolidate.build_brief(store, record, sessions)
    return record, brief, sessions


@builder("nominate")
def _nominate(store, args):
    record, brief, _ = _brief(store)
    return "consolidator", roles.request("nominate", **_consolidate.nominate_content(store, brief))


def _draft(store: Store, args) -> tuple[Draft, dict[str, Any]]:
    record, brief, _ = _brief(store)
    if args.draft:
        draft = next((d for d in store.drafts() if d.uid == args.draft), None)
        if draft is None:
            raise SystemExit(f"no draft {args.draft} in the store's proposals")
        return draft, brief
    with _model.override("consolidator", _model.Stub()):
        raws = _consolidate.nominate(store, record, brief)
    if not raws:
        raise SystemExit("the stub consolidator drafts nothing from this brief; name a draft with --draft")
    return _consolidate.draft_from(store, record, raws[0]), brief


@builder("attack")
def _attack(store, args):
    """One angle of the examiner fan: ``--lens`` names the examiner lens (default the first registered); a register with no
    examiner lens builds the single-context attack."""
    draft, brief = _draft(store, args)
    lenses = store.registry.lenses("examiner")
    lens = next((l for l in lenses if l.id == args.lens), lenses[0] if lenses else None)
    named = {"lens": {"id": lens.id, "angle": lens.angle, "counterfactual": lens.counterfactual, "claims": lens.claims, "product": lens.product}} if lens else {}
    return "examiner", roles.request("attack", **named, draft=draft.model_dump(by_alias=True, mode="json"), evidence=_consolidate.evidence_pack(store, draft, brief))


@builder("verdict")
def _verdict(store, args):
    draft, brief = _draft(store, args)
    evidence = _consolidate.evidence_pack(store, draft, brief)
    with _model.override("examiner", _model.Stub()):
        attack_payload, _ = _consolidate.attack(store, Consolidation(id="K-0000", started_at=now(), after_pass=0, sessions_read=[]), draft, evidence)
    return "adjudicator", roles.request("verdict", draft=draft.model_dump(by_alias=True, mode="json"), attack=attack_payload,
                                        oracle={"series": evidence["series"], "scores": evidence["scores"]}, watch_scorer=evidence["watch_scorer"], bars=store.registry.bars)


@builder("credit")
def _credit(store, args):
    _, brief, _ = _brief(store)
    if not brief["credit"]:
        raise SystemExit("no record was applied in the brief's window; credit has nothing to read")
    return "adjudicator", roles.request("credit", applied=brief["credit"])


@builder("currency")
def _currency(store, args):
    rows = [r for r in _index.competence(store) if r["applied_over_considered"] is not None]
    if not rows:
        raise SystemExit("no accepted decision has a competence row; currency has nothing to read")
    row = rows[0]
    d: Decision = store.read("decision", row["record"])  # type: ignore[assignment]
    guard = d.lifecycle.retirement.guard
    return "adjudicator", roles.request("currency", record=d.id, applied_over_considered=row["applied_over_considered"], threshold=guard.applied_over_considered_below,
                                        moot_when=d.lifecycle.moot_when, moot_evidence=row["considered"] > 0 and row["applied"] == 0)


@builder("triage")
def _triage(store, args):
    """The noise filter over a recurrence at the bar: the group with the most sessions, its observations and the rows they anchor."""
    _, brief, _ = _brief(store)
    groups = brief.get("groups", [])
    if not groups:
        raise SystemExit("the brief carries no group; triage has nothing to read")
    group = max(groups, key=lambda g: len(g.get("sessions") or [o.get("session") for o in g.get("observations", []) if isinstance(o, dict)]))
    evidence = _consolidate.group_evidence(store, group)
    return "adjudicator", roles.request("triage", shape=group.get("shape"), observations=evidence["observations"], rows=evidence["rows"],
                                        vocabulary=store.registry.terms("reality-verdict"))


@builder("ports")
def _ports(store, args):
    """One off-declaration channel of the port-miss stream: the cluster over the most independent records, its occasions."""
    clusters = _reviews.port_clusters(store)
    if not clusters:
        raise SystemExit("no live latch is admitted off its port declaration; ports has nothing to read")
    cluster = max(clusters, key=lambda c: len(c["records"]))
    bar = store.registry.bars.get("vocabulary", {}).get("independent_escapes", 2)
    return "adjudicator", roles.request("ports", kind=cluster["kind"], status=cluster["status"], latch_type=cluster["latch_type"],
                                        mark="forbidden", occasions=cluster["occasions"], bar=bar)


# --- reading the reply ------------------------------------------------------------------------

def parse_report(store: Store, name: str, out: Any) -> list[str]:
    """What the loop would make of the reply: the parsed shape, and every refusal for a drafting request."""
    lines = []
    if name in ("nominate", "propose"):
        key = "nominations" if name == "nominate" else "drafts"
        raws = roles.drafts_in(out, key)
        lines.append(f"{len(raws)} {key} carried" + (f" (top-level keys: {sorted(out)})" if isinstance(out, dict) else " (reply is not an object)"))
        record = Consolidation(id="K-0000", started_at=now(), after_pass=0, sessions_read=[])
        for i, raw in enumerate(raws):
            try:
                draft = roles.draft_of(store, raw, proposed_by=record.id, name=f"P-{i}", model_id=_model.model_id("pass"))
            except ValueError as e:
                lines.append(f"  [{i}] refused at parse: {roles.refusal(e)}")
                continue
            floor = [f for f in _lint.check_draft(store, draft) if f.level == "fail"]
            lines.append(f"  [{i}] parsed: {draft.rung} — {draft.body.decision[:120]!r}" + (f"; floor: " + "; ".join(f.message for f in floor) if floor else "; floor clean"))
    elif name == "verdict":
        v = out.get("verdict") if isinstance(out, dict) else None
        try:
            store.registry.check("adjudicator-verdict", str(v))
            lines.append(f"verdict {v!r} is in the vocabulary")
        except ValueError as e:
            lines.append(f"verdict refused: {e}")
    elif name == "attack":
        claims = out.get("claims", []) if isinstance(out, dict) else []
        lines.append(f"{len(claims)} claims; targets {[c.get('target') for c in claims if isinstance(c, dict)]}; landed {[c.get('landed') for c in claims if isinstance(c, dict)]}")
    elif name == "credit":
        lines.append(f"{len(out.get('steers', [])) if isinstance(out, dict) else 0} steers")
    elif name == "currency":
        lines.append(f"verdict {out.get('verdict') if isinstance(out, dict) else None!r}")
    elif name in ("triage", "ports"):
        vocab = "reality-verdict" if name == "triage" else "adjudicator-verdict"
        v = out.get("verdict") if isinstance(out, dict) else None
        try:
            store.registry.check(vocab, str(v))
            lines.append(f"verdict {v!r} is in the {vocab} vocabulary; why {str(out.get('why', ''))[:160]!r}")
        except ValueError as e:
            lines.append(f"verdict {v!r} refused: {e}")
    elif name == "lens":
        lines.append(f"{len(out.get('findings', [])) if isinstance(out, dict) else 0} findings; answer {str(out.get('answer', ''))[:100]!r}" if isinstance(out, dict) else "reply is not an object")
    else:
        lines.append(json.dumps(out)[:300])
    return lines


def try_request(root: Path, name: str, args) -> int:
    if name not in BUILDERS:
        raise SystemExit(f"no builder for {name!r}; requests are {sorted(BUILDERS)}")
    scratch = Path(tempfile.mkdtemp(prefix="hgi-roles-"))
    shutil.copytree(root, scratch / "store")
    reg = _registry.load(scratch / "store")
    token = _registry.use(reg)
    if args.out:
        os.environ[_model.REPLY_LOG] = str(args.out)
    try:
        store = Store(scratch / "store", registry=reg)
        role, payload = BUILDERS[name](store, args)
        print(f"== {name} → {role} on {_model.model_id(role)}; request {len(payload)} chars ==")
        c = _model.complete(role, payload, session="K-0000" if role != "pass" else None)
        print(f"-- reply ({len(c.text)} chars) --\n{c.text[:args.show]}" + ("\n…" if len(c.text) > args.show else ""))
        try:
            out = c.json()
        except (ValueError, json.JSONDecodeError) as e:
            print(f"-- not JSON: {e}")
            return 1
        print("-- reading --")
        for line in parse_report(store, name, out):
            print(line)
        return 0
    finally:
        _registry.reset(token)
        shutil.rmtree(scratch, ignore_errors=True)


def pricing() -> str:
    roster = _model.roster()
    return "\n".join(f"{role:13} priced for {roles.priced_for(role) or '(unpriced)'}; runs {roster[role]}" +
                     ("" if roles.is_priced_for(role, roster[role]) else "  ← unpriced for this model") for role in roles.ROLES)


def register(add, store_of, finish) -> None:
    p = add("roles", "exercise one role request against a copy of a store, or list the role prompts' pricing")
    p.add_argument("action", choices=["try", "pricing"])
    p.add_argument("request", nargs="?", help=f"for `try`: one of {sorted(BUILDERS)}")
    p.add_argument("--session", help="the session the request is built from (default: the latest evaluated attached one)")
    p.add_argument("--lens", help="for `lens`: the lens id (default L-0004); for `attack`: the examiner lens whose angle is walked (default the first)")
    p.add_argument("--draft", help="for `attack` and `verdict`: a proposal uid in the store")
    p.add_argument("--out", help="a directory for the reply log")
    p.add_argument("--show", type=int, default=4000, help="characters of the raw reply to print")
    p.set_defaults(fn=lambda args: _cmd(args, store_of))


def _cmd(args, store_of) -> int:
    if args.action == "pricing":
        print(pricing())
        return 0
    if not args.request:
        raise SystemExit("`try` names a request")
    root = Path(args.store) if args.store else _registry.default_root()
    return try_request(root, args.request, args)
