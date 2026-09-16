# /// script
# requires-python = ">=3.14"
# dependencies = ["marimo", "hgi"]
# ///
"""Agent anatomy — what each agent receives, derived from the code that assembles it.

Every prompt in the loop is built by real functions in this repo; this notebook
calls those functions and lays their output out layer by layer, so the reader can
*see* — and critique — exactly how information is passed, handled, and transformed.

Two assembly seams, two lanes:

- **The task agent** (``suite/agent.py::Agent.compose``) — the frozen actor doing
  a suite task, conditioned on the constitution and the consultation plan the boot
  selected. Its two messages are pulled straight from ``Agent.compose``.
- **The backward-pass roles** (``hgi/contract.py`` builders → ``hgi/roles``) — the
  pass, coder, consolidator, examiner, adjudicator. For each request the notebook
  runs the same builder the loop runs (against a copy of the store, no model call)
  and splits its JSON into the fixed instruction, the entry/world information, the
  store material consulted, and the reply contract.

Nothing is re-implemented: the layers you see are the strings the model would see.
Run with ``uv run marimo edit agent_anatomy.py`` (or ``marimo run`` to read only).
"""

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    import os
    import shutil
    import tempfile
    import warnings
    from pathlib import Path
    from types import SimpleNamespace

    import marimo as mo

    warnings.filterwarnings("ignore")
    _ = os.environ.setdefault("WANDB_MODE", "disabled")  # keep weave quiet; every read here is offline
    return Path, SimpleNamespace, json, mo, shutil, tempfile


@app.cell
def _():
    # The real assembly code — imported, never copied.
    import suite
    from hgi import contract, registry, roles
    from hgi.evaluate import context_records
    from hgi.store import Store
    from suite.agent import Agent
    from suite.tools import Tools
    return (
        Agent,
        Store,
        Tools,
        context_records,
        contract,
        registry,
        roles,
        suite,
    )


@app.cell
def _(mo):
    # ---- the provenance vocabulary: how we tag each layer of a prompt ----------------
    # Every category below is a claim about where a piece of the prompt comes from and
    # what kind of thing it is. The colours carry through both lanes, so the same kind
    # of information reads the same everywhere.
    KIND = {
        "fixed":     ("#64748b", "Fixed instruction", "the role's own prompt — identical on every call of this role"),
        "entry":     ("#2563eb", "Entry form",        "the task as presented to the agent (the hidden test withheld)"),
        "world":     ("#0d9488", "Run evidence",      "what actually happened this run — rows, scores, observations"),
        "store":     ("#7c3aed", "Store — consulted",  "decisions / records the store put in context"),
        "directive": ("#d97706", "Directive / vocab", "standing articles, registered vocabulary, bars, budgets"),
        "lens":      ("#db2777", "Lens",              "the interrogating angle: question, counterfactual, product"),
        "tools":     ("#059669", "Tools",             "the capabilities handed to the agent"),
        "contract":  ("#dc2626", "Output contract",   "the exact reply shape the answer must take"),
        "meta":      ("#6b7280", "Meta",              "the request name / routing"),
    }

    def legend():
        rows = "".join(
            f'<div style="display:flex;align-items:center;gap:.5rem;margin:.15rem 0;">'
            f'<span style="width:14px;height:14px;border-radius:3px;background:{c};display:inline-block;flex:0 0 auto;"></span>'
            f'<b style="color:{c};">{label}</b>'
            f'<span style="opacity:.75;">— {desc}</span></div>'
            for _, (c, label, desc) in KIND.items()
        )
        return mo.Html(
            f'<div style="border:1px solid #8883;border-radius:8px;padding:.6rem .8rem;font-size:.85rem;">'
            f'<div style="font-weight:600;margin-bottom:.3rem;">Legend — the layers a prompt is made of</div>{rows}</div>'
        )
    return KIND, legend


