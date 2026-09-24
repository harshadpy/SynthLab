# RAGLab: Comprehensive Low-Level Architectural & Technical Explanation

This document provides a complete, low-level technical understanding of **RAGLab**, including the system architecture, directory layouts, database models, ingestion pipelines, individualized RAG retrieval algorithms, routing tables, frontend component trees, and end-to-end request lifecycles.

---

## 1. System Architecture Overview

RAGLab is a high-performance, open-source scientific literature discovery and multi-architecture Retrieval-Augmented Generation (RAG) platform. It allows researchers to search and ingest academic publications from arXiv, index them into vector and lexical search engines, and benchmark/synthesize queries across 5 distinct RAG architectures powered by `gpt-5.6-luna`.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND (React + Vite)                              │
│                                                                                        │
│  [Step 1: Discover]   [Step 2: Workspace]   [Step 3: Compare]   [Step 4: Eval]   [Step 5: Insights]
│    DiscoverView.tsx     WorkspaceView.tsx    ArchCompareView     EvaluationView     InsightsView   │
│   (Search & Trending)  (Chat + Evidence)   (5-Col Matrix)       (RAG Triad)       (Theme Matrix) │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / JSON / SSE (Server-Sent Events)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   BACKEND (FastAPI API)                                │
│                                                                                        │
│  Routers:                                                                              │
│    /api/arxiv       -> Search arXiv, fetch abstracts, curated trending feed            │
│    /api/corpora     -> Create, manage, status poll, delete academic corpora            │
│    /api/rag         -> Execute single-pipeline query, compare 5 RAGs, SSE stream       │
│    /api/chat        -> General conversational and technical chat router                │
│    /api/evaluation  -> Benchmark experiment runner & LLM-as-a-judge scoring            │
│    /api/insights    -> Thematic clustering, method comparisons, research limitations   │
│                                                                                        │
│  Pipelines (apps/api/rag/):                                                            │
│    ├── Hybrid RAG         (Dense HNSW + Sparse BM25s + Reciprocal Rank Fusion)         │
│    ├── Hierarchical RAG   (Child chunk lookup -> Parent section context expansion)     │
│    ├── GraphRAG           (Entity co-occurrence graph + community summary synthesis)   │
│    ├── Agentic RAG (CRAG) (LangGraph state machine: Grading -> Rewrite -> Ingestion)   │
│    └── Adaptive RAG       (LLM query complexity classifier -> Dynamic route selection) │
│                                                                                        │
│  Core Services (apps/api/services/):                                                   │
│    ├── arxiv_service.py       -> OpenAlex & ArXiv Atom search + PDF downloader         │
│    ├── index_service.py       -> In-memory HNSW vector index + BM25s lexical index     │
│    ├── evaluation_service.py  -> RAG Triad judge (Faithfulness, Recall, Precision)     │
│    └── langsmith.py           -> LangChain / LangSmith tracing telemetry               │
│                                                                                        │
│  Storage Layer (SQLite + AsyncSQLAlchemy):                                              │
│    ├── data/arxiv_rag.db      -> Corpora, Papers, Chunks, Benchmark Experiments        │
│    ├── data/pdfs/             -> Downloaded original academic publication PDFs         │
│    └── data/indices/          -> Serialized vectors and lexical index structures       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Layout & Module Responsibilities

