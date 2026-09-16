"""Every record kind of the store, declared once.

JSON admission, the lint and the projections derive from these declarations;
there is no hand-maintained parallel field list. The models parse, they do
not validate after the fact: a malformed record is refused before the first
byte lands.

Closed-vocabulary fields are typed with :func:`Term`, which checks the value
against the registry in scope (``registry`` in the validation context, else
:func:`hgi.registry.current`). Every such field admits ``other(<what>)``.

Identity: ids are reserve-once, immutable, gap-tolerant, and encode no tier,
status or revisable slot. The prefix table is :data:`PREFIXES`.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from hgi import registry as _registry

# --- vocabulary-typed strings --------------------------------------------------

def _registry_for(info: ValidationInfo) -> _registry.Registry:
    ctx = info.context or {}
    return ctx.get("registry") or _registry.current()


def Term(*vocabs: str):  # noqa: N802 — a type constructor
    """A string constrained to one of the closed vocabularies ``vocabs`` or an ``other(<what>)`` escape.

    One vocabulary is the common case (``Term("role")``). More than one names a term drawn from a *union* of axes —
    the value is accepted when any of the vocabularies registers it, so a field can carry a term from either axis without
    the axes being merged. The hook vocabulary is such a union (:data:`HOOK_AXES`): a consultation hook keys on a term the
    pass presents, whether that term is a work-shape (the task's shape, the tool it calls) or a convention (the world-fact
    the work exhibits — a paged listing, a coded value, a versioned route). An escape passes against any axis.
    """

    def _check(value: str, info: ValidationInfo) -> str:
        registry = _registry_for(info)
        if len(vocabs) == 1:  # the common case: the underlying vocabulary's own message propagates unwrapped
            return registry.check(vocabs[0], value)
        errors: list[str] = []
        for vocab in vocabs:
            try:
                return registry.check(vocab, value)
            except ValueError as e:
                errors.append(str(e))
        raise ValueError(f"{value!r} is in none of the vocabularies {list(vocabs)}: " + " / ".join(errors))

    return Annotated[str, AfterValidator(_check)]


HOOK_AXES = ("work-shape", "convention")
"""The axes a consultation hook may key on: a term the pass presents is a ``work-shape`` (the task's shape, the tool it
calls, the fault it meets) or a ``convention`` (the world-fact the work exhibits — a paged listing, a coded value, a
versioned route). Both are presented before the payload has helped, so both are legal hook keys; the truth-maker the coder
groups an *observation* on stays the ``convention`` axis alone (see :class:`Observation`)."""


ID_PATTERN = re.compile(r"^([A-Z])-(\d{4,})$")
PREFIXES: dict[str, str] = {
    "constitution": "C",
    "decision": "D",
    "observation": "O",
    "lens": "L",
    "session": "S",
    "fire": "F",
    "hypothesis": "H",
    "steer": "T",
    "disposition": "U",
    "consolidation": "K",
}
"""Record kind → id prefix. ``O-`` is the observation's momentary *name*; its eternal identity is its ``uid``."""

ANCHOR_PATTERN = re.compile(r"(weave:///\S+|\b[A-Z]-\d{4,}\b|\bcommit:[0-9a-f]{7,}\b|\b[\w./-]+\.py:\d+\b)")
"""What counts as an anchor when cited inline in prose: a Weave URI, a record id, a commit, or a path:line."""


def anchors_in(text: str) -> list[str]:
    return ANCHOR_PATTERN.findall(text or "")


class Strict(BaseModel):
    """Every record model forbids unknown fields: a stray field is a parse failure, not a warning."""

    model_config = ConfigDict(extra="forbid")


# --- the envelope -------------------------------------------------------------

class Lineage(Strict):
    """The corpus graph's edges at this vertex. Successor edges compose into a DAG, not a chain.

    A supersedure is one retiree, one successor. A **fold** (edge contraction)
    is one successor with several predecessors, named in ``folded_from``. A
    **split** (vertex split) is one retiree with several heirs, each naming
    the parent in ``split_from``; the parent's ``superseded_by`` therefore
    lists every heir — a scalar back-pointer cannot represent a fan-out.
    """

    supersedes: list[str] = Field(default_factory=list)
    superseded_by: list[str] = Field(default_factory=list)
    split_from: str | None = None
    folded_from: list[str] = Field(default_factory=list)

    @field_validator("superseded_by", mode="before")
    @classmethod
    def _scalar_pointer(cls, v):
        """A record written before the fan-out named one successor or ``null``; both read as the list they mean."""
        if v is None:
            return []
        return [v] if isinstance(v, str) else v


