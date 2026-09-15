"""Reasoning Core's checkers and generators, vendored for the ``reasoning-core`` family.

The generators come from Reasoning Core (``sileod/reasoning-core``, MIT); this
module holds two things and nothing that imports the suite:

- the **checks**, at runtime — a produced string is graded by the generator's
  own verdict, not by a comparison against a stored answer. ``regex_ok`` is
  Reasoning Core's regex-following verdict (``regex.py``): a non-empty visible
  ASCII string that ``regex.fullmatch`` accepts. ``cfg_ok`` is grammar
  membership by the same parser Reasoning Core's grammar tasks use, NLTK's
  Earley chart parser (``grammar.py``). Both import only ``regex`` and
  ``nltk`` — declared in ``pyproject`` — never ``reasoning_core``;
- the **generation**, at fetch time — :func:`records` drives Reasoning Core's
  ``RegexFollowing`` and grammar generators at a pinned difficulty level and
  returns the pinned instances. It imports ``reasoning_core`` and its
  generation stack (``gramforge``, ``faker``, …) lazily, so a run that only
  reads the pinned file never needs them.

Reasoning Core's difficulty is a single integer ``level`` its configs fold
into their own fields (``RegexConfig``: pattern depth and example count;
``GrammarConfig``: rule count, sentence depth, alphabet). A difficulty *tier*
groups the two generators' levels, the witness-length window a grammar
instance is kept within, and the seed bases each generator's instances draw
from, into one :class:`Tier` value, so a harder tier is a config value passed
to :func:`records`, not a fork of the generation code. Two are defined:
:data:`MODERATE` (regex level 3, grammar level 2, six-to-twelve-token
witnesses) and :data:`HARD` (regex level 5, grammar level 3, ten-to-sixteen-
token witnesses), on disjoint seed bases so their instances never overlap.
Generation is made reproducible against that revision:
``gramforge.generate`` reseeds Python's RNG from entropy on every call
(``seed=None``), so :func:`records` patches the name Reasoning Core bound and
feeds it seeds from a per-instance ``random.Random``; ``faker`` is seeded
before the task modules are imported, since their terminal word lists are built
at import.

Source: ``sileod/reasoning-core`` (MIT), revision ``1c87ac6`` (2026-09-11),
package version ``0.5.0``; paper arXiv:2509.18083.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable

REPO = "https://github.com/sileod/reasoning-core"
REVISION = "1c87ac63cae33621add38b19ef6b2bafe6cd94eb"
REVISION_DATE = "2026-09-11"
VERSION = "0.5.0"
LICENSE = "MIT"
PAPER = "arXiv:2509.18083"

# --- the checks: the generator's own verdict, over the agent's produced string ------------------

SFT_ALPHA = "".join(chr(i) for i in range(33, 127))
"""The visible-ASCII domain Reasoning Core samples regex targets from (``regex.py``)."""

MAX_CFG_TOKENS = 60
"""A produced grammar string past this many tokens is refused unparsed — a guard on the checker's cost, not a rule of the language."""


def _is_sft_sample(s: str) -> bool:
    """Reasoning Core's admissibility for a regex target (``regex.py``): non-empty, printable, no whitespace."""
    return bool(s) and s.isprintable() and not any(c.isspace() for c in s)


def regex_ok(pattern: str, result: Any) -> bool:
    """Reasoning Core's regex-following verdict: the result is a visible ASCII string ``regex.fullmatch`` accepts."""
    if not isinstance(result, str):
        return False
    s = result.strip("`\n\r ")
    if not _is_sft_sample(s):
        return False
    import regex

    try:
        return bool(regex.compile(pattern).fullmatch(s, timeout=1))
    except Exception:  # an invalid pattern or a match that times out is a failed task, never a raise from the grader
        return False


def cfg_ok(grammar: str, start: str, min_tokens: int, result: Any) -> bool:
    """Grammar membership by Reasoning Core's parser (NLTK Earley): the result is ``min_tokens`` or more terminals the grammar derives."""
    if not isinstance(result, str):
        return False
    tokens = result.split()
    if len(tokens) < min_tokens or len(tokens) > MAX_CFG_TOKENS:
        return False
    try:
        from nltk import CFG, Nonterminal
        from nltk.parse.earleychart import EarleyChartParser

        # NLTK reads the first rule's LHS as the start symbol; the rules are shuffled, so the start is set back explicitly.
        g = CFG.fromstring(grammar.replace(" ::= ", " -> "))
        g = CFG(Nonterminal(start), g.productions())
        return next(EarleyChartParser(g).parse(tokens), None) is not None
    except Exception:  # an out-of-vocabulary token or an unparsable string is a failed task, never a raise from the grader
        return False


# --- the generation: Reasoning Core's own generators, seeded, at a per-tier difficulty ------------


@dataclass(frozen=True)
class Tier:
    """A difficulty setting for the two generators, so a harder tier is a config value, not a code fork.

    ``regex_level`` and ``cfg_level`` are Reasoning Core's own integer ``level`` knob for the
    ``RegexFollowing`` and grammar generators. ``cfg_tokens`` is the ``(lo, hi)`` witness-length window a
    grammar instance is kept within — the witness's own length becomes the instance's ``min_tokens``, so a
    higher floor forces a longer valid derivation. ``regex_seed_base`` / ``cfg_seed_base`` are where each
    generator's instance seeds start; a tier's bases are far enough apart that skipped seeds never overlap
    and disjoint from every other tier's, so no instance is shared between tiers.
    """

    name: str
    regex_level: int
    cfg_level: int
    cfg_tokens: tuple[int, int]
    regex_seed_base: int
    cfg_seed_base: int


