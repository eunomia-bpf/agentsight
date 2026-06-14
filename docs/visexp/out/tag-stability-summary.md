# Tag Stability Smoke

This smoke test uses raw session fragments locally but commits only hashes, tags, and counts.
It is evidence for C7 syntax/repeated-run stability, not human semantic adequacy.

## Metrics

- fallback: 24 fragments, 100.0% exact-stable, 8.333% generic outputs, 0 invalid outputs.
- llama: 24 fragments, 100.0% exact-stable, 16.667% generic outputs, 0 invalid outputs.
- fallback vs llama: 0.0% modal exact match over 24 common fragments.

## Claim Gate

- Smoke verdict: smoke_supported.
- C7 remains partial until manual adequacy labels and larger repeated-model runs exist.
