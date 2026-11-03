import json
from pathlib import Path

import pytest

from suite.security_replay import summarize


def hard_report():
    path = Path(__file__).resolve().parents[1] / "experiments" / "security-hard-01.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_replay_reproduces_paired_result():
    summary = summarize(hard_report())
    assert summary["baseline_injected"]["unauthorized_attempts"] == 2
    assert summary["defense_injected"]["unauthorized_attempts"] == 0
    assert summary["defense_injected"]["completed"] == 2


def test_replay_rejects_forged_state():
    report = hard_report()
    report["rows"][0]["trace"][0]["approved"] = True
    with pytest.raises(ValueError, match="simulator replay"):
        summarize(report)


def test_replay_rejects_missing_arm():
    report = hard_report()
    report["rows"].pop()
    with pytest.raises(ValueError, match="Missing or unmatched"):
        summarize(report)
