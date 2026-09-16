# Carry-forward

Future-facing working notes: where the build stands, the work left for the full
implementation, and housekeeping. The decisions taken along the way — each with
why it may be right and why it may not — live in `decision-log.md`, so this file
stays a to-do surface rather than a record of what is already settled.

State of the build as of 2026-09-13, after the world run, the stream run, the
review pass, the instruments pass (the true-miss floor, the precision slot, the
second retirement key, anchor resolution, the late steer sweep, the antichain
flag and the seeded controls) and the stream pass (lessons, the curriculum,
the stream runner and the evolution log), with the work left for the full
implementation.

## Where it stands

- Slices 0–3 of spec § 13 ship with their acceptance tests green
  (`uv run pytest`, 263 tests). Slice 4 ships the dashboard, the analyst
  mirror and the retirement leg; the rule tier and the grown floor do not
  exist because the roster is decisions only. Slice 6(e) — split and fold
  as executed operators — ships, with the other backward-pass legs that
  were nominators without a consumer: deferral latches, propagation over
  wiring latches, the structural-zero audit and the edit rungs, genesis
  anchoring, and vocabulary growth (README, *The backward pass*). Slice 5 (the demo) has run on
  the repository store and is recorded in the README's acceptance table.
- The suite is composed from families under a fault profile (README, *The
  world*): `genesis` (6), `conventions` (10), `mbpp` (257), `tables` (100),
  `api` (100), `transfer` (6, the `conventions` conventions re-dressed in
  different clothes; `experiments/transfer.toml`). `experiments/world.toml` samples twelve of each and faults
  the first two HTTP calls. Its `120b-attached` arm ran to completion
  (README, *The world on gpt-oss-120b*): 0.81 0.73 0.75 0.90 0.83 0.83,
  six decisions admitted over three consolidations — one by adopting the
  pass's own proposal — three retired moot, four fires discharged, 31 of 60
  observations still open. The detached arm was stopped in its first pass;
  pass 1 of the attached arm is the no-store draw. The arm store is under
  `runs/world/120b-attached/` on this machine. The `20b-attached` and
  `split-roles` arms have not run.
- The role contracts on `openai/gpt-oss-120b`: every request — classify,
  guard, lens, dispose, propose, coding, nominate, attack, verdict, credit,
  currency — has been read back through `hgi roles try` and parses; every
  role prompt is priced for it. The drafting requests answer with a sketch
  (decision 21); the reply logs of the tries are ephemeral (scratch), the
  world run's log is not kept either — `HGI_REPLY_LOG` recreates one.
- The review pass (doctrine v2, §§ 1–9, 13, 14, 16 read against this
  roster) landed as decisions 42–52 below: the noise filter, the examiner
  fan, role separation on every species, consumers for the pending
  contradictions and the recall probes, the lens lifecycle, attacker
  precision, revision routing, the port miss stream, and the small floors.
  The new requests — `triage`, `ports`, the `lens`-bearing `attack` and
  `currency` — have been read back on the stub only; their reply shapes
  are not yet priced for `openai/gpt-oss-120b` (see item 18).
- The instruments pass landed as decisions 53–59 below: the matrix's
  true-miss cell counts rows, the precision slot signature is live, a record
  never considered across a full window reaches the adjudicator, a
  counterfactual's anchor must resolve, a late note is swept at the next
  close, the antichain is flagged on the plan, and the examiner fan and the
  blind coder have seeded-positive controls. Every one is proven on the stub;
  none has been run on `store/` or read back on a real model (items 8, 18,
  23, 24).
- `experiments/baseline.toml` (the six genesis tasks, one 502) is saturated
  for gpt-oss-120b: 1.00 on every pass of both arms. Its three
  consolidations wrote one file, K-0001, three times (the id-minting bug,
  fixed in this build); the after-pass-2 and after-pass-4 records survive
  only in that arm repository's history.
- `experiments/model-sweep.toml` and `cadence.toml` are written and have
  not been run; `probe.toml` ran three passes and was stopped once its
  reply log had been read.
- The stream pass (decisions 60–65 below): `suite/lessons.py` names the
  seven lessons with their tiers and derives the naive outcome and the
  symptom; `suite/families/curriculum.py` generates 84 tasks; `suite/stream.py`
  deals a pool into batches; `hgi experiment` runs a `[stream]` arm (a new
  batch every pass, revisit passes, detached draws on their own batches)
  and `hgi/evolution.py` derives the log. `tests/test_stream.py` proves
  every clothing fails naively and passes when known within budget, the
  deal, the symptom rules and the stub smoke (351 tests green).
  `experiments/stream.toml` has run (item 25; README, *The stream on
  gpt-oss-120b*; `experiments/results/stream/`): the plain pool did not
  separate the arms, the strict pool did on one lesson and lost it on the
  rows the record overshot onto; `stream-probe.toml` was the endpoint check
  that preceded it.
- Weave: traces, evaluations, attributes, feedback → steer, and the mirror
  are verified live in `slavazinevich-worldvue/hgi-dev` and used in
  `slavazinevich-worldvue/hgi` and `hgi-experiments`.
- The reasoning-core and text2sql streams have run on a real model with the
  roles split (`experiments/reasoning-core.toml`, `experiments/text2sql.toml`;
  decision 96 below): the forward pass on the actor and every other role on
  `deepseek-ai/DeepSeek-V4-Pro`. As of 2026-09-13 mid-afternoon the attached
  and strict arms and the text2sql ablations are done, the 20b arms and the
  reasoning-core ablations still running; the stores are under
  `runs/reasoning-core/` and `runs/text2sql/`, the logs beside them. Neither
  pool separated the arms on pass rate: reasoning-core because the budget
  fails no task (item 47) and its shell lacked `nltk` (item 53), text2sql
  because the store admitted nothing about the schema (items 48–50) — the detached text2sql arm matched the attached
  arm on seven of its eight first-sight batches and was one row under on
  the eighth. The results files and the README section wait on the last
  wave.

## Leftover work for the full implementation

1. **The belief store** (spec § 4.2, § 6, § 8.5). Records, the per-pass
   prediction at close (step 5), the reference at entry, settlement through
   dispositive fires, the status projection at boot (step 6), the
   calibration table, the belief-watch lens (spec Appendix A.3's L-0009;
   L-0005 to L-0008 are the examiner fan). The watch evaluator and fire emission in
   `hgi/evaluate.py` already run over any record kind that exposes revisit
   latches, so beliefs plug into `index.triggers` and `emit_fires` as-is.
2. **The rule store** (§ 6.4, § 10.10). Rule records with the hand-authored
   adoption register, enrollment on observed non-propagation, the rule index
   that leads with the residue, demotion on applied ÷ considered, coverage
   migration, and the ladder rungs `adoption-row` and `rule-enrollment` as
   executed operators. `registry/ports.json` needs the rule declarations.
3. **The world, next.** The transfer half now ships: `suite/families/transfer.py`
   re-dresses three of the `conventions` conventions in different clothes —
   the no-trailing-newline files under new names (`part-*.tsv`, `chunk_*.dat`),
   the paging API on a different surface (`/records`, `/accounts`), the `/v2`
   move on different endpoints (`/account/42`, `/health`) — reusing
   `conventions`' `_no_newline` and `_naive_count` so the convention is shared
   and only the clothes differ. `experiments/transfer.toml` composes it beside
   `genesis`, `conventions` and `api` under the world's two-call fault profile,
   so a record admitted while scoring a convention on its source family is
   scored again on the same convention re-dressed. `tests/test_transfer.py`
   proves each convention fails naively and passes when known, that the
   transfer tasks' work-shape terms are a subset of `conventions`' while their
   file names and API paths are disjoint from it, and that the paged and moved
   routes behave. What the transfer half still leaves undone: the CSV-quoted-comma
   and byte-order-mark conventions are **not** yet re-dressed (only the three
   named ones are), and the transfer is proven structurally offline — no
   real-model arm has run to show the attached curve holding on `transfer`
   where a path-memorising record would break. What grades breadth-not-transfer
   remains: `nestful` (multi-step tool composition with a scalar gold) and a
   shell family from `InterCode-Corrections` were surveyed and, per the item,
   deliberately not transcribed. The `tables`/`api` tolerance (1% relative) is
   lenient on large totals, and `transfer`'s paged answers are exact integers
   so that caveat does not touch it. MBPP and TableBench are in every model's
   pretraining; absolute scores are inflated, the arm-against-arm comparison is
   not.
4. **The lenses on the real model.** L-0002 (the boot lens for unreached
   records) answers "no hook reached" for every task on an empty store;
   L-0003 (what the pass made false) names tasks and call URIs where it
   must name a record id, so nothing files from it. Both now have consumers
   (decisions 45 and 46): L-0002's probes are the brief's `recall` rows and
   nominate a hook-edit, L-0003's pending entries reach the adjudicator at
   the next consolidation. What is still unverified is the *content* on a
   real model — whether a probe names the right record, whether a
   contradiction names a premise — and the lens review will retire either
   lens through the genesis-deadline door if nothing it produces is ever
   consumed, which on the world run's pattern (nothing filed from L-0003)
   is the likely outcome for L-0003.
5. **TypeSafe System1.** `hgi/coder.py` assumes an OpenAI-compatible surface
   behind `TYPESAFE_BASE_URL`; the real API shape is unverified (waitlist as
   of 2026-09-12). The role is the invariant; only the adapter changes.
6. **ARIA.** The programmatic surface is now wired: `hgi consolidate
   --analyst-report <uri>` resolves the URI through `hgi.mirror.read_report`
   and the backward pass reads the report as the consolidation brief's
   primary input (`consolidate.consolidation_brief` → `analyst_brief`),
   replacing `build_brief`'s local derivation of the nominator's rows; the
   analyst's coding is stamped onto the open observations exactly where the
   local grouping would write it. A URI that resolves to no machine-readable
   report — an interactive chat report recorded only as provenance, or a
   Weave ref that cannot be fetched — falls back to the local derivation, so
   the interactive path is unchanged and the URI is still recorded. What is
   *not* here: nothing yet **produces** an ARIA report programmatically —
   `read_report` reads a Weave ref or a JSON file (a hand-exported or offline
   report), and no code publishes the brief as a fetchable object, so a live
   run still drafts the report interactively and records its URI. The report
   is trusted whole: a field it omits is empty, not re-derived per-field, and
   the score facts, accepted bodies, proposals and owed fires stay the
   store's (the analyst never authors a record or a fact). `read_report`'s
   Weave branch is offline-untested (guarded by try/except); the file and
   None branches are covered in `tests/test_analyst.py`.
7. **Split and fold nominations on a real model.** The operators execute
   (`tests/test_lineage_ops.py`); the stub's leaves share the parent's payload
   with the hook narrowed per sub-shape, which is a hook-edit wearing a
   split's lineage. A real consolidator drafts distinct leaf payloads; the
   `nominate` request carries the whole body of every record `fusion` or
   `convergence` names, and neither row has yet appeared on a real-model
   arm.
8. ~~**The lens battery** (§ 9.2, slice 6a): decoy rejection scored in Weave;
   `LensTelemetry` fields are all `design-stage`.~~
   *Mechanism done (this build); the live Weave scoring is a run.*
   `hgi/lens_battery.py` plants two decoys and two genuine signals per close
   lens (L-0003, L-0004) and scores decoy rejection as a traced
   `weave.Evaluation` (`hgi lens-battery`); `telemetry_from` computes
   `decoy_rejection` and `answer_variance` and `populate_telemetry` writes
   them onto `registry/lenses.json`, off `design-stage`
   (`tests/test_lens_battery.py`). The seeded-positive controls ship beside it
   (decision 59): the examiner control scores each examiner lens's landing on
   a planted fault of its class and its non-landing on a plausible draft, onto
   the same register; the coder control scores the blind coder's term on a
   known shape and its escape on a misfit, to `index/controls.json`. Left for
   a run: with `HGI_WEAVE_PROJECT` and the real model as the backend, confirm
   the `lens-battery-v1/*` scorer series appear in Weave with a non-null run
   URI for all three evaluations, and commit the demonstration store's
   real-model telemetry — the committed `store/registry/lenses.json` is
   deliberately left at `design-stage` and no `controls.json` is committed,
   because on the stub every control passes by the stub's own keyword rules
   (verified end to end on a scratch copy of `store/`: 1.00 on every axis).
9. **The demonstration store's seven articles are still unanchored.** The
   anchoring review exists and runs at every consolidation, and the stub
   anchors all seven from the demo's own ledgers (`tests/test_genesis.py`),
   but `store/` has not been consolidated since the review shipped: a
   `hgi consolidate --force` on it with no `HGI_WEAVE_PROJECT` would leave
   untraced ledger entries beside the traced demonstration's, so the next
   consolidation is left to a traced run. Until then the lint's seven
   `genesis-anchor` warnings stand.
10. **Genesis term retirement.** Appendix A.2 retires a work-shape term
    unused across three consolidation passes; nothing does. A retired term
    still parses on the records that carry it, so retirement is a register
    mark (`retired: <date>`) the hook index skips, not a removal.
11. **Propagation's `re-derive` act** has no derived field to recompute in
    a decisions-only roster; every wiring latch is written with `check`.
    The rule tier's adoption cells and a belief's evidence state are the
    fields `re-derive` is for.
12. ~~**Escape recurrence counts only the sessions' work-shape escapes.**~~
    *Done (this build).* `reviews.escape_events` reads an `other(<what>)`
    wherever its closed vocabulary is kept — a work-shape on the pass, a
    key-space on the latch, a `<species>-verdict` on the ledger entry — and
    `escape_clusters` counts those occasions the same way it counted
    sessions. `reviews.vocabulary` runs for every reviewable vocabulary by
    default (decision 40; `tests/test_escape_vocabularies.py`). Left: the
    verdict source reads a species-verdict off the ledger entry but not an
    `adjudicator-verdict` escape off a decision's admission (none is written
    today); a latch-key-space cluster keys on `record#index`, its occasion,
    not on the record's admitting session.
13. **The pass's own proposals** (close step 6) parse and file, and a
    consolidation adopts one whose lesson a ratified group earns; the stub
    adopts (`tests/test_proposals.py`), and the real model may draft its own.
