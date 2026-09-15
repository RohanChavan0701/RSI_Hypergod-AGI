---
name: experiment-runner
description: >-
  Run, pilot, and calibrate HGI experiments against the real model endpoint.
  Use when about to launch an experiment or arm (`hgi experiment run`), run a
  calibration or first-sight pilot, verify a role prompt on a model
  (`hgi roles try`), or when a run fails with a W&B 401, a 429 rate limit, or a
  missing-module error in the shell tool. Carries the endpoint setup (the
  WANDB_ENTITY / weave-project 401 trap, the netrc key), the concurrency
  ceiling that forces arms to run sequentially, how to run to a scratch
  directory, the reasoning-core generator stack, and how to read an arm's
  result back. The store/loop mechanics themselves live in the code and in
  `hgi --help`; this is the operator's procedure.
---

# experiment-runner — launching HGI experiments on the real endpoint

An experiment is a TOML under `experiments/` naming a model roster and a set of
arms; each arm runs the suite in its own store and writes `arm.json`, an
evolution log, and (unless `--no-commit`) a commit. This skill is how to run one
without re-deriving the environment each time. Invoke everything through the
uv-managed venv: `uv run hgi …` (or `.venv/bin/hgi`); `hgi` is not on PATH.

## The endpoint (do this first — it's the usual reason a run won't start)

The backend defaults to W&B Inference. The API key is read from `~/.netrc`
(`machine api.wandb.ai`) or `$WANDB_API_KEY`. **W&B returns 401 unless a usage
owner is set**, so every real-model run needs:

- `WANDB_ENTITY` — this repo uses `slavazinevich-worldvue`.
- a weave project — the TOML's `weave_project` (already `hgi-experiments` in the
  shipped TOMLs), or `$HGI_WEAVE_PROJECT=hgi-experiments`.

```
WANDB_ENTITY=slavazinevich-worldvue uv run hgi experiment run experiments/<x>.toml --arm <arm>
```

