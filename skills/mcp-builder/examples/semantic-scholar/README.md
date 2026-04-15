# Semantic Scholar MCP Server

A comprehensive [Model Context Protocol](https://modelcontextprotocol.io/) server
for the [Semantic Scholar](https://www.semanticscholar.org/) Graph, Recommendations,
and Datasets APIs. Built in Python with
[`FastMCP`](https://github.com/modelcontextprotocol/python-sdk) following the
`mcp-builder` skill conventions.

## What it gives an agent

- **Paper search** — relevance, bulk (token-paginated), exact title match,
  autocomplete.
- **Paper details** — single or batch fetch (up to 500 per call), citations,
  references, identifier resolution (DOI, ArXiv, PMID, PMCID, URL, MAG, ACL).
- **Author workflows** — author search, profile, authored papers, 500-author batch.
- **Recommendations** — similar-paper recommendations from a single seed or
  from positive/negative example lists.
- **Datasets** — list releases, inspect a release's datasets, fetch temporary
  download links for bulk corpora (key required).
- **Resources** — `s2://paper/{id}`, `s2://author/{id}`,
  `s2://paper/{id}/citations` for data surfacing without argument schemas.

All 18 tools accept `response_format: "markdown" | "json"`, have explicit
`readOnly` / `idempotent` annotations, and funnel failures through a single
error helper that returns actionable remediation strings (set an API key,
try a smaller limit, etc.).

## Installation

```bash
# Run ephemerally with uvx
uvx semantic-scholar-mcp

# Or install
pipx install semantic-scholar-mcp
```

Or from source:

```bash
git clone <this-repo>
cd semantic-scholar-mcp
pip install -e .
semantic-scholar-mcp
```

## Configuration

| Env var | Required? | Purpose |
| --- | --- | --- |
| `SEMANTIC_SCHOLAR_API_KEY` | No (strongly recommended) | Authenticates requests. Raises rate limits and is required by `s2_get_dataset_download_links`. Request one at <https://www.semanticscholar.org/product/api#api-key>. |

Copy `.env.example` to `.env` and fill in the key, or export it in your shell
before launching the server.

## Claude Code / Claude Desktop integration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "semantic-scholar": {
      "command": "uvx",
      "args": ["semantic-scholar-mcp"],
      "env": {
        "SEMANTIC_SCHOLAR_API_KEY": "..."
      }
    }
  }
}
```

## Transports

- `semantic-scholar-mcp` — stdio (default)
- `semantic-scholar-mcp --transport http --port 8000` — streamable HTTP

## Tool catalog

| Tool | Purpose |
| --- | --- |
| `s2_search_papers` | Relevance-ranked paper search (offset pagination). |
| `s2_search_papers_bulk` | Token-paginated bulk search, up to 1000 per page. |
| `s2_match_paper_by_title` | Best-match lookup from an exact title. |
| `s2_get_paper` | Full paper details by any accepted ID. |
| `s2_get_paper_citations` | Papers citing the given paper. |
| `s2_get_paper_references` | Papers referenced by the given paper. |
| `s2_batch_get_papers` | Fetch up to 500 papers in a single call. |
| `s2_autocomplete_paper_title` | Title autocomplete suggestions. |
| `s2_search_authors` | Author name search. |
| `s2_get_author` | Full author profile. |
| `s2_get_author_papers` | Papers authored by a specific author. |
| `s2_batch_get_authors` | Fetch up to 500 author profiles. |
| `s2_recommend_from_paper` | Recommend papers similar to a seed paper. |
| `s2_recommend_from_list` | Recommend from positive/negative paper lists. |
| `s2_list_dataset_releases` | List all dataset releases. |
| `s2_get_release_datasets` | Datasets in a specific release. |
| `s2_get_dataset_download_links` | S3 download URLs for a dataset (API key required). |
| `s2_resolve_identifier` | Normalise any accepted paper ID to canonical CorpusId + externalIds. |

## Example agent prompts

- _"What are the most-cited papers that cite 'Attention Is All You Need' and were published before 2020? Summarise the top 5."_
- _"Find the paper titled 'Deep Residual Learning for Image Recognition', list its 3 most-cited references, and give the first author of each."_
- _"Using the recommendations API, suggest 10 papers similar to arXiv 2005.14165 that I haven't read yet (my reading list is [...])."_
- _"Which dataset names are available in the most recent Semantic Scholar corpus release?"_

## Verification

```bash
# Static sanity check
python -m py_compile $(git ls-files '*.py')

# Confirm tool registration
python -c "from semantic_scholar_mcp.server import mcp; import asyncio; \
  print('tools:', [t.name for t in asyncio.run(mcp.list_tools())])"

# Interactive
npx @modelcontextprotocol/inspector uvx --from . semantic-scholar-mcp
```

An evaluation suite of 10 verifiable questions lives in
`evaluation/semantic_scholar_eval.xml`.

## License

MIT. See the repo root `LICENSE` / `LICENSE.txt` in the hosting repository.
