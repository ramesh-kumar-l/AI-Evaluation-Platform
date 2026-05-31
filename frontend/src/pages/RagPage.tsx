import { useEffect, useState } from "react";
import type { Dataset, RagCorpus, RagEval, RagEvalResult } from "@/types";
import { getRagEvalResults, listDatasets, listRagCorpora, runRagEval } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { CorpusCreateForm, IngestPanel, SearchPanel } from "@/pages/RagCorpusPanels";

// ---------------------------------------------------------------------------
// EvalPanel
// ---------------------------------------------------------------------------

interface EvalPanelProps {
  corpus: RagCorpus;
  datasets: Dataset[];
}

function EvalPanel({ corpus, datasets }: EvalPanelProps) {
  const [datasetKey, setDatasetKey] = useState("");
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [evalResult, setEvalResult] = useState<RagEval | null>(null);
  const [perQuery, setPerQuery] = useState<RagEvalResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleRun(e: React.FormEvent) {
    e.preventDefault();
    if (!datasetKey) return;
    setLoading(true);
    setError(null);
    setPerQuery([]);
    try {
      const ev = await runRagEval({
        corpus_key: corpus.entity_key,
        dataset_key: datasetKey,
        top_k: topK,
      });
      setEvalResult(ev);
      setPerQuery(await getRagEvalResults(ev.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleRun} className="flex gap-2 items-end flex-wrap">
        <div className="flex-1 min-w-40">
          <label className="block text-xs text-muted-foreground mb-1">Query dataset</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={datasetKey}
            onChange={(e) => setDatasetKey(e.target.value)}
            required
          >
            <option value="">Select dataset…</option>
            {datasets.map((d) => (
              <option key={d.entity_key} value={d.entity_key}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-muted-foreground mb-1">top-k</label>
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          >
            {[1, 3, 5, 10].map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={loading || !datasetKey}
          className="bg-primary text-primary-foreground rounded px-3 py-1.5 text-sm disabled:opacity-50"
        >
          {loading ? <Spinner /> : "Run Evaluation"}
        </button>
      </form>
      {error && <p className="text-xs text-red-500">{error}</p>}
      {evalResult && (
        <div className="space-y-2">
          <div className="grid grid-cols-3 gap-2 text-xs">
            {[
              { label: "Context Relevance", value: evalResult.mean_context_relevance },
              { label: "Faithfulness", value: evalResult.mean_faithfulness },
              { label: "Answer Relevance", value: evalResult.mean_answer_relevance },
            ].map(({ label, value }) => (
              <div key={label} className="border rounded p-2 text-center">
                <div className="font-semibold text-base">{(value * 100).toFixed(1)}%</div>
                <div className="text-muted-foreground">{label}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            {evalResult.query_count} queries · {evalResult.retrieval_method} · top-
            {evalResult.top_k}
          </p>
          {perQuery.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-semibold">Per-query breakdown</p>
              {perQuery.map((r, i) => (
                <div key={r.id} className="border rounded px-2 py-1.5 text-xs space-y-0.5">
                  <div className="font-medium">
                    Q{i + 1}: {r.query_text}
                  </div>
                  <div className="flex gap-3 text-muted-foreground">
                    <span>CR: {(r.context_relevance_score * 100).toFixed(1)}%</span>
                    <span>F: {(r.faithfulness_score * 100).toFixed(1)}%</span>
                    <span>AR: {(r.answer_relevance_score * 100).toFixed(1)}%</span>
                    <span>{r.retrieved_doc_ids.length} docs retrieved</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CorpusDetail
// ---------------------------------------------------------------------------

interface CorpusDetailProps {
  corpus: RagCorpus;
  datasets: Dataset[];
}

function CorpusDetail({ corpus, datasets }: CorpusDetailProps) {
  const [tab, setTab] = useState<"ingest" | "search" | "eval">("ingest");
  const tabs: Array<{ id: typeof tab; label: string }> = [
    { id: "ingest", label: "Ingest" },
    { id: "search", label: "Search" },
    { id: "eval", label: "Evaluate" },
  ];

  return (
    <Card>
      <div className="space-y-3">
        <div>
          <h3 className="font-semibold text-sm">{corpus.name}</h3>
          <p className="text-xs text-muted-foreground">
            v{corpus.version} · {corpus.embedding_model} · chunk {corpus.chunk_size}
          </p>
          <Badge variant="muted" className="mt-1 text-xs">
            {corpus.entity_key.slice(0, 8)}
          </Badge>
        </div>
        <div className="flex gap-1 border-b pb-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-1 text-xs rounded ${
                tab === t.id
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        {tab === "ingest" && <IngestPanel corpus={corpus} />}
        {tab === "search" && <SearchPanel corpus={corpus} />}
        {tab === "eval" && <EvalPanel corpus={corpus} datasets={datasets} />}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// RagPage
// ---------------------------------------------------------------------------

export function RagPage() {
  const [corpora, setCorpora] = useState<RagCorpus[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState<RagCorpus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listRagCorpora(), listDatasets()])
      .then(([c, d]) => {
        setCorpora(c);
        setDatasets(d);
        if (c.length > 0) setSelected(c[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">RAG Evaluation</h1>
        <p className="text-xs text-muted-foreground">
          Build knowledge bases, test retrieval, and score grounding quality.
        </p>
      </div>
      <div className="grid grid-cols-[220px_1fr] gap-4">
        <div className="space-y-3">
          <CorpusCreateForm onCreated={(c) => { setCorpora((p) => [...p, c]); setSelected(c); }} />
          {corpora.length > 0 && (
            <Card>
              <h2 className="text-xs font-semibold text-muted-foreground mb-2">CORPORA</h2>
              <ul className="space-y-0.5">
                {corpora.map((c) => (
                  <li key={c.entity_key}>
                    <button
                      onClick={() => setSelected(c)}
                      className={`w-full text-left px-2 py-1.5 rounded text-sm truncate ${
                        selected?.entity_key === c.entity_key
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      }`}
                    >
                      {c.name}
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
        <div>
          {selected ? (
            <CorpusDetail corpus={selected} datasets={datasets} />
          ) : (
            <Card>
              <p className="text-sm text-muted-foreground">Create a corpus to get started.</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