class RoleCall(Strict):
    """A traced call by one of the four roles, joinable to the trace store."""

    role: Term("role")
    model_id: str | None = None
    call: str | None = None
    """The Weave call URI; for the oracle, the fire, anchor or run that contradicted; ``None`` when the run was untraced."""


class Admission(Strict):
    """Stamped by the committer, never by the proposer.

    The admitting commit is not stored on the record because a commit cannot
    contain its own hash; it is derived from git history by
    :func:`hgi.store.admitting_commit`, which ``hgi lineage`` prints. Every
    commit message names the ids it admitted, flipped or retired — a range
    such as ``C-0001..C-0007`` naming each id it spans — and the oldest
    message naming an id is the commit that admitted it.
    """

    proposed_by: str
    """A session id, a consolidation id, or ``genesis``."""
    ledger_entry: str | None = None
    rung: Term("ladder-rung") | None = None
    """The ladder rung the admitting nomination named."""
    displaced_from: Term("ladder-rung") | None = None
    """The rung the lesson was meant for when this roster had no operator for it — a rule, a floor, an article carried as a
    decision; what a later tier reads to find the records that stand in for it."""
    verdict: Term("adjudicator-verdict")
    adjudicator: RoleCall | None = None
    committed_at: datetime


class Envelope(Strict):
    id: str
    kind: str
    status: str
    created_at: datetime
    lineage: Lineage = Field(default_factory=Lineage)
    admission: Admission

    @model_validator(mode="after")
    def _id_matches_kind(self):
        m = ID_PATTERN.match(self.id)
        if not m or m.group(1) != PREFIXES.get(self.kind):
            raise ValueError(f"id {self.id!r} does not carry the prefix for kind {self.kind!r}")
        return self


# --- the latch ---------------------------------------------------------------

class WatchPredicate(Strict):
    """A world-state key: a Weave evaluation, a scorer, and a comparator over the last ``persistence`` runs."""

    evaluation: str
    scorer: str
    comparator: Literal["<", "<=", ">", ">=", "==", "!="]
    value: float
    persistence: int = 1


class Edge(Strict):
    kind: Term("edge-kind")
    at: str | None = None
    """For ``level`` and ``schedule`` edges: ``boot`` | ``consolidation`` | ``commit``."""
    predicate: WatchPredicate | None = None
    """For ``edge`` edges keyed on world-state."""


class Guard(Strict):
    terms: list[Term(*HOOK_AXES)] = Field(default_factory=list)
    """The consultation hook's keys: registered terms the pass presents, from either hook axis (:data:`HOOK_AXES`) — a
    work-shape or a convention — so a lesson about a world-convention is retrievable on that convention, not only on the
    tool the attempt reached for."""
    not_this: list[str] = Field(default_factory=list)
    records: list[str] = Field(default_factory=list)
    """For the ``neighbor`` key-space: the record ids whose status change is the edge."""
    statuses: dict[str, str] = Field(default_factory=dict)
    """For the ``neighbor`` key-space: each record's status when the latch was written; the edge is a departure from it."""
    applied_over_considered_below: float | None = None
    over_passes: int | None = None


class OwedAct(Strict):
    class_: Term("act-class") = Field(alias="class")
    role: Term("owed-act-role")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class LatchLifecycle(Strict):
    status: Term("latch-lifecycle") = "live"
    settled_at: datetime | None = None
    settled_by: str | None = None


