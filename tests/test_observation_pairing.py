"""Carry-forward item 71 fix (d): an observation's token-bearing and inference-bearing halves stay in one record.

Item 71 point 6 root-caused ~45% of the text2sql run's observations carrying ``turned_on: null`` — and those were the
token-bearing ones: the concrete literal lived in one finding (``happened`` set, ``turned_on`` null) while the inferred
convention lived in a *separate* finding on the same call anchor. Split across two records, the drafting floor (which
needs the literal) and the grouping (which needs the convention) never saw both. The lens prose now elicits one whole
finding per world-fact, and :func:`hgi.close._merge_split_findings` is a defensive safety-net that folds a still-split
pair back into one before filing — keying only on the shared ``call`` anchor, never on any domain literal, and merging
only a clean pair so nothing standalone is dropped."""

from __future__ import annotations

from hgi import close as _close
from hgi.types import LensAnswer
from tests.test_slice3 import FAULTED, _session

LIT = "the query returned the code 'VYDAJ' where the account operation was expected"
INF = "the schema stores the operation as a coded literal, matched on its stored form not a natural word"


def test_a_split_literal_and_inference_on_one_anchor_merge_into_one_observation(store):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    call = "weave:///t/call/split"
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        {"happened": LIT, "turned_on": None, "anchor": {"call": call}},               # the literal half: token, no inference
        {"happened": "the attempt matched a natural word", "turned_on": INF, "anchor": {"call": call}},  # the inference half
    ]))
    filed = _close.file_observations(store, s)
    assert len(filed) == 1, "the two halves file as one observation, not two half-observations"
    o = filed[0]
    assert o.happened == LIT, "the literal half's concrete world-fact survives in happened"
    assert o.turned_on == INF, "the inference half's convention is folded into the same record"
    assert o.anchor.call == call
    assert s.observations_filed == [o.name]


def test_a_standalone_literal_only_finding_is_filed_as_is(store):
    """A half with no sibling is not dropped and not invented for: it files exactly as it stood, ``turned_on`` still null."""
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        {"happened": "the route answered 410 and named its /v2 successor", "turned_on": None, "anchor": {"call": "weave:///t/call/solo"}},
    ]))
    filed = _close.file_observations(store, s)
    assert len(filed) == 1 and filed[0].turned_on is None
    assert filed[0].happened == "the route answered 410 and named its /v2 successor"


def test_whole_findings_on_different_calls_are_untouched(store):
    """Two already-whole findings on different anchors are unrelated: neither is merged and neither is dropped."""
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s.lens_answers.append(LensAnswer(lens="L-0009", answer="", findings=[
        {"happened": "the /secure route answered 401", "turned_on": "the route wants a token", "anchor": {"call": "weave:///t/call/x"}},
        {"happened": "the listing returned only the first page", "turned_on": "the listing pages", "anchor": {"call": "weave:///t/call/y"}},
    ]))
    filed = _close.file_observations(store, s)
    assert len(filed) == 2
    assert {o.turned_on for o in filed} == {"the route wants a token", "the listing pages"}


def test_two_whole_findings_on_one_call_are_both_kept(store):
    """A pair on one call where *each* finding already carries its inference is not the split pattern: both survive, so a
    genuinely-whole finding is never sacrificed to a merge."""
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    call = "weave:///t/call/two-whole"
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        {"happened": "the status code 'A' matched nothing", "turned_on": "a coded status literal", "anchor": {"call": call}},
        {"happened": "the date compared as text", "turned_on": "a text date needs a date function", "anchor": {"call": call}},
    ]))
    filed = _close.file_observations(store, s)
    assert len(filed) == 2, "neither finding lacks an inference, so nothing merges and nothing is dropped"
    assert {o.turned_on for o in filed} == {"a coded status literal", "a text date needs a date function"}


def test_a_literal_and_an_inference_on_different_calls_do_not_merge(store):
    """The merge keys on the *shared* call anchor: a literal on one call and an inference on another are not a pair."""
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        {"happened": "the code 'VYDAJ' was returned", "turned_on": None, "anchor": {"call": "weave:///t/call/lit"}},
        {"happened": "the query matched a natural word", "turned_on": "a coded literal convention", "anchor": {"call": "weave:///t/call/inf"}},
    ]))
    filed = _close.file_observations(store, s)
    assert len(filed) == 2
    assert {o.turned_on for o in filed} == {None, "a coded literal convention"}


def test_a_crowd_of_findings_on_one_call_is_left_as_is(store):
    """Three findings on one call is ambiguous, not a clean pair: the safety-net is conservative and merges none of them,
    filing each finding that has a happened, so no finding is silently lost to an ambiguous merge."""
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    call = "weave:///t/call/crowd"
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        {"happened": "the code 'A' was returned", "turned_on": None, "anchor": {"call": call}},
        {"happened": "the code 'B' was returned", "turned_on": None, "anchor": {"call": call}},
        {"happened": "the attempt read a coded value as a label", "turned_on": "coded values", "anchor": {"call": call}},
    ]))
    filed = _close.file_observations(store, s)
    assert len(filed) == 3, "an ambiguous crowd is not merged; each half with a world-fact still files"
