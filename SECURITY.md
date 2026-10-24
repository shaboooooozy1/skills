# Security and Data Policy

## No client data

This repository is public. It must never contain client names, FEINs, policy numbers, loss data, claimant details, health information, premiums, or anything from a carrier or client file. Tests and examples use synthetic data only, labeled as such in `evals/`.

Before every commit, check `git diff --staged` for real names and numbers.

## Scripts

Bundled scripts read local files and write local outputs. They make no network calls, read no credentials, and need no API keys. Any change that adds network access must say why in the pull request.

## Third-party skills

Read every file in a community skill before installing it, and pin it to a commit. Do not add community skills to this marketplace without that review.

## Reporting

Open a GitHub issue for anything that looks like exposed data or unexpected behavior. For anything sensitive, contact the owner directly instead of filing publicly.
