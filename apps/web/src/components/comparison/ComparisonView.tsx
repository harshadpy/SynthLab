import React, { useState, useEffect, useRef } from 'react';
import { Corpus, AnswerResult } from '../../types';
import { api } from '../../services/api';

interface ComparisonViewProps {
  corpus: Corpus;
}

interface ArchStreamState {
  isStreaming: boolean;
  revealedText: string;
  isDone: boolean;
}

function getCleanTopic(corpus: Corpus): string {
  if (corpus.query) return corpus.query;
  const cleaned = corpus.name.replace(/Literature Corpus/i, '').trim();
  return cleaned || 'this research literature';
}

function getRelevantQuestionForCorpus(corpus: Corpus): string {
  const topic = getCleanTopic(corpus);
  if (corpus.papers && corpus.papers.length >= 2) {
    return `Compare the primary architectures, taxonomies, and technical challenges presented across the literature on ${topic}.`;
  }
  if (corpus.papers && corpus.papers.length === 1) {
    return `Explain the core architecture, mechanisms, and key findings introduced in "${corpus.papers[0].title}".`;
  }
  return `What are the core technical architectures, operational mechanisms, and findings established in the literature on ${topic}?`;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ corpus }) => {
  const [query, setQuery] = useState(() => getRelevantQuestionForCorpus(corpus));
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, AnswerResult> | null>(null);
  const [streamState, setStreamState] = useState<Record<string, ArchStreamState>>({});
  const activeTimersRef = useRef<number[]>([]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      activeTimersRef.current.forEach((t) => clearInterval(t));
      activeTimersRef.current = [];
    };
  }, []);

  // Sync benchmark query when corpus changes
  useEffect(() => {
    setQuery(getRelevantQuestionForCorpus(corpus));
    setResults(null);
    setStreamState({});
    activeTimersRef.current.forEach((t) => clearInterval(t));
    activeTimersRef.current = [];
  }, [corpus.id]);

  const handleSkipStreaming = () => {
    activeTimersRef.current.forEach((t) => clearInterval(t));
    activeTimersRef.current = [];
    if (results) {
      const fullDone: Record<string, ArchStreamState> = {};
      Object.entries(results).forEach(([archName, res]) => {
        fullDone[archName] = {
          isStreaming: false,
          revealedText: res.answer,
          isDone: true
        };
      });
      setStreamState(fullDone);
    }
  };

  const handleRunComparison = async (overrideQuery?: string) => {
    const q = (overrideQuery || query).trim();
    if (!q || loading) return;

    activeTimersRef.current.forEach((t) => clearInterval(t));
    activeTimersRef.current = [];

    // Initialize all 5 cards in streaming state
    const initialStream: Record<string, ArchStreamState> = {};
    architectures.forEach((a) => {
      initialStream[a.name] = {
        isStreaming: true,
        revealedText: '',
        isDone: false
      };
    });
    setStreamState(initialStream);
    setLoading(true);
    setResults(null);

    try {
      const data = await api.compareAll(corpus.id, q);
      setResults(data);

      // Launch progressive concurrent word streaming for each architecture card
      architectures.forEach((arch, idx) => {
        const res = data[arch.name];
        if (!res || !res.answer) return;

        const words = res.answer.split(/(\s+)/);
        let wordIndex = 0;
        let currentText = '';

        // Stagger each architecture slightly (idx * 40ms) for high-fidelity multi-pipeline visual
        const timerTimeout = window.setTimeout(() => {
          const intervalTimer = window.setInterval(() => {
            if (wordIndex >= words.length) {
              clearInterval(intervalTimer);
              setStreamState((prev) => ({
                ...prev,
                [arch.name]: {
                  isStreaming: false,
                  revealedText: res.answer,
                  isDone: true
                }
              }));
              return;
            }

            currentText += words[wordIndex] + (words[wordIndex + 1] || '');
            wordIndex += 2;

            setStreamState((prev) => ({
              ...prev,
              [arch.name]: {
                isStreaming: true,
                revealedText: currentText,
                isDone: false
              }
            }));
          }, 14);

          activeTimersRef.current.push(intervalTimer);
        }, idx * 40);

        activeTimersRef.current.push(timerTimeout);
      });
    } catch (e) {
      console.error('Comparison error:', e);
    } finally {
      setLoading(false);
    }
  };

  const isAnyCardStreaming = Object.values(streamState).some((s) => s.isStreaming);

  const topic = getCleanTopic(corpus);

  const promptSuggestions = [
    {
      label: 'Architecture & Taxonomy',
      icon: 'account_tree',
      prompt: `Compare the primary architectures, taxonomy, and system models introduced across the literature on ${topic}.`
    },
    {
      label: 'Core Mechanisms & Workflows',
      icon: 'settings_suggest',
      prompt: `What are the core technical mechanisms, operational workflows, and algorithms established in these papers?`
    },
    {
      label: 'Applications & Benchmarks',
      icon: 'bar_chart',
      prompt: `What empirical benchmarks, evaluation results, and domain applications are demonstrated across the corpus?`
    },
    {
      label: 'Challenges & Future Directions',
      icon: 'warning',
      prompt: `What critical limitations, open questions, and future research directions are highlighted in ${topic}?`
    }
  ];

  const architectures = [
    {
      name: 'Hybrid',
      icon: 'tune',
      badge: 'Dense + BM25s + RRF',
      color: 'text-primary border-primary/40 bg-primary/10'
    },
    {
      name: 'Hierarchical',
      icon: 'account_tree',
      badge: 'Parent-Child 256/2048 Tree',
      color: 'text-cyan-400 border-cyan-400/40 bg-cyan-400/10'
    },
    {
      name: 'GraphRAG',
      icon: 'hub',
      badge: 'Knowledge Graph Traversal',
      color: 'text-indigo-400 border-indigo-400/40 bg-indigo-400/10'
    },
    {
      name: 'Agentic',
      icon: 'smart_toy',
      badge: 'CRAG State Machine',
      color: 'text-amber-400 border-amber-400/40 bg-amber-400/10'
    },
    {
      name: 'Adaptive',
      icon: 'alt_route',
      badge: 'Query Classifier & Routing',
      color: 'text-emerald-400 border-emerald-400/40 bg-emerald-400/10'
    }
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0B0E14] overflow-hidden">
      {/* Header Bar */}
      <div className="p-5 border-b border-outline-variant bg-[#090D15] shrink-0 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-base font-semibold text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">compare_arrows</span>
                Five RAG Architectures — Side-by-Side Benchmark
              </h1>
              <span className="font-mono text-[11px] text-slate-400 bg-surface-container px-2 py-0.5 rounded border border-outline-variant">
                Model: <span className="text-primary font-semibold">gpt-5.6-luna</span>
              </span>
            </div>
            <p className="text-xs text-tertiary-muted mt-0.5">
              Target Corpus: <span className="text-primary font-mono font-medium">{corpus.name}</span> ({corpus.papers.length} papers indexed) · Real-Time Multi-Pipeline Streaming
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isAnyCardStreaming && (
              <button
                type="button"
                onClick={handleSkipStreaming}
                className="px-3 py-1.5 rounded-lg bg-surface-container-high border border-outline-variant hover:border-slate-400 text-slate-300 text-xs font-mono transition-all"
              >
                Skip Animation
              </button>
            )}

            <button
              onClick={() => handleRunComparison()}
              disabled={loading || !query.trim()}
              className="px-4 py-2 rounded-lg bg-primary hover:bg-[#34c4b0] text-[#00201C] text-xs font-bold flex items-center gap-1.5 transition-all shadow-md active:scale-95 disabled:opacity-50"
            >
              {loading ? (
                <span className="w-3.5 h-3.5 border-2 border-[#00201C] border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <span className="material-symbols-outlined text-[16px]">play_arrow</span>
              )}
              <span>{loading ? 'Retrieving & Streaming...' : 'Run All 5 Architectures'}</span>
            </button>
          </div>
        </div>

        {/* Input Query */}
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRunComparison()}
            placeholder={`Enter benchmark research query for ${topic}...`}
            className="w-full h-10 bg-surface-container-low border border-outline-variant rounded-xl px-3.5 text-xs text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors font-sans"
          />
        </div>

        {/* Corpus-Specific Suggestion Pills */}
        <div className="flex items-center gap-2 flex-wrap pt-0.5">
          <span className="text-[11px] font-mono text-tertiary-muted flex items-center gap-1">
            <span className="material-symbols-outlined text-[13px] text-primary">tips_and_updates</span>
            Suggested for {topic}:
          </span>
          {promptSuggestions.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(item.prompt);
                handleRunComparison(item.prompt);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-mono bg-surface-container border border-outline-variant hover:border-primary text-slate-300 hover:text-white transition-colors"
              title={item.prompt}
            >
              <span className="material-symbols-outlined text-[13px] text-primary">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 5-Column Grid Comparison Display */}
      <div className="flex-1 overflow-y-auto custom-scroll p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 items-start">
          {architectures.map((arch) => {
            const res = results?.[arch.name];
            const stream = streamState[arch.name];
            const isStreamingThis = stream?.isStreaming;
            const hasFinishedThis = stream?.isDone;
            const displayText = stream ? stream.revealedText : res?.answer;

            return (
              <div
                key={arch.name}
                className={`bg-[#0E131D] border rounded-2xl p-4 flex flex-col justify-between space-y-3 shadow-lg transition-all min-h-[460px] ${
                  isStreamingThis
                    ? 'border-primary/80 ring-1 ring-primary/40 shadow-primary/10'
                    : 'border-outline-variant/80 hover:border-outline'
                }`}
              >
                <div className="space-y-3">
                  {/* Title & Badge */}
                  <div className="flex items-center justify-between pb-2 border-b border-outline-variant/60">
                    <div className="flex items-center gap-1.5 font-semibold text-sm text-white">
                      <span className="material-symbols-outlined text-primary text-[18px]">{arch.icon}</span>
                      <span>{arch.name}</span>
                    </div>

                    {isStreamingThis && (
                      <span className="flex items-center gap-1 font-mono text-[10px] text-primary">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                        Streaming...
                      </span>
                    )}
                  </div>

                  <span className={`inline-block px-2 py-0.5 rounded font-mono text-[10px] border ${arch.color}`}>
                    {arch.badge}
                  </span>

                  {/* Telemetry Metrics Box */}
                  {res && (hasFinishedThis || !isStreamingThis) ? (
                    <div className="p-2.5 rounded-lg bg-surface-container-low border border-outline-variant/60 font-mono text-[11px] text-tertiary-muted space-y-1">
                      <div className="flex justify-between">
                        <span>Latency:</span>
                        <span className="text-slate-200 font-medium">{res.latency_ms}ms</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Retrieval:</span>
                        <span className="text-slate-400">{res.retrieval_latency_ms}ms</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tokens:</span>
                        <span className="text-slate-200">{res.token_usage?.total}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Citations:</span>
                        <span className="text-primary font-medium">{res.citations?.length || 0}</span>
                      </div>
                    </div>
                  ) : isStreamingThis ? (
                    <div className="p-2.5 rounded-lg bg-surface-container-low border border-primary/30 font-mono text-[11px] text-primary/90 space-y-1 animate-pulse">
                      <div className="flex justify-between">
                        <span>Status:</span>
                        <span className="font-semibold">Synthesizing...</span>
                      </div>
                      <div className="flex justify-between text-tertiary-muted">
                        <span>Model:</span>
                        <span>gpt-5.6-luna</span>
                      </div>
                      <div className="flex justify-between text-tertiary-muted">
                        <span>Telemetry:</span>
                        <span>Logging to LangSmith</span>
                      </div>
                    </div>
                  ) : (
                    <div className="p-2.5 rounded-lg bg-surface-container-low border border-outline-variant/40 font-mono text-[11px] text-tertiary-muted">
                      Click "Run All 5 Architectures" to benchmark.
                    </div>
                  )}

                  {/* Answer Text Block with Streaming Effect */}
                  <div className="text-xs text-slate-300 leading-relaxed">
                    {displayText || isStreamingThis ? (
                      <div className="space-y-2 max-h-72 overflow-y-auto custom-scroll pr-1">
                        <p className="whitespace-pre-line">
                          {displayText}
                          {isStreamingThis && (
                            <span className="inline-block w-1.5 h-3.5 bg-primary ml-1 animate-pulse align-middle"></span>
                          )}
                        </p>

                        {/* Citations appear when finished */}
                        {hasFinishedThis && res?.citations && res.citations.length > 0 && (
                          <div className="pt-2 border-t border-outline-variant/40 flex flex-wrap gap-1 font-mono text-[10px]">
                            <span className="text-tertiary-muted">Grounded:</span>
                            {res.citations.map((c, cIdx) => (
                              <span
                                key={cIdx}
                                className="px-1.5 py-0.2 rounded bg-surface-container border border-outline-variant text-primary"
                                title={`${c.paper_title} (p. ${c.page_number})`}
                              >
                                [{cIdx + 1}] p.{c.page_number}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="h-32 flex flex-col items-center justify-center text-tertiary-muted text-xs font-mono space-y-1 text-center">
                        <span className="material-symbols-outlined text-[24px] opacity-40">science</span>
                        <span>Ready for benchmark</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Grounded LangSmith Trace Footer */}
                {res?.trace_id && (hasFinishedThis || !isStreamingThis) && (
                  <div className="pt-2 border-t border-outline-variant/60 font-mono text-[10px] text-tertiary-muted flex items-center justify-between">
                    <span className="truncate max-w-[120px]" title={res.trace_id}>
                      {res.trace_id}
                    </span>
                    <a
                      href="https://smith.langchain.com/projects/raglab"
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-400 hover:underline flex items-center gap-0.5 shrink-0"
                      title="View verified run in LangSmith"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span>Traced</span>
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
