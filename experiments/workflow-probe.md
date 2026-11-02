# Conditional workflow probe

This is an action-selection benchmark, not an API execution benchmark. The
existing Task and family interfaces expose 12 cases in each of
`workflow-experience`, `workflow-selection`, and `workflow-test`.

The splits use different operation names and prompt templates. All share an
explicit conditional decision contract; this measures condition following and
interference from future memories, not discovery of a hidden environment rule.
There are no scripted Task policies: the generic agent stub cannot establish
performance on these tasks. The separate conditional reference is an oracle
sanity control, not a learned policy.

Run offline checks from the repository in PowerShell:

```powershell
$env:PYTHONUTF8 = "1"
uv run pytest tests/test_workflow_drift.py
uv run python -m suite.workflow_probe
```

The scripted report measures action labels only. Always-clarify scores 50%
overall, always-execute 33.3%, and always-confirm 16.7%; all score 33.3%
balanced action accuracy. The conditional reference scores 100% by construction.
Actual task grading additionally checks preservation of supplied arguments,
the missing-argument list, and the absence of unexpected fields.

Missing required arguments take precedence over confirmation. Once arguments
are complete, unconfirmed operations requiring confirmation must ask for it;
already confirmed or unrestricted operations can execute. Each operation has
all six combinations, so operation identity alone does not determine the label.

## Next experiment

1. Configure a real actor model and a total pilot spending cap. Record model,
   sampling settings, task manifests, prompts, and all call costs.
2. Measure a no-memory baseline on experience and selection only. Check class
   scores and inspect format failures separately from decision failures.
3. Add controlled overbroad lessons such as always asking before action; measure
   degradation on paired tasks. These are seeded interference tests, not learning.
4. Compare scoped lessons with unscoped lessons under matched context budgets.
5. Integrate consolidation only after the interference measurement works.

The test split has been inspected to validate the grader and is public. It is
not a secret final evaluation set. Before any research claim, freeze the method
and create a fresh external evaluation with new schemas and independently
written templates; do not adapt the method to final-test outcomes.

This initial probe is deliberately small and explicitly instructed. A ceiling
result is plausible. If all conditions saturate, extend the task mechanics
before spending on repeated evolution runs. Do not interpret the reference
control or successful unit tests as improvement by HGI.