MODERATE = Tier(name="moderate", regex_level=3, cfg_level=2, cfg_tokens=(6, 12),
                regex_seed_base=20_250_918, cfg_seed_base=30_250_918)
"""The moderate tier pinned in ``reasoning-core.jsonl``: patterns with alternation, groups, counts and
anchors; grammar sentences of six to twelve terminals over small grammars."""

HARD = Tier(name="hard", regex_level=5, cfg_level=3, cfg_tokens=(10, 16),
            regex_seed_base=40_250_918, cfg_seed_base=50_250_918)
"""The harder tier pinned in ``reasoning-core-hard.jsonl``: deeper-nested patterns (more nesting,
backreferences, escaped literals, ``\\B`` anchors) and larger grammars whose members run ten to sixteen
terminals, on seed bases disjoint from :data:`MODERATE` so the two tiers share no instance."""

FAKER_SEED = 0
"""Seeds Reasoning Core's import-time terminal word lists, so the vocabulary is fixed across regenerations."""


def _rc_modules():
    """Reasoning Core's regex and grammar task modules, with ``faker`` seeded first so their word lists are fixed."""
    try:
        from faker import Faker
    except ImportError as e:  # the generation stack is not a runtime dependency; only fetch needs it
        raise SystemExit(
            f"reasoning-core generation needs the generator installed: pip install "
            f"'reasoning_core @ git+{REPO}@{REVISION}' (and gramforge, greenery, faker, nltk, exrex)"
        ) from e
    Faker.seed(FAKER_SEED)
    import reasoning_core.tasks.grammar as grammar
    import reasoning_core.tasks.regex as regex_

    return regex_, grammar


def _seeded_gramforge(orig: Callable, master: random.Random) -> Callable:
    """``gramforge.generate`` wrapped to draw a seed from ``master`` when Reasoning Core passes none, so a run is reproducible."""

    def patched(*args, **kwargs):
        if kwargs.get("seed") is None:
            kwargs["seed"] = master.randrange(1 << 31)
        return orig(*args, **kwargs)

    return patched


def _regex_records(n: int, tier: Tier = MODERATE) -> list[dict[str, Any]]:
    regex_, _ = _rc_modules()
    orig = regex_.generate
    out: list[dict[str, Any]] = []
    i = 0
    try:
        while len(out) < n:
            seed = tier.regex_seed_base + i
            i += 1
            regex_.generate = _seeded_gramforge(orig, random.Random(seed))
            random.seed(seed)
            try:
                problem = regex_.RegexFollowing().generate_example(level=tier.regex_level, timeout=30)
            except Exception:
                continue
            pattern, witness = problem.metadata.regex, problem.answer
            if len(witness) < 2 or not regex_ok(pattern, witness):  # drop trivial one-char targets; the witness proves the pattern satisfiable
                continue
            out.append({"id": f"regex_{len(out):02d}", "kind": "regex-following", "level": tier.regex_level,
                        "seed": seed, "rc_task": problem.task, "pattern": pattern, "witness_len": len(witness)})
    finally:
        regex_.generate = orig
    return out


def _cfg_records(n: int, tier: Tier = MODERATE) -> list[dict[str, Any]]:
    _, grammar = _rc_modules()
    orig = grammar.gramforge_generate
    lo, hi = tier.cfg_tokens
    out: list[dict[str, Any]] = []
    i = 0
    try:
        while len(out) < n:
            seed = tier.cfg_seed_base + i
            i += 1
            grammar.gramforge_generate = _seeded_gramforge(orig, random.Random(seed))
            random.seed(seed)
            try:
                # random_grammar_prob=1.0 with free_form off keeps generation on `random_productive_cfg`, whose only
                # randomness is Python's seeded RNG and the faker-seeded word list; the pre-built english grammars reach
                # `trim_grammar`, which seeds a `random.Random(None)` from entropy and so cannot be reproduced.
                config = grammar.GrammarConfig(perturbation_rate=0.0, bnf_operator_prob=0.0,
                                               random_grammar_prob=1.0, free_form_grammar_prob=0.0)
                config.set_level(tier.cfg_level)
                meta = grammar.generate_parse(config)
            except Exception:
                continue
            if meta.label != "unambiguous" or not (lo <= len(meta.tokens) <= hi):
                continue
            text, start, min_tokens = meta.g.replace(" ::= ", " -> "), str(meta.start), len(meta.tokens)
            if not cfg_ok(text, start, min_tokens, " ".join(meta.tokens)):  # the witness proves the requirement satisfiable
                continue
            out.append({"id": f"cfg_{len(out):02d}", "kind": "cfg-generation", "level": tier.cfg_level,
                        "seed": seed, "rc_task": "grammar", "grammar": text, "start": start, "min_tokens": min_tokens})
    finally:
        grammar.gramforge_generate = orig
    return out


def records(n_regex: int, n_cfg: int, tier: Tier = MODERATE) -> list[dict[str, Any]]:
    """The pinned instances at ``tier``: ``n_regex`` regex-following and ``n_cfg`` grammar-generation, seeded and reproducible against the pinned revision."""
    return _regex_records(n_regex, tier) + _cfg_records(n_cfg, tier)
