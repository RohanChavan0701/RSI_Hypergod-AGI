"""The registry: closed vocabularies, port declarations, bars, the constitution
cap, the lens register and the id counters.

The registry is a *register* — a current-state surface corrected in place,
with git carrying its history. Every closed vocabulary ships the escape
``other(<what>)``; a value outside a vocabulary without the escape is refused
at parse time by the validators in :mod:`hgi.types`, which read the registry
through :func:`current`.

Files under ``<store>/registry/``:

- ``vocabulary.json``   ``{vocab: {"means": …, "terms": {term: {"means": …, "since": …}}}}``
- ``ports.json``        ``{kind: {status: {latch_type: "required"|"optional"|"forbidden"}}}``
- ``bars.json``         promotion bars and the review window (spec § 10.4)
- ``constitution.json`` ``{"max_articles": n, "max_bytes": n}``
- ``lenses.json``       the lens register, a list of lens records
- ``ids.json``          ``{prefix: last_issued}`` — the monotone counters
"""

from __future__ import annotations

from filelock import FileLock
import json
import os
import re
import tempfile
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ESCAPE = re.compile(r"^other\((.+)\)$")
"""Every closed vocabulary admits ``other(<what>)``; the group is the ``what``."""

_PARAMETRIC = re.compile(r"^([a-z-]+)\(<[^>]+>\)$")
"""A term of the form ``name(<param>)`` matches any value ``name(…)``."""


def is_escape(value: str) -> bool:
    return bool(ESCAPE.match(value))


def term_matches(term: str, value: str) -> bool:
    """Whether ``value`` instantiates the registered ``term``.

    A plain term matches only itself. A parametric term such as
    ``decline(<why>)`` matches ``decline(anything non-empty)``.
    """
    if term == value:
        return True
    m = _PARAMETRIC.match(term)
    if m:
        return bool(re.match(rf"^{re.escape(m.group(1))}\(.+\)$", value))
    return False


def term_head(value: str) -> str:
    """``decline(too weak)`` → ``decline``; a plain term is its own head."""
    return value.split("(", 1)[0]


class Unrouted(LookupError):
    """A verdict the vocabulary admits but the seam has no act for — refused loud, never a silent fall-through."""


ROUTE_TABLES: list[tuple[str, str, dict[str, str]]] = []
"""Every declared route table as ``(seam, vocabulary, {head: act})``; the tests prove each covers its vocabulary."""


def route_table(seam: str, vocab: str, table: dict[str, str]) -> dict[str, str]:
    """Declare the act a seam takes on each head of a verdict vocabulary.

    A table names every registered head and ``other`` (the escape is always
    admitted, so it is always routed); a term added to the vocabulary without
    a route is a test failure, and a verdict reaching the seam without one
    raises :class:`Unrouted`. The act is a tag the seam dispatches on, so a
    table can be read and checked without running the seam.
    """
    ROUTE_TABLES.append((seam, vocab, table))
    return table


@dataclass
class Vocabulary:
    name: str
    means: str
    terms: dict[str, dict[str, Any]]

    def check(self, value: str) -> str:
        """Return ``value`` if it is a registered term or an escape; raise otherwise."""
        if is_escape(value):
            return value
        if any(term_matches(t, value) for t in self.terms):
            return value
        raise ValueError(
            f"{value!r} is not in the closed vocabulary {self.name!r} "
            f"({', '.join(self.terms)}) and is not an other(<what>) escape"
        )


