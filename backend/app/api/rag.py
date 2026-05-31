"""RAG Evaluation API: corpora, document ingestion, search, and evaluation."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.rag_eval_result import RagEvalResult
from app.schemas.rag import (
    RagCorpusCreate,
    RagCorpusOut,
    RagDocumentBatchCreate,
    RagDocumentOut,
    RagEvalCreate,
    RagEvalOut,
    RagEvalResultOut,
    RagSearchRequest,
    RagSearchResponse,
    RagSearchResult,
)
from app.services.rag_corpus_service import create_corpus, get_corpus, list_corpora
from app.services.rag_document_service import RagError, ingest_documents, list_documents
from app.services.rag_eval_service import run_rag_eval
from app.services.rag_retrieval_service import retrieve

router = APIRouter(prefix="/rag", tags=["rag"])


# ---------------------------------------------------------------------------
# Corpora
# ---------------------------------------------------------------------------


@router.post("/corpora", response_model=RagCorpusOut, status_code=http_status.HTTP_201_CREATED)
def create_corpus_endpoint(
    body: RagCorpusCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
) -> RagCorpusOut:
    corpus = create_corpus(
        db,
        name=body.name,
        description=body.description,
        embedding_model=body.embedding_model,
        chunk_size=body.chunk_size,
        chunk_overlap=body.chunk_overlap,
        actor=actor,
    )
    return RagCorpusOut.model_validate(corpus)


@router.get("/corpora", response_model=list[RagCorpusOut])
def list_corpora_endpoint(db: Session = Depends(get_db)) -> list[RagCorpusOut]:
    return [RagCorpusOut.model_validate(c) for c in list_corpora(db)]


@router.get("/corpora/{corpus_key}", response_model=RagCorpusOut)
def get_corpus_endpoint(corpus_key: uuid.UUID, db: Session = Depends(get_db)) -> RagCorpusOut:
    corpus = get_corpus(db, corpus_key)
    if corpus is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Corpus not found")
    return RagCorpusOut.model_validate(corpus)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@router.post(
    "/corpora/{corpus_key}/documents",
    response_model=list[RagDocumentOut],
    status_code=http_status.HTTP_201_CREATED,
)
def ingest_documents_endpoint(
    corpus_key: uuid.UUID,
    body: RagDocumentBatchCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
) -> list[RagDocumentOut]:
    try:
        docs = ingest_documents(
            db,
            corpus_key=corpus_key,
            documents=[d.model_dump() for d in body.documents],
            actor=actor,
        )
    except RagError as exc:
        raise HTTPException(http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [RagDocumentOut.model_validate(d) for d in docs]


@router.get("/corpora/{corpus_key}/documents", response_model=list[RagDocumentOut])
def list_documents_endpoint(
    corpus_key: uuid.UUID, db: Session = Depends(get_db)
) -> list[RagDocumentOut]:
    corpus = get_corpus(db, corpus_key)
    if corpus is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Corpus not found")
    return [RagDocumentOut.model_validate(d) for d in list_documents(db, corpus.entity_key)]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@router.post("/corpora/{corpus_key}/search", response_model=RagSearchResponse)
def search_corpus_endpoint(
    corpus_key: uuid.UUID,
    body: RagSearchRequest,
    db: Session = Depends(get_db),
) -> RagSearchResponse:
    corpus = get_corpus(db, corpus_key)
    if corpus is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Corpus not found")
    hits = retrieve(db, corpus_key=corpus.entity_key, query=body.query, top_k=body.top_k)
    results = [
        RagSearchResult(
            doc_id=str(doc.id),
            content=doc.content,
            doc_source=doc.doc_source,
            score=score,
        )
        for doc, score in hits
    ]
    return RagSearchResponse(query=body.query, corpus_key=corpus.entity_key, results=results)


# ---------------------------------------------------------------------------
# Evaluations
# ---------------------------------------------------------------------------


@router.post("/evaluations", response_model=RagEvalOut, status_code=http_status.HTTP_201_CREATED)
def run_rag_eval_endpoint(
    body: RagEvalCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
) -> RagEvalOut:
    try:
        rag_eval = run_rag_eval(
            db,
            corpus_key=body.corpus_key,
            dataset_key=body.dataset_key,
            top_k=body.top_k,
            actor=actor,
        )
    except RagError as exc:
        raise HTTPException(http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return RagEvalOut.model_validate(rag_eval)


@router.get("/evaluations/{eval_id}", response_model=RagEvalOut)
def get_rag_eval_endpoint(eval_id: uuid.UUID, db: Session = Depends(get_db)) -> RagEvalOut:
    from app.models.rag_eval import RagEval

    row = db.get(RagEval, eval_id)
    if row is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="RAG evaluation not found")
    return RagEvalOut.model_validate(row)


@router.get("/evaluations/{eval_id}/results", response_model=list[RagEvalResultOut])
def list_rag_eval_results_endpoint(
    eval_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[RagEvalResultOut]:
    stmt = select(RagEvalResult).where(RagEvalResult.rag_eval_id == eval_id)
    rows = list(db.execute(stmt).scalars().all())
    return [RagEvalResultOut.model_validate(r) for r in rows]
