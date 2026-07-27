# WRITE report: step-0090 multi-measure integration

## 1. Main issues

Before this task, RQ1's repeated Git case showed only operation-count and token
widths, Case Study 3 showed only operation-count and token self-profiles, and
the paper did not state the retained AgentSight system-effect replay. The
abstract described additive resource views generically even though step-0090
now demonstrates count, time, token, file, and network views.

## 2. Revision strategy

The revision keeps the thesis, four RQ titles, citations, story, and all
existing numerical claims. It makes four bounded changes in
`docs/paper/main.tex`, each with a Chinese `%` comment:

1. replace one abstract clause with the demonstrated count/time/token/file/
   network view list;
2. extend the RQ1 Git paragraph with the elapsed-time replay and three-measure
   attribution ladder;
3. add one RQ1 sentence for the real R114 AgentSight eBPF system-effect replay;
4. extend Case Study 3 with the conserved FILE-READ, FILE-WRITE, and
   NETWORK-target views and add the requested FILE-WRITE `figure*`.

The requested PNG was copied from step-0090 to
`docs/visexp/out/r221-pprof-renderer-v1/selfprofile.file-write.png`.

## 3. Before/after and verified numbers

| Location | Before | After |
|---|---|---|
| Abstract | Generic additive-resource-view capability | States that count, time, token, file, and network views replay fixed hierarchies into pprof-compatible profiles |
| RQ1 Git case | The subtree held 21.47% of operations and 46.15% of tokens | Adds all 489 mapped evidence rows, 3,982 exactly conserved defined seconds, and 1,492 subtree seconds (37.47%); the ladder is count 21.47%, time 37.47%, tokens 46.15%, so changing only the measure moves the attributed share by more than a factor of two |
| RQ1 system effects | No real-effect replay sentence | Adds the R114 population's 1,520 process/file effects folded under task responsibilities through the recorded wrapper tool with exact conservation |
| Case Study 3 | Operation-count and token self-profile only | Adds exactly conserved FILE-READ 737, FILE-WRITE 31, and NETWORK-target 61 widths; created files remain exact drilldown leaves below their creating semantic operation, LLM, and tool |
| Case Study 3 figure | No file-write figure | Adds a `.97\linewidth` `figure*` using `selfprofile.file-write.png`, captioned as the semantic operation → LLM → tool → exact write-target FILE-WRITE view and labeled `fig:selfprofile-write` |

Every added experimental number was checked directly against
`docs/tmp/build-and-evaluate/step-0090-20260727T023000-0700/experiment-001/results.md`:

| Step-0090 quantity | Verified value |
|---|---:|
| Git fixed evidence rows | 489 |
| Git defined elapsed mass, exactly conserved | 3,982 s |
| `diagnose authentication` subtree | 105 operations; 1,492 s |
| Subtree share by operation count | 21.47% |
| Subtree share by elapsed time | 37.47% |
| Subtree share by provider-reported tokens | 46.15% |
| FILE-READ target references, exactly conserved | 737 |
| FILE-WRITE target references, exactly conserved | 31 |
| NETWORK/domain target references, exactly conserved | 61 |
| R114 process/file effects, exactly conserved | 1,520 |

The count-to-token endpoint ratio is greater than two, supporting the wording
"more than a factor of two." The paper does not upgrade the FILE/NETWORK
target-reference views to kernel effects or claim inner-LLM-to-kernel lineage;
the R114 sentence remains at its recorded wrapper-tool granularity.

## 4. Validation and remaining risks

- Ran `latexmk -C main.tex` followed by
  `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` from
  `docs/paper/`; the clean build completed successfully.
- The final `main.log` contains zero LaTeX error, undefined-control-sequence,
  fatal-error, undefined-reference, or undefined-citation signatures.
- The fixed thesis occurs exactly three times.
- All four RQ title lines are byte-for-byte unchanged from the pre-edit
  baseline.
- The ordered citation-key sequence is unchanged.
- `fig:selfprofile-write` occurs once in the source and resolves in `main.aux`.
- The copied PNG is byte-identical to the step-0090 source, and the rebuilt PDF
  visibly contains the full-width FILE-WRITE flamegraph and its resolved
  caption/reference.
- No git command was run.

No task-scoped TODO remains. Existing nonfatal underfull-box warnings are
outside this writing task and do not affect the new figure or references.
