# Product Requirements Document (PRD)
# ArXiv RAG Research Lab — Unified Product & Design Spec

**Document status:** Draft v2 (unifies functional PRD + design system + UI review findings)
**Product type:** Multi-paper research and RAG evaluation platform
**Primary users:** AI/ML researchers, students, engineers, technical learners
**Core value proposition:** Search ArXiv, build a research corpus from selected papers, chat with that corpus, and compare five RAG architectures side by side using reproducible LangSmith evaluations — all evidence-backed down to the page and chunk.

---

## 1. Product Overview

ArXiv RAG Research Lab is a research workspace where users search ArXiv, select multiple papers, create a persistent research corpus, and interact with it through:

- Multi-paper conversational research chat
- Paper summaries and metadata
- Evidence-backed answers with paper and page/chunk citations
- Five interchangeable RAG architectures (Hybrid, Hierarchical, GraphRAG, Agentic, Adaptive)
- Side-by-side architecture comparison
- LangSmith tracing, datasets, experiments, and evaluations
- Corpus-level research insights and exports

This is not a PDF chatbot. Its differentiator is evaluating different RAG architectures against the same user-built corpus and benchmark questions — with full transparency into retrieval, scoring, and reasoning.

---

## 2. Problem Statement

Existing RAG demos typically:

- Work with one or a few manually uploaded documents
- Hide the retrieval process from the user
- Don't compare retrieval architectures fairly
- Lack reproducible evaluation
- Produce answers without transparent, page-level evidence

Researchers need to: search a topic → build a corpus from relevant papers → understand papers individually and collectively → ask cross-paper questions → compare RAG approaches on identical inputs → inspect *why* one architecture outperformed another.

---

## 3. Goals

### 3.1 Primary
- ArXiv search with rich metadata and multi-select
- Named, persistent research corpus creation
- Asynchronous PDF processing preserving page/section/chunk metadata
- Multi-paper chat over the active corpus
- Five selectable, swappable RAG architectures behind one shared interface
- Architecture comparison using identical corpus + evaluation questions
- LangSmith tracing and evaluation as a first-class feature, not a log
- Transparent, inspectable evidence for every generated claim
- A dashboard that reads as a **serious retrieval-engineering tool**, not a generic chat UI

### 3.2 Secondary
- Save/reopen workspaces; add/remove papers; refresh corpus
- Export notes, chat history, experiment results, corpus metadata
- Function as a credible AI/RAG engineering portfolio piece

### 3.3 Non-Goals (v1)
- Full citation management (Zotero-class)
- Autonomous publication or foundation-model training
- Universal repository support (ArXiv only for v1)
- General-purpose autonomous research agent
- Guaranteeing scientific correctness of generated conclusions

---

## 4. Target Users

| Persona | Need |
|---|---|
| AI/ML Student | Understand a topic by chatting across multiple papers |
| RAG Engineer | Compare retrieval strategies, see quality/latency/cost trade-offs |
| Researcher | Build a focused corpus, surface themes/methods/gaps |
| Portfolio Reviewer | See modular architecture, evaluation rigor, observability |

---

## 5. Core User Journey

```text
Search ArXiv → Select papers → Create corpus → Async ingest & index
      → Research Workspace (chat + evidence) → Architecture Comparison
      → Run LangSmith Evaluation → Corpus Insights → Export
```

This journey is now made explicit in-product as a **top-level stepper** (see §7.1) rather than a flat tab row — a direct fix from UI review round 1, where steps read as unordered tabs.

---

## 6. Design System

*(New in this revision — governs every screen so the product reads as one coherent tool rather than five independently generated ones.)*

**Theme:** Dark mode primary, technical/academic tone — not a generic AI-startup gradient look.

| Token | Value | Usage |
|---|---|---|
| Background | `#0B0E14` | App shell |
| Surface | `#131822` | Cards, panels |
| Border | `#1F2733` | Hairlines, dividers |
| Accent (primary) | Teal `#2DD4BF` | Primary actions, active states, citations |
| Warning | Amber `#F5B942` | Processing / needs-attention **only** — not decorative |
| Error | Coral `#F87171` | Failures only |
| Text — primary | Off-white | Answers, titles |
| Text — secondary | Muted gray | Authors, descriptions |
| Text — tertiary/metadata | Dim gray, monospace | IDs, trace IDs, timestamps, token counts |

**Typography:** Geometric sans (e.g. Inter) for UI text; monospace (e.g. JetBrains Mono) reserved strictly for technical values — arXiv IDs, chunk IDs, trace IDs, latency, token counts. This distinction is a core legibility mechanism, not decoration.

**Components:** 12px card radius, 1px hairline borders (shadows reserved for elevated/hover states only), thin-line icons, 8px spacing grid.

**Hierarchy rule (critical):** Every element on screen must map to exactly one of three tiers, styled distinctly:
1. **Primary** — answer text, paper titles, citation chips → full contrast, larger, teal accents
2. **Secondary** — strategy tags, retrieval scores, config labels → muted but legible
3. **Tertiary** — session/trace IDs, telemetry, latency footers → smallest, dimmest, monospace, collapsible where possible

This rule was the single biggest gap identified in UI review round 1 (everything rendered at the same visual weight) and is now a binding constraint on every screen, not a suggestion.

---

## 7. Screen Specifications

### 7.1 Global navigation — Workflow Stepper
Replaces the original flat "1. Discover · 2. Workspace · 3. Comparison · 4. Eval" tab row with a true stepper: connecting line, checkmarks on completed steps, current step highlighted. *(Confirmed fixed in round-2 screenshot — retain this pattern and extend the same treatment to any future step, e.g. Corpus Insights.)*

### 7.2 Discover Papers
- Centered search bar (max 640px), filter chips (category, date range), sort toggle
- Results as a hairline-separated list (not heavy bordered cards): title, authors (truncate 3), 2-line abstract with fade mask, monospace category tags, date
- Checkbox on hover in left margin
- Selection triggers a bottom sheet: thumbnails of selected papers + "Create Corpus →"

### 7.3 Create Corpus
- Step 1: selected-paper chips, name input, description, live-computed stats (paper/author count, date span)
- Step 2: per-paper processing stepper (Download → Parse → Chunk → Index) with independent status dots; failed papers stay visible with inline retry, never blocking the rest of the corpus

### 7.4 Research Workspace (core screen)
Three-panel layout, resizable:

