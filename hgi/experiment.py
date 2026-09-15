"""Experiments: the per-run decisions, declared once and kept out of the run.

An experiment file (TOML) names the models it may use, the defaults every
arm inherits, and its arms. An arm is one run of the loop with every
decision fixed: which model serves which role, how many rounds, how many
passes a round holds (the consolidation cadence, written into the arm's
bars), whether the memory is attached or detached, which bars it overrides,
which suite it runs on (the task families, the sample size and the fault
profile — :class:`suite.tasks.SuiteSpec`), and how many tasks the oracle
evaluates at once. Nothing in the file is a secret: a model names the
environment variable that holds its key.

::

    name = "baseline"
    weave_project = "hgi-experiments"       # under $WANDB_ENTITY

    [models.gpt-oss-120b]
    id = "openai/gpt-oss-120b"              # base_url defaults to W&B Inference, the key to $WANDB_API_KEY

    [defaults]
    model = "gpt-oss-120b"
    rounds = 3
    passes_per_round = 2
    [defaults.suite]
    families = ["genesis", "conventions"]   # the task families; size samples each, seeded
    [defaults.suite.faults]
    http_fault_calls = 2                    # the world's fault profile, part of the suite hash

    [arms.attached]
    mode = "attached"
    [arms.detached]
    mode = "detached"
    [arms.strong-judge.roles]
    adjudicator = "gpt-oss-120b"            # any role not named runs on the arm's model

A file may ``extends = "_base.toml"`` (a path relative to the file, or a list
of them with later bases winning) to inherit a base file's tables — the
shared model registry, the ``weave_project``, a defaults block — which the
file's own tables then override, deep-merged the way an arm overrides the
defaults. A base may itself ``extends`` another; a base declares no arms and
is not a runnable experiment (its name is ``_``-prefixed by convention). The
experiment an arm loaded is snapshotted, bases merged in and ``extends``
stripped, as ``experiment.json`` beside its ``arm.json``, so a later reading
resolves against the file as it was and not against a base since edited
(:func:`Experiment.resolved`, item 52).

A **stream** arm meets a different batch every pass instead of one suite
every pass (:mod:`suite.stream`): ``[stream]`` names the pool's families,
the batch size and count, the seed and the fault profile, and the batches
to revisit after the stream; ``rounds`` is then the batch count over
``passes_per_round``. Pass *k* boots, evaluates batch *k* at first sight,
closes, and consolidates at each round's end; a detached stream arm draws
the same batches with no store. ``arm.json`` records every batch's hash and
tasks, and the arm ends by writing its evolution log
(:mod:`hgi.evolution`) beside it.

A **retrofit** (:mod:`hgi.retrofit`) is an arm that never ran a forward
pass: ``hgi experiment retrofit <old arm> --out <dir>`` splices an old
attached arm's recorded sessions into a fresh store and runs today's
backward pass over them, so the store after every iteration is what today's
code would have made of the same rows. Its ``arm.json`` carries a
``retrofit`` block naming the source, and ``report``, ``evolution`` and the
dashboard read a directory of such arms as an experiment (:func:`from_dir`);
``hgi experiment compare <retrofit arm>`` writes the per-iteration reading
of the retrofitted store beside the original's.

The runner gives each arm a fresh store under ``runs/<experiment>/<arm>/``,
in its own git repository so the write law (every write ends in a commit)
holds per arm and the code repository's history stays the code's. It seeds
the store priced for the arm's pass model, writes the cadence into the bars,
and drives the same commands ``demo.sh`` drives — ``boot``, ``evaluate``,
``close``, ``consolidate`` at each round's end, ``evaluate --detached`` for
a detached arm — through the command surface, so an arm is exactly what a
hand-run would be. ``arm.json`` beside the store records what the arm
resolved to, the code tree's commit at the moment it started (``null``
outside a checkout — a running arm outlives a commit that lands on the tree
under it, item 35), and, at the end, its curve; the report reads every
arm's curve back from its store.

Every pass also writes a **health** block into ``arm.json`` — a pure read of
the store the arm already has (:func:`hgi.evolution.health`), so a failing
arm is diagnosable while it runs and not only once the curve is in: per pass,
what retrieval reached (the records considered and the accepted
non-constitution ones a pass had in context), the tool and harness error
classes its rows carried, the failed rows against the observations filed from
them, and the disposition of the round's drafts. The field is additive; a
reading of an older ``arm.json`` that predates it is unaffected.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

import suite as _suite
from hgi import evolution
from hgi import model as _model
from hgi import registry as _registry
from hgi import tracing
from hgi.roles import ROLES
from suite import stream as _stream
from suite.stream import StreamSpec
from suite.tasks import Suite, SuiteSpec, build

RUNS = Path("runs")
"""Where arms run: ``$HGI_RUNS`` or ``./runs``, one directory per experiment, one per arm."""

BACKWARD_ROLES = ("consolidator", "examiner", "adjudicator", "coder")


class ModelSpec(BaseModel):
    """One model behind one OpenAI-compatible endpoint. The alias is the key it is declared under."""

    id: str
    """The model id the endpoint serves — ``openai/gpt-oss-120b`` on W&B Inference."""
    base_url: str = _model.WANDB_INFERENCE
    api_key_env: str = "WANDB_API_KEY"
    """The environment variable holding the key. On W&B Inference an absent variable falls back to the netrc entry ``wandb login`` wrote."""
    temperature: float = 0.0
    project: str | None = None
    """The ``OpenAI-Project`` header; on W&B Inference, ``entity/project`` for usage attribution, defaulting to the Weave project."""
    stub: bool = False
    """The deterministic stub under this alias's ``id`` — for offline arms and for telling two stub roles apart."""
    reasoning_effort: str | None = None
    """``low`` | ``medium`` | ``high``, sent as ``reasoning_effort`` on every call to this model; only models that accept the parameter should set it — gpt-oss does."""
    provider: str | None = None
    """``"claude-cli"`` routes this alias to the local ``claude`` CLI (:class:`hgi.model.ClaudeCLI`, ``id`` as its
    model alias) instead of an OpenAI-compatible endpoint — a cost-offload path for a teacher role, billed to a
    Claude subscription. ``None`` (the default) is every existing spec's path and is unaffected."""

    model_config = ConfigDict(extra="forbid")

    def backend(self) -> _model.Backend:
        if self.stub:
            b = _model.Stub()
            b.model_id = self.id
            return b
        if self.provider == "claude-cli" or self.base_url == _model.CLAUDE_CLI_SENTINEL:
            return _model.ClaudeCLI(model=self.id)
        on_wandb = self.base_url.startswith(_model.WANDB_INFERENCE)
        key = os.environ.get(self.api_key_env) or (_model.wandb_api_key() if on_wandb else None)
        if not key:
            raise SystemExit(f"model {self.id!r}: ${self.api_key_env} is not set" + (" and wandb holds no key" if on_wandb else ""))
        project = self.project or (_wandb_project() if on_wandb else None)
        return _model.OpenAICompatible(self.base_url, key, self.id, temperature=self.temperature, project=project,
                                       reasoning_effort=self.reasoning_effort)


