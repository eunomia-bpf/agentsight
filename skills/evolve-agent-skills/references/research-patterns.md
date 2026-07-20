# Research Patterns for Skill Evolution

These works motivate design patterns; they do not replace project-specific evaluation.

## Reflection and Experiential Memory

- [Reflexion](https://arxiv.org/abs/2303.11366) stores verbal reflections in episodic memory to improve later trials without updating model weights.
- [ExpeL](https://arxiv.org/abs/2308.10144) gathers experiences, extracts natural-language insights, and recalls insights and examples at inference time.

Use this pattern for compact lessons. Its main risk is turning a plausible self-explanation into an unverified rule. Require outcome linkage and cross-task evidence.

## Skill and Workflow Libraries

- [Voyager](https://arxiv.org/abs/2305.16291) builds an executable skill library and improves programs using environment feedback, execution errors, and self-verification.
- [Agent Workflow Memory](https://arxiv.org/abs/2409.07429) induces reusable workflows from trajectories and selectively retrieves them for later tasks.

Use this pattern when a repeatable procedure is compositional and retrieval can be scoped. Keep project facts local and test negative-trigger cases to avoid overgeneralization.

## Search, Self-Modification, and Archives

- [Automated Design of Agentic Systems](https://arxiv.org/abs/2408.08435) uses a meta-agent to program new agents based on an archive of prior discoveries.
- [A Self-Improving Coding Agent](https://arxiv.org/abs/2504.15228) lets an agent edit its own agent code and selects improvements using coding benchmarks.
- [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954) modifies agent code, empirically validates candidates, and retains a diverse archive instead of one irreversible lineage.

Use this pattern only with a trustworthy evaluator, held-out tasks, preserved baselines, sandboxing, and rollback. Search amplifies evaluator flaws as readily as real capability.

## Agent-Skill and Eval Engineering

- Anthropic's [Agent Skills guidance](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) recommends beginning with representative evaluations and observed capability gaps.
- Anthropic's [agent eval guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) distinguishes tasks, trials, graders, and transcripts; it recommends multiple grading layers and reading trajectories to verify that graders measure the intended behavior.

Use representative tasks, several trials for stochastic agents, outcome grading plus trajectory inspection, and explicit regression sets.

## Product Implementations

When the full global skills repository is available, compare its pinned sources under `third_party/`:

- `agent-skills` and `superpowers` for production skill structure, automatic triggering, composability, and behavior testing;
- `langmem` for hot-path versus background memory extraction and consolidation;
- `skillopt` and `evoskill` for trajectory-driven candidate generation, held-out validation, candidate archives, and deployable skill artifacts;
- `agentevals` for trajectory graders and their dependence on explicit rubrics;
- `nvidia-skills` for skill cards, evaluation datasets, benchmark reports, security scanning, signatures, and publication governance.

Google's [Gemini CLI Auto Memory](https://github.com/google-gemini/gemini-cli/blob/7504259d720d1d909f67aed43ece64a72c51936e/docs/cli/auto-memory.md) is a particularly useful product boundary: it mines past sessions in the background but sends proposed memory patches and skills to a review inbox instead of modifying active state automatically.

Product adoption is evidence that a workflow is implementable, not evidence that its evaluator is valid for another task. Audit data coverage, privacy, approval boundaries, held-out splits, failure archives, and rollback semantics before absorbing a mechanism.

## Synthesis Used by This Skill

The safe reusable loop is:

`observe -> validate sources -> stratify -> extract failures -> propose smallest memory/change -> blind A/B eval -> promote/pilot/reject -> archive -> monitor/rollback`

The critical addition over naive self-reflection is an independent evidence path. A model's own explanation or a primed reviewer verdict is a hypothesis, not the promotion oracle.
