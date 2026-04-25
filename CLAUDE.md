# CLAUDE.md

## Repository Overview

This is the **Anthropic Agent Skills** repository — a collection of skills that demonstrate Claude's capabilities using the [Agent Skills standard](https://agentskills.io/specification). Skills are self-contained folders with instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks.

## Directory Structure

```
skills/               # Main skills directory (17 skills)
├── docx/             # Word document creation/editing
├── pdf/              # PDF manipulation
├── pptx/             # PowerPoint creation/editing
├── xlsx/             # Spreadsheet creation with formulas
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

**Optional:**
- `scripts/` — Executable Python/Bash scripts (called as black boxes, never read into context)
- `references/` — Documentation loaded into context as needed
- `assets/` — Templates, icons, fonts, boilerplate code
- `LICENSE.txt` — License file

## Key Conventions

### Skill Design Principles

- **Context is a shared resource** — keep SKILL.md under 5k words; use progressive disclosure (metadata → SKILL.md → bundled resources)
- **Imperative language** — always use infinitive/imperative form in instructions
- **Description field is the trigger** — must clearly state what the skill does AND when to use it
- **No extraneous files** — no README.md, CHANGELOG.md, etc. inside skills

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

There is no traditional build system. Skills are static folders packaged as `.skill` files. Testing is done by running skills against real tasks and iterating.

## External Dependencies

Some skills require:
- **Python 3.x** with PIL/Pillow, pandas, pypdf (varies by skill)
- **Node.js/npm** (web-artifacts-builder)
- **Playwright** (webapp-testing)
- **LibreOffice** (xlsx formula recalculation)

## Licensing

- **Apache 2.0**: Example skills and specification
- **Source-Available**: Document skills (docx, pdf, pptx, xlsx)

## Plugin Marketplace

Defined in `.claude-plugin/marketplace.json` with two groups:
- **document-skills**: xlsx, docx, pptx, pdf
- **example-skills**: most other skills (see `marketplace.json` for exact list)

Skills are installed via `/plugin marketplace add` (Claude Code) or uploaded directly (Claude.ai / API).

## Using Skills via the Anthropic API

### Beta API Namespaces

All Skills functionality requires the `client.beta.*` namespace. Never use the standard `client.messages.create()` for skill-enabled calls.

```python
# ❌ Wrong
response = client.messages.create(container={...})

# ✅ Correct
response = client.beta.messages.create(
    betas=["code-execution-2025-08-25", "files-api-2025-04-14", "skills-2025-10-02"],
    container={"skills": [{"type": "anthropic", "skill_id": "xlsx", "version": "latest"}]},
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
    model="claude-sonnet-4-6",
    max_tokens=4096,
    messages=[{"role": "user", "content": "..."}],
)
```

Pass beta headers **per-request** via the `betas` parameter — do not set them in `default_headers`, which would require code execution on every call:

```python
# ❌ Wrong (applies to all requests)
client = Anthropic(default_headers={"anthropic-beta": "skills-2025-10-02"})

# ✅ Correct (scoped to skill requests only)
response = client.beta.messages.create(
    betas=["code-execution-2025-08-25", "files-api-2025-04-14", "skills-2025-10-02"],
    ...
)
```

Files must also be accessed through the beta namespace:

```python
# ❌ Wrong
content = client.files.content(file_id)

# ✅ Correct
content = client.beta.files.download(file_id)
metadata = client.beta.files.retrieve_metadata(file_id)
```

### File ID Extraction

Skills generate output files and return `file_id` values embedded in the response. The response structure differs from the standard Messages API — file IDs are nested inside `bash_code_execution_tool_result` blocks:

```python
# Manual extraction
file_ids = []
for block in response.content:
    if block.type == "tool_result":
        for inner in getattr(block, "content", []):
            if hasattr(inner, "file_id"):
                file_ids.append(inner.file_id)
```

Use `.read()` (not `.content`) to get file bytes, and `.size_bytes` (not `.size`) for file size:

```python
# ❌ Wrong
data = client.beta.files.download(file_id).content  # AttributeError
size = metadata.size                                  # AttributeError

# ✅ Correct
data = client.beta.files.download(file_id).read()
metadata = client.beta.files.retrieve_metadata(file_id)
size = metadata.size_bytes
```

### Document Generation Timing

Document generation takes significantly longer than standard API calls. Always set user expectations before triggering a generation cell:

| Document type | Typical time |
|---------------|-------------|
| Excel (`.xlsx`) | ~2 minutes |
| PowerPoint (`.pptx`) | 1–2 minutes |
| PDF | 1–2 minutes |
| Word (`.docx`) | 1–2 minutes |

Add a note immediately before long-running cells:

```markdown
**⏱️ Note**: Excel generation typically takes ~2 minutes.
The cell will show `[*]` while running — this is expected.
```

Keep generated examples simple and focused; generation time scales with complexity. Notebook cells that appear frozen are almost always still running.

## Git Conventions

- Feature branch workflow with PRs
- Commit messages: `Add [skill-name] skill for...`, `Fix ...`, `Update ...`
- Branch naming: `claude/<description>-<id>`
