# HGI — an attached associative memory for agent loops

HGI attaches to an agent loop and gives a frozen model a memory that learns
between passes. The loop's typed record corpus is its learning system: a
**forward pass** reads the store into context and acts; an **oracle** scores
what happened; a **backward pass** consolidates the signal into refined
records under separation of powers. No weights change. Everything the loop
knows lives in legible text under git.

The full design is in [spec.md](spec.md). This README states what the
repository implements, how to run it, and how each sponsor surface is bound.

## Store roster

The store space is cut by decay profile and by truth-maker (spec § 4). The
implemented roster is the **case leg plus its floor**: decisions are the one
live-question store; beliefs (the world leg) and rules (the duty leg) are
declared in the specification and not yet instantiated. Every other organ
that a full cycle needs is present.

| Store | Holds | Directory |
|---|---|---|
| constitution | the always-loaded articles, hard-capped | `store/constitution/` |
| decisions | settled point decisions constraining future forks | `store/decisions/` |
| observations | anchored noticings below every admission bar | `store/observations/` |
| ledger | hypothesis-ledger entries by species (attack, coding, reality, …) | `store/ledger/` |
| fires | latches whose guard passed, each owed a disposition | `store/fires/` |
| dispositions | use-time verdict per consulted record per pass | `store/dispositions/` |
| steers | corrections with credit assignment | `store/steers/` |
| sessions | one record per pass with its carry-forward | `store/sessions/` |
| proposals | the pre-admission tier: drafts with a `uid` and a recyclable `name` | `store/proposals/` |
| queue | proposals whose verdict is `escalate(<why>)`, awaiting a human | `store/queue/` |
| registry | closed vocabularies, ports, bars, the constitution cap, the lens register, id counters | `store/registry/` |
| index | regenerated projections; never hand-edited | `store/index/` |

Traces and facts are not directories. They live in the oracle and are
referenced by anchor.

The lens register is the composition surface: each lens is a typed question
with its counterfactual, priced per model, hosted at boot, at close, or in the
examiner's dispatch. Its warrant is effect evidence derived at consolidation
from the products that reached a consumer — an observation promoted, a
contradiction settled, a claim upheld, a steer citing it — and its lifecycle
is the crystallization law: a lens whose product stops varying, or a seed no
consumer ever took from, is nominated to the adjudicator and retired on
`moot`. The examiner's four attack angles are lenses too, walked one context
per angle.

### The hypothesis ledger, by species

Every entry carries a proposer, a contradiction source and an adjudicator,
three distinct parties; the lint proves the separation on every line.

| Species | Written by | Contradicted by | Consumed by |
|---|---|---|---|
| attack | the consolidator's nomination, through the examiner fan | the examiner, one lens per context | the committer, on the adjudicator's verdict |
| reality | every observation group at the bar, before nomination | the oracle's rows the observations anchor | the noise filter: an irreducible group is dismissed, a reducible one nominated |
| currency | a revisit fire, a rotted anchor, the retirement ratio, a genesis anchor, a lens at a door, a port's miss stream, a pass's close-time contradiction | the oracle: the fire, the ratio, the instance, the pass's reading | the backward pass: a status or premise flip, a lens retired, a port widened |
| coding | an escape recurring across independent occasions | the blind coder, the candidate withheld | the vocabulary review: a term minted or declined |
| collision, forecast | nothing yet: the species are declared with their verdict vocabularies and no writer — the collision species needs an independent deriver, the forecast species the belief store | — | — |

## Sponsor stack

Each binding names the role as the invariant and the vendor as the
coordinate (spec § 9).

| Role | Sponsor surface | Binding |
|---|---|---|
| trace store, the world, the steer channel | **W&B Weave** | `@weave.op` on every model and tool call with `hgi.session`, `hgi.pass`, `hgi.role` and `hgi.records_in_context` attributes; the task suite is a `weave.Dataset`, each scorer a `weave.Scorer`, each pass a `weave.Evaluation` run; feedback on calls becomes steer records |
| the frozen model | **CoreWeave inference endpoint**, or **W&B Inference** | one OpenAI-compatible client per model, installed per role; every call records its model id; every lens records the model it was priced for |
| the consolidation analyst | **W&B ARIA** | reads the disposition and session ledgers mirrored to Weave as datasets and drafts the consolidation brief; its report URI is recorded on the consolidation session; it nominates, never verdicts |
| projections and the escalation surface | **marimo** | `dashboard2.py` renders the index, the lineage DAG, the detection matrix and the escalation queue live from the demonstration store or any experiment arm's, overlays every arm of an experiment on one chart, charts a stream arm's lessons and what each pass cost, pulls every call's tokens and latency from Weave on request, and writes only through `hgi` commands |
| the blind second coder, the guard evaluator | **TypeSafe AI System1** | groups observations by the convention each turned on — the open `convention` axis, distinct from the `work-shape` hook vocabulary — proposing clusters over the raw `happened` without the consolidator's candidate labels; falls back to a second, separately prompted frozen-model context when the vendor is not configured |

## The demonstration and its acceptance bar

