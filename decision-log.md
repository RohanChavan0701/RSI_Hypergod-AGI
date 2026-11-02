# Decision log

The decisions taken while building HGI, each with why it may be right and why it
may not. Companion to `carry-forward.md`, which carries the future-facing work:
where the build stands, the leftover work and housekeeping. A decision here is a
past choice and its risk; a leftover item there is work still to be done, and
those items reference these decisions by number ("decision 21", "decision 96").
The numbering runs 1 through 96 with a duplicate 60 (two decisions share the
number); it is kept as authored so the cross-references stay valid.

## Decisions taken, and their risk

- **2026-11-02 — Portable ID locks and complete distributions.** Use the
  explicit `filelock` dependency for the registry counter lock so the CLI can
  import on Windows while retaining interprocess exclusion. Existing concurrent
  ID allocation tests pass on Windows; Linux locking still needs validation.
  Include `suite` alongside `hgi` in the build because the CLI imports both.
  Keep UTF-8 mode explicit in Windows setup instructions; POSIX shell experiment
  compatibility remains tracked in `carry-forward.md`.

1. **Decision-only roster.** Beliefs and rules were dropped by instruction;
   the store, ports, bars, lint and projections are written so that adding a
   kind is a new model in `hgi/types.py`, a row in `LAYOUTS`, a port
   declaration and a projection. *Right if* the kinds really are coordinates
   of one contract (the spec's claim). *Wrong if* rule routing and the
   adoption register need read paths the decision path does not anticipate —
   the boot's stage one only knows the hook-major index over decisions.
2. **All vocabularies live in `registry/vocabulary.json`; types validate
   against the registry in scope** (`Term(vocab)` with a context variable)
   rather than as Python `Literal`s. *Right:* one source, growth without a
   code change, `other(<what>)` everywhere. *Risk:* no static typing of enum
   values; a test that forgets to put a registry in scope validates against
   `./store`.
3. **Observations and fires are file-per-record, not JSON Lines**, because
   each receives one in-place flip (promotion pointer, fire disposition). The
   spec calls both ledgers. *Right:* same-commit settlement without rewriting
   a ledger. *Risk:* a reader expecting `observations.jsonl`.
4. **`admission.commit` is derived, not stored.** A commit cannot contain its
   own hash; the commit message names the ids it admitted, so the anchor is
   git history, read by `hgi.store.admitting_commit` and printed by `hgi
   lineage` (decision 28). *Risk:* the spec puts the field on the envelope;
   a consumer expecting it there finds nothing.
5. **Facts are mirrored on the session record** (`evaluation.scores` and
   `evaluation.rows`) with the Weave run URI as `source`, and the watch
   evaluator reads them from the session ledger, not from Weave. Each row
   also carries its own scores, so the close can see which task the hidden
   test failed. *Right:* offline runs, reproducible tests, one read path.
   *Risk:* the spec keeps facts in the oracle; a fact edited on a session
   file is not the oracle's.
6. **The session record is written at boot and completed at close** (one
   file, `closed_at` null in between). The spec's ledger is append-only.
   *Risk:* a crashed pass leaves an open session; `hgi boot` refuses a
   duplicate id but nothing closes an orphan.
7. **The hypothesis-ledger entry is appended once, with the verdict**, after
   the adjudicator returns; the examiner's attack payload lives inside the
   entry with its own `verdict: "pending"` field that the schema fixes as a
   `Literal`. *Right:* the ledger is never edited, and the lint can prove
   verdict authority on it. *Risk:* an attack with no adjudication is never
   written anywhere.
8. **Credit assignment is task-level**, not series-level: a record's applied
   tasks' pass fraction before and after, and only a record whose fraction
   did not improve reaches the adjudicator, which names the slot. *Right:*
   two records applied in the same passes are not confounded; the model no
   longer writes a steer for every applied record. *Risk:* `before` is the
   same tasks' earliest history, which conflates "the record didn't help"
   with "the tasks were always hard".
9. **The retirement in the demo is a supersedure**, nominated by the credit
   table and the retry observations, not a status flip to `moot` by the
   ratio. The ratio-driven leg exists and is tested (`tests/test_retirement.py`)
   but did not trigger in six passes. The README says so.
10. **The stub decides verdicts by rules that can only decline on evidence
    the examiner reads** (fault rate, independence, a task id in the
    payload) and escalates only on an unevaluable watch series. *Right:* no
    verdict without evidence. *Risk:* the stub adjudicator admits almost
    everything the consolidator nominates, so the demo's ledger has no
    decline; the decline and escalate paths are proven by tests only.
11. **Watch predicates on the demo's decisions never fired**: the cause
    decision watches `error_cause_present < 0.5`, which its own application
    raises. A watch on `task_pass_rate` would have fired at pass 4 and made
    the steer a redundant catch instead of a store miss. The choice kept the
    steer cell populated; it also left the fire ledger empty in the demo.
12. **Trace attributes are a nested `hgi` object** (`attributes.hgi.session`),
    not dotted keys, because Weave's query language resolves nested fields
    and not keys containing dots. The UI renders both the same.
13. **The consolidation window shrinks nothing**: bars stay at six passes;
    with six passes the retirement leg cannot trigger. The drop-order rule
    (6) was not applied because the supersedure satisfied the row.
14. **The Evaluation summary is overridden to scorers only**
    (`hgi.evaluate.Evaluation.summarize`), because Weave's auto-summary
    tries to average the heterogeneous task outputs and raises; the same
    override keeps each row's scores aside for the session. *Risk:* the
    Weave UI's evaluation comparison shows no model-output block.
15. **Experiment arms run in a git repository each, under `runs/`, which
    the code repository ignores.** *Right:* the write law holds per arm
    (every write ends in a commit), arms cannot clobber each other or the
    demonstration's `store/`, and the code history stays the code's.
    *Risk:* an arm's result is not in the code repository's history; the
    README table is copied from `hgi experiment report` by hand, and a
    reader of the code repository cannot regenerate it.
16. **A round is a consolidation cycle; the cadence is written into the
    arm's bars at seed.** `rounds × passes_per_round` is the run's length
    and `consolidation_every_passes` is the round size, so the file states
    the cadence once. *Risk:* the brief reads only the sessions since the
    last consolidation, so a round size of one may never meet the
    two-distinct-sessions bar — `cadence.toml` measures this rather than
    fixing it.
17. **W&B Inference is the endpoint the shipped experiment files use**, not
    a CoreWeave endpoint, because a key for it exists on this machine and
    none did for CoreWeave; the role is the invariant and a CoreWeave model
    is one more `[models.*]` entry with its own `base_url`. *Risk:* the
    sponsor binding in the README now names both.
18. **Backends are installed per role in the process** (`hgi.model.use(b,
    role=…)`), so one arm can act on one model and adjudicate on another.
    *Risk:* the session record carries one `model_id` (the pass's); the
    per-role ids are on the ledger entries' role calls and on `arm.json`.
19. **The reply shape travels with the request, not in the prompt**
    (`hgi.roles.REPLIES`, `roles.request`). *Right:* one table, the stub
    and the model read the same contract, and a shape change is one edit.
    *Risk:* the model echoes what it is shown — a placeholder inside a list
    came back as a literal element, and a `reply` key came back as a
    wrapper; both are read defensively, and the test on `REPLIES` forbids a
    string beside an object in any list.
20. **Each role receives only the record shapes it reads** (`roles.schemas(role)`):
    the drafting roles the Sketch, the judging roles the Draft and the
    ledger entry, the coder none. *Right:* a third of the tokens per call,
    and no schema a role cannot act on. *Risk:* the vocabularies are still
    validated at runtime only — the schema says `string`.
21. **Drafting roles return a sketch; the code derives the record**
    (`hgi/drafting.py`). The model judges the five slots — payload,
    overshoot, cue and exclusions, premises as falsifiers, watch, residue,
    moot condition — and `drafting.body` builds the latches, the owed acts,
    the retirement guard from the bars. *Right:* on gpt-oss-120b the full
    body came back as placeholders in every try and the sketch parses and
    clears the floor in every try since; the stub answers in the same
    shape. *Risk:* the rule-tier rungs (`adoption-row`, `rule-enrollment`)
    have no operator in a decisions-only roster; an edit rung derives its
    successor from the record it supersedes rather than from a sketch
    (decision 34), and a sketch cannot express a latch the derivation does
    not know (a wiring latch, a second consultation hook).
22. **Ids are minted against the counters on disk**, re-read before every
    reservation. *Right:* a long-running runner and the commands it drives
    hold separate registry objects; the baseline arm's three consolidations
    overwrote one file before this. *Risk:* one file read per mint; a
    process that edits `ids.json` by hand between mints is obeyed.
23. **The suite is an object in scope**, like the registry: `suite.current()`
    is what the experiment installed or what `$HGI_SUITE` names, and every
    module that read `suite.tasks.TASKS` reads it. Faults are keyed on the
    task's name within its family, so a family keeps its faults when
    composed with others. *Risk:* a test that forgets to install a suite
    runs the genesis family silently; the session records only the hash,
    not the spec — `arm.json` records the spec, a hand-run's `.env` does.
24. **The close lens that touches the artifact is walked once per failed
    row.** *Right:* over sixteen rows in one context the model filed
    nothing for two failed tasks; per row it files one anchored observation
    each. *Risk:* one call per failure — a pass that fails thirty tasks
    makes thirty lens calls — and a failure that was the model's own
    arithmetic still files, so the coder's grouping has more noise to
    separate.
25. **A pass proposal reaches the consolidator through the brief and is
    adopted by uid or expires** (`proposal_ttl_consolidations`, 2). *Right:*
    the pass proposes, the backward pass admits, and the pass's draft keeps
    its provenance on the admitted record. *Risk:* on the real model the
    pass proposes the same retry decision every pass with thin evidence;
    the consolidator has not been seen to adopt one yet.
26. **The adjudicator's reply carries a rationale**, recorded on the ledger
    entry, and a token outside the vocabulary escalates. *Right:* the
    first verdict on the real model admitted over a landed premise kill
    with no trace of why; now the weighing is on the ledger. *Risk:* the
    rationale is prose the lint cannot read.
27. **A regression is nominated mechanically before credit runs** (decision
    8): the adjudicator sees only rows whose applied tasks did not improve.
    *Risk:* a record whose tasks improved for another reason earns no steer
    even when it was wrong — the oracle's floor, disclosed.

28. **The admitting commit is the oldest commit naming the id**, rather than
    a commit parsed for the verb that names it. History is append-only and
    no message names a record before the commit that wrote it, so the oldest
    naming is the admission, and no vocabulary of message verbs has to be
    kept in step with the messages. A range such as the genesis message's
    `C-0001..C-0007` names each id it spans. *Risk:* a message that names an
    id it did not write — a revert, a plan, a message quoting another —
    reads as an admission; nothing enforces the convention the messages
    follow.
29. **A re-price that does not re-author says so on the record**
    (`priced_for.authored_for`). *Right:* the stamp cannot launder the swap
    into a green floor; the warning stands until the text follows, and
    swapping back clears the field because stamp and authoring agree again.
    *Wrong if* the two halves are really one act — then a store sits
    indefinitely priced for a model nothing was authored for, behind a
    warning nobody reads, which is exactly what `hgi genesis --force`
    avoided by making a price a fresh seed.
30. **A tombstone's `superseded_by` is a list**, not the scalar the spec's
    envelope example shows, because a split leaves one retiree with several
    heirs and a scalar cannot name them. A record written with a scalar or
    `null` reads as the list it means; `store/decisions/D-0001.json` still
    carries the scalar it was written with. *Risk:* a reader of the spec's
    example expects a string.
31. **A deferral is a latch on the draft itself**, in the pre-admission
    tier, and only that latch is exposed to the watch evaluator — the
    draft's own fan is not yet live. An adjudicator that defers without a
    condition, or returns an escape verdict, re-queues the draft at the
    next backward pass rather than leaving it without a condition that can
    fire. *Risk:* the adjudicator's `until` is read from a fixed shape
    (scorer, comparator, value, persistence — or passes); a condition it
    phrases otherwise becomes the schedule default.
32. **Observations a deferred draft rests on are claimed** until the draft
    is disposed, so it is not nominated twice from the same instances; a
    pass proposal is left unclaimed, so its instances still group and a
    nomination can adopt it. *Risk:* a declined draft frees them, and the
    same fork is nominated again at the next consolidation from the same
    observations.
33. **A wiring latch's guard remembers the status it saw**, and the fire
    ledger carries every later observation, so the latch stays immutable
    and one departure fires once. A warrant that cites a record is wired to
    it at admission, excluding the records the draft retires (the lineage
    edge already carries those, and citing a predecessor would otherwise
    close a wiring cycle the lint refuses). *Risk:* a wiring latch written
    before guards remembered statuses reads its successor as `accepted`.
34. **The edit rungs are successor records** derived from the one record
    they supersede with the named fields replaced — never an edit in
    place, because a decision is frozen after acceptance. The retirement
    review's nomination still names `counterfactual-edit` as its rung for
    want of a `retire` rung in the ladder vocabulary.
35. **Genesis anchoring is a currency question**, not an attack: the
    consolidator proposes an instance, the adjudicator reads the instance
    itself, and the ledger entry's species is `currency` with `still-holds`
    meaning the instance exemplifies the article. No examiner sits between
    them, because the claim is one instance and one article, not a five-slot
    draft. *Risk:* proposer and adjudicator without a contradictor is a
    weaker separation than the protocol of § 10.9; the adjudicator is handed
    the record, never the proposer's `why`.
36. **Vocabulary growth files as a `coding` entry** whose contradictor is
    the blind coder and whose verdict is `agree` | `disagree`; the
    adjudicator's own token (`admit` | `decline(<why>)`) is the entry's
    outcome. A declined term is re-nominated only by escapes from passes
    after the verdict.

37. **Every verdict seam routes through a closed table**
    (`registry.route_table`), and a term the vocabulary admits but the seam
    has no act for raises `Unrouted`; a test proves every table covers its
    vocabulary and the escape. *Right:* the `defer` fall-through of the
    first build cannot recur silently. *Risk:* an act tag is a string the
    seam dispatches on; the table proves coverage, not that the act is
    right.
38. **A settlement cites its licence** — an adjudicated ledger entry, a
    dispositive fire, or the admitted successor — and the committer refuses
    any other, so a corroborating fire nominates and never settles. The
    retirement latch is corroborating, so retirement cites the adjudicator's
    currency entry, and the lint proves the licence on every settled latch.
    *Risk:* `evict_article` cites no licence; the deadline in the bars is
    its only ground.
39. **A fire owed to the working pass is disposed at close** as a consulted
    record is — from the pass's own rows, in the session's commit — or the
    close is refused, and the lint's `fire-completeness` check reads the
    close seam. *Risk:* no latch in the decisions-only roster names the
    working pass as its disposer yet, so the path is proven by tests only.

40. **Escape recurrence clusters every closed vocabulary through one
    counter, keyed on the occasion the escape was written on** — a session
    for a work-shape, a `record#index` for a latch key-space, a ledger entry
    for a `<species>-verdict` — and `reviews.vocabulary` runs for each by
    default. A vocabulary no verdict seam routes (work-shape, key-space)
    grows in place on admit; a routed verdict vocabulary is surfaced but not
    minted, because growing it in place would leave the seam without an act
    for the new head (`registry.route_table` coverage). *Right:* one
    clustering law, and the demonstration store has no such escapes so the
    extra passes are no-ops there. *Risk:* an occasion of unknown pass (a
    verdict entry no session filed) is not gated by the after-pass re-count,
    so it can re-nominate each consolidation until adjudicated — its own
    uniqueness is the only guard; and the coder's contradiction still recodes
    the *suite presentations*, which are a work-shape signal, so its reading
    is weak evidence for a key-space or a verdict term.
41. **A revisit watch's direction is checked against the oracle's
    convention, not the prose stakes** — every scorer is a success rate in
    `[0, 1]` with `1.0` ideal, so a predicate the ideal satisfies but a
    failing score does not fires on success. The examiner (its stub logic
    and its prompt) lands `warrant:watch-direction` and the adjudicator
    declines. *Right:* the mechanical check needs only the two sentinels the
    suite's scorers share, and catches `task_pass_rate == 1.0` and `>= 0.9`
    alike. *Risk:* a scorer where lower is better, or one outside `[0, 1]`,
    would read backwards; the convention holds for `suite/scorers.py` today
    and is asserted nowhere the suite could not silently break.

42. **A nomination at a rung with no operator is carried as a decision that
    records its displacement.** Before this build a `floor`, `article`,
    `adoption-row` or `rule-enrollment` nomination fell through `draft_from`
    and became a decision draft wearing the rung's name; a first cut refused
    it outright, and that was reversed by instruction: the demo learns faster
    with a rule held as a decision than with no record at all, and the
    ideal-home cost is paid later, not never. The nomination's `rung` becomes
    `new-decision`, `displaced_from` keeps the rung it meant, and the
    committer stamps both on `admission`. *Right:* route-before-mint reads
    "cheapest sufficient home" over the homes that exist. *Risk:* a rule
    carried as a decision is recalled by the decision path — a full scan of
    summaries plus the hook — and has no adoption register, so "did you do it
    at every site" is never asked of it; the rule tier, when it comes, reads
    `displaced_from` to find what to re-home.
43. **The contradictor of a currency entry is the oracle, never the
    adjudicator.** Retirement, genesis anchoring, propagation and revisit
    fires wrote the adjudicator's call as the contradiction source, a
    contradictor = adjudicator collapse in name; the `oracle` role now names
    the fire, the ratio or the instance, and a pass's close-time contradiction
    is proposed by the record's admitter and contradicted by the pass. The
    `role-separation` check proves it on every line. *Risk:* the oracle's
    "call" is a fire id or a projection key, not a Weave URI, so the
    contradictor is joinable to the store and not to the trace.
44. **The noise filter is an adjudicator triage over every group at the
    bar** (spec § 10.2), before nomination, on a `reality` entry; an
    irreducible group is dismissed to the entry and never nominated. *Right:*
    I11 — nothing updates process on an irreducible failure — was a
    sentence in the spec and nothing in the code. *Risk:* one more adjudicator
    call per group; the stub classifies by harness markers ("model call
    failed", "turn limit"), which is the stub's reading of irreducible and
    not the doctrine's — a real adjudicator may dismiss a convention missed as
    "the model's own error", which is exactly the reducible case. The
    dismissed observations' recurrence tunes nothing yet: the reality entries
    are written and read by no detection-side leg.
45. **The boot recall lens has a consumer: the `recall` projection.** A
    probe naming an accepted record the pass did not consult, joined with
    steers indicting activation, is the should-have-fired stream; at the
    independence bar the consolidator re-keys the record with a hook-edit on
    the terms the probing passes presented. *Right:* § 16.21 — a lens whose
    product lands nowhere is theater. *Risk:* the stub adds every presented
    term the hook lacks, which widens a hook toward "every term"; the doctrine
    biases broad, but a real consolidator should add the term that names the
    presentation, not all of them.
46. **A pass's pending contradiction reaches the adjudicator at the next
    consolidation**, on a new entry citing the pending one; the pending line
    stays as history. *Risk:* the stub reverses a premise only when the
    finding names its id; a real adjudicator handed a finding with no
    premise id has only the prose.
47. **The examiner's angles are lenses, one call each** (the fan law and the
    host law): L-0005 independence, L-0006 premise kill, L-0007 abstraction,
    L-0008 watch direction, each declaring the claim classes it may land on,
    a claim outside its class dropped, every claim naming its angle and call.
    A register with no examiner lens falls back to the single-context attack.
    *Right:* one context walking four angles is a longer prompt, not an
    ensemble. *Risk:* four calls per draft on a real model, and the angles
    share the draft and the evidence pack, so their decorrelation is of
    context, not of input; the abstraction angle's `task_ids` are now the
    suite's task ids, so a payload naming a task is caught where before the
    list was always empty.
48. **Attacker precision is a projection and a brief row** (I16): landings
    upheld ÷ entries with a landing, per angle, with the
    should-have-been-caught-by misses (a survived record later indicted,
    reversed or moot) and two notes — zero landings interrogate the dispatch
    bar, a precision of one over zero overrulings is a ceiling artifact.
    *Risk:* nothing consumes the row into a nomination; the dispatch bar it
    interrogates is not a parameter anywhere.
49. **A lens carries a warrant and a status, and the lens review runs at
    every consolidation.** Anchors are derived from consumed products — a
    mechanical join, no adjudicator, because a derivable structure is a
    projection (I3) — and a lens at a door (genesis deadline, variance
    collapse over the review window) goes to the adjudicator; `moot` retires
    it, kept in the register and walked by nothing. `registry.lenses()`
    returns live lenses only. *Right:* I7 — every threshold has a retirement
    leg — reached the lens tier. *Risk:* the demonstration store's eight
    genesis lenses are past the deadline and unanchored (fifteen
    `genesis-anchor` warnings now, not seven); the next traced consolidation
    will retire those that were walked and produced nothing, which on the
    world run's evidence is L-0003, and possibly L-0001 and L-0002. A lens
    whose product is always empty is read as "no signal" and kept; a lens
    whose product is always the same non-empty finding is read as
    crystallized — the stub's L-0004 would be, on a suite with one recurring
    failure.
50. **Revision routing runs before a vocabulary grows.** Breadth (how many
    registered members the escaping occasions also carry) and dependence
    (the share carrying the most co-occurring member) read the pile as a
    missing peer, a partition of one member, or a cross-cutting dimension;
    the last is vertical — surfaced on the consolidation record, never
    minted, no ledger entry. Under twice the independence bar the reading is
    ambiguous and horizontal. *Right:* § 7.5 — a wrong axis at genesis
    outranks any number of missing members. *Risk:* the truth-maker feature
    is assumed identical for every escape of one vocabulary; a verdict
    vocabulary's occasions carry one member each, so its escapes always read
    as missing peers; and a vertical reading has no human seat but the
    consolidation record.
51. **The port declaration's miss stream widens a mark.** A latch admitted
    off its declaration on a warrant, recurring across independent records at
    the vocabulary's independence bar, is nominated to the adjudicator; admit
    corrects `registry/ports.json` from `forbidden` to `optional` in place, on
    a currency entry whose verdict is `reversed`. *Risk:* the only widening is
    forbidden → optional; nothing earns `required`, and nothing narrows a
    mark back.
52. **Four small floors from the activation section.** `summaries` carries
    each record's watch or `unwatched` and the consultation plan names the
    unwatched records (§ 16.17); the `key-space` check fails a neighbour key
    that resolves to nothing and a world-state watch on a scorer the oracle
    does not run (referents, never aliases); a human steer's note naming a
    record indicts it, the slot read off the note's words; the credit rows
    ship the counts their fractions are computed from (itemized, never net).
    *Risk:* the slot words are a keyword table; a note that says "hook" about
    a payload indicts activation.

53. **The true-miss cell counts rows, keyed `session/task`, and stays a
    floor.** A task that failed in a closed attached pass that consulted no
    record and filed no observation from the row is the event nothing caught:
    no latch fired, no floor refused, no noticing was made. *Right:* the cell
    was always written as a fixed empty list with a note calling it a "floor
    of zero", which is the one reading a floor forbids — an observed zero
    read as a measurement; now the store counts what it can see. *Wrong if*
    "consulted nothing" is too strict a key: a pass that consulted a record
    on another hook and still failed a row nothing bore on is also a miss
    nothing caught, and the cell does not count it — the applied disposition
    puts that pass in the top row even for the rows it did not touch.
54. **Fired-but-not-applicable is its own column, and precision is a brief
    row that nominates a `counterfactual-edit`**, at a bar of its own
    (`precision.not_applicable_over_considered_above`, 0.5), from the
    not-applicable dispositions' notes across independent passes. Two finer
    diagnoses outrank it in the derivation: a bimodal record is fused (a
    split, not an exclusion) and a record at its retirement door — never
    applied over a full window — is the retirement leg's. *Right:* the first
    slot signature of § 10.5 was a table row in the consolidator's prompt and
    nothing in the brief; the successor keeps the hook and grows `not_this`,
    which is the authoring register's own rule. *Wrong if* the bar is the
    wrong quantity: a record considered twice and not applicable once is at
    0.5 and nominated, and the independence bar on the notes' sessions is
    the only damper; and the stub adds every presentation the notes name,
    which on a real pass could grow `not_this` toward "every task".
55. **Never considered across a full window is the second retirement key,
    through the same currency request.** The record must have been accepted
    before the window opened (its `committed_at` against the first session's
    `started_at`), the window must be full, and the adjudicator sees the
    window's domain evidence — the terms its passes presented, the fault
    rate over its rows — against the record's `moot_when`; the stub keeps
    the record unless that condition is met by keyword (a fault condition
    with a zero fault rate, a budget condition with no budgeted presentation).
    *Right:* § 10.5's lifecycle row named "domain no longer entered" and the
    leg only read the ratio, which is `None` at zero considered; and never
    fired is a count, so the killer-item check sits between the count and
    the flip. *Wrong if* the stub's keyword reading of `moot_when` is taken
    as evidence of anything: it is the stub's, and a real adjudicator handed
    prose and a fault rate may retire a record whose domain would re-enter
    next pass. The nomination's rung is still `counterfactual-edit` for want
    of a `retire` rung (decision 34).
56. **A counterfactual's anchor must resolve, and an unresolved one warns.**
    The complement-law check resolves every id-shaped anchor through one
    store method (`lookup`: a file record, an observation by name or uid, a
    ledger line) that the anchoring review derives from too; a URI, a commit
    and a path are not resolved. *Right:* an anchor that matched the pattern
    and named nothing passed as anchored, which is priming wearing an anchor.
    *Wrong if* warn is too soft: a draft citing an invented observation is
    admitted with a warning nobody reads. Fail was not chosen because a
    conftest draft cites `O-0001` before the test has filed it, and because
    an anchor may name what a later admission holds; the demonstration store
    shows no unresolved anchor (its fifteen warnings are all
    `genesis-anchor`).
57. **The late steer sweep files a note once, keyed on its call URI, and the
    steer names its session.** At close, every earlier closed attached
    session's calls are re-read and a note whose call no steer's
    `source.anchor` carries is filed, stamped with the session it belongs to
    and listed on the closing session's `steers_filed`. *Right:* a note left
    after a close was lost for good, and the channel's whole point is
    capture before the context that understood it is gone. *Wrong if* the
    call URI is not a stable key across trace-store reads, or if re-reading
    every earlier session each close is the cost item 24 names; the sweep
    could be bounded to the review window.
58. **The antichain is printed as one conflict line and travels on the
    dispose request.** Records whose consultation hooks share every term
    with no lineage edge between them (no supersedure, leaf or fold) are
    read as co-applying with no specificity order; nothing ranks or drops
    one. *Right:* § 16.17 — a join over nothing is displayed, never
    tiebroken — and the pass is now told to dispose each on its own rows.
    *Wrong if* "share every term" is too narrow a reading of co-application:
    two hooks that overlap on the term that fired, and differ elsewhere, also
    co-apply on that pass and are not flagged.
59. **The seeded controls reuse the battery's scorers, evaluation and
    writer, one item per context.** Per examiner lens, a signal draft
    carrying a fault of that lens's class (one pass counted twice; a
    transient-fault premise under a zero fault rate; a task id in the
    payload; a watch on success) and a decoy draft with none, attacked
    through `consolidate.attack` with the one angle named; for the coder, a
    known-shape observation and a misfit. The stub passes both by the rules
    it already had (`_attack`, `_coding`) — no special case was added — and
    the examiner telemetry lands on the lens register while the coder's goes
    to `index/controls.json`, a telemetry file beside the projections that
    regeneration leaves alone. *Right:* a decoy-only battery cannot tell a
    lens that never fires from one that discriminates, and the controls give
    each angle a positive it must land on. *Wrong if* one plant per class is
    read as a rate: it is one item, and a lens that lands on it proves it can
    land, not that it does; and `controls.json` under `index/` bends the
    projection law (regenerated, never hand-edited) for the sake of one file
    a reader would look for there.

60. **The dashboard's charts are altair over polars, rendered as plain
    charts** (dashboard pass). `altair` and `polars` join the dependencies;
    the hand-rolled SVG had no tooltips, cycled eight hues past their domain,
    was a fixed 640 px on a white background and could not facet. An arm's
    hue is its place in the experiment's arm order (eight slots, stepped for
    the light and the dark surface off `mo.app_meta().theme`), so an arm
    keeps its colour whether or not a sibling is drawn; attached is solid,
    detached dashed; a revisit a triangle; measures of different scale are
    small multiples, never two axes; magnitude is one blue ramp. *Why right:*
    every mark carries the row behind it, the width follows the container,
    and the palette is the validated dataviz reference. *Why not:* the theme
    is read once at render, so a toggle needs a rerun; plain charts drive no
    other cell (leftover 43); and the Compute tab charges the backward
    pass's calls — which carry the consolidation id as `hgi.session` and no
    `hgi.pass` — to the pass the consolidation followed, one reading, where
    the other would give the backward pass a column of its own.

