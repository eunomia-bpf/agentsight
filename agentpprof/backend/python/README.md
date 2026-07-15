# Python Clustering Backend for agentpprof

This directory contains Python-based clustering backends for semantic tagging.
These are alternatives to the built-in regex tagger when you want to discover
natural groupings in your prompt distribution without predefined rules.

## Available Backends

### cluster_tagger.py (TF-IDF + K-Means)

Uses traditional NLP techniques to cluster prompts:
- TF-IDF vectorization for text representation
- K-Means clustering for grouping
- Automatic cluster count selection via silhouette score
- Keyword extraction for cluster naming

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic clustering

```bash
# Export prompts from agentpprof
agentpprof --project-root . --format json -o prompts.json

# Cluster and generate tag cache
python cluster_tagger.py --input prompts.json --output tags.json --show-info

# Use the tag cache with agentpprof
agentpprof --project-root . --tag-cache tags.json -o flamegraph.svg
```

### Auto-detect cluster count

```bash
python cluster_tagger.py --input prompts.json --output tags.json
```

The script will automatically find an optimal number of clusters (5-25) using
silhouette score.

### Manual cluster count

```bash
python cluster_tagger.py --input prompts.json --output tags.json --clusters 12
```

## When to Use Clustering vs Regex

| Approach | Best For |
|----------|----------|
| Regex (with agent iteration) | Production, CI, when you need stable/reproducible tags |
| Clustering | Exploration, discovering what categories exist in your data |
| LLM tagger | Complex prompts that need semantic understanding |

Clustering is useful as a **first step** to understand your prompt distribution
before writing regex rules. The cluster names give you hints about what
categories to create.

## Output Format

The output is a JSON object mapping prompt hashes to tags:

```json
{
  "a1b2c3d4e5f6...": "review",
  "f6e5d4c3b2a1...": "debug",
  ...
}
```

This format is compatible with agentpprof's `--tag-cache` option.