The run of spec § 14 is in the store and in the Weave project
[`slavazinevich-worldvue/hgi`](https://wandb.ai/slavazinevich-worldvue/hgi/weave):
six passes with the store attached, six detached (same agent, same suite
hash, no boot or close), consolidation every two passes. The frozen model
for this run is the deterministic stub (no inference endpoint was
configured), so the curve shows the loop's mechanics closing, not a model
learning; the stub applies a record only by keyword, exactly as documented
in `suite/agent.py`. The same run on a real model is
`experiments/baseline.toml` (see [Experiments](#experiments)).

### The curve — `task_pass_rate` over the same suite hash

| pass | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| memory attached | 0.50 | 0.50 | 0.67 | 0.67 | 1.00 | 1.00 |
| detached (ablation) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |

What moved it: the first consolidation (after pass 2) admitted D-0001
(*errors that wrap a failed tool call carry the underlying cause*) and
D-0002 (*under a call budget, independent calls are issued as one batched
call*) from two independent observations each. Passes 3–4 applied both;
the budget task passed, the faulted HTTP tasks named their cause and still
failed. The second consolidation read that as a payload fault — D-0001
recalled, applied, and the oracle still flat — and admitted D-0003 (*a
transient tool failure is retried once before it is reported, and the report
carries the cause*), superseding D-0001. Passes 5–6 pass every task.

### Acceptance, row by row

| Row | Holds | Evidence |
|---|---|---|
| 1. Curve, both runs, same suite hash | yes | the table above; `store/sessions/S-0001…S-0012.json`, each with its Weave evaluation URI |
| 2. One full chain observation → decision → rule | partly | observation → decision → successor decision exists (`hgi lineage D-0003`: `O-0001 → D-0001 → D-0003`), each admission's ledger entry, attack and verdict joinable to Weave call URIs; the rule tier is not instantiated in this roster |
| 3. One retirement on telemetry | yes | D-0001 superseded by D-0003; the nominating evidence is the credit table on K-0002 (applied ÷ considered 1.0, `task_pass_rate` on its applied tasks 0.0 → 0.0) and steer T-0001 |
| 4. Dispositions complete; no fire owed to the working pass undischarged | yes | every consulted record in every attached pass has a `U-` record; `store/index/fires.json` is empty |
| 5. Calibration over four settled beliefs | no | the belief store is not instantiated in this roster |
| 6. Floor green; projections equal regeneration | yes | `hgi lint` is green with fifteen warnings, all `genesis-anchor`: the seven genesis articles and the eight genesis lenses passed three consolidation passes without earning an anchor and are due for eviction, retirement or anchoring; every counterfactual's anchor resolves |
| 7. Matrix populated: a steer cell and a system-catches cell | yes | `store/index/matrix.json`: one event in `system-misses/oracle-catches` (T-0001), six in `system-catches/none-catches` (applied dispositions on passing tasks); the true-miss cell is empty because passes 1 and 2 filed an observation from every failed row — a floor, not a clean bill |
| 8. Roles separate on every ledger entry | yes | H-0001…H-0003 carry a consolidator, an examiner and an adjudicator call, three distinct Weave calls with distinct `hgi.role` attributes |

### What the demonstration does not show

Transfer to a second task family; behaviour under a model swap; the lens
telemetry; a rule enrolling or a floor growing; a belief settling; anything
about rates — every count is a floor from one run. And, because the frozen
model was the stub, nothing about whether a model conditioned on these
records would apply them.

## Running

```bash
uv sync
cp .env.example .env   # fill in the inference endpoint; leave HGI_WEAVE_PROJECT empty to run untraced
uv run hgi --help
```

Every `hgi` command reads `./.env` into its environment before it runs, and
so does the dashboard; `$HGI_ENV_FILE` names another file. A variable
already exported wins over the file, and a variable left blank in the file
reads as unset — which is how a surface is turned off: no inference endpoint
is the stub model, no `HGI_WEAVE_PROJECT` is an untraced run.

Without an inference endpoint the frozen model is replaced by a
deterministic stub, so the whole loop — boot, evaluate, close, consolidate —
runs offline and the acceptance tests run under `uv run pytest`.

On Windows PowerShell, enable UTF-8 for the store's Unicode text before running
commands or tests:

```powershell
$env:PYTHONUTF8 = "1"
uv sync --locked
uv run hgi --help
uv run pytest
uv run marimo run dashboard2.py
```

For an offline stub run, leave `HGI_INFERENCE_BASE_URL` and
`HGI_WEAVE_PROJECT` unset (or blank in `.env`).

## Commands

```
hgi boot        --session S-nnnn --pass n   # assemble context; print the consultation plan
hgi evaluate    --session S-nnnn            # run the oracle; write facts; emit fires
hgi close       --session S-nnnn            # dispositions, observations, steers, proposals, session record
hgi consolidate                             # the backward pass over the ledgers
hgi lint                                    # the floor
hgi index                                   # regenerate projections
hgi price       --model <id>                # the size of a model swap over the conditioning records
hgi lens-battery                            # the lens battery and the seeded controls; lens telemetry and index/controls.json
hgi lineage     D-0007                      # the admitting commit, and the path query over the lineage DAG
hgi suite       show | tasks | fetch <fam>  # the task suite in scope; transcribe a dataset family
hgi experiment  evolution experiments/x.toml # a stream experiment's evolution log, per arm and paired
hgi roles       try <request> --store <arm> # one role request against a copy of a store; how the reply parsed
hgi consult     --problem "<the work>"      # the store read from outside the loop: latch, then project the payload
```

Every command that writes ends in a commit whose message names the record
ids it admitted, flipped or retired, which is what makes the admitting
commit derivable: a record carries no hash of the commit that admitted it,
so `hgi lineage` reads it back as the oldest commit naming the id.
`./demo.sh` runs the whole demonstration; `uv run marimo run dashboard2.py`
opens the projection surface and the escalation queue; `uv run hgi mirror`
publishes the ledgers to Weave for the analyst.

Every lens, article and accepted decision records the frozen model its text
was authored against, and a model swap re-prices all of them in both
directions. `hgi price` names what a swap costs; `hgi price --restamp` moves
the stamp without claiming the text moved with it, keeping
`priced_for.authored_for` at the model that authored it, so the
`model-pricing` check goes on warning until the text is re-authored.

### Consulting the store from outside the loop

The loop's read is the boot: a model classifies the work, the hook-major
index matches it, a guard evaluator decides each fire. An agent that is not
the pass — a coding assistant with a problem, a sibling project — has the
same store and none of that machinery, and `hgi consult` is its read. It is
read-only and two-staged, the split being the settlement test: bare, it
prints the **surface** — per accepted decision the hook prose, the
registered terms its consultation latch keys on, the exclusions, the stakes,
the scopes and the watch, with a superseded record as a tombstone pointing
at its successor — and never the decision sentence, which a reader could
obey without opening the record. Named ids, or a latch, **project** the
payload: `--terms http-tool,tool-budget` routes registered terms through the
hook-major index exactly as the boot does and refuses an unregistered one
with the registry listed; `--problem "<the work>"` infers the terms the
prose names and runs the boot's lexical nominator over hook prose, each hit
marked as nominated since no guard ran, with an exclusion the problem
contains flagged for the reader. Records that share a hook with no lineage
edge print as co-applying. Nothing latched prints the surface for the
reader's own match. `--json` returns the structure; `--all` every accepted
payload; `--articles` adds the constitution. Nothing under the store
changes: no session, no disposition, no commit, no regenerated projection.

The procedure an agent follows — scan, latch, project, apply or dispose,
report provenance — is the project skill `consult-decisions`
(`.claude/skills/consult-decisions/SKILL.md`), which carries the invocation
and the framing and restates no record.

## The backward pass

`hgi consolidate` runs every *k* passes and on any fire owed to it. Each leg
is a nominator; every verdict is the adjudicator's, in its own context, and
the committer alone writes. In order:

| Leg | Nominates on | Executes as |
|---|---|---|
| triage | every observation group at the independence bar, with the rows its anchors name | the adjudicator classifies the recurrence `reducible` (a duty the loop missed) or `irreducible` (nothing a record could have prevented) on a `reality` entry; an irreducible group is dismissed with a pointer to the entry and leaves the brief before any slot can update on it |
| transcription | the window's price-zero happenstance floor: the mechanically-evaluable `happened` of the grouped observations and the `failure-unelicited` markers | transcribed straight to the fact layer with no adjudication — the one machine-write past the owner gate, legal exactly because the price was zero and evaluation is mechanical — and recorded on the pass record (`Consolidation.transcribed`); a `happened` a machine cannot mechanically evaluate is surfaced to the human in the brief, never auto-written, and `turned_on` (the inference) is never transcribed |
| nominations | the brief: observations grouped by the blind coder's convention clusters (the open `convention` axis, each cluster a minted `other(<what>)` label) under the independence bar, ordered variance-ripe-first and annotated with a `ripeness` score (`independence × (1 − world_content_variance) × (1 − presentation_universality)`) so a cluster naming one recurrent world-token on a non-universal presentation across independent passes is authored first, and a high-independence-but-universal cluster sinks — the machine ranks and annotates, it never authors; `precision` (fired-but-not-applicable dominating a record's considered count at the bar `precision.not_applicable_over_considered_above`, with the dispositions' notes from independent passes → counterfactual-edit growing `not_this` by the presentations they name); `fusion` (dispositions bimodal across matched sub-shapes → split); `convergence` (identical hooks applied together → fold); `structural_zero` (a record no registered hook reaches → hook-edit); `recall` (a record the boot lens probed for unconsulted, or a steer indicting activation → hook-edit re-keying on what was presented) | a draft per nomination through attack and verdict; a `hook-edit` or `counterfactual-edit` is a successor derived from the one record it supersedes; a leaf names `split_from`, a fold `folded_from`, and admission writes the DAG move with reciprocal pointers; a nomination at a rung this roster has no operator for (`adoption-row`, `rule-enrollment`, `floor`, `article`) is carried as a decision — the cheapest available home — with the rung it meant recorded on the nomination and stamped on the admitted record as `admission.displaced_from`, so a later tier can re-home it |
| attack | the draft, verbatim, after the code's two readings: the distinct-session count of its evidence against the bar (`warrant:independence`, the lint's `independence` floor check, which the committer refuses on) and the direction of its revisit watch (`warrant:watch-direction`: a watch that fires on success is dropped from the draft, which is admitted unwatched, the drop recorded on the claim) — both join the attack first, with no lens and no call | the examiner fan: one call per live examiner-hosted lens (premise kill, abstraction; L-0005 and L-0008 are seeded retired, their questions crystallized into the code's readings), each contributing only the claims of its own class, an examiner claim on a mechanical class that contradicts the code's reading discarded; a landed `payload:abstraction` with no premise kill beside it sends the draft back to the consolidator once to promote the payload to the transferable shape with the instances kept as anchors, and the abstraction angle is walked again over the promoted draft; the adjudicator, never an angle, joins them |
| verdict | the draft the attack was walked over, the attack, the oracle's evidence, the bars | one token from the closed vocabulary: `admit`; `admit-amended(<amendment>)`, the committer admitting the amended payload; `decline(<why>)` on an upheld premise kill only — a decline with no landed `premise:` claim is overridden to an admit, amended where an amendment was offered, the attack still named on the entry (`survived-with-attack-named`) and the override on its outcome; `defer(<until>)`; `escalate(<why>)`. The floor runs before any admission |
| deferrals | a `defer(<until>)` verdict | the condition becomes a latch on the draft — a watch predicate the oracle's next runs fire, or passes to wait — and the fire, owed to the backward pass, re-adjudicates the draft in fresh contexts |
| fires owed | revisit latches whose predicate held; deferral latches | a decision's by a currency verdict on its warrant; a draft's by re-adjudication; the disposition and any flip land in one commit. A fire owed to the working pass instead is discharged by that pass at close, or the close is refused |
| pending contradictions | a `currency` entry a pass filed at close (the close lens named a premise or hook the pass made false), still pending | the adjudicator re-checks the warrant against the finding; the verdict lands on a new entry citing the pending one, and a `reversed` flips the premise |
| credit | the task-level credit table, each fraction with the counts it is computed from | oracle-attributed steers, credit assigned by the adjudicator |
| retirement | applied ÷ considered under the record's retirement guard over the window; or a record accepted before the window opened that no pass considered across the whole of it — the domain no longer entered | mootness by the adjudicator's killer-item check, through the same `currency` request with the window's evidence; a never-considered record is kept unless its `moot_when` condition is met, and nothing retires by count alone |
| genesis anchoring | a seed article with no anchor | the consolidator names an instance from the ledgers, the adjudicator says whether it exemplifies the article, the committer appends the anchor; past the deadline in the bars an article still unanchored is evicted |
| lenses | a lens's products that reached a consumer; a seed lens unanchored past the deadline; a product that stopped varying over the review window | anchors are derived and appended to the lens's warrant; a lens at a door — genesis-deadline or variance-collapse — goes to the adjudicator, and `moot` retires it (kept in the register as evidence, walked by nothing) |
| vocabulary | the same `other(<what>)` from independent occasions — a pass's work-shape, a latch's key-space, a species' verdict | revision routing first reads the pile against the axis's members: a missing peer or a partition of one member is horizontal and proceeds; a distinction that cross-cuts several members is vertical — the axis conflated two questions — and is surfaced, never minted. Then the blind coder recodes the presentations with the candidate withheld, the adjudicator admits or declines, the registry grows in place |
| ports | a latch type admitted off its port declaration on a warrant by independent records | the adjudicator admits or declines widening the mark from `forbidden` to `optional`; the port table is corrected in place |
| propagation | a wiring latch whose neighbour left the status it last saw — a tombstone's successor, a warrant's cited record | a mechanical check in the same commit; a rotted anchor goes to the adjudicator as a currency question |

The projections under `store/index/` show each leg's live state: `hooks`,
`summaries` (each record's watch, or `unwatched` when no world-state latch
can send its warrant back), `triggers`, `deferred`, `wiring`, `fires`,
`competence` (applied, not-applicable, guard-failed and off-map counts per
record over the window, and the ratio), `fusion`, `convergence`,
`structural_zero`, `recall` (the should-have-fired stream: boot-lens probes
and activation steers per record), `attacker` (attacker precision per
angle, the landings the adjudicator upheld or overruled, and the
should-have-been-caught-by stream — every count a floor), `lineage`,
`matrix` (steers, fires and applied dispositions by cell, and in the
`system-misses/none-catches` cell the rows nothing caught: a task failed in
a closed attached pass that consulted no record and filed no observation
from the row, keyed `session/task` — a floor, since the store cannot see a
miss the world has not yet voted on). One more file sits beside them and is
not a projection: `controls.json`, the blind coder's seeded-control
telemetry, written by `hgi lens-battery` and regenerated by nothing.

### Telemetry

Every instrument reports a floor, never a rate. `hgi lens-battery` runs the
three that are scored as traced Weave evaluations, each item walked in its
own context, and writes what they find:

| Instrument | Plants | Scores | Written to |
|---|---|---|---|
| the lens battery | two decoys and two genuine signals per close lens (L-0003, L-0004) | `decoy_rejection` (filed nothing for the plant) and `signal_caught`; `answer_variance` across the battery | `telemetry` on each close lens in `store/registry/lenses.json` |
| the examiner control | per live examiner-hosted lens (L-0006, L-0007), a draft carrying a fault of that lens's class and a plausible draft with none, attacked through the fan one angle at a time under a fixed evidence pack | the landing on the fault as `signal_caught`, the non-landing on the clean draft as `decoy_rejection` | `telemetry` on each examiner lens in the same register |
| the coder control | an observation of a known convention, and one that fits no term | whether the blind coder returns the convention term, and whether it escapes with `other(<what>)` on the misfit | `store/index/controls.json` |

The rest are projections: the detection matrix (with the true-miss floor),
`competence` (with the not-applicable count), `attacker`, `recall` and
`structural_zero` above. The committed demonstration store carries the
battery and the controls at `design-stage` and no `controls.json`: on the
stub every control passes by the stub's own keyword rules, which measures
the mechanism and not a model, so the run that records telemetry is left to
a traced one on a real endpoint.

## The world

The suite the loop is judged on is composed from task families under one
fault profile, and pinned by a hash over every task's presentation, its
world (the files and routes it runs in) and the profile (spec § 14.1). A
family is hand-written or transcribed once from a public dataset into
`suite/data/`, so a run needs no network:

| Family | Tasks | Source | What it grades |
|---|---|---|---|
| `genesis` | 6 | hand-written | the § 14 demonstration: HTTP faults, a shell budget, a file report, a schema |
| `conventions` | 10 | hand-written | facts of this world a model meets on first contact: files with no trailing newline (`wc -l` undercounts), a paging API, an API moved under `/v2`, quoted CSV commas, a byte order mark — each proven to fail naively and pass when known |
| `mbpp` | 257 | [google-research-datasets/mbpp](https://huggingface.co/datasets/google-research-datasets/mbpp), sanitized test split, CC-BY-4.0 | write `solution.py`, run `tests.py` under three shell calls; the dataset's own asserts are the hidden check |
| `tables` | 100 | [TableBench](https://huggingface.co/datasets/Multilingual-Multimodal-NLP/TableBench), Apache-2.0, the scalar-answer rows | one question over `table.csv`, graded by a normalizer with tolerance |
| `api` | 100 | the same TableBench rows, odd positions | the same questions through a paged JSON API under a budget of pages plus two |
| `transfer` | 6 | hand-written | the `conventions` conventions re-dressed — the same no-trailing-newline files, paging API and `/v2` move worn as different file names, a different API surface and different endpoints — so a record whose hook reads the convention scores here and one that memorised a path or a filename does not |
| `curriculum` | 84 | generated (`suite/families/curriculum.py`) | seven lessons of the world in twelve clothes each — the five `conventions` lessons, an export that ends with a `TOTAL` row, a route under `/secure` that answers 401 until the token in `token.txt` is passed — each clothing a different instance from a seeded generator, disjoint from the hand-written families' names and routes, budgeted with one call to spare for discovering the convention; the pool a stream experiment deals from |
| `curriculum-strict` | 84 | generated, the same clothes | the same tasks budgeted at exactly the knowing policy's calls, so the convention costs a call the budget does not hold: only a pass that already knows it — from the store, or from the model — stays within budget |
| `text2sql` | 10 | [birdsql/bird_mini_dev](https://huggingface.co/datasets/birdsql/bird_mini_dev), `financial` subset, CC-BY-SA-4.0, over a pinned reduced `financial.sqlite` | one BIRD question over a SQLite database shipped into the working directory; the agent inspects the schema with the shell tool and returns a `SELECT`, graded by re-executing it and comparing its rows to the gold query's rows (a set/row comparison, never a string one — the gold SQL is the grading key, re-executed, never shown); the transferable convention is the schema's own SQLite-dialect quirks (text dates via `STRFTIME`, a ratio needing `CAST` or it integer-divides to a wrong-but-running answer, coded statuses, a reserved-word `order`) |
| `text2sql-strict` | 10 | the same questions and database | budgeted at exactly the knowing floor of one shell call, so discovering the schema convention costs a call the budget does not hold: only a pass that already knows it — from the store, or from the model — stays within budget |
| `text2sql-holdout` | 6 | the same database, a disjoint group of questions | held-out questions whose templates are disjoint from `text2sql`'s while their schema conventions are shared, so a record admitted on the graded group is measured for transfer rather than re-learned |
| `incidents` | 36 | `hearth/tenant-incident` scenarios, hand-authored, worn four ways | nine incident bundles in four clothes each — one brief per bundle, the operator's readings served at `/readings/<name>` under a budget of the cause readings plus one: the class must be named and a cause reading cited, and citing the bundle's decoy reading — the loud one a naive read reaches for — fails the task however right the class is; dressing 0 is the bundle as authored and dressings 1–3 rename every reading and service, shift the host ports by a thousand each and the clock by three hours each, pairwise disjoint, so a record that learned *the loud reading is the decoy* scores on the next clothing and one that memorised `pool-debug` or `orders` scores on none; each bundle's lesson is the shape of its decoy (`decoy-dependency`, `decoy-saturation`, `decoy-state`) and its `knowing` floor the count of its cause readings |
| `incidents-strict` | 36 | the same four clothes of the same nine bundles | the same tasks budgeted at exactly the cause readings, so the one wrong turn costs a call the budget does not hold: only a pass that already knows which readings carry the cause — from the store, or from the model — stays within budget |

### Lessons

A task that turns on a convention names it as its **lesson**
(`suite/lessons.py`), and every lesson is tiered by how its failure shows
in the trace: *loud* (the tool error names the convention — the 410 naming
`/v2`, the 401 naming the token file, the parse error on the byte order
mark), *visible* (the failure is silent but the convention is in the tool
output the pass read — a `next` field on the page it stopped at, a quoted
comma or a footer row in the file it counted), *invisible* (nothing in the
trace shows it — a file with no trailing newline reads the same as one
with). Every task in a lesson family carries its naive first-contact policy
as its scripted policy, so the **naive outcome** — the answer or the error
a policy that does not know the lesson produces — is derived by running it
against a fault-free world. A failed row whose result equals the naive
outcome, or whose error (or any tool error in its trace) is of the naive
error's class, is a **naive-shape** failure: the lesson missed the way first
contact misses it, decided by the task's own construction and no judge. The `incidents` lessons are tiered *visible* and keyed on the shape of the bundle's decoy readings, the one thing the four clothes of a bundle share.

### Quality

Correctness saturates where a model passes a lesson at first contact, and
the memory's value is then the cost, not the pass: a pass that knows a
convention spends the knowing policy's calls, and its method carries; one
that discovers it spends the discovery, and its method may fit the
instance. Every curriculum task declares the knowing policy's calls
(`Task.knowing`) and carries a **metamorphic twin** (`Task.twin`) — the
same names, columns and routes over different data, from a second seed,
with its own gold — and every row records its shell commands and model
turns. Three scorers grade a solution's quality beside its correctness,
each a success rate in `[0, 1]` like the rest:

| Series | Grades | Evaluable on |
|---|---|---|
| `solution_economy` | the knowing policy's calls over the calls the pass spent on budgeted tools; zero on a failed row | a task with a knowing floor |
| `turn_economy` | the same over model turns, the floor being one turn per knowing call and one to answer | a task with a knowing floor and a row that records turns |
| `method_transfer` | the pass's last shell command replayed in the twin world: its last line of output names the twin's gold, or not | a passed row of a task with a twin whose pass issued a shell command |

A method that transfers reads the convention; one that fits the instance —
or a pass that read the file and computed in its head, leaving no
replayable command — does not.

The fault profile says how many leading HTTP calls of a faulted task fail,
whether HTTP calls are budgeted, and whether shell output truncates. An
experiment file carries the suite as `[suite]` (families, a seeded sample
size, the profile), deep-merged per arm; a hand-run names a TOML with the
same table in `$HGI_SUITE`. `hgi suite show` prints the resolved suite and
its hash. The deterministic stub runs only the families that carry scripted
policies (`genesis`, and `conventions` and `transfer` naively); every other
family fails on it honestly.

## Experiments

An experiment file fixes every per-run decision outside the run: the models
it may use, which role runs on which, how many rounds and how many passes a
round holds (the consolidation cadence, written into the arm's bars),
whether the memory is attached or detached, any bar overridden, which suite
it runs on, and how many tasks the oracle evaluates at once. `hgi experiment run` gives each arm a
fresh store under `runs/<experiment>/<arm>/`, in a git repository of its own,
seeds it priced for the arm's pass model, and drives the same commands
`demo.sh` drives through the command surface; `arm.json` beside the store
records what the arm resolved to and its curve. The format is documented in
`hgi/experiment.py`.

```
hgi experiment show   experiments/baseline.toml     # every arm's resolved plan; nothing touched
hgi experiment run    experiments/baseline.toml     # every arm, or --arm <name> (repeatable); --force reruns
hgi experiment report experiments/baseline.toml     # the curves, read back from the arm stores
hgi experiment models                                # the ids the endpoint serves (W&B Inference by default)
```

| File | Arms | Question |
|---|---|---|
| `experiments/smoke.toml` | stub, attached and detached, 1 round × 2 | does the runner close the loop; the tests run it |
| `experiments/baseline.toml` | `openai/gpt-oss-120b`, attached and detached, 3 × 2 | the § 14 run on a real frozen model |
| `experiments/model-sweep.toml` | `gpt-oss-20b`, `gpt-oss-120b`, `Qwen3.6-35B-A3B`, each attached and detached, plus the roles split: the small model acts, the large one consolidates, examines and adjudicates | behaviour under a model swap (§ 14.4); whether separation of powers lets a weak actor learn from a strong judge |
| `experiments/cadence.toml` | `gpt-oss-120b` attached, consolidating every 1, 2 and 3 passes over six | how often to consolidate |
| `experiments/probe.toml` | `gpt-oss-120b` attached, 2 × 2, the hand-written families | every role request on a real model end to end; the reply log is the evidence |
| `experiments/world.toml` | `gpt-oss-120b` and `gpt-oss-20b` attached, `gpt-oss-120b` detached, the split roles; 52 tasks from five families, first two HTTP calls faulted | a world with conventions the model cannot already know: does the attached curve separate |
| `experiments/transfer.toml` | `gpt-oss-120b` attached and detached, `gpt-oss-20b` attached; `genesis`, `conventions`, `api` and `transfer`, first two HTTP calls faulted | a convention held twice in different clothes: does a record admitted on one family score on the same convention re-dressed as another |
| `experiments/stream.toml` | `gpt-oss-120b` attached and detached, `gpt-oss-20b` attached, on the `curriculum` pool; `gpt-oss-120b` attached and detached on `curriculum-strict`; ten batches of eight, consolidation every two, batches 1 and 2 revisited | the stream: first-sight performance on unseen tasks as the store grows, paired per batch and per lesson, with the same-shape recurrence per lesson; on the strict pool, whether the memory saves the discovery call |
| `experiments/economy.toml` | `gpt-oss-120b` attached and detached on the `curriculum` pool, ten batches of eight, a different deal | the stream graded on quality: economy of calls and turns, and method transfer to the twin world, where correctness saturates |
| `experiments/incidents.toml` | three actors on the `incidents` pool, each attached against its own detached ablation — `gpt-oss-120b`, `Llama-3.3-70B-Instruct` as the same-class peer, and `gpt-oss-20b` at `reasoning_effort = "low"` as the weak actor — plus the weak actor with `DeepSeek-V4-Pro` on the whole backward pass; the 36 tasks as a stream, twelve batches of three, consolidation every two, batches 1 and 2 revisited, faults off | first-sight diagnosis of unseen bundles balanced over the three decoy shapes, the four clothes of a scenario dealt into the same pool so a re-dressed bundle arrives after its source; `solution_economy` here is the step count — the cause readings over the calls the walk spent; the sweep pairs each actor against itself, and the seventh arm asks what a strong judge teaches a weak actor |
| `experiments/stream-probe.toml` | `gpt-oss-120b` attached and detached, two batches of five | a stream arm end to end on the endpoint |
| `experiments/stream-smoke.toml` | stub, attached and detached, four batches of four | the stream runner end to end offline; the tests run it |
| `experiments/incidents-smoke.toml` | stub, attached and detached on `incidents`, attached on `incidents-strict`, twelve batches of three | the incidents stream end to end offline over the three decoy shapes, the naive walk dying on the budget on both pools; the tests run it |
| `experiments/reasoning-core.toml` | `Qwen3.6-35B-A3B` attached and detached, `gpt-oss-20b` attached, the backward pass on `DeepSeek-V4-Pro`, on the `reasoning-core` pool; the Qwen actor attached and detached on `reasoning-core-strict`; 24 tasks as six batches of four, consolidation every two, batches 1 and 2 revisited | first-sight produce-and-verify on unseen regexes and grammars: whether a method — verify with the checker before answering — transfers as a record; on the strict pool, whether it saves the repair call |
| `experiments/text2sql.toml` | `gpt-oss-120b` attached and detached, `gpt-oss-20b` attached, the backward pass on `DeepSeek-V4-Pro`, on the `text2sql` and `text2sql-holdout` pools; `gpt-oss-120b` attached and detached on `text2sql-strict`; 16 questions as eight batches of two, consolidation every two, batches 1 and 2 revisited | first-sight text-to-SQL over one schema: whether the database's own conventions (TEXT dates, integer division, coded literals, a reserved column name) transfer as records to unseen questions; on the strict pool, whether the store saves the schema-discovery call |

**Seeded arms.** Each of `stream`, `transfer`, `world`, `incidents`,
`reasoning-core` and `text2sql` also carries `*-seeded` arms: the same arm
started from a hand-authored mature store under `experiments/seeds/<world>/`
(`seed = "<world>"` on the arm, injected before pass 1 by `hgi/seeds.py`)
instead of the empty genesis store. Seeded against attached against detached
on the same batches reads what the injected decisions buy, what learning them
costs, and — on the strict pools — whether an injected record saves the call
the budget does not hold; `experiments/seeds/README.md` is the design and
`experiments/seeds/AUTHORING.md` the rule a seed follows.

The shipped files run on W&B Inference (`https://api.inference.wandb.ai/v1`):
the key is `$WANDB_API_KEY` or the netrc entry `wandb login` wrote, and the
endpoint refuses a request with no `entity/project` to attribute usage to, so
`WANDB_ENTITY` must be set and the experiment names its Weave project. A
CoreWeave endpoint is a model entry with its own `base_url` and
`api_key_env`. Arms of one experiment trace into one Weave project, each call
carrying `hgi.experiment` and `hgi.arm`, each evaluation named by its arm.
The dashboard's store picker lists every arm; choosing one shows its
projections, its escalation queue and every arm of its experiment on one
chart, refreshing while the arm runs. Every chart is an altair chart
(hover a mark for the row behind it): the score curve over every arm with
the chosen arm at full ink and a rule where it admitted a record; the
solution-quality and cost-of-a-pass series as small multiples, one panel a
measure; a stream arm's lessons as a lesson × pass heatmap and a per-lesson
bar per arm; the competence projection as one stacked bar a record. The
Compute tab reads the trace store on request: every model call carries its
tokens and latency in Weave with `hgi.arm`, `hgi.pass` and `hgi.role` as
attributes, so one filtered query charts tokens and seconds per pass by
role and by the model that served the call, the backward pass charged to
the pass it followed. A retrofitted arm (`runs/retrofit/<name>`, made by
`hgi experiment retrofit`) is listed like any arm — a directory no
experiment file declares is read as an experiment from its `arm.json`
files — and its Retrofit tab charts the snapshots the retrofit writes after
every pass as they land: the observation pile by shape, one panel a state,
and the store's counts pass by pass; a button reads the original store
beside it from the source arm's history and names where the two part.

### The stream

A suite experiment runs the same tasks every pass, so its curve measures
whether the store learned *those* tasks. A **stream** experiment
(`suite/stream.py`, the `[stream]` table of an arm) deals a pool into
batches balanced over lessons and meets a new batch every pass: pass *k*
boots with what the store holds, evaluates batch *k* **at first sight** —
nothing in the store was learned on those tasks — closes on it, and
consolidates at each round's end. Every batch is a validation set once and
a training set afterwards, and the curve is first-sight performance on
unseen tasks as the store grows: the shape a knowledge base is asked to
improve, where the work that arrives is always new and the conventions
recur. A detached arm draws the same batches with no store, so the
comparison is paired per batch and per lesson; `revisit` names batches the
attached arm meets again after the stream, which measures retention on
seen tasks against transfer to unseen ones.

The **evolution log** (`hgi/evolution.py`) is derived from the arm's store
after the run and written beside it as `evolution.json` and `evolution.md`,
with the experiment's paired report at `runs/<experiment>/evolution.md`
(`hgi experiment evolution`): per pass, each row's symptom (`pass`,
`naive`, `wrong`, `error:<class>`), the records in context and which
lessons their text mentions (a keyword heuristic, logged as one), the
observations filed and what the consolidation after the pass admitted,
declined, retired or dismissed; per lesson, the first-sight series as a
grid of symbols, and the naive-shape failures before and after the first
pass that had a record mentioning the lesson in context — the same-shape
recurrence the memory exists to stop; and beside every pass rate the
quality means, `economy / turns / transfer` (economy derived from the
row's call counts and the task's floor, so it reads on runs scored before
the series existed). Every count is a floor from one run.

### The stream on `openai/gpt-oss-120b`

`experiments/stream.toml`, run on 2026-09-13 over W&B Inference from the
tree at 67c9ff0 with the close fix of 1707b72: the 84 `curriculum` tasks
dealt by seed 0 into ten batches of eight, a consolidation every two
batches, batches 1 and 2 met again after the stream; `openai/gpt-oss-120b`
attached and detached and `openai/gpt-oss-20b` attached on the plain pool,
`gpt-oss-120b` attached and detached on `curriculum-strict`; the detached
arms drawn alone after the attached ones. The logs are derived from the arm
stores (`experiments/results/stream/`), traced to
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave).

First sight per batch, every arm on the same eight tasks:

| batch | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | stream |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 120b attached | 0.25 | 0.50 | 0.38 | 0.38 | 0.25 | 0.62 | 0.50 | 0.62 | 0.50 | 0.62 | 0.46 |
| 120b detached | 0.62 | 0.75 | 0.38 | 0.50 | 0.38 | 0.50 | 0.38 | 0.62 | 0.50 | 0.75 | 0.54 |
| 20b attached | 0.62 | 0.38 | 0.62 | 0.75 | 0.50 | 0.75 | 0.50 | 0.50 | 0.50 | 0.62 | 0.57 |
| 120b strict | 0.38 | 0.25 | 0.50 | 0.25 | 0.25 | 0.38 | 0.38 | 0.38 | 0.25 | 0.38 | 0.34 |
| 120b strict detached | 0.25 | 0.38 | 0.25 | 0.25 | 0.25 | 0.38 | 0.25 | 0.25 | 0.50 | 0.50 | 0.33 |
| in context, 120b attached | — | — | — | — | — | — | D-0001 | — | D-0001 | D-0001 | |
| in context, 120b strict | — | — | D-0001 | D-0001 | D-0001 | D-0001 | D-0001 D-0002 | D-0001 D-0002 | D-0001 D-0002 | D-0001 D-0002 | |

First sight per lesson, with the naive-shape failures of the strict arm
before and after the first pass that had a record mentioning the lesson in
context (no record of the plain attached arm mentions a lesson):

| lesson | tier | 120b attached | 120b detached | 20b attached | 120b strict | strict detached | strict: naive before / after first mention |
|---|---|---|---|---|---|---|---|
| bom | loud | 1.00 (11/11) | 1.00 (11/11) | 1.00 (11/11) | 1.00 (11/11) | 1.00 (11/11) | 0/11 / — |
| moved-v2 | loud | 0.25 (3/12) | 0.50 (6/12) | 1.00 (12/12) | 0.58 (7/12) | 0.00 (0/12) | 3/3 / 0/9 (pass 3) |
| token-route | loud | 0.82 (9/11) | 1.00 (11/11) | 1.00 (11/11) | 0.00 (0/11) | 0.00 (0/11) | 2/2 / 0/9 (pass 3) |
| csv-quoted | visible | 0.67 (8/12) | 0.58 (7/12) | 0.67 (8/12) | 0.67 (8/12) | 0.50 (6/12) | 4/12 / — |
| footer-row | visible | 0.00 (0/11) | 0.00 (0/11) | 0.00 (0/11) | 0.00 (0/11) | 0.00 (0/11) | 10/11 / — |
| paged-api | visible | 0.50 (6/12) | 0.67 (8/12) | 0.25 (3/12) | 0.08 (1/12) | 0.75 (9/12) | 0/12 / — |
| trailing-newline | invisible | 0.00 (0/11) | 0.00 (0/11) | 0.09 (1/11) | 0.00 (0/11) | 0.00 (0/11) | 10/11 / — |

Revisits: the plain attached arm met batch 1 again at 0.62 (0.25 at first
sight) and batch 2 at 0.62 (0.50) with D-0001 in context — and the
detached draw of batch 1, with no store, was 0.62. The strict arm met
batch 1 again at 0.12 (0.38) and batch 2 at 0.25 (0.25) with D-0004,
D-0005 and D-0006 in context. The 20b arm: 0.75 (0.62) and 0.50 (0.38).

What was admitted, and when. The plain 120b arm filed 43 observations over
twelve passes; the blind coder shaped them into 38 groups, 20 at the
two-session bar, and the consolidator drafted 18 records: 11 were refused
at parse (an empty `not_this`, or an edit rung naming no record to
supersede), 5 were declined on the examiner's attacks (abstraction, watch
direction, a premise kill, independence), 1 was escalated, and 1 was
admitted — D-0001 after pass 6, "file-tool tasks validate the total line
count across all shard files", drafted from the trailing-newline
observations. It was consulted on five passes and applied on five rows;
the trailing-newline and footer-row rows it fired on failed with the naive
count. On pass 8 it matched lexically and failed the guard, so nothing was
in context. The strict arm filed 52, 13 groups reached the bar, 10 drafts:
6 admitted, 4 declined. D-0001 after pass 2 fused two lessons — "all HTTP
calls use versioned `/v2` endpoints and include a valid authentication
token" — with `calls to /v2 endpoints with a valid token` as its
exclusion; D-0002 after pass 6 restated the token half; D-0003 after pass 8
is the schema tautology; D-0004, D-0005 and D-0006 after pass 10 restate
D-0002 and D-0001 almost verbatim, and the fusion leg did not fold them.
Its currency review reversed D-0001's premise after pass 4 on rows where
the record applied and the route answered 404, and the record stayed
accepted. The 20b arm admitted three tautologies (wrap a None reply,
record shell usage, validate outputs) after passes 4 and 8 and retired
seven genesis lenses through the deadline door. The first run of the
strict arm, stopped at pass 7 by the close bug, had refused both lesson
drafts at parse after pass 2 and declined the versioning draft after pass
4; the rerun on the same batches admitted the fused record at its first
consolidation — admission is itself a draw.

The honest reading. On the plain pool the attached curve did not separate
from the detached one: 0.46 against 0.54 over the stream, better on two
batches, equal on three, worse on five, and the five passes that ran with
an empty store differ from the detached draws of the same batches by up to
0.37 (batch 1: 0.25 against 0.62), which is the noise of one draw of eight
tasks on this endpoint and larger than any effect in the table. No
convention was learned on the plain pool: footer-row and trailing-newline
failed every row on every arm, and the one record admitted fires on file
tasks without carrying what a file with no trailing newline does to
`wc -l`. gpt-oss-20b outscored 120b on this pool because it follows the
410's hint on every moved route where 120b reports the 410 and stops (12/12
against 3/12 and 6/12); its records are tautologies and its curve is the
model's. The strict pool did what it was built to ask: after D-0001 entered
context at pass 3, every moved-v2 row the pass called at all passed on one
HTTP call within a budget that holds no discovery call — seven rows, 0.58
against 0.00 detached, the naive shape gone from 3/3 to 0/9 — so the
memory saved the discovery call on one loud lesson. The same table shows
the cost of a record with no bound: the pass applied "all HTTP calls use
`/v2`" to paging routes and got 404s (paged-api 0.08 against 0.75
detached), and after D-0002 it made no HTTP call at all on token and
paging rows, citing the record as the cause, so token-route went from the
naive 401 to zero calls (0/11 on both arms) and the strict revisit of
batch 1 fell to 0.12. Net over the stream the strict arms tie (0.34 against
0.33): the seven rows the record won, the eight it lost. What the run
shows the mechanism doing at breadth: the close naming the convention in
its observations where the probe's did not, the coder grouping same-lesson
observations across sessions, the consolidator nominating the right
lessons in every arm — and the drafting contract, the examiner and the
adjudicator deciding which of those lessons became a record (the
carry-forward, items 25 and 32).

### The economy run on `openai/gpt-oss-120b`

`experiments/economy.toml`, run on 2026-09-13 over W&B Inference from the
tree of `claude/nervous-rubin-e8e759` and brought over with its arm stores:
the same 84 `curriculum` tasks, dealt by seed 2 into a different ten
batches of eight, a consolidation every two batches, batches 1 and 2 met
again after the stream; `openai/gpt-oss-120b` attached and detached, faults
off. It asks the stream graded on quality rather than correctness alone —
where a model passes a lesson at first contact the memory's value is the
cost, not the pass, so `solution_economy`, `turn_economy` and
`method_transfer` run beside `task_pass_rate`, paired per batch and per
lesson. The logs are derived from the arm stores
(`experiments/results/economy/`), traced to the same project as the stream,
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave).

First sight per batch, both arms on the same eight tasks, the pass rate
then `economy / turns / transfer`:

| batch | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | stream |
|---|---|---|---|---|---|---|---|---|---|---|---|
| attached | 0.50 | 0.62 | 0.38 | 0.38 | 0.50 | 0.50 | 0.50 | 0.38 | 0.62 | 0.38 | 0.47 |
| detached | 0.50 | 0.50 | 0.38 | 0.62 | 0.75 | 0.50 | 0.62 | 0.25 | 0.62 | 0.50 | 0.53 |
| attached quality | 0.26 / 0.27 / 0.00 | 0.36 / 0.38 / — | 0.21 / 0.21 / — | 0.14 / 0.17 / — | 0.17 / 0.22 / 1.00 | 0.21 / 0.24 / 1.00 | 0.21 / 0.24 / 0.00 | 0.12 / 0.13 / 0.00 | 0.36 / 0.38 / — | 0.21 / 0.21 / — | 0.23 / 0.25 / 0.40 |
| detached quality | 0.29 / 0.29 / 0.00 | 0.26 / 0.27 / 0.00 | 0.21 / 0.21 / — | 0.36 / 0.40 / — | 0.42 / 0.44 / 0.00 | 0.19 / 0.22 / 1.00 | 0.43 / 0.40 / 0.00 | 0.07 / 0.07 / — | 0.36 / 0.38 / — | 0.29 / 0.31 / — | 0.29 / 0.30 / 0.20 |
| in context, attached | — | — | — | — | — | — | — | — | — | — | |
| consolidation after | | K-0001: nothing | | K-0002: D-0001 | | K-0003: nothing | | K-0004: D-0002 | | K-0005: D-0003 | |

First sight per lesson, with the naive-shape failures of the attached arm
before and after the first pass that had a record mentioning the lesson in
context — no first-sight pass had a record in context at all, so the after
column is empty on every row:

| lesson | tier | attached | detached | attached quality | detached quality | attached: naive before / after first mention |
|---|---|---|---|---|---|---|
| bom | loud | 1.00 (11/11) | 1.00 (11/11) | — / — / — | — / — / — | 0/11 / — |
| moved-v2 | loud | 0.55 (6/11) | 0.64 (7/11) | 0.28 / 0.37 / — | 0.30 / 0.40 / — | 5/11 / — |
| token-route | loud | 0.92 (11/12) | 0.92 (11/12) | 0.45 / 0.45 / — | 0.47 / 0.47 / — | 0/12 / — |
| csv-quoted | visible | 0.45 (5/11) | 0.45 (5/11) | 0.19 / 0.22 / 0.40 | 0.22 / 0.21 / 0.20 | 6/11 / — |
| footer-row | visible | 0.00 (0/12) | 0.00 (0/12) | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 12/12 / — |
| paged-api | visible | 0.45 (5/11) | 0.73 (8/11) | 0.50 / 0.50 / — | 0.80 / 0.80 / — | 4/11 / — |
| trailing-newline | invisible | 0.00 (0/12) | 0.00 (0/12) | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 12/12 / — |

Revisits: the attached arm met batch 1 again at 0.50 (0.50 at first sight)
and batch 2 at 0.62 (0.62) with D-0003 in context, the only record the
stream left standing that the boot retrieved at all — it was applied on
twelve of the sixteen revisit rows, and on the two `moved-v2` rows, the
lesson its text mentions, both failed, one a wrong answer and one the naive
410.

What was admitted, and when. The attached arm filed 34 observations over
the ten first-sight passes and 40 over the twelve including the revisits;
the detached arm filed none, having no store to file into. K-0001 after
pass 2 shaped them into 5 groups with none at the two-session bar and
nominated nothing. K-0002 after pass 4 had 5 groups, 2 at the bar, and
admitted D-0001 from the `http-tool` group — *retry HTTP 410 Gone up to two
attempts before declaring failure*, a retry on a permanent status, which is
the lesson misread: the 410 names `/v2` and the route has moved, so no
number of attempts on the old one succeeds — and declined an
output-schema draft. K-0003 after pass 6 had 8 groups, 4 at the bar, and
admitted nothing: 2 declined, 3 refused at parse on an empty `not_this`,
1 hook-edit refused for naming no record to supersede, and D-0001,
nominated at the counterfactual-edit rung, went `moot`. K-0004 after pass 8
had 8 groups, 6 at the bar, and admitted D-0002 — *every paged query
include an `active:true` filter before counting results*, which is one
clothing's filter and not the paging convention the lesson turns on —
declined 7, saw 1 hook-edit refused at parse, and retired L-0001, L-0002
and L-0003 through the genesis-deadline door. K-0005 after pass 10 had 9
groups, 5 at the bar, and admitted D-0003 at the hook-edit rung — *a hook
that checks for HTTP 410 responses and aborts further tool calls for the
affected task* — declining 3 and seeing 1 more hook-edit refused at parse.
Six drafts refused at parse across three consolidations, and the count is
exact because every refusal is on the ledger. The detached arm's pass 10
carries the other kind of loss: `curriculum/footer_08` failed
`error:model-call`, the model having emitted a shell call whose arguments
string was not valid JSON, after which the endpoint refused the next
request outright and the model never got the turn to read the harness's
*bad tool call* answer — the row is the one `E` in that arm's footer-row
series, beside a `csv-quoted` row lost to `error:budget` on pass 8.

The honest reading. The pass rate did not separate — 0.47 (38/80) attached
against 0.53 (42/80) detached, better on two batches, equal on four, worse
on four — and the quality series could not have, because no record was in
context on any first-sight pass: D-0001 sat behind a guard the boot failed
and went `moot` at the next consolidation; D-0002's consultation latch was
scoped to `test-failure-triage`, the shape the blind coder gave the
observations rather than the task's own terms, so the boot index matched it
to no task; and D-0003 landed after the last consolidation and failed both
rows of the lesson it mentions when the revisits applied it. What the run
does give is the three series read on a real model for the first time:
`solution_economy` 0.23 attached against 0.29 detached and `turn_economy`
0.25 against 0.30, each evaluable on 69 of the 80 first-sight rows — the
eleven `bom` rows carry no knowing floor — and `method_transfer` 0.40
against 0.20, which is 2 of 5 rows against 1 of 5, since transfer is
evaluable only on a passed shell-lesson row whose pass left a replayable
command and the two silent shell lessons passed nothing: every evaluable
row in both arms is `csv-quoted`. Those two lessons are the run's flat
floor — footer-row and trailing-newline 0/12 each on both arms, 24 of 24
rows the naive shape attached and 23 of 24 detached, the missing row the
malformed tool call — and the observations the close filed named the check
and not the world ("the `method_transfer` check was missed", "did not fire
a check record to verify the total"): none of the forty named a footer row,
a missing newline or a quoted comma in words the coder could group on. The
run's four findings are the carry-forward's items 39–42 — the latch scoped
to the coder's term, the close naming scores not world-facts, the drafts
refused at parse, the malformed tool call — and the fixes that answer them
are on `main` as decisions 78, 79, 81 and 82: the parse floors relaxed, the
hook seeded from the task's own terms, the close asked for the world's fact
the row met, the malformed assistant turn replayed with arguments the
endpoint accepts. The rerun that would show whether any of them changes
this table has not been run. Every count here is a floor from one run.

### The text-to-SQL stream on `openai/gpt-oss-120b` and `gpt-oss-20b`, taught by `deepseek-ai/DeepSeek-V4-Pro`

`experiments/text2sql.toml`, run on 2026-09-13 over W&B Inference: the ten
graded `text2sql` questions and the six `text2sql-holdout` ones — sixteen
BIRD `financial` questions over one pinned SQLite database — dealt by seed 0
into eight batches of two, one of each group per batch, a consolidation
every two batches, batches 1 and 2 met again after the stream; the strict
pool is the ten graded questions alone at one shell call, five batches of
two consolidated every pass. The roles are split: the forward pass runs on
the actor and every other role — consolidator, examiner, adjudicator, blind
coder, re-author — on `deepseek-ai/DeepSeek-V4-Pro`. `gpt-oss-120b` runs
attached, detached and on both strict arms; `gpt-oss-20b` attached under
the same teacher. The two `*-seeded` arms have not run. The logs are derived
from the arm stores (`experiments/results/text2sql/`), traced to
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave).

First sight per batch, every arm on the same two questions:

| batch | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | stream |
|---|---|---|---|---|---|---|---|---|---|
| 120b attached | 0.50 | 0.50 | 0.00 | 0.00 | 0.50 | 1.00 | 0.00 | 0.50 | 0.38 |
| 120b detached | 0.50 | 0.50 | 0.00 | 0.00 | 0.50 | 1.00 | 0.00 | 0.00 | 0.31 |
| 20b attached | 1.00 | 0.00 | 0.00 | 0.50 | 0.50 | 1.00 | 0.00 | 0.00 | 0.38 |
| 120b strict | 0.00 | 0.00 | 0.00 | 0.00 | 0.50 | | | | 0.10 |
| 120b strict detached | 0.50 | 0.00 | 0.00 | 0.00 | 0.50 | | | | 0.20 |
| in context, 120b attached | — | — | — | — | — | — | D-0002 | D-0002 | |
| consolidation after, 120b attached | | K-0001: nothing | | K-0002: D-0001 | | K-0003: D-0002 D-0003 D-0004 | | K-0004: D-0005 D-0006 D-0007 | |

The attached and detached `gpt-oss-120b` arms score the same on seven of
the eight batches and differ by one row on the eighth; the strict pool's
rise to 0.50 on batch 5 is matched by its ablation. Per group the attached
arm is 4/10 on the graded questions and 2/6 on the holdout, the detached
3/10 and 2/6. Revisits: the 120b attached arm met batch 1 again at 0.50
(0.50 at first sight) and batch 2 at 0.00 (0.50) with four records in
context; the strict arm met batch 1 at 1.00 (0.00) and batch 2 at 0.00
(0.00) with both its records in context; the 20b arm reproduced its
first-sight scores on both.

What the store holds decides the run where the curve cannot. The failed
queries carry the family's conventions — `status = 'approved'` where the
code is `'A'`, on three strict-arm rows; `frequency = 'TYDNE'` for
`'POPLATEK TYDNE'`; a date column read from the wrong table — beside genuine
logic misses and three rows where the actor dumped the schema and returned
no answer. The seven decisions the 120b arm admitted name none of these.
Three are copies of the other three with the latch widened onto the tool
terms every task presents. The four live ones say the output must conform
to the schema, the SQL must translate the requirements correctly, and the
pass must consult the store's rules before executing — the last built on
seven observations that are the actor's answers to a close lens about which
record should have fired, filed as facts of the world. The strict arm's
second decision — the answer must be a row-returning `SELECT`, not an
aggregate — misreads three `COUNT(*)` questions that failed on the coded
status, and was in context when one of them failed again. The seeded
`schema-coded-value` term was never used; the blind coder read every miss
as `output-schema` or `shell-tool`. The 20b arm's three decisions say the
query must match the requested aggregation and qualify its columns. The
stronger teacher parsed on every request and wrote the same generic drafts
as `gpt-oss-120b` does, so what the run measures is the request, not the
model (carry-forward items 48–52).

### The reasoning-core stream on `Qwen/Qwen3.6-35B-A3B` and `gpt-oss-20b`, taught by `deepseek-ai/DeepSeek-V4-Pro`

`experiments/reasoning-core.toml`, run on 2026-09-13 over W&B Inference: the
24 pinned Reasoning Core instances — twelve regex-following, twelve
cfg-generation — dealt by seed 0 into six batches of four, a consolidation
every two batches, batches 1 and 2 met again after the stream; the strict
pool is the same instances at exactly the one verification call. The roles
are split as in the text-to-SQL run: the forward pass on the actor, every
other role on `deepseek-ai/DeepSeek-V4-Pro`. `Qwen3.6-35B-A3B` runs attached,
detached and on both strict arms; `gpt-oss-20b` attached under the same
teacher. The two `*-seeded` arms have not run. The logs are derived from the
arm stores (`experiments/results/reasoning-core/`), traced to
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave).

