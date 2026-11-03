"""Measurement checks for conflicting workflows, without an inference endpoint."""

from copy import deepcopy

from suite.families import FAMILIES
from suite.families.workflow_drift import OPERATIONS, cases, tasks_for
from suite.tasks import SuiteSpec, build
from suite.workflow_pilot import transfer_features


def test_transfer_destination_determines_action_across_versions_and_operations():
    rows = [transfer_features(index) for index in range(8)]
    assert len({tuple(features.values()) for features, _ in rows}) == 8
    for field in ("version", "operation"):
        for value in {features[field] for features, _ in rows}:
            assert {action for features, action in rows if features[field] == value} == {
                "execute", "confirm",
            }
    for features, action in rows:
        assert action == {"west": "execute", "east": "confirm"}[features["destination"]]


def test_disjoint_operations_and_unique_tasks():
    groups = [{row[0] for row in rows} for rows in OPERATIONS.values()]
    assert all(not left & right for i, left in enumerate(groups) for right in groups[i + 1:])
    world = build(SuiteSpec(families=[f"workflow-{split}" for split in OPERATIONS]))
    assert len(world.by_id) == 36
    assert build(SuiteSpec(families=["workflow-test"])).hash == build(
        SuiteSpec(families=["workflow-test"])).hash


def test_grader_rejects_wrong_actions_invented_arguments_and_missing_fields(tmp_path):
    for split in OPERATIONS:
        assert f"workflow-{split}" in FAMILIES
        for case, task in zip(cases(split), tasks_for(split), strict=True):
            gold = case.expected()
            assert task.check(gold, tmp_path)
            assert not task.check(None, tmp_path)
            for action in {"execute", "clarify", "confirm"} - {gold["action"]}:
                assert not task.check({**gold, "action": action}, tmp_path)
            invented = deepcopy(gold)
            invented["arguments"]["fabricated"] = "value"
            assert not task.check(invented, tmp_path)
            assert not task.check({"action": gold["action"]}, tmp_path)
            assert not task.check({**gold, "explanation": "extra"}, tmp_path)


def test_global_action_rules_fail_and_conditional_reference_is_consistent():
    for split in OPERATIONS:
        rows = cases(split)
        actions = [case.expected()["action"] for case in rows]
        assert {action: actions.count(action) for action in set(actions)} == {
            "clarify": 6, "execute": 4, "confirm": 2,
        }
        for case in rows:
            if len(case.supplied) < len(case.required):
                assert case.expected()["action"] == "clarify"
            elif case.confirmation_required and not case.confirmed:
                assert case.expected()["action"] == "confirm"
            else:
                assert case.expected()["action"] == "execute"
