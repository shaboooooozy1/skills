---
name: building-quick-charts
description: >-
  Turns pasted numbers, a CSV, or a short description into a clean chart image (PNG and SVG) ready to
  drop into a PowerPoint slide, email, or client report. Use when the user says chart, graph, plot, or
  visual for a deck or report, or asks to chart premium history, loss ratio trend, claims frequency,
  renewal increases, or any small table. Use even if they only paste numbers and say "make this a
  bar chart." Do NOT use for interactive dashboards or full slide decks.
license: MIT
metadata:
  version: 1.1.0
  author: Will Bloomstine
---

# Building Quick Charts

Produce a chart image the user can paste anywhere. One chart, one message.

## Workflow

1. **Get the data into a CSV.** If the user pasted a table or numbers, write them to a CSV with a header row. First column is the category or period. Each further column is one series.
2. **Pick the type.**
   - Bar: compare categories or a few periods. Default.
   - Line: a trend over 6 or more periods.
   - Stacked bar: parts of a total across periods (e.g., paid vs. reserved).
   - Never pie unless the user asks. Bars read more accurately.
3. **Write the takeaway title.** The title states the finding, not the topic. "Loss ratio fell 3 straight years," not "Loss Ratio 2021–2024." Use only what the data shows.
4. **Run the script.**
   ```bash
   python scripts/make_chart.py data.csv --type bar --title "Loss ratio fell 3 straight years" \
     --ylabel "Loss ratio" --format percent --out loss_ratio
   ```
   It writes `loss_ratio.png` (200 dpi, 16:9) and `loss_ratio.svg`.
5. **Look at the PNG** before sending. Check labels are legible and nothing overlaps.
6. **Deliver** the PNG and SVG with one line naming the takeaway.

## Script options

| Flag | Values | Default |
|---|---|---|
| `--type` | `bar`, `line`, `stacked` | `bar` |
| `--format` | `number`, `currency`, `percent` (data as decimals, 0.62 = 62%) | `number` |
| `--benchmark` | a number drawn as a dashed reference line, with `--benchmark-label` | none |
| `--labels` | print values on bars or points | off |
| `--size` | `wide` (16:9 slide) or `square` | `wide` |

## Broker chart recipes

- **Premium history:** bar, `--format currency`, periods as policy years.
- **Loss ratio vs. target:** line or bar, `--format percent`, `--benchmark 0.6 --benchmark-label "Target 60%"` only if the user gives the target.
- **Frequency vs. severity:** two separate charts. Never two y-axes.
- **Paid vs. reserved:** stacked bar, `--format currency`.

Never invent a benchmark, industry average, or projection. Chart only the numbers supplied.
