# Project Context & Feature Update Ledger (`context.md`)

> **Note for AI Agents & Developers**: Maintain and update this document across conversations. It serves as the single source of truth for architectural designs, feature upgrades, database schemas, pipeline graphs, and operational status.

---

## 1. System Overview
**ArXiv RAG Research Lab** is an interactive, production-grade benchmarking and experimentation platform for academic multi-paper research. It enables researchers to import ArXiv papers, parse structural sections, generate multi-scale chunkings (AST parent-child), and benchmark 5 advanced RAG architectures head-to-head with deep telemetry (latency, token usage, citation grounding, IR metrics, and precision).

### Technology Stack
- **API Backend**: FastAPI (`0.111+`), Python 3.12, Uvicorn, SQLAlchemy (`aiosqlite`), Pydantic v2.
- **Workflow Orchestration**: **LangGraph** (`langgraph>=0.0.50`, `StateGraph`, conditional edges, state compilation).
- **Knowledge Graph**: **Neo4j 5** (Bolt protocol, Cypher queries, constraints, typed ontology) + In-memory **NetworkX** fallback.
- **Retrieval & Reranking**:
  - Dense semantic retrieval: OpenAI `text-embedding-3-small` / `text-embedding-3-large`.
  - Sparse lexical indexing: `bm25s` (k1=1.5, b=0.75, English stopwords).
  - Fusion: Reciprocal Rank Fusion (configurable RRF, $k=60$).
  - Local Reranking: `LocalCrossEncoderReranker` (calibrated cross-attention interaction scoring without paid API keys).
  - AST Chunking: 256-token child anchors linked to 2,048-token parent section blocks.
- **Observability**: LangSmith tracing (`LANGCHAIN_TRACING_V2=true`).
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React icons.

---

## 2. Feature Updates & Evolution Log

### Version 2.0.0 (Current) — Advanced Architecture & Evaluation Upgrade
- **Shared Evidence & Citation Infrastructure (`apps/api/rag/common.py`)**:
  - Created standard `RetrievedChunk`, `EvidenceItem`, `EvidenceGrade`, `ClaimVerificationResult`, `LocalCrossEncoderReranker`, and `CitationVerifier`.
  - Implemented offline, calibrated `LocalCrossEncoderReranker` combining term proximity, exact technical n-gram match density, and normalized dense-sparse cross-interaction.
  - Implemented `CitationVerifier` detecting broken or unsupported citation chips `[1]`, `[2]`.
- **Hybrid RAG Upgrade (`apps/api/rag/hybrid_rag.py`)**:
  - Added `rerank_candidates` node powered by `LocalCrossEncoderReranker`.
  - Added `verify_evidence_sufficiency` gate node.
  - Made retrieval and fusion parameters configurable (`dense_top_k`, `sparse_top_k`, `rrf_k`, `rerank_enabled`, `final_context_k`).
- **Hierarchical RAG Upgrade (`apps/api/rag/hierarchical_rag.py`)**:
  - Added parent section deduplication in `expand_parent_tree` to avoid repeating parent blocks in context.
  - Added `order_and_compress_context` node mitigating lost-in-the-middle degradation by placing key anchors at the start and end of context.
  - Preserved full academic metadata in citations (`paper_id`, `arxiv_id`, `section_name`, `page_number`, `parent_chunk_id`).
- **GraphRAG Upgrade (`apps/api/rag/graph_rag.py` & `neo4j_service.py`)**:
  - Upgraded Neo4j and NetworkX schema with typed scientific research entities: `Method`, `Dataset`, `Metric`, `Task`, `Concept`.
  - Created formal relationships: `:USES_METHOD`, `:EVALUATED_ON`, `:REPORTS_METRIC`, `:TARGETS_TASK`, `:RELATES_TO`.
  - Implemented bounded 2-hop traversal with path scoring taking degree, entity match, and linked chunks into account.
  - Added Louvain/greedy modularity community cluster retrieval for thematic synthesis queries.
- **Agentic RAG Upgrade (`apps/api/rag/agentic_rag.py`)**:
  - Integrated structured `EvidenceGrade` with relevance, coverage, quality, missing information, and verdict.
  - Upgraded query rewriting with intent preservation, scientific terminology retention, and iteration guard (max 2 iterations).
  - Added post-generation `verify_faithfulness` critic node validating claims against citations.
