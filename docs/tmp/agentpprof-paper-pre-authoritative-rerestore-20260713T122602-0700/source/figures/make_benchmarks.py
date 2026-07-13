#!/usr/bin/env python3
"""Generate preliminary benchmark plots for the paper from measured data.

Reads data/startup.json and data/redis.json (produced by the bench_*.py
harness in the sandlock-bench repo) and plots medians with stdev error bars.
No values are hardcoded; re-run the benchmarks, copy the JSON into data/, and
re-run this script to refresh the figure.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "benchmarks.pdf"
DATA = HERE / "data"


def load(name):
    with open(DATA / name) as f:
        return json.load(f)


def label_bars(ax, bars, labels, dy=3, fontsize=8):
    for bar, label in zip(bars, labels):
        ax.annotate(
            label,
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=fontsize,
        )


def main():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 9,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    colors = {
        "Bare metal": "#6c757d",
        "Sandlock": "#4c78a8",
        "Docker": "#d08127",
    }
    configs = ["Bare metal", "Sandlock", "Docker"]
    keys = {"Bare metal": "bare", "Sandlock": "sandlock", "Docker": "docker"}

    startup = load("startup.json")
    redis = load("redis.json")
    ebar = dict(capsize=2.5, ecolor="#333333", error_kw={"elinewidth": 0.8})

    fig, axes = plt.subplots(1, 3, figsize=(7.05, 1.72))

    # (a) Startup latency: median +/- stdev of /bin/echo wall time (log scale).
    suite = startup["suites"]["Trivial command"]
    s_med = [suite[keys[c]]["median_ms"] for c in configs]
    s_err = [suite[keys[c]]["stdev_ms"] for c in configs]
    ax = axes[0]
    bars = ax.bar(configs, s_med, yerr=s_err, color=[colors[c] for c in configs],
                  width=0.62, **ebar)
    ax.set_yscale("log")
    ax.set_ylim(0.5, max(s_med) * 2.2)
    ax.set_ylabel("ms, log scale")
    ax.set_title("(a) Startup latency")
    ax.grid(axis="y", which="major", alpha=0.25)
    label_bars(ax, bars, [f"{v:.0f}" if v >= 10 else f"{v:.1f}" for v in s_med], dy=3)
    ax.tick_params(axis="x", rotation=25)

    # (b) Redis throughput normalized to bare-metal median.
    rs = redis["summary"]
    bare_set = rs["bare"]["SET"]["rps"]["median"]
    bare_get = rs["bare"]["GET"]["rps"]["median"]
    thr = np.array([
        [rs[keys[c]]["SET"]["rps"]["median"] / bare_set * 100,
         rs[keys[c]]["GET"]["rps"]["median"] / bare_get * 100]
        for c in configs
    ])
    thr_err = np.array([
        [rs[keys[c]]["SET"]["rps"]["stdev"] / bare_set * 100,
         rs[keys[c]]["GET"]["rps"]["stdev"] / bare_get * 100]
        for c in configs
    ])
    ax = axes[1]
    x = np.arange(2)
    width = 0.24
    for i, cfg in enumerate(configs):
        offset = (i - 1) * width
        bars = ax.bar(x + offset, thr[i], width, yerr=thr_err[i], label=cfg,
                      color=colors[cfg], **ebar)
        label_bars(ax, bars, [f"{v:.0f}%" for v in thr[i]],
                   dy=2 + 7 * (cfg == "Sandlock"), fontsize=7.4)
    ax.set_ylim(0, 132)
    ax.set_ylabel("% of bare metal")
    ax.set_title("(b) Redis throughput")
    ax.set_xticks(x, ["SET", "GET"])
    ax.grid(axis="y", alpha=0.25)

    # (c) Redis SET p99 tail latency: median +/- stdev.
    p_med = [rs[keys[c]]["SET"]["p99_ms"]["median"] for c in configs]
    p_err = [rs[keys[c]]["SET"]["p99_ms"]["stdev"] for c in configs]
    ax = axes[2]
    bars = ax.bar(configs, p_med, yerr=p_err, color=[colors[c] for c in configs],
                  width=0.62, **ebar)
    ax.set_ylim(0, max(p_med) * 1.35)
    ax.set_ylabel("ms")
    ax.set_title("(c) Redis p99 latency")
    ax.grid(axis="y", alpha=0.25)
    label_bars(ax, bars, [f"{v:.2f}" for v in p_med], dy=3)
    ax.tick_params(axis="x", rotation=25)

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=colors[cfg], label=cfg)
        for cfg in configs
    ]
    fig.legend(
        handles=handles,
        frameon=False,
        loc="center left",
        bbox_to_anchor=(0.0, 0.55),
        handlelength=0.9,
        handletextpad=0.45,
        borderaxespad=0,
    )

    fig.tight_layout(w_pad=0.85, rect=(0.15, 0.02, 1.0, 0.97))
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.04)
    print(f"wrote {OUT}")
    print(f"  startup (ms): " + ", ".join(f"{c}={m:.1f}+/-{e:.1f}" for c, m, e in zip(configs, s_med, s_err)))
    print(f"  redis SET %bare: " + ", ".join(f"{c}={thr[i][0]:.1f}" for i, c in enumerate(configs)))


if __name__ == "__main__":
    main()
