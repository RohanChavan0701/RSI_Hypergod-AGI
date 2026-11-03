# Conditional workflow probe

This is an action-selection benchmark, not an API execution benchmark. The
existing Task and family interfaces expose 12 cases in each of
`workflow-experience`, `workflow-selection`, and `workflow-test`.

## NVIDIA version-recall pilot

Run `python -m suite.workflow_pilot --provider nvidia --drift --recall --limit 4 --memory feedback`
with `NVIDIA_API_KEY` configured locally. Repeat with `--memory none` and
`--memory broad`, using a distinct `--out` path for each run.

| Condition | v1 correct | v2 correct | Total |
|---|---:|---:|---:|
| No memory | 0/2 | 2/2 | 2/4 |
| Stale v1 lesson on every request | 2/2 | 0/2 | 2/4 |
| Version-specific feedback | 2/2 | 2/2 | 4/4 |

Nemotron 3.5 Super VL received complete unapproved requests in the order
v1, v2, v2, v1. All three arms previously scored 4/4 when every request
included a worked example for each version. Removing those examples exposed
different failure patterns for the baseline and stale-memory arms. The
feedback arm uses a hand-authored mapping from versions to correct actions.
These four synthetic cases test retrieval of that mapping. Automatic lesson
generation and generalization to new workflows remain future experiments.

### Learning from graded feedback

The runner can infer a version-to-action mapping from the prior no-memory
run's grader labels. It rejects conflicting labels within a version. The
following command fits the mapping from the first run and evaluates it on
requests with new item identifiers.

```powershell
python -m suite.workflow_pilot --provider nvidia --drift --recall --limit 4 --offset 100 --learn-from .cache/nvidia-recall-none-01.json --out .cache/nvidia-learn-learned-01.json
```

| Condition | v1 correct | v2 correct | Total |
|---|---:|---:|---:|
| No memory | 0/2 | 2/2 | 2/4 |
| Stale v1 lesson | 2/2 | 0/2 | 2/4 |
| Mapping learned from grader labels | 2/2 | 2/2 | 4/4 |

Version is a programmer-selected input feature, and the evaluation changes
item identifiers while retaining the same template and two rules. This run
tests transfer to new inputs within the same workflow. Learning an activation
condition from competing features and generalizing to new workflows are open.

### Discovering which feature controls recall

Use `--discover-scope` with a graded drift run that records version,
operation, and destination. Each candidate field must cover both allowed
values and give one consistent action per value. The runner rejects
ambiguous evidence and overlapping training and evaluation item ranges.

On four NVIDIA training requests (items 200–203), the no-memory model
answered 2/4 correctly. The grader labels uniquely selected version over
operation and destination. With the learned mapping, NVIDIA answered
3/3 completed evaluation requests correctly (items 300–302). The fourth
request timed out. A retry timed out before producing a graded response.
This is a partial evaluation on the same synthetic workflow, with three
candidate features supplied by the experiment designer.

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
