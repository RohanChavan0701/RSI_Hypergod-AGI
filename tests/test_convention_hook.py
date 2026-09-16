"""Carry-forward item 71a/71c: a consultation hook may key on a term from either hook axis — a work-shape or the
convention the lesson is about — and boot classification presents both, so a lesson about a world-convention is
retrievable when that convention recurs, not only when a shared tool does. Grouping keeps a coherent registered
convention at its own altitude and never strands it into an ``other(uncoded)`` singleton (71c).

These prove the mechanism on the stub; a live re-score is the run's to confirm. Nothing here is over-keyed on any one
domain — the convention axis (``listing-paged``, ``route-versioned``, ``schema-coded-value`` …) is the world's, not SQL's.
"""

from __future__ import annotations

import pytest

from hgi import boot as _boot
from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import stub
from hgi.store import now
from hgi.types import HOOK_AXES, Observation, Session, WorkShape

from tests.conftest import adjudicator, adjudicated_entry, decision_body, draft

CONVENTION = "listing-paged"  # a registered `convention` axis term — the world-fact, not the tool


def _convention_latches() -> list[dict]:
    """A decision's latches with the consultation hook keyed on a convention rather than a work-shape."""
    body = decision_body()
    body["latches"][0]["guard"]["terms"] = [CONVENTION]
    body["latches"][0]["guard"]["not_this"] = []
    return body["latches"]


def _admit_convention_hooked(store) -> str:
    d = draft(store, "D-paged", latches=_convention_latches(),
              decision="A listing that returns a next-page cursor is paged: follow the cursor, never read the first page as the whole set.")
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator()).id


# --- 71a: the hook axis ---------------------------------------------------------------------------

def test_a_consultation_hook_parses_and_indexes_on_a_convention(store):
    rid = _admit_convention_hooked(store)
    d = store.read("decision", rid)
    assert CONVENTION in d.consultation_terms, "a convention is a legal consultation-hook key"
    assert rid in {cell["record"] for cell in _index.hooks(store).get(CONVENTION, [])}, \
        "the hook index maps the convention to the record, so a boot presenting it reaches it"


def test_classify_presents_the_conventions_a_prompt_reveals_across_both_axes(store):
    vocab = store.registry.terms_over(*HOOK_AXES)
    assert set(store.registry.terms("work-shape")) <= set(vocab) and set(store.registry.terms("convention")) <= set(vocab), \
        "the hook vocabulary is the union of the two axes"
    revealing = stub._classify({"presentations": [{"prompt": "the listing returns one page at a time; follow the next page cursor"}], "terms": vocab})
    assert CONVENTION in revealing["terms"], "a convention visible in the prompt is presented, so a convention-keyed hook can fire"
    hidden = stub._classify({"presentations": [{"prompt": "call the HTTP api and return the count"}], "terms": vocab})
    assert CONVENTION not in hidden["terms"] and "http-tool" in hidden["terms"], \
        "a convention hidden until the work fails is left unnamed — the honest floor — while the work-shape still classifies"


def test_a_convention_keyed_record_is_matched_by_the_boot_index(store):
    rid = _admit_convention_hooked(store)
    session = store.parse_as(Session, {"id": store.mint("session"), "pass": 1, "started_at": now().isoformat(),
                                       "attached": True, "work_shape": {"terms": [CONVENTION], "escapes": []}})
    considered = _boot.select(store, session)
    match = next((c for c in considered if c.record == rid), None)
    assert match is not None and match.guard_passed, \
        "a session presenting the convention consults the record hooked on it — the retrieval a tool-only hook could not give"


def test_anchor_terms_seeds_the_hook_with_the_convention_the_evidence_was_coded_into(store):
    row = {"task": "genesis/sum_numbers", "error": {"message": "listing truncated", "cause": None}, "applied": [],
           "tool_errors": [], "call": "weave:///c/paged"}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": 1, "started_at": now().isoformat(), "closed_at": now().isoformat(),
                                 "attached": True, "evaluation": {"evaluation": "suite-v1", "scores": {}, "rows": [row]}})
    store.write(s)
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=s.id,
                    happened="a listing returned one page and the attempt read it as the whole set", anchor={"call": "weave:///c/paged"})
    o.shape = [CONVENTION]  # the grouping coded it into the convention
    store.write(o)
    floor = _consolidate.anchor_terms(store, [o.name])
    assert CONVENTION in floor, "the convention the evidence turned on floors the hook, so the lesson is recalled when it recurs"
    # the task's own declared work-shape still floors it too — the two axes together, neither replacing the other
    assert "http-tool" in floor


# --- 71c: the grouping grain ----------------------------------------------------------------------

def test_a_registered_convention_is_never_demoted_by_presentation_universality(store, monkeypatch):
    """A coherent registered convention names a world-fact, not a presentation, so the presentation-universality demotion
    (which sinks a label whose only identity is a term every task carries) never strands it — only an escape is eligible."""
    a, b = "weave:///c/1", "weave:///c/2"
    def obs(name, call):
        o = Observation(uid=store.new_uid(), name=name, noticed_at=now(), session="S-" + name, happened=f"{name} world-fact", anchor={"call": call})
        return o
    convention_members = [obs("Oa", a), obs("Ob", b)]
    escape_members = [obs("Oc", a), obs("Od", b)]
    by_label = {CONVENTION: convention_members, "other(way-of-working)": escape_members}
    # force the demotion condition for *every* label: a non-empty universal set and full presentation-universality
    monkeypatch.setattr(_consolidate, "pool_universal_terms", lambda: {"tool-budget"})
    monkeypatch.setattr(_consolidate, "presentation_universality", lambda members, call_shapes: 1.0)
    monkeypatch.setattr(_consolidate, "_call_to_shapes", lambda store: {})
    surviving = _consolidate._demote_presentation_universal(store, by_label)
    assert CONVENTION in surviving, "a registered convention is a coherent grouping identity and is kept even when presentation-universal"
    assert "other(way-of-working)" not in surviving, "an escape whose only identity is a pool-universal presentation is demoted"
    # the escape's members are not dropped — they fall to an other(uncoded) singleton so nothing is lost
    assert any(o.name in {"Oc", "Od"} for members in surviving.values() for o in members)
