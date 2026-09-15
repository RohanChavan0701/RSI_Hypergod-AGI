#!/usr/bin/env python3
"""Sanity-check an HGI arm store: sessions, the observations each pass filed, the decisions the backward pass admitted,
the consolidations' nominations and their outcomes, and the ledger.

Usage:
    .venv/bin/python .claude/skills/experiment-runner/inspect_store.py <arm-store-dir> [--full]

    <arm-store-dir> is the `store/` under an arm dir, e.g. runs/text2sql/120b-attached/store
    --full prints each observation's `happened` text in full instead of truncating.

Reads only committed JSON, so it is safe to run against a store while its arm is still running (it sees whatever the
last pass committed). Pair it with the live-monitoring grep in SKILL.md ("Monitoring a live run"): the monitor tells you
*when* a pass or consolidation lands; this tells you *whether what it wrote is sound*.

The four questions it helps answer (SKILL.md spells out what a good answer looks like):
  1. Do failed tasks mint observations?  -> SESSIONS shows per-pass pass-rate and the obs each filed.
  2. Do observations state the task's world-fact, not an exogenous symptom (budget, "no rule consulted", scorer names)?
     -> OBSERVATIONS lists `turned_on` (the convention) and flags the exogenous/self-referential ones.
  3. Does obs -> decision accept/reject/consolidate correctly?  -> CONSOLIDATIONS lists every nomination's outcome
     (admitted / refused-by-floor / declined / dismissed) and DECISIONS shows what stuck, with its latch terms.
  4. Do the mints make sense?  -> read the `happened`/`turned_on` and the decision text against the family's world.
"""
from __future__ import annotations

import glob
import json
import os
import sys

FULL = "--full" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
store = args[0] if args else "store"
if os.path.basename(store) != "store" and os.path.isdir(os.path.join(store, "store")):
    store = os.path.join(store, "store")  # an arm dir was passed; descend into its store


def load(p):
    with open(p) as f:
        return json.load(f)


def jline(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


# A world-fact observation names the task's world; these cues mark one that drifted to an exogenous symptom
# (a way-of-working) or to the store's own machinery — the failure modes carry-forward items 40/48/66 name.
EXOGENOUS = ("budget", "no rule", "no matching rule", "no applicable rule", "no store records",
             "should have fired", "not consulted", "no rule was consulted", "turn limit")


def is_exogenous(obs) -> str | None:
    text = f"{obs.get('turned_on') or ''} {obs.get('happened') or ''}".lower()
    hit = [c for c in EXOGENOUS if c in text]
    return ", ".join(hit) if hit else None


print(f"### STORE: {store}\n")

sess = sorted(glob.glob(f"{store}/sessions/S-*.json"))
print(f"## SESSIONS ({len(sess)})")
for p in sess:
    d = load(p)
    ev = d.get("evaluation") or {}
    tpr = ((ev.get("scores") or {}).get("task_pass_rate") or {}).get("value") if isinstance(ev, dict) else None
    ws = d.get("work_shape") or {}
    consulted = [c.get("record") for c in (d.get("consulted") or [])]
    rate = "running" if not ev else ("unevaluable" if tpr is None else f"{tpr:.2f}")
    print(f"  {d.get('id')} pass={d.get('pass')} rate={rate} filed={d.get('observations_filed') or []} consulted={consulted or 'nothing'}")
    print(f"      work_shape terms={ws.get('terms')} escapes={ws.get('escapes')}")
print()

obs = sorted(glob.glob(f"{store}/observations/O-*.json"))
world, exo, nofact = 0, 0, 0
print(f"## OBSERVATIONS ({len(obs)})")
for p in obs:
    d = load(p)
    a = d.get("anchor") or {}
    kind = "call" if a.get("call") else ("record:" + str(a.get("record")) if a.get("record") else ("path:" + str(a.get("path")) if a.get("path") else "NO-ANCHOR"))
    disp = d.get("disposition") or {}
    flag = is_exogenous(d)
    tag = f"  ⚠ EXOGENOUS({flag})" if flag else ("" if d.get("turned_on") else "  ⚠ no turned_on")
    if flag:
        exo += 1
    elif d.get("turned_on"):
        world += 1
    else:
        nofact += 1
    print(f"  {d['name']} shape={d.get('shape') or 'open'} sess={d.get('session')} anchor={kind} disp={disp.get('state')}->{disp.get('pointer')}{tag}")
    print(f"      turned_on: {d.get('turned_on')}")
    print(f"      happened : {d.get('happened') if FULL else (d.get('happened') or '')[:200]}")
print(f"  -> {world} world-fact, {nofact} no-turned_on, {exo} exogenous/self-referential\n")

dec = sorted(glob.glob(f"{store}/decisions/D-*.json"))
print(f"## DECISIONS ({len(dec)})")
for p in dec:
    d = load(p)
    adm = d.get("admission") or {}
    terms = sorted({t for l in (d.get("latches") or []) for t in ((l.get("guard") or {}).get("terms") or [])})
    print(f"  {d.get('id') or d.get('name')}: rung={adm.get('rung')} verdict={adm.get('verdict')} by={adm.get('proposed_by')} ledger={adm.get('ledger_entry')}")
    print(f"      latch_terms={terms}")
    print(f"      decision: {d.get('decision')}")
    print(f"      counterfactual: {d.get('counterfactual')}")
print()

con = sorted(glob.glob(f"{store}/consolidations/K-*.json"))
print(f"## CONSOLIDATIONS ({len(con)})")
for p in con:
    d = load(p)
    print(f"  {d.get('id')} after_pass={d.get('after_pass')} read={d.get('sessions_read')} admitted={d.get('admitted')} "
          f"retired={d.get('retired')} corroborated={d.get('corroborated')}")
    for n in d.get("nominations") or []:
        if n.get("rung") == "article":
            continue  # genesis-anchoring housekeeping, not an obs->decision nomination
        print(f"      [{n.get('ledger_entry')}] {n.get('rung')} on {n.get('subject')} <- {n.get('evidence')}")
        print(f"          outcome: {n.get('outcome')}")
    for g in d.get("dismissed") or []:
        print(f"      dismissed: {g}")
print()

led = jline(f"{store}/ledger/ledger.jsonl")
print(f"## LEDGER ({len(led)} entries)")
for e in led:
    print(f"  {e.get('id')}: {e.get('species')} verdict={e.get('verdict')} {str(e.get('claim') or '')[:110]}")
