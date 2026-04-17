---
name: m365-email-command-center
description: Plan, draft, triage, and operationalize Microsoft 365 work email communication. Use when asked to manage Outlook-style inbox workflows, prioritize messages, draft replies, build follow-up plans, convert threads into action items, or create reusable email templates for team, stakeholder, and executive communication.
---

# M365 Email Command Center

Use this skill to run an end-to-end work-email workflow: intake, prioritization, drafting, and follow-through.

## Quick Workflow

1. Classify the request into one of these modes:
   - **Triage**: Sort messages by urgency/impact and decide next actions.
   - **Drafting**: Write new emails or replies with the right tone.
   - **Follow-through**: Convert email commitments into tasks, owners, and deadlines.
   - **Template creation**: Produce reusable snippets or full templates.
2. Load only the reference file needed for that mode:
   - `references/triage-playbook.md`
   - `references/email-templates.md`
3. Produce outputs in this order unless user asks otherwise:
   - Proposed priority queue
   - Recommended replies/drafts
   - Action tracker (owner, due date, status)

## Output Standards

- Keep subject lines specific and searchable.
- Put the decision/request in the first 2 sentences.
- Use explicit due dates (e.g., "April 22, 2026") instead of relative dates.
- End with a single clear call to action.
- For executive audiences: brief, decision-centric, low jargon.
- For cross-functional audiences: include context, dependencies, and risks.

## Triage Rules

Apply this scoring model when prioritization is needed:

- **P1 (Respond now)**: production blocker, customer escalation, legal/security risk, leadership same-day request.
- **P2 (Today)**: cross-team dependency, approaching deadline (<= 2 business days), unresolved external ask.
- **P3 (This week)**: informational updates, non-blocking requests, planning discussions.
- **P4 (Defer/archive)**: newsletters, duplicated threads, no action required.

If metadata is missing, state assumptions before drafting.

## Action Tracker Format

When a thread implies commitments, return a compact table:

| Action | Owner | Due date | Dependency | Status |
|---|---|---|---|---|

Use `At risk` status when scope, owner, or due date is unclear.

## Personalization Inputs

Ask for these only when necessary:

- role and audience seniority
- desired tone (direct, diplomatic, firm)
- deadline constraints
- approval requirements
- sensitive topics to avoid

If user skips them, proceed with neutral-professional defaults.
