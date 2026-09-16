"""The frozen model, priced.

One client serves every role — the pass, the consolidator, the examiner, the
adjudicator, the coder — and each role runs in its own context: a fresh
``complete`` call with the role's prompt as the system message and nothing
shared but the store's schemas. Independence is structural, not instructed.

Backends:

- :class:`OpenAICompatible` — any OpenAI-compatible server: a CoreWeave
  inference endpoint, W&B Inference, a local server. From the environment it
  is configured by ``$HGI_INFERENCE_BASE_URL``, ``$HGI_INFERENCE_API_KEY`` and
  ``$HGI_MODEL_ID``; an experiment (:mod:`hgi.experiment`) installs it per
  role instead.
- :class:`ClaudeCLI` — the local ``claude`` CLI, shelled out to per call and
  billed to a Claude subscription instead of an inference endpoint. Selected
  by ``$HGI_INFERENCE_BASE_URL=claude-cli://`` with ``$HGI_MODEL_ID`` naming
  the CLI's model alias, or by a :class:`hgi.experiment.ModelSpec` with
  ``provider = "claude-cli"``. A cost-offload path for the backward pass's
  teacher roles, which carry most of a run's cost; every other spec is
  unaffected.
- :class:`Stub` — a deterministic answerer used when no endpoint is
  configured. It classifies work-shape lexically, answers every lens with the
  empty finding, and attacks and adjudicates by fixed rules stated in its
  methods. It exists so the loop's mechanics run and are testable offline; it
  is not evidence that a model learned anything.

Roles resolve to backends through :func:`backend`: a role with its own
backend installed by :func:`use` gets it, every other role gets the default.
Spec § 9.6: four contexts, one model or several. Every call records its
model id; every lens and decision records the model it was priced for, and
the lint warns on a mismatch at boot.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import weave

from hgi import tracing
from hgi.roles import prompt as role_prompt

WANDB_INFERENCE = "https://api.inference.wandb.ai/v1"
"""W&B Inference: OpenAI-compatible, keyed by the W&B API key, usage attributed to ``entity/project``."""

CLAUDE_CLI_SENTINEL = "claude-cli://"
"""The ``$HGI_INFERENCE_BASE_URL`` value that selects :class:`ClaudeCLI` instead of an OpenAI-compatible endpoint."""


@dataclass
class Completion:
    text: str
    model_id: str
    call: str | None
    """The Weave call URI, joinable from ledger entries and admission stamps."""

    def json(self) -> Any:
        """Parse the completion as JSON, tolerating a fenced block around it and a model that echoes the request's ``reply`` key as a wrapper."""
        text = self.text.strip()
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if m:
            text = m.group(1).strip()
        out = json.loads(text)
        if isinstance(out, dict) and set(out) == {"reply"}:
            out = out["reply"]
        return out

    def json_or(self, default: Any) -> Any:
        """:meth:`json`, but returning ``default`` when the reply is not the JSON the caller needs — malformed JSON, or a
        reply whose top-level type is not ``default``'s. For the sites whose contract already treats a missing or unusable
        reply as empty ("empty is legal", a lens or disposition with nothing to say): a garbled endpoint reply degrades to
        the empty answer instead of crashing the pass (carry-forward item 34). The drafting sites that must *refuse* a bad
        draft keep calling :meth:`json` so the parse error still names the failing field."""
        try:
            out = self.json()
        except (json.JSONDecodeError, ValueError):
            return default
        return out if isinstance(out, type(default)) else default


class Backend:
    model_id: str

    def chat(self, messages: list[dict[str, Any]], *, json_mode: bool, tools: list[dict] | None = None) -> dict[str, Any]:
        raise NotImplementedError


class OpenAICompatible(Backend):
    """One OpenAI-compatible endpoint, one model id, deterministic by default.

    ``project`` is sent as the ``OpenAI-Project`` header, which W&B Inference
    reads as ``entity/project`` for usage attribution. ``max_retries`` covers
    the endpoint's concurrency 429s with the client's own backoff.
    """

    def __init__(self, base_url: str, api_key: str, model_id: str, *, temperature: float = 0.0,
                 project: str | None = None, max_retries: int = 5, timeout: float = 120.0,
                 reasoning_effort: str | None = None):
        from openai import OpenAI

        self.client = OpenAI(base_url=base_url, api_key=api_key, project=project, max_retries=max_retries, timeout=timeout)
        self.base_url = base_url
        self.model_id = model_id
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort

    def chat(self, messages, *, json_mode, tools=None):
        kwargs: dict[str, Any] = {"model": self.model_id, "messages": messages, "temperature": self.temperature}
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if tools:
            kwargs["tools"] = tools
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        return {"content": msg.content or "", "tool_calls": [
            {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments} for tc in (msg.tool_calls or [])
        ]}


