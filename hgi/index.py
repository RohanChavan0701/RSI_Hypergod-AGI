"""Projections: regenerated read models under ``<store>/index/``, never hand-edited.

Each projection is a pure function of the store, listed in :data:`PROJECTIONS`.
``regenerate`` writes them all; ``check`` reports which committed projections
differ from regeneration (the projection-coherence gate of the lint).

Every cell obeys the settlement test (spec § 8.2): it carries what a reader
cannot comply with without opening the record — ids, hook prose, exclusions,
stakes, owed acts — and never a compliable sentence. The decision sentence
itself is evicted to the full record; :data:`FORBIDDEN_CELL_KEYS` names the
fields the lint refuses in any cell.

One file under ``index/`` is not a projection: ``controls.json``, the blind
coder's seeded-control telemetry, written by ``hgi lens-battery``
(:mod:`hgi.lens_battery`) the way the lens register's telemetry is, and left
alone by regeneration.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Callable, Iterable

from hgi.registry import is_escape, read_json, write_json
from hgi.store import Store
from hgi.types import MECHANICAL, Decision, Disposition, Draft, Fire, Observation, Session

FORBIDDEN_CELL_KEYS = frozenset({"decision", "duty", "then", "article", "context", "options"})
"""Fields whose content a reader could obey directly from a cell; the settlement test evicts them."""

_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> set[str]:
    """Crude stems for the lexical nominator: lower-cased alphanumerics with a trailing ``s``/``ing``/``ed`` stripped."""
    out = set()
    for t in _TOKEN.findall((text or "").lower()):
        for suffix in ("ing", "ed", "es", "s"):
            if len(t) > len(suffix) + 2 and t.endswith(suffix):
                t = t[: -len(suffix)]
                break
        if len(t) > 2:
            out.add(t)
    return out


# --- self-reference: a finding about the store's own machinery, not the task's world (carry-forward item 48) --------

_LOOP_SUBJECT_CUES = (
    "no rule matched", "no rule applied", "no applicable rule", "no matching rule", "no matching hook",
    "no record matched", "no store record", "no store records", "no records consulted", "no record consulted",
    "no records were consulted", "no record was consulted", "nothing was consulted",
    "records consulted", "record consulted", "record should have fired", "record should have matched",
    "rule should have fired", "should have been consulted", "which record should", "which record fired",
    "consult the store", "the store's rule", "the store's rules", "the check record", "no records applied",
)
"""Phrases whose grammatical subject is a store record or the loop's own consultation/routing machinery — a finding about
*which record should have fired* rather than about the task's world. The stream-run artifact ("no store records consulted",
"the check record should have fired", "no rule matched", "no matching rule for text2sql generation") is exactly this class.
It is deliberately narrow: it matches a store *record* or the *consultation* act as the subject, never the bare word
"rule"/"hook"/"store", so L-0010's off-map coverage signal ("work failed and matched no hook") — whose subject is the work
— is not swept in even before its call site exempts it."""

_QUOTED = re.compile(r"""(['"`])[^'"`]+\1""")
_COMPARISON = re.compile(r"(==|!=|<=|>=|(?<![<>=!])=(?!=))")


def has_world_content(noticed: str) -> bool:
    """Whether a noticing states a checkable task-world fact — a quoted literal or an explicit comparison. A finding that
    names a store record *beside* a world convention ("D-0004 should have fired because status is 'A' not 'approved'") is
    mixed, and mixed findings are kept: the self-reference filter drops only a finding that is *purely* store-machinery.

    This is the mechanical-evaluability test the price-zero transcription reads (carry-forward item 58 lever B): a
    ``happened`` naming a checkable token settles mechanically through its anchor and may transcribe to the fact layer with
    no adjudication; one naming none is ambiguous and surfaces to the human instead."""
    return bool(_QUOTED.search(noticed or "") or _COMPARISON.search(noticed or ""))


_has_world_content = has_world_content  # the self-reference filter's earlier private name


def world_content_tokens(text: str) -> list[str]:
    """The quoted literals of a noticing — the canonical, mechanically-extractable world-content tokens (a status literal,
    a column, a route, a keyword). Empty when the text quotes none. The variance/ripeness measure groups a cluster's
    members by these (carry-forward item 58 lever A): members naming the same concrete world-fact share a token and the
    cluster reads low world-content variance. The broader mechanical-checkability test :func:`has_world_content` also
    counts a bare comparison; this returns only the strong, canonical tokens."""
    return [m.group(0) for m in _QUOTED.finditer(text or "")]


def world_content_key(text: str) -> str:
    """The canonical grouping key for a settled ``happened``: its quoted world-content literals
    (:func:`world_content_tokens`) lowercased, de-duplicated and sorted, joined by ``|`` — with the lowercased,
    whitespace-normalized whole sentence as the fallback token when it quotes none. Two ``happened`` naming the same
    concrete world-fact share a key, whatever prose surrounds it and however the coder labels the convention.

    This is the one key the world-content axis is read on, so a world-fact is grouped, named and de-duplicated the same
    way everywhere: :func:`hgi.consolidate.world_content_variance` measures the modal-token fraction over it, the
    price-zero happenstance series (:func:`hgi.consolidate._happenstance_series`) names a fact by it so one world-fact
    transcribed across rounds lands one series, the grouping pass canonicalizes a recurring escape label to the one the
    same world-fact first carried, and the dedup guard routes a nomination resting only on already-anchored world-facts to
    corroboration rather than a twin decision (carry-forward item 61)."""
    lits = sorted({t.lower() for t in world_content_tokens(text or "")})
    return "|".join(lits) if lits else " ".join((text or "").lower().split())


def self_referential(noticed: str, anchor: Any) -> bool:
    """Whether a finding's subject is a store record or the loop, not the task's world (carry-forward item 48).

    Two derivable signals: the anchor names a store *record* (a finding pointing at a record, not a task row/artifact),
    or the noticing's subject is the loop's own consultation/routing machinery (:data:`_LOOP_SUBJECT_CUES`). Conservative
    in two ways: a mixed noticing that also states a world convention is kept (:func:`_has_world_content`), and the caller
    decides scope — the off-map coverage lens (L-0010), whose product is legitimately about missing coverage, is exempt.
    """
    rec = anchor.get("record") if isinstance(anchor, dict) else getattr(anchor, "record", None)
    text = (noticed or "").lower()
    loop_subject = bool(rec) or any(cue in text for cue in _LOOP_SUBJECT_CUES)
    if not loop_subject:
        return False
    return not _has_world_content(noticed)


# --- projections --------------------------------------------------------------

def hooks(store: Store) -> dict[str, list[dict[str, Any]]]:
    """Hook-major: for each registered hook term, the accepted decisions whose consultation latches carry it.

    A hook term is drawn from either hook axis (:data:`hgi.types.HOOK_AXES`) — a work-shape or a convention — so a lesson
    keyed on the convention it is about is reached when the boot classification presents that convention, exactly as a
    work-shape-keyed one is reached on its work-shape. An ``other(<what>)`` escape in a guard is legal to write and reaches
    nothing here: no boot classifies into an escape, so a record keyed only on escapes is a structural zero until the term
    is minted and the hook re-keyed. A latch is worth exactly as much as the governance of its key-space.
    """
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in store.decisions("accepted"):
        for i, latch in enumerate(d.all_latches()):
            if latch.type != "consultation" or latch.lifecycle.status != "live":
                continue
            for term in latch.guard.terms:
                if is_escape(term):
                    continue
                out[term].append({
                    "record": d.id,
                    "latch": d.summary.latch,
                    "not_this": sorted(set(d.summary.not_this) | set(latch.guard.not_this)),
                    "stakes": d.summary.stakes,
                    "owed_act": latch.owed_act.class_,
                    "latch_index": i,
                })
    return {term: sorted(cells, key=lambda c: c["record"]) for term, cells in sorted(out.items())}


UNWATCHED = "unwatched"
"""What a record's watch cell reads when no live world-state latch can send it back for re-adjudication: the world has no
way to contradict its warrant, and the cell says so loudly rather than defaulting — a join over nothing is displayed, never
tiebroken (doctrine § 16.17)."""


def watch_of(record: Decision) -> str:
    """The record's derived falsification grammar, as a cell: its live dispositive world-state watches, or ``unwatched``."""
    watches = [l.edge.predicate for l in record.all_latches()
               if l.type == "revisit" and l.lifecycle.status == "live" and l.owed_act.role == "dispositive" and l.edge.predicate]
    if not watches:
        return UNWATCHED
    return "; ".join(f"{p.scorer} {p.comparator} {p.value} over {p.persistence}" for p in watches)


def summaries(store: Store) -> list[dict[str, Any]]:
    """The full scan of one-line summaries the decision store is recalled by; ``watch`` is the record's derived grammar or ``unwatched``."""
    return [
        {"record": d.id, "status": d.status, "latch": d.summary.latch, "stakes": d.summary.stakes,
         "not_this": d.summary.not_this, "scopes": d.scopes, "watch": watch_of(d)}
        for d in store.decisions()
    ]


def watch_hosts(store: Store) -> list[tuple[str, list]]:
    """Every record the oracle's next run can move: accepted decisions and deferred drafts, with their latch fans.

    A draft's own fan is not yet live — nothing a draft proposes is yet true —
    so only its deferral latch is exposed, at the index a fire's ``latch.index``
    reads; the body's positions are held by ``None``.
    """
    hosts: list[tuple[str, list]] = [(d.id, d.all_latches()) for d in store.decisions("accepted")]
    hosts += [(p.uid, [None] * len(p.body.all_latches()) + [p.deferral.until]) for p in store.drafts() if p.deferral]
    return hosts


def triggers(store: Store) -> list[dict[str, Any]]:
    """Live revisit latches keyed on world-state, with their predicates — on decisions and on deferred drafts alike."""
    out = []
    for host, latches in watch_hosts(store):
        for i, latch in enumerate(latches):
            if latch is not None and latch.type == "revisit" and latch.lifecycle.status == "live" and latch.edge.predicate:
                out.append({"record": host, "latch_index": i, "predicate": latch.edge.predicate.model_dump(),
                            "disposer": latch.consumer, "owed_act": latch.owed_act.class_})
    return out


def deferred(store: Store) -> list[dict[str, Any]]:
    """Drafts re-queued on a ``defer(<until>)`` verdict, with the condition each waits on."""
    out = []
    for p in store.drafts():
        if not p.deferral:
            continue
        until = p.deferral.until
        out.append({"draft": p.uid, "name": p.name, "ledger_entry": p.deferral.ledger_entry, "after_pass": p.deferral.after_pass,
                    "key_space": until.key_space, "predicate": until.edge.predicate.model_dump() if until.edge.predicate else None,
                    "over_passes": until.guard.over_passes, "disposer": until.consumer})
    return out


def wiring(store: Store) -> list[dict[str, Any]]:
    """Live neighbour-keyed latches: which record watches which, and the status each neighbour was last seen in."""
    out = []
    for d in store.decisions():
        for i, latch in enumerate(d.all_latches()):
            if latch.type == "wiring" and latch.lifecycle.status == "live":
                out.append({"record": d.id, "status": d.status, "latch_index": i, "neighbours": latch.guard.records,
                            "seen": latch.guard.statuses, "owed_act": latch.owed_act.class_, "disposer": latch.consumer})
    return out


def undischarged_fires(store: Store) -> list[dict[str, Any]]:
    return [
        {"id": f.id, "record": f.latch.record, "latch_index": f.latch.index, "disposer": f.disposer,
         "owed_act": f.disposition.act, "fired_at": f.fired_at.isoformat()}
        for f in store.all("fire") if not f.disposition.discharged  # type: ignore[attr-defined]
    ]


def competence(store: Store) -> list[dict[str, Any]]:
    """applied ÷ considered per record over the review window — the demotion nominator, never a verdict.

    ``not_applicable`` is the fired-but-not-applicable count (§ 10.5, activation — precision): the hook fired on
    presentation alone and the pass disposed the record ``considered-not-applicable``; dominating the considered count,
    it indicts the guard and nominates a ``counterfactual-edit`` growing ``not_this`` (:func:`precision`).
    """
    sessions, window = review_window(store)
    recent = {s.id for s in sessions}
    tally: dict[str, dict[str, int]] = defaultdict(lambda: {"considered": 0, "applied": 0, "not_applicable": 0, "guard_failed": 0, "off_map": 0})
    for u in store.all("disposition"):
        u: Disposition
        if u.session not in recent:
            continue
        t = tally[u.record]
        if u.considered:
            t["considered"] += 1
        if u.disposition == "applied":
            t["applied"] += 1
        elif u.disposition == "considered-not-applicable":
            t["not_applicable"] += 1
        elif u.disposition == "guard-failed":
            t["guard_failed"] += 1
        elif u.disposition == "fired-off-map":
            t["off_map"] += 1
    rows = []
    for d in store.decisions("accepted"):
        t = tally[d.id]
        ratio = (t["applied"] / t["considered"]) if t["considered"] else None
        rows.append({"record": d.id, **t, "applied_over_considered": ratio, "window_passes": window,
                     "passes_in_window": len(recent)})
    return rows


def precision(store: Store) -> list[dict[str, Any]]:
    """The activation-precision nominator (§ 10.5, the first slot signature): records whose not-applicable dispositions
    dominate their considered count over the review window, at or above the bar ``precision.not_applicable_over_considered_above``,
    each with the dispositions' notes — the presentations the hook fired on and did not bear on, which a
    ``counterfactual-edit`` grows ``not_this`` by.

    Two finer diagnoses outrank it and are left to their own rows: a record whose dispositions are bimodal across
    sub-shapes is fused (``fusion``: the not-applicable fires are the other sub-shape's, a split, not an exclusion), and a
    record at its retirement door — never applied over a full window — is the retirement leg's (mootness, after the
    killer-item check), not a guard to tighten.
    """
    bar = store.registry.bars.get("precision", {}).get("not_applicable_over_considered_above", 0.5)
    sessions, _ = review_window(store)
    recent = {s.id for s in sessions}
    bimodal = {row["record"] for row in fusion(store) if row["bimodal"]}
    notes: dict[str, list[dict[str, str]]] = defaultdict(list)
    for u in store.all("disposition"):
        u: Disposition
        if u.session in recent and u.disposition == "considered-not-applicable":
            notes[u.record].append({"disposition": u.id, "session": u.session, "note": u.note or ""})
    rows = []
    for row in competence(store):
        if not row["considered"] or row["record"] in bimodal:
            continue
        ratio = row["not_applicable"] / row["considered"]
        if ratio < bar:
            continue
        d: Decision = store.read("decision", row["record"])  # type: ignore[assignment]
        guard = d.lifecycle.retirement.guard
        at_retirement_door = (guard.applied_over_considered_below is not None and row["applied_over_considered"] < guard.applied_over_considered_below
                              and row["passes_in_window"] >= (guard.over_passes or 0))
        if at_retirement_door:
            continue
        rows.append({"record": d.id, "considered": row["considered"], "not_applicable": row["not_applicable"],
                     "not_applicable_over_considered": ratio, "bar": bar, "not_this": d.consultation_not_this,
                     "notes": notes.get(d.id, [])})
    return rows


def review_window(store: Store) -> tuple[list[Session], int]:
    """The closed attached sessions of the review window, oldest first, and the window's length."""
    window = store.registry.bars["retirement"]["window_passes"]
    sessions: list[Session] = sorted((s for s in store.all("session") if s.attached and s.closed_at is not None), key=lambda s: s.pass_)  # type: ignore[misc]
    return sessions[-window:], window


def _applied_by_session(store: Store, sessions: list[Session]) -> dict[str, dict[str, bool]]:
    """record → {session id → applied?} over the window, from the disposition ledger."""
    recent = {s.id for s in sessions}
    out: dict[str, dict[str, bool]] = defaultdict(dict)
    for u in store.all("disposition"):
        u: Disposition
        if u.session in recent and u.guard_passed:
            out[u.record][u.session] = u.disposition == "applied"
    return out


def fusion(store: Store) -> list[dict[str, Any]]:
    """Dispositions by matched sub-shape per accepted record — the split nominator of § 10.6.

    A record applied cleanly whenever one work-shape term matched it and never
    when only another did is a fused record; ``bimodal`` marks the rows where
    both sub-shapes were seen at least twice and their applied ratios sit at
    the two ends. The row nominates; the consolidator drafts the leaves and
    the adjudicator ratifies them against the raw anchors, never the labels.
    """
    sessions, _ = review_window(store)
    applied = _applied_by_session(store, sessions)
    matched = {s.id: {c.record: c.terms_matched for c in s.considered if c.via == "index"} for s in sessions}
    rows = []
    for d in store.decisions("accepted"):
        by_term: dict[str, dict[str, int]] = defaultdict(lambda: {"considered": 0, "applied": 0})
        for sid, was_applied in applied.get(d.id, {}).items():
            for term in matched.get(sid, {}).get(d.id, []):
                by_term[term]["considered"] += 1
                by_term[term]["applied"] += int(was_applied)
        if len(by_term) < 2:
            continue
        seen_twice = {t: c for t, c in by_term.items() if c["considered"] >= 2}
        always = sorted(t for t, c in seen_twice.items() if c["applied"] == c["considered"])
        never = sorted(t for t, c in seen_twice.items() if c["applied"] == 0)
        rows.append({"record": d.id, "by_term": dict(sorted(by_term.items())), "applied_on": always, "never_on": never,
                     "bimodal": bool(always and never)})
    return rows


def convergence(store: Store) -> list[dict[str, Any]]:
    """Accepted pairs whose activation overlaps and whose applications coincide — the fold nominator of § 10.6.

    Two records applied in the same passes on the same hook have put their
    differentiation under stress; whether their payloads entail one another is
    the consolidator's reading and the adjudicator's verdict, never this row's.
    """
    sessions, _ = review_window(store)
    applied = _applied_by_session(store, sessions)
    accepted = store.decisions("accepted")
    rows = []
    for i, a in enumerate(accepted):
        for b in accepted[i + 1:]:
            shared = sorted(set(a.consultation_terms) & set(b.consultation_terms))
            if not shared:
                continue
            on_a = {s for s, x in applied.get(a.id, {}).items() if x}
            on_b = {s for s, x in applied.get(b.id, {}).items() if x}
            rows.append({"records": [a.id, b.id], "shared_terms": shared, "identical_hooks": set(a.consultation_terms) == set(b.consultation_terms),
                         "co_applied": len(on_a & on_b), "applied_apart": len(on_a ^ on_b)})
    return rows


def _lineage_related(store: Store) -> set[tuple[str, str]]:
    """Every unordered pair of decisions connected through the lineage DAG's decision-to-decision edges.

    Supersedure, split and fold are the edges that make one decision a move on another; a record and its successor,
    its leaf's parent, or the records it was folded from lie in one component, and split-siblings sharing a parent lie
    in one component too. Admission and promotion edges (which touch ledger and observation nodes, not two decisions)
    are not lineage moves and are left out. Two decisions in the same component have a lineage relation between them."""
    ids = {d.id for d in store.decisions()}
    adj: dict[str, set[str]] = defaultdict(set)
    for e in lineage(store)["edges"]:
        if e["kind"] in ("supersedes", "split", "fold") and e["from"] in ids and e["to"] in ids:
            adj[e["from"]].add(e["to"])
            adj[e["to"]].add(e["from"])
    related: set[tuple[str, str]] = set()
    seen: set[str] = set()
    for start in ids:
        if start in seen:
            continue
        component, stack = [], [start]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            component.append(n)
            stack += [m for m in adj[n] if m not in seen]
        for i, x in enumerate(component):
            for y in component[i + 1:]:
                related.add((x, y))
                related.add((y, x))
    return related


def restatements(store: Store, min_overlap: float = 0.6) -> list[dict[str, Any]]:
    """Accepted pairs that restate one lesson — the fold nominator for records that never co-applied (stream-run item 33).

    Split and fold run on the lineage DAG, so :func:`convergence` folds records that were *applied together*; but a
    strict arm that admitted several near-verbatim restatements of one lesson (D-0004/5/6 restating D-0001/D-0002) left
    the store carrying that lesson many times, and every boot carried all of them — the restatements never co-applied,
    so :func:`convergence`'s co-application bar never saw them. This row nominates a fold of two admitted records that
    (1) have no lineage edge between them (:func:`_lineage_related`), (2) share a consultation term, so a boot recalls
    them on the same presentations, and (3) carry payloads shaped alike — a token overlap of the decision payload at or
    above ``min_overlap``. The alikeness is a heuristic and the fold it proposes is still drafted, examined and
    adjudicated behind the floor like any nomination; this row only proposes the merge, it does not settle it.
    """
    related = _lineage_related(store)
    by_id = {d.id: d for d in store.decisions("accepted")}
    rows = []
    for row in convergence(store):  # convergence already keys on a shared hook, so it is the pool to filter
        a, b = row["records"]
        if (a, b) in related or a not in by_id or b not in by_id:
            continue
        overlap = _jaccard(tokens(by_id[a].decision), tokens(by_id[b].decision))
        if overlap >= min_overlap:
            rows.append({**row, "payload_overlap": round(overlap, 3)})
    return rows


def _jaccard(a: set[str], b: set[str]) -> float:
    """The token overlap of two payloads: shared stems over their union; ``0.0`` when both are empty."""
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def structural_zero(store: Store) -> list[str]:
    """Accepted decisions no live consultation hook on a registered term reaches — stored, unreachable, never recalled."""
    reached = {cell["record"] for cells in hooks(store).values() for cell in cells}
    return [d.id for d in store.decisions("accepted") if d.id not in reached]


def lineage(store: Store) -> dict[str, Any]:
    """The lineage DAG: successor, split and fold edges, plus the observation → decision promotion edges."""
    edges = []
    for d in store.decisions():
        for p in d.lineage.supersedes:
            edges.append({"from": p, "to": d.id, "kind": "supersedes"})
        if d.lineage.split_from:
            edges.append({"from": d.lineage.split_from, "to": d.id, "kind": "split"})
        for p in d.lineage.folded_from:
            edges.append({"from": p, "to": d.id, "kind": "fold"})
        if d.admission.ledger_entry:
            edges.append({"from": d.admission.ledger_entry, "to": d.id, "kind": "admission"})
    for o in store.observations(state=None):
        if o.disposition.state == "promoted" and o.disposition.pointer:
            edges.append({"from": o.name, "to": o.disposition.pointer, "kind": "promotion"})
    nodes = sorted({e["from"] for e in edges} | {e["to"] for e in edges} | {d.id for d in store.decisions()})
    return {"nodes": nodes, "edges": edges}


def row_passed(row: dict[str, Any]) -> bool:
    """Whether the oracle passed a task row: its ``task_pass_rate`` score, read off the row; an unscored row reads as passed only when it carries no error."""
    score = (row.get("scores") or {}).get("task_pass_rate") or {}
    return score.get("value") == 1.0 if "value" in score else not row.get("error")


def observation_for(observations: Iterable[Observation], row: dict[str, Any]) -> Observation | None:
    """The observation a row was noticed as, among ``observations``: one anchored on the row's call, or naming its
    task when the row carries no call — ``None`` where the row was not noticed. The caller scopes ``observations``
    to the session it asks about."""
    for o in observations:
        if row.get("call") and o.anchor.call == row["call"]:
            return o
        if not row.get("call") and str(row.get("task")) in o.happened:
            return o
    return None


def observed_from(store: Store, session: Session, row: dict[str, Any]) -> bool:
    """Whether the session filed an observation from this row: one anchored on the row's call, or naming its task when the row carries no call."""
    return observation_for((o for o in store.observations(state=None) if o.session == session.id), row) is not None


def true_misses(store: Store) -> list[str]:
    """The rows nothing caught (§ 10.1, the bottom-right cell): a task failed in a closed attached session that consulted no
    record, and the pass filed no observation from the row — no latch fired, no floor refused, no noticing. Each is
    ``<session>/<task>``. A floor: the store cannot see a miss the world has not yet voted on."""
    out = []
    for s in store.all("session"):
        s: Session
        if not s.attached or s.closed_at is None or s.evaluation is None or s.consulted:
            continue
        for row in s.evaluation.rows:
            if not row_passed(row) and not observed_from(store, s, row):
                out.append(f"{s.id}/{row.get('task')}")
    return out


def matrix(store: Store) -> dict[str, Any]:
    """The detection matrix of § 10.1: steers × fires × applied dispositions × the rows nothing caught. Every count is a floor."""
    cells: dict[str, list[str]] = defaultdict(list)
    for t in store.all("steer"):
        cells[t.matrix_cell].append(t.id)  # type: ignore[attr-defined]
    indicted = {t.indicts.record for t in store.all("steer") if t.indicts}  # type: ignore[attr-defined]
    for f in store.all("fire"):
        f: Fire
        cells["system-catches/oracle-catches" if f.latch.record in indicted else "system-catches/none-catches"].append(f.id)
    for u in store.all("disposition"):
        u: Disposition
        if u.disposition == "applied" and u.record not in indicted:
            cells["system-catches/none-catches"].append(u.id)
    cells["system-misses/none-catches"] = true_misses(store)
    return {cell: sorted(ids) for cell, ids in sorted(cells.items())} | {
        "note": "system-misses/none-catches is detection-limited: it counts the failed rows of sessions that consulted nothing and filed "
                "no observation from the row, and its count is a floor — the store cannot see a miss the world has not yet voted on"}


def recall(store: Store) -> list[dict[str, Any]]:
    """Should-have-fired (§ 10.5, activation — recall): the boot recall lens's probes and the steers' archaeology, per record.

    L-0002 asks each pass which record the store holds that this work needed and no hook reached; a finding naming an
    accepted record the pass did not consult is a recall probe against that record's hook. Joined with the steers that
    indict a record's activation slot, the rows are the should-have-fired stream — a floor, never complete, and a
    nominator for re-keying (``hook-edit``), never a verdict. ``presented`` is what the probing passes classified their
    work as: the terms a re-key may add.
    """
    sessions, _ = review_window(store)
    probes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    presented: dict[str, set[str]] = defaultdict(set)
    accepted = {d.id: d for d in store.decisions("accepted")}
    for s in sessions:
        consulted = {c.record for c in s.consulted}
        for answer in s.lens_answers:
            if answer.lens != "L-0002":
                continue
            for f in answer.findings:
                rid = f.get("record")
                if rid in accepted and rid not in consulted:
                    probes[rid].append({"session": s.id, "why": str(f.get("why", "")), "call": answer.call})
                    presented[rid].update(s.work_shape.terms)
    steers = defaultdict(list)
    for t in store.all("steer"):
        if t.indicts and t.indicts.slot == "activation":  # type: ignore[attr-defined]
            steers[t.indicts.record].append(t.id)  # type: ignore[attr-defined]
    rows = []
    for rid in sorted(set(probes) | set(steers)):
        if rid not in accepted:
            continue
        hook = accepted[rid].consultation_terms
        rows.append({"record": rid, "hook": hook, "probes": probes.get(rid, []), "sessions": sorted({p["session"] for p in probes.get(rid, [])}),
                     "presented": sorted(presented.get(rid, set())), "missing": sorted(presented.get(rid, set()) - set(hook)), "steers": steers.get(rid, [])})
    return rows


def mint_ladder(store: Store) -> list[dict[str, Any]]:
    """Should-have-been-covered (§ 10.1, the miss stream climbing to activation): a class of off-map failure that recurs
    across the independence bar of distinct sessions, and that no accepted record's hook covers, nominates new activation
    coverage — a consultation hook or a close lens keyed on the work-shape. It is a nominator, never a verdict.

    This is the complement of :func:`recall`. Recall reads the should-have-fired stream for a record the store already
    holds and nominates a hook-edit to widen that record's key; the ladder reads the failures the store held *nothing* for
    — a closed attached session that consulted no record and still failed a row (the bottom-right cell :func:`true_misses`
    counts, and the raw signal :func:`hgi.close.dispose` files ``fired-off-map`` on) — and, keyed on the session's
    work-shape terms, climbs only at the second distinct session. A single off-map failure is one episode; two are the
    recurrence the promotion bar reads, mirrored here on the miss rather than the observation. A row an observation was
    filed from is still a miss of *coverage* — the pass noticed it, no hook did — so the ``noticed`` list records which
    instances a close lens caught without lowering the nomination. A floor twice over: a session that carried no
    work-shape term keys no hook and is not classed here, and the count sees only the misses the world has voted on."""
    bar = int((store.registry.bars.get("decision") or {}).get("independent_observations") or 2)
    accepted_hooks = {t for d in store.decisions("accepted") for t in d.consultation_terms}
    by_class: dict[str, dict[str, Any]] = defaultdict(lambda: {"sessions": set(), "instances": set(), "noticed": set()})
    for s in store.all("session"):
        s: Session
        if not s.attached or s.closed_at is None or s.evaluation is None or s.consulted:
            continue  # off-map is the same gate true_misses reads: a closed attached session that consulted nothing
        for row in s.evaluation.rows:
            if row_passed(row):
                continue
            instance = f"{s.id}/{row.get('task')}"
            noticed = observed_from(store, s, row)
            for term in s.work_shape.terms:  # a session with no work-shape term keys no hook and is not classed
                agg = by_class[term]
                agg["sessions"].add(s.id)
                agg["instances"].add(instance)
                if noticed:
                    agg["noticed"].add(instance)
    rows = []
    for term in sorted(by_class):
        agg = by_class[term]
        n = len(agg["sessions"])
        if n < bar or term in accepted_hooks:
            continue
        rows.append({"class": term, "distinct_sessions": n, "reading": "at the bar" if n == bar else "above the bar",
                     "instances": sorted(agg["instances"]), "noticed": sorted(agg["noticed"]),
                     "nominates": "new activation coverage: a consultation hook or a close lens keyed on this work-shape",
                     "why": f"{n} distinct sessions failed off-map on '{term}' work and no accepted record's hook covers it — the store held nothing for it",
                     "floor": "detection-limited: it counts the off-map failures of closed attached sessions, a lower bound the world's votes set"})
    return rows


def attacker(store: Store) -> dict[str, Any]:
    """The instruments are instrumented (I16): attacker precision as a tracked floor, and the attacker's misses as a stream.

    Over the attack species: how many drafts the examiner was dispatched against, how many claims it landed, how many of
    its landings the adjudicator upheld (``attack-landed`` | ``premise-killed``) against how many it overruled, per angle
    where the claims name their lens. A persistently zero landing count interrogates the dispatch bar before any target is
    declared clean, and a precision of one over zero overrulings is a ceiling artifact where the adjudicator absorbs the
    attack — both read as notes here, never as verdicts. The misses are the should-have-been-caught-by stream: a record
    that survived its attack and was later indicted by a steer, had a premise reversed, or went moot on its own warrant.
    """
    entries = [e for e in store.all("hypothesis") if e.species == "attack" and e.contradiction.attack]  # type: ignore[attr-defined]
    claims = [c for e in entries for c in e.contradiction.attack.claims]  # type: ignore[attr-defined]
    landed = [c for c in claims if c.landed]
    with_landing = [e for e in entries if any(c.landed for c in e.contradiction.attack.claims)]  # type: ignore[attr-defined]
    upheld = [e for e in with_landing if e.verdict in ("attack-landed", "premise-killed")]  # type: ignore[attr-defined]
    per_angle: dict[str, dict[str, int]] = defaultdict(lambda: {"claims": 0, "landed": 0})
    for c in claims:
        angle = c.lens or ("mechanical" if c.target in MECHANICAL else "single-context")
        per_angle[angle]["claims"] += 1
        per_angle[angle]["landed"] += int(c.landed)
    indicted = defaultdict(list)
    for t in store.all("steer"):
        if t.indicts:  # type: ignore[attr-defined]
            indicted[t.indicts.record].append(t.id)  # type: ignore[attr-defined]
    misses = []
    for d in store.decisions():
        survived = [e.id for e in entries if (e.outcome or "").startswith(f"admitted {d.id}")]  # type: ignore[attr-defined]
        if not survived:
            continue
        caught_by = list(indicted.get(d.id, []))
        caught_by += [f"premise {p.id} {p.status}" for p in d.warrant.premises if p.status in ("reversed", "disputed")]
        if d.status == "moot":
            caught_by.append("moot on its own warrant")
        if caught_by:
            misses.append({"record": d.id, "survived": survived, "caught_by": caught_by})
    notes = []
    if entries and not landed:
        notes.append(f"zero landings over {len(entries)} dispatches: interrogate the dispatch bar before declaring any target clean")
    if with_landing and len(upheld) == len(with_landing):
        notes.append("every landing upheld: a precision of one over zero overrulings is a ceiling artifact where the adjudicator absorbs the attack, not a clean bill")
    return {"dispatched": len(entries), "claims": len(claims), "landed": len(landed), "entries_with_landing": len(with_landing),
            "upheld": len(upheld), "overruled": len(with_landing) - len(upheld),
            "precision": (len(upheld) / len(with_landing)) if with_landing else None,
            "per_angle": dict(sorted(per_angle.items())), "misses": misses, "notes": notes,
            "floor": "every count is a floor: an attack the synthesis absorbed before the ledger saw it is not here"}


PROJECTIONS: dict[str, Callable[[Store], Any]] = {
    "hooks": hooks,
    "summaries": summaries,
    "triggers": triggers,
    "deferred": deferred,
    "wiring": wiring,
    "fires": undischarged_fires,
    "competence": competence,
    "fusion": fusion,
    "convergence": convergence,
    "structural_zero": structural_zero,
    "lineage": lineage,
    "matrix": matrix,
    "attacker": attacker,
    "recall": recall,
    "mint_ladder": mint_ladder,
}


def regenerate(store: Store) -> dict[str, Any]:
    out = {}
    for name, fn in PROJECTIONS.items():
        payload = fn(store)
        write_json(store.index_dir / f"{name}.json", payload)
        out[name] = payload
    return out


def check(store: Store) -> list[str]:
    """Names of projections whose committed file differs from regeneration."""
    stale = []
    for name, fn in PROJECTIONS.items():
        path = store.index_dir / f"{name}.json"
        committed = read_json(path) if path.exists() else None
        if committed != fn(store):
            stale.append(name)
    return stale


def read(store: Store, name: str) -> Any:
    path = store.index_dir / f"{name}.json"
    return read_json(path) if path.exists() else PROJECTIONS[name](store)


# --- the path query -------------------------------------------------------------

def paths_to(store: Store, id: str) -> list[list[str]]:
    """Every path through the lineage DAG that ends at ``id`` — the history of being wrong, read backwards."""
    graph = lineage(store)
    preds: dict[str, list[str]] = defaultdict(list)
    for e in graph["edges"]:
        preds[e["to"]].append(e["from"])

    def walk(node: str, seen: tuple[str, ...]) -> list[list[str]]:
        if node in seen or not preds.get(node):
            return [[node]]
        return [[*p, node] for pre in preds[node] for p in walk(pre, (*seen, node))]

    return walk(id, ())
