# Independent Outer Audit

**Gate:** REVIEW  
**Verdict:** **PASS**  
**Must-fix:** none  
**Next state:** Step 0026 EXPERIMENT / paper-value admission; no candidate is
currently authorized

## Closure Audit

The complete Step 0025 result is valid and sufficiently reviewed. The fixed
two-population verdict is MIXED: OSWorld-Human decreases and CodeTraceBench
increases. Rejecting the candidate and retaining Step 0024 is therefore the
only authorized release decision.

The five implementation, test, and evaluator files touched by the candidate
have zero diff against the Step 0024 commit. The restored release passes its
complete Rust tests, formatting, Clippy, optimized build, Python compilation,
and diff checks. The remaining changes are only this timestamped report and
concise history/frontier updates. The paper, exact thesis, four RQs, story,
authoritative submodule, branch, and global skills are unchanged. WRITE's
no-change disposition is correct.

## Rejected Next-Candidate Shortcut

Do not select Step 0024 versus Step 0025 according to the sign of the learned
cross-action NPMI cutoff. NPMI zero has a real independence interpretation, but
the current evidence does not identify a general mechanism:

- every OSWorld-Human fold has a positive cutoff and favors Step 0024;
- CodeTraceBench has a negative cutoff and favors Step 0025;
- the sign is therefore completely confounded with population identity; and
- after observing both results, the rule deterministically chooses each
  population's winner and has almost no remaining falsifiability here.

This would be an indirect benchmark selector, not an authorized scientific
improvement.

## Exact Next Decision

Step 0026 may inspect the retained raw decisions for one common error mechanism
that is stated before candidate scoring, applies independently of benchmark
identity, and can change a paper-level RQ3 answer. It may not implement the
sign-based shortcut, invent a benchmark, rename the algorithm, modify the paper
story, or search cutoffs and local-rule variants. If no common mechanism can be
admitted, record a no-admit decision and close this refinement branch rather
than keep switching rules.

Non-blocking maintenance debt—an overlong canonical evaluation file and an
absent optional progress-check script—does not belong in this scientific step
and does not authorize changes to skills, AGENTS instructions, paper, or code.
