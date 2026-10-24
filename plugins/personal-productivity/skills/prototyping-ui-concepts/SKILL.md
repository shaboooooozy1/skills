---
name: prototyping-ui-concepts
description: >-
  Builds working, clickable HTML/CSS/JS prototypes of app screens, dashboards, client portals,
  calculators, and landing pages so an idea can be tested in minutes, then iterates on feedback.
  Use when the user says prototype, mockup, wireframe, "build me a quick app," "show me what this
  could look like," or describes a tool or screen they want to try, even without asking for code.
  Do NOT use for production code in an existing codebase, static charts, or slide decks.
license: MIT
metadata:
  version: 1.1.0
  author: Will Bloomstine
---

# Prototyping UI Concepts

Get a working concept in front of the user fast. Refine after they react.

## Brief: four elements

Before building, make sure the request covers these. Infer what you can. Ask one question only if a missing element changes the build.

- **Goal**: what it does ("compare three renewal options side by side").
- **Layout**: how space is organized ("filters on the left, cards in a grid").
- **Content**: the real fields, data, and copy. Use realistic placeholder data, never real client data.
- **Audience**: who uses it. A CFO reading on a phone needs different affordances than an account manager at a desk.

## Build rules

1. If the session offers a Design or artifact type built for mockups, use it. Otherwise write one self-contained HTML file.
2. Vanilla HTML, CSS, and JS by default. React only when state gets complex.
3. Build the happy path first. Every visible button does something, even if it is a toast saying "not built yet."
4. Familiar patterns: top nav, sidebar, cards, tables, modals. Novelty is for later rounds.
5. Mobile-safe: works at 390px wide without horizontal scroll.
6. Keep everything in one file. CDN libraries only when they save real work.

## Iterating

- **Broad changes** (color, layout, new panel, "give me two alternatives"): rebuild the relevant section.
- **Targeted changes** (one component, spacing, copy): edit only that part. Do not regenerate the whole file.
- **New direction**: keep the current version as v1 and build v2 beside it, so the user can compare.

After each round, say in one line what changed and offer the single most useful next refinement.

## Insurance-flavored starting points

- Renewal comparison: incumbent vs. two alternatives, premium, retention, key coverage differences flagged as "review."
- COI tracker: vendor list, expiry dates, status chips (current, expiring in 30 days, missing).
- TCOR calculator: inputs for premium, retained losses, fees, admin; output total and per-$1,000 revenue.

Label any coverage-related output "illustrative, not a coverage determination."
