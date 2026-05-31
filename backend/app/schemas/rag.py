"""Pydantic schemas for Phase 8: RAG Evaluation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------


class RagCorpusCreate(BaseModel):
    name: str
    description: str = ""
    embedding_model: str = "tf-idf"
    chunk_size: int = Field(default=512, ge=64, le=4096)
    chunk_overlap: int = Field(default=64, ge=0, le=512)


class RagCorpusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_key: uuid.UUID
    version: int
    parent_id: uuid.UUID | None
    is_latest: bool
    created_at: datetime
    created_by: str
    name: str
    description: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


class RagDocumentCreate(BaseModel):
    content: str
    chunk_index: int = 0
    doc_source: str = ""


class RagDocumentBatchCreate(BaseModel):
    documents: list[RagDocumentCreate]


class RagDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    corpus_key: uuid.UUID
    content: str
    chunk_index: int
    doc_source: str
    created_at: datetime
    created_by: str


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


class RagSearchResult(BaseModel):
    doc_id: str
    content: str
    doc_source: str
    score: float


class RagSearchResponse(BaseModel):
    query: str
    corpus_key: uuid.UUID
    results: list[RagSearchResult]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class RagEvalCreate(BaseModel):
    corpus_key: uuid.UUID
    dataset_key: uuid.UUID
    top_k: int = Field(default=5, ge=1, le=50)


class RagEvalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    corpus_key: uuid.UUID
    dataset_key: uuid.UUID
    retrieval_method: str
    top_k: int
    query_count: int
    mean_context_relevance: float
    mean_faithfulness: float
    mean_answer_relevance: float
    status: str
    created_at: datetime
    created_by: str


class RagEvalResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rag_eval_id: uuid.UUID
    query_text: str
    retrieved_doc_ids: list[Any]
    retrieved_content: list[Any]
    answer_text: str
    context_relevance_score: float
    faithfulness_score: float
    answer_relevance_score: float
    created_at: datetime
