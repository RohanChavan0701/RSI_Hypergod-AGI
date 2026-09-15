"""A close files an observation per L-0004 finding that has an anchor and a ``noticed``; a finding a reply left without one is
skipped, not raised on — the stream run's strict arm died at pass 7 on a reply that dropped the field."""

from hgi import boot as _boot
from hgi import close as _close
from hgi.types import Consulted, LensAnswer
from tests.conftest import adjudicated_entry, adjudicator, draft
from tests.test_slice3 import FAULTED, _session

# A passed row that recovered from a non-transient convention (a 401 the /secure route guards behind a token): L-0009's
# class — the pass learned it, self-corrected on it, and the row scored 1.0, so L-0004's failed-row filter never sees it.
RECOVERED = {"task": "list_users", "error": None, "applied": [], "call": "weave:///t/call/recovered",
             "tool_errors": [{"message": "GET /secure/users failed", "cause": "HTTP 401 Unauthorized: routes under /secure require ?token=", "transient": False}],
             "scores": {"task_pass_rate": {"value": 1.0}}}
# A passed row whose only fault was a 502 that cleared on retry — transient, non-causal: the decoy L-0009 must reject.
TRANSIENT_RECOVERED = {"task": "sum_numbers", "error": None, "applied": [], "call": "weave:///t/call/transient",
                       "tool_errors": [{"cause": "HTTP 502 Bad Gateway from /numbers", "transient": True}],
                       "scores": {"task_pass_rate": {"value": 1.0}}}
# A passed row whose only fault was a call-budget refusal (item 63 part 2): non-transient but economy telemetry, not a
# convention the pass recovered from — L-0009 must not elicit an observation from it, or budget becomes the axis's only
# cross-session recurrence (the qwen-attached run minted four such on passing rows).
BUDGET_REFUSED = {"task": "regex_06", "error": None, "applied": [], "call": "weave:///t/call/budget",
                  "tool_errors": [{"message": "shell call refused", "cause": "call budget of 2 exceeded at call 3", "transient": False}],
                  "scores": {"task_pass_rate": {"value": 1.0}}}
# A passed row that hit the budget *and* a genuine non-transient 401: the real recovery still files; budget does not suppress it.
BUDGET_AND_REAL = {"task": "list_users", "error": None, "applied": [], "call": "weave:///t/call/mixed",
                   "tool_errors": [{"message": "shell call refused", "cause": "call budget of 2 exceeded at call 3", "transient": False},
                                   {"message": "GET /secure/users failed", "cause": "HTTP 401 Unauthorized: routes under /secure require ?token=", "transient": False}],
                   "scores": {"task_pass_rate": {"value": 1.0}}}
# A failed row whose error matched no hook (nothing consulted): the off-map signal L-0010 turns into a missing-rule noticing.
OFF_MAP = {"task": "novel_shape", "error": {"message": "unmatched failure", "cause": None}, "applied": [], "call": "weave:///t/call/offmap",
           "tool_errors": [], "scores": {"task_pass_rate": {"value": 0.0}}}


def _admit(store, name="D-0001"):
    d = draft(store, name)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_a_finding_with_no_noticed_is_not_filed_and_does_not_stop_the_close(store):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        {"happened": "the retry was not attempted", "anchor": {"path": "suite/tools.py:54"}},
        {"anchor": {"path": "suite/tools.py:54"}},
        {"happened": "  ", "anchor": {"path": "suite/tools.py:54"}},
        {"happened": "no anchor, not filed either"},
    ]))
    filed = _close.file_observations(store, s)
    assert [o.happened for o in filed] == ["the retry was not attempted"]
    assert s.observations_filed == [filed[0].name]


def test_l0009_files_a_recovered_nontransient_miss_from_a_passed_row(store):
    s = _session(store, 1, [RECOVERED], {"task_pass_rate": 1.0})
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    filed = _close.file_observations(store, s)
    # the passed row's non-transient recovery files as one observation, anchored on the row's call
    assert len(filed) == 1 and filed[0].anchor.call == "weave:///t/call/recovered"
    assert "401" in filed[0].happened or "token" in filed[0].happened
    assert s.observations_filed == [filed[0].name]
    assert [a.lens for a in s.lens_answers if a.findings] == ["L-0009"], "L-0004 sees no failed row; only L-0009 fires"


def test_l0009_files_nothing_from_a_passed_row_whose_only_fault_was_transient(store):
    s = _session(store, 1, [TRANSIENT_RECOVERED], {"task_pass_rate": 1.0})
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    # a 502 that cleared on retry is loud but non-causal — L-0009 is walked over no row and nothing files
    assert _close.file_observations(store, s) == []


def test_l0009_files_nothing_from_a_passed_row_whose_only_fault_was_a_budget_refusal(store):
    # item 63 part 2: a budget refusal is economy telemetry (it feeds tool_budget_respected), not a convention the pass
    # recovered from — so it stays off the observation axis and does not become the only cross-session recurrence.
    assert not _close._recovered_nontransient(BUDGET_REFUSED) and _close._is_budget_refusal(BUDGET_REFUSED["tool_errors"][0])
    s = _session(store, 1, [BUDGET_REFUSED], {"task_pass_rate": 1.0})
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    assert _close.file_observations(store, s) == []


def test_l0009_still_files_a_real_recovery_that_also_hit_the_budget(store):
    # the budget refusal does not suppress a genuine non-transient convention the pass recovered from on the same row
    assert _close._recovered_nontransient(BUDGET_AND_REAL)
    s = _session(store, 1, [BUDGET_AND_REAL], {"task_pass_rate": 1.0})
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    filed = _close.file_observations(store, s)
    assert len(filed) == 1 and filed[0].anchor.call == "weave:///t/call/mixed"


def test_l0010_files_a_missing_rule_noticing_on_an_off_map_session(store):
    s = _session(store, 1, [OFF_MAP], {"task_pass_rate": 0.0})  # nothing consulted, the work failed: off-map
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    filed = _close.file_observations(store, s)
    # the off-map condition files as one observation, anchored on the failed row's call
    assert len(filed) == 1 and filed[0].anchor.call == "weave:///t/call/offmap"
    assert "no hook" in filed[0].happened or "no rule" in filed[0].happened
    assert [a.lens for a in s.lens_answers if a.findings] == ["L-0010"], "an unmatched failure, nothing consulted — only L-0010 fires"


def test_l0010_files_nothing_when_the_pass_consulted_a_record(store):
    d = _admit(store)
    s = _session(store, 1, [OFF_MAP], {"task_pass_rate": 0.0})
    s.consulted = [Consulted(record=d.id)]  # a hook fired and a record was consulted — not off-map
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    assert _close.file_observations(store, s) == []