class Latch(Strict):
    """⟨key-space · edge · guard · consumer · owed act · lifecycle⟩ attached to one slot."""

    type: Term("latch-type")
    slot: Term("slot")
    key_space: Term("key-space")
    edge: Edge
    guard: Guard = Field(default_factory=Guard)
    consumer: str
    owed_act: OwedAct
    lifecycle: LatchLifecycle = Field(default_factory=LatchLifecycle)
    warrant: str | None = None
    """Required only for a latch off its port declaration."""

    @model_validator(mode="after")
    def _key_space_matches_edge(self):
        if self.key_space == "world-state" and self.edge.predicate is None:
            raise ValueError("a world-state latch names a watch predicate")
        if self.key_space == "work-shape" and not self.guard.terms:
            # "work-shape" is the presented-terms key-space: the terms the pass presents, spanning both hook axes
            # (:data:`HOOK_AXES` — a work-shape or a convention). The name is kept for the records already written on it.
            raise ValueError("a presented-terms latch names at least one registered term")
        if self.key_space == "neighbor" and not self.guard.records:
            raise ValueError("a neighbor latch names at least one record id")
        return self


# --- shared slots -------------------------------------------------------------

class Priced(Strict):
    model_id: str | None = None
    """The frozen model this record is priced for; ``None`` reads as unpriced."""
    authored_for: str | None = None
    """Set when the stamp has been moved without the text being re-authored: the
    model the text was actually written against. ``None`` means the stamp and the
    authoring agree, which is the case until ``hgi price --restamp`` moves one."""


class Enforcement(Strict):
    floor: list[str] = Field(default_factory=list)
    """Lint checks by name, from :mod:`hgi.lint`'s check list."""
    residue: list[str] = Field(default_factory=list)


# --- constitution -------------------------------------------------------------

class GenesisWarrant(Strict):
    evidence: str
    """``genesis`` for a seed article; otherwise the anchors that earned it."""
    anchors: list[str] = Field(default_factory=list)


class ConstitutionArticle(Envelope):
    kind: Literal["constitution"] = "constitution"
    status: Term("constitution-status")
    article: str
    counterfactual: str
    warrant: GenesisWarrant
    priced_for: Priced = Field(default_factory=Priced)

    @property
    def size(self) -> int:
        return len(self.article.encode()) + len(self.counterfactual.encode())


# --- decision -----------------------------------------------------------------

class Summary(Strict):
    """The cheap cue: what the reader sees before opening the record. Passes the settlement test by construction."""

    latch: str
    not_this: list[str] = Field(default_factory=list)
    stakes: str


class Option(Strict):
    name: str
    judged: Literal["chosen", "rejected"]
    why: str


class Premise(Strict):
    id: str
    statement: str
    falsifier: str
    status: Term("premise-status") = "unevaluated"


class Adjudication(Strict):
    ledger_entry: str | None = None
    species: Term("species") = "attack"
    verdict: str = "pending"


class DecisionWarrant(Strict):
    anchors: list[str] = Field(default_factory=list)
    premises: list[Premise] = Field(default_factory=list)
    adjudication: Adjudication = Field(default_factory=Adjudication)


class DecisionLifecycle(Strict):
    consumer: str
    moot_when: str
    retirement: Latch


class DecisionBody(Strict):
    """The content of a decision — everything but the envelope. A draft carries a body; an admitted decision carries a body inside an envelope."""

    scopes: list[str] = Field(default_factory=list)
    summary: Summary
    context: str
    options: list[Option]
    decision: str
    counterfactual: str
    warrant: DecisionWarrant
    latches: list[Latch]
    enforcement: Enforcement
    lifecycle: DecisionLifecycle
    priced_for: Priced = Field(default_factory=Priced)

    def all_latches(self) -> list[Latch]:
        return [*self.latches, self.lifecycle.retirement]

    @property
    def consultation_terms(self) -> list[str]:
        return [t for l in self.latches if l.type == "consultation" for t in l.guard.terms]

    @property
    def consultation_not_this(self) -> list[str]:
        return [n for l in self.latches if l.type == "consultation" for n in l.guard.not_this]


class Decision(Envelope, DecisionBody):
    kind: Literal["decision"] = "decision"
    status: Term("decision-status")

    def body(self) -> DecisionBody:
        """The content without the envelope — what a successor, a leaf or a fold derives from; never a second copy."""
        return DecisionBody.model_validate(self.model_dump(by_alias=True, include=set(DecisionBody.model_fields)))


# --- observation (pre-admission stratum) -------------------------------------

class Anchor(Strict):
    call: str | None = None
    path: str | None = None
    record: str | None = None
    commit: str | None = None

    @model_validator(mode="after")
    def _non_empty(self):
        if not any([self.call, self.path, self.record, self.commit]):
            raise ValueError("an anchor names at least one of call, path, record, commit")
        return self


