import React, { useState, useEffect } from 'react';
import { ArXivPaper } from '../../types';
import { api } from '../../services/api';

interface DiscoverViewProps {
  onCorpusCreated: (name: string, query: string, paperIds: string[]) => void;
}

const SUGGESTED_QUERIES = [
  { label: 'Attention Is All You Need', query: 'Attention Is All You Need' },
  { label: 'Retrieval-Augmented Generation', query: 'Retrieval Augmented Generation survey' },
  { label: 'Quantum Computing Supremacy', query: 'quantum computing supremacy' },
  { label: 'CRISPR Cas9 Genome Editing', query: 'CRISPR Cas9 gene editing' },
  { label: 'Deep Residual Learning (ResNet)', query: 'Deep Residual Learning for Image Recognition' },
  { label: 'Black Hole Thermodynamics', query: 'black hole information paradox' }
];

const DEFAULT_TRENDING_PAPERS: ArXivPaper[] = [
  {
    arxiv_id: "2501.12948",
    title: "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
    authors: ["DeepSeek-AI", "Daya Guo", "Dejian Yang", "Haowei Zhang", "Songqiang Chen"],
    abstract: "We introduce our first-generation reasoning models, DeepSeek-R1-Zero and DeepSeek-R1. DeepSeek-R1-Zero, a model trained via large-scale reinforcement learning (RL) without supervised fine-tuning (SFT) as a preliminary step, demonstrates remarkable reasoning capabilities.",
    categories: ["cs.AI", "cs.CL", "cs.LG"],
    published_date: "2025-01-22",
    pdf_url: "https://arxiv.org/pdf/2501.12948.pdf"
  },
  {
    arxiv_id: "2401.15884",
    title: "Corrective Retrieval Augmented Generation (CRAG)",
    authors: ["Shi-Qi Yan", "Jia-Chen Gu", "Yun-Xuan Zhu", "Zhen-Hua Ling"],
    abstract: "Large language models inevitably exhibit hallucinations. We propose the Corrective Retrieval-Augmented Generation (CRAG) to self-evaluate retrieved documents and refine generation with adaptive query rewrites.",
    categories: ["cs.CL", "cs.AI"],
    published_date: "2024-01-29",
    pdf_url: "https://arxiv.org/pdf/2401.15884.pdf"
  },
  {
    arxiv_id: "2404.16130",
    title: "From Local to Global: A Graph RAG Approach to Query-Focused Summarization",
    authors: ["Darren Edge", "Ha Trinh", "Newman Cheng", "Joshua Bradley", "Alex Chao"],
    abstract: "RAG fails when queries require global sensemaking over an entire dataset. We propose Graph RAG, combining LLM-extracted knowledge graphs with hierarchical community summarization.",
    categories: ["cs.CL", "cs.AI", "cs.IR"],
    published_date: "2024-04-24",
    pdf_url: "https://arxiv.org/pdf/2404.16130.pdf"
  },
  {
    arxiv_id: "2307.03172",
    title: "Lost in the Middle: How Language Models Use Long Contexts",
    authors: ["Nelson F. Liu", "Kevin Lin", "John Hewitt", "Ashwin Paranjape", "Percy Liang"],
    abstract: "While modern language models are capable of taking long contexts as input, relatively little is known about how well they use input context. Performance degrades significantly when relevant information is in the middle.",
    categories: ["cs.CL", "cs.AI"],
    published_date: "2023-07-06",
    pdf_url: "https://arxiv.org/pdf/2307.03172.pdf"
  },
  {
    arxiv_id: "2407.21783",
    title: "The Llama 3 Herd of Models",
    authors: ["Llama Team", "Meta AI"],
    abstract: "Modern AI requires foundation models capable of reasoning, instruction following, and multilingual understanding. We introduce Llama 3, natively supporting coding, reasoning, and tool usage.",
    categories: ["cs.AI", "cs.CL"],
    published_date: "2024-07-31",
    pdf_url: "https://arxiv.org/pdf/2407.21783.pdf"
  },
  {
    arxiv_id: "2402.01030",
    title: "A Survey on Large Language Model based Autonomous Agents",
    authors: ["Lei Wang", "Chen Ma", "Xueyang Feng", "Zeyu Zhang", "Hao Yang"],
    abstract: "Autonomous agents have long been a prominent research focus. Recent advances in LLMs spur great optimism. We present a comprehensive survey covering agent architecture, profiling, memory, and planning.",
    categories: ["cs.AI", "cs.MA"],
    published_date: "2024-02-01",
    pdf_url: "https://arxiv.org/pdf/2402.01030.pdf"
  },
  {
    arxiv_id: "2304.03442",
    title: "Generative Agents: Interactive Simulacra of Human Behavior",
    authors: ["Joon Sung Park", "Joseph C. O'Brien", "Carrie J. Cai", "Percy Liang", "Michael S. Bernstein"],
    abstract: "Believable proxies of human behavior empower interactive applications. We present generative agents that simulate believable human behavior through observation, reflection, and planning architectures.",
    categories: ["cs.AI", "cs.HC"],
    published_date: "2023-04-07",
    pdf_url: "https://arxiv.org/pdf/2304.03442.pdf"
  },
  {
    arxiv_id: "1706.03762",
    title: "Attention Is All You Need",
    authors: ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Lukasz Kaiser"],
    abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose the Transformer, relying entirely on an attention mechanism.",
    categories: ["cs.CL", "cs.LG"],
    published_date: "2017-06-12",
    pdf_url: "https://arxiv.org/pdf/1706.03762.pdf"
  }
];