STUB = ModelSpec(id="stub", stub=True)


def _wandb_project() -> str:
    """W&B Inference answers 401 without an ``entity/project`` to attribute usage to: the Weave project under ``$WANDB_ENTITY``."""
    project = tracing.project_name()
    if not project or "/" not in project:
        raise SystemExit("W&B Inference needs an entity/project for usage attribution: set WANDB_ENTITY and a weave project "
                         "(the experiment's weave_project or $HGI_WEAVE_PROJECT), or `project` on the model")
    return project


class ArmSpec(BaseModel):
    """One run of the loop with every per-run decision fixed."""

    mode: Literal["attached", "detached"] = "attached"
    """Attached: boot, evaluate, close every pass, consolidate every round. Detached: the ablation — the same agent and suite
    with no store, so its passes are independent draws of one evaluation and (unless ``serial_detached``) are drawn concurrently."""
    rounds: int = Field(default=3, ge=1)
    """Consolidation cycles. A detached arm has no consolidation; its rounds only size the run."""
    passes_per_round: int = Field(default=2, ge=1)
    """Passes between consolidations — written into the arm's bars as ``consolidation_every_passes``."""
    model: str = "stub"
    """The alias every role runs on unless ``roles`` says otherwise."""
    roles: dict[str, str] = Field(default_factory=dict)
    bars: dict[str, Any] = Field(default_factory=dict)
    """Overrides merged over the seed's bars, nested tables deep-merged (``[arms.x.bars.retirement] window_passes = 4``)."""
    suite: SuiteSpec = Field(default_factory=SuiteSpec)
    """The world: task families, sample size and seed, fault profile. Deep-merged like ``bars``."""
    stream: StreamSpec | None = None
    """A stream arm's pool and deal (:class:`suite.stream.StreamSpec`); when set, ``suite`` is unused and ``rounds`` is derived."""
    concurrency: int = Field(default=4, ge=1)
    """Tasks the oracle evaluates at once — W&B Inference answers 429 past its concurrency limit."""
    serial_detached: bool = True
    """A detached arm's passes are drawn one at a time, not concurrently. The safe default: each pass already
    runs its tasks ``concurrency`` at a time, and a thread pool of passes on top of that multiplies it —
    running several arms together this way put 429s past the client's retries into the detached rows on
    a real endpoint (decision 36). ``False`` restores the old concurrent draw, sound alone or with headroom
    under the endpoint's ceiling."""
    seed: str | list[str] | None = None
    """Hand-authored seed stores injected before pass 1, in order (:mod:`hgi.seeds`): each a directory, a path relative
    to the experiment file, or a world name under ``experiments/seeds``. The compare/contrast against the same arm unseeded."""
    description: str = ""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _rounds_from_stream(self):
        if self.stream is not None:
            if self.stream.batches % self.passes_per_round:
                raise ValueError(f"a stream of {self.stream.batches} batches does not divide into rounds of {self.passes_per_round} passes")
            self.rounds = self.stream.batches // self.passes_per_round
        return self

    @property
    def passes(self) -> int:
        """Passes in the run proper — the stream's batches, or the rounds' passes; a revisit pass comes after these."""
        return self.rounds * self.passes_per_round

    @property
    def revisits(self) -> list[int]:
        """The batches an attached stream arm meets again after the stream; nothing for a detached arm, whose draws are one evaluation."""
        return list(self.stream.revisit) if self.stream is not None and self.mode == "attached" else []

    def batches(self) -> list[Suite] | None:
        """The stream's batches, dealt by the seed; ``None`` for a suite arm."""
        return _stream.partition(self.stream) if self.stream is not None else None

    def alias_for(self, role: str) -> str:
        return self.roles.get(role, self.model)


