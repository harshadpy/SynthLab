import React, { useState, useEffect, useRef } from 'react';
import { Corpus } from '../../types';
import { api } from '../../services/api';
import { SettingsModal } from './SettingsModal';
import { LangSmithModal } from './LangSmithModal';
import { ProfileDropdown } from './ProfileDropdown';

interface HeaderProps {
  currentStep: number;
  onSelectStep: (step: number) => void;
  activeCorpus: Corpus | null;
  corporaList: Corpus[];
  onSelectCorpus: (corpus: Corpus) => void;
  onDeleteCorpus?: (corpusId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  onSelectStep,
  activeCorpus,
  corporaList,
  onSelectCorpus,
  onDeleteCorpus,
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isLangSmithModalOpen, setIsLangSmithModalOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);

  const [langsmithStats, setLangsmithStats] = useState({
    connected: true,
    total_runs: 100,
    project_name: 'raglab',
    recent_runs: [] as any[]
  });

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    let mounted = true;
    const fetchStats = () => {
      api.getLangSmithStats().then((s) => {
        if (mounted && s) setLangsmithStats(s);
      }).catch(() => {});
    };

    fetchStats();
    // Fast live polling every 4 seconds
    const interval = setInterval(fetchStats, 4000);

    const handleTraceEvent = () => {
      fetchStats();
      setTimeout(fetchStats, 1200);
    };

    window.addEventListener('langsmith:trace_created', handleTraceEvent);
    window.addEventListener('focus', fetchStats);

