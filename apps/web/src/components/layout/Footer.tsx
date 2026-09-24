import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-[#080B10] border-t border-outline-variant/80 py-1.5 px-4 shrink-0 select-none">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-1 text-tertiary-muted font-mono text-[10px]">
        <div className="flex items-center gap-2">
          <span>SynthLab Research Platform</span>
          <span>|</span>
          <span className="text-emerald-400">Telemetry: Subsystem Nominal</span>
        </div>
        <div className="flex items-center gap-3">
          <span>text-embedding-3-large</span>
          <span>·</span>
          <span>HNSW + BM25s</span>
          <span>·</span>
          <span>p95: 142ms</span>
        </div>
      </div>
    </footer>
  );
};
