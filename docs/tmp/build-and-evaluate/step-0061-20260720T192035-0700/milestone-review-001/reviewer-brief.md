# Independent Full-Paper Review Brief

## Scope

Review the complete current paper rooted at `docs/paper/main.tex`, including
every title, abstract, section, subsection, claim-bearing figure and table,
bibliography entry used by the text, and appendix or checklist needed to judge
the main paper. The target is AAAI 2027. The paper makes both systems and AI/ML
claims, so apply both standards and the stronger cross-domain causal-chain bar.

Remain read-only. Do not edit any file. Do not run Git. Do not read
`docs/user-instruction.md`, `docs/idea-story.md`, `docs/evaluation.md`, prior
reviews, experiment reports, Git history, or proposed fixes. They would prime
the scientific review.

## Required Sequence

1. Read the complete paper before searching externally. Record a blind
   paper-only assessment: perceived problem and stakes, challenged belief,
   simple principle, mechanism, contributions, all explicit RQs and their
   answers or missing evidence, strongest reject hypotheses, and every
   load-bearing claim requiring verification.
2. Search externally for evidence against as well as for the paper. Open and
   verify primary papers, official repositories, benchmark/dataset artifacts,
   and official documentation. Cover closest same-claim work, agent tracing and
   observability, profiling and flame graphs, task/process mining, hierarchical
   agent trajectory representations, semantic segmentation or clustering,
   stronger baselines, standard metrics, contradictory evidence, and the real
   existence of the challenged belief. Search both systems and AI communities.
3. Reread the complete paper and all claim-bearing figures/tables after the
   search. Reassess novelty, mechanism, evaluation construct, cross-domain
   causal chain, consistency, real-world relevance, limitations, and AAAI
   readiness.
4. Return one detailed Markdown review with: reviewer/model disclosure;
   external sources and links; blocker/major/minor/nit findings; strongest
   source-grounded reject argument; strongest evidence for the paper; largest
   scientific/evidence gap; largest writing-only gap; global inconsistencies;
   and a final accept/reject-style verdict.

## Algorithm And Research-Taste Questions

Judge the current semantic-stack algorithm independently of implementation
volume:

- Is the paper's main semantic object genuinely a task-responsibility stack,
  or does it remain a field grouping of system logs?
- Can the method recover variable-depth concrete task and nested-subtask
  structure, followed by phase/strategy, semantic action, operation object,
  and result?
- Are agent, model, session, prompt, tool, command, path, and status kept as
  metadata/evidence rather than persistent task frames?
- Is label-free recurrence a simple, principled mechanism connected to the
  paper's profiling insight, or a heuristic whose success on flat stage labels
  does not establish task-semantic hierarchy?
- What is the simplest non-equivalent algorithmic direction that could close
  the largest paper-level gap without changing the thesis or RQs? Do not
  recommend another prompt wording, cutoff, depth cap, contraction, or lexical
  cleanup.

State the paper's principle in one plain sentence, the real belief it
challenges, the strongest alternative explanation, the largest ambitious claim
worth defending, and whether the work is simple-but-deep,
complicated-but-shallow, or incomplete-but-promising. Prefer stronger
mechanism and evidence over claim narrowing.