- **Top bar (consolidated):** corpus title + status badge on row 1; retrieval config (Strategy selector, Top-K, Reranker, Add Papers) on row 2. *(Round 2 fix: architecture strategy and Top-K/Reranker now live together at the top instead of being split between the header and the chat input — keep this consolidation; it was the #1 fix from round 1 feedback.)*
- **Left panel:** paper library, hairline rows, 4px left-border status color, page/chunk counts in monospace, filter/search at top
- **Center panel:** chat thread. Assistant messages as clean text blocks (no bubble fill); user messages as right-aligned bubbles. Inline citations render as distinct teal chips, visually separated from other UI teal (see §7.6). Run-level metadata (model, latency, trace ID) collapses into a single compact line under each assistant message — not a permanent strip above the whole thread. *(Round 1 flagged the old metadata strip as pushing the actual answer down; round 2 shows this fixed as a slim one-line summary — keep it slim.)*
- **Right panel — Evidence Inspector:** paper title, arXiv ID (monospace, copyable), page/section breadcrumb, retrieved chunk in a left-bordered quote block, similarity/BM25/reranker scores as labeled bars, and a context-attention visualization. **Must be fully scrollable with a visible scroll affordance** — round 1 found this panel's lower content (similarity scores, token range) clipped at the panel edge with no indication more content existed. Round 2 shows more content fitting, but scroll behavior for longer evidence sets still needs explicit QA.

### 7.5 Architecture Selector
Five compact toggle buttons (icon + label) for Hybrid / Hierarchical / GraphRAG / Agentic / Adaptive, living in the workspace's config row (§7.4), not floating separately near the input. For the dedicated comparison screen, expand each into a card: icon, one-line description, 2–3 word strength/trade-off tags, evaluation status badge. Active state = 1px teal border/underline, not a filled background — keep density high.

### 7.6 Citation & Evidence Treatment
- Inline citation chips (`[1]`, `[2]`) must be visually distinct from all other teal UI elements (buttons, tags, active states) — e.g. a unique pill shape or a secondary accent hue — since evidence-checking is the product's core differentiator and currently risks blending into general color noise (flagged round 1).
- Clicking a citation always opens/updates the Evidence Inspector; never a dead-end tooltip.

### 7.7 Evaluation Dashboard
- Row of compact KPI tiles (Best Correctness, Best Faithfulness, Best Recall, Fastest, Lowest Cost, # Evaluated) separated by hairlines, not individual card shadows
- Comparison table: architectures × metrics, each numeric cell with a subtle in-cell bar scaled to that column, best-in-column marked with a small teal dot, unavailable metrics shown as em-dash — **never fabricated**
- Radar chart comparing all 5 architectures across normalized metrics, near-monochrome with only the active/selected architecture highlighted in teal
- Collapsible experiment-metadata strip: git commit, corpus version, dataset version, model, embedding model — monospace tags in one row

### 7.8 Paper Reader
Split view: PDF + page thumbnails (left), tabbed panel — Summary / Extracted Text / Chunks / Used In (right). Summary tab: abstract, numbered key contributions each tagged with a page reference, quiet "Regenerate" icon-button (not a prominent CTA).

### 7.9 Corpus Insights
2-column card grid: Common Themes (frequency-sized tag cloud, teal shades only), Method/Dataset Comparison tables, Limitations grouped by paper, and a horizontal Research Timeline (dots by publish date, hover tooltip). Every card ends with a footer citing which papers backed the insight, expandable to source chunks.

---

## 8. Five RAG Architectures

All five operate on the same corpus version and share one interface (`retrieve` → `generate` → `run`), returning a uniform result object (answer, chunks, paper IDs, page/section, scores, architecture name, model, latency, tokens, trace ID, eval metadata).

| Architecture | Purpose | Key mechanism |
|---|---|---|
| **Hybrid RAG** | Strong baseline | Dense + BM25, rank fusion (RRF), optional reranking |
| **Hierarchical RAG** | Long-document quality | Parent-child chunking, summary → detail retrieval |
| **GraphRAG** | Multi-hop / relational questions | Entity & relationship extraction into a knowledge graph, source-chunk linkage |
| **Agentic / Corrective RAG** | Adaptive quality control | Retrieval grading, query rewrite/decomposition, bounded iteration, traceable state machine |
| **Adaptive RAG** | Cost/latency-aware routing | Query-difficulty classification routes to fast / hybrid / deep retrieval; routing decision is itself traced and shown to the user |

The Architecture Selector (§7.5) and Evaluation Dashboard (§7.7) are the primary surfaces where these five are made comparable and legible to the user — this is the product's core differentiator, so both screens get priority polish.

---

## 9. LangSmith Evaluation (Core Feature)

- Full tracing per request: query preprocessing → architecture selection/routing → retrieval (dense/sparse/graph/rerank) → context assembly → prompt construction → generation → citation extraction → evaluation
- Agentic/Adaptive pipelines additionally trace routing decisions, retrieval attempts, rewrites, grader outputs, stop conditions, fallbacks
- Evaluation datasets versioned; examples include question, corpus ID, expected answer (if available), relevant paper/chunk IDs, difficulty, question type
- Metrics: retrieval (context precision/recall, Recall@K, MRR, NDCG), generation (faithfulness, relevance, correctness, citation correctness/completeness, unsupported-claim rate), system (latency breakdown, tokens, cost, iteration count, failure rate)
- Every architecture evaluated on identical corpus, questions, model, embedding model, and top-K budget unless a variation is explicitly being studied; non-comparable experiments are clearly labeled in the UI
- User feedback (Helpful/Not helpful/Correct/Incorrect/Missing evidence/Incorrect citation) links back to the LangSmith trace

---

## 10. Functional Requirements (unchanged from base PRD, referenced here for completeness)

FR-001 Search ArXiv · FR-002 Multi-select papers · FR-003 Persist corpus · FR-004 Async processing · FR-005 Processing status tracking · FR-006 Preserve evidence metadata end-to-end · FR-007 Multi-paper chat · FR-008 Architecture selection · FR-009 Shared corpus fairness across architectures · FR-010 LangSmith tracing · FR-011 Evaluation dataset versioning · FR-012 Experiment comparison · FR-013 Citation display & inspection · FR-014 Feedback capture · FR-015 Export

---

## 11. UI Iteration Log

Tracking design review rounds against actual Stitch output keeps the design and product spec unified rather than drifting apart.

### Round 1 findings (initial workspace screen)
| Issue | Status |
|---|---|
| Flat visual hierarchy — everything same teal/weight | **Open** — enforce §6 three-tier rule across all screens |
| Metadata strip above chat delays the answer | **Fixed** in round 2 (now a slim per-message line) |
| Evidence Inspector content clipped, no scroll indicator | **Partially fixed** — needs explicit scroll QA on long evidence sets |
| Strategy selector split between header and chat input | **Fixed** in round 2 — consolidated into one config row |
| Amber tags on paper list ambiguous (status vs. descriptive) | **Open** — standardize amber for warning/processing states only |
| Top bar overloaded (title + config + actions in one row) | **Fixed** in round 2 — split into two rows |
| Breadcrumb read as flat tabs, not sequential | **Fixed** in round 2 — true stepper with checkmarks |
| Citation chips blend into general teal UI | **Open** — needs a distinct treatment (see §7.6) |

### Outstanding for Round 3
1. Apply the three-tier hierarchy rule (§6) explicitly to the left paper-library panel and Evaluation Dashboard KPI row.
2. Give inline citation chips their own visual identity, separate from buttons/active-states.
3. Resolve amber-tag ambiguity on paper cards — reserve amber strictly for processing/warning.
4. QA Evidence Inspector scroll behavior with a corpus returning >5 evidence chunks.
5. Extend the confirmed stepper pattern to Corpus Insights as a fifth step, if it remains part of the primary flow.

---

## 12. Acceptance Criteria (MVP)

- User can search ArXiv, select ≥5 papers, and create a named corpus
- Corpus processes asynchronously with visible, recoverable per-paper status
- User can chat with the entire corpus and see page/chunk-level citations
- User can switch among all five architectures through one shared interface, with config (strategy, Top-K, reranker) visible in one consolidated location
- Every UI element correctly maps to primary/secondary/tertiary hierarchy (§6) — no metadata competing visually with the answer
- Evidence Inspector is fully navigable regardless of evidence-set length
- LangSmith records a full trace per run, inspectable from the UI
- Evaluation dashboard compares all five architectures on identical inputs; unavailable metrics show as unavailable, never fabricated
- Citation chips are visually distinguishable from all other interactive/teal elements

---

## 13. Success Metrics

**Product:** corpus completion rate, avg. papers/corpus, chat questions/corpus, evidence click-through rate, feedback score
**Engineering:** retrieval vs. end-to-end latency, processing throughput, failed-job rate, test coverage
**Research:** faithfulness, correctness, retrieval recall, citation correctness, cost/token efficiency per architecture
**Design:** time-to-first-answer (does the consolidated config/slim metadata actually reduce friction), citation click rate (does the new chip treatment increase evidence inspection)

---

## 14. Positioning

> **Search → Build corpus → Research → Chat → Compare RAG architectures → Evaluate → Improve.**

ArXiv RAG Research Lab is a multi-paper research workspace that turns ArXiv searches into interactive, evidence-backed research corpora, and lets users compare five RAG architectures through LangSmith-powered evaluation — presented through a dark, technical, information-dense UI that treats retrieval transparency as a first-class design principle, not an afterthought.




<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>ArXiv RAG Lab - Research Workspace</title>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<style>
    @layer base {
      html, body {
        margin: 0;
        padding: 0;
        background-color: #0B0E14;
        color: #dee2f1;
        font-family: 'Inter', sans-serif;
      }
      body { overscroll-behavior: none; }
    }
    /* Custom sleek research scrollbar */
    .custom-scroll::-webkit-scrollbar {
      width: 5px;
      height: 5px;
    }
    .custom-scroll::-webkit-scrollbar-track {
      background: transparent;
    }
    .custom-scroll::-webkit-scrollbar-thumb {
      background: #252d3d;
      border-radius: 9999px;
    }
    .custom-scroll::-webkit-scrollbar-thumb:hover {
      background: #3c4a60;
    }
    /* Citation chip glow pulse on hover */
    .citation-btn {
      box-shadow: 0 0 0 1px rgba(60, 221, 199, 0.25), 0 2px 4px rgba(0,0,0,0.4);
    }
    .citation-btn:hover {
      box-shadow: 0 0 12px rgba(60, 221, 199, 0.45), 0 0 0 1px rgba(60, 221, 199, 0.8);
    }
  </style>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script id="tailwind-config">
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          colors: {
            "background": "#0B0E14",
            "surface": "#0E131D",
            "surface-container-lowest": "#080B10",
            "surface-container-low": "#121722",
            "surface-container": "#171C28",
            "surface-container-high": "#1E2535",
            "surface-container-highest": "#283042",
            "surface-bright": "#323C50",
            "primary": "#3CDDC7",
            "primary-container": "#143D37",
            "on-primary": "#00201C",
            "secondary": "#F9BC45",
            "secondary-container": "#3F2E05",
            "outline": "#4B5568",
            "outline-variant": "#232B3A",
            "on-surface": "#F1F5F9",
            "on-surface-variant": "#94A3B8",
            "tertiary-muted": "#64748B",
            "error": "#FFB4AB"
          },
          fontFamily: {
            "sans": ["Inter", "sans-serif"],
            "mono": ["JetBrains Mono", "monospace"]
          }
        }
      }
    };
  </script>