class Experiment(BaseModel):
    name: str
    description: str = ""
    weave_project: str | None = None
    """The Weave project the arms trace into (under ``$WANDB_ENTITY``); absent, the environment's ``$HGI_WEAVE_PROJECT`` stands."""
    models: dict[str, ModelSpec] = Field(default_factory=dict)
    defaults: dict[str, Any] = Field(default_factory=dict)
    arms: dict[str, dict[str, Any]]
    path: Path | None = None

    model_config = ConfigDict(extra="forbid")

    _resolved: dict[str, Any] = PrivateAttr(default_factory=dict)
    """The file's tables with every ``extends`` base merged in and ``extends`` stripped, as :func:`load` read them —
    the self-contained definition, snapshotted beside ``arm.json`` (:func:`resolved`)."""

    def resolved(self) -> dict[str, Any]:
        """The self-contained experiment definition an arm loaded: the file's tables with every ``extends`` base merged
        under them and ``extends`` stripped. Snapshotted beside ``arm.json`` so a later reading resolves against the file
        as it was, not against a base file since edited (item 52). Reconstructed from :func:`load` when set, else re-read."""
        return self._resolved or (_load_raw(self.path) if self.path else {})

    def model_spec(self, alias: str) -> ModelSpec:
        if alias in self.models:
            return self.models[alias]
        if alias == "stub":
            return STUB
        raise SystemExit(f"experiment {self.name}: no model {alias!r} declared; models are {sorted(self.models) + ['stub']}")

    def resolve(self, arm: str) -> ArmSpec:
        """The arm with the experiment's defaults under it: scalars overridden, ``roles`` and ``bars`` merged."""
        if arm not in self.arms:
            raise SystemExit(f"experiment {self.name}: no arm {arm!r}; arms are {sorted(self.arms)}")
        merged = _merge(deepcopy(self.defaults), self.arms[arm])
        spec = ArmSpec(**merged)
        unknown = set(spec.roles) - set(ROLES)
        if unknown:
            raise SystemExit(f"arm {arm}: unknown roles {sorted(unknown)}; roles are {ROLES}")
        for alias in {spec.model, *spec.roles.values()}:
            self.model_spec(alias)
        return spec

    def roster(self, arm: str) -> dict[str, str]:
        """Role → model id, as the arm resolves it."""
        spec = self.resolve(arm)
        return {role: self.model_spec(spec.alias_for(role)).id for role in ROLES}