@app.cell
def _(KIND, json, mo):
    # ---- HTML rendering helpers ------------------------------------------------------
    import html as _html

    def _esc(s):
        return _html.escape(str(s))

    def code_block(text, limit=2000):
        """A monospace block; anything past ``limit`` folds into a <details> so the page stays scannable."""
        text = text if isinstance(text, str) else json.dumps(text, indent=2, default=str, ensure_ascii=False)
        pre = ('background:#8881;border-radius:6px;padding:.5rem .6rem;overflow:auto;'
               'font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.8rem;'
               'white-space:pre-wrap;word-break:break-word;margin:.35rem 0 0;')
        if len(text) <= limit:
            return f'<pre style="{pre}">{_esc(text)}</pre>'
        head, rest = text[:limit], text[limit:]
        return (f'<pre style="{pre}">{_esc(head)}</pre>'
                f'<details style="margin-top:.25rem;"><summary style="cursor:pointer;opacity:.7;font-size:.8rem;">'
                f'… show {len(rest):,} more characters</summary><pre style="{pre}">{_esc(rest)}</pre></details>')

    def segment(kind, title, subtitle, body_html, source=None):
        """One labelled, colour-accented layer of a prompt."""
        color, klabel, _ = KIND[kind]
        chip = (f'<span style="background:{color};color:#fff;border-radius:4px;padding:.05rem .4rem;'
                f'font-size:.68rem;font-weight:700;letter-spacing:.02em;white-space:nowrap;">{klabel.upper()}</span>')
        src = (f'<code style="opacity:.6;font-size:.72rem;">{_esc(source)}</code>' if source else "")
        sub = f'<div style="opacity:.7;font-size:.8rem;margin:.15rem 0 .1rem;">{_esc(subtitle)}</div>' if subtitle else ""
        return (
            f'<div style="border-left:4px solid {color};background:{color}12;border-radius:0 8px 8px 0;'
            f'padding:.5rem .75rem;margin:.5rem 0;">'
            f'<div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;justify-content:space-between;">'
            f'<div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;"><b>{_esc(title)}</b>{chip}</div>{src}</div>'
            f'{sub}{body_html}</div>'
        )

    def stack(layers):
        """A compact at-a-glance strip: the ordered layers of THIS message, ``(name, kind)`` each, coloured by kind."""
        bars = "".join(
            f'<div style="display:flex;align-items:center;gap:.5rem;">'
            f'<span style="width:10px;height:10px;border-radius:2px;background:{KIND[k][0]};flex:0 0 auto;"></span>'
            f'<span style="font-size:.8rem;"><b>{_esc(name)}</b> '
            f'<span style="opacity:.6;">· {KIND[k][1]}</span></span></div>'
            for name, k in layers
        )
        return (f'<div style="border:1px dashed #8884;border-radius:8px;padding:.5rem .75rem;margin:.4rem 0;'
                f'display:flex;flex-direction:column;gap:.2rem;">{bars}</div>')

    def message_card(who, layers_html):
        """A framed chat message (system / user) holding its layers."""
        return mo.Html(
            f'<div style="border:1px solid #8883;border-radius:10px;padding:.4rem .7rem .7rem;margin:.5rem 0;">'
            f'<div style="font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;opacity:.8;'
            f'border-bottom:1px solid #8882;padding-bottom:.25rem;margin-bottom:.2rem;">{_esc(who)} message</div>'
            f'{layers_html}</div>'
        )
    return code_block, message_card, segment, stack


@app.cell
def _(Path):
    # ---- discover the stores on disk that can back the notebook ----------------------
    def find_stores(root="."):
        root = Path(root)
        found = []
        for decisions in root.rglob("decisions"):
            store_dir = decisions.parent
            if (store_dir / "registry").exists() or (store_dir / "sessions").exists():
                found.append(store_dir)
        uniq = sorted({s.resolve() for s in found}, key=lambda p: (p.name != "store", len(p.parts), str(p)))
        rel = []
        for p in uniq:
            try:
                rel.append(str(p.relative_to(root.resolve())))
            except ValueError:
                rel.append(str(p))
        return rel or ["store"]
    return (find_stores,)


@app.cell
def _(find_stores, mo):
    _stores = find_stores()
    store_dd = mo.ui.dropdown(
        options=_stores,
        value="store" if "store" in _stores else _stores[0],
        label="**Decision store** to read (the world the agents are conditioned on)",
    )
    store_dd
    return (store_dd,)


