"""The reasoning-core family, read offline from its pinned file: each instance is graded by the
generator's own checker — a regex match by ``regex.fullmatch``, a grammar string by NLTK membership —
never by a comparison against a stored answer, and the strict twin carries the same instances one call tighter."""

from __future__ import annotations

import pytest

from suite.faults import FaultProfile
from suite.families import FAMILIES
from suite.families import _reasoning_core as rc
from suite.families import reasoning_core as rcf
from suite.tasks import SuiteSpec, build
from suite.tools import ToolError, Tools, can_import

INSTANCES = 24
"""Pinned instances: twelve regex-following and twelve cfg-generation."""

REGEX_ID = "reasoning-core/regex_04"
"""One pinned regex task with hand-checkable matches: the pattern ``(?:((F)Y)+)``."""
REGEX_MATCHES = ("FY", "FYFY")
REGEX_NON_MATCHES = ("F", "FYF", "")

CFG_ID = "reasoning-core/cfg_00"
"""One pinned grammar task whose language a member can be written for by hand."""
CFG_MEMBER = "boy boy boy boy boy boy boy boy boy boy floor"  # eleven terminals; the grammar's `S -> 'boy' S` chain
# members of the language but under the token floor, then a string over the floor that the grammar does not derive
CFG_NON_MEMBERS = ("floor", "boy floor", "< floor >", "boy boy boy boy boy boy boy boy boy boy nope")


def _by_id(name: str):
    return {t.id: t for t in FAMILIES[name].tasks()}


def test_both_families_load_the_same_pinned_instances_one_call_apart():
    counts = {name: len(FAMILIES[name].tasks()) for name in ("reasoning-core", "reasoning-core-strict")}
    assert counts == {"reasoning-core": INSTANCES, "reasoning-core-strict": INSTANCES}
    for name, n in counts.items():
        assert len(_by_id(name)) == n, f"{name}: task ids are not unique"

    lax, strict = _by_id("reasoning-core"), _by_id("reasoning-core-strict")
    names = {i.split("/", 1)[1] for i in lax}
    assert names == {i.split("/", 1)[1] for i in strict}, "the strict twin carries the same instances"
    for short in names:
        lt, st = lax[f"reasoning-core/{short}"], strict[f"reasoning-core-strict/{short}"]
        assert lt.shapes == st.shapes == ("shell-tool", "tool-budget")
        assert lt.knowing == st.knowing == {"shell": 1}
        assert lt.shell_budget == 2 and st.shell_budget == 1, "lax leaves one call to spare; strict holds exactly the floor"

    world = build(SuiteSpec(families=["reasoning-core", "reasoning-core-strict"]))
    assert len(world.by_id) == 2 * INSTANCES and world.families() == counts


def test_the_pinned_file_carries_the_checker_inputs_and_no_witness():
    for r in FAMILIES["reasoning-core"].records():
        assert r["kind"] in ("regex-following", "cfg-generation")
        assert "witness" not in r and "answer" not in r and "string" not in r and "tokens" not in r
        if r["kind"] == "regex-following":
            assert set(r) == {"id", "kind", "level", "seed", "rc_task", "pattern", "witness_len"}
        else:
            assert set(r) == {"id", "kind", "level", "seed", "rc_task", "grammar", "start", "min_tokens"}


def test_a_regex_task_grades_by_full_match_not_by_a_stored_string(tmp_path):
    spec = _by_id("reasoning-core")[REGEX_ID]
    assert "fully matches" in spec.prompt and "budget of 2 shell calls" in spec.prompt
    for good in REGEX_MATCHES:  # two distinct strings both match — a membership verdict, not one gold string
        assert spec.check(good, tmp_path), f"{good!r} matches the pattern and must pass"
    for bad in REGEX_NON_MATCHES:
        assert not spec.check(bad, tmp_path), f"{bad!r} does not match and must fail"
    assert not spec.check("F Y", tmp_path), "a match with whitespace is not an admissible sample"
    assert not spec.check(42, tmp_path), "a non-string result never passes"


