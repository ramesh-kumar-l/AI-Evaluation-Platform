"""Integration tests for Phase 8: RAG Evaluation."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.services.metrics.answer_relevance import score_answer_relevance
from app.services.metrics.context_relevance import score_context_relevance
from app.services.metrics.faithfulness import score_faithfulness

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_corpus(client: TestClient, name: str = "Corpus-A") -> dict:
    r = client.post("/rag/corpora", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


def _ingest(client: TestClient, corpus_key: str, contents: list[str]) -> list[dict]:
    docs = [{"content": c, "chunk_index": i, "doc_source": "test"} for i, c in enumerate(contents)]
    r = client.post(f"/rag/corpora/{corpus_key}/documents", json={"documents": docs})
    assert r.status_code == 201, r.text
    return r.json()


def _make_dataset(client: TestClient, items: list[dict]) -> dict:
    r = client.post(
        "/datasets",
        json={"name": "RAG-DS", "description": "", "items": items},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Corpus CRUD
# ---------------------------------------------------------------------------


def test_rag_corpus_create(client: TestClient) -> None:
    data = _make_corpus(client, name="FAQS")
    assert data["name"] == "FAQS"
    assert data["version"] == 1
    assert data["embedding_model"] == "tf-idf"
    assert data["chunk_size"] == 512
    assert isinstance(data["entity_key"], str)


def test_rag_corpus_list(client: TestClient) -> None:
    _make_corpus(client, name="C1")
    _make_corpus(client, name="C2")
    r = client.get("/rag/corpora")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "C1" in names and "C2" in names


def test_rag_corpus_get(client: TestClient) -> None:
    corpus = _make_corpus(client)
    r = client.get(f"/rag/corpora/{corpus['entity_key']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Corpus-A"


def test_rag_corpus_get_not_found(client: TestClient) -> None:
    r = client.get(f"/rag/corpora/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Document ingestion
# ---------------------------------------------------------------------------


def test_rag_document_ingest(client: TestClient) -> None:
    corpus = _make_corpus(client)
    docs = _ingest(
        client,
        corpus["entity_key"],
        ["Paris is the capital of France.", "Berlin is in Germany."],
    )
    assert len(docs) == 2
    assert docs[0]["chunk_index"] == 0
    assert docs[1]["chunk_index"] == 1
    assert docs[0]["corpus_key"] == corpus["entity_key"]


def test_rag_document_ingest_corpus_not_found(client: TestClient) -> None:
    r = client.post(
        f"/rag/corpora/{uuid.uuid4()}/documents",
        json={"documents": [{"content": "hello"}]},
    )
    assert r.status_code == 422


def test_rag_document_list(client: TestClient) -> None:
    corpus = _make_corpus(client)
    _ingest(client, corpus["entity_key"], ["doc1", "doc2", "doc3"])
    r = client.get(f"/rag/corpora/{corpus['entity_key']}/documents")
    assert r.status_code == 200
    assert len(r.json()) == 3


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def test_rag_search_returns_results(client: TestClient) -> None:
    corpus = _make_corpus(client)
    _ingest(
        client,
        corpus["entity_key"],
        [
            "The Eiffel Tower is in Paris.",
            "Python is a programming language.",
            "Rome was not built in a day.",
        ],
    )
    r = client.post(
        f"/rag/corpora/{corpus['entity_key']}/search",
        json={"query": "Paris Eiffel Tower", "top_k": 2},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "Paris Eiffel Tower"
    assert len(data["results"]) <= 2
    # Top result should mention Paris/Eiffel
    assert data["results"][0]["score"] > 0.0


def test_rag_search_empty_corpus(client: TestClient) -> None:
    corpus = _make_corpus(client)
    r = client.post(
        f"/rag/corpora/{corpus['entity_key']}/search",
        json={"query": "anything", "top_k": 5},
    )
    assert r.status_code == 200
    assert r.json()["results"] == []


def test_rag_search_corpus_not_found(client: TestClient) -> None:
    r = client.post(
        f"/rag/corpora/{uuid.uuid4()}/search",
        json={"query": "test"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# RAG Evaluation
# ---------------------------------------------------------------------------


def test_rag_eval_run(client: TestClient) -> None:
    corpus = _make_corpus(client)
    _ingest(
        client,
        corpus["entity_key"],
        ["The capital of France is Paris.", "Germany's capital is Berlin."],
    )
    dataset = _make_dataset(
        client,
        [
            {"input": "What is the capital of France?", "expected": "Paris"},
            {"input": "What is the capital of Germany?", "expected": "Berlin"},
        ],
    )
    r = client.post(
        "/rag/evaluations",
        json={"corpus_key": corpus["entity_key"], "dataset_key": dataset["entity_key"], "top_k": 2},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["query_count"] == 2
    assert data["status"] == "completed"
    assert 0.0 <= data["mean_context_relevance"] <= 1.0
    assert 0.0 <= data["mean_faithfulness"] <= 1.0
    assert 0.0 <= data["mean_answer_relevance"] <= 1.0


def test_rag_eval_results(client: TestClient) -> None:
    corpus = _make_corpus(client)
    _ingest(client, corpus["entity_key"], ["Python is a language.", "Java is also a language."])
    dataset = _make_dataset(
        client, [{"input": "Tell me about Python", "expected": "Python is a language"}]
    )
    r = client.post(
        "/rag/evaluations",
        json={"corpus_key": corpus["entity_key"], "dataset_key": dataset["entity_key"]},
    )
    eval_id = r.json()["id"]
    r2 = client.get(f"/rag/evaluations/{eval_id}/results")
    assert r2.status_code == 200
    results = r2.json()
    assert len(results) == 1
    assert results[0]["query_text"] == "Tell me about Python"
    assert isinstance(results[0]["retrieved_doc_ids"], list)
    assert 0.0 <= results[0]["context_relevance_score"] <= 1.0


def test_rag_eval_get(client: TestClient) -> None:
    corpus = _make_corpus(client)
    _ingest(client, corpus["entity_key"], ["some content"])
    dataset = _make_dataset(client, [{"input": "query", "expected": "answer"}])
    r = client.post(
        "/rag/evaluations",
        json={"corpus_key": corpus["entity_key"], "dataset_key": dataset["entity_key"]},
    )
    eval_id = r.json()["id"]
    r2 = client.get(f"/rag/evaluations/{eval_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == eval_id


def test_rag_eval_get_not_found(client: TestClient) -> None:
    r = client.get(f"/rag/evaluations/{uuid.uuid4()}")
    assert r.status_code == 404


def test_rag_eval_corpus_not_found(client: TestClient) -> None:
    dataset = _make_dataset(client, [{"input": "q", "expected": "a"}])
    r = client.post(
        "/rag/evaluations",
        json={"corpus_key": str(uuid.uuid4()), "dataset_key": dataset["entity_key"]},
    )
    assert r.status_code == 422


def test_rag_eval_dataset_not_found(client: TestClient) -> None:
    corpus = _make_corpus(client)
    r = client.post(
        "/rag/evaluations",
        json={"corpus_key": corpus["entity_key"], "dataset_key": str(uuid.uuid4())},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Metric scorer unit tests
# ---------------------------------------------------------------------------


def test_context_relevance_scorer(client: TestClient) -> None:
    score = score_context_relevance("python language", ["python is a programming language"])
    assert score > 0.0
    assert score_context_relevance("anything", []) == 0.0


def test_faithfulness_scorer(client: TestClient) -> None:
    score = score_faithfulness("Paris is beautiful", ["Paris is the capital and beautiful city"])
    assert score > 0.0
    assert score_faithfulness("", ["some context"]) == 0.0
    assert score_faithfulness("some answer", []) == 0.0


def test_answer_relevance_scorer(client: TestClient) -> None:
    score = score_answer_relevance("what is python", "python is a programming language")
    assert score > 0.0
    assert score_answer_relevance("", "") == 0.0