def _merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    for k, v in over.items():
        base[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else deepcopy(v)
    return base


def _load_raw(path: Path | str) -> dict[str, Any]:
    """A file's tables with its ``extends`` bases merged under them and ``extends`` stripped. ``extends`` names a base file
    (or a list of them, later bases winning) resolved relative to this file; a base may itself ``extends`` another. The
    child's tables override the bases, deep-merged like an arm over the defaults (:func:`_merge`). A ``.json`` file is
    read as a resolved snapshot (:func:`Experiment.resolved`); everything else as TOML."""
    path = Path(path)
    with path.open("rb") as f:
        raw = json.load(f) if path.suffix == ".json" else tomllib.load(f)
    bases = raw.pop("extends", None)
    if not bases:
        return raw
    merged: dict[str, Any] = {}
    for rel in [bases] if isinstance(bases, str) else bases:
        _merge(merged, _load_raw((path.parent / rel).resolve()))
    return _merge(merged, raw)


def load(path: Path | str) -> Experiment:
    path = Path(path)
    raw = _load_raw(path)
    exp = Experiment(**raw, path=path)
    exp._resolved = raw
    return exp


def runs_root() -> Path:
    return Path(os.environ.get("HGI_RUNS", RUNS))


def arm_dir(exp: Experiment, arm: str, root: Path | None = None) -> Path:
    return (root or runs_root()) / exp.name / arm


def spec_of(record: dict[str, Any]) -> ArmSpec:
    """The arm spec an ``arm.json`` recorded, read back under today's fields; a field the record carries that the
    spec no longer declares is dropped rather than refused, so an old arm still reads."""
    return ArmSpec(**{k: v for k, v in record["spec"].items() if k in ArmSpec.model_fields})


def recorded_batches(spec: ArmSpec, record: dict[str, Any]) -> tuple[list[Suite] | None, str | None]:
    """The batches a stream arm met, dealt again from its spec — or, when the pool has changed since the arm ran (a budget,
    a prompt), rebuilt from the task ids ``arm.json`` recorded, with a warning saying so, so a reading still meets the
    arm that ran. ``(None, None)`` for a suite arm."""
    if spec.stream is None or not record.get("stream"):
        return None, None
    batches = spec.batches()
    recorded = {b["batch"]: b["hash"] for b in record["stream"]["batches"]}
    if recorded == {n: b.hash for n, b in enumerate(batches, 1)}:
        return batches, None
    pool = build(spec.stream.pool_spec).by_id
    missing = sorted({t for b in record["stream"]["batches"] for t in b["tasks"] if t not in pool})
    if missing:
        raise SystemExit(f"{record.get('experiment')}/{record.get('arm')}: the pool has changed since the arm ran and no longer holds {', '.join(missing[:5])}")
    rebuilt = [Suite(spec=spec.stream.pool_spec, tasks=[pool[t] for t in b["tasks"]]) for b in record["stream"]["batches"]]
    return rebuilt, "the pool has changed since the arm ran; batches rebuilt from the recorded task ids, hashes differ"


def _alias_of(model_id: str) -> str:
    return model_id.rsplit("/", 1)[-1].lower()


def from_dir(path: Path | str) -> tuple[Experiment, Path]:
    """An experiment synthesized from arm directories on disk — arms no experiment file declares, such as retrofits
    (:mod:`hgi.retrofit`): one arm per ``arm.json`` under ``path`` (or ``path`` itself when it is an arm), each with
    its recorded spec and a model per distinct id of its roster, so ``report``, ``evolution`` and the dashboard read
    them exactly as they read a declared arm. Returns the experiment and the runs root the directories sit under."""
    path = Path(path).resolve()
    dirs = [path] if (path / "arm.json").exists() else sorted(p.parent for p in path.glob("*/arm.json"))
    if not dirs:
        raise SystemExit(f"{path} holds no arm.json, and no directory under it does")
    models: dict[str, ModelSpec] = {}
    arms: dict[str, dict[str, Any]] = {}
    notes = []
    for d in dirs:
        record = json.loads((d / "arm.json").read_text())
        spec = {k: v for k, v in record["spec"].items() if k in ArmSpec.model_fields}
        roster = record["roster"]
        pass_alias = spec.get("model", "stub")
        models[pass_alias] = ModelSpec(id=roster["pass"], stub=roster["pass"] == "stub")
        roles = {}
        for role, mid in roster.items():
            if role == "pass" or mid == roster["pass"]:
                continue
            alias = next((a for a, m in models.items() if m.id == mid), None) or _alias_of(mid)
            models[alias] = ModelSpec(id=mid, stub=mid == "stub")
            roles[role] = alias
        spec["roles"] = roles
        arms[d.name] = spec
        if r := record.get("retrofit"):
            notes.append(f"{d.name}: retrofit of {r['source_experiment']}/{r['source_arm']} at {str(r.get('source_commit') or '?')[:7]}, "
                         f"the backward pass on {r['teacher']}")
    description = ("not a live run — " + "; ".join(notes)) if notes else ""
    return Experiment(name=dirs[0].parent.name, description=description, models=models, arms=arms), dirs[0].parent.parent


# --- running an arm ------------------------------------------------------------------------

def install(exp: Experiment, spec: ArmSpec) -> dict[str, str]:
    """Install the arm's backends — one client per alias — and return the roster."""
    _model.reset()
    clients = {alias: exp.model_spec(alias).backend() for alias in {spec.model, *spec.roles.values()}}
    _model.use(clients[spec.model])
    for role, alias in spec.roles.items():
        _model.use(clients[alias], role=role)
    return _model.roster()


def seed_arm(exp: Experiment, arm: str, spec: ArmSpec, root: Path, roster: dict[str, str]):
    """A fresh store priced for the pass model, with the cadence and the arm's overrides written into its bars."""
    from hgi.genesis import seed

    reg = seed(root, model_id=roster["pass"])
    bars = _merge(_merge(dict(reg.bars), {"consolidation_every_passes": spec.passes_per_round}), spec.bars)
    _registry.write_json(root / "registry" / "bars.json", bars)
    for name in ([spec.seed] if isinstance(spec.seed, str) else spec.seed or []):
        from hgi import seeds as _seeds
        _seeds.inject(root, _seeds.resolve(name, exp.path), model_id=roster["pass"])
    return _registry.load(root)


def _preflight_shell(spec: ArmSpec) -> None:
    """Item 53: before an arm runs a single pass, verify the shell tool's own ``python3`` can import every module
    the arm's families declare they need (:attr:`suite.families.Family.requires`). A reasoning-core arm whose shell
    ``python3`` is a system interpreter without ``nltk`` would spend every row discovering the library is missing —
    ``pip install`` as the next call, the budget then refused, the answer given unverified — and file
    library-availability decisions instead of world decisions. The check runs in the same environment the shell
    tool runs under (:func:`suite.tools.can_import`), so it exercises the python a shell call actually resolves to,
    not the runner's own interpreter; it refuses to start the arm with a clear error when that python cannot import
    the requirements."""
    from suite import tools as _tools
    from suite.families import FAMILIES

    fams = spec.stream.families if spec.stream is not None else spec.suite.families
    modules: list[str] = []
    for name in fams:
        fam = FAMILIES.get(name)
        if fam is None:
            continue
        for m in fam.requires:
            if m not in modules:
                modules.append(m)
    error = _tools.can_import(modules)
    if error:
        raise SystemExit(
            f"arm cannot start: its families {sorted(set(fams))} need {modules} importable by the shell tool's "
            f"python, but that python cannot import them: {error}. The shell tool runs `python3` from PATH — put "
            f"the tree's venv on PATH (export PATH=<tree>/.venv/bin:$PATH) so a shell call's python has the "
            f"family's requirements, then rerun the arm."
        )


def run_arm(exp: Experiment, arm: str, root: Path | None = None, *, commit: bool = True, force: bool = False) -> dict[str, Any]:
    """Run one arm to completion in its own store; return the ``arm.json`` record."""
    from hgi import cli
    from hgi.store import Store, git

    spec = exp.resolve(arm)
    _preflight_shell(spec)  # item 53: refuse before touching disk if the shell python can't import the families' requirements
    where = arm_dir(exp, arm, root)
    if where.exists():
        if not force:
            raise SystemExit(f"{where} exists; pass --force to rerun the arm (its store is discarded)")
        shutil.rmtree(where)
    where.mkdir(parents=True)
    store_root = where / "store"
    if commit:
        git("init", "-q", cwd=where)

    if exp.weave_project:
        os.environ["HGI_WEAVE_PROJECT"] = exp.weave_project
    os.environ["WEAVE_PARALLELISM"] = str(spec.concurrency)
    roster = install(exp, spec)
    batches = spec.batches()
    world = batches[0] if batches else build(spec.suite)
    suite_token = _suite.use(world)
    reg = seed_arm(exp, arm, spec, store_root, roster)
    token = _registry.use(reg)
    store = Store(store_root, registry=reg)
    record: dict[str, Any] = {
        "experiment": exp.name, "arm": arm, "spec": spec.model_dump(), "passes": spec.passes, "roster": roster,
        "suite": {"hash": world.hash, "tasks": len(world.tasks), "families": world.families()} if not batches else None,
        "seed": _registry.read_json(store_root / "seed.json") if (store_root / "seed.json").exists() else None,
        "stream": {"batches": [_stream.batch_record(n, b) for n, b in enumerate(batches, 1)], "revisit": spec.revisits,
                   "passes": {n: n for n in range(1, spec.passes + 1)} | {spec.passes + k: r for k, r in enumerate(spec.revisits, 1)}} if batches else None,
        "weave_project": tracing.project_name(), "started_at": _now(), "finished_at": None, "sessions": [], "curve": {}, "health": {},
        "commit": _tree_commit(),
    }
    _write(where / "arm.json", record)
    _write(where / "experiment.json", exp.resolved())  # item 52: pin the resolved definition (extends merged in) beside the arm
    previous_store = os.environ.get("HGI_STORE")
    os.environ["HGI_STORE"] = str(store_root)
    tracing.run(exp.name, arm)
    argv = ["--store", str(store_root)] + ([] if commit else ["--no-commit"])

    def hgi(*args: str) -> None:
        if cli.main([args[0], *argv, *args[1:]]) != 0:
            raise SystemExit(f"hgi {args[0]} failed in arm {arm}")

    def hgi_retry(*args: str, tries: int = 3) -> None:
        """A step that reaches the model or Weave endpoints, retried on a transient failure so a flush/pairing timeout or a
        rate-limit blip does not abort the arm (carry-forward items 34, 36). Re-running ``evaluate`` on the same session
        re-runs the suite and overwrites the session's evaluation, so the step is safe to repeat; the last attempt raises."""
        for attempt in range(1, tries + 1):
            try:
                return hgi(*args)
            except (Exception, SystemExit) as e:  # SystemExit is hgi()'s own nonzero-step signal and is not an Exception; KeyboardInterrupt still aborts
                if attempt == tries:
                    raise
                print(f"arm {arm}: `{args[0]}` failed ({type(e).__name__}: {str(e).splitlines()[0][:200]}); retry {attempt}/{tries - 1}")

    def suite_for(n: int) -> Suite:
        """The suite pass ``n`` meets: batch ``n`` of the stream, a revisited batch past the stream, or the arm's one suite."""
        if not batches:
            return world
        return batches[record["stream"]["passes"][n] - 1]

    def progress() -> None:
        # sorted by id, not pass: a detached arm draws its passes concurrently, so the
        # session ids are minted in lock-acquisition order — the set is stable, the order is not.
        record["sessions"] = sorted(s.id for s in _sessions(store, spec.mode))
        record["curve"] = curve(store, spec.mode)
        record["health"] = evolution.health(store, spec.mode)
        _write(where / "arm.json", record)

    try:
        _commit_arm(where, store, commit, _genesis_message(exp, arm, spec, store, roster))
        if spec.mode == "attached":
            for n in range(1, spec.passes + len(spec.revisits) + 1):
                _suite.use(suite_for(n))
                try:
                    session = store.mint("session")
                    hgi("boot", "--session", session, "--pass", str(n))
                    hgi_retry("evaluate", "--session", session)
                    hgi("close", "--session", session)
                    if n <= spec.passes and n % spec.passes_per_round == 0:
                        hgi("consolidate")
                except (Exception, SystemExit) as e:  # a pass that still fails after its retries must not abort the arm unrecoverably (KeyboardInterrupt still aborts)
                    # Bad data or a persistent endpoint fault on one pass finalizes the arm gracefully: the passes already
                    # committed stand, the failure is recorded, and the `finally` writes arm.json and commits (item 34).
                    record["error"] = f"pass {n} failed: {type(e).__name__}: {str(e).splitlines()[0][:300]}"
                    print(f"arm {exp.name}/{arm}: {record['error']}; stopping after {n - 1} completed pass(es)")
                    break
                progress()
        else:
            _detached_passes(spec, store, hgi, progress, suite_for)
        _suite.use(world)
        if not record.get("error"):  # a lint over a partial store after a graceful stop would turn a recorded error into a crash
            hgi("lint", "--model", roster["pass"])
    finally:
        record["finished_at"] = _now()
        _write(where / "arm.json", record)
        if batches:
            evolution.write(exp, arm, root)
        _commit_arm(where, store, commit, f"Arm {exp.name}/{arm} finished: {_curve_line(record['curve'])}")
        tracing.run()
        _registry.reset(token)
        _suite.reset(suite_token)
        _model.reset()
        if previous_store is None:
            os.environ.pop("HGI_STORE", None)
        else:
            os.environ["HGI_STORE"] = previous_store
    return record


DETACHED_AT_ONCE = 3
"""Detached passes drawn concurrently when ``serial_detached`` is off; each already runs its tasks ``concurrency`` at a time."""


def _detached_passes(spec: ArmSpec, store, hgi, progress, suite_for) -> None:
    """A detached arm's passes are draws of one evaluation — no boot, no close, nothing carried between them.
    ``spec.serial_detached`` (the default) draws them one at a time in this thread, the way an experiment's
    other arms and an attached arm's own passes run — safe to run several arms of an experiment together
    under one endpoint's concurrency ceiling (decision 36). Off, they are drawn concurrently instead, each in
    a copy of the runner's context with its own suite in scope (a stream arm's pass draws its batch) — faster
    alone, or with headroom under the ceiling; a worker thread starts with no Weave project bound in its own
    context, so each re-enters the client before drawing (item 34) — moot in the serial mode above, where
    every draw runs in the thread the arm's own ``tracing.run()`` already joined. Either way each pass is
    written without a commit; the arm commits once."""
    from hgi import index as _index

    def draw(n: int) -> None:
        _suite.use(suite_for(n))
        hgi("evaluate", "--detached", "--pass", str(n), "--no-commit")  # the detached command mints its own session

    if spec.serial_detached:
        for n in range(1, spec.passes + 1):
            draw(n)
            progress()
    else:
        import contextvars
        from concurrent.futures import ThreadPoolExecutor

        def draw_in_thread(n: int) -> None:
            tracing.rejoin()
            draw(n)

        with ThreadPoolExecutor(max_workers=min(DETACHED_AT_ONCE, spec.passes)) as pool:
            futures = [pool.submit(contextvars.copy_context().run, draw_in_thread, n) for n in range(1, spec.passes + 1)]
            for f in futures:
                f.result()
                progress()
    _index.regenerate(store)


def _genesis_message(exp: Experiment, arm: str, spec: ArmSpec, store, roster: dict[str, str]) -> str:
    """The arm's genesis commit subject, naming the constitution ids it admits as a range, so
    ``hgi lineage C-0003`` resolves this commit as the article's admission (decision 28)."""
    ids = sorted(a.id for a in store.articles())
    span = f", constitution {ids[0]}..{ids[-1]}" if len(ids) > 1 else (f", constitution {ids[0]}" if ids else "")
    return f"Genesis for {exp.name}/{arm}: priced for {roster['pass']}, {spec.rounds} rounds of {spec.passes_per_round}{span}"


def _commit_arm(where: Path, store, commit: bool, message: str) -> None:
    from hgi.store import git

    if not commit:
        return
    git("add", "-A", ".", cwd=where)
    if git("status", "--porcelain", cwd=where):
        git("commit", "-q", "-m", message, cwd=where)


def _sessions(store, mode: str):
    attached = mode == "attached"
    return sorted((s for s in store.all("session") if s.attached == attached and s.evaluation is not None), key=lambda s: s.pass_)


def curve(store, mode: str, scorer: str = "task_pass_rate") -> dict[int, float | None]:
    """Pass → the scorer's value over the arm's sessions of ``mode``; ``None`` where unevaluable."""
    return {s.pass_: (s.evaluation.scores[scorer].value if scorer in s.evaluation.scores else None) for s in _sessions(store, mode)}


def _curve_line(c: dict[Any, float | None]) -> str:
    return " ".join("—" if v is None else f"{v:.2f}" for _, v in sorted(c.items(), key=lambda kv: int(kv[0]))) or "no passes"


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tree_commit(root: Path | None = None) -> str | None:
    """The git HEAD of the tree this process runs from — not the arm's own store repository, the code
    repository above it (``root``, default this file's directory). Pinned into ``arm.json`` at the arm's
    start: a long-running arm's process keeps the module it imported even after a later commit changes the
    tree under it (item 35), so the record says which tree actually ran. ``None`` outside a git checkout."""
    from hgi.store import git

    try:
        return git("rev-parse", "HEAD", cwd=root or Path(__file__).resolve().parent)
    except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
        return None


# --- reading arms back ----------------------------------------------------------------------

def report(exp: Experiment, root: Path | None = None, arms: list[str] | None = None) -> str:
    """Every arm's curve, read back from its store; an arm that has not run reads as such.

    ``arms`` restricts the report to a subset. The finish path (:func:`_cmd`) names only the arm(s) this
    invocation actually ran, so a commit that later appends an arm the running tree cannot construct — the pinned
    worktree that never had the appended arm's field (item 52a) — cannot crash the report of the arms that did run
    and whose stores are already on disk. An arm that no longer resolves at all is reported as a note row rather
    than crashing the whole table, so even a full-file report survives one unconstructable arm."""
    from hgi.store import Store

    rows = []
    width = 0
    for arm in (arms if arms is not None else list(exp.arms)):
        try:
            spec = exp.resolve(arm)
            roster = exp.roster(arm)
        except (SystemExit, Exception) as e:  # an arm this tree cannot construct: a later-appended field, an undeclared model
            rows.append((arm, arm, None, {}, [], f"cannot resolve: {str(e).splitlines()[0]}"))
            continue
        where = arm_dir(exp, arm, root)
        label = roster["pass"] + ("" if all(m == roster["pass"] for m in roster.values()) else " +" + "/".join(
            sorted({m for r, m in roster.items() if m != roster["pass"]})))
        if not (where / "store" / "registry").exists():
            rows.append((arm, label, spec, {}, [], "not run"))
            continue
        reg = _registry.load(where / "store")
        token = _registry.use(reg)
        try:
            store = Store(where / "store", registry=reg)
            c = curve(store, spec.mode)
            admitted = [d for k in store.all("consolidation") for d in k.admitted]  # type: ignore[attr-defined]
        finally:
            _registry.reset(token)
        width = max(width, spec.passes + len(spec.revisits))
        rows.append((arm, label, spec, c, admitted, None))
    head = ["arm", "model", "mode", "rounds×size"] + [f"p{n}" for n in range(1, width + 1)] + ["admitted"]
    lines = [f"# {exp.name}" + (f" — {exp.description}" if exp.description else ""), "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for arm, label, spec, c, admitted, note in rows:
        if spec is None:  # an arm that would not resolve: a note row, so the arms that did run still report
            lines.append("| " + " | ".join([arm, label, "—", "—"] + [""] * width + [note or "unresolvable"]) + " |")
            continue
        cells = [arm, label, spec.mode, f"{spec.rounds}×{spec.passes_per_round}" + (f" stream ×{spec.stream.batch}" if spec.stream else "")]
        cells += [("—" if c.get(n) is None else f"{c[n]:.2f}") if n <= spec.passes + len(spec.revisits) else "" for n in range(1, width + 1)]
        cells.append(note or (" ".join(admitted) or "nothing"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def show(exp: Experiment) -> str:
    """The resolved plan of every arm — no store touched, no call made."""
    lines = [f"experiment {exp.name}" + (f": {exp.description}" if exp.description else ""),
             f"weave project: {exp.weave_project or '(environment)'}", f"runs under: {runs_root() / exp.name}", ""]
    for arm in exp.arms:
        spec = exp.resolve(arm)
        roster = exp.roster(arm)
        lines.append(f"arm {arm}: {spec.mode}, {spec.rounds} rounds × {spec.passes_per_round} passes = {spec.passes} passes, concurrency {spec.concurrency}")
        if spec.description:
            lines.append(f"  {spec.description}")
        lines.append("  roles: " + ", ".join(f"{r}={m}" for r, m in roster.items()))
        if spec.stream is not None:
            lines.append("  " + _stream.describe(spec.stream, spec.batches()) + (f"; revisit passes {spec.passes + 1}..{spec.passes + len(spec.revisits)}" if spec.revisits else ""))
        else:
            lines.append("  " + build(spec.suite).describe())
        if spec.bars:
            lines.append(f"  bars: {json.dumps(spec.bars, sort_keys=True)}")
    return "\n".join(lines)


def list_models(base_url: str, api_key_env: str = "WANDB_API_KEY") -> list[str]:
    """The model ids the endpoint serves right now — the check an experiment file's ids are made against."""
    from openai import OpenAI

    on_wandb = base_url.startswith(_model.WANDB_INFERENCE)
    key = os.environ.get(api_key_env) or (_model.wandb_api_key() if on_wandb else None)
    if not key:
        raise SystemExit(f"${api_key_env} is not set")
    client = OpenAI(base_url=base_url, api_key=key, project=_wandb_project() if on_wandb else None)
    return sorted(m.id for m in client.models.list())


# --- the command ------------------------------------------------------------------------------

def register(add, store_of, finish) -> None:
    p = add("experiment", "run, show, report, retrofit or compare an experiment's arms")
    p.add_argument("action", choices=["run", "show", "report", "evolution", "models", "retrofit", "compare"])
    p.add_argument("file", nargs="?", help="the experiment TOML; for `report`/`evolution` also an arm directory or a directory of arms; "
                                          "for `retrofit` the old arm directory; for `compare` a retrofitted arm directory")
    p.add_argument("more", nargs="*", help="for `compare`: further retrofitted arm directories")
    p.add_argument("--arm", action="append", help="run only this arm (repeatable); default every arm in file order")
    p.add_argument("--force", action="store_true", help="rerun an arm that has run, discarding its store")
    p.add_argument("--base-url", default=_model.WANDB_INFERENCE, help="for `models`: the endpoint to list")
    p.add_argument("--api-key-env", default="WANDB_API_KEY", help="for `models`: the variable holding the key")
    p.add_argument("--out", help="for `retrofit`: the new arm directory; for `compare`: the results directory (default experiments/results/retrofit)")
    p.add_argument("--teacher", help="for `retrofit`: the model (an alias of the source experiment's file, or an id) the backward-pass roles run on")
    p.add_argument("--upto", type=int, help="for `retrofit`: stop after this pass")
    p.set_defaults(fn=_cmd)


def _cmd(args) -> int:
    if args.action == "models":
        print("\n".join(list_models(args.base_url, args.api_key_env)))
        return 0
    if not args.file:
        raise SystemExit("an experiment file is required")
    if args.action == "retrofit":
        from hgi import retrofit as _retrofit

        if not args.out:
            raise SystemExit("retrofit writes a new arm: pass --out <directory>")
        record = _retrofit.retrofit(args.file, args.out, teacher=args.teacher, upto=args.upto, commit=not args.no_commit, force=args.force)
        print(f"retrofit/{record['arm']}: {_curve_line(record['curve'])}", file=sys.stderr)
        return 0
    if args.action == "compare":
        from hgi import retrofit as _retrofit

        print(_retrofit.compare([args.file, *args.more], Path(args.out) if args.out else None))
        return 0
    root = None
    if Path(args.file).is_dir():
        exp, root = from_dir(args.file)
    else:
        exp = load(args.file)
    if args.action == "show":
        print(show(exp))
        return 0
    if args.action == "report":
        print(report(exp, root))
        return 0
    if args.action == "evolution":
        print(evolution.write_experiment(exp, root))
        return 0
    ran = args.arm or list(exp.arms)
    for arm in ran:
        print(f"== {exp.name}/{arm} ==", file=sys.stderr)
        record = run_arm(exp, arm, commit=not args.no_commit, force=args.force)
        print(f"{exp.name}/{arm}: {_curve_line(record['curve'])}", file=sys.stderr)
    # The finish report and evolution log resolve only the arm(s) this invocation ran (item 52a): a commit that
    # appended an arm the pinned worktree cannot construct must not crash the report of the arms whose stores are
    # on disk. `--arm` dispatch already narrows `ran`; a full run narrows nothing but is immune all the same.
    print(report(exp, arms=ran))
    if any(exp.resolve(a).stream is not None for a in ran):
        finished = exp.model_copy(update={"arms": {a: exp.arms[a] for a in ran}})
        print(evolution.write_experiment(finished))
    return 0