    return () => {
      mounted = false;
      clearInterval(interval);
      window.removeEventListener('langsmith:trace_created', handleTraceEvent);
      window.removeEventListener('focus', fetchStats);
    };
  }, [currentStep]);
  const steps = [
    { id: 1, label: 'Discover Papers' },
    { id: 2, label: 'Research Workspace' },
    { id: 3, label: 'Architecture Comparison' },
    { id: 4, label: 'Evaluation' },
    { id: 5, label: 'Corpus Insights' },
  ];

  return (
    <header className="h-[52px] w-full bg-[#080B10] border-b border-outline-variant/80 px-4 flex items-center justify-between gap-4 shrink-0 z-40 select-none">
      {/* Left: App Identity & Version */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-surface-container-high border border-outline-variant flex items-center justify-center text-primary shadow-sm shadow-primary/10">
            <span className="material-symbols-outlined text-[17px]">biotech</span>
          </div>
          <span className="font-semibold text-sm tracking-tight text-white">SynthLab</span>
        </div>

        <div className="h-4 w-[1px] bg-outline-variant mx-1 hidden sm:block"></div>

        {/* Quick Benchmark Dropdown / Scope Badge */}
        {activeCorpus && (
          <div ref={dropdownRef} className="relative hidden lg:block">
            <button
              onClick={() => setIsDropdownOpen((prev) => !prev)}
              className={`flex items-center gap-1.5 bg-surface-container-low border ${
                isDropdownOpen ? 'border-primary shadow-sm shadow-primary/20' : 'border-outline-variant/70 hover:border-outline'
              } px-2.5 py-1 rounded-md text-left transition-colors cursor-pointer`}
              type="button"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
              <span className="font-mono text-xs text-slate-300 truncate max-w-[200px]">{activeCorpus.name}</span>
              <span className="font-mono text-[11px] text-tertiary-muted">· {activeCorpus.paper_count} papers</span>
              <span className={`material-symbols-outlined text-tertiary-muted text-[15px] transition-transform duration-150 ${
                isDropdownOpen ? 'rotate-180 text-primary' : ''
              }`}>
                arrow_drop_down
              </span>
            </button>
            {isDropdownOpen && (
              <div className="absolute left-0 top-full mt-1.5 w-72 max-h-80 overflow-y-auto custom-scroll bg-[#121722] border border-outline-variant rounded-lg shadow-2xl py-1.5 z-50 text-xs divide-y divide-outline-variant/30">
                <div className="px-3 py-1.5 flex items-center justify-between text-[10px] uppercase font-mono text-tertiary-muted tracking-wider">
                  <span>Select Corpus / Convo</span>
                  <span className="text-[9px] bg-surface-container-high px-1.5 py-0.5 rounded text-slate-300">
                    {corporaList.length}
                  </span>
                </div>
                <div className="py-1">
                  {corporaList.length === 0 && (
                    <div className="px-3 py-2 text-xs text-slate-400">No active corpora found.</div>
                  )}
                  {corporaList.map((c) => {
                    const isSelected = c.id === activeCorpus.id;
                    return (
                      <div
                        key={c.id}
                        onClick={() => {
                          onSelectCorpus(c);
                          setIsDropdownOpen(false);
                        }}
                        className={`group w-full px-3 py-1.5 hover:bg-surface-container flex items-center justify-between transition-colors cursor-pointer ${
                          isSelected ? 'bg-primary/10 text-primary font-medium' : 'text-slate-300'
                        }`}
                      >
                        <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${isSelected ? 'bg-primary' : 'bg-slate-500'}`}></span>
                          <span className="truncate text-xs">{c.name}</span>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className="font-mono text-[10px] text-tertiary-muted px-1.5 py-0.5 rounded bg-surface-container-high/60">
                            {c.paper_count}p
                          </span>
                          {onDeleteCorpus && (
                            <button
                              type="button"
                              title={`Delete "${c.name}"`}
                              onClick={(e) => {
                                e.stopPropagation();
                                if (window.confirm(`Delete corpus "${c.name}"?`)) {
                                  onDeleteCorpus(c.id);
                                }
                              }}
                              className="w-5 h-5 flex items-center justify-center rounded text-tertiary-muted hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                            >
                              <span className="material-symbols-outlined text-[14px]">delete</span>
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Center: Guided Workflow Stepper */}
      <nav aria-label="Research Workflow Steps" className="hidden xl:flex items-center">
        <ol className="flex items-center">
          {steps.map((step, idx) => {
            const isCompleted = currentStep > step.id;
            const isActive = currentStep === step.id;

            return (
              <li key={step.id} className="flex items-center">
                <button
                  onClick={() => onSelectStep(step.id)}
                  className={`group flex items-center gap-2 text-xs font-medium transition-colors ${
                    isActive
                      ? 'px-2.5 py-1 rounded-full bg-surface-container-high border border-primary/50 font-semibold text-primary shadow-sm shadow-primary/20'
                      : isCompleted
                      ? 'text-slate-300 hover:text-white'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {isCompleted ? (
                    <span className="w-5 h-5 rounded-full bg-primary/15 border border-primary/40 flex items-center justify-center text-primary text-[12px]">
                      <span className="material-symbols-outlined text-[13px] font-bold">check</span>
                    </span>
                  ) : isActive ? (
                    <span className="w-4 h-4 rounded-full bg-primary text-[#00201C] flex items-center justify-center text-[10px] font-mono font-bold">
                      {step.id}
                    </span>
                  ) : (
                    <span className="w-4 h-4 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center text-[10px] font-mono text-tertiary-muted group-hover:border-slate-500">
                      {step.id}
                    </span>
                  )}
                  <span>{step.label}</span>
                </button>

                {idx < steps.length - 1 && (
                  <div
                    className={`w-7 h-[1px] mx-2 ${
                      currentStep > step.id ? 'bg-primary/40' : 'bg-outline-variant'
                    }`}
                  />
                )}
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Right: LangSmith Status & Profile */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* LangSmith Pill */}
        <button
          type="button"
          onClick={() => setIsLangSmithModalOpen(true)}
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-container-low border border-outline-variant/70 hover:border-emerald-500/50 text-tertiary-muted font-mono text-[11px] transition-all group cursor-pointer"
          title={`LangSmith Project: ${langsmithStats.project_name} (Click to inspect telemetry & live traces)`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-300 group-hover:text-white transition-colors">LangSmith</span>
          <span>·</span>
          <span className="text-emerald-400 font-semibold">
            {langsmithStats.total_runs >= 100 ? `${langsmithStats.total_runs}+` : langsmithStats.total_runs} traces
          </span>
          <span className="material-symbols-outlined text-[12px] text-tertiary-muted group-hover:text-slate-200">open_in_new</span>
        </button>

        {/* Settings Button */}
        <button
          onClick={() => setIsSettingsModalOpen(true)}
          className={`w-8 h-8 rounded-lg border ${
            isSettingsModalOpen
              ? 'border-primary text-primary bg-surface-container'
              : 'border-outline-variant/70 bg-surface-container-low hover:bg-surface-container text-slate-400 hover:text-slate-200'
          } flex items-center justify-center transition-colors cursor-pointer`}
          title="Workspace & LLM Configuration"
          type="button"
        >
          <span className="material-symbols-outlined text-[17px]">tune</span>
        </button>

        {/* Profile Avatar */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsProfileDropdownOpen((prev) => !prev)}
            className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#143D37] to-primary/80 border border-primary/40 hover:border-primary flex items-center justify-center shrink-0 cursor-pointer shadow-sm transition-transform active:scale-95"
            title="Academic Researcher Profile (HT)"
          >
            <span className="font-mono text-xs font-semibold text-white">HT</span>
          </button>

          <ProfileDropdown
            isOpen={isProfileDropdownOpen}
            onClose={() => setIsProfileDropdownOpen(false)}
            corporaList={corporaList}
            activeCorpus={activeCorpus}
            onOpenSettings={() => {
              setIsProfileDropdownOpen(false);
              setIsSettingsModalOpen(true);
            }}
          />
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        onSaveSuccess={() => {
          api.getLangSmithStats().then((s) => {
            if (s) setLangsmithStats(s);
          });
        }}
      />

      {/* LangSmith Telemetry Modal */}
      <LangSmithModal
        isOpen={isLangSmithModalOpen}
        onClose={() => setIsLangSmithModalOpen(false)}
        stats={langsmithStats}
        onAddTestTrace={() => {
          setLangsmithStats((prev) => ({
            ...prev,
            total_runs: prev.total_runs + 1
          }));
        }}
      />
    </header>
  );
};
