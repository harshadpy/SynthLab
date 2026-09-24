import React, { useState, useEffect } from 'react';
import { Corpus } from '../../types';
import { api } from '../../services/api';

interface InsightsViewProps {
  corpus: Corpus;
}

export const InsightsView: React.FC<InsightsViewProps> = ({ corpus }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadInsights = async () => {
      setLoading(true);
      try {
        const res = await api.getInsights(corpus.id);
        setData(res);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadInsights();
  }, [corpus.id]);

  const handleExport = () => {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `corpus-${corpus.id}-insights.json`;
    a.click();
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0B0E14] overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-outline-variant bg-[#090D15] shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]">lightbulb</span>
            Corpus-Wide Literature Insights
          </h1>
          <p className="text-xs text-tertiary-muted mt-0.5">
            Synthesized across {corpus.paper_count || 7} indexed research papers
          </p>
        </div>
        <button
          onClick={handleExport}
          className="px-3.5 py-1.5 rounded-lg bg-surface-container-high border border-outline-variant hover:border-primary text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-all shadow-sm"
        >
          <span className="material-symbols-outlined text-[15px] text-primary">file_download</span>
          <span>Export Insights (.json)</span>
        </button>
      </div>

      {/* 2-Column Content Grid */}
      <div className="flex-1 overflow-y-auto custom-scroll p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card 1: Common Themes (Frequency tag cloud in teal shades) */}
          <div className="bg-surface-container rounded-2xl border border-outline-variant p-5 space-y-3 shadow-lg">
            <div className="flex items-center justify-between pb-2 border-b border-outline-variant/60">
              <span className="font-mono text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-[16px]">tag</span>
                Core Thematic Clusters
              </span>
              <span className="font-mono text-[11px] text-tertiary-muted">Frequency &amp; Relevance</span>
            </div>

            <div className="flex flex-wrap gap-2.5 pt-2">
              {data?.themes?.map((t: any) => (
                <span
                  key={t.name}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/30 text-xs font-mono font-medium text-primary hover:bg-primary/20 transition-colors"
                >
                  <span>{t.name}</span>
                  <span className="text-[10px] px-1 py-0.2 rounded bg-primary/20 text-white font-bold">
                    {t.frequency}
                  </span>
                </span>
              ))}
            </div>
          </div>

          {/* Card 2: Method Comparison Matrix */}
          <div className="bg-surface-container rounded-2xl border border-outline-variant p-5 space-y-3 shadow-lg">
            <div className="flex items-center justify-between pb-2 border-b border-outline-variant/60">
              <span className="font-mono text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-[16px]">tune</span>
                Method Comparison
              </span>
            </div>

            <div className="space-y-2.5 pt-1">
              {data?.method_comparison?.map((m: any) => (
                <div key={m.method} className="p-3 rounded-xl bg-surface-container-low border border-outline-variant/60 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white">{m.method}</span>
                    <span className="font-mono text-[10px] text-primary">{m.papers.join(', ')}</span>
                  </div>
                  <div className="text-[11px] text-slate-300 font-mono">{m.mechanism}</div>
                  <div className="flex items-center gap-2 pt-1 font-mono text-[10px] text-tertiary-muted">
                    <span className="text-emerald-400">Pros: {m.pros}</span>
                    <span>·</span>
                    <span className="text-secondary">Limit: {m.limitations}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Card 3: Limitations Grouped by Paper */}
        <div className="bg-surface-container rounded-2xl border border-outline-variant p-5 space-y-3 shadow-lg">
          <div className="flex items-center justify-between pb-2 border-b border-outline-variant/60">
            <span className="font-mono text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-primary text-[16px]">report_problem</span>
              Documented Limitations &amp; Research Gaps
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            {data?.limitations?.map((l: any, idx: number) => (
              <div key={idx} className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">{l.paper}</span>
                  <span className="font-mono text-[10px] text-tertiary-muted">{l.evidence_page}</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {l.limitation}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Card 4: Horizontal Research Timeline */}
        <div className="bg-surface-container rounded-2xl border border-outline-variant p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between pb-2 border-b border-outline-variant/60">
            <span className="font-mono text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-primary text-[16px]">timeline</span>
              Research Evolution &amp; Milestone Timeline
            </span>
          </div>

          <div className="relative pt-4 pb-2">
            <div className="absolute top-7 left-0 right-0 h-[2px] bg-outline-variant" />
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative z-10">
              {data?.timeline?.map((point: any, idx: number) => (
                <div key={idx} className="flex flex-col items-start space-y-2">
                  <div className="w-6 h-6 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center font-mono text-[10px] text-primary font-bold shadow-sm">
                    {idx + 1}
                  </div>
                  <div className="space-y-0.5">
                    <span className="font-mono text-[10px] text-primary font-medium">{point.date}</span>
                    <h4 className="text-xs font-semibold text-white leading-snug">{point.title}</h4>
                    <p className="text-[11px] text-tertiary-muted leading-tight pt-1">{point.milestone}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
