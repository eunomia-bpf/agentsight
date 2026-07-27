# WRITE task: integrate step-0090 multi-measure results

Edit EXACTLY ONE file: docs/paper/main.tex in
/home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
No git commands. Bilingual %-comments. Verify every number against
docs/tmp/build-and-evaluate/step-0090-20260727T023000-0700/experiment-001/results.md
before use. Keep thesis x3, RQ titles, all existing numbers.

1. RQ1 Git paragraph: where the paper reports the diagnose-authentication
   subtree at 21.47% of operations and 46.15% of tokens, extend to the
   three-measure ladder: the same unchanged hierarchy replays under an
   elapsed-time width (3,982 defined seconds, exactly conserved; all 489
   evidence rows mapped) and the subtree holds 37.47% of elapsed time —
   count 21.47%, time 37.47%, tokens 46.15%: the measure alone moves the
   subtree's attributed share by more than a factor of two.
2. Case Study 3: add 2-3 sentences: the same self-profile hierarchy also
   replays under FILE-READ (737), FILE-WRITE (31), and NETWORK-target (61)
   widths with exact conservation, and each created file appears as a
   drilldown leaf beneath the operation that created it. Then ADD one
   figure: docs/tmp/build-and-evaluate/step-0090-20260727T023000-0700/experiment-001/selfprofile.file-write.png
   as a figure* (width .97\linewidth) captioned as the FILE-WRITE view
   with semantic operation -> LLM -> tool -> exact write target, label
   fig:selfprofile-write, referenced from the new sentences. (Copy the
   PNG into docs/visexp/out/r221-pprof-renderer-v1/ first so the include
   path matches the other figures.)
3. Implementation or RQ1 (one sentence, your judgment on placement): real
   AgentSight eBPF recordings replay the same way — the R114 population's
   1,520 process/file effects fold under task responsibilities through
   the recorded wrapper tool with exact conservation, demonstrating the
   system-effect layer end to end.
4. Check the abstract/intro multi-measure phrasing still matches (count,
   time, tokens now all demonstrated; file/network demonstrated on the
   self-profile) — adjust at most one clause if a claim can now be
   stated as shown rather than supported.

Validate: latexmk clean, zero errors, thesis x3, cite keys unchanged.
write-report.md here with before/after and the verified numbers.