@app.cell
def _(Store, registry, store_dd):
    # ---- load the selected store (offline filesystem read; registry made current) ----
    from pathlib import Path as _P

    _root = _P(store_dd.value)
    _reg = registry.load(_root)
    registry.use(_reg)  # process-global, last-wins; every builder reads store.registry off the Store
    store = Store(_root, registry=_reg)
    return (store,)


@app.cell
def _(mo, store, store_dd):
    _n = lambda kind: len(store.all(kind))
    mo.md(
        f"""
    # Agent anatomy
    ### what each agent receives — derived from the code that assembles it

    Reading **`{store_dd.value}`** · {_n('decision')} decisions · {_n('session')} sessions · {_n('observation')} observations.

    Every layer below is produced by the repo's own assembly functions —
    `suite/agent.py::Agent.compose` and `hgi/contract.py`'s builders → `hgi/roles`.
    Nothing here is re-typed by hand: it is the string the model would see, taken apart
    so you can judge each part — *is this the right lens? the right information? the right step?*
    """
    )
    return


@app.cell
def _(legend):
    legend()
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ---
    ## Lane A — the task agent
    The frozen actor running one suite task. Assembled by **`Agent.compose(task, prompt, schema, budgets)`**
    (`suite/agent.py`). Its **system** message layers the fixed `pass` prompt, the *constitution*
    (standing articles), and the *consultation plan* (the decisions the boot selected for this session);
    its **user** message is the *entry form* — the task, the output schema, the budgets. Tools are handed
    over separately as a schema.
    """
    )
    return


@app.cell
def _(mo, store, suite):
    # session + task pickers for Lane A
    _sessions = sorted(
        (s for s in store.all("session") if getattr(s, "attached", False) and getattr(s, "evaluation", None) is not None),
        key=lambda s: s.pass_, reverse=True,
    )
    session_dd = mo.ui.dropdown(
        options={f"{s.id} (pass {s.pass_})": s.id for s in _sessions} or {"(no evaluated attached session)": ""},
        value=(f"{_sessions[0].id} (pass {_sessions[0].pass_})" if _sessions else "(no evaluated attached session)"),
        label="**Session** — whose consultation plan conditions the agent",
    )
    _tasks = [r["task"] for r in suite.current().rows()]
    task_dd = mo.ui.dropdown(
        options=_tasks, value=_tasks[0], label="**Task** — the entry the agent is handed",
    )
    mo.hstack([session_dd, task_dd], justify="start", gap=1)
    return session_dd, task_dd


@app.cell
def _(
    Agent,
    Tools,
    code_block,
    context_records,
    json,
    message_card,
    mo,
    segment,
    session_dd,
    stack,
    store,
    suite,
    task_dd,
):
    # ---- assemble the task-agent messages with the REAL Agent.compose ----------------
    _sid = session_dd.value or None
    _session = store.read("session", _sid) if _sid else None
    _records = context_records(store, _session) if _session else []
    _articles = [a.article for a in store.articles()]

    _row = suite.current().by_id[task_dd.value].row()
    _budgets = {k: v for k, v in {"shell": _row["shell_budget"], "http": _row["http_budget"]}.items() if v is not None}

    _agent = Agent(session=_sid, records=_records, articles=_articles, policy="model")
    _system, _user = _agent.compose(_row["task"], _row["prompt"], _row["schema"], _budgets)

    # Split the assembled system string back into its named sections (the same markers compose writes).
    _head, _rest = _system.split("\n\n## Constitution\n", 1)
    _con, _rest = _rest.split("\n\n## Consultation plan", 1)
    _rest = _rest.split("\n", 1)[1]
    _plan, _finish = _rest.split("\n\nFinish by replying", 1)

    _sys_layers = (
        stack([("pass role prompt", "fixed"), ("Constitution", "directive"),
               ("Consultation plan", "store"), ("Finish rule", "fixed")])
        + segment("fixed", "Fixed — the `pass` role prompt",
                  "role body + reply rule + derived record schemas; identical on every pass",
                  code_block(_head, 1400), "hgi/roles/prompt('pass')")
        + segment("directive", "Constitution",
                  f"{len(_articles)} standing articles loaded with every pass — always on, never selected",
                  code_block(_con.strip() or "(none)"), "store.articles()")
        + segment("store", "Consultation plan — records in context",
                  f"{len(_records)} decision(s) the boot selected & whose guard passed for {_sid or '—'}; each owed an `apply`",
                  code_block(_plan.strip() or "- (none)"), "hgi.evaluate.context_records(store, session)")
        + segment("fixed", "Fixed — the finish rule", "how to close the turn (the output envelope)",
                  code_block(("Finish by replying" + _finish).strip()), "Agent.compose")
    )

    _budget_line = "; ".join(f"{k} calls: {v}" for k, v in _budgets.items())
    _entry = _user.split("\nOutput schema:", 1)[0]
    _usr_layers = (
        stack([("Task prompt", "entry"), ("Output schema", "contract"), ("Budgets", "directive")])
        + segment("entry", "Entry form — the task", "what the agent is asked to do (the hidden test is withheld)",
                  code_block(_entry), "Task.row()['prompt']")
        + segment("contract", "Output contract — schema", "the JSON the answer must validate against",
                  code_block(json.dumps(_row["schema"], indent=2)), "Task.row()['schema']")
        + segment("directive", "Directive — call budgets",
                  "the economy the agent must work within" if _budget_line else "no budget on this task",
                  code_block(_budget_line or "(none)"), "Tools.budgets")
    )

    _tools = segment(
        "tools", "Tools handed to the agent",
        f"{len(Tools.SCHEMA)} functions the actor may call in its loop (MAX_TURNS=8)",
        code_block([t["function"]["name"] + " — " + t["function"]["description"] for t in Tools.SCHEMA]),
        "suite.tools.Tools.SCHEMA",
    )

    mo.vstack([message_card("System", _sys_layers), message_card("User", _usr_layers), mo.Html(_tools)])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ---
    ## Lane B — the backward-pass roles
    Each request the loop asks of a role is built by a **builder** in `hgi/contract.py`, sent through the
    single chokepoint `hgi/model.py::complete`, which pairs a **system** message (`roles.prompt(role)` —
    the role's `.md` body + reply rule + derived schemas) with a **user** message
    (`roles.request(name, **content)` — the entry/world/store material *plus* the reply contract).

    Pick a request. The notebook runs its real builder against a **copy** of the store (no model call, no
    writes), then splits the resulting JSON field by field into the layers below. Where the store can't
    supply what a request needs, the fixed prompt and the output contract still render — with the reason.
    """
    )
    return


