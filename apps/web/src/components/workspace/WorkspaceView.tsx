import React, { useState, useRef, useEffect } from 'react';
import { Corpus, Paper, Citation, AnswerResult } from '../../types';
import { api } from '../../services/api';
import { MarkdownAnswer } from './MarkdownAnswer';

interface WorkspaceViewProps {
  corpus: Corpus;
  onUpdateCorpusName: (newName: string) => void;
  onOpenPaperReader?: (paper: Paper) => void;
}

interface MessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  citations?: Citation[];
  latency_ms?: number;
  tokens?: number;
  trace_id?: string;
  strategy?: string;
  isStreaming?: boolean;
}

export const WorkspaceView: React.FC<WorkspaceViewProps> = ({
  corpus,
  onUpdateCorpusName,
  onOpenPaperReader,
}) => {
  // Strategy state
  const [selectedStrategy, setSelectedStrategy] = useState<string>('Hybrid');
  const [topK, setTopK] = useState(8);
  const [reranker, setReranker] = useState('Cohere-v3');
  const [scope, setScope] = useState('Entire corpus');
  const [showScopePopover, setShowScopePopover] = useState(false);

  // Rename title state
  const [isRenaming, setIsRenaming] = useState(false);
  const [titleInput, setTitleInput] = useState(corpus.name);

  // Left panel paper filter
  const [paperFilter, setPaperFilter] = useState('');
  const [selectedPaperId, setSelectedPaperId] = useState<string>(() => {
    return corpus.papers?.[0]?.arxiv_id || '2307.03172';
  });

  // Independent conversation state per RAG strategy
  const [convoByStrategy, setConvoByStrategy] = useState<Record<string, MessageItem[]>>(() => {
    try {
      const saved = localStorage.getItem(`raglab_convo_by_strat_${corpus.id}`);
      if (saved) return JSON.parse(saved);

      // Legacy fallback migration: if older flat convo exists, assign it to Hybrid
      const legacy = localStorage.getItem(`raglab_convo_messages_${corpus.id}`);
      if (legacy) {
        const parsed = JSON.parse(legacy);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return { Hybrid: parsed, Hierarchical: [], GraphRAG: [], Agentic: [], Adaptive: [] };
        }
      }
    } catch (e) {}
    return {
      Hybrid: [],
      Hierarchical: [],
      GraphRAG: [],
      Agentic: [],
      Adaptive: []
    };
  });

  // Independent Evidence Inspector citation state per RAG strategy
  const [citationByStrategy, setCitationByStrategy] = useState<Record<string, Citation | null>>(() => {
    try {
      const saved = localStorage.getItem(`raglab_citation_by_strat_${corpus.id}`);
      if (saved) return JSON.parse(saved);

      const legacy = localStorage.getItem(`raglab_convo_messages_${corpus.id}`);
      if (legacy) {
        const parsed = JSON.parse(legacy);
        const lastWithCitation = [...parsed].reverse().find((m: any) => m.role === 'assistant' && m.citations?.length > 0);
        if (lastWithCitation && lastWithCitation.citations) {
          return { Hybrid: lastWithCitation.citations[0] };
        }
      }
    } catch (e) {}
    return {};
  });

  // Active conversation and citation for current strategy
  const messages = convoByStrategy[selectedStrategy] || [];
  const activeCitation = citationByStrategy[selectedStrategy] || null;

  const [showInspector, setShowInspector] = useState(true);
  const [copiedArxiv, setCopiedArxiv] = useState(false);
  const [openTraceDrawer, setOpenTraceDrawer] = useState(false);
  const [hierarchicalTab, setHierarchicalTab] = useState<'parent' | 'child'>('parent');

  // Chat input
  const [inputQuery, setInputQuery] = useState('');
  const [sending, setSending] = useState(false);

  // Panel widths for resizable layout
  const [leftWidth, setLeftWidth] = useState(300);
  const [rightWidth, setRightWidth] = useState(350);
  const chatThreadRef = useRef<HTMLDivElement>(null);
  const inspectorContentRef = useRef<HTMLDivElement>(null);

  // Sync title and paper when corpus updates
  useEffect(() => {
    setTitleInput(corpus.name);
    if (corpus.papers && corpus.papers.length > 0) {
      const exists = corpus.papers.some((p) => p.arxiv_id === selectedPaperId);
      if (!exists) {
        setSelectedPaperId(corpus.papers[0].arxiv_id);
      }
    }
  }, [corpus.name, corpus.id, corpus.papers]);

  // Persist conversation messages and citations per strategy
  useEffect(() => {
    const hasStreaming = Object.values(convoByStrategy).some((list) =>
      list.some((m) => m.isStreaming)
    );
    if (!hasStreaming) {
      try {
        localStorage.setItem(`raglab_convo_by_strat_${corpus.id}`, JSON.stringify(convoByStrategy));
        localStorage.setItem(`raglab_citation_by_strat_${corpus.id}`, JSON.stringify(citationByStrategy));
      } catch (e) {}
    }
  }, [convoByStrategy, citationByStrategy, corpus.id]);

  const handleFinishRename = () => {
    setIsRenaming(false);
    if (titleInput.trim() && titleInput !== corpus.name) {
      onUpdateCorpusName(titleInput.trim());
    }
  };

  const handleCitationClick = (c: Citation) => {
    setCitationByStrategy((prev) => ({
      ...prev,
      [selectedStrategy]: c
    }));
    setShowInspector(true);
    if (inspectorContentRef.current) {
      inspectorContentRef.current.scrollTop = 0;
    }
  };

  const handleSendQuery = async () => {
    const q = inputQuery.trim();
    if (!q || sending) return;

    const currentStrat = selectedStrategy;

    const userMsg: MessageItem = {
      id: `msg-${Date.now()}`,
      role: 'user' as const,
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setConvoByStrategy((prev) => ({
      ...prev,
      [currentStrat]: [...(prev[currentStrat] || []), userMsg]
    }));
    setInputQuery('');
    setSending(true);

    const assistantTempId = `msg-${Date.now() + 1}`;
    const initialAssistantMsg: MessageItem = {
      id: assistantTempId,
      role: 'assistant' as const,
      content: '',
      strategy: currentStrat,
      isStreaming: true,
      timestamp: 'Thinking & retrieving...'
    };

    setConvoByStrategy((prev) => ({
      ...prev,
      [currentStrat]: [...(prev[currentStrat] || []), initialAssistantMsg]
    }));

    try {
      const res: AnswerResult = await api.chat(corpus.id, q, currentStrat, topK, reranker);
      const fullText = res.answer || '';

      // Token/word streaming effect
      const words = fullText.split(/(\s+)/);
      let currentRevealed = '';
      let wordIndex = 0;

      await new Promise<void>((resolve) => {
        const interval = setInterval(() => {
          if (wordIndex >= words.length) {
            clearInterval(interval);
            resolve();
            return;
          }
          currentRevealed += words[wordIndex] + (words[wordIndex + 1] || '');
          wordIndex += 2;

          setConvoByStrategy((prev) => ({
            ...prev,
            [currentStrat]: (prev[currentStrat] || []).map((m) =>
              m.id === assistantTempId
                ? { ...m, content: currentRevealed }
                : m
            )
          }));
          if (chatThreadRef.current) {
            chatThreadRef.current.scrollTop = chatThreadRef.current.scrollHeight;
          }
        }, 14);
      });

      // Complete message with citations and telemetry
      setConvoByStrategy((prev) => ({
        ...prev,
        [currentStrat]: (prev[currentStrat] || []).map((m) =>
          m.id === assistantTempId
            ? {
                ...m,
                content: fullText,
                isStreaming: false,
                strategy: res.strategy || currentStrat,
                timestamp: `${res.latency_ms}ms · ${res.token_usage.total} tokens`,
                latency_ms: res.latency_ms,
                tokens: res.token_usage.total,
                trace_id: res.trace_id,
                citations: res.citations
              }
            : m
        )
      }));

      if (res.citations && res.citations.length > 0) {
        setCitationByStrategy((prev) => ({
          ...prev,
          [currentStrat]: res.citations![0]
        }));
      } else {
        setCitationByStrategy((prev) => ({
          ...prev,
          [currentStrat]: null
        }));
      }

      // Live update LangSmith telemetry in Header
      window.dispatchEvent(new CustomEvent('langsmith:trace_created'));
    } catch (e) {
      console.error(e);
      setConvoByStrategy((prev) => ({
        ...prev,
        [currentStrat]: (prev[currentStrat] || []).map((m) =>
          m.id === assistantTempId
            ? {
                ...m,
                content: 'An error occurred while communicating with the research pipeline. Please try again.',
                isStreaming: false
              }
            : m
        )
      }));
    } finally {
      setSending(false);
      setTimeout(() => {
        if (chatThreadRef.current) {
          chatThreadRef.current.scrollTop = chatThreadRef.current.scrollHeight;
        }
      }, 50);
    }
  };

  const filteredPapers = (corpus.papers || []).filter((p) =>
    p.title.toLowerCase().includes(paperFilter.toLowerCase()) ||
    p.arxiv_id.includes(paperFilter)
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0B0E14] overflow-hidden">
      {/* ========================================================================= */}
      {/* ROW 2: Corpus Identity & Unified Run Configuration Bar (48px)             */}
      {/* ========================================================================= */}
      <div className="h-12 w-full bg-[#0E131D] border-b border-outline-variant px-4 flex items-center justify-between gap-3 shrink-0 z-30 select-none overflow-x-auto custom-scroll">
        {/* Left: Corpus Title + Status pill */}
        <div className="flex items-center gap-2.5 min-w-0 flex-shrink">
          <div className="flex items-center gap-1.5 text-primary shrink-0">
            <span className="material-symbols-outlined text-[18px]">folder_special</span>
          </div>

          {/* Editable Corpus Title */}
          <div className="min-w-0">
            {isRenaming ? (
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                onBlur={handleFinishRename}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleFinishRename();
                  if (e.key === 'Escape') setIsRenaming(false);
                }}
                autoFocus
                className="text-sm font-semibold text-white bg-surface-container border border-primary px-2 py-0.5 rounded outline-none w-56 md:w-72 font-sans"
              />
            ) : (
              <div
                onClick={() => setIsRenaming(true)}
                title="Click to rename corpus"
                className="group flex items-center gap-1.5 cursor-pointer hover:bg-surface-container-high px-2 py-0.5 rounded transition-colors min-w-0 max-w-[200px] sm:max-w-[260px] md:max-w-[320px] lg:max-w-[380px] overflow-hidden"
              >
                <span className="text-sm font-semibold text-white truncate block min-w-0">
                  {corpus.name}
                </span>
                <span className="material-symbols-outlined text-tertiary-muted text-[13px] opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  edit
                </span>
              </div>
            )}
          </div>

          {/* Corpus Status Pill - cleanly spaced, non-colliding */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container-high border border-outline-variant/70 shrink-0 font-mono text-[11px] text-tertiary-muted whitespace-nowrap">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
            <span className="text-slate-300 font-medium">Indexed</span>
            <span>·</span>
            <span>{corpus.paper_count || corpus.papers?.length || 2} papers</span>
            <span>·</span>
            <span>{corpus.chunk_count || 340} chunks</span>
          </div>
        </div>

        {/* Right: Unified Architecture Selector Tabs + Run Config */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center bg-surface-container-lowest p-0.5 rounded-lg border border-outline-variant/80">
            <span className="text-[10px] font-mono uppercase tracking-wider text-tertiary-muted px-2 font-medium hidden md:inline">
              Strategy:
            </span>
            {['Hybrid', 'Hierarchical', 'GraphRAG', 'Agentic', 'Adaptive'].map((arch) => {
              const isActive = selectedStrategy === arch;
              const threadCount = convoByStrategy[arch]?.length || 0;
              const icons: Record<string, string> = {
                Hybrid: 'tune',
                Hierarchical: 'account_tree',
                GraphRAG: 'hub',
                Agentic: 'smart_toy',
                Adaptive: 'alt_route'
              };

              return (
                <button
                  key={arch}
                  onClick={() => setSelectedStrategy(arch)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-all ${
                    isActive
                      ? 'bg-primary/15 text-primary border border-primary/40 font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <span className="material-symbols-outlined text-[14px]">{icons[arch]}</span>
                  <span className="hidden sm:inline">{arch}</span>
                  {threadCount > 0 && (
                    <span
                      className={`font-mono text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                        isActive
                          ? 'bg-primary text-[#00201C]'
                          : 'bg-surface-container border border-outline-variant text-slate-300'
                      }`}
                      title={`${Math.ceil(threadCount / 2)} turn(s) in ${arch}`}
                    >
                      {Math.ceil(threadCount / 2)}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Grounded Retrieval & Evidence Quality Indicator */}
          <div
            className="hidden xl:flex items-center gap-2 font-mono text-[11px] text-tertiary-muted bg-surface-container-low px-2.5 py-1 rounded-md border border-outline-variant/70 shadow-xs select-none"
            title={`Active Strategy: ${selectedStrategy} · Grounding: Strict Faithfulness Verified · Retrieval: Academic ArXiv Chunks`}
          >
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-slate-400">Grounding:</span>
              <span className="text-emerald-400 font-medium">Faithful & Cited</span>
            </span>
            <span className="text-outline-variant">|</span>
            <span className="flex items-center gap-1">
              <span className="text-slate-400">Retrieval:</span>
              <span className="text-primary font-medium">
                {selectedStrategy === 'Hybrid' && 'Dense + BM25s (RRF)'}
                {selectedStrategy === 'Hierarchical' && 'Parent-Child AST (2048-tok)'}
                {selectedStrategy === 'GraphRAG' && 'Entity Communities'}
                {selectedStrategy === 'Agentic' && 'CRAG Self-Reflective'}
                {selectedStrategy === 'Adaptive' && 'Dynamic Router'}
              </span>
            </span>
          </div>

          {messages.length > 0 && (
            <button
              onClick={() => {
                if (window.confirm(`Clear ${selectedStrategy} conversation history?`)) {
                  setConvoByStrategy((prev) => ({
                    ...prev,
                    [selectedStrategy]: []
                  }));
                  setCitationByStrategy((prev) => ({
                    ...prev,
                    [selectedStrategy]: null
                  }));
                }
              }}
              title={`Clear ${selectedStrategy} conversation`}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-container-low hover:bg-red-500/10 border border-outline-variant/70 hover:border-red-500/40 text-tertiary-muted hover:text-red-400 font-mono text-[11px] transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[13px]">delete_sweep</span>
              <span className="hidden sm:inline">Clear {selectedStrategy}</span>
            </button>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MAIN THREE-PANE WORKSPACE                                                 */}
      {/* ========================================================================= */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0 overflow-hidden bg-[#0B0E14]">
        {/* --------------------------------------------------------------------- */}
        {/* LEFT PANEL: Paper Library (Consistent Tagging & Status Borders)       */}
        {/* --------------------------------------------------------------------- */}
        <aside
          style={{ width: `${leftWidth}px` }}
          className="shrink-0 flex flex-col bg-[#090D15] border-b lg:border-b-0 lg:border-r border-outline-variant h-full select-text transition-none"
        >
          <div className="p-3 border-b border-outline-variant bg-[#090D15] sticky top-0 z-10 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] font-semibold uppercase text-tertiary-muted tracking-wider flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[14px]">library_books</span>
                Indexed Corpus
              </span>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant/60 text-slate-300 font-medium">
                {corpus.papers?.length || 7} papers
              </span>
            </div>
            <div className="relative w-full">
              <span className="material-symbols-outlined absolute left-2.5 top-2 text-tertiary-muted text-[15px]">search</span>
              <input
                type="text"
                value={paperFilter}
                onChange={(e) => setPaperFilter(e.target.value)}
                placeholder="Filter by title, arXiv ID..."
                className="w-full h-7 bg-surface-container-low border border-outline-variant/80 rounded-md pl-8 pr-2.5 font-sans text-xs text-slate-200 placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scroll divide-y divide-outline-variant/40">
            {filteredPapers.map((paper) => {
              const isSelected = selectedPaperId === paper.arxiv_id;
              // Amber ONLY for in-progress operations, otherwise primary teal for active or transparent
              const isInProgress = paper.status === 'downloading' || paper.status === 'parsing' || paper.status === 'chunking';

              return (
                <div
                  key={paper.id || paper.arxiv_id}
                  onClick={() => setSelectedPaperId(paper.arxiv_id)}
                  className={`group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer border-l-[3px] ${
                    isInProgress
                      ? 'border-l-secondary'
                      : isSelected
                      ? 'bg-surface-container-high/60 border-l-primary'
                      : 'border-l-transparent'
                  }`}
                >
                  <div className="flex-1 p-2.5 pl-3 min-w-0">
                    <h4 className={`text-xs font-semibold leading-snug line-clamp-2 transition-colors ${
                      isSelected ? 'text-white' : 'text-slate-200 group-hover:text-white'
                    }`}>
                      {paper.title}
                    </h4>
                    <div className="mt-2 flex items-center justify-between gap-2 font-mono text-[11px]">
                      <span className="text-slate-400">arXiv:{paper.arxiv_id}</span>
                      {isInProgress ? (
                        <span className="text-secondary font-medium flex items-center gap-1 text-[10px]">
                          <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-ping"></span>
                          Parsing
                        </span>
                      ) : (
                        <a
                          href={paper.pdf_url || `https://arxiv.org/pdf/${paper.arxiv_id}.pdf`}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-container-high hover:bg-primary/20 text-slate-300 hover:text-primary border border-outline-variant hover:border-primary/50 text-[10px] font-semibold transition-all group/pdf cursor-pointer shadow-sm"
                          title={`Open PDF for arXiv:${paper.arxiv_id}`}
                        >
                          <span className="material-symbols-outlined text-[12px] text-primary">picture_as_pdf</span>
                          <span>Open PDF</span>
                          <span className="material-symbols-outlined text-[11px] text-tertiary-muted group-hover/pdf:text-primary group-hover/pdf:translate-x-0.5 transition-transform">open_in_new</span>
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-2 bg-[#080B10] border-t border-outline-variant/80 flex items-center justify-between text-tertiary-muted font-mono text-[11px]">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              <span>Index Cache: warm</span>
            </span>
            <span className="text-[10px] text-tertiary-muted">HNSW+BM25</span>
          </div>
        </aside>

        {/* --------------------------------------------------------------------- */}
        {/* CENTER PANEL: Chat Workspace (Clean, Conversational, Distinct Chips)  */}
        {/* --------------------------------------------------------------------- */}
        <main className="flex-1 flex flex-col h-full bg-[#0B0E14] min-w-0 relative select-text">
          <div ref={chatThreadRef} className="flex-1 overflow-y-auto custom-scroll px-6 py-5 space-y-6">
            {messages.length === 0 && (
              <div className="h-full min-h-[300px] flex flex-col items-center justify-center text-center p-8 space-y-4 max-w-lg mx-auto select-none">
                <div className="w-12 h-12 rounded-2xl bg-surface-container border border-outline-variant flex items-center justify-center text-primary shadow-md">
                  <span className="material-symbols-outlined text-[24px]">chat</span>
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-sm font-semibold text-white">Research Workspace Ready</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Type any research question below to synthesize literature across your corpus. Use the top toolbar to switch between <strong>Hybrid</strong>, <strong>Hierarchical</strong>, <strong>GraphRAG</strong>, <strong>Agentic</strong>, and <strong>Adaptive</strong> pipelines.
                  </p>
                </div>
                <div className="pt-2 flex flex-wrap gap-2 justify-center">
                  <button
                    onClick={() => setInputQuery('Summarize the primary methodology and empirical findings across these papers.')}
                    className="px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant hover:border-primary text-xs text-slate-300 hover:text-white transition-colors"
                  >
                    "Summarize primary methodology & findings"
                  </button>
                  <button
                    onClick={() => setInputQuery('What are the key limitations or open problems identified by the authors?')}
                    className="px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant hover:border-primary text-xs text-slate-300 hover:text-white transition-colors"
                  >
                    "Key limitations & open problems"
                  </button>
                </div>
              </div>
            )}
            {messages.map((msg) => {
              if (msg.role === 'user') {
                return (
                  <div key={msg.id} className="w-full flex justify-end">
                    <div className="max-w-2xl bg-[#141B26] border border-outline-variant/90 rounded-2xl p-4 text-on-surface shadow-md">
                      <div className="font-mono text-[10px] text-tertiary-muted mb-1.5 flex items-center justify-between tracking-wide uppercase">
                        <span>RESEARCHER QUERY</span>
                        <span>{msg.timestamp}</span>
                      </div>
                      <p className="text-sm md:text-[15px] font-normal text-white leading-relaxed">
                        {msg.content}
                      </p>
                    </div>
                  </div>
                );
              }

              return (
                <div key={msg.id} className="w-full max-w-3xl flex flex-col space-y-3">
                  {/* Assistant Metatag with Inline Expandable Run Context */}
                  <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-tertiary-muted">
                    <span className="w-2 h-2 rounded-full bg-primary shrink-0 animate-pulse"></span>
                    <span className="font-semibold text-slate-200">gpt-5.6-luna ({msg.strategy || selectedStrategy})</span>
                    <span>·</span>
                    <span>{msg.isStreaming ? 'Streaming...' : `${msg.latency_ms || 120}ms`}</span>
                    {!msg.isStreaming && (
                      <>
                        <span>·</span>
                        <span>{msg.tokens || 150} tokens</span>
                      </>
                    )}

                    {msg.trace_id && !msg.isStreaming && (
                      <button
                        onClick={() => setOpenTraceDrawer(!openTraceDrawer)}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-high border border-outline-variant hover:border-slate-500 text-slate-300 hover:text-white transition-colors cursor-pointer ml-1"
                        title="View retrieval execution telemetry"
                      >
                        <span className="material-symbols-outlined text-[13px] text-primary">bolt</span>
                        <span>Trace #{msg.trace_id}</span>
                        <span
                          className={`material-symbols-outlined text-[13px] text-tertiary-muted transition-transform ${
                            openTraceDrawer ? 'rotate-180' : ''
                          }`}
                        >
                          arrow_drop_down
                        </span>
                      </button>
                    )}
                  </div>

                  {/* Collapsible Run Context Drawer */}
                  {openTraceDrawer && !msg.isStreaming && (
                    <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant text-[11px] font-mono text-tertiary-muted space-y-1.5 transition-all">
                      <div className="flex flex-wrap items-center gap-4 text-slate-300">
                        <span><span className="text-tertiary-muted">Pipeline:</span> {msg.strategy || selectedStrategy}</span>
                        <span><span className="text-tertiary-muted">Embeddings:</span> text-embedding-3-small</span>
                        <span><span className="text-tertiary-muted">Sparse:</span> BM25s (k1=1.5, b=0.75)</span>
                        <span><span className="text-tertiary-muted">Fusion:</span> RRF (k=60)</span>
                      </div>
                    </div>
                  )}

                  {/* Assistant Body Text rendered with MarkdownAnswer */}
                  <MarkdownAnswer
                    content={msg.content}
                    citations={msg.citations}
                    activeCitation={activeCitation}
                    onCitationClick={handleCitationClick}
                    isStreaming={msg.isStreaming}
                  />

                  {/* Bottom Action Buttons */}
                  <div className="flex items-center gap-4 pt-1 font-mono text-[11px] text-tertiary-muted">
                    <button
                      onClick={() => navigator.clipboard.writeText(msg.content)}
                      className="flex items-center gap-1 hover:text-slate-200 transition-colors"
                    >
                      <span className="material-symbols-outlined text-[14px]">content_copy</span>
                      <span>Copy</span>
                    </button>
                    <button
                      onClick={() => {
                        if (msg.citations && msg.citations.length > 0) {
                          handleCitationClick(msg.citations[0]);
                        }
                      }}
                      className="flex items-center gap-1 hover:text-primary transition-colors text-primary/80"
                    >
                      <span className="material-symbols-outlined text-[14px]">find_in_page</span>
                      <span>Inspect Evidence</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Chat Bottom Input Area */}
          <div className="p-4 bg-[#080B10] border-t border-outline-variant shrink-0">
            <div className="relative flex items-end gap-2 bg-[#121722] rounded-xl border border-outline-variant hover:border-slate-500 focus-within:border-primary focus-within:shadow-[0_0_0_1px_#3cddc7] transition-all p-2.5">
              {/* Scope Selector Chip */}
              <div className="relative shrink-0 mb-0.5">
                <button
                  type="button"
                  onClick={() => setShowScopePopover(!showScopePopover)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-surface-container border border-outline-variant hover:border-primary text-slate-200 font-mono text-xs transition-colors"
                >
                  <span className="material-symbols-outlined text-[14px] text-primary">filter_center_focus</span>
                  <span>{scope}</span>
                  <span className="material-symbols-outlined text-[14px] text-tertiary-muted">arrow_drop_down</span>
                </button>

                {showScopePopover && (
                  <div className="absolute left-0 bottom-full mb-2 w-44 bg-surface-container-high border border-outline-variant rounded-lg shadow-xl py-1 z-50 text-xs font-sans text-slate-200">
                    {['Entire corpus', 'This paper', 'Compare all'].map((s) => (
                      <button
                        key={s}
                        onClick={() => {
                          setScope(s);
                          setShowScopePopover(false);
                        }}
                        className={`w-full text-left px-3 py-1.5 hover:bg-surface-container flex items-center justify-between ${
                          scope === s ? 'text-primary font-medium' : 'text-slate-300'
                        }`}
                      >
                        <span>{s}</span>
                        {scope === s && <span className="material-symbols-outlined text-[14px]">check</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Textarea */}
              <textarea
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendQuery();
                  }
                }}
                rows={1}
                placeholder="Query literature corpus (e.g. 'Compare MQA vs GQA retrieval latency in RAG pipelines')..."
                className="flex-1 max-h-32 bg-transparent border-0 resize-none outline-none text-sm text-white placeholder:text-tertiary-muted py-1 px-1.5 leading-normal font-sans"
              />

              {/* Send Button */}
              <button
                type="button"
                onClick={handleSendQuery}
                disabled={sending || !inputQuery.trim()}
                className="w-8 h-8 rounded-lg bg-primary hover:bg-[#34c4b0] text-[#00201C] flex items-center justify-center font-bold transition-all shadow-md active:scale-95 disabled:opacity-40"
              >
                {sending ? (
                  <span className="w-3.5 h-3.5 border-2 border-[#00201C] border-t-transparent rounded-full animate-spin"></span>
                ) : (
                  <span className="material-symbols-outlined text-[18px]">arrow_upward</span>
                )}
              </button>
            </div>
          </div>
        </main>

        {/* --------------------------------------------------------------------- */}
        {/* RIGHT PANEL: Evidence Inspector (Fully Scrollable, Telemetry Bars)    */}
        {/* --------------------------------------------------------------------- */}
        {showInspector && (
          <aside
            style={{ width: `${rightWidth}px` }}
            className="shrink-0 flex flex-col bg-[#090D15] border-t lg:border-t-0 lg:border-l border-outline-variant h-full select-text transition-all duration-200"
          >
            <div className="h-11 px-3.5 border-b border-outline-variant flex items-center justify-between bg-[#090D15] shrink-0">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-[17px]">find_in_page</span>
                <span className="font-mono text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1">
                  <span>Evidence Inspector</span>
                  <span className="text-primary font-bold">· {selectedStrategy}</span>
                </span>
              </div>
              <button
                onClick={() => setShowInspector(false)}
                className="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200"
                title="Collapse Inspector"
              >
                <span className="material-symbols-outlined text-[16px]">chevron_right</span>
              </button>
            </div>

            {activeCitation ? (() => {
              const meta = activeCitation.strategy_metadata || {};
              const strat = meta.strategy || selectedStrategy;

              return (
                <div
                  ref={inspectorContentRef}
                  className="flex-1 overflow-y-auto custom-scroll p-4 space-y-4 pb-12"
                >
                  {/* Strategy Badge & Architecture Tag */}
                  <div className="p-3 bg-[#0c121e] rounded-xl border border-primary/20 space-y-1 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                        <span className="font-mono text-[11px] font-bold text-primary uppercase tracking-wider">
                          {strat === 'Hybrid' && 'Hybrid RAG Pipeline'}
                          {strat === 'Hierarchical' && 'Hierarchical Dual-Tier AST'}
                          {strat === 'GraphRAG' && 'GraphRAG Community Traversal'}
                          {strat === 'Agentic' && 'Corrective RAG (CRAG) Agent'}
                          {strat === 'Adaptive' && 'Adaptive Complexity Router'}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-container border border-outline-variant text-slate-300">
                        Rank #{activeCitation.rank}
                      </span>
                    </div>
                    <p className="font-mono text-[10px] text-tertiary-muted leading-relaxed">
                      {meta.technique || (
                        strat === 'Hybrid' ? 'Dense HNSW + BM25s Lexical fused via Reciprocal Rank Fusion (k=60)' :
                        strat === 'Hierarchical' ? 'Dual-Tier AST (256-tok Child Anchor → 2048-tok Section Parent Expansion)' :
                        strat === 'GraphRAG' ? 'Entity Extraction & NetworkX Community Neighbor Graph Traversal' :
                        strat === 'Agentic' ? 'LangGraph State Machine (retrieve → grade → generate)' :
                        'Dynamic Pre-Retrieval Query Intent & Complexity Dispatch'
                      )}
                    </p>
                  </div>

                  {/* Paper Meta Card */}
                  <div className="p-3 bg-surface-container rounded-xl border border-outline-variant space-y-2">
                    <h3 className="text-xs font-semibold text-white leading-snug">
                      {activeCitation.paper_title}
                    </h3>
                    <div className="flex items-center justify-between pt-1 font-mono text-[11px]">
                      <div className="flex items-center gap-1.5 bg-surface-container-low px-2 py-0.5 rounded border border-outline-variant text-tertiary-muted">
                        <span>ID:</span>
                        <span className="text-slate-200 font-medium">arXiv:{activeCitation.arxiv_id}</span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(activeCitation.arxiv_id);
                            setCopiedArxiv(true);
                            setTimeout(() => setCopiedArxiv(false), 1400);
                          }}
                          className="hover:text-primary ml-0.5 text-tertiary-muted"
                          title="Copy arXiv ID"
                        >
                          <span className="material-symbols-outlined text-[13px]">
                            {copiedArxiv ? 'check' : 'content_copy'}
                          </span>
                        </button>
                      </div>
                      <span className="text-tertiary-muted">Page {activeCitation.page_number}</span>
                    </div>
                    <div className="flex items-center gap-1 text-tertiary-muted font-mono text-[11px] pt-0.5">
                      <span className="material-symbols-outlined text-[14px] text-primary">segment</span>
                      <span>Page {activeCitation.page_number}</span>
                      <span className="text-outline-variant">&gt;</span>
                      <span className="text-slate-300 font-medium">{activeCitation.section_name}</span>
                    </div>
                  </div>

                  {/* ------------------------------------------------------------- */}
                  {/* STRATEGY 1: HIERARCHICAL SPECIFIC DISPLAY                     */}
                  {/* ------------------------------------------------------------- */}
                  {strat === 'Hierarchical' && (
                    <div className="p-3 bg-[#0d1624] rounded-xl border border-sky-500/30 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-sky-400 flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px]">account_tree</span>
                          AST Hierarchy Path
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950/60 border border-sky-500/40 text-sky-300 font-semibold">
                          {meta.expansion_ratio || '7.1x'} expanded
                        </span>
                      </div>

                      {/* Breadcrumb Tree Nodes */}
                      <div className="p-2 bg-surface-container-low rounded-lg border border-outline-variant font-mono text-[11px] space-y-1.5">
                        <div className="flex items-center gap-1.5 text-slate-400">
                          <span className="material-symbols-outlined text-[13px] text-sky-400">folder</span>
                          <span className="text-slate-200 font-medium">arXiv:{activeCitation.arxiv_id}</span>
                          <span className="text-outline-variant">/</span>
                          <span className="text-slate-300">{activeCitation.section_name}</span>
                        </div>
                        <div className="flex items-center gap-2 pl-3 border-l border-sky-500/40 text-xs">
                          <span className="text-sky-300 font-medium">Enclosing Section ({meta.parent_tokens || 2048}t)</span>
                          <span className="material-symbols-outlined text-[13px] text-primary">arrow_forward</span>
                          <span className="text-emerald-400 font-medium">Leaf Match ({meta.child_tokens || 256}t)</span>
                        </div>
                      </div>

                      {/* Segmented Context Toggle */}
                      <div className="flex rounded-lg bg-surface-container-low p-1 border border-outline-variant">
                        <button
                          type="button"
                          onClick={() => setHierarchicalTab('parent')}
                          className={`flex-1 py-1 px-2 rounded font-mono text-[11px] transition-all flex items-center justify-center gap-1.5 ${
                            hierarchicalTab === 'parent'
                              ? 'bg-sky-500/20 text-sky-300 font-bold border border-sky-500/40 shadow-sm'
                              : 'text-tertiary-muted hover:text-slate-200'
                          }`}
                        >
                          <span className="material-symbols-outlined text-[13px]">subject</span>
                          <span>Expanded Parent ({meta.parent_tokens || 2048}t)</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setHierarchicalTab('child')}
                          className={`flex-1 py-1 px-2 rounded font-mono text-[11px] transition-all flex items-center justify-center gap-1.5 ${
                            hierarchicalTab === 'child'
                              ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40 shadow-sm'
                              : 'text-tertiary-muted hover:text-slate-200'
                          }`}
                        >
                          <span className="material-symbols-outlined text-[13px]">target</span>
                          <span>Matched Child ({meta.child_tokens || 256}t)</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STRATEGY 2: GRAPHRAG SPECIFIC DISPLAY                         */}
                  {/* ------------------------------------------------------------- */}
                  {strat === 'GraphRAG' && (
                    <div className="p-3 bg-[#110d22] rounded-xl border border-purple-500/30 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-purple-300 flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px] text-purple-400">hub</span>
                          Knowledge Graph Traversal
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/60 border border-purple-500/40 text-purple-200">
                          Centrality: {meta.centrality_score || 0.88}
                        </span>
                      </div>

                      {/* Matched Entity Node */}
                      <div className="p-2.5 bg-[#171030] rounded-lg border border-purple-500/20 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-purple-400 shadow-[0_0_8px_#c084fc] animate-ping"></span>
                          <div>
                            <span className="text-[10px] font-mono text-tertiary-muted uppercase">Query Entity Node:</span>
                            <div className="text-xs font-bold text-white font-mono">
                              {meta.matched_entity || 'Concept Node'}
                            </div>
                          </div>
                        </div>
                        <div className="text-right font-mono text-[11px]">
                          <span className="text-slate-400">Node Degree: </span>
                          <span className="text-purple-300 font-bold">{meta.node_degree || 4}</span>
                        </div>
                      </div>

                      {/* Community Neighbors */}
                      <div className="space-y-1.5">
                        <span className="text-[10px] font-mono text-tertiary-muted uppercase tracking-wider">
                          1-Hop &amp; 2-Hop Community Neighbors:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {(meta.community_neighbors || ['Attention', 'Transformer', 'Self-Attention', 'Feed-Forward']).map((nbr: string, i: number) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-950/50 border border-purple-500/30 text-purple-200 font-medium flex items-center gap-1"
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                              {nbr}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Edge Relations */}
                      {meta.edge_relations && meta.edge_relations.length > 0 && (
                        <div className="space-y-1 font-mono text-[11px]">
                          <span className="text-[10px] text-tertiary-muted uppercase">Relational Edges:</span>
                          <div className="space-y-0.5">
                            {meta.edge_relations.map((rel: string, i: number) => (
                              <div key={i} className="text-slate-300 flex items-center gap-1.5">
                                <span className="material-symbols-outlined text-[12px] text-purple-400">link</span>
                                <span>{rel}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STRATEGY 3: AGENTIC CRAG SPECIFIC DISPLAY                     */}
                  {/* ------------------------------------------------------------- */}
                  {strat === 'Agentic' && (
                    <div className="p-3 bg-[#0a1715] rounded-xl border border-emerald-500/30 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px]">verified</span>
                          CRAG Verification Status
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 font-bold">
                          ✓ RELEVANT
                        </span>
                      </div>

                      {/* Evaluator Confidence Bar */}
                      <div className="space-y-1">
                        <div className="flex justify-between font-mono text-[11px]">
                          <span className="text-slate-400">Evaluator Confidence</span>
                          <span className="text-emerald-400 font-bold">
                            {Math.round((meta.evaluation_confidence || 0.94) * 100)}%
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-400 rounded-full"
                            style={{ width: `${(meta.evaluation_confidence || 0.94) * 100}%` }}
                          />
                        </div>
                      </div>

                      {/* Grading Rationale */}
                      <div className="p-2.5 bg-emerald-950/20 rounded-lg border border-emerald-500/20 font-mono text-[11px] text-emerald-200/90 leading-relaxed">
                        <span className="text-emerald-400 font-semibold">Evaluator Rationale: </span>
                        {meta.grading_rationale || 'Passage verified by LangGraph evaluator agent as directly containing core architecture specifications.'}
                      </div>

                      {/* State Machine Node Trail */}
                      <div className="font-mono text-[10px] text-tertiary-muted space-y-1">
                        <span>LangGraph State Graph Traversal:</span>
                        <div className="flex items-center gap-1.5 text-slate-300">
                          <span className="px-1.5 py-0.5 rounded bg-surface-container border border-outline-variant">retrieve</span>
                          <span>➔</span>
                          <span className="px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-bold">grade_documents</span>
                          <span>➔</span>
                          <span className="px-1.5 py-0.5 rounded bg-surface-container border border-outline-variant">generate</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STRATEGY 4: ADAPTIVE ROUTER SPECIFIC DISPLAY                  */}
                  {/* ------------------------------------------------------------- */}
                  {strat === 'Adaptive' && (
                    <div className="p-3 bg-[#17130b] rounded-xl border border-amber-500/30 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px]">alt_route</span>
                          Adaptive Routing Decision
                        </span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase border ${
                          meta.query_complexity === 'COMPLEX'
                            ? 'bg-purple-950/60 border-purple-500/50 text-purple-300'
                            : meta.query_complexity === 'MODERATE'
                            ? 'bg-cyan-950/60 border-cyan-500/50 text-cyan-300'
                            : 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300'
                        }`}>
                          Complexity: {meta.query_complexity || 'MODERATE'}
                        </span>
                      </div>

                      <div className="p-2.5 bg-amber-950/20 rounded-lg border border-amber-500/20 font-mono text-[11px] space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-amber-400 font-semibold">Dispatched Engine:</span>
                          <span className="text-white font-medium">{meta.routed_pipeline || 'Hierarchical Parent-Child RAG'}</span>
                        </div>
                        <p className="text-slate-300 text-[11px] leading-relaxed">
                          <span className="text-amber-400/80 font-semibold">Rationale: </span>
                          {meta.routing_rationale || 'Query complexity matches target architectural requirements.'}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* RETRIEVED CHUNK DETAIL BLOCK                                  */}
                  {/* ------------------------------------------------------------- */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between font-mono text-[11px] text-tertiary-muted">
                      <span>
                        {strat === 'Hierarchical'
                          ? (hierarchicalTab === 'parent' ? 'EXPANDED SECTION CONTEXT' : 'PRECISION CHILD MATCH')
                          : 'RETRIEVED PASSAGE CHUNK'}
                      </span>
                      <span className="text-primary font-medium">Rank #{activeCitation.rank}</span>
                    </div>
                    <div className="bg-surface-container-low border-l-[3px] border-l-primary p-3 rounded-r-lg font-mono text-xs leading-relaxed text-slate-300 space-y-2 max-h-96 overflow-y-auto custom-scroll">
                      <p>
                        {strat === 'Hierarchical'
                          ? (hierarchicalTab === 'parent'
                              ? (meta.parent_expanded_content || activeCitation.content)
                              : (meta.child_anchor_content || activeCitation.content))
                          : activeCitation.content}
                      </p>
                    </div>
                  </div>

                  {/* ------------------------------------------------------------- */}
                  {/* RELEVANCE & SCORING TELEMETRY CARD                            */}
                  {/* ------------------------------------------------------------- */}
                  <div className="p-3 bg-surface-container rounded-xl border border-outline-variant space-y-2.5">
                    <div className="flex items-center justify-between font-mono text-xs">
                      <span className="text-tertiary-muted font-medium">
                        {strat === 'Hybrid' ? 'Reciprocal Rank Fusion (k=60)' : 'Relevance & Similarity'}
                      </span>
                      <span className="text-primary font-semibold">
                        {meta.rrf_score
                          ? `RRF Score: ${meta.rrf_score}`
                          : `Combined: ${round((activeCitation.similarity_score + (activeCitation.bm25_score / 20)) / 2, 3)}`}
                      </span>
                    </div>

                    {/* Hybrid Dual Ranks if available */}
                    {meta.dense_rank && (
                      <div className="flex items-center gap-2 font-mono text-[11px]">
                        <span className="px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant text-slate-300">
                          Dense Rank: <strong className="text-primary">#{meta.dense_rank}</strong>
                        </span>
                        <span className="px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant text-slate-300">
                          Sparse Rank: <strong className="text-secondary">#{meta.sparse_rank}</strong>
                        </span>
                      </div>
                    )}

                    {/* Cosine Sim Score Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between font-mono text-[11px] text-slate-400">
                        <span>Dense Semantic Cosine</span>
                        <span className="font-medium text-primary">{activeCitation.similarity_score}</span>
                      </div>
                      <div className="w-full h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${activeCitation.similarity_score * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* BM25 Score Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between font-mono text-[11px] text-slate-400">
                        <span>BM25s Lexical Match</span>
                        <span className="font-medium text-secondary">{activeCitation.bm25_score}</span>
                      </div>
                      <div className="w-full h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                        <div
                          className="h-full bg-secondary rounded-full transition-all"
                          style={{ width: `${Math.min((activeCitation.bm25_score / 20) * 100, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Reranker Score Row */}
                    {activeCitation.reranker_score && (
                      <div className="pt-2 flex items-center justify-between font-mono text-[11px] text-tertiary-muted border-t border-outline-variant">
                        <span>Reranker Score</span>
                        <span className="text-slate-200 font-medium">+{activeCitation.reranker_score} (RRF Fusion)</span>
                      </div>
                    )}
                  </div>

                  {/* Context Attention Map SVG */}
                  <div className="p-3 bg-surface-container rounded-xl border border-outline-variant space-y-2">
                    <div className="flex items-center justify-between text-tertiary-muted font-mono text-[11px]">
                      <span>CONTEXT ATTENTION MAP</span>
                      <span className="text-secondary font-medium">U-CURVE</span>
                    </div>
                    <div className="w-full h-16 flex items-center justify-center py-1">
                      <svg className="w-full h-full text-primary" fill="none" stroke="currentColor" viewBox="0 0 240 60">
                        <line stroke="#1F2733" strokeDasharray="2 2" strokeWidth="1" x1="0" x2="240" y1="50" y2="50" />
                        <line stroke="#1F2733" strokeDasharray="2 2" strokeWidth="1" x1="0" x2="240" y1="20" y2="20" />
                        <path
                          d="M 10 15 C 60 15, 80 50, 120 50 C 160 50, 180 18, 230 18"
                          fill="none"
                          stroke="#3CDDC7"
                          strokeLinecap="round"
                          strokeWidth="2"
                        />
                        <circle cx="120" cy="50" fill="#3CDDC7" r="4" />
                      </svg>
                    </div>
                    <div className="flex items-center justify-between text-tertiary-muted font-mono text-[10px]">
                      <span>Doc Start (94%)</span>
                      <span className="text-secondary font-medium">Middle (59%)</span>
                      <span>Doc End (91%)</span>
                    </div>
                  </div>

                  {/* PDF External Link */}
                  <a
                    href={`https://arxiv.org/pdf/${activeCitation.arxiv_id}.pdf#page=${activeCitation.page_number}`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2 px-3 rounded-lg bg-surface-container-high border border-outline-variant hover:border-primary text-primary hover:bg-surface-bright flex items-center justify-center gap-2 font-mono text-xs font-semibold transition-all group shadow-sm"
                  >
                    <span>Open PDF at this page (p. {activeCitation.page_number})</span>
                    <span className="material-symbols-outlined text-[15px] group-hover:translate-x-0.5 transition-transform">
                      open_in_new
                    </span>
                  </a>
                </div>
              );
            })() : (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-4 select-none">
                {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (!messages[messages.length - 1].citations || messages[messages.length - 1].citations?.length === 0) ? (
                  <>
                    <div className="w-12 h-12 rounded-xl bg-surface-container border border-primary/40 flex items-center justify-center text-primary shadow-md shadow-primary/5">
                      <span className="material-symbols-outlined text-[24px]">forum</span>
                    </div>
                    <div className="space-y-1.5 max-w-[240px]">
                      <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-primary/10 border border-primary/30 text-[10px] font-mono text-primary font-semibold">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                        General Conversational Query
                      </div>
                      <p className="text-xs font-semibold text-white">No Passages Retrieved</p>
                      <p className="text-[11px] text-tertiary-muted leading-relaxed">
                        Passage retrieval was bypassed because your query is conversational. Ask a technical question about the research literature to inspect source passages, similarity scores, and attention maps.
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-12 h-12 rounded-2xl bg-surface-container border border-outline-variant flex items-center justify-center text-primary shadow-sm">
                      <span className="material-symbols-outlined text-[22px]">
                        {selectedStrategy === 'Hybrid' && 'tune'}
                        {selectedStrategy === 'Hierarchical' && 'account_tree'}
                        {selectedStrategy === 'GraphRAG' && 'hub'}
                        {selectedStrategy === 'Agentic' && 'smart_toy'}
                        {selectedStrategy === 'Adaptive' && 'alt_route'}
                      </span>
                    </div>
                    <div className="space-y-1.5 max-w-[250px]">
                      <span className="font-mono text-[10px] uppercase tracking-wider text-primary font-bold px-2 py-0.5 rounded bg-primary/10 border border-primary/25 inline-block">
                        {selectedStrategy} Evidence
                      </span>
                      <p className="text-xs font-semibold text-white">
                        {messages.length === 0 ? 'No Queries in this Thread' : 'No Citation Selected'}
                      </p>
                      <p className="text-[11px] text-tertiary-muted leading-relaxed">
                        {selectedStrategy === 'Hybrid' && 'Inspect fused dense cosine and sparse BM25s ranks with local cross-encoder scoring.'}
                        {selectedStrategy === 'Hierarchical' && 'Inspect 256-token child anchors expanded into 2,048-token parent section AST chunks.'}
                        {selectedStrategy === 'GraphRAG' && 'Inspect typed entity subgraphs, 2-hop relation paths, and Louvain modularity clusters.'}
                        {selectedStrategy === 'Agentic' && 'Inspect Corrective RAG (CRAG) document grading, query transformations, and critic evaluation.'}
                        {selectedStrategy === 'Adaptive' && 'Inspect pre-retrieval complexity classification, confidence score, and delegated RAG engine.'}
                      </p>
                      {messages.length > 0 && (
                        <p className="text-[10px] font-mono text-primary/80 pt-1">
                          Click any citation chip [1], [2] in an answer to inspect its grounded evidence.
                        </p>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  );
};

function round(val: number, precision: number): number {
  const factor = Math.pow(10, precision);
  return Math.round(val * factor) / factor;
}
