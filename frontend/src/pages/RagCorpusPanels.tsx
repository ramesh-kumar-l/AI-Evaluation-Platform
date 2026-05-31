import { useState } from "react";
import type { RagCorpus, RagSearchResponse } from "@/types";
import { createRagCorpus, ingestDocuments, searchRagCorpus } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";

// ---------------------------------------------------------------------------
// CorpusCreateForm
// ---------------------------------------------------------------------------

interface CorpusCreateFormProps {
  onCreated: (c: RagCorpus) => void;
}

export function CorpusCreateForm({ onCreated }: CorpusCreateFormProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const corpus = await createRagCorpus({ name: name.trim() });
      setName("");
      onCreated(corpus);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create corpus");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <h2 className="text-sm font-semibold mb-3">New Knowledge Base</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          className="w-full border rounded px-3 py-1.5 text-sm"
          placeholder="Corpus name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        {error && <p className="text-xs text-red-500">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-primary text-primary-foreground rounded px-3 py-1.5 text-sm disabled:opacity-50"
        >
          {submitting ? <Spinner /> : "Create Corpus"}
        </button>
      </form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// IngestPanel
// ---------------------------------------------------------------------------

interface IngestPanelProps {
  corpus: RagCorpus;
}

export function IngestPanel({ corpus }: IngestPanelProps) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ingested, setIngested] = useState(0);

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (!lines.length) return;
    setSubmitting(true);
    setError(null);
    try {
      const docs = lines.map((content, i) => ({
        content,
        chunk_index: i,
        doc_source: "manual",
      }));
      const result = await ingestDocuments(corpus.entity_key, docs);
      setIngested((n) => n + result.length);
      setText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        One document per line. Each line = one chunk.
      </p>
      <textarea
        className="w-full border rounded px-3 py-1.5 text-sm h-28 resize-none"
        placeholder={"Paris is the capital of France.\nBerlin is the capital of Germany."}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
      {ingested > 0 && (
        <p className="text-xs text-green-600">{ingested} chunk(s) ingested total</p>
      )}
      <button
        onClick={handleIngest}
        disabled={submitting}
        className="bg-primary text-primary-foreground rounded px-3 py-1.5 text-sm disabled:opacity-50"
      >
        {submitting ? <Spinner /> : "Ingest"}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SearchPanel
// ---------------------------------------------------------------------------

interface SearchPanelProps {
  corpus: RagCorpus;
}

export function SearchPanel({ corpus }: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RagSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await searchRagCorpus(corpus.entity_key, query.trim(), topK));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          className="flex-1 border rounded px-3 py-1.5 text-sm"
          placeholder="Test retrieval query…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="border rounded px-2 py-1.5 text-sm"
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
        >
          {[1, 3, 5, 10].map((k) => (
            <option key={k} value={k}>
              top-{k}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={loading}
          className="bg-primary text-primary-foreground rounded px-3 py-1.5 text-sm disabled:opacity-50"
        >
          {loading ? <Spinner /> : "Search"}
        </button>
      </form>
      {error && <p className="text-xs text-red-500">{error}</p>}
      {result && (
        <ul className="space-y-1">
          {result.results.length === 0 ? (
            <li className="text-xs text-muted-foreground">No results (corpus may be empty)</li>
          ) : (
            result.results.map((r, i) => (
              <li key={r.doc_id} className="text-xs border rounded px-2 py-1.5">
                <span className="font-mono text-muted-foreground mr-2">#{i + 1}</span>
                <span className="text-green-700 font-semibold mr-2">
                  {(r.score * 100).toFixed(1)}%
                </span>
                {r.content}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
