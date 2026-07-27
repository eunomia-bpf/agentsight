# Independent P1-v2 Preregistration Review

## Final review

**Verdict: PASS.**

The review was strictly read-only.  It did not execute any held-out runner
subcommand, discover/select a corpus, generate an oracle or projection, or
open a result.

No scientific-validity or executability blocker remains:

1. The scientific contract changes only project quota
   \(s_i=\min(12,e_i)\), the hard minimum \(e_i\ge8\), and the question counts
   mechanically derived from those quotas.  The v1 seed, cutoff, exclusions,
   semantic grammar, oracle, edge keys, scoring, one-attempt rule, and paper
   decisions remain unchanged.
2. The frozen formula
   \(F=\lfloor30S/72+0.5\rfloor,\ Q=4F\) and Hamilton allocation are
   deterministic and outcome-independent.  Exhaustive static checking of all
   \(5^6=15{,}625\) allowed selected-count vectors found valid integer
   allocations summing to \(F\), never exceeding the five frozen templates
   per family.  Fixed manifest order breaks equal remainders, and allocation
   occurs before edge, answer, or projection generation.
3. The v2 checker differs from the upstream independent v4 checker only in
   the proportional question-ID adapter and its integrity checks.  It still
   recomputes all 20 templates per project plus every edge and call/status
   row; it rejects duplicate/faulty IDs and requires the frozen \(Q\).  The
   runner separately requires checker `questions=Q`,
   `recomputed_templates=120`, and the frozen checker hash.
4. Reuse of the v1 fixture is integrity-gated by the v1 attempt hash
   `83879d59...`, runner hash `6df7a7ee...`, terminal/pass status, and the
   unchanged production/checker/fixture hashes.  The registered measurement
   script is loaded read-only from revision `73120b00...` and matches
   `e50adb5c...`; the newer working-tree plotting-label change is neither
   accepted nor restored.
5. The runner enforces `freeze → build → preflight → full`.  Build requires
   the completed unique freeze.  The freeze manifest seals every frozen
   source, workspace blob, spec, oracle, and freeze file; build records that
   manifest hash in the code seal, and preflight/full revalidate every listed
   file.  A completed scientific negative does not block the full run.
6. All three historical exclusion archives are rebuilt after manifest/source
   hash and size validation.  Source hash, semantic root, and native call ID
   overlap must all be zero.  The edge ledger is a multiset including
   `display_path`, with separate exact gates for session order, attempted
   edges, confirmed-effect edges, and edge-call status overall, by project,
   and by represented vendor.
7. The old 60/60 remains separate repair-corpus evidence.  The new \(2F\)
   B+C denominator is reported without pooling or rescaling.

Final seals reviewed:

- runner SHA-256:
  `b40eab3e6fd16a51d0edacbfff3f3c421ca9e0795dbc91865ae50115206e7c19`;
- v2 checker SHA-256:
  `8942a0f8c22681adb9fac993a611747c4d8e59de7aa64d227f3fee661743c234`;
- project manifest SHA-256:
  `2de529d002815aefa74b1b8f8164ddf3b78b1e2f8e9e02214d43a9598f49368a`.

The transient Python bytecode created by a root-agent import-only static check
was removed before freeze.  At approval, v2 contained no attempt, corpus,
oracle, projection, or score output.
