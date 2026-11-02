# Source and integration rules

## Evidence ladder

1. User-supplied current facts and the authorized system of record for the specific question.
2. Latest first-party account documents, complete email conversation, and sent messages.
3. Company announcements, official filings, permit records, and primary public sources.
4. Credible secondary reporting, clearly attributed.

Keep each fact's source URL or record ID, event date, retrieval date, and scope. Resolve contradictions explicitly. The newer item is not automatically authoritative if it is less direct. Do not transfer attribution between unrelated companies with similar names.

## Outlook and Gmail

Discover the available account choices. An Outlook connection does not establish access to the HUB work mailbox. Match the returned account identity to the intended mailbox before describing its contents as work-email evidence. Use narrow searches for an account/domain or requested time period; include read and unread where relevant. Avoid sweeping personal mail merely because it is connected.

For daily triage, default to the last seven days if no prior completed review exists. Carry unresolved older items only when evidenced. Deduplicate by conversation. Compare the latest inbound request with later sent messages and subsequent replies; do not infer unanswered status from an isolated search snippet. Distinguish **I owe**, **waiting on them**, **resolved**, and **unverified**.

Do not copy full private mail into a public repository, demonstration, saved skill, or unrelated analytics service. Extract the minimum authorized structured fields. Never store tokens, private download links, or mailbox IDs in this skill. Keep drafts in the response unless the user requests a saved mailbox draft. Use current tool instructions for all writes.

## Data and Julius

Use a supplied table or export first. With Julius, discover only relevant files, inspect headers and meaning, and calculate over an explicit dataset. Record row counts, exclusions, date coverage, and missing fields. A named integration is not proof a dataset exists. Respect access failures; do not invent results or silently call a sample production data.

Use the bundled analyzer for its exact contract. If another schema is needed, make a reversible normalization copy and show the field mapping. Preserve source columns in the original. Do not send a whole mailbox to Julius merely to calculate a few metrics.

## GitHub

Use GitHub for requested source-code and workflow maintenance. Keep code and fictional fixtures separate from working account data. Inspect repository instructions and current branch state; create a focused branch and reviewable pull request unless the user specifies a different authorized process. Do not merge, delete, or change visibility by default. A public repository may hold this generic skill and fictional fixtures; it must not receive private pipeline records.

## Public research

Verify dates and read the substantive source. For each signal record **confirmed change**, **possible insurance implication**, and **next discovery step** separately. Seek acquisition, expansion, facility, workforce, construction, financing, and operational changes. Do not infer existing coverage gaps, current limits, premium, carrier, renewal date, or buying intent from an announcement.

## Failure behavior

Report what was and was not reviewed. Continue with supplied data or a clearly labeled example when a source is unavailable. One failed access check does not imply there are no messages or accounts. Do not repeatedly trigger stalled authorization or claim the user needs to reconnect unless the provider explicitly reports that requirement.
