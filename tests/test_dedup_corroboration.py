"""Carry-forward item 61 — the dedup/corroboration path and the convention-label stability that feeds it.

Item 60's run confirmed the item-56 gap on the endpoint: a consolidator holding the prior decision in context minted a
twin (D-0002) from the same budget happenstance rather than corroborating D-0001, because the coder had named the one
world-fact two ways across rounds (``other(call-budget-exceeded)`` then ``pool-exhausted``) and the drift forked the axis
into two clusters. Two mechanical guards close it, both keyed on the label-robust world-content key
(:func:`hgi.index.world_content_key`), never on the fickle coder label:

- **the grouping pass canonicalizes** a recurring escape label to the one the same world-fact first carried, so the axis
  does not fork across rounds (:func:`hgi.consolidate._canonical_escape`, per observation over its world-content key);
- **the consolidate loop routes** a ``new-decision`` draft resting only on world-facts an accepted decision already
  anchors to corroboration of that decision, never a twin mint (:func:`hgi.consolidate.corroborates`).
"""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import stub
from hgi.store import now
from hgi.types import Consolidation, Draft
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft
from tests.test_slice3 import FAULTED, _observe, _session

# two happeneds that quote the same budget literal — the same world-fact, however the coder labels the convention
BUDGET_A = "the shell budget of '20 calls' was exhausted and the call was refused"
BUDGET_B = "a second attempt hit the same '20 calls' shell ceiling and stopped"
MODULE = "the module 'nltk.parse.earley' does not exist; the fix is 'earleychart'"


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[])


def _admit_anchored(store, anchor_names: list[str], decision: str):
    """An accepted decision whose warrant anchors the named observations — round 1 of the repro."""
    warrant = decision_body()["warrant"]
    warrant["anchors"] = list(anchor_names)
    d = draft(store, warrant=warrant, decision=decision).model_copy(update={"evidence": list(anchor_names)})
    store.write_draft(d)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def _new_decision_draft(store, evidence: list[str]) -> Draft:
    return draft(store, name="P-twin").model_copy(update={"uid": store.new_uid(), "evidence": list(evidence)})


# --- corroborates: the label-robust dedup signal ---------------------------------------------

def test_corroborates_matches_a_decision_resting_on_the_same_world_fact(store):
    o1 = _observe(store, _session(store, 1, [FAULTED], {}), BUDGET_A)
    decision = _admit_anchored(store, [o1.name], "the shell budget '20 calls' is a hard limit; exceeding it is non-transient")
    o2 = _observe(store, _session(store, 2, [FAULTED], {}), BUDGET_B)  # a different round, the same world-fact
    twin = _new_decision_draft(store, [o2.name])
    assert _consolidate.corroborates(store, twin).id == decision.id, "a draft on an already-anchored world-fact corroborates, not mints"


def test_a_draft_bringing_a_new_world_fact_is_not_corroborated(store):
    o1 = _observe(store, _session(store, 1, [FAULTED], {}), BUDGET_A)
    _admit_anchored(store, [o1.name], "the shell budget '20 calls' is a hard limit; exceeding it is non-transient")
    o3 = _observe(store, _session(store, 2, [FAULTED], {}), MODULE)  # a genuinely new world-fact
    assert _consolidate.corroborates(store, _new_decision_draft(store, [o3.name])) is None


def test_a_partial_overlap_is_not_corroborated(store):
    """The guard is conservative: a draft that also rests on an *unanchored* world-fact is genuinely new, not a duplicate."""
    o1 = _observe(store, _session(store, 1, [FAULTED], {}), BUDGET_A)
    _admit_anchored(store, [o1.name], "the shell budget '20 calls' is a hard limit; exceeding it is non-transient")
    s2 = _session(store, 2, [FAULTED], {})
    o2, o3 = _observe(store, s2, BUDGET_B), _observe(store, s2, MODULE)  # one shared key, one new key
    assert _consolidate.corroborates(store, _new_decision_draft(store, [o2.name, o3.name])) is None


def test_the_earliest_matching_decision_is_returned(store):
    o1 = _observe(store, _session(store, 1, [FAULTED], {}), BUDGET_A)
    first = _admit_anchored(store, [o1.name], "the shell budget '20 calls' is a hard limit; exceeding it is non-transient")
    o1b = _observe(store, _session(store, 2, [FAULTED], {}), BUDGET_B)
    _admit_anchored(store, [o1b.name], "once a '20 calls' budget refusal lands it is non-transient; stop and submit")
    o2 = _observe(store, _session(store, 3, [FAULTED], {}), BUDGET_A)
    assert _consolidate.corroborates(store, _new_decision_draft(store, [o2.name])).id == first.id, "deterministic: the earliest home"


# --- corroborate: the recorded act -----------------------------------------------------------

