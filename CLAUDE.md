# CLAUDE.md

## Repository Overview

This is the **Anthropic Agent Skills** repository — a collection of skills that demonstrate Claude's capabilities using the [Agent Skills standard](https://agentskills.io/specification). Skills are self-contained folders with instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks.

## Directory Structure

```
skills/               # Main skills directory (17 skills)
├── docx/             # Word document creation/editing (source-available)
├── pdf/              # PDF manipulation (source-available)
├── pptx/             # PowerPoint creation/editing (source-available)
├── xlsx/             # Spreadsheet creation with formulas (source-available)
├── algorithmic-art/  # Generative art creation
├── brand-guidelines/ # Brand guideline enforcement
├── canvas-design/    # Canvas-based design
├── combined-chatbot/ # Conversational AI chatbot builder
├── doc-coauthoring/  # Document co-authoring
├── frontend-design/  # Frontend design patterns
├── internal-comms/   # Internal communications
├── mcp-builder/      # MCP server generation
├── skill-creator/    # Meta-skill for creating new skills
├── slack-gif-creator/# Slack GIF creation
├── theme-factory/    # Theme generation
├── web-artifacts-builder/ # React single-page artifacts
├── webapp-testing/   # Web application testing with Playwright
spec/                 # Agent Skills specification (links to agentskills.io)
template/             # Skill template with blank SKILL.md
.claude-plugin/       # Plugin marketplace configuration
```

## Skill Anatomy

Every skill follows a consistent structure:

**Required file:**
- `SKILL.md` — YAML frontmatter (`name`, `description`) + markdown instructions body

**Optional directories:**
- `scripts/` — Executable Python/Bash scripts (called as black boxes, never read into context)
- `references/` — Documentation loaded into context as needed
- `assets/` — Templates, icons, fonts, boilerplate code
- `LICENSE.txt` — Apache 2.0 (examples) or Proprietary (document skills)

## Key Conventions

### Skill Design Principles

- **Context is a shared resource** — keep SKILL.md under 5k words; use progressive disclosure (metadata → SKILL.md → bundled resources)
- **Imperative language** — always use infinitive/imperative form in instructions
- **Description field is the trigger** — must clearly state what the skill does AND when to use it
- **No extraneous files** — no README.md, CHANGELOG.md, etc. inside skills
- **Black box scripts** — run scripts with `--help` first; do not read script source into context

### Degrees of Freedom

- **High** (text instructions): multiple approaches valid, context-dependent
- **Medium** (pseudocode/scripts with parameters): preferred patterns exist, some variation OK
- **Low** (specific scripts): operations fragile, consistency critical

### Naming Conventions

- Skill names: lowercase, hyphens (`web-artifacts-builder`, `skill-creator`)
- Python scripts: `snake_case.py`
- Bash scripts: `kebab-case.sh`

## Development Workflow

### Creating a New Skill

Use the `skill-creator` skill's tools:

1. `python skills/skill-creator/scripts/init_skill.py <skill-name> --path <directory>` — scaffold a new skill
2. Implement resources (scripts, references, assets) first
3. Write SKILL.md with clear frontmatter and instructions
4. `python skills/skill-creator/scripts/package_skill.py <path/to/skill-folder>` — package as `.skill` file (validated zip)
5. `python skills/skill-creator/scripts/quick_validate.py <path>` — validate structure

### Validation Checks

The validation scripts check:
- YAML frontmatter presence and correctness
- Required fields (`name`, `description`)
- Naming conventions
- Directory structure compliance

## External Dependencies

Some skills require:
- **Python 3.x** with PIL/Pillow, pandas, pypdf (varies by skill)
- **Node.js/npm** (web-artifacts-builder)
- **Playwright** (webapp-testing)
- **LibreOffice** (xlsx formula recalculation)

## Build & Test

There is no traditional build system. Skills are static folders packaged as `.skill` files (zip archives). Testing is done by running skills against real tasks and iterating.

## Licensing

- **Apache 2.0**: Example skills and specification
- **Proprietary/Source-Available**: Document skills (docx, pdf, pptx, xlsx)

## Plugin Marketplace

Defined in `.claude-plugin/marketplace.json` with two groups:
- **document-skills**: xlsx, docx, pptx, pdf
- **example-skills**: all other skills

Skills are installed via `/plugin marketplace add` (Claude Code) or uploaded directly (Claude.ai / API).

## Git Conventions

- Feature branch workflow with PRs
- Commit messages: `Add [skill-name] skill for...`, `Fix ...`, `Update ...`
- Branch naming: `claude/<description>-<id>`