@dataclass
class Registry:
    root: Path
    vocabularies: dict[str, Vocabulary]
    ports: dict[str, dict[str, dict[str, str]]]
    bars: dict[str, Any]
    constitution_cap: dict[str, int]
    ids: dict[str, int] = field(default_factory=dict)

    # --- paths ---------------------------------------------------------
    @property
    def dir(self) -> Path:
        return self.root / "registry"

    def path(self, name: str) -> Path:
        return self.dir / f"{name}.json"

    # --- vocabulary ----------------------------------------------------
    def vocab(self, name: str) -> Vocabulary:
        try:
            return self.vocabularies[name]
        except KeyError:
            raise KeyError(f"no closed vocabulary named {name!r} in {self.path('vocabulary')}") from None

    def check(self, vocab: str, value: str) -> str:
        return self.vocab(vocab).check(value)

    def route(self, vocab: str, verdict: str, table: dict[str, str]) -> str:
        """The act ``table`` names for ``verdict``; the verdict is checked against ``vocab`` first."""
        self.check(vocab, verdict)
        head = "other" if is_escape(verdict) else term_head(verdict)
        try:
            return table[head]
        except KeyError:
            raise Unrouted(f"{vocab} verdict {verdict!r} has no route at this seam; routed heads are {sorted(table)}") from None

    def unrouted(self, vocab: str, table: dict[str, str]) -> list[str]:
        """The heads of ``vocab`` (and the escape) that ``table`` leaves without an act."""
        heads = {term_head(t) for t in self.terms(vocab)} | {"other"}
        return sorted(heads - set(table))

    def vocabulary_terms(self) -> dict[str, list[str]]:
        """Every closed vocabulary's terms by name — what a role drafting a record must draw its typed fields from."""
        return {name: self.terms(name) for name in self.vocabularies}

    def terms(self, vocab: str) -> list[str]:
        return list(self.vocab(vocab).terms)

    def terms_over(self, *vocabs: str) -> list[str]:
        """The union of several vocabularies' terms, de-duplicated in first-seen order — the vocabulary a field spanning
        axes draws from. The hook vocabulary is ``terms_over(*hgi.types.HOOK_AXES)``: the terms a consultation hook may
        key on, across the work-shape and convention axes."""
        seen: dict[str, None] = {}
        for vocab in vocabs:
            for t in self.terms(vocab):
                seen.setdefault(t, None)
        return list(seen)

    def add_term(self, vocab: str, term: str, means: str, since: str) -> None:
        """Grow a vocabulary — the route-before-mint ladder's last rung for a term."""
        self.vocab(vocab).terms[term] = {"means": means, "since": since}
        self.save("vocabulary")

    # --- ports ---------------------------------------------------------
    def port(self, kind: str, status: str, latch_type: str) -> str:
        """The obligation mark for a latch type on a kind at a status; ``optional`` when undeclared."""
        return self.ports.get(kind, {}).get(status, {}).get(latch_type, "optional")

    # --- ids -----------------------------------------------------------
    def mint(self, prefix: str) -> str:
        """Reserve the next id for ``prefix`` and persist the counter. Ids are reserve-once and gap-tolerant.

        The counters on disk are the authority: they are re-read before every
        reservation, so two registry objects over one store — a long-running
        runner and the commands it drives — never hand out the same id.
        """
        ids_path = self.path("ids")
        ids_path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(self.dir / ".ids.lock"):  # concurrent minters — threads or processes — take turns
            if ids_path.exists():
                self.ids = read_json(ids_path)
            n = self.ids.get(prefix, 0) + 1
            self.ids[prefix] = n
            self.save("ids")
        return f"{prefix}-{n:04d}"

    # --- persistence ---------------------------------------------------
    def save(self, name: str) -> None:
        payload: Any
        if name == "vocabulary":
            payload = {
                v.name: {"means": v.means, "terms": v.terms} for v in self.vocabularies.values()
            }
        elif name == "ports":
            payload = self.ports
        elif name == "bars":
            payload = self.bars
        elif name == "constitution":
            payload = self.constitution_cap
        elif name == "ids":
            payload = self.ids
        else:
            raise KeyError(name)
        write_json(self.path(name), payload)

    def lenses(self, host: str | None = None, status: str | None = "live") -> list[Any]:
        """The lens register as typed :class:`hgi.types.Lens` records, optionally filtered by host; live lenses only
        unless ``status`` is ``None`` — a retired lens is kept as evidence and walked by nothing."""
        from hgi.types import Lens  # lazy: types validates against this registry

        raw = read_json(self.path("lenses"))
        lenses = [Lens.model_validate(item, context={"registry": self}) for item in raw]
        return [l for l in lenses if (host is None or l.host == host) and (status is None or l.status == status)]

    def patch_lens(self, lens_id: str, patch: dict[str, Any]) -> None:
        """Correct one lens in the register in place — the register's one write form; git carries the history."""
        path = self.path("lenses")
        write_json(path, [item | patch if item.get("id") == lens_id else item for item in read_json(path)])


# --- loading ---------------------------------------------------------------

def read_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    """Write canonical JSON: sorted keys, two-space indent, trailing newline — so regeneration is byte-stable.

    The write is atomic (a sibling temporary file renamed into place), so a
    concurrent reader sees the old file or the new one, never a torn one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def load(root: Path | str) -> Registry:
    root = Path(root)
    reg_dir = root / "registry"
    raw_vocab = read_json(reg_dir / "vocabulary.json")
    vocabularies = {
        name: Vocabulary(name=name, means=v.get("means", ""), terms=v["terms"])
        for name, v in raw_vocab.items()
    }
    ids_path = reg_dir / "ids.json"
    return Registry(
        root=root,
        vocabularies=vocabularies,
        ports=read_json(reg_dir / "ports.json"),
        bars=read_json(reg_dir / "bars.json"),
        constitution_cap=read_json(reg_dir / "constitution.json"),
        ids=read_json(ids_path) if ids_path.exists() else {},
    )


# --- the registry in scope ---------------------------------------------------

_current: ContextVar[Registry | None] = ContextVar("hgi_registry", default=None)


def default_root() -> Path:
    """The store root: ``$HGI_STORE`` or ``./store``."""
    return Path(os.environ.get("HGI_STORE", "store"))


def current() -> Registry:
    """The registry the validators consult when a parse supplies no explicit context."""
    reg = _current.get()
    if reg is None:
        reg = load(default_root())
        _current.set(reg)
    return reg


def use(registry: Registry | None):
    """Make ``registry`` the one in scope for this context (a token to reset with :func:`reset`)."""
    return _current.set(registry)


def reset(token) -> None:
    _current.reset(token)