class ObservationDisposition(Strict):
    state: Term("observation-state") = "open"
    pointer: str | None = None
    at: datetime | None = None


class Observation(Strict):
    uid: str
    name: str
    kind: Literal["observation"] = "observation"
    noticed_at: datetime
    session: str
    happened: str = Field(min_length=1)
    """The settled world-fact the attempt met: the row output, the tool error, the query text — price-zero, transcribable.
    The grouping keys on it. Non-empty by construction: an observation states what happened."""
    turned_on: str | None = None
    """The convention the attempt met or missed — the model's inference, lower-trust; optional, never grouped on.
    Kept out of the ``happened`` register so suspected and verified never share one field."""
    anchor: Anchor
    recheck_when: str | None = None
    shape: list[Term("convention")] = Field(default_factory=list)
    """Empty at intake; filled by the consolidation pass's grouping into the open ``convention`` axis (a minted
    ``other(<what>)`` label per cluster), never by the noticing session and never from the ``work-shape`` hook vocabulary."""
    disposition: ObservationDisposition = Field(default_factory=ObservationDisposition)


# --- fire ---------------------------------------------------------------------

class LatchRef(Strict):
    record: str
    index: int
    """Index into the record's ``all_latches()``."""


class EdgeEvent(Strict):
    """What moved: for a world-state latch the evaluation's scorer; for a neighbour latch ``<id>.status``; for a schedule latch the passes elapsed."""

    evaluation: str
    """The Weave evaluation for a world-state edge, else the key-space that moved: ``neighbor`` | ``competence``."""
    pass_: int = Field(alias="pass")
    scorer: str
    observed: float | str
    source: str | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FireDisposition(Strict):
    act: Term("act-class")
    outcome: str | None = None
    at: datetime | None = None
    by: str | None = None

    @property
    def discharged(self) -> bool:
        return self.outcome is not None


class Fire(Strict):
    id: str
    kind: Literal["fire"] = "fire"
    fired_at: datetime
    latch: LatchRef
    edge_event: EdgeEvent
    guard_result: bool
    disposer: str = Field(min_length=1)
    """A fire that cannot name its disposer is a standing false alarm by construction."""
    disposition: FireDisposition


# --- use-time disposition -----------------------------------------------------

class Disposition(Strict):
    id: str
    kind: Literal["disposition"] = "disposition"
    session: str
    record: str
    considered: bool
    guard_passed: bool
    disposition: Term("use-time-disposition")
    note: str | None = None


# --- steer --------------------------------------------------------------------

class SteerSource(Strict):
    kind: Term("steer-source")
    anchor: str | None = None


class Indictment(Strict):
    record: str
    slot: Term("slot")
    signature: str


class Steer(Strict):
    id: str
    kind: Literal["steer"] = "steer"
    at: datetime
    source: SteerSource
    session: str | None = None
    """The session the correction belongs to — the one whose call the note was left on, which for a late note is an earlier
    session than the close that captured it; ``None`` for an oracle-attributed steer, whose occasion is the consolidation."""
    correction: str
    indicts: Indictment | None = None
    why_not_caught: str | None = None
    matrix_cell: Term("matrix-cell")


# --- facts (the oracle's floor, mirrored on the session) ----------------------

class Fact(Strict):
    """A settled, as-of-stamped measurement. Absent data reads ``unevaluable``, never zero."""

    series: str
    """``<evaluation>/<scorer>``."""
    value: float | None = None
    unevaluable: str | None = None
    """The reason the scorer could not run; present exactly when ``value`` is absent."""
    as_of: datetime
    source: str | None = None

    @model_validator(mode="after")
    def _oracle_honesty(self):
        if (self.value is None) == (self.unevaluable is None):
            raise ValueError("a fact carries exactly one of value and unevaluable")
        return self


class EvaluationResult(Strict):
    evaluation: str
    run: str | None = None
    suite_hash: str | None = None
    scores: dict[str, Fact] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    """Per-task outcomes as the trace store holds them — result, error, tool errors, applied records, call URI."""


# --- session ------------------------------------------------------------------

