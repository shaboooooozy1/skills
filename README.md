# Will Bloomstine's Claude Skills

Skills for a commercial P&C and employee benefits client executive. Each one turns a recurring piece of broker work into a repeatable, review-gated workflow. The math runs in scripts. The writing runs in one voice.

## Plugins

| Plugin | Skills | What it does |
|---|---|---|
| `broker-voice` | `churchill-hemingway-engine` | Drafts and edits client email, prospecting, invitations, renewals, BOR letters. Draft and edit modes. Compliance guardrails built in. |
| `pc-risk-counsel` | `analyzing-loss-runs`, `analyzing-total-cost-of-risk` | Normalizes multi-carrier loss runs into one workbook with data flags. Builds TCOR per $1,000 of revenue. Replays loss history against deductible and SIR options. |
| `personal-productivity` | `writing-formulas-and-sql`, `building-quick-charts`, `prototyping-ui-concepts`, `setup-architect` | Formulas and SQL, slide-ready chart images, clickable prototypes, and prompt/Project/Skill setup. |

## Install

**Claude Code**
```
/plugin marketplace add shaboooooozy1/skills
/plugin install pc-risk-counsel@bloomstine-skills
/plugin install broker-voice@bloomstine-skills
/plugin install personal-productivity@bloomstine-skills
```

**Claude.ai** — download a skill ZIP from the latest **main-branch** run of the Validate skills workflow (artifact `skill-zips`; pull request runs do not publish it), or build them yourself from a checkout of `main` with `python scripts/package_zips.py`. Upload in Customize > Skills.

**API** — upload the skill folder through the Skills API. Scripts need `pandas`, `openpyxl`, and `matplotlib`.

## Ground rules for every skill here

- No client data in this repo. Tests and examples use synthetic data in `evals/`.
- Never invent rates, premiums, carrier positions, coverage terms, or producer codes.
- Coverage-adjacent output ends with a review gate. Legal questions go to an attorney.

## Develop

```
python scripts/validate_skills.py      # official validator + house rules on every skill
python scripts/test_skill_scripts.py   # regression tests on synthetic data
python scripts/package_zips.py         # claude.ai-ready ZIPs in dist/
```

Trigger-eval query sets live in `evals/<skill>/trigger-queries.json`, in the format skill-creator's description optimizer expects. See `CHANGELOG.md` for versions and `docs/AUDIT-2026-10.md` for the audit behind this structure.

---

## Upstream: Anthropic example skills

This repository is a fork of [anthropics/skills](https://github.com/anthropics/skills). `spec/`, `template/`, and the skills under `skills/` that also exist upstream come from Anthropic and keep their original licenses. Four skills under `skills/` were added in this fork and are not from upstream: `email-command-center`, `m365-email-command-center`, `apollo-enrich-lead`, and `combined-chatbot`. `combined-chatbot` has a LICENSE file in its folder. `email-command-center`, `m365-email-command-center`, and `apollo-enrich-lead` have no license file yet, so no reuse terms are granted for them. Add one before sharing those skills. The original README follows.

> **Note:** This repository contains Anthropic's implementation of skills for Claude. For information about the Agent Skills standard, see [agentskills.io](http://agentskills.io).

# Skills
Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. Skills teach Claude how to complete specific tasks in a repeatable way, whether that's creating documents with your company's brand guidelines, analyzing data using your organization's specific workflows, or automating personal tasks.

For more information, check out:
- [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Equipping agents for the real world with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

# About This Repository

This repository contains skills that demonstrate what's possible with Claude's skills system. These skills range from creative applications (art, music, design) to technical tasks (testing web apps, MCP server generation) to enterprise workflows (communications, branding, etc.).

Each skill is self-contained in its own folder with a `SKILL.md` file containing the instructions and metadata that Claude uses. Browse through these skills to get inspiration for your own skills or to understand different patterns and approaches.

Many skills in this repo are open source (Apache 2.0). We've also included the document creation & editing skills that power [Claude's document capabilities](https://www.anthropic.com/news/create-files) under the hood in the [`skills/docx`](./skills/docx), [`skills/pdf`](./skills/pdf), [`skills/pptx`](./skills/pptx), and [`skills/xlsx`](./skills/xlsx) subfolders. These are source-available, not open source, but we wanted to share these with developers as a reference for more complex skills that are actively used in a production AI application.

## Disclaimer

**These skills are provided for demonstration and educational purposes only.** While some of these capabilities may be available in Claude, the implementations and behaviors you receive from Claude may differ from what is shown in these skills. These skills are meant to illustrate patterns and possibilities. Always test skills thoroughly in your own environment before relying on them for critical tasks.

# Skill Sets
- [./skills](./skills): Skill examples for Creative & Design, Development & Technical, Enterprise & Communication, and Document Skills
- [./spec](./spec): The Agent Skills specification
- [./template](./template): Skill template

# Try in Claude Code, Claude.ai, and the API

## Claude Code
You can register this repository as a Claude Code Plugin marketplace by running the following command in Claude Code:
```
/plugin marketplace add shaboooooozy1/skills
```

Then, to install a specific set of skills:
1. Select `Browse and install plugins`
2. Select `bloomstine-skills`
3. Select `document-skills` or `example-skills`
4. Select `Install now`

Alternatively, directly install either Plugin via:
```
/plugin install document-skills@bloomstine-skills
/plugin install example-skills@bloomstine-skills
```

After installing the plugin, you can use the skill by just mentioning it. For instance, if you install the `document-skills` plugin from the marketplace, you can ask Claude Code to do something like: "Use the PDF skill to extract the form fields from `path/to/some-file.pdf`"

## Claude.ai

These example skills are all already available to paid plans in Claude.ai. 

To use any skill from this repository or upload custom skills, follow the instructions in [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_a4222fa77b).

## Claude API

You can use Anthropic's pre-built skills, and upload custom skills, via the Claude API. See the [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill) for more.

# Creating a Basic Skill

Skills are simple to create - just a folder with a `SKILL.md` file containing YAML frontmatter and instructions. You can use the **template-skill** in this repository as a starting point:

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Add your instructions here that Claude will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

The frontmatter requires only two fields:
- `name` - A unique identifier for your skill (lowercase, hyphens for spaces)
- `description` - A complete description of what the skill does and when to use it

The markdown content below contains the instructions, examples, and guidelines that Claude will follow. For more details, see [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills).

# Partner Skills

Skills are a great way to teach Claude how to get better at using specific pieces of software. As we see awesome example skills from partners, we may highlight some of them here:

- **Notion** - [Notion Skills for Claude](https://www.notion.so/notiondevs/Notion-Skills-for-Claude-28da4445d27180c7af1df7d8615723d0)
