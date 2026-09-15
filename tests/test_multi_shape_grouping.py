"""Carry-forward item 64 — multi-shape observation coding.

One label per axis was the wrong model: a method that manifests as per-task singletons under drifting fine labels never
cleared the recurrence bar (item 62's F1/F3 residue). So the coder now assigns each observation a *set* of convention
labels — a broad one shared across tasks and a specific one — and grouping is **per label**: a candidate cluster is every
observation carrying label L, one observation lives in several clusters, and grouping is never a transitive union-find. A
grouping label keyed on a *presentation*-universal work-shape (a call budget every task presents) is demoted on
presentation-universality, **not** raw frequency, so budget sinks while the coarse method label — frequent but not a
presentation term — survives to recur.
"""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import stub
from hgi.store import now
from hgi.types import Consolidation, Observation
from tests.test_slice3 import FAULTED, _session


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=1, sessions_read=[])


def _obs(store, session, happened: str, call: str | None = None) -> Observation:
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=session.id,
                    happened=happened, anchor={"call": call} if call else {"path": "suite/tools.py:54"})
    store.write(o)
    return o


def _shapes(mapping: dict[str, list[str]]):
    """A cluster handler returning a fixed label *set* per observation, keyed on the observation name."""
    return lambda req: {"shapes": {o["name"]: list(mapping[o["name"]]) for o in req["observations"]}}


def _by_label(store, record) -> dict[str, dict]:
    return {g["shape"][0]: g for g in _consolidate.group_observations(store, record)}


def test_an_observation_carries_the_full_set_of_labels_the_coder_assigns(store, monkeypatch):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    o = _obs(store, s, "task cfg_05 produced 'zz' which is not a member of the grammar")
    monkeypatch.setitem(stub.HANDLERS, "cluster", _shapes({o.name: ["other(produce-then-verify)", "other(grammar-nonmember)"]}))
    _consolidate.group_observations(store, _record(store))
    assert store.observation(o.name).shape == ["other(grammar-nonmember)", "other(produce-then-verify)"], "the whole set is persisted, sorted"


def test_a_coarse_label_groups_distinct_world_facts_that_fine_labels_scatter(store, monkeypatch):
    # the F1/F3 fix: two misses of the same method over *distinct* world-facts share the coarse label and clear the bar,
    # while their specific labels stay singletons — the recurrence the single-label axis forked into two singletons.
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5})
    a = _obs(store, s1, "task alpha: module 'nltk.parse.earley' does not exist")
    b = _obs(store, s2, "task beta: the produced string 'zz' is not a grammar member")
    coarse = "other(produce-then-verify)"
    monkeypatch.setitem(stub.HANDLERS, "cluster", _shapes({
        a.name: [coarse, "other(module-not-found)"],
        b.name: [coarse, "other(grammar-nonmember)"]}))
    groups = _by_label(store, _record(store))
    assert {o["name"] for o in groups[coarse]["observations"]} == {a.name, b.name}
    assert groups[coarse]["independence"] == 2, "the coarse label recurs across two independent sessions"
    assert {o["name"] for o in groups["other(module-not-found)"]["observations"]} == {a.name}
    assert {o["name"] for o in groups["other(grammar-nonmember)"]["observations"]} == {b.name}
    # one observation lives in several clusters — the overlap the dedup guard (corroborates) must hold to one decision
    assert a.name in {o["name"] for o in groups[coarse]["observations"]} and a.name in {o["name"] for o in groups["other(module-not-found)"]["observations"]}


def test_grouping_is_per_label_and_never_transitive(store, monkeypatch):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    a = _obs(store, s, "task a produced a value the world rejected on convention x")
    b = _obs(store, s, "task b tripped conventions x and y at once")
    c = _obs(store, s, "task c produced a value the world rejected on convention y")
    monkeypatch.setitem(stub.HANDLERS, "cluster", _shapes({
        a.name: ["other(x)"], b.name: ["other(x)", "other(y)"], c.name: ["other(y)"]}))
    groups = _by_label(store, _record(store))
    assert {o["name"] for o in groups["other(x)"]["observations"]} == {a.name, b.name}
    assert {o["name"] for o in groups["other(y)"]["observations"]} == {b.name, c.name}
    # A~B on x and B~C on y must NOT collapse A,B,C into one cluster through the chain
    assert not any({a.name, c.name} <= {o["name"] for o in g["observations"]} for g in groups.values())


def test_a_presentation_universal_label_is_demoted_while_a_frequent_method_label_survives(store, monkeypatch):
    # the crux: budget is universal *on presentation* (its cluster spans tasks whose only shared work-shape is the
    # pool-universal budget term) and is demoted; the method cluster's members share a *non-universal* task-shape, so it
    # is frequent but not presentation-universal and survives — the difference from a raw-frequency guard, which would
    # demote both (each is carried by most of the pool).
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5})
    s3 = _session(store, 3, [FAULTED], {"task_pass_rate": 0.5})
    a = _obs(store, s1, "task alpha over-verified and hit the budget after producing a non-member", call="weave:///c/a")
    b = _obs(store, s2, "task beta over-verified and hit the budget after a bad parse", call="weave:///c/b")
    c = _obs(store, s3, "task gamma exhausted its budget with no method behind it", call="weave:///c/c")
    method, budget = "other(produce-then-verify)", "other(call-budget-exceeded)"
    monkeypatch.setitem(stub.HANDLERS, "cluster", _shapes({
        a.name: [method, budget], b.name: [method, budget], c.name: [budget]}))
    # a,b sit on the reasoning-core task-shape (rc-shape) plus the universal budget term; c is a bare budget task.
    monkeypatch.setattr(_consolidate, "_call_to_shapes",
                        lambda store: {"weave:///c/a": {"tool-budget", "rc-shape"}, "weave:///c/b": {"tool-budget", "rc-shape"}, "weave:///c/c": {"tool-budget"}})
    monkeypatch.setattr(_consolidate, "pool_universal_terms", lambda *a, **k: {"tool-budget"})
    groups = _by_label(store, _record(store))
    assert budget not in groups, "the budget cluster spans all shapes → shared presentation is the universal term alone → demoted"
    assert method in groups and {o["name"] for o in groups[method]["observations"]} == {a.name, b.name}, "the method label survives and groups its two misses"
    assert c.name in {o["name"] for g in groups.values() for o in g["observations"]}, "the bare-budget observation is not dropped; it falls to a singleton"


def test_a_frequent_method_label_would_be_demoted_by_the_old_raw_frequency_guard(store, monkeypatch):
    # the contrast that motivates the switch: the method label is carried by every observation (raw frequency 1.0), so a
    # raw-frequency guard would demote it; presentation-universality keeps it because its shared task-shape is not universal.
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5})
    a = _obs(store, s1, "task alpha produced a non-member", call="weave:///c/a")
    b = _obs(store, s2, "task beta produced a bad parse", call="weave:///c/b")
    method = "other(produce-then-verify)"
    monkeypatch.setitem(stub.HANDLERS, "cluster", _shapes({a.name: [method], b.name: [method]}))
    monkeypatch.setattr(_consolidate, "_call_to_shapes", lambda store: {"weave:///c/a": {"rc-shape"}, "weave:///c/b": {"rc-shape"}})
    monkeypatch.setattr(_consolidate, "pool_universal_terms", lambda *a, **k: {"tool-budget"})
    groups = _by_label(store, _record(store))
    assert method in groups and {o["name"] for o in groups[method]["observations"]} == {a.name, b.name}, "a frequent-but-not-presentation-universal label survives"
