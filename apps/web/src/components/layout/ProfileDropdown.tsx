import React, { useState, useRef, useEffect } from 'react';
import { Corpus } from '../../types';

interface ProfileDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  corporaList: Corpus[];
  activeCorpus: Corpus | null;
  onOpenSettings: () => void;
}

export const ProfileDropdown: React.FC<ProfileDropdownProps> = ({
  isOpen,
  onClose,
  corporaList,
  activeCorpus,
  onOpenSettings,
}) => {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [citationFormat, setCitationFormat] = useState('BibTeX');
  const [copiedNotification, setCopiedNotification] = useState<string | null>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const totalPapers = corporaList.reduce((acc, c) => acc + (c.paper_count || c.papers?.length || 0), 0);

  const handleExportSession = () => {
    try {
      const exportData = {
        exported_at: new Date().toISOString(),
        corpora_count: corporaList.length,
        total_papers: totalPapers,
        active_corpus: activeCorpus?.name || null,
        corpora: corporaList,
      };
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `raglab-session-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setCopiedNotification('Exported session JSON');
      setTimeout(() => setCopiedNotification(null), 2500);
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearCache = () => {
    if (window.confirm('Clear all conversation messages across all corpora?')) {
      Object.keys(localStorage).forEach((key) => {
        if (key.startsWith('raglab_convo_messages_')) {
          localStorage.removeItem(key);
        }
      });
      setCopiedNotification('Conversation caches cleared');
      setTimeout(() => {
        setCopiedNotification(null);
        window.location.reload();
      }, 800);
    }
  };

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 top-full mt-2 w-80 bg-[#101520] border border-outline-variant rounded-2xl shadow-2xl z-50 text-xs overflow-hidden select-none animate-fade-in divide-y divide-outline-variant/40"
    >
      {/* Profile Header */}
      <div className="p-4 bg-[#0B0E15]/90 flex items-center gap-3">
        <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-[#143D37] to-primary/80 border border-primary/50 flex items-center justify-center shrink-0 shadow-md">
          <span className="font-mono text-sm font-bold text-white tracking-wider">HT</span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-semibold text-white truncate">HT · Academic Researcher</h3>
            <span className="material-symbols-outlined text-[15px] text-primary" title="Verified Researcher">verified</span>
          </div>
          <p className="text-[11px] text-slate-400 truncate">researcher@arxiv-raglab.org</p>
          <div className="mt-1 flex items-center gap-1 font-mono text-[10px] text-tertiary-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>CSAIL AI Lab · Active</span>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 p-3 gap-2 bg-[#0C1018]">
        <div className="p-2 rounded-xl bg-surface-container-low border border-outline-variant/60 text-center">
          <div className="text-[10px] font-mono uppercase text-tertiary-muted">Indexed Corpora</div>
          <div className="text-base font-bold text-white font-mono">{corporaList.length}</div>
        </div>
        <div className="p-2 rounded-xl bg-surface-container-low border border-outline-variant/60 text-center">
          <div className="text-[10px] font-mono uppercase text-tertiary-muted">Total Papers</div>
          <div className="text-base font-bold text-primary font-mono">{totalPapers}</div>
        </div>
      </div>

      {/* Preferences */}
      <div className="p-3.5 space-y-3">
        <div className="space-y-1.5">
          <label className="text-[10px] font-mono uppercase text-tertiary-muted">Citation Export Format</label>
          <div className="grid grid-cols-3 gap-1.5 font-mono text-[11px]">
            {['BibTeX', 'APA 7th', 'IEEE'].map((fmt) => (
              <button
                key={fmt}
                onClick={() => setCitationFormat(fmt)}
                className={`py-1 rounded border transition-colors cursor-pointer ${
                  citationFormat === fmt
                    ? 'border-primary bg-primary/15 text-primary font-bold'
                    : 'border-outline-variant/60 bg-surface-container-low text-slate-400 hover:text-slate-200'
                }`}
              >
                {fmt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="p-2 space-y-0.5">
        <button
          type="button"
          onClick={() => {
            onClose();
            onOpenSettings();
          }}
          className="w-full px-3 py-2 rounded-lg hover:bg-surface-container flex items-center justify-between text-slate-300 hover:text-white transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-[16px] text-tertiary-muted">tune</span>
            <span>Workspace & LLM Settings</span>
          </div>
          <span className="material-symbols-outlined text-[14px] text-tertiary-muted">chevron_right</span>
        </button>

        <button
          type="button"
          onClick={handleExportSession}
          className="w-full px-3 py-2 rounded-lg hover:bg-surface-container flex items-center justify-between text-slate-300 hover:text-white transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-[16px] text-primary">download</span>
            <span>Export Research Session</span>
          </div>
          <span className="material-symbols-outlined text-[14px] text-tertiary-muted">chevron_right</span>
        </button>

        <button
          type="button"
          onClick={handleClearCache}
          className="w-full px-3 py-2 rounded-lg hover:bg-red-500/10 flex items-center justify-between text-slate-300 hover:text-red-400 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-[16px] text-red-400/80">delete_sweep</span>
            <span>Clear Conversation Caches</span>
          </div>
          <span className="material-symbols-outlined text-[14px] text-tertiary-muted">chevron_right</span>
        </button>
      </div>

      {copiedNotification && (
        <div className="p-2 text-center font-mono text-[10px] text-emerald-400 bg-emerald-500/10">
          {copiedNotification}
        </div>
      )}
    </div>
  );
};
