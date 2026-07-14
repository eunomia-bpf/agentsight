# Round 10 — Citation Verification

- **Timestamp:** 2026-07-14 05:29 -0700
- **Skill:** `check-paper-citations`
- **Reviewer:** fresh independent subagent, read-only
- **Target:** complete `docs/paper/main.tex` and `docs/paper/references.bib`
- **Disposition after fixes:** PASS

## Final counts

- **BibTeX entries:** 55
- **Active cited entries:** 45
- **Unused retained entries:** 10
- **Visible `\\cite` commands:** 39
- **Cited-key occurrences:** 64
- **Unique cited keys:** 45
- **Complete annotation blocks:** 55/55
- **`REAL: unverified`:** 0
- **Hallucinated citations:** 0
- **Ghost citations:** 0
- **Retraction risks found:** 0
- **Double-blind identity leaks found:** 0

## Mechanical verification

The mandatory `verify_bib.py` pass initially exposed stale `% STATUS: unused`
markers, shortened venue strings, one broken OSWorld URL, and public-index lag
for 2026 papers. Primary sources were used to resolve the records. The final
mechanical run checked all 45 active entries and returned:

- metadata/URL errors: 0;
- warnings: 2 title-pattern heuristics (`A Comprehensive`) on known-real
  API-Bank and GUIOdyssey papers;
- exit status: PASS.

The OSWorld record required a substantive metadata fix: the author list and
official NeurIPS URL were wrong. Both now match the official proceedings record,
and the DOI was added.

## Published-version upgrades

Six cited preprints were replaced by their official conference versions without
changing any cite key or paper claim:

- AgentRewardBench — COLM 2025;
- WebLINX — ICML 2024, PMLR 235:33007--33056;
- AgentTrek — ICLR 2025 Spotlight;
- $\tau$-bench — ICLR 2025;
- AndroidControl — NeurIPS 2024 Datasets and Benchmarks Track;
- ScaleCUA — ICLR 2026.

AgentFixer retains its official AGENT@ICSE publication, and AgentProcessBench
retains the KDD 2026 venue and ACM DOI identified by its official paper. Stable
venue abbreviations are used in the rendered bibliography, while URLs, DOI,
year, authors, and annotation notes retain source identity.

## Source-fidelity fixes

- Replaced the OSWorld-Human repository-organization author with Reyna
  Abhyankar, Qi Qi, and Yiying Zhang, restored the complete paper title and
  arXiv identifier, and retained the repository as the artifact URL.
- Converted the stale `claudecode` and `osworld` `% STATUS: unused` records into
  active, fully annotated citations.
- Added complete verification blocks to all ten genuinely unused records rather
  than deleting them.
- Updated `USED_FOR` descriptions for AgentRewardBench, SATraj-OS,
  OSWorld-Human, AgentNet, and OpenCUA.

## Claim--citation alignment fixes

Three inaccurate cite contexts were repaired:

1. The Introduction now distinguishes expensive manual inspection from the
   separate evaluator pass required by per-trajectory LLM judging.
2. The Background describes OpenTelemetry and OpenInference as standards that
   represent supplied span attributes, not as aggregation engines.
3. Related Work separates step/span localization, validation with root-cause
   analysis, and diagnostic taxonomy/audit work.

## Missing-citation fixes

Five gaps were resolved:

- removed the unsupported `thousands to millions` magnitude instead of adding
  a weak citation;
- added the official OpenAI Codex repository at first mention;
- added the official llama.cpp repository;
- added Salton and Buckley's primary TF-IDF paper;
- added MacQueen's primary K-Means paper.

Thus, four citations were added and one unsupported magnitude was removed.

## Verification

- `verify_bib.py`: PASS, 45 active entries, 0 errors
- BibTeX + pdfLaTeX: PASS
- PDF length: 8 pages
- Undefined citations/references: none
- Overfull boxes: none
- `git diff --check`: PASS
- No Git operation performed
- Canonical paper submodule untouched at `7f80c433c9555317a2aa45a78d0ff93518f4c12c`