60. **The stream is prequential: every batch is a test set once and a
    training set afterwards**, and the curve is first-sight performance on
    unseen tasks as the store grows. *Right:* a suite run scores whether the
    store learned the tasks it was scored on, and the world run's curve
    moved within noise on the same 52 tasks; a knowledge base is asked to
    improve work that is always new. *Wrong if* one task per lesson per
    batch is too thin a sample: a lesson's first-sight rate over ten batches
    is ten draws, and the paired difference to the detached arm is the only
    thing that carries; the per-batch curve alone reads batch difficulty as
    learning.
61. **Same-shape failures are decided by the task's naive outcome, not by
    a judge.** Every lesson task carries its naive first-contact policy as
    its scripted policy, so the answer or error first contact produces is
    derivable by running it, and a failed row that reproduces it is the
    lesson missed the naive way — with the row's tool errors read too, so a
    410 met and reported without its cause still counts. *Right:* the
    external-oracle problem (a judge asked "is this the same error?") is
    replaced by a construction the task already has, deterministic and
    offline. *Wrong if* the naive policy is not the way a model misses: a
    model that reads a page and sums it wrong is `wrong`, not `naive`, and a
    lesson whose naive shape a model never reproduces shows no recurrence
    even when the lesson is never learned; the `wrong` and `error` columns
    are kept beside `naive` for that reason.
