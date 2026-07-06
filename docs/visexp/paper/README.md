# agentpprof Operation-Stack Paper Draft

The current Chinese draft is no longer the older AgentFlame
session/prompt-centric paper. It is the `agentpprof` operation-stack paper:
the only core abstractions are `operation` and `operation stack`, while
prompt, session, tool call, process, syscall, GUI action, safety label, plan,
and subagent are operation shapes or operation fields.

The legacy figure builder is kept for historical AgentFlame artifacts:

```bash
python3 docs/visexp/paper/make_figures.py
```

Build the current Chinese LaTeX draft:

```bash
cd docs/visexp/paper
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

The R396 smoke gate exercises this build path without dirtying the source tree:
it builds the English paper in a temporary copy, builds this Chinese draft into
a temporary output directory, and records the final logs under
`docs/visexp/out/paper-build-smoke-r396/`.

The draft intentionally does not claim completed user-utility evidence or fully
unsupervised boundary discovery. Those remain future gates in
`evaluation-claims-setup.zh-CN.md` and `docs/evaluation.md`.