class WorkShape(Strict):
    """The terms the pass presents, read at boot from the task presentations — across both hook axes
    (:data:`HOOK_AXES`): the tasks' declared work-shapes floor it, and the classification adds the work-shapes and the
    conventions it reads on top. It is the key-space the stage-one hook index is matched against, so a consultation hook
    keyed on a convention the presentations exhibit fires here, not only a work-shape one."""

    terms: list[Term(*HOOK_AXES)] = Field(default_factory=list)
    escapes: list[str] = Field(default_factory=list)


class Consulted(Strict):
    record: str
    disposition: str | None = None
    """The ``U-`` id; ``None`` until close."""


class Considered(Strict):
    """One stage-one selection event: the routing verdict before the pass disposes it."""

    record: str
    terms_matched: list[str] = Field(default_factory=list)
    via: Literal["index", "lexical", "constitution"]
    guard_passed: bool
    owed_act: str


class LensAnswer(Strict):
    lens: str
    answer: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    call: str | None = None


class Session(Strict):
    id: str
    kind: Literal["session"] = "session"
    pass_: int = Field(alias="pass")
    started_at: datetime
    closed_at: datetime | None = None
    model_id: str | None = None
    trace_root: str | None = None
    work_shape: WorkShape = Field(default_factory=WorkShape)
    considered: list[Considered] = Field(default_factory=list)
    consulted: list[Consulted] = Field(default_factory=list)
    lens_answers: list[LensAnswer] = Field(default_factory=list)
    fires_seen: list[str] = Field(default_factory=list)
    observations_filed: list[str] = Field(default_factory=list)
    steers_filed: list[str] = Field(default_factory=list)
    ledger_entries: list[str] = Field(default_factory=list)
    proposals: list[str] = Field(default_factory=list)
    evaluation: EvaluationResult | None = None
    carry_forward: str = ""
    attached: bool = True
    """``False`` for an ablation pass: same agent, same suite, no boot or close."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --- hypothesis ledger --------------------------------------------------------

class AttackClaim(Strict):
    target: str
    """What is attacked: ``premise:p2``, ``payload``, ``activation``, ``warrant`` …"""
    refutation: str
    """Refute-phrased: what reading of the evidence would show the claim false."""
    reading_taken: bool
    landed: bool
    evidence: list[str] = Field(default_factory=list)
    lens: str | None = None
    """The examiner lens whose angle produced the claim — one angle per context (the fan law); ``None`` for a single-context attack."""
    call: str | None = None
    """That context's Weave call URI, so each angle's product is joinable to its own trace."""


MECHANICAL: tuple[str, ...] = ("warrant:independence", "warrant:watch-direction")
"""The attack classes the code reads instead of a lens: the distinct-session count against the bar, and the watch's
direction against the stakes. Their claims carry no lens and no call, join the attack first, and an examiner claim on
either that contradicts the computed reading is discarded (:func:`hgi.consolidate.settle`)."""


class Attack(Strict):
    """The examiner's payload. It carries no verdict; ``pending`` is the only value the schema admits here."""

    claims: list[AttackClaim]
    verdict: Literal["pending"] = "pending"


class Contradiction(Strict):
    source: RoleCall
    attack: Attack | None = None
    coding: dict[str, Any] | None = None


class LedgerEntry(Strict):
    id: str
    kind: Literal["hypothesis"] = "hypothesis"
    at: datetime
    species: Term("species")
    subject: str
    """The draft uid or the record id the entry is about."""
    claim: str
    proposer: RoleCall
    contradiction: Contradiction
    verdict: str = "pending"
    adjudicator: RoleCall | None = None
    amendment: str | None = None
    rationale: str | None = None
    """The adjudicator's one-sentence weighing of the attack against the evidence."""
    rung: Term("ladder-rung") | None = None
    outcome: str | None = None
    """What the committer did: ``admitted D-0007`` | ``declined`` | ``escalated`` | ``deferred``."""

    @model_validator(mode="after")
    def _verdict_in_species_vocabulary(self, info: ValidationInfo):
        if self.verdict == "pending":
            return self
        reg = _registry_for(info)
        vocab = f"{self.species}-verdict"
        if vocab in reg.vocabularies:
            reg.check(vocab, self.verdict)
        return self


# --- proposals (the pre-admission tier) --------------------------------------

