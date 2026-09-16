"""The seed: the smallest configuration that runs one full cycle.

The loop's first organs cannot have been admitted by the loop and need not
be. Genesis writes the registry (Appendix C of the specification), the
constitution under its cap (Appendix A.1), the genesis work-shape terms
(A.2), the boot and close lens fans (A.3), and the id counters. Everything
else is minted by the loop from its own miss stream, through the ladder, at
the bars. Genesis articles and terms carry ``warrant.evidence: genesis`` and
earn an anchor by the third consolidation pass or are evicted.

``store/registry/*.json`` and ``store/constitution/*.json`` in the repository
are this module's output at genesis; afterwards they are registers the loop
corrects in place, and git carries the divergence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from hgi import registry as _registry
from hgi.registry import write_json

GENESIS_DATE = "2026-09-12"


def _terms(*pairs: tuple[str, str]) -> dict[str, dict[str, str]]:
    return {term: {"means": means, "since": GENESIS_DATE} for term, means in pairs}


VOCABULARY: dict[str, dict] = {
    "work-shape": {
        "means": "the closed vocabulary of task presentations a consultation hook keys on; minted from the task suite's "
                 "known presentations, which exist ahead of the instances. These are the tool-major cues a boot classify "
                 "keys a hook on (a task that calls the HTTP tool), coarse by design. It is one of the two hook axes: a "
                 "consultation hook keys on a work-shape or on a `convention` (the world-fact the work exhibits), and boot "
                 "classification presents both; observation grouping still keys on the `convention` axis alone",
        "terms": _terms(
            ("tool-call-retry", "the task involves retrying a tool call that failed transiently"),
            ("http-tool", "the task calls the HTTP tool"),
            ("shell-tool", "the task calls the shell tool"),
            ("file-tool", "the task reads or writes through the file tool"),
            ("output-schema", "the task's output must conform to a declared schema"),
            ("test-failure-triage", "the task diagnoses a failing test"),
            ("tool-budget", "the task runs under a call budget"),
            ("error-wrapping", "the task wraps, rethrows or reports an error"),
            ("task-planning", "the task requires a plan before action"),
        ),
    },
    "convention": {
        "means": "the open, instance-grown vocabulary the blind coder groups observations by: the world-fact an attempt "
                 "turned on, the granularity a lesson recurs at (a route the world has retired to a versioned successor). "
                 "It grows by the escape→mint ladder rather than being minted whole at genesis like the tool-major axis; the "
                 "seed terms below are the conventions the suite already knows. Two misses of one convention share a shape "
                 "and two of different conventions differ even when both called the same tool — which the tool cue alone "
                 "conflated (shape-radius sweep, decision 77; carry-forward item 57). It is both the grouping axis and, "
                 "alongside work-shape, a hook axis: a decision whose lesson is about a convention keys its consultation "
                 "hook on that convention, so it is recalled when the convention recurs, not only on a shared tool "
                 "(carry-forward item 71a)",
        "terms": _terms(
            ("route-versioned", "a route the world has retired, answering with the versioned successor it moved to"),
            ("listing-paged", "a listing the world returns one page at a time, each page naming the next or its end"),
            ("route-guarded", "a route the world answers only when a held token authorizes the call"),
            ("field-quoted", "a delimited field the world quotes so it may carry the delimiter inside it"),
            ("summary-row", "a tabular export the world ends with a total or summary row that is not a data record"),
            ("line-unterminated", "a text file whose last line the world leaves with no terminating newline"),
            ("byte-order-mark", "a text file the world opens with a byte-order mark a strict parser refuses"),
            ("schema-coded-value", "a fixed database whose schema stores a value in an encoded form a plain query gets "
                                   "wrong — a status or category kept as a coded literal to match on its stored form not a "
                                   "natural word, a date kept as text and reached with STRFTIME not a date function, a ratio "
                                   "the dialect integer-divides unless it is cast — the schema convention a query over it must know"),
            ("pool-exhausted", "a datastore pool the world saturates under its own load — backends busy, queries slow, "
                               "waiters queued — the local capacity fault the pool readings show and the dependency "
                               "readings do not"),
            ("dependency-stalled", "a dependency the world slows or fails, holding the caller's connections so a healthy "
                                   "pool fills as a consequence — queries fast, backends idle in transaction, the "
                                   "provider's status or latency carries the onset"),
            ("release-regressed", "an error or latency spike the world starts at a deploy with the data unchanged — the "
                                  "release history carries the onset, the payload samples do not"),
        ),
    },
    "latch-type": {"means": "the typed activation units of § 6.2", "terms": _terms(
        ("consultation", "keyed on the terms the pass presents — a work-shape or a convention; polled at boot; the working pass applies the payload"),
        ("revisit", "keyed on world-state; the oracle moving; the backward pass re-adjudicates the warrant"),
        ("wiring", "keyed on a neighbour record changing status; propagation re-derives or checks"),
        ("floor", "keyed on the diff or the proposal at commit; the committer's lint checks"),
        ("retirement", "keyed on competence signals at consolidation; the lifecycle review retires or demotes"),
    )},
    "key-space": {"means": "what a latch's guard is matched against", "terms": _terms(
        ("work-shape", "registered terms the pass presents, across the work-shape and convention hook axes"), ("world-state", "a Weave evaluation, scorer and comparator"),
        ("neighbor", "record ids"), ("diff", "the proposal or diff under commit"), ("competence", "derived telemetry ratios"),
    )},
    "edge-kind": {"means": "how a latch becomes considered", "terms": _terms(
        ("level", "polled while the condition holds"), ("edge", "fires on a transition"), ("schedule", "fires at a scheduled point"),
    )},
    "act-class": {"means": "the closed set an owed act opens with", "terms": _terms(
        ("apply", "apply the payload to the work in hand"), ("re-adjudicate", "re-open the warrant for a verdict"),
        ("re-derive", "recompute a derived field"), ("check", "run a check"), ("retire", "retire or demote the record"),
    )},
    "owed-act-role": {"means": "whether a fire can settle the record", "terms": _terms(
        ("dispositive", "a disposed fire can settle the record"), ("corroborating", "a fire bears, never settles"),
    )},
    "latch-lifecycle": {"means": "the state of a latch", "terms": _terms(("live", ""), ("settled", ""), ("moot", ""))},
    "slot": {"means": "the five slots of the entry contract", "terms": _terms(
        ("activation", ""), ("payload", ""), ("warrant", ""), ("enforcement", ""), ("lifecycle", ""),
    )},
    "constitution-status": {"means": "", "terms": _terms(("live", "loaded every pass"), ("evicted", "displaced under the cap; superseded, never deleted"))},
    "decision-status": {"means": "", "terms": _terms(("proposed", ""), ("accepted", ""), ("superseded", ""), ("moot", ""))},
    "premise-status": {"means": "the one in-place flip a warrant takes; only a disposed fire may flip it", "terms": _terms(
        ("unevaluated", ""), ("supported", ""), ("disputed", ""), ("reversed", ""),
    )},
    "observation-state": {"means": "", "terms": _terms(("open", ""), ("promoted", "delete-with-pointer"), ("dismissed", ""), ("expired", ""))},
    "use-time-disposition": {"means": "the verdict a consulted record receives from the pass that consulted it", "terms": _terms(
        ("applied", "the payload bore on the work and was applied"),
        ("considered-not-applicable", "the hook fired on presentation alone; routing working as designed"),
        ("fired-off-map", "applied outside the declared hook, or the work matched no hook at all"),
        ("guard-failed", "considered but the guard did not pass"),
    )},
    "steer-source": {"means": "", "terms": _terms(("human", "a note on a call"), ("oracle", "an evaluation regression attributed by the adjudicator"))},
    "matrix-cell": {"means": "the detection matrix of § 10.1: did the store catch it, did the world or a human", "terms": _terms(
        ("system-catches/oracle-catches", "redundant catch; demotion-side evidence"),
        ("system-catches/human-catches", "redundant catch; demotion-side evidence"),
        ("system-catches/none-catches", "the amortization working"),
        ("system-misses/oracle-catches", "the steer: credit assignment plus a free miss report"),
        ("system-misses/human-catches", "the steer: credit assignment plus a free miss report"),
        ("system-misses/none-catches", "the true miss, repaired backwards from the manifested defect"),
    )},
    "species": {"means": "the kinds of hypothesis-ledger entry", "terms": _terms(
        ("attack", "the examiner's refute-phrased attack on a draft"), ("collision", "a derivation disagreeing with an implementation"),
        ("forecast", "a settled prediction"), ("reality", "a design premise contradicted by the world"),
        ("currency", "a premise re-checked for currency"), ("coding", "a blind second coding of observations"),
    )},
    "attack-verdict": {"means": "", "terms": _terms(("pending", ""), ("survived-with-attack-named", ""), ("attack-landed", ""), ("premise-killed", ""))},
    "collision-verdict": {"means": "", "terms": _terms(("pending", ""), ("derivation-wrong", ""), ("implementation-wrong", ""), ("contract-open", ""))},
    "forecast-verdict": {"means": "", "terms": _terms(("pending", ""), ("true", ""), ("false", ""), ("unevaluable", ""), ("void", ""))},
    "reality-verdict": {"means": "", "terms": _terms(("pending", ""), ("reducible", "a duty was missed; route it"), ("irreducible", "no authoring duty could have prevented it"))},
    "currency-verdict": {"means": "", "terms": _terms(("pending", ""), ("still-holds", ""), ("reversed", ""), ("moot", ""))},
    "coding-verdict": {"means": "", "terms": _terms(("pending", ""), ("agree", "ratifies the class"), ("disagree", "keeps the boundary open"))},
    "adjudicator-verdict": {"means": "the one token the adjudicator returns", "terms": _terms(
        ("admit", ""), ("admit-amended(<amendment>)", "amends only the slot the attack indicted"),
        ("decline(<why>)", "drops the draft"), ("defer(<until>)", "re-queues with the condition as a latch"),
        ("escalate(<why>)", "routes to the human queue"),
    )},
    "ladder-rung": {"means": "the cheapest sufficient home for a ratified recurrence, in order", "terms": _terms(
        ("counterfactual-edit", "1. an edit to an existing record's counterfactual or not_this"),
        ("adoption-row", "2. a row in an existing rule's adoption register"),
        ("rule-enrollment", "3. a new rule enrolled under an existing decision"),
        ("hook-edit", "4. a hook edit on an existing latch"),
        ("new-decision", "5. a new decision, only on a genuinely undecided fork"),
        ("floor", "6. a mechanical floor, only where the check is fully mechanical"),
        ("article", "7. a constitution article, only with a forced eviction"),
    )},
    "lens-purpose": {"means": "", "terms": _terms(("adjudicative", "terminates in an authority, never in the answerer"), ("generative", "touches the item; is never handed an answer"))},
    "lens-contact": {"means": "the strongest contact outside the answerer the lens forces", "terms": _terms(("record", ""), ("artifact", ""), ("oracle", ""), ("none", ""))},
    "lens-host": {"means": "the step that walks the lens", "terms": _terms(("boot", ""), ("close", ""), ("examiner", ""))},
    "lens-status": {"means": "a lens's lifecycle: walked, or retired through a crystallization door (§ 7.4 of the doctrine)", "terms": _terms(
        ("live", "walked by its host"), ("retired", "no longer walked: its answer crystallized, or its genesis earned no anchor by the deadline"),
    )},
    "role": {"means": "the four contexts of the separation of powers, plus the pass and the coder", "terms": _terms(
        ("pass", "the working pass — the agent under test and its boot and close steps"),
        ("consolidator", "nominates"), ("examiner", "contradicts"), ("adjudicator", "verdicts"),
        ("committer", "admits mechanically"), ("coder", "the blind second coder"), ("human", "the escalation queue"),
        ("oracle", "the world channel — a fire, a ratio, an evaluation run; it contradicts and grounds, it never authors or verdicts"),
    )},
}

PORTS = {
    "decision": {
        "proposed": {"consultation": "required", "revisit": "optional", "wiring": "optional", "floor": "forbidden", "retirement": "forbidden"},
        "accepted": {"consultation": "required", "revisit": "optional", "wiring": "optional", "floor": "forbidden", "retirement": "required"},
        "superseded": {"consultation": "forbidden", "revisit": "forbidden", "wiring": "required", "floor": "forbidden", "retirement": "forbidden"},
        "moot": {"consultation": "forbidden", "revisit": "forbidden", "wiring": "optional", "floor": "forbidden", "retirement": "forbidden"},
    },
}

BARS = {
    "as_of": GENESIS_DATE,
    "observation": {"noticings": 1, "anchors": 1},
    "decision": {
        "independent_observations": 2,
        "or_steer_attributed_regressions": 1,
        "independence": "observations from distinct sessions",
    },
    "retirement": {"applied_over_considered_below": 0.1, "window_passes": 6},
    "precision": {"not_applicable_over_considered_above": 0.5},
    "vocabulary": {"independent_escapes": 2, "independence": "escapes from distinct sessions; two from one pass are one datum"},
    "consolidation_every_passes": 2,
    "genesis_anchor_deadline_consolidations": 3,
    "proposal_ttl_consolidations": 2,
}

CONSTITUTION_CAP = {"max_articles": 7, "max_bytes": 4096}

ARTICLES: list[tuple[str, str]] = [
    ("The pass proposes; the backward pass admits. No pass writes to an eternal store.",
     "The overshoot: a pass that files nothing because it cannot admit — proposals are the pass's product, not a courtesy."),
    ("Consultation is reported as a count with ids and dispositions; a bare assurance is a defect.",
     "The overshoot: opening every record to inflate the count — the count nominates precision review, never quality."),
    ("Every claim is a hypothesis with an anchor; suspected and verified never share a register.",
     "The overshoot: refusing to file a suspicion until it is verified — the observation ledger exists for the unverified."),
    ("The oracle grounds, the adjudicator decides, the committer writes; no context holds two roles.",
     "The overshoot: an adjudicator that defers every verdict to escalation — escalate is for ambiguity, not for reluctance."),
    ("Promotion raises abstraction; a copied instance is refused.",
     "The overshoot: an abstraction the anchors no longer instantiate — a floating entry."),
    ("Every floor discloses its residue; absent data reads unevaluable, never zero.",
     "The overshoot: a residue list so long the floor is not worth running — a floor with no bindable part is not a floor."),
    ("Every threshold has a retirement leg; nothing is deleted, everything is superseded.",
     "The overshoot: retiring the rarely-binding record for low salience — the killer-item is exempt regardless of count."),
]

LENSES = [
    {"id": "L-0001", "host": "boot", "purpose": "adjudicative",
     "angle": "Which consulted record's hook fired on presentation alone and does not bear on this task? Name it and dispose it considered-not-applicable.",
     "counterfactual": "The overshoot: disposing every record not-applicable to shorten the read — a record applied nowhere in the pass is a demotion datum, and the trace will show it.",
     "externality": {"contact": "record", "terminates_in": "the index and the consulted records, cited by id"},
     "product": "a list of {record, disposition, why}; empty is a legal answer", "consumer": "the working pass"},
    {"id": "L-0002", "host": "boot", "purpose": "generative",
     "angle": "The store holds a record this task needs and no hook reached it — which?",
     "counterfactual": "The overshoot: inventing a need to have a finding; an answer with no record id is not filed.",
     "externality": {"contact": "record", "terminates_in": "the decision store's summary lines"},
     "product": "a list of {record, why}; empty is a legal answer", "consumer": "the backward pass: the brief's recall rows nominate a hook-edit; the structural-zero audit"},
    {"id": "L-0003", "host": "close", "purpose": "adjudicative",
     "angle": "What did this pass make false in the store — which premise, which hook?",
     "counterfactual": "The overshoot: manufacturing a falsification; empty is a legal answer.",
     "externality": {"contact": "record", "terminates_in": "the store's premises and hooks, cited by id"},
     "product": "a list of {record, slot, what-changed, anchor}; empty is a legal answer", "consumer": "the backward pass"},
    {"id": "L-0004", "host": "close", "purpose": "generative",
     "angle": "The first attempt in this pass failed on this row. Read the artifact — the query it produced, the rows it returned, the tool error — and name where it was wrong against the schema and the question: the clause, column, value or dialect token it got wrong.",
     "counterfactual": "Two overshoots: grading the pass's own lesson as settled — the answer is an observation at the floor, never a rule; and answering with the store instead of the world — 'no rule matched', 'which record should have fired', 'no coverage' name the loop's routing, not this row's world-fact, and are the off-map lens's subject (L-0010), not this one's.",
     "externality": {"contact": "artifact", "terminates_in": "the trace: a call URI per finding"},
     "product": "for the failed task in the subject, at most one {happened, turned_on, anchor, recheck_when}: `happened` names the task and the settled world-fact its first attempt met — the query text, the returned rows, the tool error — in one or two sentences; `turned_on` names the schema or dialect convention it missed as a checkable world-fact — a column, a coded value, a dialect token (STRFTIME on a TEXT date, CAST for a ratio) — never a store record or 'no rule / no coverage', which is L-0010's subject; null when you cannot name a world convention; `anchor` is {call: the row's call URI, path: null}; `recheck_when` says when to look for the same miss again; empty when the failure was not the pass's to avoid",
     "consumer": "the observation ledger; the backward pass"},
    {"id": "L-0009", "host": "close", "purpose": "generative",
     "angle": "A row passed, but its first attempt was wrong — a non-transient fault the pass corrected on the way to the score. Name the convention that first attempt missed.",
     "counterfactual": "The overshoot: filing the transient fault that cleared on retry — a recovered 502 is loud but non-causal; file only a non-transient miss the pass corrected.",
     "externality": {"contact": "artifact", "terminates_in": "the trace: a call URI per finding"},
     "product": "a list of {happened, turned_on, anchor}; each becomes an observation: `happened` the settled world-fact, `turned_on` the convention it turned on (optional)", "consumer": "the observation ledger; the backward pass"},
    {"id": "L-0010", "host": "close", "purpose": "generative",
     "angle": "This pass failed and matched no hook — the store held no rule for this work. Name the one shape of work the store has no coverage for, at the altitude of the class, not the row.",
     "counterfactual": "Two overshoots: crying 'a rule is missing' on a pass that did consult a record — that is not off-map, fire only when nothing was consulted and the work failed, empty is legal; and filing one finding per failed row — the coverage gap is one class of work, so name it once for the pass, not once per instance.",
     "externality": {"contact": "record", "terminates_in": "the pass's off-map disposition and its failed rows' calls in the trace"},
     "product": "at most one {happened, turned_on, anchor}: `happened` names the class of work the store held no rule for — the work-shape, named once for the pass, not one finding per failed row; `turned_on` the coverage the store lacks (optional); `anchor` a representative failed row's call URI. It becomes one coverage observation feeding the should-have-been-covered miss stream.", "consumer": "the observation ledger; the backward pass"},
    # the examiner fan: the attack's angles, one context each (the fan law), hosted where independence is structural (the host law).
    # L-0005 and L-0008 are seeded retired through the crystallization door: their questions became gates the code reads
    # (hgi.lint.independence, hgi.consolidate.drop_success_watch), and the register keeps them as the evidence of that.
    {"id": "L-0005", "host": "examiner", "purpose": "adjudicative", "claims": ["warrant:independence"], "status": "retired",
     "warrant": {"evidence": "crystallized: the distinct-session count against the bar is the floor's (hgi.lint independence)", "anchors": []},
     "angle": "Do the draft's anchored observations come from independent passes, or is one context counted twice? Read the sessions the evidence names and land `warrant:independence` when they are fewer than the bar.",
     "counterfactual": "The overshoot: landing independence on every draft whose observations share a task — independence is by session, never by task; two passes meeting the same fault are the recurrence the bar asks for.",
     "externality": {"contact": "record", "terminates_in": "the observations' session ids, as the evidence lists them"},
     "product": "claims on `warrant:independence`, each naming the sessions read", "consumer": "the adjudicator"},
    {"id": "L-0006", "host": "examiner", "purpose": "adjudicative", "claims": ["premise:"],
     "angle": "For each premise of the warrant: what reading of the oracle's evidence would show it false — and taken, did it? The premise kill is the highest-value attack; land `premise:<id>` only on a reading you took.",
     "counterfactual": "The overshoot: killing a premise from what the evidence does not show — a series with no evaluable value is `unevaluable`, never a refutation; a kill needs a reading that came back false.",
     "externality": {"contact": "oracle", "terminates_in": "the fault rate, the series and the scores in the evidence"},
     "product": "one claim per premise, `premise:<id>`, its refutation the premise's own falsifier read against the evidence", "consumer": "the adjudicator"},
    {"id": "L-0007", "host": "examiner", "purpose": "adjudicative", "claims": ["payload:"],
     "angle": "Does the payload name the transferable shape, or an instance — a task id, a file name, a path, a single tool's failure? Land `payload:abstraction` on a copied instance; promotion raises abstraction.",
     "counterfactual": "The overshoot: reading every concrete noun as an instance — a payload about the HTTP tool may name HTTP; what it may not name is the one task or file it was seen in.",
     "externality": {"contact": "record", "terminates_in": "the payload text against the task ids in the evidence"},
     "product": "a claim on `payload:abstraction`", "consumer": "the adjudicator"},
    {"id": "L-0008", "host": "examiner", "purpose": "adjudicative", "claims": ["warrant:watch-direction"], "status": "retired",
     "warrant": {"evidence": "crystallized: a watch that fires on success is dropped from the draft by the code (hgi.consolidate drop_success_watch)", "anchors": []},
     "angle": "Does the revisit watch fire on the failure the stakes name — a low score on a higher-is-better scorer — or on success? A predicate a passing score satisfies and a failing score does not (`task_pass_rate == 1.0`, `>= 0.9`) fires when the record works and stays silent when it regresses: land `warrant:watch-direction`.",
     "counterfactual": "The overshoot: landing on a watch a failing score also satisfies (`!= 1.0`, `>= 0.0`) — it fires on the regression too, so it still returns the loop to the record.",
     "externality": {"contact": "oracle", "terminates_in": "the watch predicate against the scorers' convention: success rates in [0, 1], 1.0 ideal"},
     "product": "a claim on `warrant:watch-direction`, its evidence the predicate", "consumer": "the adjudicator"},
]


def seed(root: Path | str, model_id: str | None = None, now: datetime | None = None) -> _registry.Registry:
    """Write the seed into ``root`` and return the loaded registry. Idempotent over an empty store."""
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    reg_dir = root / "registry"
    write_json(reg_dir / "vocabulary.json", VOCABULARY)
    write_json(reg_dir / "ports.json", PORTS)
    write_json(reg_dir / "bars.json", BARS)
    write_json(reg_dir / "constitution.json", CONSTITUTION_CAP)
    write_json(reg_dir / "lenses.json", [
        {"status": "live", "warrant": {"evidence": "genesis", "anchors": []}, **lens, "kind": "lens", "priced_for": {"model_id": model_id},
         "telemetry": {"answer_variance": "design-stage", "decoy_rejection": "design-stage", "signal_caught": "design-stage", "miss_stream": "steers/ citing this lens"}}
        for lens in LENSES
    ])
    write_json(reg_dir / "ids.json", {"C": len(ARTICLES)})
    reg = _registry.load(root)

    from hgi.store import Store  # lazy: the store validates against this registry
    from hgi.types import ConstitutionArticle

    store = Store(root, registry=reg)
    for n, (article, counterfactual) in enumerate(ARTICLES, start=1):
        store.write(ConstitutionArticle(
            id=f"C-{n:04d}", status="live", created_at=now,
            admission={"proposed_by": "genesis", "verdict": "admit", "committed_at": now},
            article=article, counterfactual=counterfactual,
            warrant={"evidence": "genesis"}, priced_for={"model_id": model_id},
        ))
    for d in ("decisions", "observations", "ledger", "fires", "dispositions", "steers", "sessions",
              "proposals", "queue", "index", "consolidations"):
        (root / d).mkdir(parents=True, exist_ok=True)
    return reg