</head>
<body class="bg-[#0B0E14] font-sans text-on-surface antialiased selection:bg-primary selection:text-on-primary flex flex-col h-screen overflow-hidden">
<!-- ========================================================================= -->
<!-- ROW 1: Identity & Workflow Stepper & Telemetry Status (52px)               -->
<!-- ========================================================================= -->
<header class="h-[52px] w-full bg-[#080B10] border-b border-outline-variant/80 px-4 flex items-center justify-between gap-4 shrink-0 z-40">
<!-- Left: App Identity & Version -->
<div class="flex items-center gap-3 shrink-0">
<div class="flex items-center gap-2">
<div class="w-7 h-7 rounded-lg bg-surface-container-high border border-outline-variant flex items-center justify-center text-primary shadow-sm shadow-primary/10">
<span class="material-symbols-outlined text-[17px]">biotech</span>
</div>
<div class="flex items-baseline gap-1.5">
<span class="font-semibold text-sm tracking-tight text-white">ArXiv RAG Lab</span>
<span class="font-mono text-[10px] text-tertiary-muted border border-outline-variant/60 bg-surface-container-low px-1.5 py-0.2 rounded font-medium">v1.4</span>
</div>
</div>
<div class="h-4 w-[1px] bg-outline-variant mx-1 hidden sm:block"></div>
<!-- Quick Benchmark Dropdown / Scope Badge -->
<button class="hidden lg:flex items-center gap-1.5 bg-surface-container-low border border-outline-variant/70 hover:border-outline px-2.5 py-1 rounded-md text-left transition-colors" type="button">
<span class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
<span class="font-mono text-xs text-slate-300">Transformer Hallucination Benchmark</span>
<span class="font-mono text-[11px] text-tertiary-muted">· 12 papers</span>
<span class="material-symbols-outlined text-tertiary-muted text-[15px]">arrow_drop_down</span>
</button>
</div>
<!-- Center: Guided Workflow Stepper (7. Redesigned Breadcrumbs) -->
<nav aria-label="Research Workflow Steps" class="hidden xl:flex items-center">
<ol class="flex items-center">
<!-- Step 1: Discover Papers (Completed) -->
<li class="flex items-center">
<a class="group flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors" href="#">
<span class="w-5 h-5 rounded-full bg-primary/15 border border-primary/40 flex items-center justify-center text-primary text-[12px] group-hover:bg-primary/25">
<span class="material-symbols-outlined text-[13px] font-bold">check</span>
</span>
<span>Discover Papers</span>
</a>
<!-- Hairline connector -->
<div class="w-8 h-[1px] bg-primary/40 mx-2.5"></div>
</li>
<!-- Step 2: Research Workspace (Active Node) -->
<li class="flex items-center">
<a aria-current="step" class="flex items-center gap-2 px-2.5 py-1 rounded-full bg-surface-container-high border border-primary/50 text-xs font-semibold text-primary shadow-sm shadow-primary/20" href="#">
<span class="w-4 h-4 rounded-full bg-primary text-[#00201C] flex items-center justify-center text-[10px] font-mono font-bold">2</span>
<span>Research Workspace</span>
</a>
<!-- Hairline connector -->
<div class="w-8 h-[1px] bg-outline-variant mx-2.5"></div>
</li>
<!-- Step 3: Architecture Comparison (Upcoming) -->
<li class="flex items-center">
<a class="group flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors" href="#">
<span class="w-4 h-4 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center text-[10px] font-mono text-tertiary-muted group-hover:border-slate-500">3</span>
<span>Architecture Comparison</span>
</a>
<div class="w-8 h-[1px] bg-outline-variant mx-2.5"></div>
</li>
<!-- Step 4: Evaluation Dashboard (Upcoming) -->
<li class="flex items-center">
<a class="group flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors" href="#">
<span class="w-4 h-4 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center text-[10px] font-mono text-tertiary-muted group-hover:border-slate-500">4</span>
<span>Evaluation</span>
</a>
<div class="w-8 h-[1px] bg-outline-variant mx-2.5"></div>
</li>
<!-- Step 5: Corpus Insights (Upcoming) -->
<li class="flex items-center">
<a class="group flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors" href="#">
<span class="w-4 h-4 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center text-[10px] font-mono text-tertiary-muted group-hover:border-slate-500">5</span>
<span>Corpus Insights</span>
</a>
</li>
</ol>
</nav>
<!-- Right: LangSmith Status & Profile -->
<div class="flex items-center gap-2.5 shrink-0">
<!-- Muted telemetry pill (Tier 3) -->
<div class="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-container-low border border-outline-variant/70 text-tertiary-muted font-mono text-[11px]">
<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
<span class="text-slate-300">LangSmith</span>
<span>·</span>
<span>142 traces</span>
</div>
<button class="w-8 h-8 rounded-lg border border-outline-variant/70 bg-surface-container-low hover:bg-surface-container flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors" title="Workspace Settings" type="button">
<span class="material-symbols-outlined text-[17px]">tune</span>
</button>
<div class="w-8 h-8 rounded-full bg-gradient-to-tr from-[#143D37] to-primary/80 border border-primary/40 flex items-center justify-center shrink-0 cursor-pointer shadow-sm">
<span class="font-mono text-xs font-semibold text-white">AR</span>
</div>
</div>
</header>
<!-- ========================================================================= -->
<!-- ROW 2: Corpus Identity & Unified Run Configuration Bar (48px)             -->
<!-- ========================================================================= -->
<div class="h-12 w-full bg-[#0E131D] border-b border-outline-variant px-4 flex items-center justify-between gap-4 shrink-0 z-30 select-none">
<!-- Left: Corpus Title + Status pill + Add Papers -->
<div class="flex items-center gap-3 min-w-0">
<div class="flex items-center gap-2 text-primary shrink-0">
<span class="material-symbols-outlined text-[18px]">folder_special</span>
</div>
<!-- Editable Corpus Title -->
<div class="flex items-center gap-1.5 min-w-0">
<div class="group flex items-center gap-1.5 cursor-pointer hover:bg-surface-container-high px-2 py-1 rounded transition-colors" id="corpus-title-display" title="Click to rename corpus">
<span class="text-sm font-semibold text-white truncate max-w-xs md:max-w-md" id="corpus-title-text">
            Retrieval Augmented Generation in Long-Context Reasoning
          </span>
