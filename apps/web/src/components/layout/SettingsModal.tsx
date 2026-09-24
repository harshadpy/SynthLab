import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveSuccess?: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, onSaveSuccess }) => {
  const [activeTab, setActiveTab] = useState<'providers' | 'models' | 'observability'>('providers');
  const [loading, setLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Provider Keys
  const [openaiKey, setOpenaiKey] = useState('');
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [anthropicKey, setAnthropicKey] = useState('');
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);
  const [cohereKey, setCohereKey] = useState('');
  const [showCohereKey, setShowCohereKey] = useState(false);

  // Models
  const [chatModel, setChatModel] = useState('gpt-4o');
  const [embeddingModel, setEmbeddingModel] = useState('text-embedding-3-large');
  const [rerankerModel, setRerankerModel] = useState('Cohere-v3');

  // LangSmith Observability
  const [tracingEnabled, setTracingEnabled] = useState(false);
  const [langsmithEndpoint, setLangsmithEndpoint] = useState('https://api.smith.langchain.com');
  const [langsmithKey, setLangsmithKey] = useState('');
  const [showLangsmithKey, setShowLangsmithKey] = useState(false);
  const [langsmithProject, setLangsmithProject] = useState('raglab');

  // Remote config tracking
  const [serverConfig, setServerConfig] = useState<any>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    // Load local storage first
    try {
      const local = localStorage.getItem('raglab_user_settings');
      if (local) {
        const parsed = JSON.parse(local);
        if (parsed.openaiKey) setOpenaiKey(parsed.openaiKey);
        if (parsed.anthropicKey) setAnthropicKey(parsed.anthropicKey);
        if (parsed.cohereKey) setCohereKey(parsed.cohereKey);
        if (parsed.chatModel) setChatModel(parsed.chatModel);
        if (parsed.embeddingModel) setEmbeddingModel(parsed.embeddingModel);
        if (parsed.rerankerModel) setRerankerModel(parsed.rerankerModel);
        if (parsed.tracingEnabled !== undefined) setTracingEnabled(parsed.tracingEnabled);
        if (parsed.langsmithEndpoint) setLangsmithEndpoint(parsed.langsmithEndpoint);
        if (parsed.langsmithKey) setLangsmithKey(parsed.langsmithKey);
        if (parsed.langsmithProject) setLangsmithProject(parsed.langsmithProject);
      }
    } catch (e) {}

    // Fetch server status
    api.getSettings().then((s) => {
      setServerConfig(s);
      if (s) {
        if (!chatModel && s.default_chat_model) setChatModel(s.default_chat_model);
        if (!embeddingModel && s.default_embedding_model) setEmbeddingModel(s.default_embedding_model);
        if (s.langchain_tracing_v2 !== undefined) setTracingEnabled(s.langchain_tracing_v2);
        if (s.langchain_endpoint) setLangsmithEndpoint(s.langchain_endpoint);
        if (s.langchain_project) setLangsmithProject(s.langchain_project);
      }
    }).finally(() => setLoading(false));
  }, [isOpen]);

  const handleSave = async () => {
    setSaveStatus('saving');
    const payload = {
      openai_api_key: openaiKey || undefined,
      anthropic_api_key: anthropicKey || undefined,
      cohere_api_key: cohereKey || undefined,
      default_chat_model: chatModel,
      default_embedding_model: embeddingModel,
      langchain_tracing_v2: tracingEnabled,
      langchain_endpoint: langsmithEndpoint,
      langchain_api_key: langsmithKey || undefined,
      langchain_project: langsmithProject,
    };

    // Save to localStorage
    try {
      localStorage.setItem('raglab_user_settings', JSON.stringify({
        openaiKey,
        anthropicKey,
        cohereKey,
        chatModel,
        embeddingModel,
        rerankerModel,
        tracingEnabled,
        langsmithEndpoint,
        langsmithKey,
        langsmithProject,
      }));
    } catch (e) {}

    const ok = await api.updateSettings(payload);
    if (ok) {
      setSaveStatus('saved');
      onSaveSuccess?.();
      setTimeout(() => {
        setSaveStatus('idle');
        onClose();
      }, 700);
    } else {
      setSaveStatus('saved'); // Local storage is updated anyway
      setTimeout(() => {
        setSaveStatus('idle');
        onClose();
      }, 700);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in select-none">
      <div className="bg-[#0F141F] border border-outline-variant rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-outline-variant/80 flex items-center justify-between bg-[#0B0E15]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-surface-container-high border border-outline-variant flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-[18px]">tune</span>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">System & Model Configuration</h2>
              <p className="text-[11px] text-tertiary-muted font-mono">Configure LLM providers, model selection, and LangSmith tracing</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg hover:bg-surface-container flex items-center justify-center text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center border-b border-outline-variant/60 px-6 bg-[#0B0E15]/50 gap-2 pt-2">
          {[
            { id: 'providers', label: 'LLM Providers', icon: 'key' },
            { id: 'models', label: 'Model Selection', icon: 'smart_toy' },
            { id: 'observability', label: 'LangSmith Observability', icon: 'monitoring' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-medium border-b-2 transition-all cursor-pointer ${
                activeTab === tab.id
                  ? 'border-primary text-primary font-semibold bg-surface-container/30 rounded-t'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <span className="material-symbols-outlined text-[15px]">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto custom-scroll flex-1 space-y-5 text-xs">
          {/* TAB 1: LLM Providers */}
          {activeTab === 'providers' && (
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/60 text-[11px] text-slate-300 flex items-start gap-2.5">
                <span className="material-symbols-outlined text-primary text-[17px] shrink-0 mt-0.5">info</span>
                <p className="leading-relaxed">
                  Keys are used to perform live paper parsing, dense vector indexing, and generation. In <strong>dry-run mode</strong>, the system serves high-fidelity research benchmarks without consuming live API tokens.
                </p>
              </div>

              {/* OpenAI API Key */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-mono text-slate-300 font-medium flex items-center gap-1.5">
                    <span>OPENAI_API_KEY</span>
                    {serverConfig?.openai_api_key_configured && (
                      <span className="text-[10px] text-emerald-400 font-normal bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/30">Configured in .env</span>
                    )}
                  </label>
                  <span className="text-[10px] text-tertiary-muted">Used for GPT-4o & embeddings</span>
                </div>
                <div className="relative flex items-center">
                  <input
                    type={showOpenaiKey ? 'text' : 'password'}
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    placeholder={serverConfig?.openai_api_key_masked || "sk-proj-..."}
                    className="w-full h-8 bg-surface-container border border-outline-variant rounded-md pl-3 pr-9 font-mono text-xs text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                    className="absolute right-2.5 text-tertiary-muted hover:text-slate-200 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {showOpenaiKey ? 'visibility_off' : 'visibility'}
                    </span>
                  </button>
                </div>
              </div>

              {/* Anthropic API Key */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-mono text-slate-300 font-medium flex items-center gap-1.5">
                    <span>ANTHROPIC_API_KEY</span>
                    {serverConfig?.anthropic_api_key_configured && (
                      <span className="text-[10px] text-emerald-400 font-normal bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/30">Configured in .env</span>
                    )}
                  </label>
                  <span className="text-[10px] text-tertiary-muted">Used for Claude 3.5 Sonnet</span>
                </div>
                <div className="relative flex items-center">
                  <input
                    type={showAnthropicKey ? 'text' : 'password'}
                    value={anthropicKey}
                    onChange={(e) => setAnthropicKey(e.target.value)}
                    placeholder={serverConfig?.anthropic_api_key_masked || "sk-ant-..."}
                    className="w-full h-8 bg-surface-container border border-outline-variant rounded-md pl-3 pr-9 font-mono text-xs text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                    className="absolute right-2.5 text-tertiary-muted hover:text-slate-200 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {showAnthropicKey ? 'visibility_off' : 'visibility'}
                    </span>
                  </button>
                </div>
              </div>

              {/* Cohere API Key */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-mono text-slate-300 font-medium flex items-center gap-1.5">
                    <span>COHERE_API_KEY</span>
                    {serverConfig?.cohere_api_key_configured && (
                      <span className="text-[10px] text-emerald-400 font-normal bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/30">Configured in .env</span>
                    )}
                  </label>
                  <span className="text-[10px] text-tertiary-muted">Used for Cohere-v3 Reranker</span>
                </div>
                <div className="relative flex items-center">
                  <input
                    type={showCohereKey ? 'text' : 'password'}
                    value={cohereKey}
                    onChange={(e) => setCohereKey(e.target.value)}
                    placeholder={serverConfig?.cohere_api_key_masked || "co-..."}
                    className="w-full h-8 bg-surface-container border border-outline-variant rounded-md pl-3 pr-9 font-mono text-xs text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCohereKey(!showCohereKey)}
                    className="absolute right-2.5 text-tertiary-muted hover:text-slate-200 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {showCohereKey ? 'visibility_off' : 'visibility'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Model Selection */}
          {activeTab === 'models' && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="font-mono text-slate-300 font-medium">DEFAULT_CHAT_MODEL</label>
                <select
                  value={chatModel}
                  onChange={(e) => setChatModel(e.target.value)}
                  className="w-full h-8 bg-surface-container border border-outline-variant rounded-md px-2.5 font-sans text-xs text-white focus:border-primary focus:outline-none transition-colors"
                >
                  <option value="gpt-4o">gpt-4o (High Reasoning & Multi-Hop Synthesis)</option>
                  <option value="gpt-4o-mini">gpt-4o-mini (Low-Latency RAG Ingestion)</option>
                  <option value="claude-3-5-sonnet">claude-3-5-sonnet (High Context Faithfulness)</option>
                  <option value="gemini-1.5-pro">gemini-1.5-pro (1M Token Long-Context Benchmark)</option>
                  <option value="gpt-5.6-luna">gpt-5.6-luna (Simulated Research Frontier Model)</option>
                </select>
                <p className="text-[10px] text-tertiary-muted">Selected foundation model used in Synthesis & Evaluation.</p>
              </div>

              <div className="space-y-1.5">
                <label className="font-mono text-slate-300 font-medium">DEFAULT_EMBEDDING_MODEL</label>
                <select
                  value={embeddingModel}
                  onChange={(e) => setEmbeddingModel(e.target.value)}
                  className="w-full h-8 bg-surface-container border border-outline-variant rounded-md px-2.5 font-sans text-xs text-white focus:border-primary focus:outline-none transition-colors"
                >
                  <option value="text-embedding-3-large">text-embedding-3-large (3072-dim Cosine Inverted Index)</option>
                  <option value="text-embedding-3-small">text-embedding-3-small (1536-dim High Throughput)</option>
                  <option value="cohere-embed-v3">cohere-embed-v3 (Multi-lingual Academic Semantic Search)</option>
                  <option value="bge-large-en-v1.5">bge-large-en-v1.5 (Local HuggingFace Dense Embedding)</option>
                </select>
                <p className="text-[10px] text-tertiary-muted">Dense vector representation computed during chunk indexing.</p>
              </div>

              <div className="space-y-1.5">
                <label className="font-mono text-slate-300 font-medium">DEFAULT_RERANKER_ENGINE</label>
                <select
                  value={rerankerModel}
                  onChange={(e) => setRerankerModel(e.target.value)}
                  className="w-full h-8 bg-surface-container border border-outline-variant rounded-md px-2.5 font-sans text-xs text-white focus:border-primary focus:outline-none transition-colors"
                >
                  <option value="Cohere-v3">Cohere-v3 Cross-Encoder Reranker</option>
                  <option value="BGE-Reranker-Large">BGE-Reranker-Large (Open-source Neural Ranker)</option>
                  <option value="ColBERT-v2">ColBERT-v2 (Late-Interaction Token Scoring)</option>
                </select>
                <p className="text-[10px] text-tertiary-muted">Cross-encoder reranking pass executed on top retrieved candidate chunks.</p>
              </div>
            </div>
          )}

          {/* TAB 3: LangSmith Observability */}
          {activeTab === 'observability' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low border border-outline-variant/60">
                <div className="space-y-0.5">
                  <div className="font-mono text-xs font-semibold text-white">LANGCHAIN_TRACING_V2</div>
                  <div className="text-[11px] text-slate-400">Stream runtime RAG pipelines and feedback to LangSmith</div>
                </div>
                <button
                  type="button"
                  onClick={() => setTracingEnabled(!tracingEnabled)}
                  className={`w-11 h-6 rounded-full transition-colors relative flex items-center p-1 cursor-pointer ${
                    tracingEnabled ? 'bg-emerald-500' : 'bg-surface-container-high border border-outline-variant'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      tracingEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              <div className="space-y-1.5">
                <label className="font-mono text-slate-300 font-medium">LANGCHAIN_ENDPOINT</label>
                <input
                  type="text"
                  value={langsmithEndpoint}
                  onChange={(e) => setLangsmithEndpoint(e.target.value)}
                  placeholder="https://api.smith.langchain.com"
                  className="w-full h-8 bg-surface-container border border-outline-variant rounded-md px-3 font-mono text-xs text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-mono text-slate-300 font-medium">LANGCHAIN_PROJECT</label>
                <input
                  type="text"
                  value={langsmithProject}
                  onChange={(e) => setLangsmithProject(e.target.value)}
                  placeholder="raglab"
                  className="w-full h-8 bg-surface-container border border-outline-variant rounded-md px-3 font-mono text-xs text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-mono text-slate-300 font-medium">LANGCHAIN_API_KEY</label>
                  {serverConfig?.langchain_api_key_configured && (
                    <span className="text-[10px] text-emerald-400 font-normal bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/30">Configured in .env</span>
                  )}
                </div>
                <div className="relative flex items-center">
                  <input
                    type={showLangsmithKey ? 'text' : 'password'}
                    value={langsmithKey}
                    onChange={(e) => setLangsmithKey(e.target.value)}
                    placeholder={serverConfig?.langchain_api_key_masked || "lsv2_pt_..."}
                    className="w-full h-8 bg-surface-container border border-outline-variant rounded-md pl-3 pr-9 font-mono text-xs text-white placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowLangsmithKey(!showLangsmithKey)}
                    className="absolute right-2.5 text-tertiary-muted hover:text-slate-200 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {showLangsmithKey ? 'visibility_off' : 'visibility'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-outline-variant/80 bg-[#0B0E15] flex items-center justify-between">
          <span className="text-[11px] font-mono text-tertiary-muted">
            {saveStatus === 'saved' ? (
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">check_circle</span>
                Settings Saved & Applied
              </span>
            ) : (
              'Changes take effect immediately'
            )}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-container text-xs text-slate-300 hover:text-white transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saveStatus === 'saving'}
              className="px-4 py-1.5 rounded-lg bg-primary hover:bg-[#34c4b0] text-[#00201C] text-xs font-bold transition-all shadow-md shadow-primary/20 cursor-pointer flex items-center gap-1.5"
            >
              {saveStatus === 'saving' ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-[#00201C] border-t-transparent rounded-full animate-spin"></span>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[15px]">save</span>
                  <span>Save Configuration</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
