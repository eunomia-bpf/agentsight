# Semantic Flamegraph Paper Draft

Build figures from the current artifact:

```bash
python3 docs/visexp/paper/make_figures.py
```

Build the Chinese LaTeX draft:

```bash
cd docs/visexp/paper
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

The draft intentionally does not claim completed user-study or live exact
AgentSight capture evidence. Those remain gated by `docs/visexp/CLAIM_VERDICT.md`.
