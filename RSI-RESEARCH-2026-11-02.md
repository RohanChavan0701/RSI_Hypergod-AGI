# RSI research and development brief

Research date: November 2, 2026. Project: RSI_Hypergod-AGI / HGI.

## Scope and evidence

This is a targeted literature review, not a systematic review or independent replication. Primary papers, author project pages, official engineering blogs, and a public code release were consulted. For selected papers, the methods, evaluation, cost, or limitations sections were examined in addition to abstracts. Code release availability does not establish reproducibility; external repositories were not installed or executed. Recent arXiv results should be treated as reported findings, not established consensus. Dates below identify the cited release or publication, not necessarily the earliest version of an idea.

The central distinction is between improving an answer, improving a persistent agent, and improving the procedure that produces future agents. Only the last directly tests improvement of the improvement mechanism. None establishes unlimited improvement or an intelligence explosion.

## Findings from papers and author materials

### 1. Darwin Goedel Machine (May 2025)

The system retains an archive of agent variants and uses evaluated code modifications to extend it. Its important design contribution for us is the reuse of diverse intermediate agents as stepping stones. Task improvement and self-modification are closely aligned in coding, which complicates extrapolation to other domains. HGI should compare an archive against both a single incumbent and independent best-of-N search.

Source: [Sakana author article, paper and code links](https://sakana.ai/dgm/).

### 2. AlphaEvolve (May 2025; impact update May 2026)

Evolutionary program search is coupled to executable evaluators, with applications reported across algorithms and computing infrastructure. This is an engineering argument for investing in reliable scoring before sophisticated proposal generation. Algorithm optimization under a well-defined objective is a narrower setting than general self-improving agency.

Sources: [original author article](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/), [2026 impact update](https://deepmind.google/blog/alphaevolve-impact/).

### 3. GEPA (July 2025)

Reflective prompt evolution uses execution feedback and a Pareto-oriented search process. It is an essential baseline for a system that claims benefits from learning textual instructions. HGI must separate the value of structured governance from the value of simply generating and evaluating better prompts. Reimplementing a rough approximation should be labeled as such.

Source: [paper](https://arxiv.org/abs/2507.19457).

### 4. Agentic Context Engineering (October 2025)

ACE treats context as an evolving playbook with incremental updates and modular generation, reflection, and curation. Structured persistent memory is therefore prior art. For HGI, the research question is whether activation boundaries, empirical admission, and retirement improve outcomes beyond a competent playbook baseline, including their extra cost.

Source: [paper](https://arxiv.org/abs/2510.04618).

### 5. ReasoningBank (author blog April 2026)

ReasoningBank distills generalizable lessons from successful and failed experiences into structured memory. The author blog describes retrieval, extraction, and append-based storage, leaving richer consolidation as future work. This makes it a particularly relevant comparison for HGI's governed consolidation. Do not assume an LLM's self-judgment is ground truth; measure its disagreements with executable outcomes.

Source: [Google Research article, with paper and code links](https://research.google/blog/reasoningbank-enabling-agents-to-learn-from-experience/).

### 6. MemRL (January 2026)

The work studies runtime reinforcement learning over episodic memory while keeping the language model frozen. It motivates learning which experiences are useful rather than ranking memories solely by semantic similarity. HGI could test outcome-informed retrieval against its existing activation path without changing the entire system at once.

Source: [paper](https://arxiv.org/abs/2601.03192).

### 7. Meta-Harness (March 2026)

An agentic proposer searches harness code while inspecting prior source, traces, and scores through a filesystem. The paper uses evaluation-budget comparisons and a best-of-N control. One discovered classification harness retrieves evidence that challenges an initial prediction. This suggests preserving accessible experimental artifacts and testing counterexample retrieval. Filesystem history access itself should be ablated against concise summaries.

Sources: [full paper](https://arxiv.org/html/2603.28052v1), [author project and artifact links](https://yoonholee.com/meta-harness/).

### 8. HyperAgents (March 2026)

Task and meta agents are jointly editable; the mechanism generating improvements can evolve. Its improvement@k experiment holds a meta agent fixed while measuring how well it generates improved task agents. That is a valuable way to distinguish task skill from improvement skill. The cost appendix estimates tens of millions of tokens for substantial runs, reinforcing the need for a smaller pilot. Broad generality remains a hypothesis beyond the evaluated settings.

Sources: [full paper](https://arxiv.org/html/2603.19461v1), [public implementation](https://github.com/facebookresearch/HyperAgents).

### 9. AIDE squared (September 2026)

The paper reports an eight-day trajectory with seven accepted rewrites and tests transfer on external benchmarks. It explicitly distinguishes private scores used for selection from benchmarks that never affected selection. HGI should adopt that distinction: a rising selection curve is evidence of successful selection, not by itself evidence of generalization or accelerating improvement.

Source: [full paper](https://arxiv.org/html/2609.26457v1).

### 10. Harness squared (October 2026)

The framework combines task-level harness refinement with accumulated experience about harnessing. Contrastive propose/probe/compose steps address settings lacking ground-truth feedback. Its limitations discuss the added cost of refinement. Useful for candidate generation, but subjective probing should not replace executable final evaluation where that is available.

Source: [full paper, including limitations](https://arxiv.org/html/2610.14224v1).

### 11. Memento 3 (October 2026)

Natural-language world-model rulebooks are compiled into executable models and checked against observed transitions. This motivates a later HGI experiment in executable lessons. Fidelity to observed transitions does not establish correctness on unobserved states; independent transfer tests are still required.

Source: [paper](https://arxiv.org/abs/2610.11794).

### 12. Are Self-Evolving Agents Continual Learners? (October 2026)

The study evaluates evolving agents under topic, workflow, and domain drift. Its analysis identifies both destructive shared edits and retrieval collisions between similar queries requiring conflicting behavior. This directly motivates testing HGI's activation conditions and exclusions. Importantly, a relevance threshold alone cannot resolve conditions that are semantically similar but operationally incompatible.

Source: [full paper, especially section 4.4](https://arxiv.org/html/2610.25858v1).

### 13. REUSE: Which Self-Improvements Should We Trust? (September 2026)

The paper studies adaptive benchmark reuse and proposes risk-controlled promotion. Its guarantees depend on the formal protocol and assumptions; adding ordinary confidence intervals to HGI would not reproduce them. Before adopting it, audit the mathematical assumptions against our task sampling, candidate feedback, and stopping rules. Keep an untouched external test distribution regardless.

Source: [full paper](https://arxiv.org/html/2609.33180v2).

### 14. The Winner's Curse in LLM Self-Improvement Loops (October 2026)

The study distinguishes selection noise, repeated testing, and adaptive feedback. Reported selection-to-test gaps make a strong case against accepting the largest observed gain on a tiny sample. Its tested acceptance rules do not solve adaptive reuse in general. Our evaluation should log all attempts, rejected changes, and the total selection budget.

Source: [full paper](https://arxiv.org/html/2610.09239v1).

### 15. EvalResearchBench (October 2026)

The benchmark asks agents to create executable evaluators under resource limits and measures agreement with target benchmarks. It motivates validating a cheap screening suite before trusting it to filter HGI candidates. A screen should be evaluated by whether it ranks or accepts candidates correctly, not merely by its own average task accuracy.

Source: [full paper](https://arxiv.org/html/2610.04184v2).

## Engineering blogs: useful practice, different evidence

Anthropic's [long-running agent article](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) describes initialization, incremental work, and persistent handoff artifacts. These are useful reliability patterns, not demonstrations of recursive improvement. Its [managed-agent architecture article](https://www.anthropic.com/research/managed-agents) argues for stable interfaces and reconsidering harness workarounds as models change. For HGI, keep durable experiment state and version lessons against model and environment identity; test whether an old workaround is still useful after a model swap.

## Assessment of this repository

Inspected surfaces include README.md, spec.md, carry-forward.md, hgi/consolidate.py, and function inventories in hgi/reviews.py, hgi/latches.py, and hgi/evolution.py. This is not a line-by-line audit.

Existing strengths: typed records, evidence anchors, activation guards, role-separated consolidation, supersession and retirement, and experiment reporting. Existing gaps: controlled causal evidence for individual lessons, a validated admission protocol under repeated selection, and a benchmark separating task improvement from improvement-procedure improvement. Different role contexts do not guarantee statistically independent judgments.

Recorded local validation is 727 passed, 63 failed, 1 skipped on native Windows. Build artifacts and CLI startup succeed; full experimental portability does not. Repository notes include mixed results, saturated tasks, and evaluation defects. Earlier real-model runs are historical repository reports, not experiments reproduced during this research pass.

## Proposed contribution

Hypothesis: scoped, experimentally evaluated updates can reduce harmful adaptation under workflow drift while preserving useful learning per unit of total compute. A second hypothesis is that evolution of the consolidation procedure improves learning efficiency on fresh streams.

These are proposed hypotheses, not established novelty claims. Existing work covers almost every individual component. A contribution would require a clear new method or benchmark, strong comparisons, and convincing results.

### First experiment: conflicting workflows

Build paired API tasks with similar wording but different action preconditions: complete arguments require immediate execution; missing arguments require clarification; irreversible operations require specified confirmation; retryable failures differ from permanent failures. Give the agent observable conditions sufficient to distinguish them. Avoid solving the benchmark by exposing an artificial task-family label unavailable in deployment.

Alternate workflow blocks, then revisit earlier blocks and evaluate unseen combinations. Add a second domain, such as SQL schema changes, only after the first experiment is reliable. Split by templates, schemas, and environment versions rather than random paraphrases alone.

Compare no memory, nearest-neighbor memory, structured playbook memory, prompt optimization, current HGI, and HGI with empirical admission. Run full baselines on a pilot first; use a smaller fixed subset for expensive repetitions only with explicit justification. Match actor models and total resource budgets, including proposal, judge, consolidation, and evaluation calls. Include extra-inference and best-of-N controls.

Measure task success, previous-block regression, harmful activation rate, rejection of actually useful lessons, cumulative reward over experience, tokens, latency, and cost. Evaluate abstention: no applicable lesson is a valid retrieval outcome. Report per-family results and uncertainty across independent runs; tasks sharing a template are not independent observations.

### Second experiment: isolate improvement skill

Save the original and evolved consolidators. Hold each fixed and give both the same starting task agent, fresh experience streams, and equal budgets. Measure the performance of descendants selected on validation and evaluated on untouched tasks. Reinitialize task memory to prevent carried-over answers from masquerading as a better learning algorithm. Evaluate several streams and models before claiming transfer.

### Admission protocol

Use paired interventions with and without a lesson on controlled task instances. Re-running recorded outputs cannot estimate how a model would behave with changed context; new model rollouts are needed for that comparison. Repeat stochastic runs and distinguish measurement uncertainty from adaptive-selection bias.

Separate development, candidate selection, and final testing. Freeze final candidates before external testing; never feed final-test results back into the same reported run. Define acceptance constraints before the pilot ends. If claiming a formal guarantee, implement and validate an appropriate sequential protocol rather than improvising one.

## Implementation sequence and exit criteria

1. Reproducibility: choose Linux as the initial reference platform, resolve harness defects, freeze task manifests and model configuration, and verify baseline scoring. Exit: repeatable baseline runs with recorded failures and costs.
2. Measurement: add candidate and evaluation records, paired runs, and retention reports. Exit: known helpful and harmful seeded changes are distinguished without using final-test feedback.
3. Scoped adaptation: test empirical lesson admission and retirement against current HGI. Exit: a held-out benefit at a declared compute budget with quantified retention trade-offs.
4. Meta-evolution: allow bounded consolidation or retrieval changes while keeping evaluation and resource accounting fixed. Exit: an evolved improver outperforms the original on fresh streams under matched budgets.
5. Executable lessons: evaluate only after the above mechanisms work. Exit: verified artifacts improve new tasks beyond prose lessons at comparable total cost.

Suggested new modules are hgi/interventions.py for paired rollouts, hgi/promotion.py for acceptance policy, and hgi/retention.py for capability tracking. Reuse existing Store, registry, experiment, lineage, and projection facilities. Do not build a parallel orchestration stack before these experiments require it.

## What would change the recommendation?

If simple retrieval performs equally well, simplify HGI. If retention checks consume more value than they preserve, reserve them for high-impact changes. If an evolved consolidator fails on new streams, describe the result as task-specific optimization. If gains disappear against compute-matched controls, the result concerns inference allocation rather than learned improvement. Publish negative and null results alongside successful trajectories.

The next useful deliverable is a reproducible conflicting-workflow pilot with explicit baselines and cost accounting. A larger architecture is justified only by failures that this pilot exposes.
