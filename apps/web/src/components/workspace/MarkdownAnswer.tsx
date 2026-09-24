import React from 'react';
import { Citation } from '../../types';

interface MarkdownAnswerProps {
  content: string;
  citations?: Citation[];
  activeCitation: Citation | null;
  onCitationClick: (citation: Citation) => void;
  isStreaming?: boolean;
}

export const MarkdownAnswer: React.FC<MarkdownAnswerProps> = ({
  content,
  citations = [],
  activeCitation,
  onCitationClick,
  isStreaming = false,
}) => {
  // Helper to parse inline markdown (bold, italic, quoted italic, inline code, citations)
  const renderInline = (text: string): React.ReactNode[] => {
    // Unescape literal backslash escaped quotes if present
    const clean = text.replace(/\\"/g, '"');

    // Tokenize for:
    // 1. Interactive Citations: [1], [2], etc.
    // 2. Inline code: `code`
    // 3. Bold-Italic: ***text***
    // 4. Bold: **text**
    // 5. Quoted italic: *"text"* or *"text"?*
    // 6. Italic: *text* or _text_
    const regex = /(\[\d+\]|`[^`]+`|\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*\"[^*"]+\"\*|\*[^*]+\*|_[^_]+_)/g;
    const parts = clean.split(regex);

    return parts.map((part, idx) => {
      if (!part) return null;

      // 1. Citation match: [1], [2]
      const citMatch = part.match(/^\[(\d+)\]$/);
      if (citMatch) {
        const citNum = parseInt(citMatch[1], 10);
        const citation = citations[citNum - 1];
        if (citation) {
          const isActive =
            activeCitation &&
            activeCitation.arxiv_id === citation.arxiv_id &&
            activeCitation.rank === citation.rank;

          return (
            <button
              key={idx}
              type="button"
              onClick={() => onCitationClick(citation)}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono transition-all cursor-pointer align-baseline mx-1 ${
                isActive
                  ? 'bg-primary text-[#00201C] font-bold shadow-md shadow-primary/30 border border-primary scale-105 ring-2 ring-primary/40'
                  : 'font-semibold text-primary bg-[#102D29] border border-primary/60 hover:bg-[#16433E] hover:text-white'
              }`}
              title={`Inspect citation [${citNum}] from arXiv:${citation.arxiv_id}`}
            >
              <span className="material-symbols-outlined text-[12px]">format_quote</span>
              <span>[{citNum}]</span>
            </button>
          );
        }
        return <span key={idx} className="font-mono text-primary font-semibold">[{citNum}]</span>;
      }

      // 2. Inline code: `code`
      if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
        return (
          <code
            key={idx}
            className="font-mono text-[12px] px-1.5 py-0.5 rounded bg-[#131A26] border border-outline-variant/80 text-primary font-medium"
          >
            {part.slice(1, -1)}
          </code>
        );
      }

      // 3. Bold-Italic: ***text***
      if (part.startsWith('***') && part.endsWith('***') && part.length > 6) {
        return (
          <strong key={idx} className="font-bold italic text-white">
            {part.slice(3, -3)}
          </strong>
        );
      }

      // 4. Bold: **text**
      if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
        return (
          <strong key={idx} className="font-semibold text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }

      // 5. Quoted Italic: *"text"*
      if (part.startsWith('*') && part.endsWith('*') && part.includes('"') && part.length > 4) {
        const inner = part.slice(1, -1);
        return (
          <span key={idx} className="italic text-primary/95 font-medium">
            {inner}
          </span>
        );
      }

      // 6. Italic: *text* or _text_
      if ((part.startsWith('*') && part.endsWith('*') && part.length > 2) ||
          (part.startsWith('_') && part.endsWith('_') && part.length > 2)) {
        return (
          <em key={idx} className="italic text-slate-200">
            {part.slice(1, -1)}
          </em>
        );
      }

      return <span key={idx}>{part}</span>;
    });
  };

  // Split lines and render structured paragraphs, lists, headers, and code blocks
  const lines = content.split('\n');
  const renderedElements: React.ReactNode[] = [];
  let currentList: { type: 'ul' | 'ol'; items: Array<{ num?: string; content: React.ReactNode }> } | null = null;
  let inCodeBlock = false;
  let codeBlockBuffer: string[] = [];
  let codeBlockLang = '';

  const flushList = () => {
    if (currentList) {
      if (currentList.type === 'ul') {
        renderedElements.push(
          <ul key={`ul-${renderedElements.length}`} className="space-y-2.5 my-3 pl-1">
            {currentList.items.map((it, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-slate-200 leading-relaxed">
                <span className="w-1.5 h-1.5 rounded-full bg-primary/80 shrink-0 mt-2"></span>
                <div className="flex-1 min-w-0">{it.content}</div>
              </li>
            ))}
          </ul>
        );
      } else {
        renderedElements.push(
          <ol key={`ol-${renderedElements.length}`} className="space-y-3 my-3 pl-1">
            {currentList.items.map((it, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-slate-200 leading-relaxed font-sans">
                <span className="font-mono text-xs font-bold text-primary shrink-0 mt-0.5 bg-primary/10 px-1.5 py-0.2 rounded border border-primary/25 shadow-sm">
                  {it.num ? `${it.num}.` : `${idx + 1}.`}
                </span>
                <div className="flex-1 min-w-0">{it.content}</div>
              </li>
            ))}
          </ol>
        );
      }
      currentList = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Code block toggle
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        const codeText = codeBlockBuffer.join('\n');
        renderedElements.push(
          <div key={`code-${renderedElements.length}`} className="my-3 rounded-xl bg-[#090D15] border border-outline-variant overflow-hidden">
            {codeBlockLang && (
              <div className="px-3 py-1 bg-surface-container-low border-b border-outline-variant flex items-center justify-between text-[11px] font-mono text-tertiary-muted">
                <span>{codeBlockLang}</span>
              </div>
            )}
            <pre className="p-3 text-xs font-mono text-slate-200 overflow-x-auto custom-scroll leading-relaxed">
              <code>{codeText}</code>
            </pre>
          </div>
        );
        codeBlockBuffer = [];
        inCodeBlock = false;
        codeBlockLang = '';
      } else {
        flushList();
        inCodeBlock = true;
        codeBlockLang = trimmed.slice(3).trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockBuffer.push(rawLine);
      continue;
    }

    // Blank line handling with loose list lookahead
    if (!trimmed) {
      let continueList = false;
      if (currentList) {
        for (let j = i + 1; j < lines.length; j++) {
          const nextTrim = lines[j].trim();
          if (!nextTrim) continue;
          if (currentList.type === 'ol' && /^\d+\.\s+/.test(nextTrim)) {
            continueList = true;
          } else if (currentList.type === 'ul' && /^[-*+]\s+/.test(nextTrim)) {
            continueList = true;
          }
          break;
        }
      }
      if (!continueList) {
        flushList();
      }
      continue;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      flushList();
      renderedElements.push(
        <h4 key={`h4-${renderedElements.length}`} className="text-sm font-bold text-white tracking-wide pt-2 pb-0.5 flex items-center gap-1.5">
          <span className="w-1.5 h-3.5 rounded-sm bg-primary shrink-0"></span>
          <span>{renderInline(trimmed.slice(4))}</span>
        </h4>
      );
      continue;
    }

    if (trimmed.startsWith('## ')) {
      flushList();
      renderedElements.push(
        <h3 key={`h3-${renderedElements.length}`} className="text-base font-semibold text-white tracking-wide pt-2.5 pb-1 flex items-center gap-2 border-b border-outline-variant/60">
          <span>{renderInline(trimmed.slice(3))}</span>
        </h3>
      );
      continue;
    }

    if (trimmed.startsWith('# ')) {
      flushList();
      renderedElements.push(
        <h2 key={`h2-${renderedElements.length}`} className="text-lg font-bold text-white tracking-tight pt-3 pb-1">
          {renderInline(trimmed.slice(2))}
        </h2>
      );
      continue;
    }

    // Blockquote
    if (trimmed.startsWith('> ')) {
      flushList();
      renderedElements.push(
        <blockquote key={`bq-${renderedElements.length}`} className="border-l-2 border-primary/70 pl-3 py-1.5 my-2 bg-surface-container-low/60 rounded-r-lg text-slate-300 text-sm italic">
          {renderInline(trimmed.slice(2))}
        </blockquote>
      );
      continue;
    }

    // Unordered list item
    const ulMatch = trimmed.match(/^[-*+]\s+(.*)$/);
    if (ulMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList();
        currentList = { type: 'ul', items: [] };
      }
      currentList.items.push({ content: renderInline(ulMatch[1]) });
      continue;
    }

    // Ordered list item
    const olMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (olMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList();
        currentList = { type: 'ol', items: [] };
      }
      currentList.items.push({ num: olMatch[1], content: renderInline(olMatch[2]) });
      continue;
    }

    // Standard paragraph
    flushList();
    renderedElements.push(
      <p key={`p-${renderedElements.length}`} className="text-[#F1F5F9] text-[14.5px] leading-[1.75] font-normal">
        {renderInline(rawLine)}
      </p>
    );
  }

  flushList();

  return (
    <div className="space-y-3.5 select-text">
      {renderedElements}
      {isStreaming && (
        <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse align-middle rounded-sm"></span>
      )}
    </div>
  );
};
