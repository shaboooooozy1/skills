"""Pydantic input models for every Semantic Scholar MCP tool."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import (
    DEFAULT_LIMIT,
    MAX_BATCH_SIZE,
    MAX_BULK_SEARCH_LIMIT,
    MAX_RECOMMENDATIONS_LIMIT,
    MAX_SEARCH_LIMIT,
)
from .formatting import ResponseFormat


class _Base(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class _FormatMixin(_Base):
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human reading, 'json' for machine parsing.",
    )


# ---------------------------------------------------------------------------
# Paper tools
# ---------------------------------------------------------------------------


class SearchPapersInput(_FormatMixin):
    """Input for :func:`s2_search_papers` (relevance-ranked search)."""

    query: str = Field(
        ...,
        description="Free-text search query (e.g. 'attention is all you need', 'graph neural networks').",
        min_length=1,
        max_length=500,
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Max papers to return (1-100).",
        ge=1,
        le=MAX_SEARCH_LIMIT,
    )
    offset: int = Field(
        default=0,
        description="Pagination offset (0-based).",
        ge=0,
    )
    fields: Optional[str] = Field(
        default=None,
        description="Comma-separated field list to request. Leave blank for a sensible default.",
        max_length=500,
    )
    year: Optional[str] = Field(
        default=None,
        description="Filter by publication year(s). Accepts a single year '2021', a range '2018-2021', or open-ended '2018-' / '-2020'.",
        max_length=20,
    )
    venue: Optional[str] = Field(
        default=None,
        description="Comma-separated list of venue names to restrict to (e.g. 'Nature,Science,NeurIPS').",
        max_length=200,
    )
    fields_of_study: Optional[str] = Field(
        default=None,
        description="Comma-separated fields of study filter (e.g. 'Computer Science,Physics').",
        max_length=200,
    )
    open_access_pdf: bool = Field(
        default=False,
        description="If True, restrict results to papers with an open-access PDF.",
    )


class SearchPapersBulkInput(_FormatMixin):
    """Input for :func:`s2_search_papers_bulk` (token-paginated, large result sets)."""

    query: str = Field(..., description="Free-text search query.", min_length=1, max_length=500)
    token: Optional[str] = Field(
        default=None,
        description="Continuation token from a previous call to paginate through bulk results.",
        max_length=200,
    )
    limit: int = Field(
        default=100,
        description="Max papers per page (1-1000).",
        ge=1,
        le=MAX_BULK_SEARCH_LIMIT,
    )
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)
    year: Optional[str] = Field(default=None, description="Year filter.", max_length=20)
    venue: Optional[str] = Field(default=None, description="Venue filter.", max_length=200)
    fields_of_study: Optional[str] = Field(default=None, description="Fields-of-study filter.", max_length=200)
    sort: Optional[str] = Field(
        default=None,
        description="Sort key. Accepts 'paperId:asc', 'publicationDate:desc', 'citationCount:desc'.",
        max_length=50,
    )


class MatchPaperByTitleInput(_FormatMixin):
    """Input for :func:`s2_match_paper_by_title`."""

    title: str = Field(..., description="Full paper title to match.", min_length=3, max_length=500)
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)


class GetPaperInput(_FormatMixin):
    """Input for :func:`s2_get_paper`."""

    paper_id: str = Field(
        ...,
        description=(
            "Paper identifier. Accepts CorpusId (e.g. '2140197'), DOI (e.g. '10.1038/s41586-020-2649-2'), "
            "'ARXIV:<id>', 'MAG:<id>', 'ACL:<id>', 'PMID:<id>', 'PMCID:<id>', or 'URL:<url>'."
        ),
        min_length=1,
        max_length=300,
    )
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)


class PaperPaginatedInput(_FormatMixin):
    """Shared input for citations / references listings."""

    paper_id: str = Field(..., description="Paper identifier (see s2_get_paper for formats).", min_length=1, max_length=300)
    limit: int = Field(default=DEFAULT_LIMIT, description="Max results per page (1-100).", ge=1, le=MAX_SEARCH_LIMIT)
    offset: int = Field(default=0, description="Pagination offset.", ge=0)
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)


class BatchGetPapersInput(_FormatMixin):
    """Input for :func:`s2_batch_get_papers`."""

    paper_ids: List[str] = Field(
        ...,
        description="List of paper identifiers (max 500).",
        min_length=1,
        max_length=MAX_BATCH_SIZE,
    )
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)

    @field_validator("paper_ids")
    @classmethod
    def _strip_ids(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("paper_ids must contain at least one non-empty identifier")
        return cleaned


class AutocompletePaperTitleInput(_FormatMixin):
    """Input for :func:`s2_autocomplete_paper_title`."""

    query: str = Field(..., description="Partial paper title.", min_length=1, max_length=200)


# ---------------------------------------------------------------------------
# Author tools
# ---------------------------------------------------------------------------


class SearchAuthorsInput(_FormatMixin):
    query: str = Field(..., description="Author name or fragment (e.g. 'Geoffrey Hinton').", min_length=1, max_length=200)
    limit: int = Field(default=DEFAULT_LIMIT, description="Max authors to return (1-100).", ge=1, le=MAX_SEARCH_LIMIT)
    offset: int = Field(default=0, description="Pagination offset.", ge=0)
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)


class GetAuthorInput(_FormatMixin):
    author_id: str = Field(..., description="Semantic Scholar author ID (e.g. '1741101').", min_length=1, max_length=50)
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)


class GetAuthorPapersInput(_FormatMixin):
    author_id: str = Field(..., description="Semantic Scholar author ID.", min_length=1, max_length=50)
    limit: int = Field(default=DEFAULT_LIMIT, description="Max papers per page (1-100).", ge=1, le=MAX_SEARCH_LIMIT)
    offset: int = Field(default=0, description="Pagination offset.", ge=0)
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)


class BatchGetAuthorsInput(_FormatMixin):
    author_ids: List[str] = Field(
        ...,
        description="List of Semantic Scholar author IDs (max 500).",
        min_length=1,
        max_length=MAX_BATCH_SIZE,
    )
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)

    @field_validator("author_ids")
    @classmethod
    def _strip_ids(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("author_ids must contain at least one non-empty identifier")
        return cleaned


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


class RecommendFromPaperInput(_FormatMixin):
    paper_id: str = Field(..., description="Seed paper identifier.", min_length=1, max_length=300)
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Max recommendations (1-500).",
        ge=1,
        le=MAX_RECOMMENDATIONS_LIMIT,
    )
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)
    recent_only: bool = Field(
        default=True,
        description="If True, restrict to papers published in the last 60 days (API default).",
    )


class RecommendFromListInput(_FormatMixin):
    positive_paper_ids: List[str] = Field(
        ...,
        description="Papers you WANT more like.",
        min_length=1,
        max_length=MAX_BATCH_SIZE,
    )
    negative_paper_ids: Optional[List[str]] = Field(
        default=None,
        description="Papers to AVOID recommending near.",
        max_length=MAX_BATCH_SIZE,
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Max recommendations (1-500).",
        ge=1,
        le=MAX_RECOMMENDATIONS_LIMIT,
    )
    fields: Optional[str] = Field(default=None, description="Comma-separated field list.", max_length=500)


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------


class ListDatasetReleasesInput(_FormatMixin):
    """No parameters other than response_format."""


class GetReleaseDatasetsInput(_FormatMixin):
    release_id: str = Field(
        ...,
        description="Release identifier (YYYY-MM-DD or 'latest').",
        min_length=1,
        max_length=20,
    )


class GetDatasetDownloadLinksInput(_FormatMixin):
    release_id: str = Field(..., description="Release identifier.", min_length=1, max_length=20)
    dataset_name: str = Field(
        ...,
        description="Dataset name (e.g. 'papers', 'authors', 'citations').",
        min_length=1,
        max_length=50,
    )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


class ResolveIdentifierInput(_FormatMixin):
    paper_id: str = Field(
        ...,
        description=(
            "Any accepted Semantic Scholar paper identifier (DOI, ARXIV:<id>, etc.). "
            "Returns the canonical CorpusId / paperId plus all known externalIds."
        ),
        min_length=1,
        max_length=300,
    )