class ClaudeCLI(Backend):
    """The local ``claude`` CLI, one clean subprocess per call, billed to a Claude subscription rather
    than an inference endpoint.

    The system message becomes ``--system-prompt`` (replacing Claude Code's own primer entirely) and
    the user message is the prompt argument. Each call runs from a fresh, empty ``tempfile.mkdtemp()``
    directory with no ``CLAUDE.md`` up its tree, an empty ``--settings``, and ``--strict-mcp-config``
    with an empty ``--mcp-config`` — so no project memory, skills, or MCP servers leak into the reply.
    ``--output-format json`` wraps the reply in an envelope; the completion text is its ``result`` field.

    This backend does not support tool-calling — the teacher roles it serves never pass ``tools`` — and
    does not act on ``json_mode``: the role prompt itself states the JSON reply shape (:data:`hgi.roles.REPLY_RULE`).

    ``effort`` (``low | medium | high | xhigh | max``, the CLI's own ``--effort`` levels) defaults to
    ``$HGI_CLAUDE_CLI_EFFORT`` or ``"low"`` — this backend serves the backward pass's teacher roles, where
    latency (measured at ~2 minutes a call on ``sonnet`` at the default effort) is the live cost, so the
    default is biased for speed; raise it per call site for a role that needs the deeper reasoning.
    ``max_budget_usd`` (``$HGI_CLAUDE_CLI_MAX_BUDGET_USD``, unset by default) is a per-call safety cap the
    CLI itself enforces (``--max-budget-usd``) — a stop against a runaway call burning the subscription's
    metered spend, not a pricing input the loop reads.
    """

    def __init__(self, model: str = "sonnet", *, claude_bin: str | None = None, timeout: float = 300.0,
                 effort: str | None = None, max_budget_usd: float | None = None):
        self.model_id = model
        self.claude_bin = claude_bin or os.environ.get("HGI_CLAUDE_CLI_BIN") or "claude"
        self.timeout = timeout
        self.effort = effort if effort is not None else os.environ.get("HGI_CLAUDE_CLI_EFFORT", "low")
        budget_env = os.environ.get("HGI_CLAUDE_CLI_MAX_BUDGET_USD")
        self.max_budget_usd = max_budget_usd if max_budget_usd is not None else (float(budget_env) if budget_env else None)
        self.last_envelope: dict[str, Any] | None = None
        """The most recent call's parsed envelope — usage, cost, latency — kept for inspection, not read by ``chat``."""

    def chat(self, messages, *, json_mode, tools=None):
        assert not tools, "ClaudeCLI does not support tool-calling"
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user = next((m["content"] for m in messages if m.get("role") == "user"), "")
        cmd = [self.claude_bin, "-p", "--system-prompt", system, "--settings", "{}", "--strict-mcp-config",
               "--mcp-config", '{"mcpServers": {}}', "--output-format", "json", "--model", self.model_id]
        if self.effort:
            cmd += ["--effort", self.effort]
        if self.max_budget_usd is not None:
            cmd += ["--max-budget-usd", str(self.max_budget_usd)]
        cmd.append(user)
        scratch = tempfile.mkdtemp(prefix="hgi-claude-cli-")
        try:
            proc = subprocess.run(cmd, cwd=scratch, capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"claude CLI timed out after {self.timeout}s: {e}") from e
        except OSError as e:
            raise RuntimeError(f"claude CLI ({self.claude_bin!r}) failed to start: {e}") from e
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"claude CLI returned an unparseable envelope (exit {proc.returncode}): "
                                f"stdout={proc.stdout[:2000]!r} stderr={proc.stderr[:2000]!r}") from e
        if proc.returncode != 0 or envelope.get("is_error"):
            raise RuntimeError(f"claude CLI failed (exit {proc.returncode}): {envelope.get('result') or proc.stderr or envelope}")
        if "result" not in envelope:
            raise RuntimeError(f"claude CLI envelope carries no `result` field: {envelope}")
        self.last_envelope = envelope
        return {"content": envelope["result"], "tool_calls": []}


class Stub(Backend):
    """Deterministic answers, keyed on the role in the system prompt. See :mod:`hgi.stub` for the rules."""

    model_id = "stub"

    def chat(self, messages, *, json_mode, tools=None):
        from hgi.stub import answer

        return {"content": answer(messages, tools), "tool_calls": []}


def wandb_api_key() -> str | None:
    """The W&B API key the way ``wandb`` itself finds it: ``$WANDB_API_KEY``, then the netrc entry ``wandb login`` wrote."""
    key = os.environ.get("WANDB_API_KEY")
    if key:
        return key
    try:
        import wandb

        return wandb.Api().api_key
    except Exception:
        return None


