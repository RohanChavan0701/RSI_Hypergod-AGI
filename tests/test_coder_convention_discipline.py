"""Carry-forward item 71 fix (b): the blind coder prefers a *registered* ``convention`` term when one fits, and reserves
the ``other(...)`` escape for a genuine gap — a convention the vocabulary has no term for.

Item 71 point 5 root-caused the weak text2sql decisions to the coder escaping 100% (every label ``other(...)``, ``shape:
[]`` on two sessions), so the consolidator was handed escapes, not conventions — even where a registered term
(``schema-coded-value``, item 71 point 2) exactly fit. These tests pin the corrected discipline on the ``cluster`` path
(item 64's multi-shape coding): when a registered convention names the world-fact, the coder lands on it — especially the
broad label grouping depends on — rather than escaping; when nothing registered fits, it still escapes. The behaviour is
exercised through the deterministic stub, a lexical proxy for the model's convention inference; the prompt discipline is
what a live re-score confirms. The examples span the loop's families (a guarded route, a paged listing, an unterminated
file, a coded schema value) so the mechanism reads as universal, not keyed to any one domain."""

from __future__ import annotations

from hgi import coder as _coder


def _cluster(store, observations):
    shapes, _ = _coder.cluster(observations, store.registry.terms("convention"), session="K-test", records_in_context=[])
    return shapes


def test_cluster_lands_on_a_registered_convention_rather_than_escaping(store):
    """A guarded route (a 401 wanting a token) is a registered convention; the coder uses the term, it does not escape."""
    shapes = _cluster(store, [
        {"name": "o-token", "happened": "the /secure route answered 401 unauthorized; the attempt sent no token, the route wants it authorized"},
    ])
    assert "route-guarded" in shapes["o-token"]
    assert not any(l.startswith("other(") for l in shapes["o-token"]), "a registered convention fits; escaping is the lazy default the fix removes"


def test_cluster_uses_the_schema_convention_the_run_escaped(store):
    """Item 71 point 2 directly: ``schema-coded-value`` exactly fit the coded-value miss yet the run escaped. It now lands."""
    shapes = _cluster(store, [
        {"name": "o-coded", "happened": "task q117 filtered on the word 'paid' but the status is a coded value stored as a single-letter code, so nothing matched"},
    ])
    assert "schema-coded-value" in shapes["o-coded"]
    assert not any(l.startswith("other(") for l in shapes["o-coded"])


def test_two_misses_of_one_convention_share_the_registered_broad_label(store):
    """The broad label is the one grouping most needs on a registered term: two unterminated-file misses, worded
    differently, share ``line-unterminated`` so they group rather than each escaping to its own singleton."""
    shapes = _cluster(store, [
        {"name": "o-a", "happened": "task count_people read a file whose last line carried no trailing newline, so the count came up short"},
        {"name": "o-b", "happened": "task tally_rows: the final row is left without a terminating newline; wc -l counted one fewer"},
    ])
    assert "line-unterminated" in shapes["o-a"] and "line-unterminated" in shapes["o-b"]
    assert set(shapes["o-a"]) & set(shapes["o-b"]), "a shared registered label is the grouping key the escape would have scattered"


def test_a_genuine_gap_still_escapes(store):
    """The fix is 'prefer registered when it fits', not 'never escape': a bare budget miss turns on the way of working,
    not a world-convention the vocabulary names, so it escapes rather than borrowing a registered term that does not fit."""
    shapes = _cluster(store, [
        {"name": "o-budget", "happened": "task fan_out exceeded its shell budget: independent calls were issued one per input instead of batched"},
    ])
    assert all(l.startswith("other(") for l in shapes["o-budget"]), "no registered convention is behind a bare budget miss"
    assert not (set(store.registry.terms("convention")) & set(shapes["o-budget"])), "escaping does not force a registered term onto a world-fact it does not match"
