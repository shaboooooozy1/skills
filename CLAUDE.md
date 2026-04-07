# CLAUDE.md

This is Anthropic's **Agent Skills Repository** — a collection of skills that extend Claude's capabilities. Skills are self-contained packages with instructions, scripts, and resources that Claude loads dynamically to perform specialized tasks.

## Repository Structure

```
skills/                     # All skill implementations (18 skills)
├── algorithmic-art/        # Generative art with p5.js
├── brand-guidelines/       # Brand styling (colors, typography)
├── canvas-design/          # Interactive canvas design
├── combined-chatbot/       # Chatbot development guide
├── doc-coauthoring/        # Document collaboration
├── docx/                   # Word document creation/editing (proprietary)
├── frontend-design/        # Frontend design patterns
├── internal-comms/         # Internal communications
├── mcp-builder/            # MCP server development guide
├── pdf/                    # PDF manipulation toolkit (proprietary)
├── pptx/                   # PowerPoint creation/editing (proprietary)
├── skill-creator/          # Guide for creating new skills
├── slack-gif-creator/      # Animated GIF creation for Slack
├── theme-factory/          # Theme styling toolkit
├── web-artifacts-builder/  # React/Tailwind/shadcn web builder
├── webapp-testing/         # Web app testing with Playwright
└── xlsx/                   # Excel spreadsheet toolkit (proprietary)
spec/                       # Agent Skills specification (points to agentskills.io)
template/                   # Minimal skill template (starting point for new skills)
.claude-plugin/             # Plugin marketplace configuration
```

## Skill Anatomy

Every skill follows this structure:

```
skill-name/
├── SKILL.md          # Required: YAML frontmatter + markdown instructions
├── LICENSE.txt       # License (Apache 2.0 or Proprietary)
├── scripts/          # Optional: Executable code (Python/Bash/JS)
├── references/       # Optional: Documentation loaded on-demand
└── assets/           # Optional: Templates, fonts, icons, boilerplate
```

### SKILL.md Format

```markdown
---
name: skill-name
description: What the skill does and when Claude should use it
---

# Skill Title

[Instructions, examples, guidelines]
```

- **Frontmatter** requires only `name` and `description` (plus optional `license`)
- `name`: lowercase, hyphen-separated identifier
- `description`: the primary trigger mechanism — must clearly describe what the skill does and when to use it
- Body: markdown instructions loaded only after the skill triggers
- Keep under 500 lines to minimize context bloat

## Key Conventions

### Naming
- Skill directories use lowercase hyphenated names (e.g., `skill-creator`, `web-artifacts-builder`)
- Scripts use snake_case (e.g., `package_skill.py`, `rotate_pdf.py`)

### Licensing
- **Apache 2.0**: Open source skills (skill-creator, brand-guidelines, webapp-testing, mcp-builder, etc.)
- **Proprietary/Source-available**: Document skills (docx, pdf, pptx, xlsx)
- All skills include a `license:` field in SKILL.md frontmatter referencing LICENSE.txt

### Design Principles
- **Concise is key**: The context window is shared — only add what Claude doesn't already know
- **Progressive disclosure**: Metadata always in context, body loaded on trigger, resources loaded as needed
- **Appropriate degrees of freedom**: Match specificity to task fragility (narrow bridge = strict guardrails, open field = many routes)
- **Scripts for determinism**: Use scripts/ for tasks needing deterministic reliability or frequently rewritten code

## Plugin Marketplace

Defined in `.claude-plugin/marketplace.json`. Two plugin bundles:
- **document-skills**: xlsx, docx, pptx, pdf
- **example-skills**: All other skills (12 total)

Install via Claude Code:
```
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

## Development Workflow

### No centralized build/test/lint system
Each skill is self-contained. There is no repo-wide package.json, test runner, or linter. Skills manage their own dependencies (e.g., `requirements.txt` in individual skill directories).

### Creating a new skill
1. Copy `template/SKILL.md` as a starting point
2. Follow patterns in `skills/skill-creator/SKILL.md` for comprehensive guidance
3. Place the skill directory under `skills/`
4. Add to `.claude-plugin/marketplace.json` if it should be in a plugin bundle

### Modifying existing skills
- Read the existing SKILL.md thoroughly before making changes
- Preserve the frontmatter format (name, description, license)
- Keep instructions action-oriented and concise
- Test any scripts independently before committing

## Dependencies by Skill

Most skills have no external dependencies. Notable exceptions:
- `slack-gif-creator/`: pillow, imageio, imageio-ffmpeg, numpy (Python)
- `mcp-builder/scripts/`: anthropic, mcp (Python)
- `webapp-testing/`: Playwright (Node.js)
- Document skills (docx, pdf, pptx, xlsx): Various Python libraries for file manipulation
