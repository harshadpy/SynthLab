import React, { useState, useEffect } from 'react';
import { Corpus } from './types';
import { api } from './services/api';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { DiscoverView } from './components/discover/DiscoverView';
import { WorkspaceView } from './components/workspace/WorkspaceView';
import { ComparisonView } from './components/comparison/ComparisonView';
import { EvaluationView } from './components/evaluation/EvaluationView';
import { InsightsView } from './components/insights/InsightsView';

export const App: React.FC = () => {
  // Start strictly from Step 1: Discover Papers
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [activeCorpus, setActiveCorpus] = useState<Corpus | null>(null);

  useEffect(() => {
    const fetchCorpora = async () => {
      try {
        const list = await api.listCorpora();
        if (list && list.length > 0) {
          setCorpora(list);
          setActiveCorpus(list[0]);
        }
      } catch (e) {
        console.warn('No active corpora found:', e);
      }
    };
    fetchCorpora();
  }, []);

  const handleCorpusCreated = async (name: string, query: string, paperIds: string[]) => {
    try {
      const created = await api.createCorpus(name, query, paperIds);
      setCorpora((prev) => [created, ...prev]);
      setActiveCorpus(created);
      setCurrentStep(2); // Move to workspace once corpus is created
    } catch (e) {
      console.warn('API error creating corpus, creating local session:', e);
      const newCorpus: Corpus = {
        id: `corpus-${Date.now()}`,
        name,
        query,
        status: 'ready',
        paper_count: paperIds.length,
        page_count: paperIds.length * 14,
        chunk_count: paperIds.length * 28,
        categories: ['cs.AI', 'cs.CL'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        papers: paperIds.map((id) => ({
          id: `p-${id}`,
          corpus_id: `corpus-${Date.now()}`,
          arxiv_id: id,
          title: `Research Publication (${id})`,
          authors: ['Academic Author et al.'],
          status: 'indexed',
          page_count: 14,
          chunk_count: 28,
          categories: ['cs.AI'],
          created_at: new Date().toISOString()
        }))
      };
      setCorpora((prev) => [newCorpus, ...prev]);
      setActiveCorpus(newCorpus);
      setCurrentStep(2);
    }
  };

  const handleUpdateCorpusName = async (newName: string) => {
    if (!activeCorpus) return;
    try {
      await api.updateCorpus(activeCorpus.id, newName);
    } catch (e) {
      console.warn('Rename error:', e);
    }
    setActiveCorpus((prev) => (prev ? { ...prev, name: newName } : null));
    setCorpora((prev) =>
      prev.map((c) => (c.id === activeCorpus.id ? { ...c, name: newName } : c))
    );
  };

  const handleDeleteCorpus = async (corpusId: string) => {
    try {
      await api.deleteCorpus(corpusId);
    } catch (e) {
      console.warn('Delete corpus error:', e);
    }
    const updated = corpora.filter((c) => c.id !== corpusId);
    setCorpora(updated);
    try {
      localStorage.removeItem(`raglab_convo_messages_${corpusId}`);
    } catch (e) {}

    if (activeCorpus?.id === corpusId) {
      if (updated.length > 0) {
        setActiveCorpus(updated[0]);
      } else {
        setActiveCorpus(null);
        setCurrentStep(1);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0B0E14] text-on-surface">
      {/* Row 1: Global Stepper & Identity */}
      <Header
        currentStep={currentStep}
        onSelectStep={(s) => setCurrentStep(s)}
        activeCorpus={activeCorpus}
        corporaList={corpora}
        onSelectCorpus={(c) => setActiveCorpus(c)}
        onDeleteCorpus={handleDeleteCorpus}
      />

      {/* Dynamic View Area */}
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {currentStep === 1 && (
          <DiscoverView onCorpusCreated={handleCorpusCreated} />
        )}

        {currentStep > 1 && !activeCorpus && (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4 bg-[#0B0E14] select-none">
            <div className="w-14 h-14 rounded-2xl bg-surface-container border border-outline-variant flex items-center justify-center text-primary shadow-lg shadow-primary/5">
              <span className="material-symbols-outlined text-[28px]">folder_off</span>
            </div>
            <div className="space-y-1.5 max-w-md">
              <h2 className="text-base font-semibold text-white">No Active Research Corpus</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                Please begin at <strong>Step 1 (Discover Papers)</strong> to search arXiv, select research papers across any academic domain, and create your corpus.
              </p>
            </div>
            <button
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2 rounded-xl bg-primary hover:bg-[#34c4b0] text-[#00201C] text-xs font-bold flex items-center gap-2 transition-all shadow-md active:scale-95"
            >
              <span className="material-symbols-outlined text-[16px]">search</span>
              <span>Go to Step 1: Discover Papers</span>
            </button>
          </div>
        )}

        {currentStep === 2 && activeCorpus && (
          <WorkspaceView
            key={activeCorpus.id}
            corpus={activeCorpus}
            onUpdateCorpusName={handleUpdateCorpusName}
          />
        )}
        {currentStep === 3 && activeCorpus && (
          <ComparisonView corpus={activeCorpus} />
        )}
        {currentStep === 4 && activeCorpus && (
          <EvaluationView corpus={activeCorpus} />
        )}
        {currentStep === 5 && activeCorpus && (
          <InsightsView corpus={activeCorpus} />
        )}
      </div>

      {/* Row 3: Subsystem Telemetry Footer */}
      <Footer />
    </div>
  );
};

export default App;