def test_a_cfg_task_grades_by_grammar_membership_over_the_token_floor(tmp_path):
    spec = _by_id("reasoning-core")[CFG_ID]
    record = next(r for r in FAMILIES["reasoning-core"].records() if f"reasoning-core/{r['id']}" == CFG_ID)
    assert record["start"] in spec.prompt and str(record["min_tokens"]) in spec.prompt
    assert spec.check(CFG_MEMBER, tmp_path), "a string the grammar derives at the token floor must pass"
    for bad in CFG_NON_MEMBERS:
        assert not spec.check(bad, tmp_path), f"{bad!r} is under the floor or not derivable and must fail"
    assert not spec.check(("< " * 200).strip(), tmp_path), "a string past the token cap is refused unparsed"
    assert not spec.check(7, tmp_path), "a non-string result never passes"


def test_the_regex_checker_is_reasoning_cores_full_match_verdict():
    assert rc.regex_ok(r"(?:((F)Y)+)", "FYFY") and not rc.regex_ok(r"(?:((F)Y)+)", "FYF")
    assert not rc.regex_ok(r"a(", "a")  # an invalid pattern is a failed task, not a raise from the grader


# --- the budget is a tool-call limit the check never grades: it fails no task, the answer alone decides
#     (carry-forward items 47, 56) ---

def test_the_tool_layer_refuses_an_over_budget_call(tmp_path):
    tools = Tools(task="t", workdir=tmp_path, profile=FaultProfile(), shell_budget=1)
    assert tools.shell("echo one").strip() == "one"  # the one verification call, within budget
    with pytest.raises(ToolError, match="refused"):
        tools.shell("echo two")  # the repair call, refused past the budget of one
    assert tools.calls["shell"] == 2 and not tools.budget_respected()  # the overage is counted for the economy series


def test_the_answer_alone_decides_a_pass(tmp_path):
    # A matching witness / grammar member passes both pools; the check never reads the working directory.
    assert _by_id("reasoning-core")[REGEX_ID].check(REGEX_MATCHES[1], tmp_path)
    assert _by_id("reasoning-core")[CFG_ID].check(CFG_MEMBER, tmp_path)
    assert _by_id("reasoning-core-strict")["reasoning-core-strict/regex_04"].check(REGEX_MATCHES[1], tmp_path)


def test_the_budget_fails_no_task_the_answer_carries_it(tmp_path):
    # The tool layer still refuses a call past each pool's budget, but the check grades the answer alone: a matching
    # answer passes whether or not a later call was refused. The strict pool bites through the answer instead — a wrong
    # first candidate it cannot repair within one call is submitted and fails on the answer, not on a budget flag.
    for fam, limit in (("reasoning-core", 2), ("reasoning-core-strict", 1)):
        spec = _by_id(fam)[f"{fam}/regex_04"]
        assert spec.shell_budget == limit  # derived from KNOWING + SLACK, not hardcoded here
        wd = tmp_path / fam
        wd.mkdir()
        tools = Tools(task=spec.id, workdir=wd, profile=FaultProfile(), shell_budget=spec.shell_budget)
        for _ in range(limit):
            tools.shell("echo ok")  # spend the whole budget, each call within it
        tools.dispatch("shell", '{"command": "echo over"}')  # one call past the budget, refused
        assert not tools.budget_respected(), f"{fam}: the overage is counted"
        assert spec.check(REGEX_MATCHES[1], wd), f"{fam}: over budget, a matching answer still passes"
        assert not spec.check(REGEX_NON_MATCHES[0], wd), f"{fam}: a non-matching answer fails, over budget or not"


# --- the harder tier: new family variants at a lower first-sight ceiling, same instances (follow-up to item 47) ---

HARD_INSTANCES = 24
"""The harder tier pins the same count as the moderate one: twelve regex-following and twelve cfg-generation."""

HARD_REGEX_ID = "reasoning-core-hard/regex_04"
"""One pinned harder regex task with hand-checkable matches: the pattern ``((?:(T?))financial*)$``."""
HARD_REGEX_MATCHES = ("financia", "financial", "Tfinancia")  # optional T?, the literal 'financia', then l*
HARD_REGEX_NON_MATCHES = ("financi", "financiaX", "")