```
researchsystem/
├── apps/
│   ├── api/                           # FastAPI Application Backend
│   │   ├── core/                      # Global runtime configuration
│   │   │   ├── config.py              # Environment variables, model names, paths
│   │   │   ├── database.py            # SQLite async engine, sessionmaker, init_db
│   │   │   └── langsmith.py           # LangSmith tracing client wrapper
│   │   ├── models/                    # SQLAlchemy ORM Models
│   │   │   └── corpus.py              # Corpus, Paper, Chunk, BenchmarkExperiment
│   │   ├── schemas/                   # Pydantic validation schemas
│   │   │   ├── arxiv.py               # ArXivPaperItem, ArXivSearchResponse
│   │   │   ├── corpus.py              # CorpusCreateRequest, CorpusResponse, PaperResponse
│   │   │   └── rag.py                 # QueryRequest, AnswerResult, CitationChip
│   │   ├── services/                  # Core domain logic
│   │   │   ├── arxiv_service.py       # Live arXiv fetching, OpenAlex API, PDF downloads
│   │   │   ├── index_service.py       # HNSW cosine search, BM25 lexical indexing
│   │   │   └── evaluation_service.py  # LLM-as-a-judge automated benchmarking
│   │   ├── rag/                       # The 5 RAG Retrieval Architectures
│   │   │   ├── base.py                # Grounding engine, prompt builder, general query router
│   │   │   ├── hybrid_rag.py          # Dense + Sparse fusion pipeline (RRF k=60)
│   │   │   ├── hierarchical_rag.py    # Child (256 token) to Parent (2048 token) retrieval
│   │   │   ├── graph_rag.py           # Entity relationship graph & multi-hop extraction
│   │   │   ├── agentic_rag.py         # Corrective RAG (CRAG) with LangGraph state machine
│   │   │   └── adaptive_rag.py        # Dynamic query complexity classifier & router
│   │   ├── routers/                   # API HTTP Endpoints
│   │   │   ├── arxiv.py               # Search, trending, paper metadata
│   │   │   ├── corpora.py             # CRUD operations & background ingestion triggers
│   │   │   ├── chat.py                # Conversational endpoints
│   │   │   ├── rag.py                 # Query, comparison, and SSE streaming
│   │   │   ├── evaluation.py          # Benchmark experiment runs
│   │   │   └── insights.py            # Thematic synthesis, methodology matrix, timeline
│   │   └── main.py                    # Application entrypoint, lifespan, CORS, seed data
│   │
│   └── web/                           # Vite + React + TypeScript Frontend
│       ├── src/
│       │   ├── components/
│       │   │   ├── layout/
│       │   │   │   ├── Header.tsx     # Brand banner (RAGLab), Global 5-Step Stepper
│       │   │   │   └── Footer.tsx     # Telemetry status, active embedding model badge
│       │   │   ├── discover/
│       │   │   │   └── DiscoverView.tsx # Dual-pane search & live Trending Papers panel
│       │   │   ├── workspace/
│       │   │   │   ├── WorkspaceView.tsx # Chat interface, SSE token streaming, Strategy tabs
│       │   │   │   ├── EvidenceInspector.tsx # Slide-out drawer with chunk attention depths
│       │   │   │   └── TraceDrawer.tsx # Pipeline intermediate step inspector
│       │   │   ├── comparison/
│       │   │   │   └── ArchitectureComparisonView.tsx # 5-way comparative synthesis grid
│       │   │   ├── evaluation/
│       │   │   │   └── EvaluationView.tsx # Benchmark dashboard with RAG Triad KPIs
│       │   │   └── insights/
│       │   │       └── InsightsView.tsx # Thematic matrices, methodology comparisons
│       │   ├── services/
│       │   │   └── api.ts             # Typed REST API client & SSE consumer with fallbacks
│       │   ├── types/
│       │   │   └── index.ts           # TypeScript interfaces mirroring API Pydantic schemas
│       │   ├── App.tsx                # Top-level state machine & global navigation manager
│       │   └── index.css              # Custom scrollbars, glassmorphism, animations
│       └── package.json               # Frontend dependencies & scripts
│
├── data/                              # Local persistent storage
│   ├── arxiv_rag.db                   # SQLite relational database
│   ├── pdfs/                          # Raw arXiv PDF publications
│   └── indices/                       # Precomputed embeddings and token inverted indices
└── .env                               # API Keys & runtime flags
```

---

## 3. Database Schema & Data Models