Model ids are W&B Inference ids: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`,
`Qwen/Qwen3.6-35B-A3B`, `deepseek-ai/DeepSeek-V4-Pro`. `uv run hgi experiment
models` lists what is live today.

## Running arms

- One arm: `... hgi experiment run experiments/<x>.toml --arm <arm>` (repeat
  `--arm` for a few; omit it to run every arm in file order).
- `--no-commit` leaves the tree for you to commit; without it the arm commits.
- `$HGI_RUNS` sets the runs directory. **For a pilot or calibration, point it at
  a scratch dir** so a throwaway run never lands in `runs/`:
  ```
  HGI_RUNS=/tmp/scratch/runs WANDB_ENTITY=slavazinevich-worldvue \
    uv run hgi experiment run experiments/<x>.toml --arm <arm> --no-commit
  ```

## Concurrency — the 429 ceiling forces sequential arms

W&B Inference rate-limits past roughly **12–30 concurrent requests**, and a
single detached arm already fans out internally (its `concurrency`, ~4–6). So:

- **Never run multiple arms concurrently.** Chain them: `... --arm a && ... --arm
  b && ... --arm c`. A sweep of candidates is one chained command, sequential.
- A multi-arm `run` (no `--arm`) executes arms in order; that is fine. What trips
  429s is launching separate concurrent `run` processes, or an old runner that
  drew detached arms alongside attached ones.

## Verifying a role prompt on a model (no full run)

Before spending a run on a roster, check the role reads and fills its slot:

```
uv run hgi roles try <request> --store <an arm store> --out /tmp/replies
```

It copies the store, sends the real request to the role's backend (set
`HGI_MODEL_ID` to target a specific model, e.g. the teacher), and prints how the
reply parsed and any floor refusal. Role prompts declare a `priced_for:`
frontmatter line (`hgi/roles/*.md`); `hgi lint` **warns** (does not fail) when a
role runs on a model not listed there — restamp the line to quiet it.

## reasoning-core: the generator stack and the shell preflight

- Generating or re-pinning reasoning-core instances (only for `hgi suite fetch`,
  not to run a pinned experiment) needs the generator stack:
  ```
  uv pip install 'reasoning_core==0.5.0' gramforge greenery faker nltk exrex
  ```
- The **shell tool the model drives must import `nltk` and `regex`** (grammar
  membership is verified there). `run_arm` preflights this before pass 1 via each
  family's `requires`; the venv on PATH satisfies it. If the shell's `python3`
  is the system one, every cfg row fails on the missing import — the classic
  confounded reasoning-core run.

## Reading a run back

- `arm.json` holds `curve` (pass rate per pass) and `health` (per-pass retrieval
  reach, tool-error counts, draft dispositions — the mid-run diagnostics). It
  also carries an `error` field when a pass failed and the arm stopped early
  (see the resilience note below): a finished `arm.json` with an `error` is a
  graceful partial run, not a crash.
- `uv run hgi experiment report experiments/<x>.toml` and `... evolution ...`
  render the tables; `... report <arm-dir>` reads one arm back.
- For a per-generator or per-lesson split beyond the aggregate, read the
  session evaluation rows (`<store>/store/sessions/S-*.json`) and split by task
  id, using `hgi.index.row_passed` for the pass verdict — the aggregate `curve`
  can hide a split between task kinds.

## Monitoring a live run

An attached arm runs its passes to stdout as it goes; a long run (a full stream
plus consolidations on a strong teacher) takes many minutes, so watch it rather
than block on it. Run to a log and grep the log for the events that matter:

```
WANDB_ENTITY=slavazinevich-worldvue HGI_WEAVE_PROJECT=hgi-experiments \
  uv run hgi experiment run experiments/<x>.toml --arm <arm> > run.log 2>&1 &

# the lines worth a notification (a Monitor grep, or `tail -f run.log | grep -E`):
tail -n +1 -f run.log | grep -E --line-buffered \
  "attached: task_pass_rate=|Consolidate K-|admitted|nominated .*→|retry [0-9]|stopping after|Traceback|429|Flush timeout"
```

What the signals mean:
- **`attached: task_pass_rate=`** — a pass closed; its first-sight rate. A hard
  family sits well under 1.0 (text2sql ~0.3–0.5); a rate stuck at 1.0 is
  saturation — the run will mint no observations to consolidate (the
  reasoning-core trap, carry-forward items 66–69).
- **`Consolidate K-… admitted …`** — a backward pass ran; what it admitted.
- **`retry N/2`** — a step hit a transient (a Weave flush/pairing timeout, a
  429) and is retrying; the loop self-heals these (below). Occasional retries
  are normal; a storm of them means the endpoint is congested — let the arm
  finish alone, don't add load.
- **`… stopping after N completed pass(es)`** — a pass failed past its retries
  and the arm finalized *gracefully* (the completed passes are committed, the
  cause is in `arm.json`'s `error`). Not a crash; read the error and decide
  whether to rerun.

**Resilience the runner now has** (so a bad reply from the model or a Weave
hiccup does not abort a whole arm, carry-forward item 34): a None/malformed
Weave evaluation summary is rebuilt from the per-row scores; a garbled role
reply at an "empty is legal" site (classify, a lens, dispose) reads as the empty
answer; the flaky `evaluate` step is retried; and a pass that still fails stops
the arm gracefully instead of raising. A `Traceback` in the log is therefore a
real bug to fix, not an expected transient.

## Sanity-checking an arm's observations and decisions

The curve says whether the arm learned; it does not say whether the *loop* did
the right thing. After (or during) a run, read the store's own records with the
inspector in this skill dir — it reads only committed JSON, so it is safe to run
while the arm is still going:

```
.venv/bin/python .claude/skills/experiment-runner/inspect_store.py runs/<exp>/<arm> [--full]
```

It prints the sessions (per-pass rate, the observations each filed, what each
consulted), every observation (`turned_on`/`happened`, flagging the exogenous
and no-world-fact ones), the admitted decisions (with their latch terms), and
each consolidation's nominations *with their outcomes* (admitted /
refused-by-floor / declined / dismissed / moot-retired). The four things to
check, and what a sound answer looks like:

1. **Failed tasks mint observations.** Every failed row should elicit at least
   one observation (the SESSIONS block: a pass at rate 0.5 over six tasks should
   show ~3 in `filed`). A failed row that mints none files a `failure-unelicited`
   marker instead — a silent recall-floor miss to note.
2. **Observations state the task's world-fact, not an exogenous symptom.** Good:
   "used EXISTS where every transaction had to match", "missing GROUP BY". Drift
   (flagged `⚠ EXOGENOUS`): "exceeded the call budget", "no rule was consulted",
   anything naming a scorer or a store record (carry-forward items 40, 48, 66).
   A few are expected; a majority means the close lens is reading the symptom,
   not the world.
3. **The obs→decision pipeline accepts/rejects for the right reason.** A group
   below the two-distinct-session independence bar should be *refused by the
   floor* (not admitted) — the first consolidation usually admits nothing
   because no shape has recurred across two batches yet. A group at the bar
   whose evidence is sound should be *admitted*; an all-self-referential group
   should be *dismissed*. Read the nomination outcomes and check the reason
   matches the evidence.
4. **The mints make sense and will retrieve.** Read each admitted decision's
   text against the family's world, and check its `latch_terms`: a decision
   latched only on generic tool terms (`tool-budget`, `task-planning`) rather
   than the task's own hook will not retrieve on a later matching task — the
   retrieval miss of carry-forward item 39/49.