This run is confounded, and the confound is the finding to carry. The arms
were launched with the venv's interpreter directly rather than through `uv
run`, so the shell tool's `python3` was the system interpreter and every
`import nltk` in a grammar row failed — the Qwen arms hit `No module named
'nltk'` on twelve of twelve cfg rows apiece, spent their spare call on `pip
install`, and answered without a verified candidate (decision-log decision
95(d) names this dependency; a launcher must put `.venv/bin` first on PATH).
Every decision the three attached arms admitted — verify a library before
importing it, install it or fall back to the standard library, plan the
calls to fit the budget — describes that launch environment, not the world
of regexes and grammars. Read the pass rates as the actor's unaided produce
rate and the economy series as contaminated on the cfg rows.

First sight per batch, every arm on the same four instances:

| batch | 1 | 2 | 3 | 4 | 5 | 6 | stream |
|---|---|---|---|---|---|---|---|
| qwen attached | 0.75 | 1.00 | 1.00 | 0.50 | 0.75 | 0.75 | 0.79 |
| qwen detached | 0.75 | 1.00 | 1.00 | 0.75 | 0.75 | 1.00 | 0.88 |
| 20b attached | 0.75 | 0.50 | 1.00 | 0.50 | 0.75 | 1.00 | 0.75 |
| qwen strict | 0.75 | 1.00 | 0.75 | 1.00 | 1.00 | 0.75 | 0.88 |
| qwen strict detached | 1.00 | 1.00 | 0.75 | 1.00 | 1.00 | 0.75 | 0.92 |
| in context, qwen attached | — | — | D-0001 D-0002 | D-0001 D-0002 | D-0001–D-0003 | D-0001–D-0003 | |
| consolidation after, qwen attached | | K-0001: D-0001 D-0002 | | K-0002: D-0003 | | K-0003: D-0004 D-0005 | |

Both detached arms score at or above their attached siblings, within two
rows over 24, and the strict pool scores above the lax one: the budget fails
no task here, because a row is graded on its answer and the shell refusing a
call past the budget leaves the actor free to answer from its own derivation
(`tool_budget_respected` sat between 0.00 and 0.75 on rows that passed).
Revisits: the qwen attached arm met batch 1 again at 1.00 (0.75 at first
sight) and batch 2 at 0.50 (1.00); the strict arm at 1.00 (0.75) and 1.00
(1.00); the 20b arm at 1.00 (0.75) and 0.50 (0.50). In the strict arm the
teacher's own decision to "enforce a strict budget of one shell call" had
its premise reversed one consolidation later on the evidence that
over-budget passes went unpunished. For the pool to measure the store the
answer has to depend on the shell — grade only a candidate the row
verified, or fail an over-budget row outright — and the level-3 regexes
and level-2 grammars are near saturation for a 35B actor regardless
(carry-forward items 47 and 53).

### The incidents pool on `openai/gpt-oss-120b` and `gpt-oss-20b`

`experiments/incidents.toml`, run on 2026-09-13 over W&B Inference and traced
to
[`rohanpchavan0701/hgi-experiments`](https://wandb.ai/rohanpchavan0701/hgi-experiments/weave):
36 tasks — nine hearth bundles worn four ways each — over three decoy lessons,
`decoy-dependency`, `decoy-saturation` and `decoy-state`, each bundle a set of
readings whose loudest signal names a cause that is not the cause. Seed 0 deals
them into twelve batches of three, one pass per batch, batches 1 and 2 met
again after the stream, so every pass is first sight and the two revisits are
the only rows a store could have taught. The arms run today, the stream rate
being the pass rate over all 36 first-sight rows:

| arm | actor | judge roster | stream | admitted |
|---|---|---|---|---|
| 120b-detached | `gpt-oss-120b` | — | 0.47 (17/36) | — |
| 120b-attached | `gpt-oss-120b` | `gpt-oss-120b` | still running at ten of twelve passes, 0.47 (14/30) | D-0001 after pass 4 |
| student-detached | `gpt-oss-20b`, low effort | — | 0.33 (12/36) | — |
| student-attached | `gpt-oss-20b` | `gpt-oss-20b` | 0.42 (15/36) | nothing |
| student-strong-judge | `gpt-oss-20b` | `DeepSeek-V4-Pro` | 0.36 (13/36) | D-0001, D-0002 |
| student-120b-judge | `gpt-oss-20b` | `gpt-oss-120b` | 0.47 (17/36) | nothing |
| peer-detached | `Llama-3.3-70B` | — | 0.00 (0/36) | — |

Three of those rows are not results. The 120b-detached 0.47 is at the current
prompt hash; an earlier run of the same arm at the previous hash, before
`ruled_out` was asked for, scored 0.64 (23/36), and 120b-attached at that same
earlier hash scored 0.56 with the store never once in context — the pair is a
prompt change and not a memory effect, and neither number belongs in the same
column as the others. student-120b-judge died at pass 2 on a `None` evaluation
summary twice before the third attempt completed, so its curve is the survivor
of three starts. And peer-detached's 0.00 is a protocol mismatch, not a
diagnosis result: Llama-3.3-70B reports its answer by shelling `echo` and never
returns the final JSON, so 32 of its 36 rows end at the turn limit with nothing
the grader can read. The student-attached arm admitted nothing at all — three
pass proposals expired unadopted — and the two records student-strong-judge did
admit are tooling hygiene, not diagnosis: *retry an HTTP read with bounded
backoff* and *a reply that is not valid JSON fails the task*, both flipped at
the next consolidation and never consulted by any row.

The control says the same thing from the other side. `upstream-outage-b` is the
bundle whose readings look like saturation and are not, and every detached arm
scored 0/4 on it, every miss answering `pool-exhaustion`. Across 120b-detached's
thirteen misses the shape is: 0 rows over budget, 7 rows naming the right class
while citing a decoy reading, 6 rows naming the wrong class, all six
`pool-exhaustion`. The pool is not hard because the models run out of calls. It
is hard because the loud reading is believed.

What was admitted, and when. In every attached arm, on every pass, `in context`
is empty — not a record declined, a record never reached. The boot classifier
codes an incident brief as work-shape `[]` with the escape `other(incident
brief)`, so every record's guard fails on an empty term intersection and the
store sits there logged as considered. The fix — `8c7cd80`, making the tasks'
declared shapes the floor of the pass's work-shape, mirroring `anchor_terms` on
the write side — landed after the sweep had started, so none of the sweep arms
ran with it. The rest of the chain shows the same fault one link further up: all
thirteen observations filed in the first 120b run named the loop and not the
world ("did not consult the detection record"), the blind coder escaped 41 of 41
noticings under the old vocabulary, and the three convention terms the domain
actually needs — `pool-exhausted`, `dependency-stalled`, `release-regressed` —
landed on 1 of 4 shapes on the student arm and 2 of 4 on the judge arm. A lens
diagnostic over the detached failures, 45 calls, isolates the last link:
appending one sentence to the L-0004 angle moves world-naming noticings from 42%
to 88% of rows, dropping `consulted` from the brief makes it worse rather than
better (15%), and the lens restates the attempt's own class because the row it
is given never carries what the readings said.

**The seeded run.** Because nothing the loop wrote could reach context, the
records were written by hand: four decisions — pool-exhausted, dependency-
stalled, release-regressed, and citation discipline — placed into fresh stores
for each model, then the same 36 tasks run twice, pass 1 with the boot bug in
place (records present, unreachable) and pass 2 after the fix:

| | 20b p1 | 20b p2 | 120b p1 | 120b p2 |
|---|---|---|---|---|
| task_pass_rate | 0.50 | 0.44 | 0.47 | 0.69 |
| in context | none | D-0002 | none | D-0001, D-0003 |
| bad-deploy (release-regressed) | 5/8 | 3/8 | 1/8 | 8/8 |
| upstream-outage (dependency-stalled) | 5/8 | 6/8 | 4/8 | 6/8 |
| pool-exhaustion (pool-exhausted) | 5/12 | 1/12 | 7/12 | 5/12 |
| poison-message (no record) | 3/8 | 6/8 | 5/8 | 6/8 |
| control upstream-outage-b | 2/4 | 3/4 | 0/4 | 2/4 |

Each store took a second pass-2 run: 20b 0.47 with D-0001 and D-0003 in
context, 120b 0.56 with D-0001 alone. After the boot fix all four records are
reached through the index and the model-based guard — `_coder.guard`, the
`not_this` check against the presentations — admits one or two of them per boot,
nondeterministically, which is why the two runs of a cell differ in what they
saw. D-0004 was never in context on any of them.

The honest reading. The strong actor moves in the direction the records teach:
0.47 to 0.69 overall, bad-deploy 1/8 to 8/8, and the control 0/4 to 2/4 with
`ruled_out` now naming the pool readings it set aside rather than answering
with them — and the lift tracks which record reached context, 0.56 with one and
0.69 with two. The weak actor reads the same records, applies them, and does not
convert: flat to slightly down across both of its pass-2 runs, its one gain the
control at 2/4 to 3/4. And in both actors the genuine `pool-exhaustion` family
falls, 5/12 to 1/12 and 7/12 to 5/12, which is the finding rather than a blemish
on it: the dependency record shifts the prior away from pool-exhaustion instead
of teaching the discriminator that separates the two, so what the run
demonstrates is a shifted prior and not acquired discrimination. Thirty-six rows
per cell, single samples, no repeats. The larger caveat is upstream of the
table: the automatic chain — observation to coder to record to hook — produced
none of these four records today, they were written by hand, and the three links
it is missing are now named rather than guessed at: the row must carry what the
tool returned, the lens must be asked for the world's fact and not the attempt's
account of itself, and the vocabulary must hold the domain's own terms. The
runner itself died on validation errors three times over the day — a verdict
token, a `None` evaluation summary twice, a minted term — all of them in shared
code and all listed in PR #7. The arms and rosters are in
`experiments/incidents.toml`; every call behind these numbers is in the Weave
project above.

### The baseline on `openai/gpt-oss-120b`

Run on 2026-09-12 over W&B Inference, six passes attached and six detached,
consolidation every two passes, traced to
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave):

| pass | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| memory attached | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| detached (ablation) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

The honest reading: this suite is saturated for this model. gpt-oss-120b
retries a transient 502 unprompted, batches the budgeted shell calls and
names causes, so every lesson the stub demonstration learned is behaviour
the model already has, and the store has nothing to teach it. The attached
run filed eight observations (every one a recovered transient fault) and
admitted nothing: the consolidator's drafts were refused at the floor. A
separation needs either a world with faults the model does not already
handle or a model that does not already handle them; both are one arm in
an experiment file. An earlier run of the same arms, before the role
requests stated their reply shapes, scored 0.67–0.83 on both curves with two
tasks failing on a double-wrapped result and no observation filed; that run
is recorded in `carry-forward.md`, not here, because its numbers measured
the contract and not the model.

### The world on `openai/gpt-oss-120b`

`experiments/world.toml`, run on 2026-09-12 over W&B Inference: 52 tasks
(twelve of each transcribed family, all of `genesis` and `conventions`),
the first two HTTP calls of a faulted task failing, six passes attached,
consolidation every two passes, traced to
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave):

| pass | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| memory attached | 0.81 | 0.73 | 0.75 | 0.90 | 0.83 | 0.83 |
| records in context | none | none | D-0002 | D-0002 | D-0002, D-0003 | D-0002, D-0003 |

The detached arm was not run to completion: a detached pass has no boot,
no close and no store, so its passes are draws of one evaluation, and pass
1 of the attached arm — an empty store, nothing consulted, the constitution
the only conditioning — is that draw. The runner now draws a detached
arm's passes concurrently for the same reason.

What the attached arm did: every failed row filed one anchored observation
(60 over six passes); the first consolidation grouped them into twelve
shapes, nominated four, declined two on the examiner's premise attacks and
admitted D-0001 (*tool outputs conform to the schema*) and D-0002 (*calls
stop at the HTTP budget*); the second admitted D-0003, D-0005 and D-0004 —
the last by adopting the pass's own close-time proposal of a retry
decision, the pre-admission tier working end to end — and expired one
unadopted proposal; the third admitted D-0006 and retired D-0001, D-0004 and
D-0005 as moot on their own telemetry, discharging three fires. Passes 3–6
consulted D-0002 and D-0003 and applied them; the lint is green with the
seven genesis-anchor warnings.

The honest reading: the curve moved within the run's own noise. Passes 3
and 4 ran with the same record in context and scored 0.75 and 0.90; the
same task flips between passes with nothing in context changed
(`api/21f6f753` passes, fails twice, passes twice; `mbpp/430` fails, fails,
passes three times, fails), and the decisions admitted were the loop's
tautologies —
schema, budget, argument validation — not the world's conventions. The two
conventions that failed every pass (`log_lines`, a budget of one shell call
over files with no trailing newline; `versioned_status`, an API moved under
`/v2` behind two faulted calls) never earned a record: their observations
were coded into shapes the consolidator did not nominate on, or nominated
and declined. The record that would have taught them is one the ladder's
`hook-edit` and `counterfactual-edit` rungs would carry, and those rungs
have no operator yet (decision-log, decision 21). What the run does show
is the mechanism at breadth on a real model: observations from every
failure, grouping, four-role adjudication with declines, adoption, expiry,
fires discharged and retirement — each of which the six-task baseline
could not exercise.

## Tests

```bash
uv run pytest
```

The tests are the slice acceptance bars of spec § 13: the floor's named
refusals and the committer (slice 0), facts, watches and fires (slice 1),
two passes chained through the store (slice 2), admit, decline, escalate,
the human queue, verdict authority and role separation on the ledger
(slice 3), the retirement leg, and the backward pass's other legs: split
and fold on the lineage DAG, the structural-zero audit and the edit rungs,
deferral latches and propagation, genesis anchoring, and vocabulary growth;
and the doctrine's disciplines over them: the noise filter, the examiner fan,
the code's readings of independence and watch direction, the amend-only
abstraction claim and the decline override, attacker precision, the recall stream, the lens lifecycle, revision routing,
the port miss stream, the key-space floor, the refusal of a rung with no
operator, the true-miss floor, the precision slot, the second retirement
key, anchor resolution, the late steer sweep, the antichain flag, and the
seeded controls.