The persistence layer uses SQLite via `SQLAlchemy`'s asynchronous extension (`aiosqlite`). Defined in `apps/api/models/corpus.py`:

```
┌────────────────────────────────┐
│             Corpus             │
├────────────────────────────────┤
│ id: String(36) [PK]            │
│ name: String(255)              │
│ description: Text              │
│ query: String(255)             │
│ status: String(50)             │  <- 'processing' | 'ready' | 'failed'
│ paper_count: Integer           │
│ page_count: Integer            │
│ chunk_count: Integer           │
│ created_at: DateTime           │
│ updated_at: DateTime           │
└───────────────┬────────────────┘
                │ 1
                │
                │ *
┌───────────────▼────────────────┐
│             Paper              │
├────────────────────────────────┤
│ id: String(36) [PK]            │
│ corpus_id: String(36) [FK]     │
│ arxiv_id: String(50)           │  <- e.g. "2501.12948"
│ title: String(500)             │
│ authors: JSON                  │  <- List of author name strings
│ abstract: Text                 │
│ categories: JSON               │  <- List of arXiv category tags (e.g. ["cs.AI"])
│ published_date: String(50)     │
│ pdf_url: String(500)           │
│ status: String(50)             │  <- 'queued' | 'downloading' | 'parsing' | 'indexed'
│ page_count: Integer            │
│ chunk_count: Integer           │
│ created_at: DateTime           │
└───────────────┬────────────────┘
                │ 1
                │
                │ *
┌───────────────▼────────────────┐
│             Chunk              │
├────────────────────────────────┤
│ id: String(36) [PK]            │
│ corpus_id: String(36) [FK]     │
│ paper_id: String(36) [FK]      │
│ arxiv_id: String(50)           │
│ page_number: Integer           │  <- Preserves exact publication page number
│ section_name: String(255)      │  <- e.g. "§3.2 Positional Degradation"
│ chunk_type: String(20)         │  <- 'child' (256 tokens) or 'parent' (2048 tokens)
│ parent_chunk_id: String(36)    │  <- Self-referencing link for hierarchical expansion
│ content: Text                  │
│ token_count: Integer           │
│ start_offset: Integer          │
│ end_offset: Integer            │
│ created_at: DateTime           │
└────────────────────────────────┘
```

---

## 4. End-to-End Paper Ingestion & Indexing Pipeline

When a user selects papers (from search or trending) and clicks **"Ingest & Launch Workspace"**, the following pipeline runs:

```
[User Selects Papers] ──▶ POST /api/corpora ──▶ BackgroundTasks(process_corpus_background)
                                                           │
                                                           ▼
                                                [Step 1: Download PDF]
                                               arxiv_service.download_pdf
                                                 (Saved to data/pdfs/)
                                                           │
                                                           ▼
                                                [Step 2: Parse PDF AST]
                                                PyMuPDF / pypdf / pypdfium2
                                             Extract text per page & section
                                                           │
                                                           ▼
                                                 [Step 3: Paper Structural Chunking]
                                              Parent Chunks: Academic Sections (§1, §3.2, etc.)
                                              Child Chunks: Natural Paragraphs + Complete Sentences
                                              Anchored with Section Tags (`[§3.2 Attention] ...`)
                                                           │
                                                           ▼
                                                [Step 4: Hybrid Indexing]
                                     ┌─────────────────────┴─────────────────────┐
                                     ▼                                           ▼
                            [Dense Embeddings]                           [Lexical Inverted Index]
                           text-embedding-3-small                              BM25s Okapi
                            In-Memory Cosine / HNSW                         Token frequencies
```

1. **Paper Resolution**:
   - `arxiv_service.get_paper(arxiv_id)` first checks the in-memory **Trending Papers cache** (sub-millisecond hit).
   - If not cached, it scrapes the official `https://arxiv.org/abs/{id}` page using `httpx`.
   - If that fails, it falls back to the OpenAlex Global Research API.