62. **Lessons are tiered by how the failure shows in the trace** (loud,
    visible, invisible), and the report groups by tier. *Right:* the world
    run's two conventions that never earned a record were silent ones, and
    whether the loop learns only what the trace names is the question the
    tiers put. *Risk:* the tier is asserted per lesson by hand, not
    measured; a model that reads a file with `cat` sees a footer row and one
    that sums with `awk` does not, so *visible* is a property of the pass as
    much as of the lesson.
63. **The curriculum is generated, not transcribed**, from one seeded
    generator per lesson over word lists, with clothes disjoint from the
    hand-written families' file names and routes and budgets that leave the
    knowing policy one call to spare. *Right:* no public dataset carries the
    structure the stream needs — many unseen instances of few recurring
    conventions — and the generator gives as many clothes as a stream asks
    (`CLOTHES`, twelve today; 84 tasks bound the stream at ten batches of
    eight). *Wrong if* generated clothes are too alike: a record that
    memorises "files named `<stem>-<n>.<ext>`" transfers within the family
    where a real world's next instance would break it; the `transfer`
    family's hand-written re-dressing is the stricter test and is not in the
    pool.
64. **The stream faults nothing by default.** The `[stream.faults]` profile
    defaults to no transient 502s, so the lessons are the conventions alone
    and a budget of two on a moved route is reachable (the world run's
    `versioned_status` sat behind two faulted calls under a budget of two,
    which no policy could pass). *Risk:* the retry lesson, the one lesson
    every model already has, is now absent from the stream, so the store's
    first admissions cannot be the tautologies the world run admitted — and
    cannot be the easy win either.
65. **A revisit is an attached pass after the stream with no consolidation
    after it, and a detached arm has none.** A detached pass is one draw of
    an evaluation, so meeting a batch again would repeat pass *k*; the
    attached arm's pass-*k* score is the first-sight baseline for its own
    revisit. *Risk:* the revisit passes are closed on — observations filed,
    proposals drafted — so a second revisit reads a store the first one
    touched, and the lint's per-pass checks run on them like any pass.

66. **Quality is graded by derived floors and a twin world, not by a
    judge.** Economy divides the knowing policy's calls (declared on the
    task; the budget is that plus the family's slack) by the calls spent,
    turn economy the same over model turns, and method transfer replays
    the pass's last shell command in a twin drawn from a second seed over
    the same names and routes. *Right:* the hint's value shows where
    correctness saturates — the probe passed five of seven lessons at
    first contact — and none of it needs a rubric. *Wrong if* the floor is
    gamed: a lucky one-call guess scores full economy, which is why
    transfer stands beside it; and a solution computed in the model's head
    after a `cat` scores zero transfer though it passed, which is the
    scorer's reading (no replayable method) and not the model's.
67. **A failed row's economy is zero, its transfer unevaluable.** Zero
    because a failed pass has no solution to be economical about and the
    series must not reward a cheap failure; unevaluable because a method
    that produced the wrong answer has nothing to transfer. *Risk:* the two
    conventions differ, so the two means over a batch are over different
    denominators; the log prints both with `—` where nothing was
    evaluable.
68. **The twin shares structure and varies data; the structural draw is
    separated from the data draw.** The generator's first seed fixes how
    many files, pages and which route, the second the counts, items and
    rows; the twin reseeds only the second. *Right:* a command replayed in
    the twin meets the same names and shapes and only its arithmetic is
    tested. *Risk:* separating the draws changed the pool since the probe
    ran (the evolution log rebuilds an old arm's batches from recorded task
    ids and says so); and six twins — the moved routes that answer `ok` —
    carry no data to vary and are identical to their tasks.
69. **The stream run's record is derived from the tree that ran it, not
    from `main`.** The logs and the curve report under
    `experiments/results/stream/` were regenerated from a worktree at
    67c9ff0 plus the close fix, and the README's numbers are theirs.
    *Right:* the rows were scored against that pool, and the symptom
    derivation reruns the naive policy against the task's world — a
    different data draw would mislabel rows. *Wrong if* the reader expects
    `hgi experiment evolution` on `main` to reproduce the files: it
    rebuilds the arms from recorded task ids with a warning and the
    symptoms may differ; the results directory is the record.
70. **The detached arms were redrawn alone rather than kept with their
    429 rows.** *Right:* a 429 after five retries is the endpoint's
    concurrency ceiling, not the model's first contact, and six and seven
    such rows in eighty would have moved the detached curves by the size
    of the effects being read. *Wrong if* a redraw is read as the same
    draw: the detached curve is now a second draw of the same batches,
    taken an hour later, and the attached arms' rows show no 429, so the
    comparison is paired per batch but not per hour.
71. **The strict attached arm was rerun from scratch, not resumed.** The
    runner has no resume; `--force` discards the store. *Right:* a resumed
    store would mix a first run that consolidated differently with a
    second; one run is one record. *Wrong if* the first run's
    consolidations mattered: they did (item 25) and survive only in a
    note. A resume that replays the recorded sessions and re-consolidates
    is the mechanism a long run needs.
72. **The arms ran concurrently.** *Right:* the five arms finished in
    ninety minutes instead of four hours on the night before the
    submission. *Risk:* item 36 — the detached draws paid in 429s and were
    redrawn; the attached arms' rows show no rate-limit error, so their
    curves stand.
73. **Independence and the watch's direction are the code's readings, not a
    lens's.** The distinct-session count of a draft's evidence against the
    bar is a lint floor check (`independence`) the committer refuses on,
    and a sketched watch that fires on success is dropped from the draft
    before any context opens — the watch is optional, the draft is not —
    with the drop recorded on the ledger claim; both join the attack first
    with no lens and no call, an examiner claim on either class that
    contradicts the computed reading is discarded, and L-0005 and L-0008
    are seeded retired through the crystallization door. *Right:* over the
    stream run's fifteen attacks `warrant:watch-direction` landed nine
    times and was wrong at least twice (on `task_pass_rate < 1.0` and
    `== 0.0`, both of which fire on failure) and `warrant:independence`
    landed on a draft whose group came from two sessions; a count and a
    comparator are gates, and a gate asked as a question is a lens whose
    answer has crystallized. *Risk:* a register seeded before this change
    still walks the two lenses and pays two calls per draft for claims
    that are then advisory; and a watch dropped is a record unwatched —
    its warrant returns only through the retirement ratio or a pass's
    close-time contradiction, never through the oracle's series.