<span class="material-symbols-outlined text-tertiary-muted text-[15px] opacity-0 group-hover:opacity-100 transition-opacity">edit</span>
</div>
<input class="hidden text-sm font-semibold text-white bg-surface-container border border-primary px-2 py-0.5 rounded outline-none w-80 font-sans" id="corpus-title-input" type="text" value="Retrieval Augmented Generation in Long-Context Reasoning"/>
</div>
<!-- Corpus Status Pill -->
<div class="hidden sm:flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-surface-container-high border border-outline-variant/70 shrink-0 font-mono text-[11px] text-tertiary-muted">
<span class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
<span class="text-slate-300 font-medium">Indexed</span>
<span>·</span>
<span>12 papers</span>
<span>·</span>
<span>340 chunks</span>
</div>
<!-- Add Papers Action -->
<button class="flex items-center gap-1 px-2.5 py-1 rounded-md bg-surface-container-high hover:bg-surface-bright border border-outline-variant/80 text-slate-200 text-xs font-medium transition-colors shrink-0" type="button">
<span class="material-symbols-outlined text-[15px] text-primary">add</span>
<span>Add Papers</span>
</button>
<!-- Corpus Overflow Options -->
<div class="relative">
<button class="w-7 h-7 rounded border border-outline-variant/60 hover:bg-surface-container flex items-center justify-center text-tertiary-muted hover:text-slate-200 transition-colors" id="corpus-overflow-btn" type="button">
<span class="material-symbols-outlined text-[16px]">more_vert</span>
</button>
<div class="hidden absolute left-0 mt-1 w-44 bg-surface-container-high border border-outline-variant rounded-lg shadow-2xl py-1 z-50 text-xs font-sans text-slate-300" id="corpus-overflow-dropdown">
<button class="w-full text-left px-3 py-1.5 hover:bg-surface-container flex items-center gap-2" id="action-rename">
<span class="material-symbols-outlined text-[14px] text-tertiary-muted">edit</span>
            Rename Corpus
          </button>
<button class="w-full text-left px-3 py-1.5 hover:bg-surface-container flex items-center gap-2">
<span class="material-symbols-outlined text-[14px] text-tertiary-muted">file_download</span>
            Export Indices (.json)
          </button>
<button class="w-full text-left px-3 py-1.5 hover:bg-surface-container flex items-center gap-2 text-error">
<span class="material-symbols-outlined text-[14px]">delete_forever</span>
            Delete Corpus
          </button>
</div>
</div>
</div>
<!-- Right/Integrated: Unified Architecture Selector Tabs + Run Config (Point 4 & 6) -->
<div class="flex items-center gap-3 shrink-0">
<!-- Strategy Selector Pill Bar -->
<div class="flex items-center bg-surface-container-lowest p-0.5 rounded-lg border border-outline-variant/80">
<span class="text-[10px] font-mono uppercase tracking-wider text-tertiary-muted px-2 font-medium hidden md:inline">Strategy:</span>
<button class="arch-toggle-btn active flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-all bg-primary/15 text-primary border border-primary/40 font-semibold" data-strategy="Hybrid" type="button">
<span class="material-symbols-outlined text-[14px]">tune</span>
<span>Hybrid</span>
</button>
<button class="arch-toggle-btn flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-slate-400 hover:text-slate-200 border border-transparent transition-all" data-strategy="Hierarchical" type="button">
<span class="material-symbols-outlined text-[14px]">account_tree</span>
<span>Hierarchical</span>
</button>
<button class="arch-toggle-btn hidden sm:flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-slate-400 hover:text-slate-200 border border-transparent transition-all" data-strategy="GraphRAG" type="button">
<span class="material-symbols-outlined text-[14px]">hub</span>
<span>GraphRAG</span>
</button>
<button class="arch-toggle-btn hidden md:flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-slate-400 hover:text-slate-200 border border-transparent transition-all" data-strategy="Agentic" type="button">
<span class="material-symbols-outlined text-[14px]">smart_toy</span>
<span>Agentic</span>
</button>
<button class="arch-toggle-btn hidden lg:flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-slate-400 hover:text-slate-200 border border-transparent transition-all" data-strategy="Adaptive" type="button">
<span class="material-symbols-outlined text-[14px]">alt_route</span>
<span>Adaptive</span>
</button>
</div>
<!-- Compact Parameters (Top-K & Reranker) -->
<div class="hidden xl:flex items-center gap-2 font-mono text-[11px] text-tertiary-muted bg-surface-container-low px-2.5 py-1 rounded-md border border-outline-variant/70">
<span class="flex items-center gap-1">
<span class="text-slate-400">Top-K:</span>
<span class="text-slate-200 font-medium">8</span>
</span>
<span class="text-outline-variant">|</span>
<span class="flex items-center gap-1">
<span class="text-slate-400">Reranker:</span>
<span class="text-slate-200 font-medium">Cohere-v3</span>
</span>
</div>
</div>
</div>
<!-- ========================================================================= -->
<!-- MAIN THREE-PANE WORKSPACE                                                 -->
<!-- ========================================================================= -->
<div class="flex-1 flex flex-col lg:flex-row min-h-0 overflow-hidden bg-[#0B0E14]" id="workspace-container">
<!-- --------------------------------------------------------------------- -->
<!-- LEFT PANEL: Paper Library (Clean Consistent Tagging)                  -->
<!-- --------------------------------------------------------------------- -->
<aside class="w-full lg:w-[280px] xl:w-[310px] shrink-0 flex flex-col bg-[#090D15] border-b lg:border-b-0 lg:border-r border-outline-variant h-full select-text" id="panel-left">
<!-- Search & Filter Header -->
<div class="p-3 border-b border-outline-variant bg-[#090D15] sticky top-0 z-10 space-y-2">
<div class="flex items-center justify-between">
<span class="font-mono text-[11px] font-semibold uppercase text-tertiary-muted tracking-wider flex items-center gap-1.5">
<span class="material-symbols-outlined text-[14px]">library_books</span>
            Indexed Corpus
          </span>
<span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant/60 text-slate-300 font-medium">12 papers</span>
</div>
<div class="relative w-full">
<span class="material-symbols-outlined absolute left-2.5 top-2 text-tertiary-muted text-[15px]">search</span>
<input class="w-full h-7 bg-surface-container-low border border-outline-variant/80 rounded-md pl-8 pr-2.5 font-sans text-xs text-slate-200 placeholder:text-tertiary-muted focus:border-primary focus:outline-none transition-colors" id="paper-filter-input" placeholder="Filter by title, arXiv ID..." type="text"/>
</div>
</div>
<!-- Paper Rows List (Consistent Tier 1 / 3 tags - No random amber for completed) -->
<div class="flex-1 overflow-y-auto custom-scroll divide-y divide-outline-variant/40" id="papers-list">
<!-- Paper 1 (Selected & Active) -->
<div class="paper-item group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer bg-surface-container-high/60 border-l-[3px] border-l-primary" data-paper-id="2307.03172">
<div class="flex-1 p-2.5 pl-3 min-w-0">
<h4 class="text-xs font-semibold text-white leading-snug group-hover:text-primary transition-colors line-clamp-2">
              Lost in the Middle: How Language Models Use Long Contexts
            </h4>
<div class="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-tertiary-muted">
<span class="text-slate-400">arXiv:2307.03172</span>
<span>·</span>
<span>14p · 28 chunks</span>
</div>
</div>
<div class="flex items-center pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" title="Paper Options" type="button">
<span class="material-symbols-outlined text-[15px]">more_vert</span>
</button>
</div>
</div>
<!-- Paper 2 (Completed) -->
<div class="paper-item group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer border-l-[3px] border-l-transparent" data-paper-id="2310.03025">
<div class="flex-1 p-2.5 pl-3 min-w-0">
<h4 class="text-xs font-semibold text-slate-200 leading-snug group-hover:text-white transition-colors line-clamp-2">
              RAG vs Long-Context LLMs: A Benchmark Study
            </h4>