2. **PDF Acquisition**:
   - `arxiv_service.download_pdf(arxiv_id)` fetches the raw PDF from `https://arxiv.org/pdf/{arxiv_id}.pdf` with browser-like headers and saves it locally into `data/pdfs/{arxiv_id}.pdf`.
3. **Paper-Aware Structural Chunking Scheme (`ChunkingService`)**:
   - Rather than arbitrary fixed-window token slicing that cuts through sentences, equations, or section boundaries, RAGLab parses academic PDFs according to the author's logical structure:
   - **Section Header Recognition**: Employs layout-aware PyMuPDF block analysis supporting two-column LaTeX formats, capturing both single-line and two-line headers (e.g. `3.2` followed by `Attention`).
   - **Parent Chunks**: Encompass entire logical sections and subsections (e.g., *§1 Introduction*, *§3 Model Architecture*, *§3.2 Attention*). This preserves complete thematic context for high-level synthesis.
   - **Child Chunks**: Formed strictly along **natural paragraph boundaries and complete sentence boundaries** (`re.split(r'(?<=[.!?])\s+', ...)`). Tiny paragraphs are merged into coherent units (~200–300 tokens), while very long paragraphs are partitioned strictly between complete sentences. Never slices mid-word or mid-sentence.
   - **Section Anchor Prefixing**: Each child chunk is automatically prepended with its section header (e.g., `[§3.2 Attention]`), giving vector embeddings and BM25 lexical search instant contextual grounding even before parent expansion.
4. **Dual In-Memory Indexing**:
   - `index_service.index_corpus(corpus_id, chunks)` builds:
     - **Dense Vector Matrix**: Embeds each child chunk using OpenAI's `text-embedding-3-small` (or local fallback vectors if no API key is provided).
     - **BM25 Lexical Index**: Tokenizes child chunks using `BM25s` with standard English stemming and stop-word filtering.

---

## 5. The 5 Individualized RAG Architectures

RAGLab avoids generic retrieval by giving each of the 5 architectures a completely distinct algorithmic pipeline:

### 5.1. Hybrid RAG (`apps/api/rag/hybrid_rag.py`)
- **Philosophy**: Combines dense semantic understanding with exact sparse lexical precision.
- **Algorithm**:
  1. Computes dense cosine similarity: $S_{\text{dense}}(q, c) = \frac{\mathbf{e}_q \cdot \mathbf{e}_c}{\|\mathbf{e}_q\| \|\mathbf{e}_c\|}$.
  2. Computes BM25 lexical score: $S_{\text{bm25}}(q, c) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t, c) \cdot (k_1 + 1)}{f(t, c) + k_1 \cdot (1 - b + b \cdot \frac{|c|}{\text{avgdl}})}$.
  3. Fuses rankings using **Reciprocal Rank Fusion (RRF)**:
     $$\text{RRF}(c) = \frac{1}{60 + \text{Rank}_{\text{dense}}(c)} + \frac{1}{60 + \text{Rank}_{\text{bm25}}(c)}$$
  4. Returns Top-$K$ fused passages with both dense and lexical score diagnostics.

### 5.2. Hierarchical RAG (`apps/api/rag/hierarchical_rag.py`)
- **Philosophy**: Solves the "needle-in-a-haystack" trade-off between retrieval precision and synthesis context using paper-native structural hierarchies.
- **Algorithm**:
  1. Searches the index using high-precision **paragraph child chunks** (~200–300 tokens) anchored by section titles (`[§3.2 Attention]`).
  2. For the top matching child chunks, resolves their corresponding **parent section chunk** (`parent_chunk_id`) representing the full academic section/subsection.
  3. Deduplicates parent sections and passes the expanded, cohesive parent context to `gpt-5.6-luna`.
  4. Analyzes the relative token offset where the child chunk appeared inside the parent section to assign an **Attention Depth** (`prefix` for 0-30%, `middle` for 30-70%, `suffix` for 70-100%).