class Deferral(Strict):
    """A ``defer(<until>)`` verdict made concrete: the condition as a latch, re-queued to the backward pass.

    The latch is keyed on the world (a watch predicate the oracle's next runs
    settle) or on the schedule (passes to wait); its fire is owed to the
    backward pass, which re-adjudicates the draft in fresh contexts.
    """

    ledger_entry: str
    until: Latch
    deferred_at: datetime
    after_pass: int
    """The pass the deferring consolidation had read up to; a schedule latch counts from here."""


class Draft(Strict):
    """A candidate record. Eternal identity attaches at admission; a draft carries a non-recycled ``uid`` and a recyclable ``name``."""

    uid: str
    name: str
    kind: Literal["decision"] = "decision"
    drafted_at: datetime
    proposed_by: str
    rung: Term("ladder-rung")
    rung_why: str
    """Why the cheaper rungs do not suffice."""
    displaced_from: Term("ladder-rung") | None = None
    """The rung the nomination named when this roster has no operator for it (:data:`hgi.consolidate.DISPLACED_TO`)."""
    body: DecisionBody
    evidence: list[str] = Field(default_factory=list)
    """The observation uids, steer ids and Weave URIs the draft rests on."""
    supersedes: list[str] = Field(default_factory=list)
    """Decisions this draft retires on admission; the committer writes the reciprocal lineage pointers."""
    split_from: str | None = None
    """The fused record this draft is a leaf of (§ 10.6): the parent retires when its first heir lands and lists every heir."""
    folded_from: list[str] = Field(default_factory=list)
    """The records whose payloads this draft contracts into one (§ 10.6): each retires on admission, superseded by the fold."""

    deferral: Deferral | None = None
    """Set by the committer on a ``defer(<until>)`` verdict; ``None`` for a draft awaiting its first adjudication."""

    def all_latches(self) -> list[Latch]:
        """The body's fan plus the deferral latch, indexed the way a fire's ``latch.index`` reads."""
        return [*self.body.all_latches(), *([self.deferral.until] if self.deferral else [])]

    @model_validator(mode="after")
    def _lineage_operators(self):
        if len(self.folded_from) == 1:
            raise ValueError("a fold contracts at least two records; one predecessor is a supersedure")
        if self.split_from and self.split_from in self.folded_from:
            raise ValueError("a record is split from or folded from, not both")
        return self

    @property
    def retires(self) -> list[str]:
        """Every record this draft's admission flips to ``superseded``."""
        out = [*self.supersedes, *self.folded_from]
        if self.split_from:
            out.append(self.split_from)
        return list(dict.fromkeys(out))


class QueueEntry(Strict):
    """An escalated proposal awaiting a human verdict from the same closed vocabulary."""

    draft: Draft
    ledger_entry: str
    why: str
    queued_at: datetime
    oracle_evidence: dict[str, Any] = Field(default_factory=dict)


# --- lens ---------------------------------------------------------------------

class Externality(Strict):
    contact: Term("lens-contact")
    terminates_in: str


class LensTelemetry(Strict):
    answer_variance: str = "design-stage"
    decoy_rejection: str = "design-stage"
    signal_caught: str = "design-stage"
    miss_stream: str = "steers/ citing this lens"


class Lens(Strict):
    """Composition's unit, evaluated at the lens's coordinates of the pentad (doctrine § 14.1): activation is its host's
    walk; the payload a question, never an answer; the warrant its effect evidence — the anchored instances its product
    reached a consumer through, and the steers that cite it; enforcement the floor's shape checks with answer truth as
    residue; the lifecycle the crystallization doors — variance-collapse and authority-crystallization — plus the
    genesis deadline every seed shares."""

    id: str
    kind: Literal["lens"] = "lens"
    status: Term("lens-status") = "live"
    angle: str
    counterfactual: str
    purpose: Term("lens-purpose")
    externality: Externality
    product: str
    consumer: str
    host: Term("lens-host")
    claims: list[str] = Field(default_factory=list)
    """For an examiner-hosted lens: the attack-claim target classes its angle may land on, as prefixes (``premise:``,
    ``warrant:independence``). A claim outside them is another angle's product and is dropped — a distinct product per
    angle is what makes the fan an ensemble rather than a longer prompt."""
    warrant: GenesisWarrant = Field(default_factory=lambda: GenesisWarrant(evidence="genesis"))
    """Effect evidence: ``genesis`` until the lens's product reaches a consumer — an observation promoted, an entry
    adjudicated, a claim upheld, a steer citing it — each such instance an anchor. A seed lens unanchored past the
    deadline is a question nobody's answer ever needed."""
    priced_for: Priced = Field(default_factory=Priced)
    telemetry: LensTelemetry = Field(default_factory=LensTelemetry)


