# Draft text for merge (apply to main.tex after compression codex finishes)

## 1. Data Availability statement (2-3 sentences, AAAI: inside content pages or clear supplement pointer)

Exported source-linked rows, the 120-question conformance benchmark with
expected answers, and all analysis code are released in the anonymized
repository (link on OpenReview). Raw native session records contain private
prompts and filesystem paths and are not redistributable; every reported
statistic is recomputable from the released rows without them.

## 2. Intro framing sentence (tighten "progress" construct; keep descriptive stance)

Insert after the first abstract/intro occurrence of the progress question, one sentence:

We use "progress" strictly in the descriptive sense of this paper: whether
observed activity consolidates into persistent, revisited, and
validation-associated artifacts — not as a judgment of outcome quality,
correctness, or developer productivity.

## 3. Merge checklist (from merge-spec.md)

- [ ] final-HEAD rerun numbers landed (if changed)
- [ ] Data Availability paragraph inserted
- [ ] framing sentence inserted
- [ ] extensions results → supplement + ≤1 line each in main
- [ ] compile: main ≤9pp with refs-only on 8-9 if that long; supplement compiles; no undefined refs
- [ ] commit + push
