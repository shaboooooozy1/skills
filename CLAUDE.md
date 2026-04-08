# CLAUDE.md

## Project Overview

This is **Anthropic's official skills repository** — a collection of skill definitions that Claude loads dynamically to improve performance on specialized tasks. Skills are folders containing instructions (`SKILL.md`), optional scripts, references, and assets. The repository also serves as a Claude Code Plugin marketplace.

For background: [Agent Skills spec](https://agentskills.io/specification) | [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills) | [Creating custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)

## Repository Structure

```
skills/                  # Root (this repo)
├── CLAUDE.md            # This file
├── README.md            # Public-facing documentation
├── THIRD_PARTY_NOTICES.md
├── .gitignore
├── .claude-plugin/
│   └── marketplace.json # Plugin marketplace config (two collections: document-skills, example-skills)
├── spec/
│   └── agent-skills-spec.md  # Points to https://agentskills.io/specification
├── template/
│   └── SKILL.md         # Minimal skill template with required frontmatter
└── skills/              # All 16 skill folders
    ├── algorithmic-art/     # Generative art with p5.js (Apache 2.0)
    ├── brand-guidelines/    # Anthropic brand styling (Apache 2.0)
    ├── canvas-design/       # Canvas/poster design with custom fonts (Apache 2.0)
    ├── doc-coauthoring/     # Document co-authoring (Apache 2.0)
    ├── docx/                # Word document processing (Proprietary)
    ├── frontend-design/     # Production-grade frontend UI (Apache 2.0)
    ├── internal-comms/      # Internal communication templates (Apache 2.0)
    ├── mcp-builder/         # MCP server development guide (Apache 2.0)
    ├── pdf/                 # PDF processing (Proprietary)
    ├── pptx/                # PowerPoint processing (Proprietary)
    ├── skill-creator/       # Meta-skill for creating new skills (Apache 2.0)
    ├── slack-gif-creator/   # Animated GIF creation (Apache 2.0)
    ├── theme-factory/       # Theme/design system generation (Apache 2.0)
    ├── web-artifacts-builder/ # React artifacts with Tailwind/shadcn (Apache 2.0)
    ├── webapp-testing/      # Web application testing (Apache 2.0)
    └── xlsx/                # Excel spreadsheet processing (Proprietary)
```

## Skill Anatomy

Every skill follows this structure:

```
skill-name/
├── SKILL.md          # REQUIRED — frontmatter + instructions
├── LICENSE.txt       # Optional — Apache 2.0 or Proprietary
├── scripts/          # Optional — Python/Bash executables
├── references/       # Optional — supporting documentation
├── examples/         # Optional — example files
└── assets/           # Optional — fonts, templates, etc.
```

### SKILL.md Format

```markdown
---
name: skill-name          # Required: kebab-case unique identifier
description: What it does  # Required: when to trigger this skill
license: See LICENSE.txt   # Optional
---

# Instructions in Markdown
```

- `name` must be lowercase with hyphens (e.g., `mcp-builder`, `slack-gif-creator`)
- `description` should clearly state what the skill does AND when Claude should use it
- Markdown body contains instructions, examples, guidelines, and decision trees

## Key Conventions

### Naming
- Skill folder names match the `name` field in frontmatter
- Always kebab-case for skill names and folder names

### Licensing
- **Open source (Apache 2.0):** All example/creative/technical skills
- **Proprietary (Anthropic):** Document processing skills (`docx`, `pdf`, `pptx`, `xlsx`) — no extraction, reproduction, or distribution outside Anthropic Services

### Content Style
- Instructions should be concise — avoid unnecessary verbosity
- Use decision trees or phased workflows for complex skills
- Embed code examples directly in SKILL.md when helpful
- Reference external docs in `references/` for lengthy technical details
- Bundle resources (fonts, templates, schemas) in `assets/` or skill subdirectories

### Scripts
- Python scripts should be executable and self-contained
- Bash scripts (e.g., `init-artifact.sh`, `bundle-artifact.sh`) for build/setup tasks
- Validation scripts exist in `skill-creator/scripts/` for checking skill structure

## Plugin Marketplace

The `.claude-plugin/marketplace.json` defines two plugin collections:

1. **document-skills** — `xlsx`, `docx`, `pptx`, `pdf`
2. **example-skills** — all 12 remaining skills

When adding a new skill, it must be added to the appropriate collection in `marketplace.json`.

Install via Claude Code:
```
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

## Development Workflow

### Creating a New Skill
1. Copy `template/SKILL.md` into a new folder under `skills/`
2. Fill in required frontmatter (`name`, `description`)
3. Write clear, concise instructions in the markdown body
4. Add scripts, references, examples, and assets as needed
5. Add a `LICENSE.txt` (Apache 2.0 for open source)
6. Register the skill in `.claude-plugin/marketplace.json` under the appropriate collection
7. Validate with `python skills/skill-creator/scripts/quick_validate.py`

### Modifying Existing Skills
- Edit the `SKILL.md` for instruction changes
- Keep changes focused — skills should remain single-purpose
- Test that the skill still triggers correctly based on its description

## No Build System

This repository has no package manager, no CI/CD pipeline, and no build step. It is a collection of static files (Markdown, Python, Bash, fonts, etc.) consumed directly by Claude's skill loading system. Validation is done via Python scripts in `skill-creator/scripts/`.

## .gitignore

Ignores: `.DS_Store`, `__pycache__/`, `.idea/`, `.vscode/`
