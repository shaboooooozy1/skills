---
name: apollo-enrich-lead
description: Enrich a lead (person or company) using the Apollo data tools, score it against our generic B2B SaaS ICP, and produce a structured lead profile with qualification verdict and a suggested next step. Use whenever the user asks to enrich, qualify, score, or research a lead/contact/account, or pastes an email, LinkedIn URL, person+company, or company domain.
---

# Apollo: Enrich Lead

> Generic B2B SaaS template. Replace the placeholders in **Customization checklist** before first real use.

## When to use this skill

Trigger this skill whenever the user:
- asks to enrich, qualify, score, or research a lead, contact, or account
- pastes an email address, LinkedIn URL, person name + company, or company domain
- asks "who at <company> should we talk to?" or "tell me about <person/company>"
- asks for a list of likely buyers at a target account
- asks to refresh / re-enrich a record they already have

## Inputs accepted

- Person email (e.g. `jane@acme.com`)
- LinkedIn profile URL
- Person name + company name
- Company name or domain
- A list (CSV, newline-separated, or pasted table) of any of the above

If only a company is given, do account enrichment + suggest 3–5 likely buyer-persona contacts.

## ICP — generic B2B SaaS

A lead is **qualified** if it matches the bulk of the following.

**Firmographics (account)**
- Industry: Software, SaaS, Internet, Information Technology, Financial Services, Professional Services
- Headcount: 50–5,000 employees (sweet spot 200–1,500)
- Revenue: $10M–$1B ARR (or unknown but funded)
- Geography: US, Canada, UK, EU, ANZ
- Tech signals: cloud-native; has engineering / RevOps / data / security functions
- Funding: Series A through Pre-IPO, or profitable / bootstrapped at scale

**Buying-committee personas (contact)**
- Economic buyer: VP / Director / Head of (Engineering, Product, RevOps, Data, Sales Ops, Marketing Ops, IT, Security)
- Champion: Senior IC or Manager in those same functions
- C-level: CTO, CIO, CISO, CRO, CMO, COO

**Disqualifiers**
- Headcount < 25 or > 25,000
- Industries: government, defense, gambling, adult, crypto-only
- Geography: sanctioned regions
- Title: student, intern, retired, side-project founder unrelated to target buyer

## Process

1. **Pick the right tool call**
   - Single person → `find-and-enrich-list-of-contacts` (one-item list is fine)
   - Single company → `find-and-enrich-company`
   - Contacts at a known company → `find-and-enrich-contacts-at-company`
   - List input → batch through the matching endpoint, do **not** loop one-by-one
   - Missing fields after enrichment → follow up with `add-company-data-points` / `add-contact-data-points`
   - If the user wants to ask a free-form question over their existing book of business → `ask-question-about-accounts`

2. **Request these data points** (call the `add-*-data-points` tools if not in the default response)
   - **Account:** domain, industry, employee_count, estimated_annual_revenue, hq_location, founded_year, funding_total, latest_funding_stage, technologies, short_description
   - **Contact:** full_name, title, seniority, department, linkedin_url, email (+ verification status), phone, location, current_company

3. **Resolve & dedup**
   - Multiple matches → pick strongest signal (verified email > LinkedIn URL match > phone) and list alternates
   - No match → say "not found" explicitly. Never fabricate.

4. **Score** with the rubric below. Show the breakdown, not just the verdict.

5. **Produce the report** using the output template.

6. **Recommend next step**
   - Tier A → outreach + 1–2 sentence personalization hook drawn from concrete enrichment facts (recent funding, hiring signal, tech adoption, exec hire)
   - Tier B → nurture / wait for trigger event
   - Tier C → disqualify with a one-line reason

## Scoring rubric

| Signal | Points |
|---|---|
| Industry in target list | +3 |
| Headcount in sweet spot (200–1,500) | +3 |
| Headcount in extended range (50–5,000) | +1 |
| Geography in target list | +2 |
| Funding stage in target range | +2 |
| Persona is economic buyer | +4 |
| Persona is champion | +2 |
| Persona is C-level in target function | +3 |
| Verified email present | +1 |
| Any disqualifier hit | -10 |

Tiers: **A** ≥ 10 · **B** 5–9 · **C** ≤ 4 (or any disqualifier)

## Output template (single lead)

```
### Lead: <Name> @ <Company>
**Verdict:** Tier A / B / C — <one-line reason>

**Account**
- Domain: ...
- Industry / Headcount / Revenue: ...
- HQ: ...
- Funding: ...
- Tech & signals: ...

**Contact**
- Title / Seniority / Department: ...
- LinkedIn: ...
- Email (verified?): ...
- Phone: ...
- Location: ...

**Score breakdown**
- <signal>: +N
- ...
- Total: N → Tier X

**Personalization hook**
<1–2 sentences citing a concrete enrichment fact>

**Next step**
<Outreach / Nurture / Disqualify> — <reason>
```

## Output template (list)

A markdown table with one row per lead — columns: Name, Company, Title, Tier, Hook, Next step — followed by the per-lead detail blocks above.

## Guardrails

- Never fabricate emails, phone numbers, titles, or firmographics. If Apollo returns nothing, say "not found".
- Don't share data you didn't get from a tool call.
- Respect rate limits: batch list calls; never loop one-by-one when a batch endpoint exists.
- If the user has a CRM MCP available (HubSpot / Salesforce / Common Room / etc.), offer to write the enriched record back — do **not** write without explicit confirmation.
- Keep PII handling tight: don't paste full enrichment payloads into long-lived chat history if the user only asked for a verdict.

## Customization checklist

Edit before first real use to make this match your company:
- [ ] Target industries
- [ ] Headcount / revenue band
- [ ] Geographies
- [ ] Buyer personas (titles + functions)
- [ ] Disqualifiers
- [ ] Scoring weights
- [ ] Personalization hook style (tone, length, opener)
- [ ] CRM write-back destination (HubSpot / Salesforce / other)

## Keywords

apollo, enrich lead, enrich contact, enrich account, qualify lead, lead scoring, ICP fit, prospect research, account research, contact enrichment, sales prospecting, who should we talk to