HARD_CFG_ID = "reasoning-core-hard/cfg_00"
"""One pinned harder grammar task: a bracket-nested chain — ``[ … ]`` around ``< … >`` around a word, floor eleven tokens."""
HARD_CFG_MEMBER = "[ [ [ < < about > > ] ] ]"  # eleven tokens; `S -> '[' S ']'` three deep around `B -> '<' B '>'` twice around `'about'`
HARD_CFG_NON_MEMBERS = ("mother", "[ mother ]", "[ [ [ < < about > > ] ] mother")  # under the floor, or unbalanced brackets over it


def test_the_hard_tier_config_matches_the_pinned_records():
    assert rc.HARD.regex_level == 5 and rc.HARD.cfg_level == 3 and rc.HARD.cfg_tokens == (10, 16)
    assert rc.MODERATE.regex_level == 3 and rc.MODERATE.cfg_level == 2 and rc.MODERATE.cfg_tokens == (6, 12)
    # disjoint seed bases: no instance is shared between the tiers
    assert rc.HARD.regex_seed_base != rc.MODERATE.regex_seed_base
    assert rc.HARD.cfg_seed_base != rc.MODERATE.cfg_seed_base


def test_the_two_tiers_are_disjoint_and_the_hard_tier_is_harder():
    mod = {r["seed"] for r in FAMILIES["reasoning-core"].records()}
    hard_recs = FAMILIES["reasoning-core-hard"].records()
    hard = {r["seed"] for r in hard_recs}
    assert mod and hard and not (mod & hard), "the tiers share no seed, so no instance overlaps"
    assert all(r["level"] == 5 for r in hard_recs if r["kind"] == "regex-following"), "harder regex is level 5"
    assert all(r["level"] == 3 for r in hard_recs if r["kind"] == "cfg-generation"), "harder grammar is level 3"
    # the harder grammar tier's window floor forces a longer valid derivation than the moderate tier's floor
    assert min(r["min_tokens"] for r in hard_recs if r["kind"] == "cfg-generation") >= 10


def test_hard_families_load_the_same_pinned_instances_one_call_apart():
    counts = {name: len(FAMILIES[name].tasks()) for name in ("reasoning-core-hard", "reasoning-core-hard-strict")}
    assert counts == {"reasoning-core-hard": HARD_INSTANCES, "reasoning-core-hard-strict": HARD_INSTANCES}
    for name, n in counts.items():
        assert len(_by_id(name)) == n, f"{name}: task ids are not unique"

    lax, strict = _by_id("reasoning-core-hard"), _by_id("reasoning-core-hard-strict")
    names = {i.split("/", 1)[1] for i in lax}
    assert names == {i.split("/", 1)[1] for i in strict}, "the hard strict twin carries the same instances"
    for short in names:
        lt, st = lax[f"reasoning-core-hard/{short}"], strict[f"reasoning-core-hard-strict/{short}"]
        assert lt.shapes == st.shapes == ("shell-tool", "tool-budget")
        assert lt.knowing == st.knowing == {"shell": 1}
        assert lt.shell_budget == 2 and st.shell_budget == 1, "the hard pair carries the same slack as the moderate pair"

    world = build(SuiteSpec(families=["reasoning-core-hard", "reasoning-core-hard-strict"]))
    assert len(world.by_id) == 2 * HARD_INSTANCES and world.families() == counts


def test_the_hard_pinned_file_carries_the_checker_inputs_and_no_witness():
    recs = FAMILIES["reasoning-core-hard"].records()
    assert len(recs) == HARD_INSTANCES
    for r in recs:
        assert r["kind"] in ("regex-following", "cfg-generation")
        assert "witness" not in r and "answer" not in r and "string" not in r and "tokens" not in r
        if r["kind"] == "regex-following":
            assert set(r) == {"id", "kind", "level", "seed", "rc_task", "pattern", "witness_len"}
        else:
            assert set(r) == {"id", "kind", "level", "seed", "rc_task", "grammar", "start", "min_tokens"}


def test_a_hard_regex_task_is_satisfiable_and_grades_by_full_match(tmp_path):
    spec = _by_id("reasoning-core-hard")[HARD_REGEX_ID]
    assert "fully matches" in spec.prompt and "budget of 2 shell calls" in spec.prompt
    for good in HARD_REGEX_MATCHES:  # two distinct matches — a membership verdict, not one gold string; the witness proves it satisfiable
        assert spec.check(good, tmp_path), f"{good!r} matches the harder pattern and must pass"
    for bad in HARD_REGEX_NON_MATCHES:
        assert not spec.check(bad, tmp_path), f"{bad!r} does not match and must fail"
    assert not spec.check(42, tmp_path), "a non-string result never passes"