- **Adaptive RAG Upgrade (`apps/api/rag/adaptive_rag.py`)**:
  - Formulated as a dynamic query complexity classifier and pipeline dispatcher (`simple` -> Hybrid, `moderate` -> Hierarchical, `complex` -> GraphRAG, `agentic` -> Agentic).
  - Preserved independent user selectability: users can pick any of the 5 models directly, and Adaptive RAG is only used when selected.
  - Returned rich adaptive routing telemetry (route difficulty, confidence score, rationale, latency breakdown).
- **Evaluation Suite Upgrade (`apps/api/services/evaluation_service.py`)**:
  - Added classical IR metrics: `Recall@k`, `Precision@k`, `MRR`, `nDCG@k`, and `Hit Rate`.
  - Added generation metrics: `Faithfulness`, `Correctness`, `Citation Correctness`.
  - Added comprehensive 8-question benchmark dataset covering single-paper, multi-paper, comparative, method/dataset, and unanswerable questions.
- **Paper Search & Ingestion Event Loop Optimization**:
  - Accelerated `arxiv_service.search` with concurrent querying across both official ArXiv Atom feed and OpenAlex index, plus a 10-minute in-memory query cache (`_search_cache`), slashing search times to sub-second on cache hits and ~3-4s on cold live queries.
  - Offloaded CPU-bound and synchronous PDF extraction (`pdf_processor.extract_document`), AST chunking (`chunking_service.create_hierarchical_chunks`), and corpus indexing (`index_service.index_corpus`) to background worker threads via `asyncio.to_thread`, preventing event loop starvation.
  - Pre-seeded landmark papers and search mappings in `ArXivService` for sub-50ms instant paper lookup.
  - Added shared in-memory `_papers_cache` storing all queried papers to enable 0ms metadata retrieval during corpus creation.
  - Reduced network timeouts for ArXiv and OpenAlex queries to 2.5s with bounded `asyncio.wait`, preventing UI loading stalls.
  - Enhanced PDF downloading with 3.5s timeout and automatic high-fidelity structured PDF synthesis containing exact title, authors, abstract, and academic sections.
  - Upgraded `create_corpus` to concurrently fetch paper metadata using `asyncio.gather`, reducing corpus creation latency from >15s to ~79ms.
  - Added instant client-side pre-matching in `DiscoverView.tsx`, rendering matches in 0ms while background live searches complete smoothly.
- **Workspace UI & Grounded Telemetry Upgrades**:
  - Replaced arbitrary Top-K and Cohere indicators with a dynamic Grounding & Evidence Quality indicator (`Grounding: Faithful & Cited | Retrieval: <Strategy-Specific>`).
  - Implemented live LangSmith trace tracking with automatic `+` notation for trace counts $\ge 100$ (`100+ traces`) and event-driven updates on query execution.
  - Updated user profile avatar badge to `HT` across Header and ProfileDropdown.
  - Replaced static `14p · 28 chunks` fallback in sidebar paper cards with an explicit, clickable `Open PDF` button for direct arXiv access.
  - Fixed top bar title truncation and container flex-shrink behavior, preventing collisions between corpus titles and status badges across all viewport widths.
  - Implemented sequential numbered list formatting and rich citation chip styling in `MarkdownAnswer.tsx`.

---

## 3. RAG Architecture & LangGraph StateGraph Specifications

### 1. Hybrid RAG (`apps/api/rag/hybrid_rag.py`)
- **Type**: Dual-Retrieval Fusion with Reciprocal Rank Fusion & Cross-Encoder Reranking.
- **LangGraph Flow**:
  ```text
  [START]
     │
     ▼
  [retrieve_dense] ──► [retrieve_sparse]
                             │
                             ▼
                 [reciprocal_rank_fusion] (k=60)
                             │
                             ▼
                    [rerank_candidates] (LocalCrossEncoder)
                             │
                             ▼
              [verify_evidence_sufficiency]
                             │
                             ▼
                     [build_citations]
                             │
                             ▼
                     [generate_answer] ──► [END]
  ```
