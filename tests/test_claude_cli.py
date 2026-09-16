"""The ``claude`` CLI backend: a teacher role's calls shelled out to a subscription-billed local CLI
instead of an inference endpoint. No test here calls the real CLI — ``subprocess.run`` is mocked."""

from __future__ import annotations

import json
import subprocess

import pytest

from hgi import model as _model


def envelope(result: str = "ok", *, is_error: bool = False, **extra) -> str:
    return json.dumps({"type": "result", "subtype": "success", "is_error": is_error, "result": result,
                        "usage": {"input_tokens": 12, "output_tokens": 3}, "duration_ms": 456, **extra})


def _run(monkeypatch, *, returncode: int = 0, stdout: str = "", stderr: str = "", capture: dict | None = None):
    """Stand in for ``subprocess.run``: records the built command and cwd (and whether it is a fresh, empty
    directory with no ``CLAUDE.md`` up its tree, checked before the real call would clean it up), returns
    a canned CompletedProcess."""
    from pathlib import Path

    def fake_run(cmd, *, cwd, capture_output, text, timeout):
        assert capture_output and text
        if capture is not None:
            capture["cmd"] = cmd
            capture["cwd"] = cwd
            capture["timeout"] = timeout
            capture["cwd_empty"] = list(Path(cwd).iterdir()) == []
            capture["no_claude_md_up_the_tree"] = not any((p / "CLAUDE.md").exists() for p in [Path(cwd), *Path(cwd).parents])
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(_model.subprocess, "run", fake_run)


MESSAGES = [{"role": "system", "content": "you are the consolidator"}, {"role": "user", "content": '{"request": "nominate"}'}]


def test_the_command_carries_system_prompt_and_json_output_format(monkeypatch):
    capture: dict = {}
    _run(monkeypatch, stdout=envelope("{}"), capture=capture)
    backend = _model.ClaudeCLI(model="sonnet", claude_bin="claude")
    backend.chat(MESSAGES, json_mode=True)
    cmd = capture["cmd"]
    assert cmd[0] == "claude"
    assert cmd[cmd.index("--system-prompt") + 1] == "you are the consolidator"
    assert cmd[-1] == '{"request": "nominate"}'  # the user message is the trailing prompt argument
    assert "--output-format" in cmd and cmd[cmd.index("--output-format") + 1] == "json"
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "sonnet"
    assert "--strict-mcp-config" in cmd
    # a fresh, empty scratch directory with no CLAUDE.md up its tree — no primer, memory, or skill discovery
    assert capture["cwd_empty"] and capture["no_claude_md_up_the_tree"]


def test_effort_defaults_to_low_and_is_configurable_by_the_constructor(monkeypatch):
    capture: dict = {}
    _run(monkeypatch, stdout=envelope("{}"), capture=capture)
    _model.ClaudeCLI(model="sonnet").chat(MESSAGES, json_mode=True)
    cmd = capture["cmd"]
    assert cmd[cmd.index("--effort") + 1] == "low", "the teacher's latency is the live cost; the default is biased for speed"

    _model.ClaudeCLI(model="sonnet", effort="high").chat(MESSAGES, json_mode=True)
    assert capture["cmd"][capture["cmd"].index("--effort") + 1] == "high"


def test_effort_defaults_from_the_environment(monkeypatch):
    monkeypatch.setenv("HGI_CLAUDE_CLI_EFFORT", "medium")
    capture: dict = {}
    _run(monkeypatch, stdout=envelope("{}"), capture=capture)
    _model.ClaudeCLI(model="sonnet").chat(MESSAGES, json_mode=True)
    cmd = capture["cmd"]
    assert cmd[cmd.index("--effort") + 1] == "medium"