def test_corroborate_records_a_still_holds_currency_entry_and_refuses_the_twin(store):
    o1 = _observe(store, _session(store, 1, [FAULTED], {}), BUDGET_A)
    decision = _admit_anchored(store, [o1.name], "the shell budget '20 calls' is a hard limit; exceeding it is non-transient")
    o2 = _observe(store, _session(store, 2, [FAULTED], {}), BUDGET_B)
    twin = _new_decision_draft(store, [o2.name])
    store.write_draft(twin)
    record = _record(store)
    outcome = _consolidate.corroborate(store, record, twin, decision)

    assert decision.id in outcome and record.corroborated == [twin.uid]
    assert store.draft(twin.uid) is None, "the twin draft is dropped, never admitted"
    assert store.observation(o2.name).disposition.state == "promoted"
    assert store.observation(o2.name).disposition.pointer == decision.id, "the corroborating instance points at the standing decision"
    entry = next(e for e in store.all("hypothesis") if e.species == "currency" and e.subject == decision.id)
    assert entry.verdict == "still-holds" and entry.adjudicator is None
    assert entry.contradiction.coding["dedup"] == twin.uid
    # the accepted set did not grow: no twin decision was minted
    assert [d.id for d in store.decisions("accepted")] == [decision.id]


def test_the_consolidate_loop_routes_a_duplicate_mint_to_corroboration(store, monkeypatch):
    """The two-round repro end to end: round 1 admits the budget decision; round 2 the consolidator nominates a fresh
    ``new-decision`` on the same world-fact and the loop corroborates instead of minting the twin item 60 saw."""
    o1 = _observe(store, _session(store, 1, [FAULTED], {}), BUDGET_A)
    decision = _admit_anchored(store, [o1.name], "the shell budget '20 calls' is a hard limit; exceeding it is non-transient")
    o2 = _observe(store, _session(store, 2, [FAULTED], {"task_pass_rate": 0.5}), BUDGET_B)

    sketch = {"decision": "once a '20 calls' budget refusal lands it is non-transient; stop and submit",
              "counterfactual": "The overshoot is stopping on any error — observed in O-0001.", "latch": "a shell tool under a call budget",
              "terms": ["http-tool"], "not_this": [], "stakes": "a retry storm burns the budget", "context": "seen in S-0001, S-0002",
              "options": [{"name": "A — stop and submit", "judged": "chosen", "why": "the budget is a hard limit"}],
              "premises": [{"id": "p1", "statement": "the '20 calls' budget is a hard limit", "falsifier": "a budget the runner raises on refusal"}],
              "watch": None, "residue": [], "moot_when": "the runner stops enforcing a budget", "scopes": []}
    raw = {"rung": "new-decision", "rung_why": "the loop has no record that the budget is a hard limit", "subject": "budget",
           "evidence": [o2.name], "sketch": sketch}
    monkeypatch.setattr(_consolidate, "nominate", lambda store, record, brief: [raw])

    record = _consolidate.consolidate(store, force=True)
    assert record.admitted == [], "no twin admitted"
    assert record.corroborated, "the duplicate mint was routed to corroboration"
    assert [d.id for d in store.decisions("accepted")] == [decision.id]
    assert store.observation(o2.name).disposition.pointer == decision.id
    assert any(e.species == "currency" and e.verdict == "still-holds" and e.subject == decision.id for e in store.all("hypothesis"))


# --- label canonicalization: the drift that fed the twin -------------------------------------

def _shape_prior(store, happened: str, label: str):
    """A prior-pass observation already shaped and consumed — round 1's labeling of a world-fact."""
    o = _observe(store, _session(store, 1, [FAULTED], {}), happened)
    o.shape = [label]
    o.disposition.state = "promoted"
    store.write(o)
    return o


def test_a_recurring_escape_keeps_the_label_its_world_fact_first_carried(store, monkeypatch):
    _shape_prior(store, BUDGET_A, "other(call-budget-exceeded)")  # round 1's label for the budget world-fact
    o_now = _observe(store, _session(store, 2, [FAULTED], {}), BUDGET_B)  # round 2, same world-fact
    # the coder drifts: it names the one happenstance a second way
    monkeypatch.setitem(stub.HANDLERS, "cluster", lambda req: {"shapes": {o["name"]: ["other(pool-exhausted)"] for o in req["observations"]}})
    _consolidate.group_observations(store, _record(store))
    assert store.observation(o_now.name).shape == ["other(call-budget-exceeded)"], "the drifted escape canonicalizes to the first label"


def test_distinct_world_facts_are_not_merged(store, monkeypatch):
    _shape_prior(store, BUDGET_A, "other(call-budget-exceeded)")
    o_now = _observe(store, _session(store, 2, [FAULTED], {}), MODULE)  # a different world-fact
    monkeypatch.setitem(stub.HANDLERS, "cluster", lambda req: {"shapes": {o["name"]: ["other(module-not-found)"] for o in req["observations"]}})
    _consolidate.group_observations(store, _record(store))
    assert store.observation(o_now.name).shape == ["other(module-not-found)"], "a distinct world-fact keeps its own label"


def test_a_registered_prior_label_does_not_rewrite_an_escape(store, monkeypatch):
    """The net is escape→escape only: a registered term is the coder's to pick (it holds the vocabulary), never forced on
    by canonicalization — so a prior *registered* label leaves a fresh escape untouched."""
    _shape_prior(store, BUDGET_A, "listing-paged")  # a registered convention term (from the seed vocabulary)
    o_now = _observe(store, _session(store, 2, [FAULTED], {}), BUDGET_B)
    monkeypatch.setitem(stub.HANDLERS, "cluster", lambda req: {"shapes": {o["name"]: ["other(pool-exhausted)"] for o in req["observations"]}})
    _consolidate.group_observations(store, _record(store))
    assert store.observation(o_now.name).shape == ["other(pool-exhausted)"], "a registered prior does not override; the coder owns that promotion"