@app.cell
def _(contract, mo, roles):
    # request → role (from contract.py's builders), for labelling even when a build fails
    REQ_ROLE = {
        "classify": "pass", "lens": "pass", "dispose": "pass", "propose": "pass",
        "coding": "coder", "guard": "coder",
        "nominate": "consolidator", "attack": "examiner",
        "credit": "adjudicator", "currency": "adjudicator", "triage": "adjudicator", "verdict": "adjudicator",
    }
    REQ_DESC = {
        "classify": "name the work-shape/convention terms the tasks instantiate",
        "guard": "the blind second coder: does this hook fire on these presentations?",
        "lens": "walk one lens's angle over the run and file findings",
        "dispose": "for each consulted record, say how it bore on the rows",
        "propose": "propose decisions from what the pass observed",
        "coding": "name the convention each observation turned on",
        "nominate": "draft / retire decisions from the consolidation brief",
        "credit": "did an applied record regress its tasks? indict a slot",
        "currency": "does this decision still hold, given its competence row?",
        "triage": "reducible or irreducible? the noise filter over a recurrence",
        "attack": "adversarially refute a draft's premises / abstraction",
        "verdict": "admit / amend / decline / defer / escalate a draft",
    }
    _opts = {f"{name}  →  {REQ_ROLE.get(name, '?')}": name for name in sorted(roles.REPLIES) if name in contract.BUILDERS}
    request_dd = mo.ui.dropdown(options=_opts, value="propose  →  pass", label="**Request** — one thing a role is asked to answer")
    request_dd
    return REQ_DESC, REQ_ROLE, request_dd


@app.cell
def _(REQ_ROLE, request_dd):
    role_for_request = REQ_ROLE.get(request_dd.value, "pass")
    return (role_for_request,)


