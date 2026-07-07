# Round 3 — Contributions and Design Goals

**Date:** 2026-07-07

## What was checked

Contributions list and design requirements R1-R3 against idea-quality-checklist.md Section 3.

## Findings

1. **C3 is compound (Important):** Packed methodology + 3 RQ results into one bullet. Checklist says each item should be one sentence.
2. **C2 is artifact-first (Important):** "We implement this model as a Rust CLI..." leads with implementation, not what the system enables.
3. **R1-RQ mapping implicit (Minor):** No RQ explicitly references R1. The coverage of 15 families validates R1 but isn't labeled.
4. **Missing dimensions in contributions (Minor):** Motivation promises failure/safety/quality but contribution text only says "hidden labeled problems."

## What was changed

### C2 (lines 140-144): Lead with what system enables
- Before: "We implement this model as a Rust CLI with pluggable intent recognition, four built-in views, and output formats..."
- After: "A profiler that realizes this model with pluggable intent recognition (regex rules, local LLM tagging, unsupervised clustering)..."

### C3 (lines 145-154): Decompound + add explicit label types
- Removed "On 325 real sessions" lead-in, compressed to single-sentence methodology + headline numbers
- Added explicit label types: "(failure, safety, redundancy, and human-task boundaries)"

### RQ1 (line 498): Add R1 reference
- Added "validating R1" after "without type-specific objects"

## Remaining concerns

- C3 is still longer than ideal (methodology + three RQ headline numbers). Acceptable for a workshop/short paper where space is tight.