74. **A landed abstraction claim amends; it never declines.** With no
    premise kill beside it and the bar met, the consolidator is re-asked
    once (the `promote` request: the payload, the refutation, the task ids
    and the instances) to restate the payload at the transferable shape
    with the instances kept as anchors; the abstraction angle is walked
    again over the promoted draft, the entry keeps the nominated text as
    its claim, the promoted text as its amendment and the promotion under
    `coding`; when no promotion comes back the adjudicator's
    `admit-amended` restates the payload and the committer admits the
    amended text. *Right:* on gpt-oss-120b the claim landed four times and
    was right each time, and the adjudicator never once returned
    `admit-amended`: an instance-shaped lesson is a lesson mis-stated, not
    a lesson refuted, and dropping it drops the recurrence with it. *Risk:*
    one more consolidator call per landed claim, whose product only the
    re-walked abstraction angle judges; a consolidator that promotes past
    the evidence yields a floating payload the anchors no longer
    instantiate, which only the adjudicator's exemplification check reads;
    and the re-ask returns the whole payload, so a promotion can change
    more than the instance's name.
75. **A decline stands only on an upheld premise kill.** The adjudicator's
    `decline` with no landed `premise:` claim is overridden to an admit —
    amended where it offered an amendment — the entry keeps the attack
    named (`survived-with-attack-named`) and its outcome says which token
    was overridden and why; the floor still refuses an overridden draft
    below the bar; defer and escalate are the adjudicator's as returned.
    A decline that stands is always `premise-killed`, so `attack-landed`
    is reached only from the human queue. *Right:* the run's two premise
    kills that stood were right, and every other decline was on a class
    that is now mechanical or amend-only. *Wrong if* a refutation exists
    that is neither a premise kill nor a mis-statement — an anchor that
    does not exemplify the payload is the case the prompt still names, and
    its decline is now an admission the floor cannot catch (exemplification
    is residue); the override is written on the outcome so the ledger shows
    where that happens.
76. **A model call the endpoint refuses fails the row, scored, not
    dropped** — and a refusal the model caused, by emitting tool-call
    arguments that are not JSON, is counted the same way (economy run,
    `claude/nervous-rubin-e8e759`). *Right:* a row the harness could not
    finish must not vanish from the denominator, and a model that writes
    malformed output did fail the task. *Wrong if* the endpoint's
    validation is stricter than the loop's: the loop tolerates a bad tool
    call and lets the model recover, the endpoint does not, so the row
    measures the endpoint's contract as much as the model; item 42 carries
    the fix.
77. **The shape-radius sweep: exact match already conflates lessons, so
    widening the Jaccard radius cannot buy precision on this data — τ\*=1.0,
    and the fix is the coding (item 40), not the radius.** A self-contained
    analysis (`hgi/grouping_sweep.py`, `hgi grouping-radius`, scorer test
    `tests/test_grouping_sweep.py`) sweeps τ over
    `{1.0, 0.67, 0.5, 0.33, 0.25, ~0}`, clustering observations by
    single-linkage connected components on `jaccard(shape_i, shape_j) >= τ`
    and scoring each clustering against the curriculum lesson the
    observation's anchor resolves to (the true label). *Dataset:* the
    recorded attached stream arms on disk (`runs/stream/{120b-attached,
    120b-strict, 20b-attached}`, not freshly generated), combined and
    session-namespaced per arm — N=104 labeled observations over 27
    sessions and 6 lessons (only `bom` drew none); the curve and table are
    written to `experiments/results/grouping-radius/radius.{json,md}`.
    *The curve* (τ → homogeneity / cross_lesson_clusters / lessons_at_bar):
    1.0 → 0.45 / 9 / 0; 0.67 → 0.45 / 9 / 0; 0.5 → 0.09 / 3 / 0;
    0.33 → 0.09 / 3 / 0; 0.25 → 0.09 / 3 / 0; ~0 → 0.00 / 1 / 0. *Reading:*
    the win the widening was meant to buy (`lessons_at_bar` — a lesson
    reaching the 2-distinct-session bar inside one pure cluster) is zero at
    every τ, because the precision cost is already paid at τ=1.0: the blind
    coder shapes on the tool or the triage, not the world's convention, so
    one shape covers many lessons before any merge — `[http-tool]` →
    {moved-v2, paged-api, token-route}, `[shell-tool]` → {csv-quoted,
    footer-row, trailing-newline}, `[test-failure-triage]` → four lessons.
    The recommendation rule (lowest τ with `cross_lesson_clusters == 0`,
    max `lessons_at_bar`) has no admissible τ — even exact match is impure
    — so it falls back to the baseline τ=1.0 with the caveat that widening
    the radius cannot recover a precision the join never had. *Right:* this
    is the same diagnosis as items 39 and 40 reached from the run logs, now
    measured — the shapes are generic, so grouping is not the lever;
    fixing the observation coding to name the convention (item 40) is.
    *Caveat:* thin data (N=104, ~15 obs/lesson) combined across two models
    and two families (curriculum, curriculum-strict), so the shape
    vocabulary is heterogeneous; the conflation holds within each single
    arm too, so it is not an artifact of combining. The scorer is trusted
    independently: `test_grouping_sweep.py` builds a synthetic labeled
    fixture whose Jaccard geometry is exact and whose τ\* (0.25) is known,
    and asserts the whole curve and the rule. *Next:* widening the labeled
    set with the real coder over the full 7×12 pool (needs a W&B inference
    endpoint; not run here) would sharpen the curve, but the recommendation
    would only change if fixing the coding first made the shapes
    lesson-specific. The number seeds a tunable registry bar default that a
    separate change wires into `group_observations`.
78. **The two parse floors that refused every draft before adjudication are
    relaxed** (commit `ceb51b6`, addressing item 32 gates 1–2 and item 41).
    `Sketch.not_this` defaults to `[]` and the complement law warns rather
    than fails on a consultation latch with no exclusions; an edit rung
    (`hook-edit`, `counterfactual-edit`) that names no record on an empty
    store is displaced to `new-decision` (keeping `rung_why`) instead of
    refused, while one that names none when records exist is still refused.
    *Right:* seven of nine 120b drafts and six more in the economy run died
    here before any verdict; a floor refusal only kept the lesson out of the
    store where it could be corrected, and the precision leg grows `not_this`
    from `not_applicable` notes after a record fires wrongly. *Risk:* a
    record with no exclusion fires on every presentation its terms match; the
    retirement ratio bounds one that never applies, so the cost is a window,
    not the store. The repair-turn alternative (re-ask the model with the
    refusal, item 41) was left unbuilt — the floor relaxation is item 32's
    prescribed cheaper first move.
79. **A record's consultation hook is seeded from the anchor tasks' own
    declared work-shape terms** (commit `f05eb7b`, addressing item 39). When
    a draft is assembled from a group of observations, the union of the
    tasks' `shapes` (resolved through each observation's anchor call to the
    row that names its task) joins the terms the drafter chose. *Right:* the
    economy run's one admitted record never fired because its hook carried
    only the blind coder's coding of how the failure presented, which the
    next task's classification did not share; the task's own term (`http-tool`)
    is on the anchor and matches the boot index. *Risk:* the seed broadens
    the hook toward whatever the task declares, so a record can be consulted
    on a task that shares the tool but not the fault — the same generic-shape
    problem decision 77 measures, here on the hook rather than the group; the
    not-this exclusions and retirement are what bound it.
80. **Near-verbatim restatements that never co-applied are folded** (commit
    `54635f6`, addressing item 33). `index.restatements` filters the
    shared-hook pairs to those with no lineage relation (connected components
    over the DAG's supersedure/split/fold edges) whose decision payloads
    overlap at or above a token-Jaccard threshold (0.6), and the
    consolidation brief surfaces them as convergence-shaped rows so each is
    drafted as a fold and adjudicated behind the floor. *Right:* the strict
    arm admitted D-0004/5/6 restating D-0001/D-0002, and every boot carried
    all of them; nothing nominated two lineage-unrelated records with the
    same latch and alike payload. *Risk:* the alikeness is a token-overlap
    heuristic that only *proposes* the merge — a threshold too low folds
    distinct records, too high misses restatements; 0.6 separated the run's
    cases but is a tunable parameter, and the floor and adjudicator are the
    real gate.
81. **The close elicits the world's fact, not the score it failed** (commit
    `3131406`, addressing item 40). The observation lens's brief drops the
    row's scores and every series-named field, and the pass is asked to name
    the convention the attempt turned on (a footer row, a missing newline, a
    quoted comma), never the check it scored against. *Right:* in the economy
    run none of forty observations named the convention in words the blind
    coder could group on, so two silent lessons stayed 24/24 naive; grouping
    starved before any bar. *Wrong if* the coder shapes on the tool anyway —
    decision 77 shows the shapes are generic even with better `noticed` text,
    so this fixes the observation's words but not yet the coder's vocabulary;
    making the coder shape on the convention is the unbuilt next lever.
82. **A malformed tool call no longer poisons the conversation, and its
    symptom reads apart from a genuine endpoint fault** (commit `c22f147`,
    addressing item 42 and decision 76). A tool call whose arguments are not
    valid JSON is replayed into history wrapped as a valid object
    (`{"_raw": …}`) so the endpoint accepts the next request and the model
    reads the bad-call result and retries; the wasted turn still costs turn
    economy. `error:model-call` splits into `error:endpoint` and
    `error:malformed-tool-call`. *Right:* one row of 96 was lost outright
    because the raw string made the endpoint refuse the next request, and the
    symptom conflated the model's fault with the endpoint's. *Risk:* the
    malformed flag is sticky for the row, so a later endpoint fault after a
    malformed call reads as `malformed-tool-call` — a retrospective grouping
    choice, defensible since the poisoning mode should no longer recur.
83. **The experiment runner is pinned and its detached draws serialized**
    (commits `0c3e659`, `941a6ef`, `f815546`, addressing items 35, 36, 34).
    The evolution writer imports eagerly with the runner and `arm.json`
    records the tree's commit; detached passes run serially by default
    (`ArmSpec.serial_detached = True`), with the concurrent thread-pool path
    behind the flag and the Weave client re-entered per worker thread when it
    is used. *Right:* quality commits moved the code under a running arm and
    changed a log; five concurrent arms drove the endpoint past its
    concurrency ceiling into 429s on the detached rows; the detached threads
    lost their Weave traces. *Risk:* serial detached draws are slower — a run
    that had headroom under the ceiling now pays wall-clock it need not; the
    flag restores concurrency, and Fix 3's `rejoin` is moot under the serial
    default (no worker threads spawn).
84. **The recurrence count is graded for the adjudicator** (commit `bd5df03`).
    `recurrence_reading` bands the distinct-session count N against the bar
    (below the floor / modest small-N / strong at ≥ 2×bar, mirroring the
    vocabulary nominator's small-N reading) and enters the adjudicator's
    request as context beside the draft, attack and oracle. *Right:* above
    the floor the count was discarded, so N=2 and N=10 read alike; a stronger
    recurrence is corroboration that a pattern is a real world-fact and bears
    on whether a premise refutation holds and on defer-versus-escalate.
    *Risk:* it is adjudicator-facing context only — the floor and the
    premise-kill logic are byte-for-byte unchanged, so N cannot mechanically
    admit a draft; a model that over-weights it could lean toward admitting a
    thinly-founded draft, which the premise checks and the floor still catch.
    Post-elegant-faraday a soft decline is already overridden to admit, so
    the count's remaining room is the adjudicator's reasoning, not a verdict
    override; whether N should ever soften a premise kill was left as the
    owner's call (it does not today).
85. **A refused draft's observations stay in the open pile** (commit
    `5db9358`, a regression lock, addressing the owner's requirement on
    item 39). Only `store.admit` promotes an observation; decline/drop, a
    floor refusal and escalate call only `drop_draft`, which touches no
    observation, and a deferral's claim on a live draft's evidence is the
    intended exception. *Right:* a lesson refused at N=2 must be able to
    regroup with a third instance at N=3 rather than be discarded; the test
    proves a premise-killed decline leaves its two observations open and they
    regroup at N=3. *Risk:* the open observations re-nominate the same lesson
    every pass until it is admitted, deferred or its observations retire —
    churn that decision 84's grading and the retirement ratio, not a
    suppression, are meant to resolve.