def from_env() -> Backend:
    """The backend the environment names: the endpoint of ``$HGI_INFERENCE_BASE_URL`` and ``$HGI_MODEL_ID``,
    the local ``claude`` CLI when the base url is :data:`CLAUDE_CLI_SENTINEL`, else the stub."""
    base_url = os.environ.get("HGI_INFERENCE_BASE_URL")
    model = os.environ.get("HGI_MODEL_ID")
    if not (base_url and model):
        return Stub()
    if base_url == CLAUDE_CLI_SENTINEL:
        return ClaudeCLI(model=model)
    key = os.environ.get("HGI_INFERENCE_API_KEY") or (wandb_api_key() if base_url.startswith(WANDB_INFERENCE) else None) or "none"
    project = tracing.project_name() if base_url.startswith(WANDB_INFERENCE) else None
    return OpenAICompatible(base_url, key, model, project=project)


_default: Backend | None = None
_roles: dict[str, Backend] = {}


def backend(role: str | None = None) -> Backend:
    """The backend serving ``role``: its own when one is installed, else the default."""
    global _default
    if role is not None and role in _roles:
        return _roles[role]
    if _default is None:
        _default = from_env()
    return _default


def use(b: Backend | None, role: str | None = None) -> None:
    """Install ``b`` as the default backend, or as ``role``'s own; ``None`` uninstalls (the default then re-reads the environment)."""
    global _default
    if role is None:
        _default = b
    elif b is None:
        _roles.pop(role, None)
    else:
        _roles[role] = b


def reset() -> None:
    """Forget every installed backend."""
    global _default
    _default = None
    _roles.clear()


@contextmanager
def override(role: str, b: Backend) -> Iterator[None]:
    """Serve ``role`` from ``b`` for the duration of the block, whatever is installed."""
    previous = _roles.get(role)
    _roles[role] = b
    try:
        yield
    finally:
        if previous is None:
            _roles.pop(role, None)
        else:
            _roles[role] = previous


def model_id(role: str | None = None) -> str:
    return backend(role).model_id


def roster() -> dict[str, str]:
    """Every role's model id — the default's, unless the role has its own backend."""
    from hgi.roles import ROLES

    return {role: model_id(role) for role in ROLES}


@weave.op(name="hgi.complete")
def _complete(role: str, system: str, user: str, json_mode: bool) -> dict[str, Any]:
    return backend(role).chat([{"role": "system", "system_role": role, "content": system}, {"role": "user", "content": user}], json_mode=json_mode)


def complete(role: str, user: str, *, json_mode: bool = True, session: str | None = None, pass_: int | None = None,
             records_in_context: list[str] | None = None) -> Completion:
    """One fresh context for ``role``: its prompt file as the system message, ``user`` as the whole conversation."""
    system = role_prompt(role)
    with tracing.attributes(session=session, pass_=pass_, role=role, records_in_context=records_in_context):
        result, call = _complete.call(role, system, user, json_mode, __should_raise=True)  # an endpoint error is raised, never a None reply
    completion = Completion(text=result["content"], model_id=model_id(role), call=tracing.call_uri(call))
    log_reply(role, user, completion)
    return completion


REPLY_LOG = "HGI_REPLY_LOG"
"""A directory; when set, every role request and its raw reply land there as one JSON file each, numbered in call order."""


def log_reply(role: str, user: str, completion: Completion) -> None:
    where = os.environ.get(REPLY_LOG)
    if not where:
        return
    from pathlib import Path

    directory = Path(where)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        name = json.loads(user).get("request", "free")
    except (json.JSONDecodeError, AttributeError, TypeError):
        name = "free"
    n = len(list(directory.glob("*.json"))) + 1
    (directory / f"{n:03d}-{role}-{name}.json").write_text(json.dumps(
        {"role": role, "request": name, "model_id": completion.model_id, "call": completion.call, "user": user, "reply": completion.text},
        indent=2, ensure_ascii=False) + "\n")


def chat_with_tools(role: str, messages: list[dict[str, Any]], tools: list[dict], *, session: str | None = None,
                    pass_: int | None = None, records_in_context: list[str] | None = None) -> tuple[dict[str, Any], str | None]:
    """One turn of a tool-using conversation for the agent under test; returns (message, call uri)."""
    with tracing.attributes(session=session, pass_=pass_, role=role, records_in_context=records_in_context):
        result, call = _turn.call(role, messages, tools, __should_raise=True)
    return result, tracing.call_uri(call)


@weave.op(name="hgi.turn")
def _turn(role: str, messages: list[dict[str, Any]], tools: list[dict]) -> dict[str, Any]:
    return backend(role).chat(messages, json_mode=False, tools=tools)
