import React, { useState, useEffect } from 'react';
import { Corpus, MetricSummary } from '../../types';
import { api } from '../../services/api';

interface EvaluationViewProps {
  corpus: Corpus;
}

export const EvaluationView: React.FC<EvaluationViewProps> = ({ corpus }) => {
  const [metrics, setMetrics] = useState<Record<string, MetricSummary>>({});
  const [loading, setLoading] = useState(false);

  const loadEvaluation = async (forceRerun: boolean = false) => {
    setLoading(true);
    try {
      const data = await api.runEvaluation(corpus.id, forceRerun);
      setMetrics(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvaluation(false);
  }, [corpus.id]);

  const archList = Object.values(metrics);

  const bestCorrectness = archList.length ? archList.reduce((max, p) => p.correctness > max.correctness ? p : max, archList[0]) : null;
  const bestFaithfulness = archList.length ? archList.reduce((max, p) => p.faithfulness > max.faithfulness ? p : max, archList[0]) : null;
  const bestRecall = archList.length ? archList.reduce((max, p) => p.recall_at_k > max.recall_at_k ? p : max, archList[0]) : null;
  const fastest = archList.length ? archList.reduce((min, p) => p.latency_ms < min.latency_ms ? p : min, archList[0]) : null;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0B0E14] overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-outline-variant bg-[#090D15] shrink-0 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">analytics</span>
              LangSmith-Powered Evaluation Dashboard
            </h1>
            <p className="text-xs text-tertiary-muted mt-0.5">
              Benchmark Dataset: <span className="text-slate-300 font-mono">ArXiv RAG Benchmark · Grounded on {corpus.name}</span> · Reproducible evaluation across all 5 architectures
            </p>
          </div>
          <button
            onClick={() => loadEvaluation(true)}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-surface-container-high border border-outline-variant hover:border-primary text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-all"
          >
            <span className={`material-symbols-outlined text-[15px] ${loading ? 'animate-spin' : ''}`}>
              refresh
            </span>
            <span>Re-run Evaluation</span>
          </button>
        </div>

        {/* Collapsible Monospace Experiment Metadata Strip */}
        <div className="p-2 px-3 rounded-lg bg-surface-container-low border border-outline-variant/60 flex flex-wrap items-center gap-4 font-mono text-[11px] text-tertiary-muted">
          <span><span className="text-slate-400">Git Commit:</span> main-e9b42</span>
          <span><span className="text-slate-400">Corpus:</span> {corpus.name}</span>
          <span><span className="text-slate-400">Dataset:</span> v1.0.0</span>
          <span><span className="text-slate-400">Eval Model:</span> gpt-5.6-luna</span>
          <span><span className="text-slate-400">Embeddings:</span> text-embedding-3-large</span>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto custom-scroll p-6 space-y-6">
        {/* KPI Tiles Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-surface-container rounded-2xl border border-outline-variant space-y-1">
            <span className="font-mono text-[10px] uppercase text-tertiary-muted tracking-wider">Best Correctness</span>
            <div className="text-xl font-bold font-mono text-primary">
              {bestCorrectness ? (bestCorrectness.correctness * 100).toFixed(1) + '%' : '—'}
            </div>
            <div className="text-xs text-slate-300 truncate">{bestCorrectness?.architecture || '—'}</div>
          </div>

          <div className="p-4 bg-surface-container rounded-2xl border border-outline-variant space-y-1">
            <span className="font-mono text-[10px] uppercase text-tertiary-muted tracking-wider">Best Faithfulness</span>
            <div className="text-xl font-bold font-mono text-cyan-400">
              {bestFaithfulness ? (bestFaithfulness.faithfulness * 100).toFixed(1) + '%' : '—'}
            </div>
            <div className="text-xs text-slate-300 truncate">{bestFaithfulness?.architecture || '—'}</div>
          </div>

          <div className="p-4 bg-surface-container rounded-2xl border border-outline-variant space-y-1">
            <span className="font-mono text-[10px] uppercase text-tertiary-muted tracking-wider">Highest Recall@K</span>
            <div className="text-xl font-bold font-mono text-indigo-400">
              {bestRecall ? (bestRecall.recall_at_k * 100).toFixed(1) + '%' : '—'}
            </div>
            <div className="text-xs text-slate-300 truncate">{bestRecall?.architecture || '—'}</div>
          </div>

          <div className="p-4 bg-surface-container rounded-2xl border border-outline-variant space-y-1">
            <span className="font-mono text-[10px] uppercase text-tertiary-muted tracking-wider">Fastest Pipeline</span>
            <div className="text-xl font-bold font-mono text-emerald-400">
              {fastest ? `${fastest.latency_ms}ms` : '—'}
            </div>
            <div className="text-xs text-slate-300 truncate">{fastest?.architecture || '—'}</div>
          </div>
        </div>

        {/* Comparative Metric Matrix Table */}
        <div className="bg-surface-container rounded-2xl border border-outline-variant overflow-hidden shadow-lg">
          <div className="p-4 border-b border-outline-variant flex items-center justify-between">
            <span className="font-mono text-xs font-semibold text-white uppercase tracking-wider">
              Architecture Performance Matrix
            </span>
            <span className="font-mono text-[11px] text-tertiary-muted">Evaluated on identical inputs</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-surface-container-high/60 border-b border-outline-variant/60 text-tertiary-muted">
                <tr>
                  <th className="py-3 px-4">Architecture</th>
                  <th className="py-3 px-4 text-right">Correctness</th>
                  <th className="py-3 px-4 text-right">Faithfulness</th>
                  <th className="py-3 px-4 text-right">Recall@K</th>
                  <th className="py-3 px-4 text-right">Latency</th>
                  <th className="py-3 px-4 text-right">Tokens</th>
                  <th className="py-3 px-4 text-right">Cost / 1k</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/40 text-slate-200">
                {archList.map((row) => (
                  <tr key={row.architecture} className="hover:bg-surface-container-high/40 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-primary"></span>
                      <span>{row.architecture}</span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="font-medium text-primary">{(row.correctness * 100).toFixed(1)}%</span>
                      <div className="w-16 h-1 bg-surface-container-low rounded-full ml-auto mt-1 overflow-hidden">
                        <div className="h-full bg-primary rounded-full" style={{ width: `${row.correctness * 100}%` }}></div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="font-medium text-cyan-400">{(row.faithfulness * 100).toFixed(1)}%</span>
                      <div className="w-16 h-1 bg-surface-container-low rounded-full ml-auto mt-1 overflow-hidden">
                        <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${row.faithfulness * 100}%` }}></div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="font-medium text-indigo-400">{(row.recall_at_k * 100).toFixed(1)}%</span>
                      <div className="w-16 h-1 bg-surface-container-low rounded-full ml-auto mt-1 overflow-hidden">
                        <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${row.recall_at_k * 100}%` }}></div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-300">
                      {row.latency_ms}ms
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-400">
                      {row.tokens}
                    </td>
                    <td className="py-3.5 px-4 text-right text-secondary font-medium">
                      {row.estimated_cost}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Normalized Radar Profile */}
        <div className="p-5 bg-surface-container rounded-2xl border border-outline-variant space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-semibold text-white uppercase tracking-wider">
              Normalized Quality vs Cost Profile
            </span>
            <span className="font-mono text-[11px] text-tertiary-muted">Higher = Better</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2">
            {archList.map((item) => (
              <div key={item.architecture} className="p-3 bg-surface-container-low rounded-xl border border-outline-variant/60 space-y-2">
                <div className="text-xs font-semibold text-white">{item.architecture}</div>
                <div className="space-y-1.5 font-mono text-[10px]">
                  <div className="flex justify-between text-slate-400">
                    <span>Quality:</span>
                    <span className="text-primary font-medium">{Math.round((item.correctness + item.faithfulness) * 50)}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Speed:</span>
                    <span className="text-slate-200 font-medium">{Math.max(100 - Math.round(item.latency_ms / 6), 10)}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Efficiency:</span>
                    <span className="text-secondary font-medium">{Math.max(100 - Math.round(item.tokens / 16), 10)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