86. **The store is readable from outside the loop, through its projections**
    (`hgi consult`, `hgi/consult.py`; the skill `consult-decisions`). The
    read is additive: a new module registered beside the pass commands, no
    change to boot, close or consolidate, and no write to the store — the
    test hashes the tree before and after. Stage one is built from the
    `summaries`, `hooks` and `lineage` projections and so passes the
    settlement test by construction; stage two opens the record for the
    payload. The two latches are the boot's own: exact terms through the
    hook-major index, and the lexical nominator at the same two-token floor.
    The shape follows the sibling projects' consultation reads (WorldVue's
    `rules:adoption-status --shapes`, the Gauntlet's `gauntlet decisions`
    with its `adr-read` skill): an activation-only scan that withholds the
    payload, a targeted read, an unknown token refused with the vocabulary
    listed, and the reader as the matcher. *Right:* an end user's agent
    gets the lessons the loop admitted without running a pass, and the
    loop's ledgers stay the loop's — a consultation from outside files no
    disposition, so the applied-over-considered ratios the retirement leg
    reads are not diluted by reads it cannot score. *Risk:* no guard runs,
    so the reader decides the exclusions alone, and the `excluded_by` flag
    is the stub guard's literal reading, which a paraphrased exclusion
    escapes; the lexical route nominates on two shared stems, a floor that
    over-reaches on common words (`tool`, `call`) and under-reaches on a
    hook written in vocabulary the problem does not share — the surface
    fallback and the reader's eye are the recovery, not a better matcher.
    What an outside reader learns has no channel back into the store; if
    the reads should count, a consultation session kind with its own
    dispositions is the addition, and it would need the retirement ratio to
    distinguish it from a pass.
87. **The blind coder shapes on the convention, not the tool — the deeper
    lever decision 77 exposed** (commits `fe7a303`, `29e6d95`, addressing
    item 40's unbuilt next lever and decision 81). Decision 81 made the
    `noticed` name the world-fact; this makes the coder *group* on it. The
    work-shape vocabulary gains a convention-major granularity beside the
    tool-major cues (`route-versioned`, `listing-paged`, `route-guarded`,
    `field-quoted`, `summary-row`, `line-unterminated`, `byte-order-mark`);
    `coder.md` and the coding reply shape now tell the coder to shape an
    observation on the finer of the two its noticing names, a tool-major
    term only for a way of working with no world-fact behind it (a budget, a
    retry, a wrap) and `other(<convention>)` for a convention the vocabulary
    lacks. The tool cues stay: the boot classify still keys a consultation
    hook on the coarse cue, where the convention is hidden from the task
    prompt, so the stub gives the coder a convention keyword map distinct
    from the classify's tool map and `_classify` is untouched. *Measured*
    (`hgi grouping-shaping`, tests `test_convention_shaping.py`,
    `test_coder_convention.py`): on a synthetic labeled set in the blind
    close's voice the τ=1.0 grouping the sweep left in place moves from
    impure to pure — homogeneity 0.37→1.0, cross-lesson clusters 2→0,
    `lessons_at_bar` 1→7 (all seven), four shapes for seven lessons becoming
    one convention shape per lesson; re-coding the recorded arms (118 obs)
    both ways corroborates on real noticings, 0.48→0.96 homogeneity and 1→5
    lessons at the bar. The grouping radius did not move; the coding did.
    *Right:* two misses of one convention now share a shape and two of
    different conventions differ even when both called the same tool, which
    is exactly what decision 77 measured the tool cue could not do; the
    coder stays blind by construction — the coding request carries each
    observation's name and noticing and the flat term list, never the task
    id, the lesson or a score, a leakage guard pins it. *Risk:* the
    convention terms align one-for-one with the curriculum's scoring lessons
    because both enumerate the same world-conventions — the mechanism's
    target, not a leak, since the coder infers the term from the noticing
    prose, but a vocabulary that *is* the answer key's partition is a soft
    leak of the label space, and the guarantee rests on the noticing being
    blind (decision 81) and the per-observation label never in context. The
    numbers are the stub, a lexical proxy for the model's convention
    inference; the pending confirmation is a live re-score of freshly coded
    observations on `openai/gpt-oss-120b` (needs `WANDB_ENTITY` and a weave
    project), not run here — no live curve was fabricated. The recorded
    re-score's residue (homogeneity short of 1.0, two clusters still
    crossing) is the pre-81 noticings' noise, the gap the live re-score over
    post-81 noticings would close. If the model does not normalize a
    convention onto the same registered term across clothes, exact-match
    grouping splits a lesson on near-shapes — the completeness failure the
    radius sweep was meant to catch, now guarded only by τ\*=1.0 standing;
    the escape-to-vocabulary-bar path is the doctrine's answer if a
    convention the seed lacks recurs.

88. **A procedural fast-fail family from Reasoning Core: regex-following and
    cfg-generation, graded by the generator's own checker** (commits
    `881e9f7`, `3c5e26b`, `897c144`). Reasoning Core (`sileod/reasoning-core`,
    MIT, rev `1c87ac6`, v0.5.0, arXiv:2509.18083) is structurally the
    `curriculum` pattern — procedural, many instances of one lesson, an
    executable checker — with a single integer difficulty knob (`level`) its
    configs fold into pattern depth, rule count, sentence depth. Two families
    are added over its generators, `reasoning-core` and its strict twin
    `reasoning-core-strict`, built from the `mbpp` shape (pinned file +
    `fetch` transcriber) so the suite hash is stable and a run touches neither
    the network nor the generation stack. Scope is the generators that make
    the agent *churn* shell calls to verify a candidate — regex-following
    (produce a visible-ASCII string a regex fully matches) and cfg-generation
    (produce a string of ≥ `min_tokens` terminals a grammar derives) — so
    decisions get generated; the answer-only RC generators (regex
    equivalence/containment, parsing-derivation graded by edit-similarity,
    continuation) are the deferred later slice noted below. *What grades:* the
    generator's own verdict, never a stored-answer compare — `regex.fullmatch`
    over an admissible sample (RC's `regex.py` `_is_sft_sample`), and grammar
    membership under NLTK's Earley chart parser (the parser RC's grammar tasks
    use). Note RC's own `RegexFollowing.score_answer` *is* a canonical-string
    compare; grading membership (any match) is the deliberate reading of the
    task's "produce a string matching" framing and of the instruction to grade
    by the checker, not by a compare. The checker inputs are pinned (the
    regex; the grammar with its start and token floor) and no witness is —
    the file cannot leak an answer, and for regex there is no unique answer to
    leak. *The strict twin:* `knowing={"shell":1}` (a knowing policy verifies
    once); lax leaves one call to spare so a pass may iterate on a candidate,
    strict holds exactly the floor so a wrong first candidate cannot be
    repaired — the `curriculum`/`curriculum-strict` slack `{1,0}`, differing
    only in slack. *Difficulty-knob values chosen:* RegexConfig `level` 3
    (alternation, groups, exact counts, anchors, word boundaries), witness
    length ≥ 2 to drop trivial one-char targets; GrammarConfig `level` 2 with
    the witness length kept in 6–12 tokens, `min_tokens` set to the witness's
    own length so a member provably exists. Twelve instances of each are
    pinned; ids and integer seeds are disjoint from every other family's
    (string-keyed) seeds and clothes. *Right:* the two families build (hash
    `2eb120f` over the pair), 513 tests pass including a new
    `test_reasoning_core.py` that shows two distinct strings both matching a
    pattern and membership over the token floor — a verdict, not a gold
    string; the checks catch broad exceptions and return False, so a bad
    pattern or an out-of-vocabulary token is a failed task, never a raise from
    the grader (the `mbpp` convention). *Determinism, and what it cost:*
    `gramforge.generate` reseeds Python's RNG from entropy on every call
    (`seed=None`), so the bound name is patched to draw seeds from a
    per-instance `random.Random`, and `faker` is seeded before the task
    modules import (their terminal word lists are import-time); the CFG
    generator is additionally forced onto `random_productive_cfg`
    (`random_grammar_prob=1.0`, free-form off) because the pre-built english
    grammars reach `trim_grammar`, which seeds a `random.Random(None)` from
    entropy and cannot be reproduced — the synthetic productive CFGs (bracket
    nesting, word terminals) are kept, the natural-language grammars dropped.
    Cross-process regeneration is byte-identical (sha `5a25c31`). *Risks and
    leftovers:* (1) the ~0.5 first-sight target is a **hypothesis, not
    measured** — no inference endpoint here, and these families carry no stub
    (like `mbpp`), so they fail the deterministic stub harness and
    `naive_outcome`/`symptom` return no-naive; the first live arm run is what
    calibrates level and budget to the 0.47/0.50 band, and difficulty is
    **non-monotonic** in `level` for "produce a match" — high levels admit
    trivial short matches, so raising `level` is not a reliable hardener, the
    lever is pattern/grammar structure and the token floor. (2) `fetch` is not
    runnable in the standard hgi env — the generation stack (`reasoning_core`,
    `gramforge`, `greenery`, `faker`, `exrex`) is deliberately not a runtime
    dependency (only `regex` and `nltk` are, for the checks and the agent's
    shell); the committed jsonl is the reproducibility artifact, and re-fetch
    needs that stack installed and would rewrite the file and move the hash.
    (3) the broad `except Exception` in the checks could mask a genuine
    checker bug as a failed task. (4) the agent's shell membership check
    depends on `nltk` being importable in the run's `python3` — true now that
    it is a dependency. (5) no metamorphic `twin` is attached (the
    `method_transfer` scorer will not read this family); a second-seed twin is
    the addition if it should. *Next slice:* the answer-only RC generators,
    and a live arm run to place these two on the target band before they enter
    a stream/transfer design.
