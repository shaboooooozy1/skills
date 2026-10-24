#!/usr/bin/env python3
"""Render a clean, presentation-ready chart (PNG + SVG) from a CSV.

CSV layout: first column = category or period, each further column = one numeric series.

Usage:
  python make_chart.py data.csv --type bar --title "Takeaway" --format currency --out chart
"""
import argparse
import csv
import math
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

# Neutral, colorblind-safe palette. First series gets the strongest color.
PALETTE = ["#1F4E79", "#E07B39", "#5B8E7D", "#8C6BB1", "#A0A0A0"]
INK = "#222222"
MUTED = "#6B6B6B"
GRID = "#E3E3E3"
SIZES = {"wide": (10, 5.625), "square": (7, 7)}  # 16:9 slide and 1:1


def fmt_value(v, kind):
    if kind == "currency":
        a, sign = abs(v), "-" if v < 0 else ""
        if a >= 1_000_000:
            return f"{sign}${a / 1_000_000:,.1f}M"
        if a >= 10_000:
            return f"{sign}${a / 1_000:,.0f}K"
        return f"{sign}${a:,.0f}"
    if kind == "percent":
        return f"{v * 100:.0f}%"
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.2f}".rstrip("0").rstrip(".")


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    if len(rows) < 2 or len(rows[0]) < 2:
        sys.exit("CSV needs a header row and at least one data row with 2+ columns.")
    header, body = rows[0], rows[1:]
    cats = [r[0] for r in body]
    series = {}
    for j, name in enumerate(header[1:], start=1):
        vals = []
        for r in body:
            raw = (r[j] if j < len(r) else "").strip().replace(",", "").replace("$", "")
            if raw.endswith("%"):
                raw = str(float(raw[:-1]) / 100)
            try:
                vals.append(float(raw) if raw else math.nan)  # blank = unknown, never zero
            except ValueError:
                sys.exit(f"Non-numeric value {r[j]!r} in column {name!r}.")
        series[name] = vals
    return cats, series


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv")
    p.add_argument("--type", choices=["bar", "line", "stacked"], default="bar")
    p.add_argument("--title", required=True)
    p.add_argument("--subtitle", default="")
    p.add_argument("--ylabel", default="")
    p.add_argument("--format", choices=["number", "currency", "percent"], default="number")
    p.add_argument("--benchmark", type=float)
    p.add_argument("--benchmark-label", default="")
    p.add_argument("--labels", action="store_true")
    p.add_argument("--size", choices=list(SIZES), default="wide")
    p.add_argument("--source", default="", help="Footnote, e.g. 'Source: carrier loss runs valued 6/30/2026'")
    p.add_argument("--out", default="chart")
    a = p.parse_args()

    cats, series = read_csv(a.csv)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": INK,
                         "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, ax = plt.subplots(figsize=SIZES[a.size])
    x = list(range(len(cats)))
    names = list(series)
    n = len(names)

    if a.type == "line":
        for i, name in enumerate(names):
            ax.plot(x, series[name], color=PALETTE[i % len(PALETTE)], linewidth=2.5, marker="o",
                    markersize=6, label=name)
            if a.labels:
                for xi, v in zip(x, series[name]):
                    if math.isnan(v):
                        continue
                    ax.annotate(fmt_value(v, a.format), (xi, v), textcoords="offset points",
                                xytext=(0, 9), ha="center", fontsize=10, color=INK)
    elif a.type == "stacked":
        blanks = sum(math.isnan(v) for vals in series.values() for v in vals)
        if blanks:
            print(f"Note: {blanks} blank cell(s) drawn as zero in the stack. Say so on the slide.", file=sys.stderr)
            series = {k: [0.0 if math.isnan(v) else v for v in vals] for k, vals in series.items()}
        bottom = [0.0] * len(cats)
        tallest = max(sum(series[nm][k] for nm in names) for k in range(len(cats))) or 1
        for i, name in enumerate(names):
            bars = ax.bar(x, series[name], 0.6, bottom=bottom, color=PALETTE[i % len(PALETTE)], label=name)
            if a.labels:
                for b, v, btm in zip(bars, series[name], bottom):
                    if v and v >= 0.08 * tallest:
                        ax.text(b.get_x() + b.get_width() / 2, btm + v / 2, fmt_value(v, a.format),
                                ha="center", va="center", fontsize=9, color="white")
            bottom = [b + v for b, v in zip(bottom, series[name])]
        if a.labels:
            for xi, tot in zip(x, bottom):
                ax.text(xi, tot, fmt_value(tot, a.format), ha="center", va="bottom", fontsize=10)
    else:
        width = 0.7 / n
        for i, name in enumerate(names):
            offs = [xi - 0.35 + width * (i + 0.5) for xi in x]
            bars = ax.bar(offs, series[name], width * 0.92, color=PALETTE[i % len(PALETTE)], label=name)
            if a.labels:
                for b, v in zip(bars, series[name]):
                    if math.isnan(v):
                        continue  # blank: no bar, no label
                    ax.text(b.get_x() + b.get_width() / 2, v, fmt_value(v, a.format),
                            ha="center", va="bottom" if v >= 0 else "top", fontsize=10, color=INK)

    if a.benchmark is not None:
        ax.axhline(a.benchmark, color=MUTED, linestyle="--", linewidth=1.3)
        if a.benchmark_label:
            ax.text(len(cats) - 0.5, a.benchmark, " " + a.benchmark_label, va="bottom", ha="right",
                    fontsize=10, color=MUTED)

    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_value(v, a.format)))
    lo, hi = ax.get_ylim()
    has_negative = any(v < 0 for vals in series.values() for v in vals)
    bottom = lo if (a.type == "line" or has_negative) else 0
    ax.set_ylim(bottom, hi * 1.08 if (a.labels and hi > 0) else hi)
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#BBBBBB")
    ax.tick_params(length=0)
    if a.ylabel:
        ax.set_ylabel(a.ylabel)

    fig.suptitle(a.title, x=0.06, ha="left", fontsize=17, fontweight="bold", color=INK)
    if a.subtitle:
        fig.text(0.06, 0.875, a.subtitle, ha="left", fontsize=12, color=MUTED)
    top = 0.86 if a.subtitle else 0.9
    if n > 1:
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, frameon=False, loc="upper left", ncol=min(n, 4), fontsize=11,
                   bbox_to_anchor=(0.055, top - 0.005))
        top -= 0.06
    if a.source:
        fig.text(0.06, 0.02, a.source, ha="left", fontsize=9, color=MUTED)

    fig.tight_layout(rect=(0.02, 0.05 if a.source else 0.02, 0.98, top))
    fig.savefig(f"{a.out}.png", dpi=200)
    fig.savefig(f"{a.out}.svg")
    print(f"Wrote {a.out}.png and {a.out}.svg")


if __name__ == "__main__":
    main()
