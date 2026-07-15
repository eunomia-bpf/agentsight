#!/usr/bin/env python3
"""
Clustering-based tagger for agentpprof.

This module provides unsupervised semantic clustering of prompts using
traditional NLP techniques (TF-IDF + K-Means). It serves as an alternative
to regex-based tagging when you want to discover natural groupings in
your prompt distribution without predefined rules.

Usage:
    # Generate tags from a folded stack file
    python cluster_tagger.py --input prompts.jsonl --output tags.json --clusters 15

    # Or read from stdin
    agentpprof --format json ... | python cluster_tagger.py --clusters 15

The output is a JSON mapping of prompt hash -> tag that can be used with
agentpprof's --tag-cache option.
"""

import argparse
import json
import sys
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import Counter

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans, MiniBatchKMeans
    from sklearn.metrics import silhouette_score
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def hash_prompt(text: str) -> str:
    """Generate a stable hash for a prompt."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def preprocess_prompt(text: str) -> str:
    """Basic preprocessing: lowercase, strip, normalize whitespace."""
    text = text.lower().strip()
    # Normalize whitespace
    text = ' '.join(text.split())
    # Remove very short prompts that are likely noise
    if len(text) < 3:
        return ''
    return text


def extract_keywords_from_cluster(
    texts: List[str],
    vectorizer: 'TfidfVectorizer',
    cluster_labels: np.ndarray,
    cluster_id: int,
    top_n: int = 3
) -> List[str]:
    """Extract top keywords for a cluster based on TF-IDF scores."""
    cluster_mask = cluster_labels == cluster_id
    cluster_texts = [t for t, m in zip(texts, cluster_mask) if m]

    if not cluster_texts:
        return []

    # Get feature names
    feature_names = vectorizer.get_feature_names_out()

    # Transform cluster texts
    cluster_tfidf = vectorizer.transform(cluster_texts)

    # Get mean TF-IDF scores for each term
    mean_scores = np.asarray(cluster_tfidf.mean(axis=0)).flatten()

    # Get top keywords
    top_indices = mean_scores.argsort()[-top_n:][::-1]
    return [feature_names[i] for i in top_indices if mean_scores[i] > 0]


def generate_cluster_name(keywords: List[str], cluster_id: int) -> str:
    """Generate a human-readable cluster name from keywords."""
    if not keywords:
        return f"cluster{cluster_id}"

    # Use first keyword as primary name, clean it up
    name = keywords[0]

    # Remove non-alphanumeric characters
    name = ''.join(c for c in name if c.isalnum())

    # Ensure valid tag format (3-12 lowercase letters)
    name = name[:12].lower()
    if len(name) < 3:
        return f"cluster{cluster_id}"

    return name


def find_optimal_clusters(
    tfidf_matrix,
    min_clusters: int = 5,
    max_clusters: int = 25
) -> int:
    """Find optimal number of clusters using silhouette score."""
    best_score = -1
    best_k = min_clusters

    for k in range(min_clusters, min(max_clusters + 1, tfidf_matrix.shape[0])):
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=3)
        labels = kmeans.fit_predict(tfidf_matrix)

        # Need at least 2 unique labels for silhouette
        if len(set(labels)) < 2:
            continue

        score = silhouette_score(tfidf_matrix, labels, sample_size=min(1000, tfidf_matrix.shape[0]))

        if score > best_score:
            best_score = score
            best_k = k

    return best_k


def cluster_prompts(
    prompts: List[str],
    n_clusters: Optional[int] = None,
    auto_clusters: bool = True,
    min_clusters: int = 5,
    max_clusters: int = 25
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """
    Cluster prompts and return tag mappings.

    Returns:
        (tag_map, cluster_info)
        - tag_map: dict of prompt_hash -> tag
        - cluster_info: dict of tag -> list of sample prompts
    """
    if not HAS_SKLEARN:
        raise ImportError(
            "scikit-learn is required for clustering. "
            "Install with: pip install scikit-learn"
        )

    # Preprocess
    processed = [preprocess_prompt(p) for p in prompts]
    valid_indices = [i for i, p in enumerate(processed) if p]
    valid_prompts = [processed[i] for i in valid_indices]

    if len(valid_prompts) < 2:
        return {}, {}

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95
    )

    tfidf_matrix = vectorizer.fit_transform(valid_prompts)

    # Determine number of clusters
    if n_clusters is None and auto_clusters:
        n_clusters = find_optimal_clusters(tfidf_matrix, min_clusters, max_clusters)
        print(f"Auto-selected {n_clusters} clusters", file=sys.stderr)
    elif n_clusters is None:
        n_clusters = 10

    # Cluster
    n_clusters = min(n_clusters, len(valid_prompts))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(tfidf_matrix)

    # Generate cluster names
    cluster_names = {}
    for cluster_id in range(n_clusters):
        keywords = extract_keywords_from_cluster(
            valid_prompts, vectorizer, labels, cluster_id
        )
        cluster_names[cluster_id] = generate_cluster_name(keywords, cluster_id)

    # Build tag map
    tag_map = {}
    cluster_info = {name: [] for name in set(cluster_names.values())}

    for idx, (orig_idx, label) in enumerate(zip(valid_indices, labels)):
        original_prompt = prompts[orig_idx]
        prompt_hash = hash_prompt(original_prompt)
        tag = cluster_names[label]
        tag_map[prompt_hash] = tag

        # Store sample prompts (limit to 5 per cluster)
        if len(cluster_info[tag]) < 5:
            cluster_info[tag].append(original_prompt[:100])

    return tag_map, cluster_info


def load_prompts_from_jsonl(path: str) -> List[str]:
    """Load prompts from a JSONL file."""
    prompts = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # Handle different formats
                if isinstance(obj, dict):
                    if 'prompt' in obj:
                        prompts.append(obj['prompt'])
                    elif 'text' in obj:
                        prompts.append(obj['text'])
                    elif 'content' in obj:
                        prompts.append(obj['content'])
                elif isinstance(obj, str):
                    prompts.append(obj)
            except json.JSONDecodeError:
                continue
    return prompts


def main():
    parser = argparse.ArgumentParser(
        description='Cluster prompts for semantic tagging'
    )
    parser.add_argument(
        '--input', '-i',
        help='Input JSONL file with prompts (default: stdin)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file for tag map (default: stdout)'
    )
    parser.add_argument(
        '--clusters', '-k',
        type=int,
        help='Number of clusters (default: auto-detect)'
    )
    parser.add_argument(
        '--no-auto',
        action='store_true',
        help='Disable automatic cluster count selection'
    )
    parser.add_argument(
        '--min-clusters',
        type=int,
        default=5,
        help='Minimum clusters for auto-detection (default: 5)'
    )
    parser.add_argument(
        '--max-clusters',
        type=int,
        default=25,
        help='Maximum clusters for auto-detection (default: 25)'
    )
    parser.add_argument(
        '--show-info',
        action='store_true',
        help='Print cluster info to stderr'
    )

    args = parser.parse_args()

    # Load prompts
    if args.input:
        prompts = load_prompts_from_jsonl(args.input)
    else:
        prompts = []
        for line in sys.stdin:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and 'prompt' in obj:
                        prompts.append(obj['prompt'])
                    elif isinstance(obj, str):
                        prompts.append(obj)
                except json.JSONDecodeError:
                    prompts.append(line)

    if not prompts:
        print("No prompts found", file=sys.stderr)
        sys.exit(1)

    print(f"Clustering {len(prompts)} prompts...", file=sys.stderr)

    # Cluster
    tag_map, cluster_info = cluster_prompts(
        prompts,
        n_clusters=args.clusters,
        auto_clusters=not args.no_auto,
        min_clusters=args.min_clusters,
        max_clusters=args.max_clusters
    )

    # Show cluster info
    if args.show_info:
        print("\nCluster distribution:", file=sys.stderr)
        tag_counts = Counter(tag_map.values())
        for tag, count in tag_counts.most_common():
            pct = 100.0 * count / len(tag_map)
            print(f"  {tag}: {count} ({pct:.1f}%)", file=sys.stderr)
            if tag in cluster_info:
                for sample in cluster_info[tag][:2]:
                    print(f"    - {sample[:60]}...", file=sys.stderr)

    # Output
    output = json.dumps(tag_map, indent=2)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Wrote {len(tag_map)} tags to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