89. **A text-to-SQL family whose convention is the database's own schema,
    and the credit correction it exposes** (commits `9379d35`, `f22c079`,
    `c6685d1`, `ae758f0`, addressing DATASET-EVAL-RESEARCH.md's BIRD
    recommendation and its required evaluator correction). Three new
    families — `text2sql`, `text2sql-strict`, `text2sql-holdout` — over
    BIRD mini-dev's `financial` questions and one pinned SQLite database.
    The agent inspects the schema with the shell tool and returns a
    `SELECT`; the hidden check re-executes it against the shipped database
    and compares its rows to the dataset's own gold query's rows (a
    float-rounded, order-insensitive multiset), never a string comparison.
    The gold SQL is the grading key: pinned in the record, re-executed by
    the check, kept out of the prompt and `Task.row` so it cannot leak — the
    way `mbpp` reruns `tests.py` rather than diffing source. The graded and
    strict families carry the same ten questions and differ only in slack
    (three shell calls vs the knowing floor of one), mirroring `curriculum`
    vs `curriculum-strict`; the holdout six are a template-disjoint group
    over the same schema, for transfer. *Right:* the transferable convention
    is the schema's SQLite-dialect quirks the BIRD evidence never states —
    text dates reached with `STRFTIME` (there is no `YEAR()`), a ratio
    needing `CAST(... AS REAL)` or SQLite integer-divides, coded statuses, a
    reserved-word `order` — so a decision learned on one question scores on
    an unseen one over the same database, which is what the stream/transfer
    experiments measure; the evidence stays in the prompt so a question is
    answerable, but names the domain mapping, not the dialect. A ratio
    without the CAST is the crisp case: it executes cleanly and returns the
    wrong number, so `credit_table`'s old `not row.get("error")` would have
    credited a wrong answer — `hgi.consolidate.row_passed` now reads the
    oracle's per-row `task_pass_rate`, falling back to absence-of-error only
    for a legacy row that carries no per-row score (which is why the
    existing credit tests, whose rows carry none, are unchanged). The
    database ships through a new general `Task.blobs` binary channel
    (base64 in, bytes out), hashed by the digest of its bytes so a
    megabyte-scale asset does not bloat the composition hash, and the
    `blobs` key is absent when a task carries none so every existing suite
    hashes as before. *Decisions and their risks:* (a) The full
    `financial.sqlite` is 71 MB, all but 24k rows of it the `trans` table
    (1M rows); the pinned `text2sql.sqlite` keeps every table whole except a
    `trans` sample (accounts ≤ 20, for schema fidelity), 856 KB. No selected
    question reads `trans` — `fetch` verifies each gold on the reduced
    database before pinning, so every gold returns exactly the rows it
    returns against the full database, and the four trans-touching financial
    questions (#116/129/145/159) are simply not selected. *Risk:* a future
    question added to `SELECTED` that reads `trans` would grade against the
    sample, not the world; the fetch sanity pass catches a gold that fails
    outright but not one whose rows the reduction merely changed, so any
    trans-reading question needs the sample widened or the id left out. (b)
    The pass-rate target (~0.5 first-sight) is a design goal, not measured
    here — no model was run; the difficulty is a guess from BIRD's own
    moderate/challenging mix under a three-call budget. *If it lands off
    the band,* tune by question selection (the 32 financial questions, minus
    the 4 trans ones, are the pool) or the slack budget, not by touching the
    check. (c) The task shapes are the tool-major cues (`shell-tool`,
    `file-tool`, `tool-budget`) the boot classify keys on, since the schema
    convention is hidden from the prompt (that is the point). Beside them a
    new convention-major work-shape term, `schema-coded-value`, was seeded
    (`hgi/genesis.py`, `hgi/stub.py`, `hgi/roles/coder.md`, following
    decision 87's precedent exactly — the seed and the stub, not the
    diverged store snapshot, whose committed registry predates the
    convention terms), so the blind coder groups two text-to-SQL misses over
    the one fixed schema — a coded-status miss and a text-date miss — under
    the same shape rather than the coarse tool cue. It is deliberately one
    term, not one per quirk: the family runs over a single database, so its
    quirks are one convention and a decision hooked on the term can carry the
    whole schema, which is the transfer the family demonstrates. *Right:* the
    grouping is sharpened; *the limit that remains:* the term sharpens the
    consolidation grouping and rides the decision's hook, but boot retrieval
    still keys on the tool cue (the convention cannot be read from the
    prompt), so a schema-convention record is retrieved for any shell-tool
    task via the tool-major terms `anchor_terms` seeds — the coarse-retrieval
    limit decision 87 already documented, not new here. (d) `fetch` downloads BIRD's 346 MB dev bundle and verifies
    `financial.sqlite` against a pinned SHA-256; `$HGI_BIRD_DEV_ZIP` caches
    it. Re-fetching is rare (only to re-pin) and rewrites both the jsonl and
    the committed 856 KB database, changing the suite hash — the same
    contract as every transcribed family.
90. **The signal half of the battery lands on the per-lens register, beside
    the decoy half** (commit `ce19b3d`). The battery scored two axes onto each
    lens — `decoy_rejection` and `answer_variance` — but the `SignalCaught`
    scorer's product went only to the global fact series
    `lens-battery-v1/signal_caught`, never onto the lens register, so a lens
    that rejected every decoy while catching half its genuine signals read
    healthy per-lens and the partial signal-miss was invisible. `LensTelemetry`
    gains a `signal_caught` cell seeded `design-stage` the way the other two
    are (the genesis seed and the committed lens register carry it), and
    `telemetry_from` computes the per-lens caught fraction over the signal
    items exactly as `decoy_rejection` is computed over the decoys —
    `1.00 — 2/2 planted signals caught (lens-battery-v1)`, or `unevaluable` when
    a lens has no signal — flowing onto the register through the existing
    `model_dump`. *Right:* the register now carries both halves of the same
    run, so a lens's floor gate (reject the decoy) and its recall (catch the
    signal) are read side by side; on the honest stub L-0004 reads 1.00 and
    L-0003 reads 0.00, the miss the decoy axis alone showed as a clean 1.00.
    *Risk:* the fraction is the stub answerer's, a lexical proxy for the pass
    model's filing, and the two axes share the one battery run — a dataset that
    plants too few signals reads a coarse fraction (2/2 is the current plant),
    and a lens with no signal items reads `unevaluable`, never a false 1.00.
91. **A human steer can cite a lens, and the register reads the steers that
    cite it** (commit `ecf1d81`). Every lens declared
    `"miss_stream": "steers/ citing this lens"`, a dead literal no code
    populated: `indictment()` resolved ids through `store.find`, which reaches
    only file-layout record kinds, while lens ids live in the register, so a
    note naming `L-000x` was dropped. `indictment()` now resolves a lens id
    through `store.registry` when no store record matched the note — records
    come first, so a note naming both keeps its record, and only a note naming
    no record but a registered lens is credited to the lens — and
    `populate_telemetry` reads `store.all("steer")` and replaces each battered
    lens's static `miss_stream` with the steers that cite it,
    `1 steer cites this lens: T-0003` or `no steer cites this lens
    (lens-battery-v1)`. *Right:* a lens id flows harmlessly through every
    consumer of `Steer.indicts` — no fire latches on a lens id, so `file_note`
    lands the steer in `system-misses/human-catches` (the right cell: a human
    caught a lens miss the system did not), and `matrix`, `recall` and
    `attacker` gate their lens-id reads on `decisions`/`accepted` records that
    never include one. *Risk:* the `indicts.record` field now carries either a
    record id or a lens id, and the reader tells them apart only by prefix; the
    matrix's `indicted` set mixes both, harmless today because fires and
    dispositions never key on a lens, but a future reader that assumes
    `indicts.record` is always a decision would misread a lens-citing steer.
    The miss stream is written only for the lenses `populate_telemetry`
    touches (the battered ones), so a boot lens no battery reaches keeps its
    static literal until a run writes it.
