PASS

Both blocking defects are closed:

- Any non-`complete` matrix cell forces `mixed_or_inconclusive` before superiority/parity evaluation.
- Only atomic, hash-tagged corrected-v4 checkpoints are resumable. Intermediate obsolete scoring is isolated under `attempt-1/`, post-call correction resumes without another model call, and preflight supports three numbered attempts with mandatory repair notes after attempt 1.

Corpus hashes, model/reasoning, prompt, budgets, 18-cell matrix, repetitions, scoring, bootstrap, and parity thresholds remain unchanged. No files edited.