<div class="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-tertiary-muted">
<span class="text-slate-400">arXiv:2310.03025</span>
<span>·</span>
<span>22p · 46 chunks</span>
</div>
</div>
<div class="flex items-center pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" type="button">
<span class="material-symbols-outlined text-[15px]">more_vert</span>
</button>
</div>
</div>
<!-- Paper 3 (In-Progress Operation: Genuine Amber tag) -->
<div class="paper-item group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer border-l-[3px] border-l-secondary" data-paper-id="2401.15884">
<div class="flex-1 p-2.5 pl-3 min-w-0">
<h4 class="text-xs font-semibold text-slate-200 leading-snug group-hover:text-secondary transition-colors line-clamp-2">
              Corrective Retrieval Augmented Generation (CRAG)
            </h4>
<div class="mt-1.5 flex items-center gap-1.5 font-mono text-[11px]">
<span class="inline-block w-1.5 h-1.5 rounded-full bg-secondary animate-ping mr-0.5"></span>
<span class="text-secondary font-medium">Embedding HNSW</span>
<span class="text-tertiary-muted">·</span>
<span class="text-tertiary-muted">18p · 36 chunks</span>
</div>
</div>
<div class="flex items-center pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" type="button">
<span class="material-symbols-outlined text-[15px]">more_vert</span>
</button>
</div>
</div>
<!-- Paper 4 (Completed) -->
<div class="paper-item group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer border-l-[3px] border-l-transparent" data-paper-id="2004.04906">
<div class="flex-1 p-2.5 pl-3 min-w-0">
<h4 class="text-xs font-semibold text-slate-200 leading-snug group-hover:text-white transition-colors line-clamp-2">
              Dense Passage Retrieval for Open-Domain QA
            </h4>
<div class="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-tertiary-muted">
<span class="text-slate-400">arXiv:2004.04906</span>
<span>·</span>
<span>11p · 31 chunks</span>
</div>
</div>
<div class="flex items-center pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" type="button">
<span class="material-symbols-outlined text-[15px]">more_vert</span>
</button>
</div>
</div>
<!-- Paper 5 (Completed) -->
<div class="paper-item group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer border-l-[3px] border-l-transparent" data-paper-id="2312.10997">
<div class="flex-1 p-2.5 pl-3 min-w-0">
<h4 class="text-xs font-semibold text-slate-200 leading-snug group-hover:text-white transition-colors line-clamp-2">
              Retrieval-Augmented Generation for Large Language Models: A Survey
            </h4>
<div class="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-tertiary-muted">
<span class="text-slate-400">arXiv:2312.10997</span>
<span>·</span>
<span>27p · 62 chunks</span>
</div>
</div>
<div class="flex items-center pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" type="button">
<span class="material-symbols-outlined text-[15px]">more_vert</span>
</button>
</div>
</div>
<!-- Paper 6 (Completed) -->
<div class="paper-item group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer border-l-[3px] border-l-transparent" data-paper-id="2305.14283">
<div class="flex-1 p-2.5 pl-3 min-w-0">
<h4 class="text-xs font-semibold text-slate-200 leading-snug group-hover:text-white transition-colors line-clamp-2">
              Active Retrieval Augmented Generation (FLARE)
            </h4>
<div class="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-tertiary-muted">
<span class="text-slate-400">arXiv:2305.14283</span>
<span>·</span>
<span>13p · 24 chunks</span>
</div>
</div>
<div class="flex items-center pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" type="button">
<span class="material-symbols-outlined text-[15px]">more_vert</span>
</button>
</div>
</div>
<!-- Paper 7 (In-Progress Operation: Genuine Amber tag) -->
<div class="paper-item group relative flex items-stretch hover:bg-surface-container/80 transition-colors cursor-pointer border-l-[3px] border-l-secondary" data-paper-id="2402.03367">
<div class="flex-1 p-2.5 pl-3 min-w-0">
<h4 class="text-xs font-semibold text-slate-200 leading-snug group-hover:text-secondary transition-colors line-clamp-2">
              Self-RAG: Learning to Retrieve, Generate, and Critique
            </h4>
<div class="mt-1.5 flex items-center gap-1.5 font-mono text-[11px]">
<span class="inline-block w-1.5 h-1.5 rounded-full bg-secondary animate-ping mr-0.5"></span>
<span class="text-secondary font-medium">Parsing AST</span>
<span class="text-tertiary-muted">·</span>
<span class="text-tertiary-muted">19p · 41 chunks</span>
</div>
</div>
<div class="flex items-center pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" type="button">
<span class="material-symbols-outlined text-[15px]">more_vert</span>
</button>
</div>
</div>
</div>
<!-- Bottom Library Diagnostic Indicator -->
<div class="p-2 bg-[#080B10] border-t border-outline-variant/80 flex items-center justify-between text-tertiary-muted font-mono text-[11px]">
<span class="flex items-center gap-1.5">
<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
<span>Index Cache: warm</span>
</span>
<button class="hover:text-primary transition-colors flex items-center gap-1 text-[11px]" type="button">
<span class="material-symbols-outlined text-[13px]">refresh</span>
          Re-index
        </button>