92. **L-0009, the recovered-miss lens: a passed row that self-corrected on a
    non-transient convention is a lesson, not a discard** (commit `9ccf21b`).
    Across `runs/`, 375 rows passed but 87 recovered from a non-transient fault
    on the first attempt — 37× a `route-guarded` 401 (`/secure` needs
    `?token=`), ~15× a `route-versioned` 410 (the API serves `/v2/…`), plus
    awk/traceback/call-budget faults — real conventions the pass learned and
    self-corrected on, discarded today because the row scored 1.0: L-0004's
    failed-row filter never sees them. L-0009 is a close generative lens, host
    `close`, contact `artifact`, walked once per row that is the *complement*
    of L-0004's — a passed row (`_index.row_passed`) carrying at least one
    non-transient tool error (`_recovered_nontransient`) — its subject shape
    identical to L-0004's per-row subject, so `_artifact_subject` is shared and
    L-0004's read is byte-for-byte unchanged. `file_observations` no longer
    hard-codes `L-0004`; it walks `OBSERVATION_LENSES`, the module constant
    naming the observation-producing close lenses, and the same
    `{noticed, anchor}` → `Observation` logic files for all of them. The stub's
    `_recovered_misses` files a noticing that carries the fault's cause (so the
    blind coder groups it on `route-guarded`/`route-versioned` through the
    convention keywords) and files nothing when the only fault was transient.
    The battery plants two decoys (a 502/503 that cleared on retry) and two
    signals (the 401 token, the 410 route-version); the lens rejects the
    decoys and catches the signals, reading `1.00` on both axes. *Right:* the
    recovered convention now reaches the observation ledger, where before it
    left only a green score — the pass's strongest evidence of a rule the store
    still lacks a hook for, filed at the floor as an observation, never a rule.
    *Risk:* the "non-transient" cut is only as good as the `transient` flag the
    tool layer stamps on a `tool_error`; a fault mislabeled transient is a
    signal L-0009 silently drops, and one mislabeled non-transient is a decoy
    it files (the L-0004 counterfactual's overshoot, mirrored). The stub is a
    lexical proxy for the pass model's convention inference; a live re-score is
    what confirms the noticing groups on the convention, not the cause string.
93. **L-0010, the off-map noticing lens: a failure the store had no hook for is
    a rule that is missing, not just telemetry** (commit `40c85ea`). When work
    fails and matches no hook, `dispose` records a bare `fired-off-map`
    disposition (`record="none"`) — in one arm six such sessions produced only
    telemetry, no proposition, and nothing turned the store's strongest
    "a rule is missing" signal into a noticing. (Distinct from L-0002, which
    asks after records that *exist* but were not reached; L-0010 is failure the
    store had *no* hook for.) Because close lenses walk before `dispose`, L-0010
    cannot read the disposition — it reads the raw off-map condition, the exact
    predicate `dispose` files `fired-off-map` on: `not session.consulted and
    any(r.get("error") for r in rows)`. It is a close generative lens (host
    `close`, contact `record`) with a whole-pass subject carrying that off-map
    flag and the failed rows a missing-rule noticing anchors on (a failed row's
    call); it is added to `OBSERVATION_LENSES`, so its `{noticed, anchor}`
    findings file as observations too. The stub's `_off_map_noticings` files a
    missing-coverage noticing when the subject is off-map and nothing when a
    record was consulted; the battery plants two decoys (a failed pass that
    consulted a record — a hook fired, not off-map) and two signals (a failed
    pass that consulted nothing), reading `1.00` on both axes. *Right:* the
    off-map failure now reaches the observation ledger where it fed only the
    detection matrix's bottom-right cell before — and that cell shrinks as a
    consequence: `hgi.index.true_misses` counts a failed, unconsulted row only
    when the session filed no observation from it, so an off-map row L-0010
    anchors a noticing on (`observed_from` matches the call) is no longer a
    silent true-miss but a filed lesson. *Risk:* the off-map cut is coarse — it
    fires on *any* failed row when nothing was consulted, so a pass that failed
    for a reason a rule could never cover (a flaky environment, a
    mis-specified task) files a missing-rule noticing the backward pass must
    still judge; the observation is at the floor, never a rule, and the
    counterfactual (a pass that *did* consult is not off-map) is the only guard.
    The anchor rides a failed row's call, so an off-map pass whose rows carry no
    call files nothing — the same count-and-provenance floor the other
    observation lenses answer to. index.py was read but not edited (another
    change owns it); the `true_misses`/matrix interaction above is behavioral,
    through the observation L-0010 now files, not a code change here.
94. **The mint ladder: the miss stream climbs to activation — two same-class
    off-map failures nominate new coverage** (commit `f8463c7`). The detection
    matrix computed the bottom-right cell (`hgi.index.true_misses`, the failed
    rows nothing caught) and displayed it, but nothing consumed it to nominate a
    hook or a lens — the miss stream dead-ended. `hgi.index.mint_ladder` is a new
    read-only projection that joins it to nomination: a class of off-map failure
    (a closed attached session that consulted no record and failed a row, the
    same gate `true_misses` reads) that recurs across the independence bar of
    distinct sessions (`bars.decision.independent_observations`, two) and that no
    accepted record's consultation hook covers nominates new activation coverage
    — a consultation hook or a close lens keyed on the session's work-shape term.
    It is the complement of `recall`: recall reads the should-have-fired stream
    for a record the store *already holds* and nominates a hook-edit to widen its
    key; the ladder reads the failures the store held *nothing* for and nominates
    the coverage that is missing. A row an observation was filed from stays in
    the `noticed` list — the pass noticed it, no hook did, so it is still a miss
    of coverage. On the committed store it fires on two classes (`file-tool`,
    `output-schema`) at the bar. *Right:* the recurring off-map class, which
    decision 93's L-0010 turned into a per-row observation, now also nominates
    the *activation* fix — a hook or lens — rather than only feeding a rule
    candidate; a nominator, never a verdict, mirroring recall. *Risk:* the class
    is the boot classifier's work-shape term, so a miss on work that carried no
    term keys no hook and is not classed (a floor, noted in the projection), and
    two misses of the same term from genuinely different faults would nominate
    one coverage the human must still shape; the count is detection-limited — a
    lower bound the world's votes set, never a census.

95. **Seed stores and the seeded arms: a hand-authored mature store per world,
    injected before pass 1, as the compare/contrast against the loop's own
    learning.** `experiments/seeds/<world>/` holds what a store that had
    already learned the world would carry — `conventions` (9: the seven
    lessons plus the genesis retry and the budget plan), `world` (7: mbpp's
    test-first loop and triage, tables/api's parsing, coercion and scalar
    answer, the api retry and the page walk), `incidents` (4: the walk plan
    and the three decoy shapes as symptom signatures), `reasoning-core` (4:
    derive-then-verify, the regex witness rule, the grammar derivation with
    the start-symbol reset, the budget rule), `text2sql` (6: the schema card,
    TEXT dates, real division, coded literals, the reserved `order`, the
    one-call method). `hgi/seeds.py` injects them (ids minted past the
    store's own, priced for the pass model, write-seam lint, projections;
    `proposed_by = "seed"` on every record), an arm's `seed` field drives it,
    and `stream`, `transfer`, `world`, `incidents`, `reasoning-core` and
    `text2sql` carry `*-seeded` twins of their attached and strict arms.
    Every seed lints green injected into a fresh genesis store; none has been
    run on a real model. Why it may be right: the seeded − detached gap on
    batch 1 is the value of the decisions themselves, seeded − attached over
    the stream the cost of learning them, and the strict pools ask the
    knowledge-base question directly. Why it may not: (a) the seeds are the
    authors' reading of the family code, not the loop's reading of misses —
    a seed decision can be righter than any the loop would admit, so the gap
    overstates what the loop could reach on its own; the honest twin is the
    attached arm's late passes, not the seed. (b) The pass sees only id,
    terms, stakes and decision text (`suite/agent.py`), so the seeds carry
    the symptom signature and the exclusions inside the decision sentence;
    D-0003 of `incidents` is 1.7k characters and the boot's context grows
    with every co-applying record — on `world` sixteen records reach every
    task. (c) Five of the twelve sampled `api` tasks under `world.toml` are
    unpassable by any honest walk (two faulted calls plus the description
    plus the pages exceed the budget; `suite/families/api.py` documents slack
    for one fault), so the seeded arm's api ceiling is 7/12 and the world
    seed's page-walk decision tells the pass to stop within budget and
    report the cause; `versioned_status` has the same shape. (d) The
    reasoning-core verification depends on `uv run` putting the venv's
    `python3` (nltk, regex) first on the shell tool's PATH; a runner launched
    outside the venv fails every grammar check. (e) A seed keyed on the
    registered terms fires on every batch that presents them; per-task
    selection rests on the decision's opening clause, which the guard call
    does not enforce across a mixed batch. (f) The seeded arm still closes
    and consolidates, so its store can retire or supersede a seed decision
    the world contradicts — a seed the loop retires is itself a finding, and
    the evolution log can tell the two apart by `proposed_by`.
96. **The roles split with the forward pass alone on the actor, and the
    experiments dispatched in waves from a pinned tree** (reasoning-core and
    text2sql runs, 2026-09-13). Both experiments put the pass on a mid-sized
    actor (Qwen3.6-35B-A3B for reasoning-core, gpt-oss-120b for text2sql,
    gpt-oss-20b as the weak actor in each) and every other role —
    consolidator, examiner, adjudicator, coder and, at the user's direction,
    the reauthor — on `deepseek-ai/DeepSeek-V4-Pro`, set once in
    `[defaults.roles]`. A probe arm (`runs/rc-probe`, project `hgi-dev`)
    preceded the dispatch: two batches of three, consolidation every pass,
    which showed the teacher parsing on contracts priced for gpt-oss-120b
    and Qwen passing 6/6. The ten arms ran as detached processes in three
    waves — attached Qwen and 120b arms; the 20b arms with the text2sql
    ablations; the reasoning-core ablations alone — from a worktree pinned
    at the commit the arms loaded, with the TOMLs read from main. Why it may
    be right: the split is § 9.6's four contexts on several models, and a
    stronger backward pass is the cheapest test of whether the store's
    weakness is the judge or the request; the waves kept every arm under the
    endpoint's concurrency ceiling with no 429 past the retries; the pin
    kept two merges to main out of the running code. Why it may not: (a) the
    contracts are priced for one model and the pricing floor warns on every
    other — the teacher's drafts parsed but were no better (item 49), so the
    result speaks to the request, not to the model choice, and a priced
    contract for DeepSeek-V4-Pro would be the fair test; (b) the pin covered
    the code and not the experiment file, which another session extended
    mid-run (item 52a); (c) `text2sql` and `text2sql-holdout` were pooled
    into one stream, so the holdout is more first sights rather than a
    separate transfer leg — in a prequential stream every batch is unseen,
    but the family's disjoint-template design is unused; (d) the strict
    text2sql pool consolidates every pass because five batches do not
    divide into rounds of two, so its cadence differs from its lax sibling's
    and the two are not paired on consolidation points.
97. **The dedup/corroboration gap and its convention-label cause are closed
    mechanically, both keyed on one world-content key** (item-61 experiment
    correctness, 2026-09-15). Item 60 confirmed the item-56 pathology on the
    endpoint: the consolidator, holding D-0001 in context, minted the twin
    D-0002 from the same budget happenstance because the coder had named the
    one world-fact two ways across rounds (`other(call-budget-exceeded)` then
    `pool-exhausted`), forking the axis into two clusters. One canonical key —
    `hgi.index.world_content_key`, the quoted literals lowercased, sorted and
    `|`-joined, else the normalized sentence, already the token
    `world_content_variance` groups on — now feeds four call sites so a
    world-fact is grouped, named and de-duplicated the same way everywhere:
    (a) `world_content_variance` reads it; (b) `_happenstance_series` names a
    price-zero fact by it, so one world-fact transcribed across rounds lands
    one series rather than a fresh name cut from a noisy `happened` fragment
    (the item-61 chore); (c) `group_observations` canonicalizes a recurring
    *escape* label to the one the same world-fact first carried
    (`_canonical_label`, escape→escape only, first-seen wins); (d) the
    consolidate loop routes a fresh `new-decision` draft whose evidence rests
    *entirely* on world-facts an accepted decision already anchors to
    corroboration of that decision — a `still-holds` currency entry, the
    evidence consumed pointing at the standing record, the twin dropped —
    rather than minting (`corroborates`/`corroborate`, a new `corroborated`
    leg on the pass record). *Right if:* the world-content literal is the
    stable identity of a happenstance the coder's prose only labels, so keying
    the axis on it (not on the label) is the honest grouping, and the subset
    test — the draft brings *no* new world-fact — makes the dedup guard
    conservative, a false mint (a standing tax, I5) being the lesser cost than
    a suppressed genuine decision. It also credits the *drifting-label* half of
    the item-61 recurrence question: a method restated under a drifting escape
    now keeps one label and accumulates independence. *Wrong if:* two genuinely
    distinct escapes quote the same literal and are wrongly merged (mitigated —
    escape→escape only, registered terms untouched, and the no-literal fallback
    keys on the whole sentence, which rarely collides); or the coder's label,
    however it drifts, still carried information the canonical key discards. It
    does *not* touch the F1/F3 residue — a method manifesting as per-task
    *singletons over distinct world-facts* still never recurs, because those
    are different keys; whether cross-session keying should abstract across
    distinct world-facts is the still-open design question, left unforced.
98. **The intake reads the world-fact through a way-of-working symptom, keeps a
    budget refusal off the observation axis, and repairs a non-JSON final reply**
    (item 63, the qwen-attached run's binding defect, 2026-09-15). The item-61/62
    guards proved structurally sound on the endpoint, but every guard is downstream
    of the *coding* step, and the run showed intake was the ceiling on relevance:
    the actor over-verified until the budget refused a call and emitted a non-JSON
    reply, and the close then filed the *budget refusal* — or the harness's
    "final reply was not JSON" — as the world-fact, so the only thing that recurred
    cross-session was budget, never the produce-and-verify method. Three intake
    changes: (a) `hgi/roles/pass.md` and `coder.md` now tell the eliciting and
    coding steps to read *through* a way-of-working symptom (a call-budget refusal,
    a malformed reply, an error wrapper) to what the task was producing and whether
    it satisfied the world — the budget/format symptom is `turned_on` at most, never
    the `happened` a finding groups on (GCE §11.1, "a way of working turns on
    itself, not on the world"); (b) `close._recovered_nontransient` no longer treats
    a call-budget refusal as a fault a passing row "recovered from"
    (`_is_budget_refusal`, keyed on the `"call budget of … exceeded"` cause), so
    L-0009 stops minting an observation from a passing row whose only fault was
    spending its budget — it is economy telemetry (`tool_budget_respected`), not a
    convention; (c) `suite/agent.py` gives the model one bounded repair turn on a
    non-JSON final reply (the sibling of decision/item-42's malformed-tool-call
    recovery, for the answer) demanding the task's outcome, and splits the symptom
    (a format failure that survived the repair reads apart by `cause`). *Right if:*
    the ceiling on relevance was set entirely by what the coder read off the row, so
    fixing intake is the highest-leverage change and it is offline-testable; a budget
    refusal on a passing row is genuinely not a world-convention, and the repair turn
    lets the true method outcome surface instead of the harness error masking it.
    *Wrong if:* the hard tier stays near-saturation for the actor (only 2 of 20 rows
    failed), so even a perfect intake has thin method signal to group — the harder
    floor and a repair on the *final* answer may still leave too few genuine method
    failures to recur; and the prompt changes are authored, not yet re-verified on
    the endpoint (`priced_for` unchanged; a live re-run is owed). The budget-refusal
    gate keys on the cause string `suite.tools` raises, so a reworded refusal would
    slip past it (mitigated — the two are edited together).
99. **Multi-shape observation coding: a set of convention labels per observation,
    per-label grouping, and demotion on presentation-universality** (item 64, the
    F1/F3 root, 2026-09-15). One label per observation was the wrong model: a method
    that manifests as per-task singletons under drifting fine labels
    (`other(module-not-found)`, `other(grammar-parse)`, `other(invalid-json)`) never
    cleared the recurrence bar, and decision 97's per-world-fact canonicalization
    could not help — those are genuinely distinct world-facts, not one fact drifting.
    So the coder (`cluster`) now returns a *set* of labels per observation — a broad
    convention shared across tasks and a specific one — `group_observations` groups
    **per label** (a candidate cluster is every observation carrying label L, one
    observation lives in several clusters), never a transitive union-find, and
    `_demote_pool_universal` (raw frequency) is replaced by
    `_demote_presentation_universal`: a grouping label is demoted only when its
    cluster's *shared presentation* is pool-universal (item 58's
    `presentation_universality`), never on how frequent the label is. No schema
    migration — `Observation.shape` was already a list; the readers that assumed
    `shape[0]` (`_prior_escape_labels`) now iterate the set, and `_canonical_label`
    became the per-observation `_canonical_escape`, secondary now that the coarse
    label does the cross-round merging. *Right if:* the redundancy is the fix — a
    coarse shared label survives the fine-wording drift a single narrow label
    scatters into singletons, and presentation-universality is the correct refusal:
    budget is universal *on presentation* (its cluster spans every task-shape, so its
    shared presentation collapses to the universal term alone → demoted), while a
    coarse method label is frequent but keyed on a non-universal task-shape → kept.
    Raw frequency would demote the very method label the redundancy exists to keep.
    It maps universality to the presentation axis where §11.1 says it belongs and
    retires the hand-crafted canonicalization. *Wrong if:* per-label grouping
    multiplies candidate nominations, so the dedup guard (decision 97) must hold the
    overlap — one observation feeding two near-duplicate nominations must route to
    corroboration, not two decisions; the coder now judges multiple labels per
    observation, trading one call's precision for coverage (guarded by the
    blind-coder agreement control, decision 59); and the soft coarse+specific
    discipline lives in the prompt, so a model that returns one narrow label
    degenerates to the old behavior. All of it is offline/stub-tested; the live
    confirmation that a genuine method now recurs on the endpoint is owed.
100. **Raise the reasoning-core hard floor via the grammar derivation window, not
    a generator level** (item 66, 2026-09-15). `HARD.cfg_tokens` `(8, 14)` →
    `(10, 16)` (`suite/families/_reasoning_core.py`); both generator levels stay
    (regex 5, grammar 3). The pinned `reasoning-core-hard.jsonl` was re-fetched at
    the new window (12 cfg instances regenerated, the 12 regex unchanged since the
    regex level and seed base did not move), the durable text and the
    instance-coupled tests followed (the new `cfg_00` is a bracket-nesting grammar
    with an eleven-token floor). *Why this lever:* the item-66 re-run saturated at
    24/24 on the stream — the actor solved every learning-pass task, so method
    failures came only on the non-consolidating revisit and never reached coding;
    item 65's "thin method signal at near-saturation" is the binding constraint, and
    the run's actual failures were all `cfg` tasks, so the grammar floor is the
    targeted knob. *Why the window, not a level:* item 47 names "a longer valid
    derivation" as the grammar floor lever, and a window change keeps both levels, so
    the seed store's level-specific method facts (D-0002's regex level-5 witness
    rules, D-0003's leftmost-derivation method) stay valid — only token-count numbers
    move; a `regex_level` or `cfg_level` bump would invalidate the seed's authored
    facts. *Why it may be right:* it targets the generator that actually failed,
    keeps the blast radius to a config value + re-fetch, and is reversible. *Why it
    may not:* item 47's cfg cliff — `(8,14)`→0.33, `(10,18)`→0.17 — makes cfg a
    knife-edge, and `(10,16)` sits near it; **item 47's absolute numbers are stale**
    because item-63(3)'s repair turn post-dates them (it lifted `(8,14)` from a
    calibrated ~0.33 to an observed ~1.0), so where `(10,16)` lands is unmeasured. A
    scratch calibration pilot (per the **experiment-runner** skill) is owed before
    the next billed `qwen-attached` run — watch for the ~0.17 floor effect where even
    the store cannot lift the actor. **Measured (2026-09-15):** a scratch
    `qwen-detached` pilot at `(10,16)` scored **23/24 (0.958)** first-sight (curve
    `1.0×5 / 0.75`) — the lax pool is still saturated, the *opposite* end from the
    0.17 cliff, because the actor fails on neither grammar hardness (it produces
    valid members) nor, with item-63(3)'s repair turn, over-verification; the window
    is **not the lever for the lax pool**. The strict pool (budget 1, no repair) is
    the difficulty lever, and decision 100's window raise still *helps* it (harder
    grammars → more wrong first candidates) — it is just insufficient for the lax
    pool alone (carry-forward item 67). *Owed:* the seed store
    (`experiments/seeds/reasoning-core-hard`) is authored for the old `(8,14)` window
    and is now stale relative to the raised floor — its window numbers and
    instance-specific counts (e.g. "nine of twelve grammars") must be re-verified and
    re-authored for `(10,16)` before the `qwen-seeded`/`qwen-strict-seeded` twins run.
    The plain arms (attached, detached, strict, 20b) do not use the seed and run at
    the new floor once calibrated.