### 5.3. GraphRAG (`apps/api/rag/graph_rag.py`)
- **Philosophy**: Enables multi-hop reasoning across papers by extracting conceptual entities and relation triplets.
- **Algorithm**:
  1. Extracts entities from query terms (e.g., "Attention", "Positional Degradation", "CRAG", "RRF").
  2. Builds an entity co-occurrence adjacency graph across the corpus chunks.
  3. Computes connected component subgraphs (communities) and extracts passages where multiple related concepts intersect.
  4. Returns multi-hop context paths showing how Paper A's methodology addresses Paper B's limitation.

### 5.4. Agentic RAG / CRAG (`apps/api/rag/agentic_rag.py`)
- **Philosophy**: Implements Corrective Retrieval-Augmented Generation using an explicit self-grading state machine.
- **LangGraph State Graph**:
  ```
     [User Query]
          │
          ▼
     [Node: Retrieve] ──▶ Fetches initial candidate passages
          │
          ▼
     [Node: Grade Documents] ──▶ Evaluates relevance confidence score
          │
          ├──────────────────────────────────────────┐
          │ (Confidence ≥ 0.75)                      │ (Confidence < 0.75)
          ▼                                          ▼
     [Node: Generate]                       [Node: Rewrite Query]
  Synthesizes answer with               Reformulates search query using
  strict grounded citations             gpt-5.6-luna for deeper technical lookup
          ▲                                          │
          │                                          ▼
          └───────────────────────────────── [Node: Retrieve Supplementary]
  ```
- Intermediate execution steps are recorded in the `intermediate_steps` array and displayed in the frontend Trace Drawer.

### 5.5. Adaptive RAG (`apps/api/rag/adaptive_rag.py`)
- **Philosophy**: Routes queries dynamically to the most cost-effective and accurate RAG strategy based on query intent and complexity.
- **Algorithm**:
  1. Evaluates query difficulty via an upfront LLM classification call:
     - `simple`: Direct factual query (e.g., "Who proposed Transformer architecture?") $\to$ Routed to **Hybrid RAG** with Top-K=4.
     - `moderate`: In-depth mechanism explanation $\to$ Routed to **Hierarchical RAG** with Parent Section expansion.
     - `complex`: Multi-paper comparison or trade-off analysis $\to$ Routed to **GraphRAG / Agentic RAG** with query decomposition.
  2. Synthesizes the final answer using the dynamically selected sub-pipeline.

---

## 6. Synthesis, Grounding & Model Cascading

All pipelines delegate answer synthesis to `generate_research_answer()` in `apps/api/rag/base.py`.

### 6.1. Grounding Rules & Prompt Engineering
The system prompt enforces strict evidence attribution:
```python
system_prompt = (
    "You are an expert AI scientific research assistant. You provide evidence-grounded research answers.\n"
    "STRICT GROUNDING RULES:\n"
    "1. Base your answer EXCLUSIVELY on the provided numbered context passages.\n"
    "2. Whenever you state a technical fact, mechanism, limitation, or finding, you MUST cite the corresponding passage using inline citation chips like [1], [2].\n"
    "3. Provide a clear, rigorous, academic synthesis. State what is supported, and explicitly state if evidence is limited or inconclusive.\n"
    "4. Do NOT hallucinate claims not supported by the passages.\n"
)
```

### 6.2. Model Resolution & Fallback Cascade
The default model configured across the application is `gpt-5.6-luna`. To guarantee 100% uptime regardless of preview API tier availability:
1. First attempts completion with `gpt-5.6-luna`.
2. If OpenAI returns `model_not_found` or unsupported model string, it automatically catches the exception and falls back to `gpt-4o`.
3. Returns token usage metrics (`input`, `output`, `total`) and execution latencies (`retrieval_latency_ms`, `generation_latency_ms`).

