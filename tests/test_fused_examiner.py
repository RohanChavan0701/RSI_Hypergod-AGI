"""``fuse_examiner`` (:attr:`hgi.experiment.ArmSpec.fuse_examiner`): opt-in, additive. Off (the default), the
attack is the examiner's fan — one fresh call per lens, structurally independent of the draft (the host law).
On, the consolidator self-critiques the draft in one further call of its own, covering every lens at once — the
examiner's N calls collapse toward one. Either way :func:`hgi.consolidate.adjudicate` hands the adjudicator the
same claim structure, and the adjudicator's own context is never folded."""

from __future__ import annotations

import json

from hgi import consolidate as _consolidate
from hgi import model as _model
from tests.conftest import draft
from tests.test_watch_direction import _anchored, _evidence, _record


def _calls(monkeypatch):
    """Spy on every role call, recording (role, parsed request), while still answering through the real backend
    (the store fixture's stub) so the reply shape is exercised, not faked."""
    seen = []
    real = _model.complete

    def spy(role, payload, **kw):
        seen.append((role, json.loads(payload)))
        return real(role, payload, **kw)

    monkeypatch.setattr(_model, "complete", spy)
    return seen


# --- the default path is untouched --------------------------------------------------------------

def test_fuse_examiner_defaults_off_and_the_fan_is_unchanged(store, monkeypatch):
    assert "fuse_examiner" not in store.registry.bars or store.registry.bars["fuse_examiner"] is False
    seen = _calls(monkeypatch)
    d = draft(store)
    payload, first = _consolidate.attack(store, _record(store), d, _evidence())
    attacks = [(role, req) for role, req in seen if req.get("request") == "attack"]
    lenses = store.registry.lenses("examiner")
    assert [role for role, _ in attacks] == ["examiner"] * len(lenses), "one fresh examiner call per lens, as before"
    assert all("lens" in req and "lenses" not in req and "instruction" not in req for _, req in attacks)
    assert first is not None and payload["verdict"] == "pending"


# --- fused: one consolidator call replaces the fan ------------------------------------------------

def test_fused_attack_is_one_consolidator_call_covering_every_lens(store, monkeypatch):
    store.registry.bars["fuse_examiner"] = True
    seen = _calls(monkeypatch)
    d = draft(store)
    payload, c = _consolidate.attack(store, _record(store), d, _evidence(), fused=True)
    attacks = [(role, req) for role, req in seen if req.get("request") == "attack"]
    assert [role for role, _ in attacks] == ["consolidator"], "the examiner's fan is never called; one consolidator call stands in for it"
    role, req = attacks[0]
    lenses = store.registry.lenses("examiner")
    assert [l["id"] for l in req["lenses"]] == [l.id for l in lenses], "every lens's angle is in the one call, not walked one at a time"
    assert req["instruction"] == _consolidate.SELF_CRITIQUE_INSTRUCTION
    assert c.model_id == _model.model_id("consolidator")
    # the same product shape the fan produces: claims naming their lens and the call that produced them
    by_lens = {}
    for claim in payload["claims"]:
        by_lens.setdefault(claim["lens"], []).append(claim["target"])
        assert claim["call"] == c.call
    assert by_lens == {"L-0006": ["premise:p1"], "L-0007": ["payload:abstraction"]}, "the same claims the fan would produce, just from one call"
    assert payload["verdict"] == "pending"


def test_fused_claims_reach_the_adjudicator_the_same_way_the_fans_do(store, monkeypatch):
    """End to end through adjudicate(): fused or not, the adjudicator sees the same attack structure and the same
    verdict follows from the same landed claim — only who produced the attack, and how many calls it took, differs."""
    fan_seen = _calls(monkeypatch)
    d, nomination = _anchored(store, "<", 0.7)
    fan_entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    fan_attacks = [role for role, req in fan_seen if req.get("request") == "attack"]

    store.registry.bars["fuse_examiner"] = True
    fused_seen = _calls(monkeypatch)
    d2, nomination2 = _anchored(store, "<", 0.7)
    fused_entry = _consolidate.adjudicate(store, _record(store), nomination2, d2, {"scores": {}})
    fused_attacks = [role for role, req in fused_seen if req.get("request") == "attack"]

    assert fan_attacks == ["examiner"] * len(store.registry.lenses("examiner")) and fused_attacks == ["consolidator"]
    assert fan_entry.outcome.startswith("admitted D-") and fused_entry.outcome.startswith("admitted D-"), "the fold changes nothing about the verdict reached"
    assert fan_entry.verdict == fused_entry.verdict == "survived-with-attack-named"
    fan_targets = sorted(c.target for c in fan_entry.contradiction.attack.claims)
    fused_targets = sorted(c.target for c in fused_entry.contradiction.attack.claims)
    assert fan_targets == fused_targets, "the adjudicator reads the same claim targets either way"
    assert fan_entry.contradiction.source.role == "examiner"
    assert fused_entry.contradiction.source.role == "consolidator", "the ledger honestly names who made the call"
    # the adjudicator itself is never folded: its own role call is unaffected by fuse_examiner
    assert fan_entry.adjudicator.role == fused_entry.adjudicator.role == "adjudicator"