101. **Experiment files derive from shared bases via `extends`, and an arm pins the
    resolved definition beside its `arm.json`** (item 68, 2026-09-15). `load()` reads
    an optional top-level `extends` — a base file, or a list, resolved relative to the
    file — and deep-merges the file's tables over the base(s) with the same `_merge`
    that lays an arm over the defaults, so inheritance is one more level of the merge
    already in use, not a second mechanism (`hgi/experiment.py`). Two bases hold what
    the W&B-Inference runs restated file by file: `experiments/_base.toml` the
    `weave_project` and the model registry (the ids `hgi experiment models` lists), and
    `experiments/_teacher.toml` (itself `extends`-ing `_base`) the split-roles teacher
    block. Ten files now `extends` one of them, dropping ~18 model-id declarations, 13
    `weave_project` lines and 3 verbatim teacher blocks. `Experiment.resolved()` returns
    the file's tables with every base merged in and `extends` stripped; `run_arm` writes
    it as `experiment.json` beside `arm.json`, and `load()` reads a `.json` file back as
    that snapshot — the second half of item 52(a) (the first, resolve-only-the-arm-run,
    was built at `9847d1b`). *Why extends, not a templating/codegen layer:* it keeps the
    files plain readable TOML the spec's "declared once, kept out of the run" ethos wants,
    reuses `_merge`, and adds ~12 lines to `load()` with no new schema type. *Why a JSON
    snapshot, not a TOML one:* the venv has no TOML writer (stdlib `tomllib` is read-only),
    and JSON is a faithful, re-loadable resolution — so the pin does not depend on adding a
    dependency. *Why two bases, not one:* the teacher roles are shared by exactly the three
    split-roles files; folding them into `_base` would silently put DeepSeek on every other
    file's non-pass roles and change their runs. *Why some files keep their own registry:*
    `incidents.toml` uses different aliases and a different DeepSeek id (`-0813`), and the
    `hgi-dev` probes a different `weave_project`; they are left un-migrated rather than made
    to override the base back. *Why it may be right:* every one of the 72 arms across the 16
    files resolves byte-identically before and after (a captured-baseline diff, and the two
    new tests in `tests/test_experiment.py`), so the change is pure de-duplication; the base
    files are `_`-prefixed and skipped by the experiment globs. *Why it may not:* an unused
    alias inherited from `_base` now sits in a file's registry (inert, since an arm resolves
    only the models it names — confirmed by the identical diff), and a base edit now reaches
    every deriving file at once, which is the point but also a wider blast radius than a
    per-file id; the `experiment.json` pin is what guards a *past* run against that.
102. **The loop tolerates bad or missing data from its APIs (Weave, the model
    endpoint) without aborting an arm unrecoverably** (commit `936162b`,
    `tests/test_api_resilience.py`). A real Weave flush/pairing-timeout (item 34's
    class) returned a `None` evaluation summary and `evaluate.facts_from` crashed on
    `summary.get`, killing the text2sql `120b-attached` arm at pass 3 and losing every
    later pass. Three additive layers answer it: (a) `evaluate.summary_from_rows`
    rebuilds the scorers' summary from the per-row scores that survive the flush, and
    `facts_from` guards on `isinstance(summary, dict)` — a `None` or malformed summary
    reads as unevaluable, never an AttributeError; (b) `model.Completion.json_or(default)`
    degrades a garbled or wrong-typed reply to the default at the "empty is legal" sites
    (`boot.classify`, the lens walk, `close`'s `dispose`) — a single bad endpoint reply
    no longer crashes the pass; (c) `experiment.run_arm` retries the flaky `evaluate`
    step (`hgi_retry`) and, on a pass that still fails, finalizes the arm gracefully —
    completed passes committed, the cause recorded in `arm.json`'s `error`, nothing
    escaping `run_arm`; it catches `SystemExit` (hgi()'s own nonzero-step signal, which
    is not an `Exception`) as well as `Exception`, leaving `KeyboardInterrupt` to abort.
    *Why it may be right:* the failure class is exactly the reruns the carry-forward is
    full of (items 34, 36); the per-row scores are already computed when the summary is
    lost, so the recovery re-bills nothing; the change is strictly additive (759 tests
    green, the happy path byte-for-byte unchanged), and the hardened rerun of the same
    arm completed all six passes with no retries or stops. *Why it may not:* `json_or`
    could mask a reply that should have been refused — mitigated because the drafting
    sites still call `json()` and refuse with the field named, and only the
    contract-empty-legal sites use `json_or`; the graceful stop turns a persistent bug
    into a recorded `error` rather than a loud crash — mitigated because a `Traceback`
    is now, by construction, a real bug and the `error` surfaces in `arm.json` and the
    monitor; and `summary_from_rows` assumes `row_scores` is populated when the summary
    is `None` (true when the flush follows a completed `summarize`; if `summarize` never
    ran, `row_scores` is empty → unevaluable, still no crash).
103. **A consultation hook may key on a convention, not only a work-shape** (commit
    `e4f909b`, `tests/test_convention_hook.py`; carry-forward item 71a). The hook
    vocabulary is now the union of the two axes (`types.HOOK_AXES`): `Term(*vocabs)`
    accepts a term from either, `Guard.terms`/`WorkShape.terms`/`Sketch.terms` span
    both, boot `classify` offers both and names the conventions a presentation reveals,
    `anchor_terms` floors the hook with the convention the evidence was coded into, and
    `applies_when` offers both axes and never flags a convention pool-universal. The
    route taken was the *structural* one item 71a named — unblock the existing
    convention axis as a hook key — not the alternative of adding SQL/query work-shape
    terms, which would have over-keyed the vocabulary on the instance that surfaced it.
    *Why it may be right:* the load-bearing failure item 71 root-caused was that a
    SQL lesson could latch only `shell-tool` (pool-universal in a SQL pool) — a
    non-discriminating hook; a convention key (`schema-coded-value`) is never
    pool-universal, so the record gets a hook that selects, and the change is a strict
    superset (every prior work-shape hook still parses and fires; 774 green). *Why it
    may not:* a convention is often visible only once the work fails, so a
    convention-keyed hook does not fire at boot where the presentation hides it — no
    worse than a work-shape the prompt does not reveal, but not the universal retrieval
    a naive reading might expect; and offering the convention vocabulary to `classify`
    invites the model to name conventions from prompts speculatively — bounded by the
    same "plainly instantiates" discipline the work-shape classification already runs
    under, and by the guard re-checking at fire time.
104. **The blind coder prefers a registered convention over escaping** (commit
    `55e61f1`, `tests/test_coder_convention_discipline.py`; carry-forward item 71b).
    A prompt-discipline change in `coder.md`: scan the registered `convention`
    vocabulary before writing any `other(...)`, use a registered term when its
    world-fact is the one the attempt turned on, and reserve the escape for a genuine
    gap — binding hardest on the broad label, the one grouping leans on. No mechanical
    auto-snap (that would corrupt the blind-coding contract). *Why it may be right:*
    the text2sql run escaped 100% while `schema-coded-value` exactly fit, so the
    consolidator was handed escapes not conventions (item 71 pt 5); the fix keeps the
    two guardrails (never force a term that does not fit, never escape one already
    covered) so it cannot corrupt grouping. *Why it may not:* it is prose discipline,
    not a floor — a model that still escapes is not mechanically corrected; the
    escape→mint ladder remains the recovery, and a live re-score is what confirms the
    discipline holds on the endpoint.
105. **Grouping never demotes a registered convention** (commit `e4f909b`,
    `tests/test_convention_hook.py`; carry-forward item 71c). `_demote_presentation_universal`
    now exempts a registered `convention` label: it names a world-fact axis, not a
    presentation, so it is the grain at which a logical fault stays coherent, and only
    escapes and unregistered labels remain eligible for the presentation-universality
    demotion. *Why it may be right:* the demotion exists to sink a label whose only
    grouping identity is a term every task carries (a way-of-working an escape landed
    on); a coherent world-convention is exactly what the demotion must not strand into
    `other(uncoded)` singletons — the loss item 71 pt 4 names. *Why it may not:* a
    registered convention that genuinely coincides with a pool-universal presentation
    across its members is now never demoted on that ground — accepted as the safer
    error, since a registered convention is a curated world-fact term, not a coarse
    escape, and the ripeness score still sinks a universal-presentation cluster at
    ranking time.
106. **An observation's literal and inference halves stay in one record** (commit
    `989ce52`, `tests/test_observation_pairing.py`; carry-forward item 71d). The
    observation lenses (L-0004/L-0009) and the shared lens reply shape now elicit, per
    failed world-fact, a single finding carrying both the concrete literal (`happened`)
    and the convention it turned on (`turned_on`); `close._merge_split_findings` is a
    defensive backstop that folds a clean literal-only/inference-only pair on the same
    `call` anchor into one, keying only on the shared anchor, never a domain literal.
    *Why it may be right:* ~45% of the text2sql observations carried `turned_on: null`
    on exactly the token-bearing rows, splitting the drafting floor's required token
    from the grouping's required convention (item 71 pt 6); the directive fixes it at
    source and the merge is a conservative belt (a clean pair only, never dropping a
    standalone finding). *Why it may not:* the merge is a heuristic — an ambiguous
    crowd on one anchor is left untouched (both halves then file separately, as before),
    so the directive, not the backstop, carries the load, and only a live run confirms
    the model files the one finding.