### 6.3. Server-Sent Events (SSE) Streaming
For real-time token streaming:
- **Endpoint**: `POST /api/rag/corpora/{corpus_id}/chat/stream`
- Yields SSE events formatted as:
  - `data: {"type": "token", "token": "..."}`
  - `data: {"type": "metadata", "citations": [...], "latency_ms": 280, ...}`
  - `data: [DONE]`

---

## 7. HTTP Routing & API Reference Table

The backend exposes the following complete REST API surface mounted under `/api`:

| Router | Method | Path | Request Body / Query Params | Response Schema | Description |
|---|---|---|---|---|---|
| **ArXiv** | `GET` | `/api/arxiv/trending` | `limit: int = 10` | `List[ArXivPaperItem]` | Returns curated, real-world trending arXiv publications. |
| **ArXiv** | `GET` | `/api/arxiv/search` | `q: str, max_results: int = 15` | `ArXivSearchResponse` | Queries live OpenAlex & ArXiv Atom feeds. |
| **ArXiv** | `GET` | `/api/arxiv/papers/{arxiv_id}` | Path: `arxiv_id` | `ArXivPaperItem` | Fetches full title, authors, abstract, and PDF link. |
| **Corpora** | `GET` | `/api/corpora` | None | `List[CorpusResponse]` | Lists all active and indexed research corpora. |
| **Corpora** | `POST` | `/api/corpora` | `CorpusCreateRequest` | `CorpusResponse` | Initiates asynchronous paper download & indexing. |
| **Corpora** | `GET` | `/api/corpora/{id}` | Path: `id` | `CorpusResponse` | Gets metadata and paper processing statuses for a corpus. |
| **Corpora** | `PATCH` | `/api/corpora/{id}` | `{"name": "New Name"}` | `CorpusResponse` | Updates the display name of a research corpus. |
| **RAG** | `POST` | `/api/rag/corpora/{id}/query` | `QueryRequest` (query, strategy, top_k) | `AnswerResult` | Runs query through specified individualized RAG pipeline. |
| **RAG** | `POST` | `/api/rag/corpora/{id}/compare`| `QueryRequest` (query, top_k) | `Dict[str, AnswerResult]` | Simultaneously executes query across all 5 architectures. |
| **RAG** | `POST` | `/api/rag/corpora/{id}/chat/stream` | `QueryRequest` (query, strategy) | `text/event-stream` | Real-time token streaming with final metadata package. |
| **Chat** | `POST` | `/api/chat/corpora/{id}/chat` | `QueryRequest` | `AnswerResult` | Conversational query wrapper. |
| **Evaluation** | `POST` | `/api/evaluation/experiments` | Query: `corpus_id` | `BenchmarkExperimentResponse` | Evaluates all 5 RAGs against benchmark questions. |
| **Insights** | `GET` | `/api/insights/corpora/{id}/themes` | Path: `id` | `CorpusInsightsResponse` | Synthesizes themes, method matrices, limitations, timeline. |
| **System** | `GET` | `/health` | None | `{"status": "ok", "version": "1.4.0"}` | Backend liveness and telemetry health check. |

---

## 8. Frontend Architecture & Component Hierarchy

The frontend is built with React 18, Vite, and Tailwind CSS. State is managed via top-level reactive hooks in `App.tsx` and custom service layer utilities.