def test_a_hard_cfg_task_is_satisfiable_and_grades_by_membership_over_the_floor(tmp_path):
    spec = _by_id("reasoning-core-hard")[HARD_CFG_ID]
    record = next(r for r in FAMILIES["reasoning-core-hard"].records() if f"reasoning-core-hard/{r['id']}" == HARD_CFG_ID)
    assert record["start"] in spec.prompt and str(record["min_tokens"]) in spec.prompt
    assert record["min_tokens"] == 11, "the pinned harder floor for this instance"
    assert spec.check(HARD_CFG_MEMBER, tmp_path), "a string the grammar derives at the harder floor must pass"
    for bad in HARD_CFG_NON_MEMBERS:
        assert not spec.check(bad, tmp_path), f"{bad!r} is under the floor or not derivable and must fail"
    assert not spec.check(7, tmp_path), "a non-string result never passes"


def test_the_hard_tier_budget_fails_no_task_at_each_pool(tmp_path):
    for fam, limit in (("reasoning-core-hard", 2), ("reasoning-core-hard-strict", 1)):
        spec = _by_id(fam)[f"{fam}/regex_04"]
        assert spec.shell_budget == limit  # derived from KNOWING + SLACK, not hardcoded here
        wd = tmp_path / fam
        wd.mkdir()
        tools = Tools(task=spec.id, workdir=wd, profile=FaultProfile(), shell_budget=spec.shell_budget)
        for _ in range(limit):
            tools.shell("echo ok")  # spend the whole budget
        tools.dispatch("shell", '{"command": "echo over"}')  # one call past budget, refused
        assert not tools.budget_respected(), f"{fam}: the overage is counted"
        assert spec.check(HARD_REGEX_MATCHES[0], wd), f"{fam}: over budget, a matching answer still passes"


# --- item 53: the shell tool's python must satisfy the family's declared requirements ---

def test_every_reasoning_core_family_declares_its_shell_requirements():
    """A reasoning-core task tells the actor to verify with regex.fullmatch / NLTK, so the family declares those
    modules as shell requirements; the arm's preflight (hgi.experiment) checks them before pass 1."""
    for name in ("reasoning-core", "reasoning-core-strict", "reasoning-core-hard", "reasoning-core-hard-strict"):
        assert FAMILIES[name].requires == ("nltk", "regex"), f"{name} must declare nltk+regex"


def test_can_import_checks_the_shell_tools_python():
    """The check runs through the shell tool's own environment, so it reads the interpreter a shell call resolves
    to. In this tree's venv nltk and regex are importable; a module that is not installed comes back as an error."""
    assert can_import(["nltk", "regex"]) is None, "the family's requirements import under the shell tool's python"
    assert can_import([]) is None, "no requirement is vacuously satisfiable"
    missing = can_import(["a_module_that_is_not_installed_zzz"])
    assert missing is not None and "No module named" in missing


def test_the_shell_tools_python_resolves_the_family_requirements(tmp_path):
    """The environment fix (item 53a): a `python3` invoked through the shell tool imports nltk and regex — the same
    call a reasoning-core task asks the actor to make — because the shell runs with the venv's bin ahead on PATH."""
    tools = Tools(task="t", workdir=tmp_path, profile=FaultProfile())
    out = tools.shell('python3 -c "import nltk, regex; print(42)"').strip()
    assert out == "42", "a shell call's python3 has the family's requirements"


def test_both_tiers_regenerate_identically_from_their_seeds():
    """With the generation stack installed, each tier's pinned file is reproduced bit-for-bit from its seeds and level."""
    import json

    pytest.importorskip("reasoning_core")
    for fam, tier in (("reasoning-core", rc.MODERATE), ("reasoning-core-hard", rc.HARD)):
        regen = rc.records(rcf.REGEX_N, rcf.CFG_N, tier=tier)
        gen = [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in regen]
        pinned = [l for l in FAMILIES[fam].data_path.read_text().splitlines() if l.strip()]
        assert gen == pinned, f"{fam}: the pinned file no longer matches its seeds/tier"
