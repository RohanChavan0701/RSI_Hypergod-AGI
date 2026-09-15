"""The loop tolerates bad or missing data from its APIs — the model endpoint and Weave — without crashing an arm
unrecoverably (carry-forward item 34, and the design directive it grew into).

Three layers are covered:
  A. a None/malformed Weave evaluation summary is rebuilt from the per-row scores that survive a flush timeout, or read
     as unevaluable — never an AttributeError (:func:`hgi.evaluate.facts_from`, :func:`hgi.evaluate.summary_from_rows`);
  B. a garbled (non-JSON, or wrong-typed) role reply at an "empty is legal" site degrades to the empty answer
     (:meth:`hgi.model.Completion.json_or`);
  C. a pass that keeps failing after its retries finalizes the arm gracefully — completed passes preserved, the failure
     recorded, no exception escaping :func:`hgi.experiment.run_arm`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from hgi import evaluate as _evaluate
from hgi import experiment as _experiment
from hgi import model as _model

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"


@pytest.fixture(autouse=True)
def clean_backends():
    _model.reset()
    yield
    _model.reset()


# --- Layer A: the Weave summary ------------------------------------------------------------------

def test_facts_from_reads_a_none_summary_as_unevaluable_never_crashing():
    facts = _evaluate.facts_from(None, datetime(2026, 9, 15), "call:x")
    assert facts["task_pass_rate"].value is None and facts["task_pass_rate"].unevaluable
    # a malformed (non-dict) summary is the same graceful outcome
    assert _evaluate.facts_from("garbage", datetime(2026, 9, 15), None)["task_pass_rate"].value is None  # type: ignore[arg-type]


def test_summary_from_rows_rebuilds_the_means_from_the_surviving_row_scores():
    row_scores = {
        "q1": {"task_pass_rate": {"value": 1.0}, "output_schema_valid": {"value": 1.0}},
        "q2": {"task_pass_rate": {"value": 0.0}, "output_schema_valid": {"value": None, "unevaluable": "x"}},
    }
    summary = _evaluate.summary_from_rows(row_scores)
    assert summary["task_pass_rate"]["value"]["mean"] == 0.5, "mean over the two evaluable rows"
    assert summary["output_schema_valid"]["value"]["mean"] == 1.0, "the None row is dropped, not counted as zero"
    # and this rebuilt summary reads straight back through facts_from
    facts = _evaluate.facts_from(summary, datetime(2026, 9, 15), None)
    assert facts["task_pass_rate"].value == 0.5


def test_summary_from_rows_is_unevaluable_when_no_row_scored():
    summary = _evaluate.summary_from_rows({})
    assert summary["task_pass_rate"]["value"]["mean"] is None
    assert _evaluate.facts_from(summary, datetime(2026, 9, 15), None)["task_pass_rate"].value is None


# --- Layer B: a garbled role reply ---------------------------------------------------------------

def test_json_or_returns_the_default_on_bad_data_and_the_reply_on_good():
    assert _model.Completion(text="not json at all", model_id="m", call=None).json_or({}) == {}
    assert _model.Completion(text="[1, 2, 3]", model_id="m", call=None).json_or({}) == {}, "valid JSON of the wrong type is the default too"
    assert _model.Completion(text='{"answer": "ok", "findings": []}', model_id="m", call=None).json_or({}) == {"answer": "ok", "findings": []}
    # the fenced/echoed-wrapper tolerance of json() still applies through json_or
    assert _model.Completion(text='```json\n{"reply": {"terms": ["t"]}}\n```', model_id="m", call=None).json_or({}) == {"terms": ["t"]}


# --- Layer C: a pass that keeps failing does not abort the arm ------------------------------------

def test_a_pass_that_keeps_failing_stops_the_arm_gracefully(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    real_run = _evaluate.run
    calls = {"n": 0}

    def boom(store, session):
        if session.pass_ == 2:  # pass 1 succeeds and is preserved; pass 2 fails every time
            calls["n"] += 1
            raise RuntimeError("simulated endpoint fault")
        return real_run(store, session)

    monkeypatch.setattr(_evaluate, "run", boom)
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")

    record = _experiment.run_arm(exp, "attached", tmp_path, commit=False)  # must NOT raise

    where = tmp_path / "smoke" / "attached"
    assert (where / "arm.json").exists() and record["finished_at"], "the arm finalized: arm.json is written"
    assert "error" in record and "pass 2" in record["error"], "the failure is recorded, not swallowed silently"
    assert record["sessions"] == ["S-0001"] and sorted(record["curve"]) == [1], "the one completed pass is preserved"
    assert calls["n"] == 3, "the failing evaluate step was retried to exhaustion (1 + 2) before the arm gave up"
