"""RAG evaluation service: orchestrate retrieval + scoring for a dataset of queries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.rag_corpus import RagCorpus
from app.models.rag_eval import RagEval
from app.models.rag_eval_result import RagEvalResult
from app.services import audit
from app.services.metrics.answer_relevance import score_answer_relevance
from app.services.metrics.context_relevance import score_context_relevance
from app.services.metrics.faithfulness import score_faithfulness
from app.services.rag_document_service import RagError
from app.services.rag_retrieval_service import retrieve
from app.services.versioning import get_latest


def _extract_query(item: Any) -> str:
    if isinstance(item, dict):
        inp = item.get("input", "")
        if isinstance(inp, dict):
            return str(inp.get("query", inp.get("text", str(inp))))
        return str(inp)
    return str(item)


def _extract_answer(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("expected", ""))
    return ""


def run_rag_eval(
    db: Session,
    *,
    corpus_key: uuid.UUID,
    dataset_key: uuid.UUID,
    top_k: int,
    actor: str,
) -> RagEval:
    """Run a RAG evaluation: retrieve + score every query in the dataset."""
    corpus = get_latest(db, RagCorpus, corpus_key)
    if corpus is None:
        raise RagError(f"Corpus {corpus_key} not found")

    dataset = get_latest(db, Dataset, dataset_key)
    if dataset is None:
        raise RagError(f"Dataset {dataset_key} not found")

    items: list[Any] = dataset.items
    now = datetime.now(UTC)

    rag_eval = RagEval(
        id=uuid.uuid4(),
        corpus_key=corpus.entity_key,
        dataset_key=dataset.entity_key,
        retrieval_method="tf-idf",
        top_k=top_k,
        query_count=0,
        mean_context_relevance=0.0,
        mean_faithfulness=0.0,
        mean_answer_relevance=0.0,
        status="completed",
        created_at=now,
        created_by=actor,
    )
    db.add(rag_eval)
    db.flush()

    result_rows: list[RagEvalResult] = []
    for item in items:
        query = _extract_query(item)
        answer = _extract_answer(item)
        retrieved = retrieve(db, corpus_key=corpus.entity_key, query=query, top_k=top_k)
        contents = [doc.content for doc, _ in retrieved]
        doc_ids = [str(doc.id) for doc, _ in retrieved]

        cr = score_context_relevance(query, contents)
        faith = score_faithfulness(answer, contents)
        ar = score_answer_relevance(query, answer)

        row = RagEvalResult(
            id=uuid.uuid4(),
            rag_eval_id=rag_eval.id,
            query_text=query,
            retrieved_doc_ids=doc_ids,
            retrieved_content=contents,
            answer_text=answer,
            context_relevance_score=cr,
            faithfulness_score=faith,
            answer_relevance_score=ar,
            created_at=now,
        )
        db.add(row)
        result_rows.append(row)

    n = len(result_rows)
    rag_eval.query_count = n
    rag_eval.status = "completed" if n > 0 else "failed"
    if n > 0:
        rag_eval.mean_context_relevance = round(
            sum(r.context_relevance_score for r in result_rows) / n, 4
        )
        rag_eval.mean_faithfulness = round(sum(r.faithfulness_score for r in result_rows) / n, 4)
        rag_eval.mean_answer_relevance = round(
            sum(r.answer_relevance_score for r in result_rows) / n, 4
        )

    db.flush()
    audit.record_event(
        db,
        actor=actor,
        action="create",
        entity_type="rag_evals",
        entity_key=rag_eval.id,
        entity_version_id=None,
        payload={
            "corpus_key": str(corpus_key),
            "dataset_key": str(dataset_key),
            "query_count": n,
            "status": rag_eval.status,
        },
    )
    db.commit()
    db.refresh(rag_eval)
    return rag_eval