const TRENDING_CATEGORIES = [
  { id: 'all', label: 'All' },
  { id: 'reasoning', label: 'Reasoning' },
  { id: 'rag', label: 'RAG & Retrieval' },
  { id: 'agents', label: 'Agentic AI' },
  { id: 'foundations', label: 'Foundations' }
];

export const DiscoverView: React.FC<DiscoverViewProps> = ({ onCorpusCreated }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [papers, setPapers] = useState<ArXivPaper[]>([]);
  const [trendingPapers, setTrendingPapers] = useState<ArXivPaper[]>(DEFAULT_TRENDING_PAPERS);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const [trendingFilter, setTrendingFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [corpusName, setCorpusName] = useState('');

  // Fetch trending papers from API on mount
  useEffect(() => {
    let mounted = true;
    api.getTrendingPapers(10).then((liveTrending) => {
      if (mounted && liveTrending && liveTrending.length > 0) {
        setTrendingPapers(liveTrending);
      }
    }).catch(() => {
      // Keep defaults
    });
    return () => { mounted = false; };
  }, []);

  const doSearch = async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;

    // Instant local match so the user sees results in 0 milliseconds
    const qLower = trimmed.toLowerCase();
    const localMatches = trendingPapers.filter(
      (p) =>
        p.title.toLowerCase().includes(qLower) ||
        p.arxiv_id.toLowerCase().includes(qLower) ||
        (p.abstract && p.abstract.toLowerCase().includes(qLower)) ||
        (qLower.includes('attention') && p.arxiv_id === '1706.03762') ||
        (qLower.includes('deepseek') && p.arxiv_id === '2501.12948') ||
        (qLower.includes('crag') && p.arxiv_id === '2401.15884') ||
        (qLower.includes('graph') && p.arxiv_id === '2404.16130') ||
        (qLower.includes('middle') && p.arxiv_id === '2307.03172')
    );

    if (localMatches.length > 0) {
      setPapers(localMatches);
      setHasSearched(true);
    }

    setLoading(true);
    setHasSearched(true);
    try {
      const results = await api.searchArXiv(trimmed, 20);
      if (results && results.length > 0) {
        setPapers(results);
      } else if (localMatches.length > 0) {
        setPapers(localMatches);
      } else {
        setPapers([]);
      }
      setActiveCategory('all');
    } catch (e) {
      console.error(e);
      if (localMatches.length > 0) {
        setPapers(localMatches);
      } else {
        setPapers([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (q: string) => {
    setSearchQuery(q);
    doSearch(q);
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const selectAll = () => {
    if (selectedIds.size === filteredPapers.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredPapers.map(p => p.arxiv_id)));
    }
  };

  const handleToggleAllTrending = () => {
    const trendingFilteredIds = filteredTrending.map(p => p.arxiv_id);
    const allSelected = trendingFilteredIds.every(id => selectedIds.has(id));
    const next = new Set(selectedIds);

    if (allSelected) {
      trendingFilteredIds.forEach(id => next.delete(id));
    } else {
      trendingFilteredIds.forEach(id => next.add(id));
    }
    setSelectedIds(next);
  };

  const handleOpenCreateModal = () => {
    let defaultName = 'Research Literature Corpus';
    if (searchQuery) {
      defaultName = `${searchQuery.charAt(0).toUpperCase() + searchQuery.slice(1)} Corpus`;
    } else if (selectedIds.size > 0) {
      defaultName = 'Frontier Research Literature Corpus';
    }
    setCorpusName(defaultName);
    setShowCreateModal(true);
  };

  const handleCreate = () => {
    if (selectedIds.size === 0) return;
    onCorpusCreated(corpusName || 'New Research Corpus', searchQuery || 'Frontier Research', Array.from(selectedIds));
    setShowCreateModal(false);
  };

  // Derive unique categories dynamically from current search results
  const availableCategories = Array.from(
    new Set(papers.flatMap(p => p.categories || []))
  ).slice(0, 8);

  const filteredPapers = papers.filter(p => {
    if (activeCategory === 'all') return true;
    return p.categories && p.categories.includes(activeCategory);
  });

  // Filter trending papers
  const filteredTrending = trendingPapers.filter(p => {
    if (trendingFilter === 'all') return true;
    const text = (p.title + ' ' + (p.abstract || '') + ' ' + (p.categories || []).join(' ')).toLowerCase();
    if (trendingFilter === 'reasoning') {
      return text.includes('deepseek') || text.includes('reasoning') || text.includes('llama');
    }
    if (trendingFilter === 'rag') {
      return text.includes('rag') || text.includes('retrieval') || text.includes('middle') || text.includes('graph');
    }
    if (trendingFilter === 'agents') {
      return text.includes('agent') || text.includes('autonomous');
    }
    if (trendingFilter === 'foundations') {
      return text.includes('transformer') || text.includes('attention') || text.includes('1706.03762');
    }
    return true;
  });

  const allTrendingSelected = filteredTrending.length > 0 && filteredTrending.every(p => selectedIds.has(p.arxiv_id));

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0B0E14] overflow-hidden relative">
      {/* Top Search & Filter Bar */}
      <div className="p-4 md:p-5 border-b border-outline-variant bg-[#090D15] shrink-0 space-y-3">
        <div className="max-w-6xl mx-auto w-full space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-baseline gap-2.5">
              <h1 className="text-base md:text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">hub</span>
                SynthLab
              </h1>
              <span className="hidden sm:inline-block text-xs text-tertiary-muted font-medium tracking-wide border-l border-outline-variant pl-2.5">
                From Literature to Synthesis
              </span>
            </div>
            <div className="flex items-center gap-3">
              {hasSearched && (
                <span className="font-mono text-xs text-tertiary-muted">
                  {filteredPapers.length} results available
                </span>
              )}
              <span className="font-mono text-[11px] text-slate-400 bg-surface-container px-2 py-0.5 rounded border border-outline-variant">
                Model: <span className="text-primary font-semibold">gpt-5.6-luna</span>
              </span>
            </div>
          </div>

          <div className="relative flex items-center">
            <span className="material-symbols-outlined absolute left-3.5 text-tertiary-muted text-[18px] pointer-events-none">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && doSearch(searchQuery)}
              placeholder="Search across all scientific fields (e.g. Attention, Quantum, CRISPR, or arXiv ID: 2501.12948)..."
              className="w-full h-11 bg-surface-container-low border border-outline-variant rounded-xl pl-10 pr-28 text-sm text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-all shadow-inner"
            />
            {searchQuery && (
              <button
                onClick={() => { setSearchQuery(''); setPapers([]); setHasSearched(false); }}
                className="absolute right-20 text-tertiary-muted hover:text-white text-xs px-1"
                title="Clear query"
              >
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            )}
            <button
              onClick={() => doSearch(searchQuery)}
              disabled={loading || !searchQuery.trim()}
              className="absolute right-1.5 h-8 px-4 rounded-lg bg-primary hover:bg-[#34c4b0] disabled:opacity-50 text-[#00201C] text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-[#00201C] border-t-transparent rounded-full animate-spin"></span>
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <span>Search</span>
                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </>
              )}
            </button>
          </div>

          {/* Filter Chips - Show dynamically if papers exist */}
          {papers.length > 0 && availableCategories.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[11px] font-mono text-tertiary-muted mr-1">Discipline:</span>
              <button
                onClick={() => setActiveCategory('all')}
                className={`px-2.5 py-1 rounded-md text-xs font-mono transition-colors ${
                  activeCategory === 'all'
                    ? 'bg-primary/15 text-primary border border-primary/40 font-medium'
                    : 'bg-surface-container border border-outline-variant text-slate-400 hover:text-slate-200'
                }`}
              >
                All ({papers.length})
              </button>
              {availableCategories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-2.5 py-1 rounded-md text-xs font-mono transition-colors ${
                    activeCategory === cat
                      ? 'bg-primary/15 text-primary border border-primary/40 font-medium'
                      : 'bg-surface-container border border-outline-variant text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Dual-Pane Area: Search Content (Left) + Trending Papers (Right) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane: Search Results & Exploration */}
        <div className="flex-1 overflow-y-auto custom-scroll p-6 space-y-4 pb-28">
          {/* Loading Spinner */}
          {loading && papers.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              <p className="font-mono text-xs text-slate-400">Querying live arXiv & scientific repositories...</p>
            </div>
          )}

          {loading && papers.length > 0 && (
            <div className="flex items-center gap-2.5 p-2.5 px-3.5 rounded-xl bg-primary/10 border border-primary/25 text-xs font-mono text-primary animate-pulse">
              <span className="w-2 h-2 rounded-full bg-primary animate-ping shrink-0"></span>
              <span>Showing instant matches · Querying live arXiv repositories for more papers...</span>
            </div>
          )}

          {/* Clean Initial State (Before search) */}
          {!loading && !hasSearched && papers.length === 0 && (
            <div className="py-8 flex flex-col items-center text-center space-y-6 max-w-xl mx-auto">
              <div className="w-14 h-14 rounded-2xl bg-surface-container border border-outline-variant flex items-center justify-center text-primary shadow-lg shadow-primary/5">
                <span className="material-symbols-outlined text-[28px]">travel_explore</span>
              </div>
              <div className="space-y-2">
                <h2 className="text-base font-semibold text-white">Discover & Ingest Scientific Literature</h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Search open-access papers across all academic domains: Computer Science, Physics, Mathematics, Quantitative Biology, and Frontier AI.
                </p>
              </div>

              <div className="w-full space-y-2.5 pt-2">
                <div className="text-[11px] font-mono text-tertiary-muted uppercase tracking-wider">
                  Recommended Research Topics
                </div>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  {SUGGESTED_QUERIES.map((item) => (
                    <button
                      key={item.label}
                      onClick={() => handleSuggestionClick(item.query)}
                      className="px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/80 hover:border-primary text-xs text-slate-300 hover:text-white transition-all hover:bg-surface-container-high active:scale-95"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface-container/60 border border-outline-variant/60 text-left max-w-md w-full space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
                  <span className="material-symbols-outlined text-primary text-[16px]">info</span>
                  <span>Direct Ingestion Ready</span>
                </div>
                <p className="text-[11px] text-tertiary-muted leading-relaxed">
                  You can also select any of the high-impact papers from the <strong className="text-slate-300">Trending Papers</strong> panel on the right to build an instant research corpus without searching!
                </p>
              </div>
            </div>
          )}

          {/* No results state */}
          {!loading && hasSearched && papers.length === 0 && (
            <div className="py-16 text-center space-y-3">
              <div className="w-12 h-12 rounded-xl bg-surface-container border border-outline-variant mx-auto flex items-center justify-center text-tertiary-muted">
                <span className="material-symbols-outlined text-[24px]">search_off</span>
              </div>
              <h3 className="text-sm font-semibold text-white">No research papers found</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No papers matched "{searchQuery}". Try broader scientific keywords or search directly by arXiv ID (e.g. 2501.12948).
              </p>
            </div>
          )}

          {/* Results List */}
          {!loading && papers.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-1 px-1">
                <span className="text-xs text-slate-400">
                  Found <span className="text-white font-medium">{filteredPapers.length}</span> papers
                </span>
                <button
                  onClick={selectAll}
                  className="text-xs font-mono text-primary hover:underline"
                >
                  {selectedIds.size === filteredPapers.length ? 'Deselect All' : 'Select All Filtered'}
                </button>
              </div>

              {filteredPapers.map((paper) => {
                const isSelected = selectedIds.has(paper.arxiv_id);

                return (
                  <div
                    key={paper.arxiv_id}
                    onClick={() => toggleSelect(paper.arxiv_id)}
                    className={`group p-4 rounded-xl border transition-all cursor-pointer select-none ${
                      isSelected
                        ? 'bg-surface-container-high/90 border-primary/70 shadow-md shadow-primary/5'
                        : 'bg-surface-container hover:bg-surface-container-high border-outline-variant/70'
                    }`}
                  >
                    <div className="flex items-start gap-3.5">
                      {/* Custom Checkbox */}
                      <div className="pt-0.5 shrink-0">
                        <div
                          className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                            isSelected
                              ? 'bg-primary border-primary text-[#00201C]'
                              : 'border-outline group-hover:border-slate-400'
                          }`}
                        >
                          {isSelected && <span className="material-symbols-outlined text-[13px] font-bold">check</span>}
                        </div>
                      </div>

                      <div className="flex-1 min-w-0 space-y-1.5">
                        <div className="flex items-baseline justify-between gap-2">
                          <h3 className="text-sm font-semibold text-white group-hover:text-primary transition-colors leading-snug">
                            {paper.title}
                          </h3>
                          {paper.published_date && (
                            <span className="font-mono text-[11px] text-tertiary-muted shrink-0">
                              {paper.published_date}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <span className="truncate max-w-md">{paper.authors.join(', ')}</span>
                          <span className="text-tertiary-muted">·</span>
                          <span className="font-mono text-[11px] text-primary/80">arXiv:{paper.arxiv_id}</span>
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
                          {paper.abstract}
                        </p>

                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          {paper.categories.map((cat) => (
                            <span
                              key={cat}
                              className="px-1.5 py-0.5 rounded bg-surface-container-low border border-outline-variant/60 font-mono text-[10px] text-tertiary-muted"
                            >
                              {cat}
                            </span>
                          ))}
                          <a
                            href={paper.pdf_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="ml-auto inline-flex items-center gap-1 font-mono text-[11px] text-primary hover:underline"
                          >
                            <span>PDF</span>
                            <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Pane: Trending Papers Beside Screen */}
        <div className="w-80 md:w-96 xl:w-[420px] shrink-0 border-l border-outline-variant bg-[#090D15]/90 flex flex-col h-full overflow-hidden">
          {/* Trending Header */}
          <div className="p-4 border-b border-outline-variant/70 flex items-center justify-between shrink-0 bg-[#0c101a]">
            <div className="flex items-center gap-2.5">
              <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-base shadow-sm">
                🔥
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-white">Trending Papers</h2>
                  <span className="px-1.5 py-0.2 rounded bg-primary/20 text-primary border border-primary/30 font-mono text-[9px] font-bold">
                    LIVE
                  </span>
                </div>
                <p className="text-[11px] text-tertiary-muted">Frontier & high-impact research</p>
              </div>
            </div>

            <button
              onClick={handleToggleAllTrending}
              className="text-[11px] font-mono text-primary hover:underline hover:text-[#34c4b0] transition-colors"
            >
              {allTrendingSelected ? 'Deselect' : `+ All (${filteredTrending.length})`}
            </button>
          </div>

          {/* Topic Filter Tabs */}
          <div className="p-2 px-3 border-b border-outline-variant/40 bg-surface-container-low/40 flex items-center gap-1.5 overflow-x-auto custom-scroll shrink-0">
            {TRENDING_CATEGORIES.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setTrendingFilter(tab.id)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono whitespace-nowrap transition-colors ${
                  trendingFilter === tab.id
                    ? 'bg-primary/20 text-primary border border-primary/40 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Scrollable Trending Paper Cards */}
          <div className="flex-1 overflow-y-auto custom-scroll p-3 space-y-2.5 pb-28">
            {filteredTrending.map((paper) => {
              const isSelected = selectedIds.has(paper.arxiv_id);

              return (
                <div
                  key={paper.arxiv_id}
                  onClick={() => toggleSelect(paper.arxiv_id)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer select-none group ${
                    isSelected
                      ? 'bg-surface-container-high/90 border-primary/80 shadow-sm shadow-primary/10 ring-1 ring-primary/40'
                      : 'bg-surface-container hover:bg-surface-container-high border-outline-variant/70'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-mono text-[10px] text-primary/90 bg-primary/10 border border-primary/25 px-1.5 py-0.5 rounded">
                      arXiv:{paper.arxiv_id}
                    </span>
                    {paper.published_date && (
                      <span className="font-mono text-[10px] text-tertiary-muted">
                        {paper.published_date}
                      </span>
                    )}
                  </div>

                  <h3 className="text-xs font-semibold text-white group-hover:text-primary transition-colors leading-snug pt-1.5">
                    {paper.title}
                  </h3>

                  <p className="text-[11px] text-slate-400 truncate pt-0.5">
                    {paper.authors.slice(0, 3).join(', ')}{paper.authors.length > 3 ? ' et al.' : ''}
                  </p>

                  <p className="text-[11px] text-slate-300 leading-relaxed line-clamp-2 pt-1">
                    {paper.abstract}
                  </p>

                  <div className="flex items-center justify-between pt-2.5 mt-1 border-t border-outline-variant/40">
                    <div className="flex items-center gap-1">
                      {paper.categories.slice(0, 2).map((cat) => (
                        <span
                          key={cat}
                          className="px-1 py-0.2 rounded bg-surface-container-low font-mono text-[9px] text-tertiary-muted border border-outline-variant/50"
                        >
                          {cat}
                        </span>
                      ))}
                      <a
                        href={paper.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-0.5 text-[10px] font-mono text-slate-400 hover:text-primary ml-1"
                        title="View PDF on arXiv"
                      >
                        <span>PDF</span>
                        <span className="material-symbols-outlined text-[11px]">open_in_new</span>
                      </a>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSelect(paper.arxiv_id);
                      }}
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold flex items-center gap-1 transition-all ${
                        isSelected
                          ? 'bg-primary text-[#00201C] font-bold shadow-sm'
                          : 'bg-surface-container-high border border-outline-variant text-slate-300 hover:text-white hover:border-primary/60'
                      }`}
                    >
                      {isSelected ? (
                        <>
                          <span className="material-symbols-outlined text-[12px] font-bold">check</span>
                          <span>Added</span>
                        </>
                      ) : (
                        <>
                          <span>+ Add</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Floating Bottom Drawer when papers selected */}
      {selectedIds.size > 0 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-30">
          <div className="bg-[#121722] border border-primary/50 rounded-2xl p-3 px-4 shadow-2xl shadow-primary/10 flex items-center justify-between gap-4 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-primary text-[#00201C] flex items-center justify-center font-mono text-xs font-bold">
                {selectedIds.size}
              </span>
              <span className="text-xs font-semibold text-white">papers selected for RAGLab corpus</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelectedIds(new Set())}
                className="px-2.5 py-1 text-xs text-slate-400 hover:text-white transition-colors"
              >
                Clear
              </button>
              <button
                onClick={handleOpenCreateModal}
                className="px-4 py-1.5 rounded-lg bg-primary hover:bg-[#34c4b0] text-[#00201C] text-xs font-bold flex items-center gap-1 transition-all shadow-md active:scale-95"
              >
                <span>Create Corpus</span>
                <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Corpus Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-outline-variant rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">folder_special</span>
                Create Named Research Corpus
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-tertiary-muted hover:text-white"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <div className="space-y-1.5">
              <label className="font-mono text-xs text-tertiary-muted">Corpus Name</label>
              <input
                type="text"
                value={corpusName}
                onChange={(e) => setCorpusName(e.target.value)}
                placeholder="e.g. Frontier Reasoning & RAG Corpus"
                className="w-full h-9 bg-surface-container-low border border-outline-variant rounded-lg px-3 text-sm text-white focus:border-primary focus:outline-none"
              />
            </div>

            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/60 font-mono text-xs text-tertiary-muted space-y-1">
              <div className="flex justify-between">
                <span>Selected Papers:</span>
                <span className="text-slate-200 font-semibold">{selectedIds.size}</span>
              </div>
              <div className="flex justify-between">
                <span>LLM Generation Model:</span>
                <span className="text-primary font-medium">gpt-5.6-luna</span>
              </div>
              <div className="flex justify-between">
                <span>Ingestion Pipeline:</span>
                <span className="text-slate-300 font-medium">AST + HNSW + BM25s</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-1.5 rounded-lg bg-primary hover:bg-[#34c4b0] text-[#00201C] text-xs font-bold shadow-md active:scale-95"
              >
                Ingest & Launch Workspace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
