"""The model tool-loop gives one bounded repair turn on a non-JSON final reply, so the task's world-fact
surfaces instead of the harness format error masking it; a repair that still fails splits the symptom."""

from __future__ import annotations

import tempfile

import suite as _suite
from suite.agent import MAX_FINAL_REPAIRS, Agent
from suite.tasks import SuiteSpec, build
from suite.tools import Tools


def tmp_dir():
    return tempfile.mkdtemp(prefix="hgi-repair-")


def test_a_non_json_final_reply_gets_one_repair_turn_and_the_real_result_surfaces(store):
    from hgi import model as _model

    class ProseThenJSON(_model.Backend):
        """Emits a prose final reply first (as the actor does after a budget refuses a call), then, given the
        repair turn back, states the world-fact as one JSON object."""

        model_id = "prose-then-json"

        def __init__(self):
            self.seen: list[list[dict]] = []

        def chat(self, messages, *, json_mode, tools=None):
            self.seen.append(messages)
            if len(self.seen) == 1:
                return {"content": "I could not finish because the shell budget refused my last call.", "tool_calls": []}
            return {"content": '{"result": {"answer": 42, "unit": "n"}, "error": null, "applied": []}', "tool_calls": []}

    backend = ProseThenJSON()
    world = build(SuiteSpec())
    token = _suite.use(world)
    _model.use(backend, role="pass")
    try:
        agent = Agent(policy="model", records=[])
        out = agent._model("genesis/schema_answer", "Return it.", {}, Tools(task="genesis/schema_answer", workdir=tmp_dir()))
    finally:
        _model.use(None, role="pass")
        _suite.reset(token)
    assert out["error"] is None and out["result"] == {"answer": 42, "unit": "n"}, "the repaired reply's real result surfaces"
    assert out["turns"] == 2, "the wasted prose turn still counts; the model recovers on the repair turn"
    assert len(backend.seen) == 2, "the endpoint took a second request rather than the row failing outright"
    repair = backend.seen[1]
    assert repair[-2]["role"] == "assistant" and "shell budget" in repair[-2]["content"], "the raw prose is replayed as an assistant turn"
    assert repair[-1]["role"] == "user" and "one JSON object" in repair[-1]["content"], "a corrective user turn asks for the world-fact as JSON"


def test_a_final_reply_that_never_becomes_json_ends_with_the_split_symptom_and_does_not_loop(store):
    from hgi import model as _model

    class AlwaysProse(_model.Backend):
        model_id = "always-prose"

        def __init__(self):
            self.calls = 0

        def chat(self, messages, *, json_mode, tools=None):
            self.calls += 1
            return {"content": "still cannot produce JSON, the budget refused the call.", "tool_calls": []}

    backend = AlwaysProse()
    world = build(SuiteSpec())
    token = _suite.use(world)
    _model.use(backend, role="pass")
    try:
        out = Agent(policy="model", records=[])._model("genesis/schema_answer", "Return it.", {}, Tools(task="genesis/schema_answer", workdir=tmp_dir()))
    finally:
        _model.use(None, role="pass")
        _suite.reset(token)
    assert out["error"]["message"] == "final reply was not JSON", "the message text downstream matches on is preserved"
    assert out["error"]["cause"] == "still not JSON after a repair turn", "the split symptom marks a format failure that survived a repair"
    assert backend.calls == 1 + MAX_FINAL_REPAIRS, "one first shot plus exactly one bounded repair — it does not loop"
    assert out["turns"] == 1 + MAX_FINAL_REPAIRS


def test_a_non_dict_json_final_reply_splits_its_own_symptom(store):
    from hgi import model as _model

    class AlwaysList(_model.Backend):
        """Valid JSON, but a list, not the required object — on both the first shot and the repair turn."""

        model_id = "always-list"

        def chat(self, messages, *, json_mode, tools=None):
            return {"content": "[1, 2, 3]", "tool_calls": []}

    world = build(SuiteSpec())
    token = _suite.use(world)
    _model.use(AlwaysList(), role="pass")
    try:
        out = Agent(policy="model", records=[])._model("genesis/schema_answer", "Return it.", {}, Tools(task="genesis/schema_answer", workdir=tmp_dir()))
    finally:
        _model.use(None, role="pass")
        _suite.reset(token)
    assert out["error"]["message"] == "final reply was not a JSON object", "the message text is preserved"
    assert out["error"]["cause"] == "still not a JSON object after a repair turn", "its own split symptom, distinct from the not-JSON one"