def test_max_budget_usd_is_off_by_default_and_settable_via_env_or_constructor(monkeypatch):
    capture: dict = {}
    _run(monkeypatch, stdout=envelope("{}"), capture=capture)
    _model.ClaudeCLI(model="sonnet").chat(MESSAGES, json_mode=True)
    assert "--max-budget-usd" not in capture["cmd"], "no cap unless one is named"

    monkeypatch.setenv("HGI_CLAUDE_CLI_MAX_BUDGET_USD", "0.5")
    _model.ClaudeCLI(model="sonnet").chat(MESSAGES, json_mode=True)
    cmd = capture["cmd"]
    assert cmd[cmd.index("--max-budget-usd") + 1] == "0.5"

    _model.ClaudeCLI(model="sonnet", max_budget_usd=2.0).chat(MESSAGES, json_mode=True)
    cmd = capture["cmd"]
    assert cmd[cmd.index("--max-budget-usd") + 1] == "2.0", "an explicit constructor value wins over the environment"


def test_a_well_formed_envelope_parses_to_its_result_field(monkeypatch):
    _run(monkeypatch, stdout=envelope("the consolidator's sketch"))
    backend = _model.ClaudeCLI(model="sonnet")
    out = backend.chat(MESSAGES, json_mode=True)
    assert out == {"content": "the consolidator's sketch", "tool_calls": []}
    assert backend.last_envelope["usage"]["input_tokens"] == 12


def test_a_nonzero_exit_raises(monkeypatch):
    _run(monkeypatch, returncode=1, stdout=envelope("Failed to authenticate: OAuth session expired", is_error=True), stderr="")
    backend = _model.ClaudeCLI(model="sonnet")
    with pytest.raises(RuntimeError, match="OAuth session expired"):
        backend.chat(MESSAGES, json_mode=True)


def test_an_unparseable_envelope_raises_naming_stderr(monkeypatch):
    _run(monkeypatch, returncode=0, stdout="not json", stderr="a warning on stderr")
    backend = _model.ClaudeCLI(model="sonnet")
    with pytest.raises(RuntimeError, match="a warning on stderr"):
        backend.chat(MESSAGES, json_mode=True)


def test_an_envelope_with_no_result_field_raises(monkeypatch):
    _run(monkeypatch, stdout=json.dumps({"type": "result", "is_error": False}))
    backend = _model.ClaudeCLI(model="sonnet")
    with pytest.raises(RuntimeError, match="no `result` field"):
        backend.chat(MESSAGES, json_mode=True)


def test_tools_are_not_supported():
    backend = _model.ClaudeCLI(model="sonnet")
    with pytest.raises(AssertionError):
        backend.chat(MESSAGES, json_mode=True, tools=[{"name": "shell"}])


def test_from_env_selects_the_cli_on_the_sentinel_base_url(monkeypatch):
    monkeypatch.setenv("HGI_INFERENCE_BASE_URL", _model.CLAUDE_CLI_SENTINEL)
    monkeypatch.setenv("HGI_MODEL_ID", "opus")
    monkeypatch.delenv("HGI_INFERENCE_API_KEY", raising=False)
    backend = _model.from_env()
    assert isinstance(backend, _model.ClaudeCLI) and backend.model_id == "opus"


def test_from_env_leaves_every_other_base_url_on_the_openai_compatible_path(monkeypatch):
    monkeypatch.setenv("HGI_INFERENCE_BASE_URL", "https://endpoint.example/v1")
    monkeypatch.setenv("HGI_MODEL_ID", "some-model")
    monkeypatch.setenv("HGI_INFERENCE_API_KEY", "k")
    backend = _model.from_env()
    assert isinstance(backend, _model.OpenAICompatible)


def test_model_spec_routes_to_the_cli_by_provider_and_is_additive(monkeypatch):
    from hgi.experiment import ModelSpec

    cli_spec = ModelSpec(id="sonnet", provider="claude-cli")
    assert isinstance(cli_spec.backend(), _model.ClaudeCLI)

    sentinel_spec = ModelSpec(id="opus", base_url=_model.CLAUDE_CLI_SENTINEL)
    assert isinstance(sentinel_spec.backend(), _model.ClaudeCLI)

    stub_spec = ModelSpec(id="stub", stub=True)
    assert isinstance(stub_spec.backend(), _model.Stub)  # every existing (non-opt-in) spec is unaffected