- **State**: `HybridState` (query, corpus_id, dense_results, sparse_results, fused_results, reranked_results, is_sufficient, citations, intermediate_steps, answer, token_usage).

### 2. Hierarchical RAG (`apps/api/rag/hierarchical_rag.py`)
- **Type**: AST Multi-Scale Parent-Child Expansion with Lost-in-the-Middle Context Ordering.
- **LangGraph Flow**:
  ```text
  [START]
     │
     ▼
  [retrieve_child_anchors] (256-token AST Leaf Chunks)
     │
     ▼
  [expand_parent_tree] (Resolves 2,048-token Parent Sections with Dedup)
     │
     ▼
  [order_and_compress_context] (Lost-in-Middle Edge Positioning)
     │
     ▼
  [assemble_citations]
     │
     ▼
  [generate_answer] ──► [END]
  ```

### 3. GraphRAG (`apps/api/rag/graph_rag.py`)
- **Type**: Typed Entity Knowledge Graph Traversal with Neo4j & NetworkX Symmetrical Engines.
- **LangGraph Flow**:
  ```text
  [START]
     │
     ▼
  [extract_query_entities] (Scientific Term Disambiguation)
     │
     ▼
  [query_graph_engine] (Bounded 2-Hop Traversal & Community Clusters)
     │
     ▼
  [augment_dense_evidence] (Dense Similarity Fusion)
     │
     ▼
  [assemble_citations] (Path Scoring & Centrality)
     │
     ▼
  [generate_answer] ──► [END]
  ```

### 4. Agentic RAG (`apps/api/rag/agentic_rag.py`)
- **Type**: Corrective RAG (CRAG) with Structured Grading, Query Reformulation, and Faithfulness Critic.
- **LangGraph Flow**:
  ```text
  [START]
     │
     ▼
  [retrieve_candidates] ◄──────────────────┐
     │                                     │
     ▼                                     │
  [grade_documents] (EvidenceGrade)         │
     │                                     │
     ├─► [verdict == "insufficient" AND iter < max] ──► [rewrite_query]
     │
     └─► [verdict == "sufficient" OR iter >= max]
           │
           ▼
     [generate_answer]
           │
           ▼
     [verify_faithfulness] (Critic Node) ──► [END]
  ```

### 5. Adaptive RAG (`apps/api/rag/adaptive_rag.py`)
- **Type**: Query Complexity Classifier & Pipeline Dispatcher.
- **LangGraph Flow**:
  ```text
  [START]
     │
     ▼
  [classify_query_complexity] (simple / moderate / complex / agentic + confidence)
     │
     ▼
  [compile_adaptive_telemetry] ──► [END]
  ```
- **Delegated Execution**:
  - `simple`: Dispatches to `hybrid_rag`
  - `moderate`: Dispatches to `hierarchical_rag`
  - `complex`: Dispatches to `graph_rag`
  - `agentic`: Dispatches to `agentic_rag`

---

## 4. API Endpoints Reference
- `GET  /api/health` — API health check and version.
- `GET  /api/corpora` — List corpora with document counts.
- `POST /api/corpora` — Create corpus.
- `POST /api/corpora/{id}/papers` — Ingest ArXiv papers into corpus.
- `GET  /api/rag/architectures` — List all 5 RAG architecture definitions and trade-offs.
- `POST /api/rag/corpora/{id}/compare` — Concurrently execute all 5 architectures on a query.
- `POST /api/corpora/{id}/chat` — Execute selected RAG pipeline and persist conversation.
- `POST /api/runs/{run_id}/feedback` — Record user ratings and comments (logged to LangSmith).
- `POST /api/evaluation/experiments` — Run benchmark evaluation suite across architectures.

---

## 5. Verification Commands
```bash
# Execute all RAG pipeline tests
.\.venv\Scripts\python.exe -m pytest tests/test_rag_pipelines.py tests/test_langgraph_and_neo4j.py -v

# Execute evaluation benchmark suite
.\.venv\Scripts\python.exe -m pytest tests/test_evaluation.py -v

# Run full test suite
.\.venv\Scripts\python.exe -m pytest tests/
```