</div>
</aside>
<!-- Resizer Divider 1 -->
<div class="hidden lg:flex w-1 bg-[#0E131D] hover:bg-primary cursor-col-resize items-center justify-center transition-colors group z-20" id="resizer-left">
<div class="w-0.5 h-8 bg-outline-variant group-hover:bg-primary rounded"></div>
</div>
<!-- --------------------------------------------------------------------- -->
<!-- CENTER PANEL: Chat Workspace (Front & Center, Generous Leading)       -->
<!-- --------------------------------------------------------------------- -->
<main class="flex-1 flex flex-col h-full bg-[#0B0E14] min-w-0 relative select-text" id="panel-center">
<!-- Chat Stream Scroller (Point 2: Removed intrusive banner, conversational focus) -->
<div class="flex-1 overflow-y-auto custom-scroll px-6 py-5 space-y-6" id="chat-thread">
<!-- Message 1: User Question (Tier 1: Crisp #F1F5F9 text, clear hierarchy) -->
<div class="w-full flex justify-end">
<div class="max-w-2xl bg-[#141B26] border border-outline-variant/90 rounded-2xl p-4 text-on-surface shadow-md">
<div class="font-mono text-[10px] text-tertiary-muted mb-1.5 flex items-center justify-between tracking-wide uppercase">
<span>RESEARCHER QUERY</span>
<span>11:42:08 AM</span>
</div>
<p class="text-sm md:text-[15px] font-normal text-white leading-relaxed">
              How do Hybrid RAG and Hierarchical RAG handle positional bias when retrieving from 30+ page papers?
            </p>
</div>
</div>
<!-- Message 2: Assistant Response (Generous leading, high contrast white text) -->
<div class="w-full max-w-3xl flex flex-col space-y-3">
<!-- Assistant Metatag with Inline Expandable Run Context (Point 2) -->
<div class="flex flex-wrap items-center gap-2 font-mono text-[11px] text-tertiary-muted">
<span class="w-2 h-2 rounded-full bg-primary shrink-0"></span>
<span class="font-medium text-slate-300">claude-3.5-sonnet</span>
<span>·</span>
<span>618ms</span>
<span>·</span>
<span>894 tokens</span>
<!-- Sleek Inline Expandable Context Chip -->
<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-high border border-outline-variant hover:border-slate-500 text-slate-300 hover:text-white transition-colors cursor-pointer ml-1" id="toggle-run-context-btn" title="View retrieval execution telemetry">
<span class="material-symbols-outlined text-[13px] text-primary">bolt</span>
<span>Trace #tr-8849-01c</span>
<span class="material-symbols-outlined text-[13px] text-tertiary-muted transition-transform" id="run-context-icon">arrow_drop_down</span>
</button>
</div>
<!-- Collapsed Run Context Drawer -->
<div class="hidden p-3 rounded-lg bg-surface-container-low border border-outline-variant text-[11px] font-mono text-tertiary-muted space-y-1.5 transition-all" id="run-context-drawer">
<div class="flex flex-wrap items-center gap-4 text-slate-300">
<span><span class="text-tertiary-muted">Embeddings:</span> text-embedding-3-large (3072d)</span>
<span><span class="text-tertiary-muted">Sparse:</span> BM25s (k1=1.5, b=0.75)</span>
<span><span class="text-tertiary-muted">Fusion:</span> RRF (c=60)</span>
<span><span class="text-tertiary-muted">Depth:</span> 40-60% span filter</span>
</div>
</div>
<!-- Assistant Body Text (Crisp #F1F5F9, high readability, generous leading) -->
<div class="text-[#F1F5F9] text-[15px] leading-[1.75] space-y-3.5">
<p>
              When dealing with long scientific documents exceeding 30 pages, standard dense vector embeddings suffer heavily from the <strong class="text-white font-semibold">"lost-in-the-middle"</strong> phenomenon, where information positioned deep in the interior of long contexts exhibits significantly depressed retrieval and attention scores
              <!-- Interactive Citation Chip [1] (Point 1 & Point 8: Distinctive interactive pill badge) -->
<button class="citation-btn inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-semibold text-primary bg-[#102D29] border border-primary/60 hover:bg-[#16433E] hover:text-white transition-all cursor-pointer align-baseline ml-1" data-evidence="lost-in-middle-chunk" title="Inspect citation [1] from arXiv:2307.03172">
<span class="material-symbols-outlined text-[13px]">format_quote</span>
<span>[1]</span>
</button>.
            </p>
<p>
              The structural degradation differs markedly between <strong class="text-white font-semibold">Hybrid RAG</strong> and <strong class="text-white font-semibold">Hierarchical RAG</strong>:
            </p>
<div class="space-y-3 my-2.5 pl-3 border-l-2 border-outline-variant/60">
<div class="flex items-start gap-2.5">
<span class="material-symbols-outlined text-primary text-[17px] mt-0.5 shrink-0">check_circle</span>
<div>
<strong class="text-white font-medium">Hybrid RAG (Dense + BM25s with RRF):</strong> Mitigates positional decay by pairing cosine distance over dense embeddings with exact token inverted indexes
                  <!-- Interactive Citation Chip [2] (Point 1 & Point 8) -->
<button class="citation-btn inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-semibold text-primary bg-[#102D29] border border-primary/60 hover:bg-[#16433E] hover:text-white transition-all cursor-pointer align-baseline ml-1" data-evidence="rag-benchmark-chunk" title="Inspect citation [2] from arXiv:2310.03025">
<span class="material-symbols-outlined text-[13px]">format_quote</span>
<span>[2]</span>
</button>.
                  BM25 is position-agnostic regarding document offsets, ensuring dense passages located in middle sections (e.g., Pages 14–26) with distinct technical vocabulary retain high lexical ranks regardless of embedding compression limits.
                </div>
</div>
<div class="flex items-start gap-2.5">
<span class="material-symbols-outlined text-primary text-[17px] mt-0.5 shrink-0">check_circle</span>
<div>
<strong class="text-white font-medium">Hierarchical RAG (Parent-Child AST Chunking):</strong> Circumvents context saturation by indexing small 256-token child chunks for precision match, then retrieving the surrounding 2,048-token parent section at synthesis time. This avoids semantic smearing across distant sections while preventing isolated snippet hallucinations.
                </div>
</div>
</div>
<p>
              Empirical evaluations show that combining reciprocal rank fusion (RRF) with a positional decay penalty offset reduces middle-span miss rates from <span class="font-mono text-xs text-secondary px-1.5 py-0.5 rounded bg-surface-container border border-secondary/30">41.8%</span> to under <span class="font-mono text-xs text-primary px-1.5 py-0.5 rounded bg-surface-container border border-primary/30">9.2%</span> on multi-hop benchmarks.
            </p>
</div>
<!-- Bottom Action Buttons for Message -->
<div class="flex items-center gap-4 pt-1 font-mono text-[11px] text-tertiary-muted">
<button class="flex items-center gap-1 hover:text-slate-200 transition-colors" type="button">
<span class="material-symbols-outlined text-[14px]">content_copy</span>
<span>Copy</span>
</button>
<button class="flex items-center gap-1 hover:text-slate-200 transition-colors" type="button">
<span class="material-symbols-outlined text-[14px]">terminal</span>
<span>Inspect DAG</span>
</button>
<button class="flex items-center gap-1 hover:text-slate-200 transition-colors" type="button">
<span class="material-symbols-outlined text-[14px]">sync_alt</span>
<span>Compare Dense</span>
</button>
</div>
</div>
</div>
<!-- Chat Bottom Input Area (Point 4: Clean, focused, distraction-free) -->
<div class="p-4 bg-[#080B10] border-t border-outline-variant shrink-0">
<div class="relative flex items-end gap-2 bg-[#121722] rounded-xl border border-outline-variant hover:border-slate-500 focus-within:border-primary focus-within:shadow-[0_0_0_1px_#3cddc7] transition-all p-2.5">
<!-- Scope Selector Chip -->
<div class="relative shrink-0 mb-0.5">
<button class="flex items-center gap-1 px-2.5 py-1 rounded-md bg-surface-container border border-outline-variant hover:border-primary text-slate-200 font-mono text-xs transition-colors" id="scope-selector-btn" type="button">
<span class="material-symbols-outlined text-[14px] text-primary">filter_center_focus</span>
<span id="current-scope-label">Entire corpus</span>
<span class="material-symbols-outlined text-[14px] text-tertiary-muted">arrow_drop_down</span>
</button>
<!-- Scope Popover -->
<div class="hidden absolute left-0 bottom-full mb-2 w-44 bg-surface-container-high border border-outline-variant rounded-lg shadow-xl py-1 z-50 text-xs font-sans text-slate-200" id="scope-popover">
<button class="scope-option w-full text-left px-3 py-1.5 hover:bg-surface-container flex items-center justify-between text-primary font-medium" data-scope="Entire corpus">
<span>Entire corpus</span>
<span class="material-symbols-outlined text-[14px]">check</span>
</button>
<button class="scope-option w-full text-left px-3 py-1.5 hover:bg-surface-container flex items-center justify-between text-slate-300" data-scope="This paper">
<span>This paper</span>
</button>
<button class="scope-option w-full text-left px-3 py-1.5 hover:bg-surface-container flex items-center justify-between text-slate-300" data-scope="Compare all">
<span>Compare all</span>
</button>
</div>
</div>
<!-- Multiline Textarea -->
<textarea class="flex-1 max-h-32 bg-transparent border-0 resize-none outline-none text-sm text-white placeholder:text-tertiary-muted py-1 px-1.5 leading-normal font-sans" id="chat-input-textarea" placeholder="Query literature corpus (e.g. 'Compare MQA vs GQA retrieval latency in RAG pipelines')..." rows="1"></textarea>
<!-- Action Buttons inside input -->
<div class="flex items-center gap-1.5 shrink-0 mb-0.5">
<button class="w-8 h-8 rounded-lg hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200 transition-colors" title="Attach excerpt or equation" type="button">
<span class="material-symbols-outlined text-[18px]">attachment</span>
</button>
<!-- Send Button -->
<button class="w-8 h-8 rounded-lg bg-primary hover:bg-[#34c4b0] text-[#00201C] flex items-center justify-center font-bold transition-all shadow-md active:scale-95" id="send-query-btn" title="Run Retrieval" type="button">
<span class="material-symbols-outlined text-[18px]">arrow_upward</span>
</button>
</div>
</div>
</div>
</main>
<!-- Resizer Divider 2 -->
<div class="hidden lg:flex w-1 bg-[#0E131D] hover:bg-primary cursor-col-resize items-center justify-center transition-colors group z-20" id="resizer-right">
<div class="w-0.5 h-8 bg-outline-variant group-hover:bg-primary rounded"></div>
</div>
<!-- --------------------------------------------------------------------- -->
<!-- RIGHT PANEL: Evidence Inspector (Point 3: Fully scrollable, unclipped) -->
<!-- --------------------------------------------------------------------- -->
<aside class="w-full lg:w-[320px] xl:w-[360px] shrink-0 flex flex-col bg-[#090D15] border-t lg:border-t-0 lg:border-l border-outline-variant h-full select-text transition-all duration-200" id="panel-right">
<!-- Panel Header -->
<div class="h-11 px-3.5 border-b border-outline-variant flex items-center justify-between bg-[#090D15] shrink-0">
<div class="flex items-center gap-1.5">
<span class="material-symbols-outlined text-primary text-[17px]">find_in_page</span>
<span class="font-mono text-xs font-semibold text-slate-200 uppercase tracking-wider">Evidence Inspector</span>
</div>
<div class="flex items-center gap-1">
<button class="w-6 h-6 rounded hover:bg-surface-bright flex items-center justify-center text-tertiary-muted hover:text-slate-200" id="close-inspector-btn" title="Collapse Inspector" type="button">
<span class="material-symbols-outlined text-[16px]">chevron_right</span>
</button>
</div>
</div>
<!-- Inspector Scroll Content with Custom Scrollbar and Bottom Padding to prevent ANY clipping -->
<div class="flex-1 overflow-y-auto custom-scroll p-4 space-y-4 pb-12" id="inspector-content">
<!-- Paper Meta Card -->
<div class="p-3 bg-surface-container rounded-xl border border-outline-variant space-y-2">
<h3 class="text-xs font-semibold text-white leading-snug">
            Lost in the Middle: How Language Models Use Long Contexts
          </h3>
<div class="flex items-center justify-between pt-1 font-mono text-[11px]">
<div class="flex items-center gap-1.5 bg-surface-container-low px-2 py-0.5 rounded border border-outline-variant text-tertiary-muted">
<span>ID:</span>
<span class="text-slate-200 font-medium" id="arxiv-id-val">arXiv:2307.03172</span>
<button class="hover:text-primary ml-0.5 text-tertiary-muted" id="copy-arxiv-btn" title="Copy arXiv ID" type="button">
<span class="material-symbols-outlined text-[13px]">content_copy</span>
</button>
</div>
<span class="text-tertiary-muted">v3 · Jul 2023</span>
</div>
<div class="flex items-center gap-1 text-tertiary-muted font-mono text-[11px] pt-0.5">
<span class="material-symbols-outlined text-[14px] text-primary">segment</span>
<span>Page 4</span>
<span class="text-outline-variant">&gt;</span>
<span class="text-slate-300 font-medium">§3.2 Positional Degradation</span>
</div>
</div>
<!-- Retrieved Chunk Detail Block -->
<div class="space-y-1.5">
<div class="flex items-center justify-between font-mono text-[11px] text-tertiary-muted">
<span>RETRIEVED VECTOR CHUNK</span>
<span class="text-primary font-medium">Rank #1</span>
</div>
<!-- Quote Block with 4px Teal Left Border & Matches Highlighting -->
<div class="bg-surface-container-low border-l-[3px] border-l-primary p-3 rounded-r-lg font-mono text-xs leading-relaxed text-slate-300 space-y-2">
<p>
              "...We observe that retrieval performance in modern transformer models degrades significantly when relevant key-value states reside in the interior segments of context windows. Specifically, when documents are positioned in the middle <span class="bg-primary/20 text-primary font-medium px-1 rounded">(depths 40%–60%)</span>, accuracy falls by up to <span class="bg-secondary/20 text-secondary font-medium px-1 rounded">34.2 percentage points</span> compared to prefix placement..."
            </p>
<p class="text-tertiary-muted text-[11px]">
              "...This U-shaped curve persists across foundation models, demonstrating that attention bias requires architectural interventions during multi-stage passage reranking."
            </p>
</div>
</div>
<!-- Relevance Score Telemetry Card -->
<div class="p-3 bg-surface-container rounded-xl border border-outline-variant space-y-2.5">
<div class="flex items-center justify-between font-mono text-xs">
<span class="text-tertiary-muted font-medium">Similarity &amp; Density</span>
<span class="text-primary font-semibold">Combined: 0.941</span>
</div>
<!-- Cosine Sim Score Bar -->
<div class="space-y-1">
<div class="flex justify-between font-mono text-[11px] text-slate-400">
<span>Cosine Similarity</span>
<span class="font-medium text-primary">0.892</span>
</div>
<div class="w-full h-1.5 bg-surface-container-low rounded-full overflow-hidden">
<div class="h-full bg-primary rounded-full" style="width: 89.2%"></div>
</div>
</div>
<!-- BM25 Score Bar -->
<div class="space-y-1">
<div class="flex justify-between font-mono text-[11px] text-slate-400">
<span>BM25s Score</span>
<span class="font-medium text-secondary">14.82</span>
</div>
<div class="w-full h-1.5 bg-surface-container-low rounded-full overflow-hidden">
<div class="h-full bg-secondary rounded-full" style="width: 74%"></div>
</div>
</div>
<!-- Reranker Score Row -->
<div class="pt-2 flex items-center justify-between font-mono text-[11px] text-tertiary-muted border-t border-outline-variant">
<span>Reranker Score</span>
<span class="text-slate-200 font-medium">+0.814 (Cohere)</span>
</div>
</div>
<!-- Context Attention Map SVG -->
<div class="p-3 bg-surface-container rounded-xl border border-outline-variant space-y-2">
<div class="flex items-center justify-between text-tertiary-muted font-mono text-[11px]">
<span>CONTEXT ATTENTION MAP</span>
<span class="text-secondary font-medium">U-CURVE</span>
</div>
<div class="w-full h-16 flex items-center justify-center py-1">
<svg class="w-full h-full text-primary" fill="none" stroke="currentColor" viewbox="0 0 240 60">
<line stroke="#1F2733" stroke-dasharray="2 2" stroke-width="1" x1="0" x2="240" y1="50" y2="50"></line>
<line stroke="#1F2733" stroke-dasharray="2 2" stroke-width="1" x1="0" x2="240" y1="20" y2="20"></line>
<path d="M 10 15 C 60 15, 80 50, 120 50 C 160 50, 180 18, 230 18" fill="none" stroke="#3CDDC7" stroke-linecap="round" stroke-width="2"></path>
<circle cx="120" cy="50" fill="#3CDDC7" r="4"></circle>
</svg>
</div>
<div class="flex items-center justify-between text-tertiary-muted font-mono text-[10px]">
<span>Doc Start (94%)</span>
<span class="text-secondary font-medium">Middle (59%)</span>
<span>Doc End (91%)</span>
</div>
</div>
<!-- PDF External Direct Link Button -->
<div>
<a class="w-full py-2 px-3 rounded-lg bg-surface-container-high border border-outline-variant hover:border-primary text-primary hover:bg-surface-bright flex items-center justify-center gap-2 font-mono text-xs font-semibold transition-all group shadow-sm" href="#">
<span>Open PDF at this page (p. 4)</span>
<span class="material-symbols-outlined text-[15px] group-hover:translate-x-0.5 transition-transform">open_in_new</span>
</a>
</div>
<!-- Token Range & Raw Vector Trigger -->
<div class="p-2.5 bg-surface-container-low border border-outline-variant rounded-lg flex items-center justify-between text-tertiary-muted font-mono text-[11px]">
<span>Tokens: 1842 - 2354</span>
<button class="hover:text-primary text-slate-300 transition-colors flex items-center gap-1" type="button">
<span class="material-symbols-outlined text-[13px]">raw_on</span>
<span>Raw Vector</span>
</button>
</div>
</div>
</aside>
</div>
<!-- ========================================================================= -->
<!-- FOOTER TELEMETRY (32px)                                                   -->
<!-- ========================================================================= -->
<footer class="w-full bg-[#080B10] border-t border-outline-variant/80 py-1.5 px-4 shrink-0 select-none">
<div class="flex flex-col sm:flex-row items-center justify-between gap-1 text-tertiary-muted font-mono text-[10px]">
<div class="flex items-center gap-2">
<span>ArXiv RAG Research Lab</span>
<span>|</span>
<span class="text-emerald-400">Telemetry: Subsystem Nominal</span>
</div>
<div class="flex items-center gap-3">
<span>text-embedding-3-large</span>
<span>·</span>
<span>HNSW + BM25s</span>
<span>·</span>
<span>p95: 142ms</span>
</div>
</div>
</footer>
<!-- ========================================================================= -->
<!-- CLIENT INTERACTIVITY JAVASCRIPT                                           -->
<!-- ========================================================================= -->
<script>
    (function initWorkspace() {
      // 1. Corpus Title Inline Rename
      const titleDisplay = document.getElementById('corpus-title-display');
      const titleInput = document.getElementById('corpus-title-input');
      const titleText = document.getElementById('corpus-title-text');
      const renameBtn = document.getElementById('action-rename');

      function startRename() {
        titleDisplay.classList.add('hidden');
        titleInput.classList.remove('hidden');
        titleInput.focus();
        titleInput.select();
      }

      function finishRename() {
        const val = titleInput.value.trim();
        if (val) titleText.textContent = val;
        titleInput.classList.add('hidden');
        titleDisplay.classList.remove('hidden');
      }

      if (titleDisplay && titleInput) {
        titleDisplay.addEventListener('click', startRename);
        if (renameBtn) {
          renameBtn.addEventListener('click', () => {
            document.getElementById('corpus-overflow-dropdown').classList.add('hidden');
            startRename();
          });
        }
        titleInput.addEventListener('blur', finishRename);
        titleInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') finishRename();
          if (e.key === 'Escape') {
            titleInput.value = titleText.textContent;
            finishRename();
          }
        });
      }

      // 2. Overflow Menu Toggle
      const overflowBtn = document.getElementById('corpus-overflow-btn');
      const overflowMenu = document.getElementById('corpus-overflow-dropdown');
      if (overflowBtn && overflowMenu) {
        overflowBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          overflowMenu.classList.toggle('hidden');
        });
        document.addEventListener('click', (e) => {
          if (!overflowMenu.contains(e.target) && e.target !== overflowBtn) {
            overflowMenu.classList.add('hidden');
          }
        });
      }

      // 3. Architecture Selector (Unified in Row 2)
      const archButtons = document.querySelectorAll('.arch-toggle-btn');
      archButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          archButtons.forEach(b => {
            b.classList.remove('bg-primary/15', 'text-primary', 'border-primary/40', 'font-semibold');
            b.classList.add('text-slate-400', 'border-transparent');
          });
          btn.classList.add('bg-primary/15', 'text-primary', 'border-primary/40', 'font-semibold');
          btn.classList.remove('text-slate-400', 'border-transparent');
        });
      });

      // 4. Toggle Collapsible Run Context Drawer
      const toggleContextBtn = document.getElementById('toggle-run-context-btn');
      const runContextDrawer = document.getElementById('run-context-drawer');
      const runContextIcon = document.getElementById('run-context-icon');
      if (toggleContextBtn && runContextDrawer) {
        toggleContextBtn.addEventListener('click', () => {
          const isHidden = runContextDrawer.classList.contains('hidden');
          if (isHidden) {
            runContextDrawer.classList.remove('hidden');
            runContextIcon.style.transform = 'rotate(180deg)';
          } else {
            runContextDrawer.classList.add('hidden');
            runContextIcon.style.transform = 'rotate(0deg)';
          }
        });
      }

      // 5. Scope Popover Selector
      const scopeBtn = document.getElementById('scope-selector-btn');
      const scopePopover = document.getElementById('scope-popover');
      const scopeLabel = document.getElementById('current-scope-label');
      const scopeOptions = document.querySelectorAll('.scope-option');

      if (scopeBtn && scopePopover) {
        scopeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          scopePopover.classList.toggle('hidden');
        });
        scopeOptions.forEach(opt => {
          opt.addEventListener('click', () => {
            const scope = opt.getAttribute('data-scope');
            if (scopeLabel) scopeLabel.textContent = scope;
            scopePopover.classList.add('hidden');
          });
        });
        document.addEventListener('click', (e) => {
          if (!scopePopover.contains(e.target) && e.target !== scopeBtn) {
            scopePopover.classList.add('hidden');
          }
        });
      }

      // 6. Auto-grow Textarea
      const textarea = document.getElementById('chat-input-textarea');
      if (textarea) {
        textarea.addEventListener('input', function() {
          this.style.height = 'auto';
          this.style.height = Math.min(this.scrollHeight, 128) + 'px';
        });
      }

      // 7. Citation Chips Click Event & Flash Evidence Panel
      const citations = document.querySelectorAll('.citation-btn');
      const rightPanel = document.getElementById('panel-right');
      const inspectorContent = document.getElementById('inspector-content');
      citations.forEach(chip => {
        chip.addEventListener('click', () => {
          if (rightPanel && rightPanel.classList.contains('hidden')) {
            rightPanel.classList.remove('hidden');
          }
          if (inspectorContent) {
            inspectorContent.scrollTop = 0;
          }
          rightPanel.classList.add('ring-2', 'ring-primary');
          setTimeout(() => rightPanel.classList.remove('ring-2', 'ring-primary'), 600);
        });
      });

      // 8. Collapsible Evidence Inspector
      const closeInspectorBtn = document.getElementById('close-inspector-btn');
      if (closeInspectorBtn && rightPanel) {
        closeInspectorBtn.addEventListener('click', () => {
          rightPanel.classList.toggle('hidden');
        });
      }

      // 9. Copy ArXiv ID
      const copyBtn = document.getElementById('copy-arxiv-btn');
      const arxivId = document.getElementById('arxiv-id-val');
      if (copyBtn && arxivId) {
        copyBtn.addEventListener('click', () => {
          navigator.clipboard.writeText(arxivId.textContent);
          const icon = copyBtn.querySelector('.material-symbols-outlined');
          if (icon) {
            icon.textContent = 'check';
            setTimeout(() => icon.textContent = 'content_copy', 1400);
          }
        });
      }

      // 10. Filter Papers in Left Panel
      const filterInput = document.getElementById('paper-filter-input');
      const paperRows = document.querySelectorAll('.paper-item');
      if (filterInput) {
        filterInput.addEventListener('input', (e) => {
          const query = e.target.value.toLowerCase();
          paperRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? 'flex' : 'none';
          });
        });
      }

      // 11. Send Query Button
      const sendBtn = document.getElementById('send-query-btn');
      const chatThread = document.getElementById('chat-thread');
      if (sendBtn && textarea && chatThread) {
        sendBtn.addEventListener('click', () => {
          const q = textarea.value.trim();
          if (!q) return;

          const userMsg = document.createElement('div');
          userMsg.className = 'w-full flex justify-end';
          userMsg.innerHTML = `
            <div class="max-w-2xl bg-[#141B26] border border-outline-variant/90 rounded-2xl p-4 text-on-surface shadow-md">
              <div class="font-mono text-[10px] text-tertiary-muted mb-1.5 flex items-center justify-between tracking-wide uppercase">
                <span>RESEARCHER QUERY</span>
                <span>JUST NOW</span>
              </div>
              <p class="text-sm md:text-[15px] font-normal text-white leading-relaxed">${q.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</p>
            </div>
          `;
          chatThread.appendChild(userMsg);
          textarea.value = '';
          textarea.style.height = 'auto';
          chatThread.scrollTop = chatThread.scrollHeight;
        });
      }

      // 12. Panel Resizing
      const leftResizer = document.getElementById('resizer-left');
      const rightResizer = document.getElementById('resizer-right');
      const leftPanel = document.getElementById('panel-left');

      if (leftResizer && leftPanel) {
        let isResizingLeft = false;
        leftResizer.addEventListener('mousedown', () => {
          isResizingLeft = true;
          document.body.style.cursor = 'col-resize';
        });
        document.addEventListener('mousemove', (e) => {
          if (!isResizingLeft) return;
          const newWidth = e.clientX;
          if (newWidth > 220 && newWidth < 450) {
            leftPanel.style.width = newWidth + 'px';
          }
        });
        document.addEventListener('mouseup', () => {
          if (isResizingLeft) {
            isResizingLeft = false;
            document.body.style.cursor = 'default';
          }
        });
      }

      if (rightResizer && rightPanel) {
        let isResizingRight = false;
        rightResizer.addEventListener('mousedown', () => {
          isResizingRight = true;
          document.body.style.cursor = 'col-resize';
        });
        document.addEventListener('mousemove', (e) => {
          if (!isResizingRight) return;
          const newWidth = window.innerWidth - e.clientX;
          if (newWidth > 260 && newWidth < 500) {
            rightPanel.style.width = newWidth + 'px';
          }
        });
        document.addEventListener('mouseup', () => {
          if (isResizingRight) {
            isResizingRight = false;
            document.body.style.cursor = 'default';
          }
        });
      }
    })();
  </script>
</body></html>