@app.cell
def _():
    # ---- field-name → provenance category, and a one-line gloss ----------------------
    # Keyed by field name because the loop reuses the same names across requests; this is the
    # notebook's reading of what hgi/contract.py passes, kept small so it doesn't drift.
    FIELD_KIND = {
        "presentations": "entry", "work_shape": "entry", "shape": "entry", "prompt": "entry", "task": "entry", "schema": "entry",
        "rows": "world", "scores": "world", "observations": "world", "evidence": "world", "oracle": "world",
        "watch_scorer": "world", "series": "world", "noticed": "world", "applied": "world", "subject": "world",
        "scorers": "world",
        "consulted": "store", "hook": "store", "record": "store", "draft": "store", "co_applying": "store",
        "fires_owed": "store", "unreached": "store", "articles": "store", "attack": "store",
        "applied_over_considered": "store", "moot_evidence": "store", "supersedes": "store",
        "terms": "directive", "vocabulary": "directive", "vocabularies": "directive", "bars": "directive", "threshold": "directive",
        "moot_when": "directive", "proposed_terms": "directive", "rungs": "directive", "mark": "directive",
        "bar": "directive", "kind": "directive", "status": "directive", "latch_type": "directive", "occasions": "directive",
        "lens": "lens", "claims": "lens", "angle": "lens", "counterfactual": "lens", "product": "lens",
        "reply": "contract", "empty_is_legal": "contract", "request": "meta", "model_id": "meta",
    }
    FIELD_DESC = {
        "presentations": "every task's id+prompt, hidden test withheld — what the boot classifies",
        "terms": "the registered vocabulary the answer must draw its terms from",
        "vocabulary": "the closed vocabulary this verdict must answer in",
        "work_shape": "the boot's classification of the task's shape",
        "hook": "the consulted decision's activation hook — terms it fires on, and its exclusions",
        "consulted": "the store decisions this pass had in context (the record views)",
        "rows": "the evaluated rows — each task's outcome this run",
        "scores": "the scorer readings for the session",
        "co_applying": "groups of consulted records whose hooks overlap — read together",
        "fires_owed": "acts the consulted records obliged this pass to carry",
        "observations": "what the pass noticed — the failures being coded / drafted from",
        "lens": "the interrogating angle: its question, counterfactual and product shape",
        "draft": "the candidate decision under examination / adjudication",
        "evidence": "the evidence pack assembled for this draft",
        "oracle": "the scorer series and scores bearing on the verdict",
        "watch_scorer": "the scorer the decision's falsification watch keys on",
        "bars": "the registry's numeric thresholds (the floors)",
        "applied": "records applied over the window and whether their tasks improved",
        "subject": "the material the lens interrogates (consulted records, rows, scores, presentations)",
        "reply": "the exact JSON shape the answer must take — the output contract",
        "empty_is_legal": "a directive: refusal (an empty list) is a first-class answer",
        "shape": "the recurring shape of the grouped observations",
        "record": "the decision whose currency is under review",
        "request": "the request name the role and the stub both key on",
        "vocabularies": "the registered vocabularies a draft's terms must come from",
        "scorers": "the scorers whose readings the proposal may cite as evidence",
        "rungs": "the ladder of decision strengths a draft may claim",
        "model_id": "the model the reply is being priced for",
    }
    return FIELD_DESC, FIELD_KIND


@app.cell
def _(SimpleNamespace, Store, contract, registry, shutil, tempfile):
    # ---- run a builder against a COPY of the store, so nothing is written -------------
    from pathlib import Path as _BP

    def build_request(store_root_str, name):
        scratch = _BP(tempfile.mkdtemp(prefix="anatomy-"))
        try:
            shutil.copytree(store_root_str, scratch / "s")
            reg = registry.load(scratch / "s")
            tok = registry.use(reg)
            try:
                st = Store(scratch / "s", registry=reg)
                args = SimpleNamespace(session=None, lens=None, draft=None, out=None, store=None, show=4000)
                role, payload = contract.BUILDERS[name](st, args)
                return role, payload, None
            finally:
                registry.reset(tok)
        except SystemExit as e:
            return None, None, str(e)
        except Exception as e:  # a store that lacks what the request needs — report, don't crash
            return None, None, f"{type(e).__name__}: {e}"
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    return (build_request,)