```
App.tsx (Current Step State: 1 | 2 | 3 | 4 | 5)
 ├── Header.tsx (Global navigation stepper & Corpus switcher)
 │
 ├── Step 1: DiscoverView.tsx
 │    ├── Left Pane: Search bar, query clear, Recommended Topic Pills, Search Results list
 │    ├── Right Pane: 🔥 Trending Papers side-panel, Category Filters, Ingest "+ Add" buttons
 │    └── Floating Bottom Bar: Multi-paper selection drawer & "Create Corpus" modal
 │
 ├── Step 2: WorkspaceView.tsx
 │    ├── Corpus Sidebar (Indexed papers, status badges, page counts)
 │    ├── Chat Area (Strategy selection tabs: Hybrid, Hierarchical, GraphRAG, Agentic, Adaptive)
 │    ├── Message Stream (Grounded answers, inline [1] citation chip popovers)
 │    ├── Evidence Inspector (Slide-out drawer with chunk attention depth visualizers)
 │    └── Trace Drawer (Step-by-step pipeline execution logs)
 │
 ├── Step 3: ArchitectureComparisonView.tsx
 │    ├── Query input bar
 │    └── 5-Column Side-by-Side Grid (Direct response, citations, latency diffs, token counts)
 │
 ├── Step 4: EvaluationView.tsx
 │    ├── Benchmark Dataset Selector (ArXiv RAG Benchmark v1)
 │    ├── Metric KPI Summary Cards (Context Precision, Recall, Faithfulness, Answer Relevance)
 │    └── Architectural Performance Radar & Bar Charts
 │
 ├── Step 5: InsightsView.tsx
 │    ├── Thematic Concept Cluster Cards
 │    ├── Methodological Comparison Matrix (Mechanism, Pros, Limitations)
 │    ├── Open Research Problems Grid
 │    └── Interactive Publication Timeline
 │
 └── Footer.tsx (Platform telemetry, embedding model identifier, API latency readout)
```

### Key Frontend Features:
- **Streaming Response Processor**: Consumes SSE streams using browser `ReadableStreamDefaultReader`, incrementally updating the UI while parsing the final JSON payload containing citation chips.
- **Interactive Citation Chips**: Clicking `[1]`, `[2]` inside any generated markdown answer automatically opens the **Evidence Inspector** to the exact page, section, and attention depth of that excerpt.
- **Trending Panel Integration**: Papers added from the Trending Papers panel are seamlessly combined with searched papers to create unified multi-paper research corpora.

---

## 9. Observability & Telemetry

RAGLab includes native telemetry and tracing hooks:
- **LangSmith Tracing**: Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in `.env`. When active, `apps/api/core/langsmith.py` attaches run traces to every RAG pipeline invocation.
- **Trace ID Injection**: Every `AnswerResult` returns a unique `trace_id`. The user can inspect this in the frontend Trace Drawer or cross-reference it in the LangSmith dashboard.
- **Performance Metrics**: Every retrieval operation tracks dense lookup time, sparse lexical indexing time, generation time, prompt tokens, and completion tokens.

---

## 10. Summary of Key Files

| File | Path | Key Role |
|---|---|---|
| **App Entry** | `apps/api/main.py` | FastAPI instantiation, lifespan, router inclusion |
| **ArXiv Service** | `apps/api/services/arxiv_service.py` | Live search, PDF downloads, trending paper cache |
| **Index Service** | `apps/api/services/index_service.py` | HNSW embeddings & BM25s lexical indexer |
| **Grounding Base** | `apps/api/rag/base.py` | Prompt construction, inline citation formatting, fallback |
| **Hybrid RAG** | `apps/api/rag/hybrid_rag.py` | Reciprocal Rank Fusion of dense and lexical scores |
| **Hierarchical RAG**| `apps/api/rag/hierarchical_rag.py` | Child chunk lookup $\to$ parent context expansion |
| **GraphRAG** | `apps/api/rag/graph_rag.py` | Entity extraction and community cluster synthesis |
| **Agentic RAG** | `apps/api/rag/agentic_rag.py` | LangGraph Corrective RAG state machine |
| **Adaptive RAG** | `apps/api/rag/adaptive_rag.py` | LLM query difficulty routing |
| **Discovery UI** | `apps/web/src/components/discover/DiscoverView.tsx` | Search interface + live Trending Papers panel |
| **Workspace UI** | `apps/web/src/components/workspace/WorkspaceView.tsx` | Chat, SSE streaming, Evidence Inspector |