14. **Re-authoring on a re-price — mechanized; the text's quality is
    unverified.** The `reauthor` role and `hgi price --reauthor` ship: the
    role rewrites each conditioning field (a lens's angle, an article, a
    decision's sentence, each with its counterfactual) against the new model,
    and the path stamps the text and the authoring together (`authored_for`
    null), so `model-pricing` clears because the text followed the model —
    where `--restamp` (stamp-only, warning stands) is unchanged. The
    mechanism is proven offline against the stub (`tests/test_price.py`): a
    re-author moves every field, agrees the stamp, and quiets the floor; a
    restamp leaves the warning a later re-author clears. What only a real
    model can verify is the *content*: the stub marks the conditioning it
    stands in for (`[for <model>] …`) rather than rewriting for the model,
    so whether a re-authored angle or article actually conditions the new
    model better than the old text is the same unverified drafting contract
    as item 4 (the lenses on the real model) and needs a live run to read
    back through `HGI_REPLY_LOG`. `--reauthor` has not been run on `store/`;
    the Housekeeping note's `--restamp`-or-`genesis --force` choice now has a
    third option that keeps the store and moves the text.
15. ~~**`hgi experiment`'s genesis message names no article ids** (`Genesis for
    <exp>/<arm>: priced for …`), so `hgi lineage C-0003` finds no admitting
    commit in an arm's store.~~ *Done (this build).* The arm's genesis commit
    subject now appends the constitution range (`, constitution
    C-0001..C-0007`, endpoints derived from `store.articles()`, decision 28),
    so `hgi lineage <C-id>` resolves an admitting commit inside an arm's store
    as it does in the demonstration store (`hgi/experiment.py._genesis_message`;
    `tests/test_experiment.py`).
16. ~~**The watch a model sketches** is sometimes a watch on success.~~
    *Done (this build).* `drafting.fires_on_success` reads a revisit watch's
    direction against the oracle's convention (a higher-is-better score in
    `[0, 1]`, `1.0` ideal): a predicate the ideal satisfies but a failing
    score does not fires when the record works. The examiner lands a
    `warrant:watch-direction` claim on such a watch and the adjudicator
    declines it (decision 41; the examiner and adjudicator prompts carry the
    same check; `tests/test_watch_direction.py`).
17. **Executing model-written code.** `mbpp` tasks run `python3 tests.py`
    over a file the model wrote, on this machine, with a timeout and
    nothing else; the shell tool already ran model commands the same way.
    A sandbox is a tool-layer concern, not the suite's.

18. **The new role requests are unpriced for the real model.** `triage`
    (the noise filter), `ports` (the port miss stream), the `lens`-bearing
    `attack` (one angle per call), the `lens`-, `finding`- and
    `domain_entered`-bearing `currency` requests, the `precision` row on
    `nominate` and the `co_applying` content on `dispose` parse on the stub
    and have not been read back through `hgi roles try` on
    `openai/gpt-oss-120b`; `role-pricing` will not warn,
    because the prompt files still list the model. A live run's first
    consolidation now costs four examiner calls per draft instead of one,
    plus one triage call per group at the bar.
19. **The `article` rung has no operator.** The ladder's top rung — a
    constitution article with a forced eviction — is carried as a decision
    like the rule rungs (decision 42), so a lesson meant for every pass is
    only consulted on a matching hook. The constitution is in this roster,
    so the operator is in scope: a nomination carrying the article, its counterfactual and
    the article it evicts, through attack and verdict, written with the
    eviction in one commit under the cap. It needs a draft kind beside the
    decision draft, which the queue and the committer currently assume.
20. **No collision species writer.** The species is declared with its
    verdict vocabulary and nothing writes it; the doctrine's canonical
    instance — a test author deriving expectations blind from committed
    artifacts — has no analogue in the loop yet. The blind coder is coded as
    `coding`, which is its own species.
21. ~~**The antichain is displayed as a list, not as a conflict.**~~ *Done
    (this build; decision 58).* `boot.co_applying` reads the consulted records
    whose hooks share every term with no lineage edge between them; the plan
    prints them on one `co-applying:` line and the dispose request carries the
    same reading. Still left: the leaf lattice that would give them regions is
    a split nomination only, and a real pass's disposition notes have not been
    read to see whether they say which applied where.
22. **Yield per steer is not instrumented.** The matrix counts steers and
    the credit table attributes them; nothing reads how much each steer
    moved — the quantity the doctrine says to maximize, against steer count,
    which it says never to target.
23. **The precision slot on a real model is unverified.** The stub's
    disposition note names the pass's tasks after a fixed marker and the
    stub consolidator reads them back as `not_this` entries; a real pass's
    note is prose ("which rows it bore on, or why it did not") and a real
    consolidator must turn it into a presentation exclusion — the prompt says
    so, no reply has been read. And the stub's guard matches `not_this` by
    substring over the prompts, so a task-name exclusion excludes nothing at
    the stub's guard: on the stub the successor is proven admitted, not
    proven quieter.
24. **The true-miss join reads the row's call, or the task name in the
    noticing when the row carries none.** A pass whose lens files an
    observation anchored on a path alone and naming no task hides its failed
    row from the cell — the count stays a floor, but one that a lens's
    anchoring habit can lower. The late steer sweep re-reads every earlier
    closed session's calls at every close: one trace-store query per earlier
    session per close, which on a long run is a cost the channel's
    best-effort clause hides rather than prices.
25. **The stream run.** `experiments/stream.toml` ran on 2026-09-13 (README,
    *The stream on gpt-oss-120b*; `experiments/results/stream/`): every arm,
    from the tree at 67c9ff0 with the close fix 1707b72, the detached arms
    redrawn alone afterwards, the strict attached arm rerun from scratch
    after the close bug stopped its first run at pass 7. What it answered:
    ten batches do give a lesson enough same-shaped observations to group —
    the coder shaped the moved-v2 and token-route observations alike in
    every 120b arm and the groups reached the bar from the first
    consolidation — and the drafts then died at the contract's floors and
    the examiner's attacks in the plain arm (11 refused at parse, 5
    declined, 1 admitted, a record that names no lesson) while the strict
    arm admitted the fused `/v2`-plus-token record at its first
    consolidation and five more after. The strict pool separated the arms
    on one lesson (moved-v2: 0.58 attached, 0.00 detached, the naive shape
    3/3 before the record and 0/9 after) and lost the gain on the rows the
    record overshot onto (paged-api 0.08 against 0.75; token-route blocked
    to zero calls by D-0002), for a tie over the stream. The plain pool did
    not separate (0.46 against 0.54) and its no-store passes differ from the
    detached draws of the same batches by up to 0.37, the noise floor of
    eight tasks on this endpoint. The probe's concern — observations naming
    the task and the number but not the convention — did not recur: the
    stream's closes named the route and the `/v2` fix. What did not happen:
    footer-row and trailing-newline earned no record on any arm, and the
    one record drafted from the newline observations fired on file rows
    and left them failing the naive way. The first strict run and its
    rerun met the same batches with the same model at temperature 0 and
    consolidated differently (the first refused both lesson drafts at
    parse after pass 2 and declined the versioning draft after pass 4; the
    rerun admitted the fused record after pass 2): admission is a draw, and
    the first run's store is gone (`--force` discards it) — its two
    consolidations survive only in this note. The evidence for the
    reject-vs-amend and admission-slack changes is item 32 and the task
    spun from it.
26. **Retention and forgetting beyond one revisit.** `revisit` re-meets
    whole batches after the stream; the modes a continual-agent benchmark
    scores (AgentMemoryBench: improvement, retention, forgetting,
    generalization, conflict) would take a revisit at fixed checkpoints
    during the stream and a held-out probe set met with the store and never
    closed on — the `evaluate --detached` path has no store, and no probe
    mode (boot + evaluate, no close) exists yet.
27. **A mixed stream.** The stream's pool can name any families
    (`families = ["curriculum", "tables"]`; a task with no lesson is dealt
    under its family), but no shipped experiment mixes lesson tasks with
    distractors, so the loop's grouping has not been tried where most
    failures carry no lesson.
28. **The mention heuristic — replaced by the firing signal.** `evolution`
    used to drive the lesson series off a keyword match over a record's
    decision, latch and context, so the headline reported "a record whose
    text uses the lesson's words," not "a record that fired and helped." The
    join that replaces it is now read: `_applied_join` in `hgi/evolution.py`
    reads `rows[].applied` (the record ids the loop actually applied on that
    row) against the row's `symptom`, so per pass and per lesson the log
    carries which records fired and how the rows they fired on turned out.
    The series pivots on `first_applied_pass` (first stream pass a record
    fired on the lesson's rows) instead of `first_mention_pass`; the
    naive-before/after split turns on it; the arm and experiment tables gain
    an `applied → outcome` column (`passed/tasks (✓ N W)` over the fired-on
    rows) and the records tables show `fired` (passed/rows on which lessons)
    instead of pivoting on `mentions`. The keyword `mentions` field is kept
    and still logged, but is no longer the driving signal (docstring and the
    report Reading legend say so). Applied ids are filtered to the arm's own
    accepted records at row construction, so a retrofit's rows — which carry
    the *source* arm's applied ids — read as unfired, matching "nothing was
    in context." This surfaces what the text2sql run hid: on `120b-attached`
    D-0002 fires from pass 7 on `text2sql` and passes only 1 of 3 fired-on
    rows (item 50's latch-widening supersession), while D-0001/D-0003/D-0004
    were admitted but `fired never` (item 49's vacuous decisions) — none of
    which was readable when the column pivoted on keyword mention (which
    never matched, since the text2sql lesson keys are not in
    `suite.lessons.LESSONS`). Tests in `tests/test_stream.py`
    (`test_the_lesson_series_pivots_on_firing_not_on_keyword_mention`,
    `test_an_applied_id_absent_from_every_row_leaves_the_series_unfired`).
    *Interaction:* the inline `in_context` computation another agent extracts
    for `experiment.progress()` is unchanged — its logic and signature were
    not touched.
30. **The economy run.** `experiments/economy.toml` — 120b attached and
    detached on the plain pool under a different deal (seed 2) — is the
    stream graded on quality (`solution_economy`, `turn_economy`,
    `method_transfer`); it had not run when this was written, and no real
    model has yet scored the three series (the stub's smoke scores them
    zero and unevaluable on its failed rows). The two runs are additive:
    the stream run's evolution log already shows `economy`, derived from
    the counts, and only `turns` and `transfer` need the new envelope.
    It has since run on `openai/gpt-oss-120b` (2026-09-13, brought over
    from `claude/nervous-rubin-e8e759`; `experiments/results/economy/`):
    pass rate did not separate (38/80 attached against 42/80 detached) and
    quality could not have, because no record was in context on any
    first-sight pass — D-0001 sat behind a guard the boot failed and went
    moot, D-0002's consultation latch was scoped to a work-shape term
    (`test-failure-triage`) so the boot index matched it to nothing,
    D-0003 landed after pass 10 and failed both moved-v2 rows it was
    applied to. The run's own findings — the retrieval miss, the close
    naming scores not world-facts, the parse refusals and the malformed
    tool call — are items 39–42 below and are the evidence for gap fixes
    beyond the admittance bar.
31. **Quality beyond the shell lessons.** `method_transfer` replays a
    shell command, so it grades the three shell lessons only; the API
    lessons' method is the walk and transfers trivially, and `bom` has no
    budget so no economy floor. A hidden-assert variant of `mbpp` (one
    assert shown, two held out) with a lint or complexity column would be
    the lesson-free family with a graded quality metric, for a mixed
    stream; not built.
38. **The review's reject-vs-amend change is proven on the stub only.**
    Decisions 73–75 — independence and watch direction read by the code,
    a landed abstraction claim amended through one promote re-ask, a
    decline standing only on an upheld premise kill — are proven by the
    stub's paths and the tests (`tests/test_mechanical_review.py`,
    `tests/test_abstraction_amend.py`, `tests/test_decline_override.py`)
    and by no real-model run. The evidence they answer is the stream run's
    ledgers (`runs/stream/*/store/ledger/ledger.jsonl`, 2026-09-13): three
    lesson drafts on gpt-oss-120b — endpoint versioning, the moved-v2
    route, after passes 2 and 6 of the attached arm and in the strict arm —
    were declined on abstraction and watch direction alone and dropped.
    The test of whether the run now admits the moved-v2 record is a rerun
    of `experiments/stream.toml` arm `120b-attached`; not run.
29. **Public continual-learning suites.** SWE-Bench-CL, AgentMemoryBench,
    AgentCL and the procedural-memory-retrieval benchmark were surveyed
    (2026-09-13) as the scale-up path for the stream shape — repository
    feature work with recurring conventions — and not transcribed: each
    needs a repository-scale agent and a run measured in hours, where the
    curriculum measures the mechanism in minutes. The curriculum's lessons
    are the conventions of a small world; the claim that the shape carries
    to a codebase's conventions is untested.

32. **Admission slack — notes for easing the floors that refused every
    lesson draft of the stream run.** The stream run (item 25) filed an
    observation on every failed row, the blind coder shaped same-lesson
    observations alike and groups reached the two-session bar, and the
    consolidator nominated the right lessons (endpoint versioning, auth,
    budget, csv-header); then every gpt-oss-120b draft died before or at
    adjudication and nothing was admitted. Four gates did it, in order of
    cost, each with the slack proposed and what it risks:
    - **`not_this` must be non-empty** (`hgi/drafting.py`, `Sketch.not_this:
      Field(min_length=1)`, refused at parse; and again at the write-time
      floor, `hgi/lint.py` complement-law, "consultation latch declares no
      not-this exclusions", which refuses a draft the adjudicator admitted).
      Seven of the run's nine 120b new-decision drafts were refused here.
      The exclusion exists to recover precision for a hook biased broad —
      but a false fire costs one disposition and is telemetry (the
      consolidator's own register says so), and the precision leg
      (`counterfactual-edit`, grow `not_this` from `not_applicable`
      notes) exists to add exclusions after the record has fired wrongly.
      Gating admission on an exclusion the drafter has not yet seen the
      need for gates helpfulness behind compliance. *Slack:* default
      `not_this` to `[]` in the sketch (`Field(default_factory=list)`),
      drop the lint `fail` to a `warn` ("declares no exclusions; precision
      review will grow them"), and leave the precision leg as the place
      exclusions come from. *Risk:* a record with no exclusion fires on
      every presentation its terms match; the retirement leg
      (`applied_over_considered_below` 0.1 over 6 passes) retires one that
      never applies, so the cost is bounded by the window. Tests:
      `tests/test_roles.py::sketch_of` (empty `not_this` currently refused),
      the complement-law cases in `tests/test_lint*.py`; `test_precision.py`
      is unaffected (it grows a non-empty list).
    - **An edit rung must supersede exactly one record**
      (`hgi/consolidate.py`, `edited_body`). The 120b consolidator chose
      `counterfactual-edit` and `hook-edit` on an empty store (K-0002 of
      `120b-attached`, K-0003 of `20b-attached` with two records it did not
      name), so the draft was refused for naming no record. *Slack:* when
      `supersedes` is empty and the store holds no record the rung could
      edit, displace the nomination to `new-decision` the way a rung with
      no operator is displaced (`displacement`), keeping `rung_why`;
      when records exist and none is named, refuse as now. *Risk:* a
      displaced edit is drafted as a new decision from the same evidence,
      which is the right outcome on an empty store and a duplicate on a
      full one — hence the guard. Test: a stub nomination on an edit rung
      with an empty store lands as a new decision.
    - **The abstraction attack lands on a payload that names instances**
      (lens L-0007; the adjudicator declined H-0004 of `120b-attached` and
      H-0008 of `120b-strict` on it). The draft said "use /v2/zones/90,
      /v2/projects/82" instead of "a 410 that names a versioned route is the
      route moved; call the named route". The lens is right that the
      instance does not transfer — but the decline drops the draft, and
      the adjudicator has `admit-amended` with an `amendment` that
      replaces the decision text (`store.admit(..., amendment=...)`) and
      never used it on this run. *Slack:* tell the adjudicator (in
      `hgi/roles/adjudicator.md`) that a landed `payload:abstraction` on
      evidence that is otherwise sound is the case for `admit-amended`
      with the promoted payload, not `decline`; or, mechanically, re-ask
      the consolidator once with the landed claim ("promote the payload;
      keep the instances as anchors") before the verdict. *Risk:* the
      adjudicator promotes past the evidence — a floating entry — which the
      genesis article on promotion names as the overshoot; the anchors
      stay, so the lint's anchor checks still bound it.
    - **The watch-direction attack** (L-0008) landed on H-0008 because the
      sketched watch (`error_cause_present == 1.0`, `task_pass_rate >= 0.9`)
      fires on success; `hgi/drafting.py` already checks a watch's
      direction against the stakes (commit 585c1be) for the stub. *Slack:*
      when the watch is wrong, drop the watch (it is optional, `watch:
      null`) rather than the draft — a decision with no revisit latch is
      admissible and the retirement leg still bounds it. *Risk:* none to
      admission; a record without a watch is re-adjudicated only by
      currency and retirement.
    What not to loosen: the independence bar (two sessions) held every
    lesson group on this run and is what makes a recurrence a recurrence;
    and the premise kill (L-0006), which landed once (H-0008, on a missing
    `/v2` route that was in fact the task's own fault injection) — that one
    is an examiner reading error, not a floor to move. The order to take
    them in is the order above: the first two are contract floors that
    refused seven drafts at parse and cost nothing to relax; the third is
    where the lesson records will come from; the fourth is a one-line
    prompt note. A rerun of `120b-attached` alone after the first two is
    the cheapest test of whether the run admits.
33. **The fusion leg did not fold restatements.** The strict arm admitted
    D-0004, D-0005 and D-0006 after pass 10, each restating D-0002 or
    D-0001 almost verbatim (a token before any request; `/v2` plus a
    token; a token before any GET), so the same lesson sits in one store
    five times and every boot carries all of them. Split and fold run on
    the lineage DAG; nothing nominates two records with no lineage between
    them and the same latch for a fold. A textual or hook-overlap nominator
    (two accepted records whose `terms` match the same presentations and
    whose payloads the coder shapes alike) is the missing consumer.
34. **Detached draws lose Weave traces.** A detached arm's passes run in
    thread copies of the runner's context (`_detached_passes`), and Weave's
    trace-batch flush in those threads failed on every pass with
    `Invalid project_id format: . Expected 'entity/project'` ("Task
    failed", 96 times per arm); the evaluations, row calls and scores were
    written with project-qualified call URIs and the log is complete, so
    the cost is some traces of the detached draws, not data. The attached
    arms, which run in the main thread, logged cleanly. Untraced; the fix
    is probably to re-enter the Weave client in each worker or to run the
    draws sequentially under a flag.
35. **Code moved under a running arm.** The arm processes loaded the tree
    at 67c9ff0 when they started; the quality commits (2b0bc96, 4880cb4)
    landed on `main` while they ran and changed the curriculum's data draw
    (decision 68) and `hgi/evolution.py`. The runner imports `evolution`
    lazily at the arm's end, so the 20b arm wrote its log with the new
    module over the old rows (economy columns as dashes) and the plain
    120b arm's end write crashed on `Task.knowing` after its last pass —
    the arm's curve and store were complete and its final commit was made
    by hand. Every log under `experiments/results/stream/` was derived
    from a worktree at 67c9ff0 plus the close fix, with `HGI_RUNS` pointing
    at the main `runs/`; `hgi experiment evolution` on `main` rebuilds
    these arms from their recorded task ids with the pool-changed warning
    and would score the rows against a pool whose data differs. Import the
    log writer eagerly with the runner, and record the tree's commit in
    `arm.json`.
36. **W&B Inference's per-user concurrency.** Five arms at once — two
    attached at six tasks each and two detached at three passes of six —
    put 429s past the client's five retries into the detached rows (6 and
    7 of 80); the attached arms at six took none. The detached arms were
    redrawn alone afterwards (decision 70). The ceiling is somewhere
    between 12 and 30 concurrent requests on `openai/gpt-oss-120b`; a
    runner that serializes detached draws behind attached arms, or reads
    the limit, would let an experiment's arms run together safely.
37. **A lens reply that drops `noticed`.** The strict arm's first run died
    at pass 7's close on an L-0004 finding with an anchor and no `noticed`;
    `file_observations` now skips such a finding (1707b72,
    `tests/test_close_findings.py`). Whether to refuse the reply instead
    (the finding is malformed) is the contract's question; skipping loses
    an observation the pass tried to file.
39. **A consultation latch's scope is drawn from the observation's coding,
    not the task's terms** (economy run, `claude/nervous-rubin-e8e759`).
    D-0002 was admitted for `paged-api` rows and latched on
    `test-failure-triage`, the shape the blind coder gave the observations,
    so the boot index matched it to nothing and its competence window
    closed at zero considered: a record admitted but never retrieved. The
    task's own terms (`http-tool` for every API lesson) are on the
    observation's anchor and could seed the latch's `terms`; today the
    drafter chooses them. This is the retrieval floor the admittance-bar
    raise does not touch — a higher bar admits fewer records, none of which
    fire if the latch scope does not match the task.
40. **The close files observations about its scores, not the world's
    facts** (economy run). The close reads the row's scores by series name
    and the observations say so ("the `method_transfer` check was missed",
    "did not fire a check record to verify the total"); none of the forty
    named the convention (a footer row, a missing newline, a quoted comma)
    in words the blind coder could group on, and the two silent shell
    lessons stayed at 24/24 naive in both arms. The series names should not
    reach the close's brief, and the observation request should ask for the
    world's fact the row met, not the check the row failed.
41. **Drafts refused at parse at the `hook-edit` rung** (economy run). Six
    drafts were refused across three consolidations — three because the
    hook-edit named no record to supersede (`a hook-edit supersedes exactly
    one record; got []` on an empty store), three because `not_this` came
    back empty. These are gates 2 and 1 of item 32 seen again on a second
    run. A repair turn (re-ask with the refusal) or a rung-specific example
    in the request would recover most of them, keeping the contract rather
    than relaxing the floor; item 32 relaxes the floor instead. Every
    refusal is on the ledger, so the count is exact.
42. **A tool call with malformed arguments loses the row** (economy run).
    In the detached arm's pass 10 the model emitted a shell call whose
    arguments string was not valid JSON; `suite/tools.py` answered with a
    *bad tool call* result, but the assistant message carrying the raw
    string went back into the history and the endpoint refused the next
    request outright (`messages[2].tool_calls[0].function.arguments must be
    a valid JSON object string`), so the model never got the turn to read
    the error and retry. The row failed `error:model-call` — a symptom that
    covers a genuine endpoint fault and the model's own malformed output
    alike. The fix is in `suite/agent.py`: replay the assistant turn with
    arguments the endpoint accepts (the raw string wrapped as a JSON
    object) so the conversation continues and the wasted turn still costs
    turn economy; and split the symptom so the two causes read apart.

**Addressed (2026-09-13).** The gaps items 32–42 name are now built and on
`main`, each as a decision below with its risk: parse floors (item 32
gates 1–2, item 41) → decision 78; the hook seeded from the task's terms
(item 39) → 79; folding restatements (item 33) → 80; the close eliciting
the world's fact (item 40) → 81; the malformed tool call (item 42, decision
76) → 82; the runner pinned and its draws serialized (items 34–36) → 83. The
recurrence graded for the adjudicator → 84 and refused observations kept in
the open pile → 85 are the further levers built on top. The shape-radius
sweep (decision 77) found τ\*=1.0 — the coder's shapes already conflate
lessons, so widening the grouping radius is not the lever and item 40's
coding fix is; no `group_observations` change was made. The coder shaping on
the convention rather than the tool — the deeper reading decision 77 exposed
— is now built and measured on the stub (decision 87): the τ=1.0 grouping
moves from impure to pure at the source. What remains untested is a rerun on
the live endpoint — whether drafts now survive to adjudication, the seeded
hook fires, the fold collapses the restatements, and the live coder
normalizes each convention onto its registered term so the pure exact-match
grouping decision 87 shows on the stub holds on `openai/gpt-oss-120b`.

43. **Click-to-open on the score curve** (dashboard pass). `mo.ui.altair_chart`
    puts its point-selection param on every layer of a layered chart and
    projects it on x and y; in the compiled view the admitted-record rule and
    label layers lose theirs (Vega-Lite warns "Cannot project a selection on
    encoding channel y", with or without a y field on them), so the frontend
    listens for `select_point_2` / `select_point_3` signals that do not exist
    and no selection reaches Python. The curve is a plain chart and the
    Passes drill-down is the dropdown. Ways out: a unit chart
    (`mark_line(point=True)`) with the rules dropped or drawn as a strip
    beneath, or an upstream fix in marimo's vega component.
44. **The Compute tab reads Weave on request only, and prices nothing**
    (dashboard pass). One filtered `get_calls` over
    `attributes.hgi.experiment` and the completions op name (about 5 s for
    the stream project's 12k calls) gives tokens and latency per arm, pass,
    role and model. No cost, because no price table exists: a per-model
    $/Mtok table in the experiment TOML would let the tab and
    `hgi experiment report` say what an arm cost. The CoreWeave seam is the
    endpoint dimension — the model id in Weave's usage summary and the
    `base_url` the experiment installed per role; CoreWeave Observe exposes
    the Prometheus paths (`/api/v1/query_range`, bearer token), so a refresh
    cell could overlay endpoint latency and throughput on the pass timeline.
    Unexercised: no CoreWeave endpoint credentials existed on 2026-09-13.
45. **The arms are traced but not mirrored into W&B runs** (dashboard pass).
    A `wandb.init(project, group=experiment, name=arm)` per arm with
    `wandb.log({"task_pass_rate": v}, step=pass)` from `run_arm`'s
    `progress()` would put the same curve on a W&B workspace beside the Weave
    evaluations, and a W&B Report could carry the experiment's story with the
    dashboard's pages linked; the other direction is `mo.iframe` of a report
    or panel share link in the Loop tab. Neither is built.

46. **The Retrofit tab reads snapshots, not the store's history** (dashboard
    pass). It charts `snapshots/after-pass-<k>.json` as the retrofit writes
    them and, on request, the original beside it through
    `hgi.retrofit.reading` (a git archive per pass of the source arm, about
    a tenth of a second for twelve). The two retrofits under
    `runs/retrofit/` were at pass 2 of 12 when this was written, so the tab
    has been seen with one snapshot only; the shape legend, the four state
    panels and the original-versus-retrofit count panels are exercised in
    code, not on a finished run. The pile chart colours shapes by first
    appearance across the snapshots, so a shape's hue is stable within an
    arm but not across arms.

47. **The reasoning-core budget fails no task, so its strict pool is not
    strict** (reasoning-core run). `suite/tools.py` refuses a shell call past
    the budget, but the task is graded on the answer alone, and a regex
    witness or a grammar member is something the actor can produce unaided
    — so `tool_budget_respected` sat at 0.00–0.75 while `task_pass_rate` was
    1.00 on the same rows, the strict arm on Qwen3.6-35B-A3B scored 0.88 at
    first sight and the lax arm 0.79, and the teacher's own second decision
    ("enforce the one-call budget") had its premise reversed a consolidation
    later on the evidence that over-budget passes go unpunished. The budget
    only reaches the economy series. For the pool to bite, the answer has to
    depend on the shell — grade only a candidate the row verified (a
    `commands` check the way `mbpp` reruns `tests.py`), or fail a row whose
    budget was exceeded outright, as `curriculum` does in effect because its
    answer needs the call — and the level-3/level-2 instances are near
    saturation for a 35B model regardless (item 88 said the 0.5 target was a
    hypothesis; it is now measured at ~0.85). The `reasoning-core` seed
    (decision 95) inherits the same ceiling.
    **Built (commits `a025dcf`, `ea23456`):** fix (b), the lower-risk one. A
    refused over-budget call now drops a sentinel (`.hgi_budget_exceeded`) in
    the working directory (`suite/tools.py`, general and inert for every family
    whose check grades data), and the reasoning-core check fails a marked row
    regardless of the answer — so `task_pass_rate` now depends on the shell
    call, not the answer alone. The gate reads no magic number: each pool gates
    at its own `shell_budget` (KNOWING + SLACK), so the strict pool fails the
    moment the repair call is refused and the lax pool only its successor;
    within-budget verified passes are unchanged. It is on by default and
    reversible via `HGI_REASONING_CORE_BUDGET_GATE=0`, which restores
    answer-only grading; no TOML change was needed because every arm wants the
    default. Not done: fix (a), the `commands`-verified candidate check, which
    stays the stronger but more invasive option. **Caveat unchanged — go/no-go
    on the rerun is a judgment call:** the gate makes the budget genuinely
    decide pass/fail, but it does not touch saturation. The level-3/level-2
    instances still sit near ~0.85 for a 35B actor, so an unaided actor that
    happens to produce a member first time passes the strict pool within its
    one call and the arms may still not separate even though the budget now
    bites. The gate is necessary for the strict pool to mean anything; it is
    not sufficient to guarantee separation. A rerun is worth it only if the
    ~0.5 first-sight band the run wants can be reached another way (a harder
    level, a longer floor) — this fix removes the confound, it does not lower
    the ceiling.
    **Hard tier added and calibrated (commits `e1ad5cf`, `18f0518`, `4fc2909`,
    `a6c7427`, `5b22eca`; 2026-09-14):** the harder level the caveat asked for.
    Difficulty was parameterized into a `Tier`
    (`suite/families/_reasoning_core.py`) and a harder tier added — regex level 5,
    cfg level 3 over an 8–14 token derivation window — with `-hard` /
    `-hard-strict` families and `experiments/reasoning-core-hard.toml`, the budget
    gate and grading unchanged. A single strict-detached calibration pilot on
    Qwen3.6-35B-A3B (no store) set the cfg level. The finding: cfg difficulty
    saturates to ~0.17 the moment it hits *either* level 3 *or* the long (10,18)
    window, and only L2-with-short-window is easy (~0.85), so L3 @ (8,14) is the
    usable middle — cfg first-sight ~0.33, regex L5 ~0.75 (L5 barely moved off
    moderate, left as is; the initial pilot's 0.46 average hid this 0.75/0.17
    split, caught by reading the per-generator rows). The *config* was calibrated,
    not the instances: the shipped hard cfg is a fresh unbiased draw at L3/(8,14),
    not the pilot's pins. A hard-tier seed
    (`experiments/seeds/reasoning-core-hard/`, commits `c4c0422`/`15960e1`) carries
    the level-independent produce-and-verify method rewritten for L5/L3, and the
    `qwen-seeded`/`qwen-strict-seeded` twins are wired. **Left:** the hard rerun is
    unrun (item 55); ~0.33 cfg is on the harder side, so watch for a floor effect
    where even the store cannot lift it.
    **Superseded — the gate is removed; the budget fails no task** (2026-09-14,
    item 56, commit pending): fix (b) is reverted. The item-56 dropped run showed
    the gate re-created the very confound it was meant to fix — it failed an actor
    that verified a *correct* answer but over-spent (O-0007 found `'12'`, re-verified,
    and the third call was refused), so every observation and both decisions were
    about budget arithmetic, not the produce-and-verify method. The reasoning-core
    check now grades the answer alone (`_answer` in `suite/families/reasoning_core.py`);
    `_gated`/`_budget_gates_pass`/`BUDGET_GATE_ENV` and the `BUDGET_SENTINEL`
    machinery in `suite/tools.py` are gone. The budget is still a real tool-call
    limit — the tool layer refuses a call past it and the economy series measures
    adherence (`tool_budget_respected`) — but it fails no task. The strict pool now
    bites *through the answer*: a wrong first candidate it cannot repair within one
    call is submitted and fails on the answer, which is a genuine method failure the
    teacher can distill. The caveat's premise ("the gate is necessary for the strict
    pool to mean anything") is retired — on the hard tier, where a first candidate is
    often wrong, the answer carries the strict/lax separation; on the near-saturated
    moderate tier the pools stay close, as they already did. Fix (a) (a
    `commands`-verified candidate check) remains unbuilt and is now unnecessary.
48. **Lens answers about the store's own machinery become observations of
    the world** (text2sql run). Seven of the attached arm's twenty-one
    observations read "no rule matched", "no store records consulted", "the
    check record should have fired" — the actor answering a close lens that
    asks which record should have fired, filed by the close as a finding —
    and the consolidator built a decision on them (D-0004/D-0007: "a
    solution must consult the store's rules before execution; a failure with
    no applicable rule is a process failure"). This is item 40 in a second
    clothing: there the observations named the scorer, here they name the
    store. The close's observation request should exclude findings whose
    subject is a store record or the loop, and the noise filter (decision 42)
    should drop a nomination whose every anchor is self-referential. Until
    then any retrofit reproduces the artifact.
    **Built:** a `self_referential(noticed, anchor)` predicate in
    `hgi/index.py` (a finding is self-referential when its anchor names a store
    *record*, or its noticing's subject is the loop's own consultation/routing
    machinery — a narrow cue set matching a *record* or *consultation* as
    subject, not the bare word "rule"/"hook"/"store"). (a) `hgi/close.py`
    `file_observations` drops a self-referential finding from a world-fact lens
    (L-0004/L-0009); the off-map coverage lens L-0010 is exempt (`OFF_MAP_LENS`)
    because its legitimate subject *is* missing coverage. (b) `hgi/consolidate.py`
    `triage` mechanically drops a group whose *every* observation is
    self-referential before the adjudicated triage, dismissing its observations
    with the consolidation as their pointer (no model call — the reading is the
    code's). **Risk:** the predicate is prose-cue-based, so a novel phrasing of
    a store-machinery finding could slip through (kept), and a world finding that
    happens to quote a loop cue with no world literal could be dropped — both are
    conservative failures (err toward keeping): a mixed noticing (a store cue
    *and* a quoted literal or comparison) is always kept, and only a group whose
    every anchor is self-referential is dropped, so one genuine world observation
    saves the group. New tests: `tests/test_self_referential.py`.
49. **The teacher abstracts a real miss into an instruction** (text2sql run).
    The anchors were right — EXISTS where every transaction had to match,
    a district column read as a client average, the 2015 unemployment
    columns for 1995 — and the decision they became was "a SQL solution must
    correctly translate the task's logical requirements" (D-0003/D-0006).
    Meanwhile the failed rows that recur across the pool — `status =
    'approved'` three times where the code is `'A'`, `frequency = 'TYDNE'`
    for `'POPLATEK TYDNE'` — became no decision at all, and the strict arm's
    D-0002 ("the final answer must be a row-returning SELECT, not an
    aggregate") misread three `COUNT(*)` questions that failed on the coded
    status as schema violations, a decision that is wrong and was in context
    when the same question failed again on the revisit. The seeded
    `schema-coded-value` term was never used; the blind coder read every miss
    as `output-schema` or `shell-tool`. Three levers, in order of leverage:
    (a) the nominate request should ask for the world's fact the row met
    (item 40's fix applies here too), and the propose sketch should be
    refused when the decision sentence names no value, column, dialect or
    command — a decision with no falsifiable content about the world is an
    instruction, and the adjudicator should decline it; (b) the coder's
    coverage question should be put to the row's `result` and `commands`,
    not to the observation prose, since the wrong literal is in the query
    text; (c) a teacher stronger than the actor did not help here — the
    contracts are priced for `gpt-oss-120b`, DeepSeek-V4-Pro parsed on every
    request but wrote the same generic drafts, so the fix is in the request,
    not the model.
    **Built (a):** `hgi/drafting.py` `names_world_content(decision, registry)` —
    a decision passes when it carries any concrete signal (a quoted literal, a
    path/route, a comparison, a call/command token, a code identifier, an
    all-caps code, or a registered work-shape mechanism term derived from the
    vocabulary), and a `Sketch` model-validator refuses one that carries none, so
    both `propose` (close) and `nominate` (consolidate) refuse a content-free
    sketch at parse. Adjudicator guidance in `hgi/roles/adjudicator.md` names the
    same class as a decline (defensive — the floor refuses it first). The
    elicitation side, per a live DeepSeek-V4-Pro teacher preflight, is in
    `hgi/roles/consolidator.md`: the drafter is told to carry the concrete
    convention token into the decision (GOOD/BAD pair) and to cite *all* the
    group's independent sessions so a real recurrence is not floor-dropped for
    under-citation — the prompt asks for exactly what the floor requires. The
    independence bar (two sessions, item 32) is untouched. **Why it will not
    over-refuse:** the predicate admits on any one signal (errs toward keeping),
    and it tracks the store's own work-shape vocabulary, so the three stub
    lessons and every existing test admit unchanged; the risk it carries is the
    mirror — a genuinely concrete decision phrased without any of these tokens
    would be refused, which is why the consolidator prompt now steers the drafter
    to include one. New tests: `tests/test_falsifiable_decision.py`.
    **Built (b):** `hgi/coder.py` `code(..., rows=...)` enriches each observation
    with its anchored row's `result` and `commands` (`coding_observations`), and
    `hgi/consolidate.py` `group_observations` builds the call→row map and passes
    it, so the blind coder reads the query text where the wrong literal lives, not
    only the noticing prose; `hgi/roles/coder.md` tells the coder to read them.
    The anchor is dropped from the payload (a resolution key, not evidence), so
    the blindness guard is unchanged. The `hgi try coding` preview builder in
    `contract.py` (owned elsewhere) still shows the base shape; only the live
    consolidation path is enriched. New tests:
    `tests/test_coder_reads_result_commands.py`.
50. **Supersession by latch widening** (text2sql run). Three of the seven
    decisions are copies of the other three whose only change is the latch
    terms — `output-schema` widened to `shell-tool, tool-budget`, and so on —
    the hook-edit rung firing because the boot classifies every text2sql
    task under the tool cues and a record keyed on a convention term never
    fired. Widening a latch to the shape every task presents makes the
    record fire on every task and mean nothing; D-0002 was in context on two
    later rows that both failed. A hook-edit that widens onto a term every
    task in the pool carries should be refused or should count as a
    retirement candidate, and the report should show `applied` against the
    row's outcome so this is visible without reading the store.
    **Built:** the refusal half. `hgi/consolidate.py` `pool_universal_terms()`
    reads the pool's declared presentations (`suite.Task.shapes`) and returns the
    work-shape terms (essentially) every task carries (>= 95%, empty for a pool
    under two tasks). `edited_body` refuses a `hook-edit` whose consultation-term
    edit *adds* any pool-universal term (`new - old` intersected with the
    universal set) — the record would fire on every task and select nothing. Only
    a genuine widening is refused: a narrowing, a broadening onto a term the whole
    pool does not carry, or keeping a universal term already present, all stand.
    The refusal surfaces as a draft-refused-at-parse nomination outcome. **Why it
    will not over-refuse:** the bar is near 1.0, so a common-but-not-universal
    term is fine, and only the newly-added terms are checked, so refining an
    already-broad hook is untouched. The report half was already shipped as item
    28 (evolution.py reports `applied → outcome` per record). New tests:
    `tests/test_latch_widening.py`.
51. **Two tasks a batch is too few** (text2sql run). With eight batches of
    two, the strict arm's rise from 0.00 to 0.50 on batch 5 was matched by
    the detached ablation on the same batch, and the lax arms differed by
    one row over sixteen. *Partly addressed:* `experiments/text2sql.toml`
    now deals the same sixteen pinned questions into **four batches of four**
    (lax) and the ten strict questions into **two batches of five** — a
    batch's first-sight rate is a fraction over four or five, not one row of
    noise — reusing the existing pool, no new data, so the change is
    reversible; the deal was verified (three lax batches carry two graded and
    two held-out, the fourth the four leftover graded; both strict batches
    five graded) and a test in `tests/test_experiment.py` pins the shape.
    *Superseded — the full expansion is built (2026-09-14, commits `34bc0cc`,
    `549323d`, `0725ebf`, `f520eb2`, `5e784ad`, `0e39655`):* the pool is now
    **all 32 `financial` questions**. The whole `financial.sqlite` is pinned —
    the `trans` table kept whole (1,056,320 rows; ~53 MB after VACUUM) rather
    than sampled — and every one of the 32 golds was re-executed against both the
    source and the pinned copy and pinned only on row-equality, none fabricated.
    18 graded + 14 held-out, template-disjoint. The stream **samples** by seed
    rather than dealing the whole set (`suite/stream.partition` already did this
    when the pool exceeds `batch × batches`): lax batch 6 × 4 = 24 of 32 (each
    batch 3 graded + 3 held-out), strict 6 × 2 = 12 of 18, the remainder left as
    headroom. The DB layer is parameterized behind a `DbConfig`
    (`suite/families/text2sql.py`) so a second BIRD database is config + data with
    no code fork (the multi-DB to-do, item 55). The seed was refreshed for the
    whole-`trans` schema (D-0001 card rewritten; D-0007 added for the `trans`
    coded values `type`/`operation`; README and line anchors re-pinned) and the
    tests followed the enlarged pool. **Watch in the rerun:** q194's gold uses
    `STRFTIME(CURRENT_TIMESTAMP)`, so its expected rows are calendar-dependent —
    grading is sound (the gold is re-executed at check time) but the pinned answer
    is time-varying; and read the decision content beside the curve as the primary
    evidence — here the content decided the question the curve could not.
52. **Follow-ups on the runs themselves.** (a) The wave-2 and wave-3 arms
    exit 1 after writing their store, `arm.json` and evolution log: commit
    a04d9e8 appended `seed`-keyed arms to both TOMLs while the arms ran from
    a worktree pinned before the field existed, and the end-of-run report
    resolves every arm in the file — the data is intact; regenerate the
    reports from main. `experiment.py` should resolve only the arm it ran,
    or a run should snapshot the TOML it loaded beside `arm.json`. (b) The
    results files under `experiments/results/reasoning-core/` and
    `experiments/results/text2sql/` and the README section are not written;
    the last wave was running when this item was. (c) The `*-seeded` twins
    (decision 95) of both experiments have not run; on text2sql the seed
    carries exactly the six conventions the loop failed to learn, so the
    seeded − attached gap there is the cleanest reading of items 48–50. (d)
    The retrofit (`hgi experiment retrofit`, running on the stream and
    economy arms) reproduces item 48's artifact by construction, since it
    re-runs the same close; read its stores with that in mind.
    **Built (a) (commit `9847d1b`):** `hgi experiment`'s finish path resolves only
    the arm(s) actually run (`report(exp, root, arms=…)` with `ran = args.arm or
    list(exp.arms)`), and `report` wraps per-arm resolution in try/except so an
    unconstructable sibling becomes a "cannot resolve" note row, not a crash — a
    TOML that later gains an arm no longer exit-1s a finished arm's report.
    **Built (a), second half (item 68, decision 101):** a run now snapshots the
    resolved experiment (bases merged in, `extends` stripped) as `experiment.json`
    beside its `arm.json`, so a later reading resolves against the file as the arm
    loaded it, not against a base since edited.
    (b) is item 55 (the reruns and their result files are unwritten because the
    reruns are unrun). (c) the seeded twins now exist for both experiments (items
    47, 51) but neither rerun has been executed (item 55). (d) stands.
53. **The reasoning-core arms ran with the system `python3` in the shell,
    so every grammar verification failed** (reasoning-core run). The
    launcher started each arm as `.venv/bin/python -c "from hgi.cli import
    main; ..."` from the pinned worktree, which puts the venv's interpreter
    in the process and nothing on PATH, so the shell tool's `python3` was
    the system one: `ModuleNotFoundError: No module named 'nltk'` on all
    twelve cfg rows of each Qwen arm, `pip install nltk` as the next call,
    the budget then refused, and the answer given unverified. Decision 95(d)
    named the dependency; it was not read before launch. Every decision the
    three attached arms admitted is about library availability or budget
    planning — the environment, not the world — and the economy series on
    the cfg rows grade the install attempts. What stands from the run: the
    unaided produce rate (0.79 attached, 0.88 detached on Qwen; 0.75 on
    gpt-oss-20b; 0.88/0.92 on the strict pool), which is the saturation
    reading of item 47 either way. Fixes: (a) a launcher must export
    `PATH=<tree>/.venv/bin:$PATH` or go through `uv run`; (b) the arm
    runner should refuse to start a `reasoning-core` arm whose shell
    `python3` cannot import `nltk` and `regex` — a preflight the family can
    declare (`suite/families/reasoning_core.py`, a `requires` on the
    family) and `run_arm` check before pass 1; (c) the rerun is the natural
    next step and costs about eighty minutes of endpoint for the five arms
    in three waves; the `*-seeded` twins should join it, since the seed's
    derive-then-verify method needs the same shell.
    **Built (commit `1c21b0e`):** both fixes. (a) `suite/tools.py` `shell_env()`
    prepends the running interpreter's directory to `PATH` and every shell call
    runs under it, so a shell `python3` resolves to the venv's, not the system
    one. (b) a general `requires` field on `Family` (the four reasoning-core
    families declare `("nltk","regex")`); `run_arm` preflights it before pass 1 by
    importing through the *shell tool's* python (`can_import`, the same
    `shell=True` path a command runs under), and refuses to start with a clear
    message otherwise — verified a reasoning-core arm preflight-passes in this
    repo's venv and would refuse where the shell python lacks the modules. (c) the
    rerun is still unrun (item 55).
54. **Mid-run health telemetry in the arm runner** (wired). The
    reasoning-core and text2sql runs (items 47–53) were wasted invisibly
    because `progress()` wrote only `sessions` and `curve` to `arm.json`, so
    an arm whose retrieval reached nothing (empty `in_context`, items 39,
    48, 50) or whose every draft died at the contract floor (items 32, 41,
    49) produced a normal-looking curve and could not be told from a healthy
    arm until it finished. `hgi.evolution.health(store, mode)` now derives,
    from the store already on disk (no model call), a per-pass block that
    `progress()` writes into `record["health"]` on the attached loop and the
    detached draw both — tail-able as the arm runs. Per pass: `reach`
    (records considered and the accepted non-constitution ones in context —
    empty is the silent failure, and on a seeded arm the pass-1 tripwire that
    the latch scope is wrong), `errors` (rows, tool-error rows, and the count
    by class over each row's final error and its whole `tool_errors` trace,
    so the nltk `shell-exit` and the malformed-tool-call spikes both show and
    a world-fault class like `http-410` reads apart from harness breakage),
    `coverage` (failed rows, how many filed an observation, how many shaped),
    and `consolidation` (the round's drafts: `nominated`, `admitted`, and
    each nomination's bucket — `refused_floor` kept apart from `declined`, so
    the text2sql/economy floor-refusal reads distinctly). The reach and
    coverage logic is factored, not duplicated: `evaluated_sessions` and
    `in_context_records` in `hgi/evolution.py` (shared with `arm_log`/
    `_pass_entry`) and `observation_for` in `hgi/index.py` (shared with
    `observed_from`). Deferred: a pre-nomination parse-refusal count — drafts
    dropped as malformed in `roles.drafts_in` before they become nominations
    are not persisted to disk, so a pure read cannot see them; the
    floor-refusal that text2sql/economy actually hit *is* captured, since it
    lands as a nomination outcome (`refused by the floor: …`). Also deferred:
    surfacing the block in the dashboard and a `--tail`/`hgi experiment
    watch` reader — the field is written and readable, but nothing yet
    renders it live.
55. **The reruns are prepared and unrun; session housekeeping** (2026-09-14).
    Everything items 47–54 name is built and on `main` (33 commits from
    `4ee3142`), and both experiments are ready but have **not** been executed —
    running them is the next action:
    - **reasoning-core**: run `experiments/reasoning-core-hard.toml` (the
      calibrated hard tier — regex L5 / cfg L3 @ (8,14) — with the
      `qwen-seeded`/`qwen-strict-seeded` twins). This is the rerun, not the
      saturated moderate `reasoning-core.toml`. The item-53 shell preflight now
      guards the `nltk` trap before pass 1.
    - **text2sql**: run `experiments/text2sql.toml` (the 32-question pool,
      sampled, with the seeded twins). The DeepSeek teacher was verified live to
      draft token-anchored, adequately-cited records under the item-49 elicitation
      fix (it declines honestly rather than writing generic drafts) — but
      **coverage is now the binding constraint**: records are earned only where the
      stream forms ≥2-session groups on one convention, so where it doesn't,
      expect principled declines, not fills. Watch the mid-run `health` block
      (item 54): empty `reach` on a seeded arm's pass 1 means the latch scope is
      wrong and the seeded run is moot before endpoint is spent.
    - The seeds' compare/contrast expectations (both experiments) are projections,
      not measured; the runs confirm or refute them.
    - **Multi-DB injection for text2sql** (optional, deferred): `DbConfig` is
      parameterized, so a second BIRD database is verify-SHA + select/group its
      questions template-disjoint + add a `DbConfig` + `_register` + `hgi suite
      fetch` — config and data, no code fork.
    - **Housekeeping shipped:** the role prompts were restamped for the split
      rosters (`3c43b73`; the teacher roles carry `deepseek-ai/DeepSeek-V4-Pro`,
      the pass carries the reasoning-core actors — quiets `role-pricing` at boot),
      and `CLAUDE.md` was added as the always-loaded constitution with the
      operational procedure moved into the `experiment-runner` skill (`4fe9376`,
      `a2c7740`), so agents stop re-deriving the venv/endpoint/concurrency setup.
56. **reasoning-core-hard `qwen-attached` — the budget mechanic confounds the
    hard tier, again; and round 3 minted a duplicate instead of corroborating**
    (2026-09-14, run dropped early at pass 7 of 8, not committed; store lived
    under gitignored `runs/`). The item-53 fixes held at launch — nltk/regex
    import in the shell, preflight passed, and passes 1–6 carried zero
    `shell-exit`. The curve read 1.0, 0.5, 0.25, 0.5, 0.75, 0.75, then 0.25 on
    the batch-1 revisit. The health telemetry (item 54) was healthy throughout
    (backward pass covering, store growing), so the findings are in the decision
    *content*, not the curve (item 51's warning):
    - **Environment, not world (item 53 recurring on the hard tier).** All 11
      observations and both admitted decisions (D-0001, D-0002) are about the
      **shell-call budget** or the reply format (`tool-budget` shape ×9, two
      `other(non-JSON …)`); none is about the produce-and-verify *method* the
      world is designed to teach. The actor keeps failing by exhausting its call
      budget (over-verifying — O-0007 found the right answer `'12'` then
      re-verified until the third call was refused), so budget-discipline is all
      the teacher can distill. The "halt before exceeding, submit best-so-far"
      lesson plausibly *lifts* the lax curve (the recovery to 0.75), which is why
      the drift is invisible in the pass rate. The hard tier's difficulty is
      confounded by the budget mechanic — the same defect item 47 named for the
      moderate tier's strict pool, still unfixed for the harder run.
    - **Duplication: round 3 minted a twin instead of corroborating.** D-0001
      (round 2, K-0002) and D-0002 (round 3, K-0003) are the same claim ("a tool
      call budget is a hard limit: halt before exceeding it, even if a candidate
      is unverified"), same latch terms (`tool-budget`, `shell-tool`), same
      work-shape, same enforcement floor. Corroboration *worked within* round 2
      (D-0001 aggregated 7 observations across S-0002/3/4), but in round 3 the
      two new budget observations (O-0010, O-0011) minted D-0002 as a fresh
      `rung: new-decision` (`lineage.supersedes=[]`, `folded_from=[]`) rather
      than corroborating D-0001. This is a consolidator dedup/folding gap
      independent of this experiment — cf. item 33 (the strict arm not folding
      restatements). Both twins then fired together (pass 7 `reach.in_context=2,
      [D-0001, D-0002]`).
    - **Negative transfer on revisit.** Batch 1 scored 1.0 at first sight
      (pass 1, empty store); re-met at pass 7 with both budget decisions in
      context it dropped to **0.25**, `errors.budget=4` and a lone `shell-exit`
      (uninvestigated — the run was dropped mid-check; likely a transient
      non-zero shell exit, not the nltk import trap, since preflight passed and
      1–6 were clean). The injected budget lessons correlate with a regression
      on already-solved tasks — the sharpest single reading that the store is
      steering the actor wrong here.
    - **Next.** ~~Fix item 47 (make the budget fail no task, or price the pool so
      producing-and-verifying is what separates) before rerunning the hard tier,
      or the run measures budget arithmetic, not method transfer.~~ **Done**
      (2026-09-14): the budget gate is removed, the check grades the answer alone,
      so the strict pool bites through the answer and the teacher sees method
      failures, not budget overruns (item 47, superseded note). Separately,
      chase the round-N corroboration-vs-mint gap in the consolidator (why fresh
      observations of an existing claim mint a new decision across rounds); a
      focused repro is two rounds of same-shape observations. The other item-55
      arms (`qwen-detached`, `20b-attached`, the strict and seeded twins) and the
      text2sql rerun remain unrun.
57. **The observation-grouping axis is conflated with the consultation-hook
    vocabulary, and that is the root of the budget over-keying (items 47, 56).**
    A review against the GCE doctrine v2 (`WorldVue/docs/research/gce-doctrine/`,
    §§ 7.4–7.5, 8, 10.3, 11.1, 12.6) and its latch walks found HGI's observation
    *stratum* already doctrine-correct — `Observation.shape` is empty at intake
    and filled only at the owner-gated backward pass (`hgi/types.py:368`,
    `hgi/consolidate.py:87`) — but the *vocabulary* it is filled from is wrong.
    `work-shape` (the 9-term closed set, `store/registry/vocabulary.json`) does
    two incompatible jobs: decision consultation-hook routing (legitimate — it is
    minted from known task presentations, which exist ahead of the instances) and
    observation grouping (illegitimate — the lesson-convention axis cannot be
    known ahead of the instances; §7.5 "classes minted ahead of instances are
    priming"; §11.1 orthogonal-axes). Of the nine terms, seven are
    tool/way-of-working, so the palette pushes the blind coder toward tool-major
    shapes — the exact failure `hgi/roles/coder.md` warns against (item 87).
    Mechanism of the budget over-keying: `tool-budget` is declared by nearly
    every family, so budget noticings cluster across sessions and clear
    `decision.independent_observations`, while the real conventions (the
    produce-and-verify *method*) have no term, fall to `other(<convention>)`, and
    never group by tuple-equality (`hgi/consolidate.py:93`), so they never reach
    the bar. `pool_universal_terms` (`hgi/consolidate.py:686`) guards *hooks*
    against this, not observation grouping — the leak. The fix is a six-part
    contract evolution; parts (1)(4)(5) are the ones that would have moved the
    reasoning-core-hard run, (2)(3)(6) the structural cleanup that stops it
    recurring:
    1. **Separate the axes.** A distinct, open, instance-grown *convention*
       vocabulary (a new key-space) for observation grouping; keep `work-shape`
       for decision hooks only. Legible symbolic keys stay on the decision side
       (§2 position 1); grouping moves to an open axis.
    2. **Group on raw anchors, derive the label.** The blind coder proposes
       clusters over raw anchors (it is already blind — the coding species done
       right) rather than picking from a closed enum and joining on tuple
       equality; the shape is a label minted from the cluster, closed-with-escape
       (§7.3, §7.4 "ratified against the raw anchors, never the labels").
    3. **Give both vocabularies an escape→mint lifecycle** so they are
       dynamically expandable — a recurring `other(X)` across independent
       sessions nominates `X` at the owner-gated pass. Extend the existing mint
       ladder (decision 94) and `reviews.escape_events` (item 12), do not
       rebuild; the gap is that the ladder does not yet feed the new convention
       axis.
    4. **Cross-shape applicability as a consolidation lens.** Today the payload
       is abstracted (`hgi/roles/consolidator.md`) but the hook is dragged back
       to the origin tasks by `anchor_terms` (`hgi/consolidate.py:631`, item 79),
       defeating transfer by construction. Demote `anchor_terms` to a floor and
       add a generative lens asking which shapes the lesson fires on + the
       `not_this` (§7.4/§8: the consolidator sets the applies-when edges).
    5. **Typed `failure-unelicited` markers.** L-0004 walks every failed row
       (`hgi/close.py:234`) but `file_observations` mints nothing on an empty
       reply ("empty is legal", `hgi/roles/pass.md`), so a failure with no
       elicited convention vanishes — it never forms a group, never reaches
       `triage`'s reducible/irreducible split, never becomes a reality entry.
       Do **not** force a substantive observation (§7.5: a forced pick
       manufactures noise); instead file a typed marker so non-elicitation is
       visible telemetry — the lens miss stream / recall floor (§12.6; the
       WorldVue `11a-bg` "unknown IS a finding" shape). A failed run is the world
       voting (reality species, §7.3); it must leave a record either way.
    6. **Split `noticed` into `happened` / `turned_on`.** The record blends the
       settled world-fact (price-zero, transcribable, §10.3 "knowledge of
       happenstance") with the model's inference (the convention/fix,
       lower-trust) in one field, though `pass.md` insists suspected and verified
       never share a register. Split them; group on `happened`. Also apply the
       elicitation score-strip (`hgi/close.py:200` `_world_facts`) to the coder's
       rows — the coder is currently passed the full evaluation row, scores
       included (`hgi/consolidate.py:85`), so the anti-over-keying discipline is
       dropped at coding.
    *Why it may be right:* it removes the structural selection-for-budget at its
    source (the palette), makes transfer and non-elicitation first-class instead
    of silent, and each part maps to a named doctrine law. *Why it may not:*
    parts 1–3 and 6 are a schema change to the observation record and the
    registry, so the seed stores under `experiments/seeds/` need migration and
    the committed `store/` re-reads; grouping on raw anchors (2) trades a
    deterministic join for a model judgment (guard it with the blind-coder
    agreement control, decision 59); and an open convention axis without the
    pool-universal guard extended to it (part 1 must carry the guard across)
    could regrow a different over-broad shape. Sequence: the schema/axis seam
    (1, 2, 6) is a contract change and ships serial-first; the consumers (3, 4, 5)
    build on it. Migration note owed for `experiments/seeds/`.
58. **Variance-driven ripeness: mechanize the fast-tracking of materialization,
    up to — never past — the human gate.** Builds on item 57 (needs the
    `happened`/`turned_on` split and the open convention axis). The
    crystallization law (doctrine §7.4), the leafing law (§8) and the price-zero
    limit (§10.3, §3.2) are one skeleton: a latent lesson materializes on a
    mechanical settlement/falsification signal, lazily. Variance is that signal
    for the observation/lens tier, and both halves are already computed
    (`_variance` `hgi/lens_battery.py:394`; `pool_universal_terms`
    `hgi/consolidate.py:686`), so this is composition, not new machinery. Two
    composed levers:
    - **(A) Ripeness auto-nomination + brief ordering.** Per grouped cluster,
      score independence × (low variance over the cluster's `happened` tokens) ×
      (1 − pool-universality); float ripe clusters (low-variance, non-universal,
      multi-session) to the head of the consolidation brief, annotated with the
      score, so the consolidator authors the ripe ones first — the machine ranks
      and annotates, it never authors the sketch (I2). Pure projection/ordering —
      no new store, no new gate. The
      universality penalty is what refuses the budget false-ripeness (high
      independence but universal presentation — the exact item-56 trap).
    - **(B) Price-zero transcription of the happenstance floor.** The `happened`
      half is settled happenstance — price zero, mechanically evaluable through
      the anchor — so it transcribes to the fact layer with no adjudication
      (§10.3: "transcription is legal exactly where the claim's price was zero at
      entry AND evaluation is mechanical"); only `turned_on → decision payload`
      crosses the gate. Reuse the existing fact kind; do not add one.
    **The refinement that keeps it from re-creating the budget bug:** variance is
    measured on the world-content axis (the concrete token), never on the
    presentation/environment axis — §11.1's lint in mechanical form; the
    `names_world_content` floor (`hgi/drafting.py:96`) already refuses a payload
    naming no checkable token. **The boundary:** nothing auto-admits — I2 / §7.2
    make the permanent-write gate non-collapsible (a security control, post-§15
    poisoning). The machine enumerates, pre-computes the ripe nomination, and
    transcribes price-zero facts; the owner commits. *Why it may be right:* it is
    the direct test of the doctrine's claim that variance is the observation/lens
    materialization signal, and it optimizes throughput-into-the-gate rather than
    catch-count (I9). *Why it may not:* the variance stream is design-stage in the
    doctrine (§12.6, §17), so this promotes an unvalidated instrument to a live
    nominator; a small or low-independence pile makes variance and universality
    both noisy (floor both levers below a minimum cluster size); and transcription
    (B) widens the machine-writes surface — keep it strictly to the price-zero
    fact floor, mechanical-eval only, or it becomes the loophole §10.3 warns
    against. Depends on item 57 parts 1, 2, 6; sequenced after the seam and after
    item 57 parts 3–5 (all share `hgi/consolidate.py` and `hgi/close.py`).
59. **Validate items 57 and 58 on the reasoning-core-hard endpoint — the empirical
    test the stub cannot run.** Items 57/58 ship proven on the stub and 732 tests;
    whether they fix the item-56 pathology is a real-model claim, unrun. Run the
    attached arm of `experiments/reasoning-core-hard.toml` (`arms.qwen-attached` —
    the arm that consolidates and re-meets batches 1–2 for retention; the strong
    teacher over the mid-sized actor). Load the **experiment-runner** skill first
    (the W&B `WANDB_ENTITY`/weave-project 401 trap, the 429 concurrency ceiling so
    arms run sequentially, the reasoning-core generator stack, reading a run back).
    Falsifiers, each read from the arm store (`runs/reasoning-core-hard/qwen-attached/`)
    and its consolidations:
    - **Method over environment (items 56, 57).** Admitted decisions name the
      produce-and-verify *method* / world-conventions (regex-level-5, grammar
      facts) — not nine `tool-budget` duplicates. Budget lands as
      `other(<way of working>)` on the `convention` axis and does not dominate
      grouping. The failure is a store still keyed on budget.
    - **Negative transfer gone (item 56).** The batch-1/2 re-meet after the stream
      does not regress (item 56 saw batch 1 fall 1.0 → 0.25 once both budget
      decisions were in context). The failure is a re-meet that drops with the
      store in context.
    - **Ripeness surfaces the method (item 58 lever A).** The two Cut-C slots are
      populated on the brief's clusters, and the method clusters — low
      world-content variance, non-universal presentation, multi-session — rank
      ahead of any budget cluster (which sinks on the universality factor).
    - **Non-elicitation is visible (item 57 part 5).** Failed rows that elicit no
      convention appear as `failure-unelicited` markers in `brief["unelicited"]`,
      not silently absent.
    - **Corroboration, not mint (item 56 round-3 gap).** Fresh observations of an
      already-admitted claim corroborate it (a `counterfactual-edit`/`hook-edit`
      or nothing), never mint a duplicate decision across rounds.
    Runs sequentially on the endpoint (billed); the detached twin
    (`arms.qwen-detached`) is the paired no-store control if a second run is
    affordable. A green run commits its result files under `runs/` and a
    carry-forward note; a red falsifier is the more valuable outcome — it names
    which of items 57/58 the endpoint refuses.
60. **The item-59 run — the axis rework holds where item 56 broke, and two reds
    name what 57/58 do *not* reach** (2026-09-15, `qwen-attached` complete over
    8 passes + `qwen-detached` 6-pass control; result files under
    `experiments/results/reasoning-core-hard/`, arm stores under gitignored
    `runs/reasoning-core-hard/`). Attached curve `1.0 1.0 0.75 0.75 1.0 1.0 |
    0.75 0.75` (revisit), stream 0.92 (22/24); detached `0.75 1.0 0.75 0.75 0.75
    1.0`, 0.83 (20/24), no store. Two admitted decisions, both budget: D-0001
    (after pass 4, fired 1/1) "the shell budget is a hard limit; exceeding it is
    a non-transient error"; D-0002 (after pass 6, **fired never**) "once a budget
    refusal lands it is non-transient — stop and submit". The five falsifiers:
    - **A precondition red, found and fixed first: the endpoint crashed the
      pass-4 consolidation.** DeepSeek coded the bare convention label
      `call-budget-exceeded` onto the grouping axis; item 57's escape→mint wrap
      (`_convention_label`) was wired on the local coder path
      (`group_observations`) but **not** on the analyst/ARIA path
      (`adopt_shapes`), so `Term("convention")` refused the bare term and the run
      died mid-stream (first two attempts: one API timeout, one this crash). Fixed
      `9d0c1c8` — `adopt_shapes` routes through `_convention_label`, the label
      lands as `other(call-budget-exceeded)`, regression test pins the exact
      term. This is itself an item-57 finding: the escape ladder was half-wired.
    - **Method over environment — RED, but the keying pathology is gone.** The
      two admitted decisions are budget, not the produce-and-verify method — so
      the store is still budget-keyed at *admission*. **But** budget no longer
      mints a `tool-budget` shape: it lands as `other(call-budget-exceeded)` (×9)
      and `pool-exhausted` (×3) on the open `convention` axis, exactly as item 57
      intends, and the method conventions *do* land on the axis
      (`other(module-not-found)` — the real `nltk.parse.earley` vs `earleychart`
      fix — `other(grammar-parsing-attempt)`, `other(invalid-json-reply)`). The
      residue is not over-keying but recurrence: budget is the only convention
      that recurs cross-session (indep≥2), while every method convention is a
      per-task singleton (indep=1) that never clears the bar. Items 57/58 stopped
      budget from *drowning the axis*; they cannot make a singleton method recur.
    - **Negative transfer — GREEN.** Batch 1/2 re-meets fell only 1.0 → 0.75
      (item 56 fell 1.0 → 0.25), and both drops are `final reply was not JSON`
      rows with `applied=[]` — no budget decision fired on them (D-0001 fired
      once, on a *passing* row; D-0002 never fired). The detached control scores
      batch 1 at 0.75 at first sight with no store at all, so the attached 0.75
      re-meet sits inside actor-alone variance, not a store-steered regression.
      The sharp negative transfer item 56 named is not reproduced.
    - **Ripeness surfaces the method — RED, but the refusal half works.** Both
      Cut-C slots are populated on every cluster (`world_content_variance`,
      `presentation_universality` computed), and the universality penalty
      **correctly sinks both budget clusters to `ripeness=0.0`** (pu=1.0) — the
      item-56 false-ripeness trap is refused. But no method cluster ranks ahead:
      the method conventions are `ripeness=None` singletons (indep=1), so there is
      nothing ripe to float. Ripeness worked as a refusal; it had no recurring
      method to surface, because the method did not recur (same cause as the F1
      residue).
    - **Non-elicitation visible — GREEN (path present, not exercised).** Zero
      `failure-unelicited` markers, correctly: every failed row elicited an
      observation (cfg_07 → O-0007/8/9, cfg_06 → O-0016/17, cfg_08 → O-0019). The
      marker fires only on an *empty* reply, which never occurred this run, so 0
      is right — the path is wired (`hgi/close.py:148`), just not triggered.
    - **Corroboration, not mint — RED (item 56 round-3 gap recurs).** K-0003
      admitted D-0002 as `rung: new-decision` from the `pool-exhausted` cluster
      **with D-0001 already in the accepted set shown to the consolidator**; the
      nomination's `rung_why` claims "the loop has no record that teaches the
      shell budget is a hard limit whose exhaustion is non-transient" — which
      D-0001 states almost verbatim. The same budget happenstance was coded under
      two different convention labels across rounds (`other(call-budget-exceeded)`
      round 2, `pool-exhausted` round 3), and the consolidator minted a twin
      rather than corroborating. Nuance: D-0002 adds recovery guidance
      ("stop and submit"), so it is not a verbatim duplicate — but it never fired,
      a standing tax with no consumer (I5). This is the consolidator dedup gap
      item 56 flagged as independent of the experiment, confirmed on the endpoint.
    - **Net.** Items 57/58 fix what they were built to fix: budget no longer
      over-keys the grouping axis (it escapes to `other(<way of working>)`), its
      false ripeness is refused, and the catastrophic negative transfer is gone.
      What they do not reach is orthogonal: (a) a method that manifests as
      per-task singletons never recurs into a decision, so budget — the one
      genuinely recurring convention — is still what admission sees; (b) the
      consolidator's corroboration-vs-mint judgment (item 56's open dedup gap)
      still mints twins across rounds under drifting labels. Neither is an axis
      defect; both are the next work. Minor: lever-B transcription runs
      (K-0002 transcribed 2 / surfaced 8; K-0003 3 / 3) but the `happenstance/…`
      series names are cut from noisy `happened` fragments
      (`world_content_token`, `hgi/consolidate.py:1203`) — a normalization owed.
    - **Leftover.** Chase the round-N corroboration gap (why a consolidator with
      the prior decision in context mints a twin — a focused two-round repro
      against the dedup path); consider whether the convention-label instability
      across rounds (`other(call-budget-exceeded)` vs `pool-exhausted` for one
      happenstance) is a coder-stability problem feeding the dedup gap. The other
      `-hard` arms (`20b-attached`, the strict and seeded twins) and the
      detached-strict control remain unrun.
61. **What the item-60 run leaves broken — the two reds and the chores, lifted
    out of the run report into their own work item.** Items 57/58 did what they
    were built to do — budget escapes the grouping axis to `other(<way of
    working>)`, its false ripeness is refused, and the catastrophic negative
    transfer is gone (item 60). What the endpoint still refuses is orthogonal to
    the axis and is the next work:
    - **The consolidator mints twins across rounds — the dedup gap (item 56,
      now confirmed on the endpoint).** K-0003 admitted D-0002 as
      `rung: new-decision` from the `pool-exhausted` cluster with D-0001 already
      in the accepted set shown to the consolidator, its `rung_why` restating
      D-0001 almost verbatim; D-0002 then never fired (a standing tax with no
      consumer, I5). A consolidator holding the prior decision in context still
      mints a duplicate rather than corroborating. Next: a focused two-round repro
      against the dedup/corroboration path — feed a fresh observation of an
      already-admitted claim and assert it corroborates (a `counterfactual-edit` /
      `hook-edit`, or nothing), never a new decision. This is the open item-56
      gap, independent of the axis rework.
    - **A method that manifests as per-task singletons never recurs into a
      decision (item 60, the F1/F3 residue).** Every method convention this run —
      `other(module-not-found)` (the real `nltk.parse.earley` vs `earleychart`
      fix), `other(grammar-parsing-attempt)`, `other(invalid-json-reply)` — is an
      `indep=1` singleton that never clears the recurrence bar, while budget is
      the one convention that recurs cross-session (`indep≥2`). So budget is still
      what admission sees, and ripeness (which correctly sinks both budget
      clusters to `ripeness=0.0`) has no recurring method to float. Items 57/58
      stopped budget drowning the axis; they cannot make a singleton method recur.
      Open question: whether the recurrence bar / cross-session keying should
      credit a method restated under drifting labels as the same convention.
    - **Convention-label instability across rounds may feed the dedup gap.** The
      one budget happenstance was coded `other(call-budget-exceeded)` in round 2
      and `pool-exhausted` in round 3; that drift is what let the consolidator see
      two clusters and mint the twin above. Investigate whether this is a
      coder-stability problem (the coder naming one happenstance two ways)
      upstream of the corroboration gap.
    - **Chore: normalize the `happenstance/…` series names.** Lever-B
      transcription runs (K-0002 transcribed 2/8, K-0003 3/3), but the series
      names are cut from noisy `happened` fragments (`world_content_token`,
      `hgi/consolidate.py:1203`) — a normalization owed.
    - **The other `-hard` arms remain unrun.** `20b-attached`, the strict and
      seeded twins, and the detached-strict control of
      `experiments/reasoning-core-hard.toml` were not run at item 60.
    - *(Item 62 records which of these are now fixed — the dedup gap, the
      label instability and the series-name chore — and lifts the two still
      open — the F1/F3 abstract-keying question and the unrun arms — forward.)*
62. **The item-61 experiment-correctness fixes — what landed, what is still
    open** (2026-09-15). The three code bullets item 61 raised are fixed and
    the reasoning recorded as decision 97; regression + a two-round dedup repro
    live in `tests/test_dedup_corroboration.py` (full suite 742 green). One
    canonical world-content key (`hgi.index.world_content_key`) now feeds the
    grouping variance, the happenstance series name, the escape-label
    canonicalization and the dedup guard, so a world-fact is grouped, named and
    de-duplicated the same way everywhere.
    - **Done — the dedup/corroboration gap.** A fresh `new-decision` draft whose
      evidence rests entirely on world-facts an accepted decision already
      anchors is routed to corroboration (a `still-holds` currency entry, the
      evidence consumed pointing at the standing record, the twin dropped),
      never minted (`corroborates`/`corroborate`, `hgi/consolidate.py`; the pass
      record grows a `corroborated` leg). The guard keys on the world-content
      key, not the coder label, so it survives the label drift that fed the
      item-60 twin.
    - **Done — the convention-label instability.** `group_observations`
      canonicalizes a recurring *escape* label to the one the same world-fact
      first carried (`_canonical_label`, escape→escape only, first-seen wins),
      so the axis no longer forks across rounds. This also credits the
      *drifting-label* half of the recurrence question: a method restated under
      a drifting escape keeps one label and accumulates independence.
    - **Done — the `happenstance/…` series-name chore.** `_happenstance_series`
      now uses the canonical key, so a world-fact transcribed across rounds
      lands one series rather than a fresh name cut from a noisy `happened`
      fragment.
    - **Open — the F1/F3 residue (the abstract-keying design question).** A
      method that manifests as per-task *singletons over distinct world-facts*
      (`other(module-not-found)` on one module, another on the next) still never
      recurs, because those are genuinely different keys — canonicalization
      merges a drifting label for *one* world-fact, never *distinct* world-facts.
      Whether the recurrence bar / cross-session keying should abstract a method
      across distinct world-facts is unresolved and was left unforced: an
      over-eager abstraction would merge distinct conventions. Needs evidence (a
      repro that a genuine method recurs under distinct literals) before a keying
      change, not a speculative one.
    - **Open — the unrun `-hard` arms (billed, out of this session's scope).**
      `20b-attached`, the strict and seeded twins, and the detached-strict
      control of `experiments/reasoning-core-hard.toml` remain unrun; they are
      endpoint runs (load the **experiment-runner** skill), not a code fix. A
      re-run of `qwen-attached` would also be the live confirmation that the two
      guards close the item-60 twin on the endpoint, not only on the stub.
63. **The `qwen-attached` restart, stopped at pass 5 — the guards hold, but the
    coding step reads budget and harness errors off the rows, not the method; fix
    before spending the rest of the sweep** (2026-09-15, fresh `--force` run on
    tree `f052e28`, stopped after 2 of 3 rounds because the defects were already
    unambiguous; store discarded, not committed). Curve `1.0 1.0 1.0 0.75 0.75`;
    5 observations, 1 decision (D-0001, budget), 2 consolidations (K-0001 admit,
    K-0002 refused). The item-61/62 guards are structurally sound on the endpoint
    — budget escapes to `other(budget-exceeded)` on the open convention axis (no
    `tool-budget` shape), the `happened`/`turned_on` split is populated, D-0001 is
    retrieved and fires (competence 2/2), and no pass-4 crash. What the run shows
    is that the *coding* step, upstream of every guard, is the binding defect:
    - **(A) The coder codes the method failure as budget — the core relevance
      miss, caught on the one genuine failure.** Pass 4's only failed row is
      `regex_10` (failed `final reply was not JSON`; it over-verified, made a third
      call, was budget-refused). The observation filed on it (O-0003) reads
      "exceeded the 2-shell-call budget" — the *budget refusal*, not the method
      failure (no valid regex member produced). Its sibling O-0004 is on
      `regex_06`, which **passed**. So of the four shaped observations, all four
      are budget and one sits on a real method failure it mis-reads, while the
      pass-5 failure `cfg_05` — whose `happened` does name the method ("verify a
      candidate string … final reply was not JSON") — was filed as O-0005 but not
      yet coded (`shape=[]` is normal at intake; the coder assigns shape at the
      next consolidation, round 3, which was cut). What round 3 would have shaped
      O-0005 as — method or budget — is the unresolved question. Net: the store's
      only decision so far is
      budget discipline; nothing about produce-and-verify. This is item-60 F1 /
      item-57 parts 2+6 confirmed live on a guarded run — the axis rework stops
      budget *drowning* the axis but cannot make the coder read the method.
    - **(B) Observations track budget refusals, not task outcomes, and fire on
      passing rows.** Passes 1–3 had zero failed tasks yet minted four budget
      observations, all on rows that passed after over-verifying. A budget refusal
      on a *passing* row is economy telemetry (it already feeds
      `tool_budget_respected`), not a world-fact failure, but it reaches the
      observation/grouping axis and is the only thing that recurs cross-session.
      Also: the health `coverage` block counts only failed-row observations, so it
      read `observed=0` on passes 1–3 while budget observations were filed through
      the tool-error path — the two intake streams diverge and the telemetry
      undercounts.
    - **(C) The `not-json` final-reply failure masks the method outcome.** Both
      real failures (`regex_10` p4, `cfg_05` p5) are "final reply was not JSON"
      after the actor over-verified into a budget refusal — so the recorded
      symptom is the format/harness error, not "the produced string was not a
      member." A repair turn on a non-JSON final reply (sibling of item 42's
      malformed-args fix, but for the final answer) would let the true method
      outcome surface; at minimum the close must elicit the world-fact (did the
      candidate match?) rather than the harness error.
    - **(D) Label drift across rounds, unmerged** (the known item-62 F1/F3
      residue, confirmed to bite): `other(budget-exceeded)` round 1 vs
      `other(shell-call-budget-exceeded)` round 2 — canonicalization is per
      world-content key and these are distinct tasks, so it does not merge.
    - **(E) The dedup/corroboration guard was never exercised** — the round-2
      budget nomination died at the independence floor (1 session S-0004 vs bar 2;
      ledger H-0010), so the item-61/62 corroboration path never got a
      cross-session budget group to act on. Round 3 (cut) was the next chance; the
      item-62 live confirmation of the twin-close is still owed.
    - **(F) Over-verification is the actor's dominant failure mode** — it applies
      "verify before answering" until the budget refuses, then emits non-JSON. The
      lesson worth teaching is "one verification suffices," which D-0001 gestures
      at as budget arithmetic rather than method.
    **Fix before rerunning (the point of stopping early):** in order of leverage —
    (1) the close's failed-row observation request and the coder must elicit and
    shape the **world-fact** for reasoning-core (did the candidate match the
    pattern / belong to the grammar, and what about it failed), not the budget or
    the not-json error — items 40 and 49(a) applied to this family, a
    request/prompt change in `hgi/roles/pass.md` and `hgi/roles/coder.md`; (2)
    keep a budget refusal on an otherwise-passing row out of the observation axis
    (it is economy telemetry) so it stops being the only cross-session recurrence;
    (3) a repair turn on a non-JSON final reply, and split the symptom. *Why this
    is right:* every guard downstream is working, so the ceiling on relevance is
    set entirely by what the coder reads off the row — fixing intake is the
    highest-leverage change and it is offline-testable on the stub before spending
    the endpoint again. *Why it may not be enough:* the hard tier is still near
    saturation for the actor (only 2 of 20 rows failed), so even a perfect coder
    has thin method signal to group; issue (C)'s repair turn and a harder floor
    may be needed for the method to fail often enough to recur. The other `-hard`
    arms and the `qwen-detached` control were not started (resources held for the
    fixes).
64. **Multi-shape observation coding to defeat vocabulary drift — one label per
    axis is the wrong model; induce a *set* of labels per observation, and demote
    on presentation-universality, not raw frequency** (2026-09-15, design from the
    item-63 reading). The item-63 run showed the grouping axis drifts: the same
    world-fact coded `other(budget-exceeded)` (cfg_10) one round and
    `other(shell-call-budget-exceeded)` (regex_10) the next never merged, so a
    recurrence read as two singletons. The cause is structural, not L-0009-only:
    the coder assigns **exactly one** convention label per observation
    (`group_observations`, `o.shape = [label]`, `hgi/consolidate.py:183`), grouping
    keys on that one token, and `_canonical_label` (`hgi/consolidate.py:123`) only
    rescues a drifting label when the modal `world_content_key` — a normalized
    `happened` sentence — matches a prior escape. A narrowly-worded token has no
    coarser sibling to fall back on, so distinct task literals fork the axis. This
    is the item-62 F1/F3 residue's root, and L-0004 drifts the same way; L-0009
    only makes it worse because a passing row's "convention missed" is incidental
    and its wording varies most.
    **The design (multi-select with escape, no typed axes):**
    - **Each observation carries a *set* of shapes, not one.** The coder
      multi-selects from the open `convention` vocabulary plus an `other(<what>)`
      escape — closed-with-escape multi-label. `shape` is already a list field, so
      this is **no schema migration**: a coder-contract change (`_coder.cluster`
      returns a label set per observation), `group_observations`, the guard, and
      relaxing `_canonical_label`. Do **not** pre-type the axes (granularity,
      workflow, …): minting classes ahead of the instances is priming (doctrine
      §7.5). The redundancy is the fix — a coarse shared label catches what a fine
      label's drift misses, and it largely retires `_canonical_label` because the
      coarse label does the cross-round merging by construction.
    - **Group per label, not by transitive overlap.** A candidate cluster is *all
      observations carrying label L*; an observation lives in several candidate
      clusters, each nominating on its own label's distinct-session independence.
      Transitive union-find (A~B on X, B~C on Y ⇒ A,B,C) would collapse the pool
      through a chain and must be avoided. Per-label grouping makes the item-61/62
      **dedup guard more load-bearing**: one observation feeding two near-duplicate
      nominations must route to corroboration, not two decisions.
    - **The crux — demote a grouping label on *presentation*-universality (item
      58's `presentation_universality`), never on raw frequency.** With free
      multi-select the coder attaches coarse labels liberally, so a coarse label is
      carried by most of the pool. `_demote_pool_universal`
      (`hgi/consolidate.py:89`) demotes any label over 95% of a multi-cluster pool
      — but in a homogeneous stream like reasoning-core, the coarse label we *want*
      (a `produce-and-verify-method` unifying the distinct fine facts
      `module-not-found` / `grammar-parse` / `invalid-json`) is near-universal by
      frequency, so the raw-frequency guard would demote exactly the method label
      back to singletons — the F1/F3 residue re-created under a new mechanism.
      Budget is universal *on presentation* (every task presents a shell-call
      budget; item 60 saw it sink to `pu=1.0`); a method label is *frequent but not
      a presentation term*. So demoting on presentation-universality sinks budget
      while keeping the coarse method label — this is the difference between
      multi-shape amplifying budget and finally letting the method group.
    - **Soft coder discipline:** ask for at least one coarse and one specific label
      per observation, without naming the axes, so the redundant coarse key is
      guaranteed to exist; otherwise multi-select degenerates back to a single
      narrow label.
    *Drift is not relevance — keep them separate.* Better grouping makes budget
    group *more* robustly too, so this composes with item 63(2): keep a
    budget-refusal-on-a-passing-row (L-0009) out of the convention axis at intake
    (it is economy telemetry), or the presentation-universality guard is left doing
    all the work alone. *Why it may be right:* it makes a coarse recurrence
    survive fine-wording drift, retires the hand-crafted canonicalization, and maps
    universality to the presentation axis where §11.1 says it belongs. *Why it may
    not:* per-label grouping multiplies candidate nominations (the dedup guard must
    hold), and the coder judging multiple labels per observation trades one model
    call's precision for coverage (guard with the blind-coder agreement control,
    decision 59). All of it is offline/stub-testable — no endpoint, no migration —
    and is the natural companion to item 63's intake fix; sequence it after, since
    both touch `group_observations` and the coder contract.
65. **Items 63 and 64 landed offline; what is lifted forward** (2026-09-15). The
    intake fixes (item 63) and multi-shape coding (item 64) are implemented and the
    reasoning recorded as decisions 98 and 99; the full suite is green (752 tests,
    up from 742: the repair-turn tests, the two budget-refusal L-0009 tests, and
    `tests/test_multi_shape_grouping.py`). What landed:
    - **Item 63(1) — read through the symptom.** `hgi/roles/pass.md` and `coder.md`
      now direct the eliciting and coding steps to state the task's world-fact, not
      the budget refusal or the not-JSON error, when that is the visible symptom.
    - **Item 63(2) — budget off the observation axis.** `close._recovered_nontransient`
      excludes a call-budget refusal (`_is_budget_refusal`), so L-0009 no longer
      files an observation from a passing row whose only fault was spending its
      budget.
    - **Item 63(3) — the repair turn.** `suite/agent.py` gives one bounded repair
      turn on a non-JSON final reply and splits the symptom by `cause`.
    - **Item 64 — multi-shape coding.** The coder assigns each observation a *set*
      of convention labels (`cluster` → `{shapes: {name: [labels]}}`),
      `group_observations` groups per-label (non-transitive), and
      `_demote_presentation_universal` replaces the raw-frequency demotion.
    Still open, lifted forward:
    - **The live endpoint confirmation is owed** (billed, out of this offline
      session's scope; load **experiment-runner**). A `qwen-attached` re-run of
      `experiments/reasoning-core-hard.toml` is the confirmation that (i) the intake
      now codes the produce-and-verify method rather than budget, (ii) the coarse
      multi-shape label lets that method recur across distinct world-facts, and
      (iii) the item-61/62 twin-close and the multi-shape dedup overlap both hold on
      the endpoint (the item-62 live confirmation of the twin-close is still owed
      from item 63(E)). The prompt edits are authored, not re-priced — `priced_for`
      is unchanged; re-verify with `hgi roles try` (or `hgi price --reauthor`)
      before the run.
    - **Thin method signal at near-saturation** (item 63, *why it may not be
      enough*). The hard tier failed only 2 of 20 rows for the actor, so even a
      correct intake has little to group; a harder floor (item 63(C)'s repair on
      the *final answer* is in, but a harder task floor is not) may be needed for
      the method to fail often enough to recur.
    - **The unrun `-hard` arms** (item 62). `20b-attached`, the strict and seeded
      twins, and the detached-strict control of `experiments/reasoning-core-hard.toml`
      remain unrun.
    - **The F1/F3 abstract-keying question is now *answered by construction*, not
      by a keying change.** Multi-shape lets a coarse label span distinct world-facts
      without abstracting the world-content key itself (decision 97 left the key
      untouched, correctly). The residual question is empirical: does the model
      actually attach a stable coarse label across distinct fine facts, or does the
      coarse label itself drift? That is what the endpoint run measures.
66. **The item-65 `qwen-attached` re-run — the intake fix works where it fired,
    but the stream saturates and the method failures land where nothing
    consolidates; the floor is raised in answer** (2026-09-15, fresh `--force
    --no-commit` run on the committed item-63/64 tree `b8e22df`; store under
    gitignored `runs/reasoning-core-hard/qwen-attached/`). Clean run (W&B auth,
    Weave, the item-53 `nltk`/`regex` shell preflight all passed; no pass-4 crash
    — the item-60 `adopt_shapes` fix held). Curve `1.0 1.0 1.0 1.0 1.0 1.0 | 1.0
    0.75` (revisit), stream **24/24**, **0 records admitted**. The result is an
    experiment-saturation finding, not a pipeline defect:
    - **The stream (passes 1–6) was fully saturated** — `failed:0, observed:0` on
      every consolidating pass. The three consolidations (K-0001/2/3 after passes
      2/4/6) each nominated exactly one thing — an *ungrounded pass proposal* (e.g.
      H-0001, "consolidate all verification logic into the initial tool call to
      avoid redundant execution") — and correctly **refused it at the independence
      floor** (`refused_floor:1`, 0 sessions of evidence vs bar 2). Empty piles
      produced no phantom decisions; the pipeline behaved.
    - **The only real method failures landed on the retention revisit (passes
      7–8), which by design does not consolidate** — so the three observations
      minted there were never coded, grouped, or adjudicated (`shape:[]`, open,
      stranded). No K-0004.
    - **The three observations, against the intake fix (item 63):** O-0001 (cfg_10)
      is a *clean produce-and-verify method fact* — "the first shell call failed
      with a non-transient NLTK parsing error because the script passed a nested
      list of tokens to the parser instead of a flat list" — the item-63 intake
      edit working live, where item 60 would have said "exceeded the 2-shell-call
      budget". O-0002 (cfg_09) names the real NLTK method error in `happened` but
      its `turned_on` still drifts to budget (partial). O-0003 (cfg_09) is an
      exogenous turn-limit harness symptom (a miss, though the downstream artifact
      of the same over-verification). So intake is materially better than item 60
      (which was budget-only) but not clean on the harder cfg_09.
    - **Falsifier scorecard (item 59):** *negative transfer* — **GREEN** (batch-2's
      1.0→0.75 re-meet is with an **empty store**, actor-alone variance; item 60's
      sharp 1.0→0.25 did not recur). *Method-over-environment*, *ripeness surfaces
      the method*, *corroboration-not-mint* — **not reached** (0 admits; coding
      never ran on the stranded observations). *Non-elicitation visible* — **N/A**
      (no empty-reply failures). The intake layer is confirmed; the
      coding→grouping→decision path is untested on the endpoint because nothing
      failed during a consolidating pass.
    - **Two standing gaps this surfaces.** (a) *Structural:* method failures that
      emerge only on the retention revisit are minted as observations but never
      consolidated — late-emerging signal is invisible to learning. If the revisit
      is purely a retention probe, that is by-design, but the observations sit
      stranded. (b) *Telemetry:* the item-63(B) health-coverage undercount
      reproduced — O-0001 sits on a *recovered/passing* row (pass 7 was 1.0) filed
      through the non-failed-row path, so `coverage.observed` read 0 while the
      observation exists; the two intake streams still diverge.
    - **The binding constraint is item-65's "thin method signal at near-saturation",
      now measured sharply:** 24/24 on the stream, and item-63(3)'s repair turn on
      non-JSON final replies likely *compounds* it by recovering would-be failures
      into passes. **Answer:** the difficulty floor is raised (decision 100, the
      next commit) — `HARD.cfg_tokens` `(8,14)`→`(10,16)`, the item-47 "longer valid
      derivation" lever on the generator the actor actually failed on (cfg), levels
      unchanged so the seed's level-specific method facts stay valid. **Owed before
      the next billed run:** a scratch calibration pilot — item 47's absolute cfg
      numbers ((8,14)→0.33, (10,18)→0.17, a knife-edge) are **stale** because the
      repair turn post-dates them and lifted (8,14) to ~1.0, so where (10,16) lands
      is unmeasured and must be piloted to scratch (per the **experiment-runner**
      skill) before spending `qwen-attached` again. Watch for the 0.17 floor effect
      the cliff warns of.
    - **The other `-hard` arms remain unrun** (item 62): `20b-attached`, the strict
      and seeded twins, and the detached-strict control.
    - **The seed store is now stale relative to the raised floor** (decision 100).
      `experiments/seeds/reasoning-core-hard` is authored for the old `(8,14)`
      window; its window numbers and instance-specific counts ("nine of twelve
      grammars", "the twelve pinned patterns") must be re-verified and re-authored
      for `(10,16)` before the `qwen-seeded`/`qwen-strict-seeded` twins run. The
      plain arms do not use the seed.
67. **Calibration: the `(10,16)` lax floor is still saturated — the window is not
    the lever for the lax pool; the strict pool is** (2026-09-15, scratch
    `qwen-detached` pilot on `openai`/`Qwen/Qwen3.6-35B-A3B`, `HGI_RUNS` under the
    session scratchpad, `--no-commit`, store discarded). First-sight **23/24
    (0.958)**, curve `1.0 1.0 1.0 1.0 1.0 0.75`, the one failure a wrong-answer row
    (clean run, no harness fault). This confirms the item-66 reading: the actor
    fails on **neither** grammar hardness (it produces valid grammar members
    first-try) **nor** over-verification (item-63(3)'s repair turn recovers the
    non-JSON failures that were the failure mode), so raising the grammar window
    within the safe band (off item 47's `(10,18)`→~0.17 cliff) **cannot move the lax
    pool**. **NO-GO for `qwen-attached` at this floor** — it would reproduce item
    66's null result (no method failures during the consolidating passes). The
    difficulty lever is the **strict pool** (`reasoning-core-hard-strict`, budget 1,
    **no repair call**): a wrong first candidate cannot be repaired and fails on the
    answer, which is where method signal comes from. Decision 100's window raise is
    not wasted — harder grammars mean more wrong first candidates, which *helps the
    strict pool* — it is just insufficient for the lax pool alone. **Next:** a
    `qwen-strict-detached` scratch pilot at `(10,16)`; item 47 saw *moderate*
    strict-detached at ~0.85–0.92 on Qwen, so the hard strict number is genuinely
    unknown and is what the pilot measures. If it lands ~0.5, run
    `qwen-strict-attached` (the seeded twin waits on the seed re-authoring, decision
    100). If strict is *also* saturated, the lever is a different/weaker actor or a
    higher generator level, not the window.
68. **Experiment files derive from shared bases; the resolved definition is pinned
    per arm** (2026-09-15, decision 101). The W&B-Inference files' restated model
    registry, `weave_project` and split-roles teacher block now live in
    `experiments/_base.toml` and `experiments/_teacher.toml`; ten files `extends` one
    of them via `load()`'s new top-level `extends` key (deep-merged by the same
    `_merge` that lays an arm over the defaults). `run_arm` writes the resolved
    experiment as `experiment.json` beside `arm.json` (the second half of item 52(a)).
    All 72 arms resolve byte-identically before/after (captured-baseline diff + two new
    tests in `tests/test_experiment.py`). *Left un-migrated by choice:* `incidents.toml`
    (its own aliases and a different DeepSeek id, `-0813`), the `hgi-dev` probes
    (`probe.toml`, `stream-probe.toml` — a different `weave_project`), and the stub
    smoke files (no registry). *Leftover:* (a) `reasoning-core`/`-hard` are still
    arm-for-arm twins differing only in the family suffix — `extends` removed their
    shared models/roles/defaults but not the per-arm `families` lines or the prose;
    parameterizing the suffix was judged more machinery than two files justify (decision
    101), revisit if a third tier appears. (b) nothing re-reads `experiment.json` yet —
    `report`/`compare`/`from_dir` still read `arm.json`'s recorded spec (self-contained
    per arm); the pin is provenance for a human or a future reader, not yet a load path.
69. **Calibration (continues items 66/67): the hard strict pool is also saturated,
    and none of the three difficulty levers is genuine — the actor's method ceiling
    is high across grammar levels; what the strict pool's turn cap converts into
    "failures" is slow convergence, not wrong method** (2026-09-15, all runs to the
    session scratchpad, `--no-commit`, nothing under `runs/`). The item-67-owed
    `qwen-strict-detached` pilot and two follow-up scratch pilots that triangulate the
    lever:
    - **`qwen-strict-detached` at `(10,16)`** (`Qwen/Qwen3.6-35B-A3B`, the billed pilot
      item 67 owed; clean run — W&B auth, Weave, the item-53 shell preflight all passed).
      First-sight **22/24 = 0.917** (curve `0.75 1.0 1.0 0.75 1.0 1.0`, confirmed by
      `row_passed` over the six session stores — no hidden split). Per generator: **regex
      12/12 = 1.0** (saturated), **cfg 10/12 = 0.83**; both failures (`cfg_00`, `cfg_01`)
      are clean strict-pool method failures (valid schema, wrong answer, repair call
      refused at budget 1). This is the **~0.85–1.0 still-saturated band**, the opposite
      end from item 47's ~0.17 cliff. **NO-GO for `qwen-strict-attached`** — it would land
      in item 66's near-saturated regime (thin method signal for the consolidating passes).
      So the window raise (decision 100) is insufficient for the strict pool *as well as*
      the lax pool: harder grammars give more wrong first candidates in principle, but at
      `(10,16)` the actor still produces a valid member first-try on ~0.92 of rows.
    - **Weaker actor `gpt-oss-20b`, strict-detached, cfg L3** (16-task scratch pilot, same
      seed 0 as the qwen batches). First-sight **13/16 = 0.81** — a real ~11-point
      downshift off qwen's 0.92 (and 20b now fails regex too, 5/7, where qwen was 12/12),
      but still above the ~0.4–0.6 target. The weaker actor **alone** is not enough.
    - **`cfg_level` 3→4, `gpt-oss-20b`, strict, cfg-only** (12-task scratch pilot; the
      `HARD` tier bumped to `cfg_level=4`, same `(10,16)` window, temperature 0; run through
      the real `evaluate_session(detached)` via `suite.use()` on a level-4 suite generated
      by the real generator stack — Agent, `shell_budget=1`, scorers and checker all the
      real ones). First-sight reads **6/12 = 0.50** — apparently dead-center of target — but
      **that is a turn-cap artifact, not difficulty**: 4 of the 6 failures were
      `turn limit reached` at `MAX_TURNS=8` (not method failures), and re-running the *same*
      12 instances with `MAX_TURNS=16` gave **10/12 = 0.83**, with the four previously-
      exhausted rows passing (three in a single turn — run-to-run endpoint nondeterminism at
      temp 0, not the cap alone). Only `cfg_00` is a genuine grammar-difficulty method
      failure across both runs; the remaining fail is an endpoint malformed-tool-call
      artifact (item 42's class). So the actor's *convergent* ceiling at cfg L4 is ~0.83 —
      the same saturated band as L3 — and the apparent target-band number at the real 8-turn
      cap is **turn-starvation plus draw variance**, exactly item 66's "exogenous turn-limit
      harness symptom": minted as observations, carrying no produce-and-verify method fact
      the teacher can distill.
    **Reading.** Across all three levers — grammar window (0.92–0.96), weaker actor (0.81),
    `cfg_level` bump (0.50 artifact / 0.83 real) — none genuinely lowers the actor's
    produce-and-verify ceiling. The strict premise (a wrong first candidate that cannot be
    repaired) rarely bites because the actor's candidates are usually *eventually* correct
    given turns; the turn cap, not correctness, is doing the separating. **NO-GO on
    `cfg_level=4` as a difficulty lever** (and it would invalidate the seed, decision 100,
    for a false lever). Raising the turn cap is the wrong direction (it lifts the rate);
    lowering it manufactures harness-symptom failures, not method signal. **A genuine lever
    must make the first candidate hard to get *right*, not slow to *verify*** — a task family
    whose members need reasoning the actor cannot shortcut, or an actor materially weaker at
    the produce step — not a longer derivation the actor still reaches. Until such a lever
    exists, the `-hard` strict attached arms stay unrun; the seed re-authoring for `(10,16)`
    (decision 100 / owed) is moot for these arms while the pool is saturated.

70. **text2sql is the genuine high-hardness lever the item 66–69 calibration
    sought; the attached run generates many observations and the
    observation→decision pipeline sanity-checks correct** (2026-09-15,
    `experiments/text2sql.toml` arm `120b-attached`, gpt-oss-120b actor +
    DeepSeek-V4-Pro teacher, batch 6×4 + revisit `[1, 2]`; store under gitignored
    `runs/text2sql/120b-attached/`). Items 66–69 found reasoning-core saturated
    across every lever (grammar window, weaker actor, cfg-level → ~0.85–1.0, the
    "failures" being turn-cap artifacts, not method failures) and asked for "a
    family whose members need reasoning the actor cannot shortcut." text2sql is
    that family: SQL over a real BIRD schema, graded by **re-executing** the
    returned SELECT — a wrong-but-running query fails, and the traps
    (EXISTS-vs-all, missing GROUP BY/SUM, coded status/frequency literals,
    district-vs-client scope, wrong year-columns) are genuine reasoning, not
    verification speed.
    - **Difficulty confirmed before spending the arm:** a detached 2-batch
      scratch pilot (same seed 0) landed **0.33 / 0.50** first-sight with
      `output_schema_valid`/`tool_budget_respected`/`suite_hash` all 1.0 — the
      failures are real wrong-answer method failures, not harness/budget/schema
      artifacts.
    - **The run:** curve `0.33 0.33 0.17 0.17 | 0.17 0.33` (4 first-sight + 2
      revisit), **40 observations**, two consolidations, two decisions. K-0001
      (after pass 2) admitted **D-0001** ("inspect the schema to verify table and
      column names before writing the query") from a group of 10 observations
      spanning S-0001 *and* S-0002 (clearing the two-session independence bar);
      K-0002 (after pass 4) admitted **D-0002**, a hook-edit refining the same
      lesson from 5 more observations, and **declined** an over-reaching
      aggregation hook-edit as already covered by `schema-coded-value`. D-0001
      **retrieved** on pass 3 (S-0003 consulted it) — the retrieval the item-49
      text2sql run never achieved.
    - **Sanity-check verdict (the four questions):** (1) failed rows mint
      observations abundantly (16 by pass 2, 40 total; two lenses per failed row
      via item-64 multi-shape coding); (2) the majority state the world-fact
      (aggregation-misapplied, wrong table, unverified columns, coded values), a
      minority are exogenous (budget / "no rule consulted" — items 40/48/66), and
      all anchor on the failing row's call; (3) accept/refuse is correct —
      single-session groups refused at the independence floor, the two-session
      group admitted, the vocabulary over-reach declined, no all-self-referential
      group to dismiss; (4) the mint is a genuine transferable SQL lesson.
    - **What it leaves standing.** (a) *Weak transfer:* the revisit passes (5–6)
      did **not** improve over first sight — the admitted lesson (schema
      inspection) retrieves but does not fix the *logical* SQL failures
      (aggregation, coded values) that actually recur; the deeper conventions were
      not the ones admitted (echoes item 49). (b) *Latch scope:* D-0001 latches on
      generic tool terms (`file-tool`, `http-tool` — spurious for SQL —
      `shell-tool`, `tool-budget`) with no SQL-specific hook, item 39/49's
      retrieval-scope concern (it retrieved anyway via tool-shape overlap). (c) the
      run converged on one strong lesson, not several distinct conventions.
    - **Only completed because of the API-hardening (decision 102):** the first
      attempt crashed at pass 3 on a Weave flush/pairing-timeout (`None` summary →
      `facts_from` AttributeError); the hardened rerun ran all six passes with no
      retries or stops. The **experiment-runner** skill now carries the
      live-monitoring grep and the store sanity-check inspector
      (`.claude/skills/experiment-runner/inspect_store.py`) used here.
    - **Cost, and an offload in progress (not on `main`).** Measured per attached
      arm ≈ **$0.5–1.3** on W&B-Inference prices (a one-off Weave usage query; the
      repo still prices nothing — item 44), of which the **teacher is ~70%**
      (DeepSeek runs every backward-pass role at ~10× the actor's per-token price).
      A `ClaudeCLI` teacher backend (billed to the claude.ai subscription, not
      per-token) is prototyped and validated at the `hgi roles try` level — valid
      role JSON, primers stripped, `apiProvider: firstParty` — with **latency
      (~2 min/call)** the open concern; a flag-gated **fused propose+examine** mode
      (fold the examiner fan into the consolidator, keep the adjudicator fresh) and
      an **effort=low** knob (`--effort` on the CLI, `reasoning_effort` on W&B) are
      being added on a worktree branch, pending a strict-arm pilot. Both trade the
      examiner's structural fresh-context independence (the host law) and reasoning
      depth for speed/cost, so they make an arm non-comparable to the split-role
      studies — hence flag-gated, non-default.

## Housekeeping

- `smoke_test.py` is the original W&B/Weave connectivity check and is not
  part of the package.
- The store's genesis articles and lenses are priced for `stub`. Before a
  hand-run on a real model, either `uv run hgi price --model <model>
  --restamp`, which keeps the store and leaves `model-pricing` warning that
  the text is still authored for `stub`, or `HGI_MODEL_ID=<model> uv run hgi
  genesis --force`, which prices a seed by writing it fresh and resets the
  store with it. A third option now keeps the store and moves the text with
  the stamp: `HGI_INFERENCE_BASE_URL=… HGI_MODEL_ID=<model> uv run hgi price
  --reauthor`, which re-authors each conditioning field against the model
  through the `reauthor` role and clears `model-pricing` (offline the stub
  answers but only marks the text; a real endpoint actually re-authors it).
  An experiment arm seeds its own store priced for its pass
  model and needs neither. The demonstration store's L-0004 product text
  predates the per-row walk; an arm seeded now carries the current text.
- `runs/smoke/`, `runs/baseline/`, `runs/baseline-precontract/`,
  `runs/probe/` and `runs/world/` on this machine are the 2026-09-12 runs;
  they are ignored by git. The baseline-precontract arms are the only
  record of the pre-contract run.