@app.cell
def _(
    FIELD_DESC,
    FIELD_KIND,
    REQ_DESC,
    build_request,
    code_block,
    json,
    message_card,
    mo,
    request_dd,
    role_for_request,
    roles,
    segment,
    stack,
    store_dd,
):
    _name = request_dd.value
    _role = role_for_request

    # ---------- SYSTEM message: roles.prompt(role), split into body / reply-rule / schemas ----------
    _full = roles.prompt(_role)
    _rule = roles.REPLY_RULE
    _body, _tail = _full.split("\n\n" + _rule, 1) if ("\n\n" + _rule) in _full else (_full, "")
    _schemas = _tail.replace("\n\n", "", 1) if _tail else ""
    _sys_layers = (
        stack([("role .md body", "fixed"), ("reply rule", "fixed"), ("record schemas", "fixed")])
        + segment("fixed", f"`{_role}.md` — the role instruction",
                  "the durable prompt for this role; the store material never enters here",
                  code_block(_body.strip(), 2200), f"hgi/roles/{_role}.md")
        + segment("fixed", "Reply rule", "the constant that pins the answer to one JSON object",
                  code_block(_rule), "roles.REPLY_RULE")
        + segment("fixed", "Record schemas",
                  "JSON-Schema of the records this role reads/writes, derived from hgi/types.py — never a second copy",
                  code_block(_schemas.strip() or "(this role reads no record shapes)", 1200), "roles.schemas(role)")
    )

    # ---------- USER message: run the real builder, split field by field ----------
    _brole, _payload, _reason = build_request(store_dd.value, _name)

    _note = None
    if _payload is None:
        _note = mo.callout(
            mo.md(f"**`{_name}` can't be exercised on `{store_dd.value}`.** {_reason}\n\n"
                  f"The fixed prompt and the output contract still show below — only the live entry/store "
                  f"material is missing. Try a richer store, or one with the record this request needs."),
            kind="warn",
        )
        _obj = {"request": _name, "reply": roles.REPLIES.get(_name, {})}
    else:
        _obj = json.loads(_payload)

    _keys = [k for k in _obj if k not in ("request", "reply")]
    _layer_strip = [("request", "meta")] + [(k, FIELD_KIND.get(k, "store")) for k in _keys] + [("reply", "contract")]

    _usr = stack(_layer_strip)
    _usr += segment("meta", "request", "the request name — the role and the stub both dispatch on it",
                    code_block(_obj.get("request")), "roles.request(name, …)")
    for _k in _keys:
        _usr += segment(FIELD_KIND.get(_k, "store"), _k,
                        FIELD_DESC.get(_k, "content the builder assembled for this request"),
                        code_block(_obj[_k]), None)
    _usr += segment("contract", "reply",
                    "the exact shape the role must answer in — travels with the request, not the prompt",
                    code_block(roles.REPLIES.get(_name, {})), "roles.REPLIES[name]")

    _header = mo.md(
        f"### `{_name}` → **{_role}**\n*{REQ_DESC.get(_name, '')}* · built by "
        f"`hgi/contract.py::BUILDERS['{_name}']`, sent through `hgi/model.py::complete`."
    )

    mo.vstack([x for x in [_header, _note, message_card("System", _sys_layers), message_card("User", _usr)] if x is not None])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ---
    ### How to read this for critique
    - **Fixed** should hold nothing task-specific — if run detail leaked into a role's `.md`, that's a smell.
    - **Entry** is the agent's whole view of the task; the hidden test is *never* here by design.
    - **Store / Consultation plan** is where to ask *are these the right decisions, and is the lens right?*
      An empty plan means the boot selected nothing — a hook-coverage question, not a bug.
    - **Directive / vocab** is the registered surface the answer must stay inside; a missing term shows up as an escape.
    - **Output contract** is the shape the reply must take — a mismatch here is what the drafting floor rejects.

    Change the store, the session, the task, or the request above and every layer re-derives from the code.
    """
    )
    return


if __name__ == "__main__":
    app.run()