# --- consolidation record -----------------------------------------------------

class Nomination(Strict):
    rung: Term("ladder-rung")
    rung_why: str
    displaced_from: Term("ladder-rung") | None = None
    """The rung the consolidator named, when the nomination was carried at another for want of an operator."""
    subject: str
    evidence: list[str]
    draft: str | None = None
    """The draft uid, when the nomination produced one."""
    adopts: str | None = None
    """The uid of a pass proposal the nomination adopted as its draft, instead of sketching one."""
    ledger_entry: str | None = None
    outcome: str | None = None


class Consolidation(Strict):
    id: str
    kind: Literal["consolidation"] = "consolidation"
    started_at: datetime
    closed_at: datetime | None = None
    after_pass: int
    sessions_read: list[str]
    brief: dict[str, Any] = Field(default_factory=dict)
    """The consolidation brief: applied ÷ considered per record, observation groups by convention cluster (ordered ripe-first
    and annotated with each cluster's ``ripeness``, item 58 lever A), escape clusters, the ``unelicited`` recall-floor
    telemetry — the window's ``failure-unelicited`` markers (a failed row that elicited no observation), surfaced for the
    human, never a group to nominate on — and the ``transcription`` block (item 58 lever B: the price-zero facts written and
    the ambiguities surfaced for the human)."""
    analyst_report: str | None = None
    """The ARIA report URI, when the brief was drafted by the analyst."""
    nominations: list[Nomination] = Field(default_factory=list)
    fires_discharged: list[str] = Field(default_factory=list)
    admitted: list[str] = Field(default_factory=list)
    flipped: list[str] = Field(default_factory=list)
    deferred: list[str] = Field(default_factory=list)
    """Draft uids re-queued with their condition as a latch."""
    anchored: list[str] = Field(default_factory=list)
    """Genesis articles that earned an anchor in this pass."""
    minted: list[str] = Field(default_factory=list)
    """Vocabulary terms minted in this pass, as ``<vocabulary>/<term>``."""
    expired: list[str] = Field(default_factory=list)
    """Pass proposals dropped unadopted at the bar ``proposal_ttl_consolidations``."""
    dismissed: list[str] = Field(default_factory=list)
    """Observations the noise filter dismissed as irreducible, each pointing at its reality entry (§ 10.2)."""
    corroborated: list[str] = Field(default_factory=list)
    """Draft uids the dedup guard routed to corroboration of an already-accepted decision instead of minting a twin
    (carry-forward item 61): the draft rested only on world-facts that decision already anchors, so a ``still-holds``
    currency entry corroborated the standing record and the duplicate mint was refused."""
    retired: list[str] = Field(default_factory=list)
    """Lenses retired in this pass through a crystallization door or the genesis deadline."""
    transcribed: list[Fact] = Field(default_factory=list)
    """The price-zero happenstance facts this pass transcribed without adjudication (carry-forward item 58 lever B): each a
    settled ``happened`` world-content, mechanically evaluable through its anchor, keyed by the world-content token. The one
    machine-write §10.3 permits past the owner gate, legal exactly because the price was zero and evaluation is mechanical;
    a ``happened`` that is not mechanically evaluable is surfaced to the human in the brief instead, never written here. The
    inference (``turned_on``) is never transcribed — it crosses the gate as a decision payload, adjudicated, or not at all."""


# --- kind table ---------------------------------------------------------------

RECORD_MODELS: dict[str, type[BaseModel]] = {
    "constitution": ConstitutionArticle,
    "decision": Decision,
    "observation": Observation,
    "fire": Fire,
    "disposition": Disposition,
    "steer": Steer,
    "session": Session,
    "hypothesis": LedgerEntry,
    "consolidation": Consolidation,
    "lens": Lens,
}
