"""Seed stores: a hand-authored decision injected before pass 1 is minted past the store's own ids, priced for the
arm's pass model, reached by the boot's consultation and disposed like any admitted record — the compare/contrast
against the same arm from an empty store (``experiments/seeds/AUTHORING.md``)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hgi import experiment as _experiment
from hgi import genesis as _genesis
from hgi import model as _model
from hgi import seeds as _seeds
from hgi.registry import read_json

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def clean_backends():
    _model.reset()
    yield
    _model.reset()


def _seed_from(decision: Path, seed_dir: Path) -> Path:
    """A one-decision seed cut from an admitted decision of the repository store, in the seed's own shape."""
    d = read_json(decision)
    d.update(id="D-0001", status="accepted", priced_for={"model_id": None, "authored_for": None},
             lineage={"folded_from": [], "split_from": None, "superseded_by": [], "supersedes": []})
    d["admission"].update(proposed_by="seed", ledger_entry=None, rung="new-decision",
                          adjudicator={"role": "adjudicator", "model_id": "seed", "call": None})
    d["latches"] = [l for l in d["latches"] if l["type"] != "wiring"]
    for latch in d["latches"] + [d["lifecycle"]["retirement"]]:
        latch["lifecycle"] = {"status": "live", "settled_at": None, "settled_by": None}
    (seed_dir / "decisions").mkdir(parents=True)
    (seed_dir / "decisions" / "D-0001.json").write_text(json.dumps(d, indent=2, sort_keys=True))
    (seed_dir / "vocabulary.json").write_text(json.dumps({"work-shape": {"sql-query": "the task writes a SQL query"}}))
    return seed_dir


def test_inject_mints_past_the_store_prices_and_registers_terms(tmp_path):
    seed = _seed_from(ROOT / "store" / "decisions" / "D-0003.json", tmp_path / "seed")
    store = tmp_path / "store"
    _genesis.seed(store, model_id="stub")
    manifest = _seeds.inject(store, seed, model_id="stub")
    assert [r["id"] for r in manifest["injected"]] == ["D-0001"] and manifest["terms_added"] == ["work-shape:sql-query"]
    rec = read_json(store / "decisions" / "D-0001.json")
    assert rec["priced_for"]["model_id"] == "stub" and rec["admission"]["proposed_by"] == "seed"
    assert read_json(store / "registry" / "ids.json")["D"] == 1
    assert "sql-query" in read_json(store / "registry" / "vocabulary.json")["work-shape"]["terms"]
    assert (store / "seed.json").exists() and (store / "index" / "hooks.json").exists()


def test_a_seed_that_fails_the_floor_is_refused(tmp_path):
    seed = tmp_path / "seed"
    (seed / "decisions").mkdir(parents=True)
    (seed / "decisions" / "D-0001.json").write_text(json.dumps({"id": "D-0001", "kind": "decision", "status": "accepted"}))
    store = tmp_path / "store"
    _genesis.seed(store, model_id="stub")
    with pytest.raises(SystemExit, match="write-seam lint"):
        _seeds.inject(store, seed, model_id="stub")


def test_a_seeded_arm_consults_the_injected_decision_at_boot(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    seed = _seed_from(ROOT / "store" / "decisions" / "D-0003.json", tmp_path / "seed")
    toml = tmp_path / "seeded.toml"
    toml.write_text(f'name = "seeded"\n[defaults]\nmodel = "stub"\nrounds = 1\npasses_per_round = 2\n'
                    f'[arms.seeded]\nmode = "attached"\nseed = "{seed}"\n[arms.bare]\nmode = "attached"\n')
    exp = _experiment.load(toml)
    record = _experiment.run_arm(exp, "seeded", tmp_path / "runs", commit=False)
    assert [r["id"] for r in record["seed"]["injected"]] == ["D-0001"]
    session = read_json(tmp_path / "runs" / "seeded" / "seeded" / "store" / "sessions" / "S-0001.json")
    assert [c["record"] for c in session["consulted"]] == ["D-0001"], "the seed is reached by the boot's index on pass 1"
    bare = _experiment.run_arm(exp, "bare", tmp_path / "runs", commit=False)
    assert bare["seed"] is None
    assert read_json(tmp_path / "runs" / "seeded" / "bare" / "store" / "sessions" / "S-0001.json")["consulted"] == []


def test_resolve_finds_a_world_under_experiments_seeds(tmp_path):
    (tmp_path / "seeds" / "w" / "decisions").mkdir(parents=True)
    assert _seeds.resolve("w", tmp_path / "x.toml") == tmp_path / "seeds" / "w"
    with pytest.raises(SystemExit, match="no directory"):
        _seeds.resolve("nowhere", tmp_path / "x.toml")


def test_two_seeds_inject_in_order_and_the_manifest_holds_both(tmp_path):
    a = _seed_from(ROOT / "store" / "decisions" / "D-0003.json", tmp_path / "a")
    b = _seed_from(ROOT / "store" / "decisions" / "D-0003.json", tmp_path / "b")
    store = tmp_path / "store"
    _genesis.seed(store, model_id="stub")
    _seeds.inject(store, a, model_id="stub")
    manifest = _seeds.inject(store, b, model_id="stub")
    assert [r["id"] for r in manifest["injected"]] == ["D-0001", "D-0002"] and manifest["seed"] == [str(a), str(b)]
    assert (store / "decisions" / "D-0002.json").exists()


def test_every_seeded_arm_in_the_experiment_files_resolves():
    for toml in sorted((ROOT / "experiments").glob("*.toml")):
        if toml.name.startswith("_"):  # extends bases (_base.toml, _teacher.toml), not experiments
            continue
        exp = _experiment.load(toml)
        for arm in exp.arms:
            spec = exp.resolve(arm)
            for name in ([spec.seed] if isinstance(spec.seed, str) else spec.seed or []):
                assert (_seeds.resolve(name, exp.path) / "decisions").is_dir(), f"{toml.name}/{arm}: seed {name}"
