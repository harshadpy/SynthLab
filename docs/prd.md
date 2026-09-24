# Product Requirements Document (PRD)
# ArXiv RAG Research Lab

**Document status:** Draft  
**Product type:** Multi-paper research and RAG evaluation platform  
**Primary users:** AI/ML researchers, students, engineers, and technical learners  
**Core value proposition:** Search ArXiv, create a research corpus from selected papers, chat with that corpus, and compare five RAG architectures using reproducible LangSmith evaluations.

---

## 1. Product Overview

ArXiv RAG Research Lab is a research workspace where users can search for academic papers through ArXiv, select multiple papers, create a persistent research corpus, and interact with that corpus through:

- Multi-paper conversational research chat
- Paper summaries and metadata
- Evidence-backed answers with paper and page/chunk citations
- Five interchangeable RAG architectures
- Side-by-side architecture comparison
- LangSmith tracing, datasets, experiments, and evaluations
- Corpus-level research insights and exports

The product is not intended to be a simple PDF chatbot. Its main differentiator is the ability to evaluate different RAG architectures against the same user-created research corpus and benchmark questions.

---

## 2. Problem Statement

Existing RAG demos commonly:

- Work with one or a few manually uploaded documents
- Hide the retrieval process
- Do not compare retrieval architectures fairly
- Lack reproducible evaluation
- Do not provide useful research-workspace features
- Produce answers without transparent paper-level evidence

Researchers need a system where they can:

1. Search for a topic.
2. Build a corpus from relevant ArXiv papers.
3. Understand the papers individually and collectively.
4. Ask cross-paper questions.
5. Compare RAG approaches using the same corpus and questions.
6. Inspect why one architecture performed better than another.

---

## 3. Goals

### 3.1 Primary goals

- Allow users to search ArXiv using a search query.
- Display searchable paper metadata and abstracts.
- Allow users to select multiple papers from search results.
- Create a named research corpus from selected papers.
- Download and process selected PDFs.
- Preserve paper metadata, section information, page numbers, and source references.
- Support multi-paper chat over the active corpus.
- Provide five selectable RAG architectures.
- Support architecture comparison using the same corpus and evaluation questions.
- Integrate LangSmith for tracing and LLM evaluation.
- Provide transparent evidence citations for generated answers.
- Provide a clean, modern research dashboard.

### 3.2 Secondary goals

- Allow users to save and reopen research workspaces.
- Support corpus refresh and adding/removing papers.
- Export research notes, chat history, experiment results, and corpus metadata.
- Make the system useful as an AI/RAG engineering portfolio project.
- Enable future research experiments without rewriting the whole platform.

### 3.3 Non-goals for the first release

- Full academic citation management like Zotero.
- Automatic publication of research papers.
- Training a foundation model.
- Supporting every academic repository.
- Building a general-purpose autonomous research agent.
- Guaranteeing that generated research conclusions are scientifically correct.
- Building five unrelated applications.

---

## 4. Target Users

### Persona A: AI/ML student

Wants to understand a research topic by reading and chatting with multiple papers.

### Persona B: RAG engineer

Wants to compare retrieval strategies and understand quality/latency trade-offs.

### Persona C: Researcher

Wants to create a focused literature corpus and identify themes, methods, limitations, and research gaps.

### Persona D: Portfolio reviewer

Wants to see a technically serious system with modular architecture, evaluation, observability, and measurable results.

---

## 5. Core User Journey

```text
User enters research query
        |
        v
Search ArXiv
        |
        v
Review papers, abstracts, authors, dates, categories
        |
        v
Select multiple papers
        |
        v
Create named research corpus
        |
        v
Download PDFs and process asynchronously
        |
        v
Build shared document representation
        |
        +------------------+
        |                  |
        v                  v
   Research Dashboard   RAG Chat
        |                  |
        v                  v
Architecture selection  Evidence-backed answer
        |
        v
Run LangSmith evaluation
        |
        v
Compare five RAG architectures
```

---

## 6. Product Scope

### 6.1 ArXiv discovery

Users can:

- Search by keyword.
- Search by title.
- Search by author.
- Search by abstract.
- Filter by category.
- Filter by date range.
- Sort by relevance or submission date.
- View paper title, authors, abstract, categories, published date, ArXiv ID, and PDF link.
- Select one or many papers.
- Avoid duplicate papers using normalized ArXiv IDs.

### 6.2 Research corpus creation

A corpus is a user-created workspace based on selected ArXiv papers.

Each corpus should have:

- Corpus ID
- Name
- Description
- Original search query
- Creation date
- Last updated date
- Selected paper IDs
- Processing status
- Number of papers
- Number of pages
- Number of chunks
- Number of indexed documents
- Available RAG architectures
- Evaluation status

Users can:

- Create a corpus.
- Rename a corpus.
- Add papers.
- Remove papers.
- Reprocess failed papers.
- Refresh metadata.
- Delete a corpus.
- Reopen a previous corpus.

### 6.3 Multi-paper research dashboard

The dashboard should contain:

#### Overview

- Corpus title and description
- Original search query
- Number of papers
- Number of authors
- Date range
- Categories
- Processing progress
- Index status
- Current RAG architecture
- Last evaluation run

#### Paper library

Each paper should display:

- Title
- Authors
- Abstract
- ArXiv ID
- Publication/submission date
- Categories
- PDF link
- Processing status
- Page count
- Chunk count
- Summary status
- Citation count within the corpus, if available from supported metadata

Actions:

- Open paper details
- View PDF
- View extracted text
- Summarize paper
- Remove from corpus
- Reprocess paper

#### Research insights

The system should support:

- Corpus-wide summary
- Paper-by-paper summaries
- Common themes
- Method comparison
- Dataset comparison
- Limitations
- Open problems
- Research timeline
- Concept/entity overview
- Cross-paper comparison

These insights must cite the papers and evidence used.

---

## 7. Five RAG Architectures

All five architectures must operate on the same logical corpus and the same evaluation questions.

The system should use a common interface so each architecture can be swapped without changing the rest of the application.

### 7.1 Architecture 1: Hybrid RAG

#### Purpose

Provide a strong retrieval baseline using both semantic and lexical retrieval.

#### Retrieval flow

```text
User query
   |
   +--> Dense vector retrieval
   |
   +--> BM25 / sparse retrieval
   |
   v
Rank fusion
   |
   v
Optional reranking
   |
   v
Context assembly
   |
   v
LLM answer
```

#### Requirements

- Dense retrieval
- BM25 or equivalent sparse retrieval
- Reciprocal Rank Fusion or another documented fusion method
- Optional cross-encoder reranking
- Paper and chunk metadata preservation

#### Research value

Demonstrates classical information retrieval combined with modern embeddings.

---

### 7.2 Architecture 2: Hierarchical RAG

#### Purpose

Improve retrieval over long research papers and multi-paper corpora.

#### Retrieval flow

```text
Corpus
   |
   v
Document sections / chunks
   |
   v
Hierarchical summaries
   |
   v
Retrieve relevant summaries
   |
   v
Retrieve detailed child chunks
   |
   v
Answer with local evidence
```

#### Requirements

- Section-aware document representation
- Parent-child document relationships
- Summary or hierarchical index
- Retrieval from broad to narrow context
- Page and section citations

#### Research value

Demonstrates long-document retrieval and context organization.

---

### 7.3 Architecture 3: GraphRAG

#### Purpose

Support questions involving relationships, concepts, methods, datasets, and multi-hop reasoning.

#### Retrieval flow

```text
Paper chunks
   |
   v
Entity and relationship extraction
   |
   v
Knowledge graph
   |
   v
Graph/entity retrieval
   |
   v
Relevant source chunks
   |
   v
LLM answer
```

#### Requirements

- Entity extraction
- Relationship extraction
- Graph storage
- Entity and community retrieval
- Source chunk linkage
- Evidence-backed graph-derived answers

#### Example questions

- Which papers use the same benchmark datasets?
- How are different RAG architectures related?
- Which methods address a specific limitation?
- What concepts connect these papers?

#### Research value

Demonstrates graph-based retrieval and multi-hop research.

---

### 7.4 Architecture 4: Agentic / Corrective RAG

#### Purpose

Allow the system to evaluate retrieval quality and perform additional retrieval when evidence is insufficient.

#### Retrieval flow

```text
User query
   |
   v
Query analysis
   |
   v
Initial retrieval
   |
   v
Evidence assessment
   |
   +--> Sufficient --> Generate answer
   |
   +--> Insufficient
             |
             v
       Query rewrite / decomposition
             |
             v
       Additional retrieval
             |
             v
       Evidence verification
             |
             v
       Generate answer
```

#### Requirements

- Explicit state machine or LangGraph workflow
- Query classification
- Retrieval grading
- Query rewriting or decomposition
- Maximum iteration limit
- Failure handling
- Traceable intermediate steps
- No unsupported claims when evidence is insufficient

#### Research value

Demonstrates orchestration, adaptive retrieval, and agentic workflows.

---

### 7.5 Architecture 5: Adaptive RAG

#### Purpose

Select the retrieval depth or strategy based on query difficulty and retrieval sufficiency.

#### Retrieval flow

```text
User query
   |
   v
Query difficulty / sufficiency estimation
   |
   +--> Simple query --> Fast retrieval
   |
   +--> Moderate query --> Hybrid + reranking
   |
   +--> Complex query --> Multi-step / graph / deeper retrieval
   |
   v
Evidence validation
   |
   v
Answer generation
```

#### Requirements

- Query classification or routing
- Retrieval sufficiency signal
- Configurable routing policy
- Fallback path
- Maximum latency and token budget
- Routing trace in LangSmith
- Clear explanation of selected route

#### Research value

Demonstrates intelligent retrieval routing and quality/cost trade-offs.

#### Important implementation note

Adaptive RAG may internally call other retrieval components, but it must still be treated as a distinct architecture because its contribution is the routing and decision policy.

---

## 8. Shared RAG Interface

All architectures should implement a common contract.

```python
class RAGPipeline(Protocol):
    async def retrieve(self, query: str, corpus_id: str) -> RetrievalResult:
        ...

    async def generate(
        self,
        query: str,
        retrieval_result: RetrievalResult,
    ) -> AnswerResult:
        ...

    async def run(
        self,
        query: str,
        corpus_id: str,
        config: dict,
    ) -> AnswerResult:
        ...
```

Every result should include:

- Answer text
- Retrieved chunks
- Paper IDs
- Page numbers where available
- Section names where available
- Retrieval scores
- Architecture name
- Model name
- Latency
- Token usage
- Trace ID
- Evaluation metadata

---

## 9. Corpus and Indexing Requirements

### 9.1 Shared ingestion pipeline

```text
ArXiv metadata
      |
      v
PDF download
      |
      v
PDF parsing
      |
      v
Page-aware text extraction
      |
      v
Section detection
      |
      v
Document normalization
      |
      v
Chunking
      |
      v
Metadata enrichment
      |
      +--> Dense index
      |
      +--> Sparse index
      |
      +--> Hierarchical index
      |
      +--> Graph index
```

### 9.2 Metadata requirements

Every chunk should preserve:

- Corpus ID
- Paper ID
- ArXiv ID
- Paper title
- Authors
- Page number
- Section name
- Chunk ID
- Parent document ID
- Source PDF URL
- Text hash
- Embedding model version
- Ingestion version
- Created timestamp

### 9.3 Processing behavior

- Processing must be asynchronous.
- The UI must show progress.
- Failed papers must not fail the entire corpus.
- Processing must be resumable.
- Duplicate papers must not be indexed twice.
- Reprocessing must be versioned or safely replace old indexes.
- Empty or malformed PDFs must be reported clearly.
- OCR may be added as a future enhancement.

---

## 10. Research Chat Requirements

### 10.1 Chat modes

The user should be able to select:

- One paper
- Selected papers
- Entire corpus
- Specific architecture
- Compare all architectures

### 10.2 Supported question types

- Paper summary
- Main contributions
- Methodology explanation
- Dataset comparison
- Results comparison
- Limitations
- Research gaps
- Cross-paper synthesis
- Concept explanation
- Evidence lookup
- Architecture comparison

### 10.3 Answer requirements

Every research answer should:

- Clearly distinguish evidence from inference.
- Cite source papers.
- Include page or section references when available.
- Avoid claiming unsupported facts.
- State when the corpus does not contain enough evidence.
- Provide a concise answer first, followed by supporting details.
- Show retrieved evidence on demand.
- Allow the user to inspect source chunks.

### 10.4 Chat history

Store:

- Conversation ID
- Corpus ID
- User query
- Selected papers
- Architecture
- Answer
- Retrieved sources
- Trace ID
- Timestamp
- Feedback
- Evaluation status

---

## 11. LangSmith Evaluation Requirements

LangSmith is a core product feature, not an optional logging add-on.

### 11.1 LangSmith integration

The system must support:

- LangSmith tracing
- Run/project organization
- Dataset creation
- Dataset versioning
- Evaluation runs
- Online or offline evaluators
- Feedback capture
- Trace inspection
- Experiment comparison

### 11.2 Trace structure

Each RAG request should trace:

```text
Root RAG run
  |
  +--> Query preprocessing
  |
  +--> Architecture selection
  |
  +--> Retrieval
  |      |
  |      +--> Dense retrieval
  |      +--> Sparse retrieval
  |      +--> Graph retrieval
  |      +--> Reranking
  |
  +--> Context assembly
  |
  +--> Prompt construction
  |
  +--> LLM generation
  |
  +--> Citation extraction
  |
  +--> Evaluation
```

For agentic and adaptive pipelines, trace:

- Routing decisions
- Retrieval attempts
- Query rewrites
- Grader outputs
- Stop conditions
- Fallbacks

### 11.3 Evaluation dataset

The system should allow users or developers to create an evaluation dataset from:

- Manually written questions
- Generated questions from corpus papers
- Existing benchmark questions
- Questions collected from real chat sessions
- Human-provided reference answers
- Reference source documents

Each example should contain:

- Question
- Corpus ID
- Expected answer, if available
- Relevant paper IDs
- Relevant chunk IDs, if available
- Difficulty
- Question type
- Dataset version

### 11.4 Required evaluation metrics

#### Retrieval metrics

- Context precision
- Context recall
- Recall@K
- MRR
- NDCG, if applicable
- Relevant paper retrieval rate

#### Generation metrics

- Faithfulness
- Answer relevance
- Correctness
- Citation correctness
- Citation completeness
- Unsupported-claim rate

#### System metrics

- End-to-end latency
- Retrieval latency
- LLM latency
- Input tokens
- Output tokens
- Total tokens
- Estimated cost
- Number of retrieval calls
- Number of agentic iterations
- Failure rate

### 11.5 Evaluation strategy

Every architecture must be evaluated on:

- The same corpus
- The same questions
- The same reference answers where applicable
- The same LLM, unless the experiment explicitly studies model variation
- The same embedding model where applicable
- The same top-K budget where possible
- The same token and latency reporting rules

The dashboard must clearly label experiments that are not directly comparable.

### 11.6 Human feedback

Users should be able to mark an answer as:

- Helpful
- Not helpful
- Correct
- Incorrect
- Missing evidence
- Incorrect citation
- Incomplete

Feedback should be linked to the LangSmith trace where possible.

---

## 12. Evaluation Dashboard

The evaluation dashboard should show:

### Summary

- Best architecture by correctness
- Best architecture by faithfulness
- Best architecture by retrieval recall
- Fastest architecture
- Lowest token usage
- Lowest estimated cost
- Number of evaluated questions
- Evaluation dataset version

### Comparison table

| Architecture | Correctness | Faithfulness | Recall@K | Latency | Tokens | Cost |
|---|---:|---:|---:|---:|---:|---:|
| Hybrid RAG | — | — | — | — | — | — |
| Hierarchical RAG | — | — | — | — | — | — |
| GraphRAG | — | — | — | — | — | — |
| Agentic RAG | — | — | — | — | — | — |
| Adaptive RAG | — | — | — | — | — | — |

No metric should be fabricated. Empty or unavailable values must be shown as unavailable.

### Detailed experiment view

- Experiment name
- Date
- Git commit/version
- Corpus version
- Dataset version
- Model version
- Architecture configuration
- Prompt version
- Metric results
- Failed examples
- Best examples
- Worst examples
- LangSmith project/trace links

---

## 13. Suggested Technical Architecture

### Backend

- Python
- FastAPI
- LangChain and/or LangGraph
- Pydantic
- Background task system
- PostgreSQL
- Object storage for PDFs
- Vector database
- Sparse retrieval index
- Graph database for GraphRAG
- LangSmith

### Frontend

- React
- Next.js
- TypeScript
- Tailwind CSS
- Component library
- Streaming chat UI
- Interactive evaluation charts

### Data layer

Recommended logical entities:

```text
User
Corpus
Paper
PaperVersion
Document
Chunk
EmbeddingIndex
SparseIndex
GraphEntity
GraphRelationship
Conversation
Message
RAGRun
EvaluationDataset
EvaluationExample
EvaluationExperiment
Feedback
```

### Suggested repository structure

```text
arxiv-rag-lab/
├── apps/
│   ├── web/
│   └── api/
├── packages/
│   ├── rag-core/
│   ├── ingestion/
│   ├── evaluation/
│   ├── retrieval/
│   └── shared/
├── services/
│   ├── arxiv/
│   ├── document-processing/
│   └── indexing/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── retrieval/
│   └── evaluation/
├── docs/
├── scripts/
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 14. API Requirements

### ArXiv

```http
GET /api/arxiv/search?q=...
GET /api/arxiv/papers/{arxiv_id}
```

### Corpus

```http
POST /api/corpora
GET /api/corpora
GET /api/corpora/{corpus_id}
PATCH /api/corpora/{corpus_id}
DELETE /api/corpora/{corpus_id}
POST /api/corpora/{corpus_id}/papers
DELETE /api/corpora/{corpus_id}/papers/{paper_id}
POST /api/corpora/{corpus_id}/process
GET /api/corpora/{corpus_id}/processing-status
```

### Chat

```http
POST /api/corpora/{corpus_id}/chat
GET /api/conversations/{conversation_id}
GET /api/runs/{run_id}
```

### RAG architectures

```http
GET /api/rag/architectures
POST /api/corpora/{corpus_id}/runs
POST /api/corpora/{corpus_id}/compare
```

### Evaluation

```http
POST /api/evaluation/datasets
GET /api/evaluation/datasets
POST /api/evaluation/experiments
GET /api/evaluation/experiments/{experiment_id}
GET /api/evaluation/experiments/{experiment_id}/results
```

---

## 15. UI Requirements

### Main navigation

- Home
- Discover Papers
- My Corpora
- Active Research Workspace
- RAG Experiments
- Evaluation Dashboard
- Settings

### Research workspace layout

```text
┌──────────────────────────────────────────────────────────┐
│ Corpus title · Search query · Processing status           │
├───────────────┬───────────────────────────┬──────────────┤
│ Paper Library │ Research Chat             │ Evidence     │
│               │                           │ Inspector    │
│ Paper list    │ Conversation              │              │
│ Filters       │ Architecture selector     │ Source paper │
│ Metadata      │ Chat input                │ Page/chunk   │
│               │                           │              │
├───────────────┴───────────────────────────┴──────────────┤
│ Corpus insights · Architecture comparison · Evaluations  │
└──────────────────────────────────────────────────────────┘
```

### Architecture selector

The selector must show:

- Architecture name
- Short description
- Retrieval strategy
- Expected strengths
- Expected trade-offs
- Current configuration
- Evaluation status

### Evidence inspector

When the user clicks a citation, show:

- Paper title
- ArXiv ID
- Page number
- Section
- Source chunk
- Retrieval score
- Architecture that retrieved it
- Link to original paper/PDF

---

## 16. Functional Requirements

### FR-001: Search ArXiv

The system shall allow a user to search ArXiv and return paper metadata.

### FR-002: Select multiple papers

The system shall allow users to select multiple search results and create a corpus.

### FR-003: Create persistent corpus

The system shall persist corpus metadata and selected papers.

### FR-004: Process papers asynchronously

The system shall download, parse, chunk, and index papers without blocking the main request.

### FR-005: Track processing status

The system shall expose queued, processing, completed, and failed states.

### FR-006: Preserve evidence metadata

The system shall preserve paper, page, section, and chunk metadata throughout retrieval and generation.

### FR-007: Multi-paper chat

The system shall answer questions against one or more papers in a corpus.

### FR-008: Architecture selection

The system shall allow users to choose among five RAG architectures.

### FR-009: Shared corpus fairness

The system shall allow all architectures to run against the same corpus version.

### FR-010: LangSmith tracing

The system shall trace retrieval, generation, routing, and evaluation operations.

### FR-011: Evaluation datasets

The system shall support creation and versioning of evaluation datasets.

### FR-012: Experiment comparison

The system shall compare architecture results using consistent metrics.

### FR-013: Citation display

The system shall show source citations and allow evidence inspection.

### FR-014: User feedback

The system shall collect answer feedback and associate it with runs.

### FR-015: Export

The system shall export corpus metadata, chat history, evidence, and experiment results.

---

## 17. Non-Functional Requirements

### Performance

- Search results should begin rendering quickly.
- Chat should stream responses where supported.
- Corpus processing should report progress.
- Retrieval latency should be measured separately from generation latency.
- Evaluation jobs should run asynchronously.

### Reliability

- Failed paper processing should be recoverable.
- Duplicate ingestion should be prevented.
- API failures should be retried with limits.
- Long-running jobs should be resumable.
- Partial corpus availability should be supported.

### Security

- API keys must be stored server-side.
- Secrets must never be exposed in frontend code.
- User corpus access must be isolated.
- Uploaded/downloaded documents must be validated.
- LangSmith configuration must be environment-based.
- Logs must not expose secrets or sensitive user content unnecessarily.

### Observability

- Structured application logs
- Request IDs
- Corpus processing logs
- RAG run IDs
- LangSmith trace IDs
- Error tracking
- Evaluation job status

### Reproducibility

Every experiment should record:

- Git commit
- Corpus version
- Dataset version
- Prompt version
- Model
- Embedding model
- Chunking configuration
- Retrieval configuration
- Reranker
- Architecture configuration
- Timestamp

---

## 18. MVP Definition

The MVP should include:

1. ArXiv search.
2. Multi-paper selection.
3. Persistent corpus creation.
4. PDF ingestion with page-aware metadata.
5. Shared dense and sparse indexes.
6. Hybrid RAG.
7. Hierarchical RAG.
8. GraphRAG basic version.
9. Agentic/Corrective RAG.
10. Adaptive RAG basic routing.
11. Multi-paper chat.
12. Evidence citations.
13. LangSmith tracing.
14. A manually curated evaluation dataset.
15. Basic architecture comparison dashboard.

The MVP does not need every advanced feature immediately. The first goal is a reliable end-to-end workflow.

---

## 19. Recommended Implementation Phases

### Phase 1: Foundation

- Replace prototype global state with persistent storage.
- Set up FastAPI.
- Set up database and object storage.
- Implement ArXiv search service.
- Implement corpus and paper models.
- Implement background processing.
- Add tests.

### Phase 2: High-quality baseline

- Implement page-aware parsing.
- Implement metadata-rich chunking.
- Implement dense retrieval.
- Implement BM25.
- Implement Hybrid RAG.
- Implement citation-aware answer generation.
- Add LangSmith tracing.

### Phase 3: Additional architectures

- Implement Hierarchical RAG.
- Implement GraphRAG.
- Implement Agentic/Corrective RAG using LangGraph.
- Implement Adaptive RAG routing.
- Add architecture configuration and common interfaces.

### Phase 4: Evaluation

- Create evaluation dataset schema.
- Add reference questions and relevant sources.
- Add LangSmith evaluators.
- Add retrieval and generation metrics.
- Add experiment runner.
- Add comparison dashboard.

### Phase 5: Product polish

- Build modern frontend.
- Add streaming chat.
- Add paper reader and evidence inspector.
- Add corpus insights.
- Add exports.
- Add authentication and workspace isolation.
- Add deployment configuration.

---

## 20. Acceptance Criteria

The product is ready for an MVP demo when:

- A user can search ArXiv.
- A user can select at least five papers.
- A user can create a named corpus.
- The system processes the papers and reports status.
- The user can open the corpus dashboard.
- The user can chat with the entire corpus.
- Answers show source papers and page/chunk evidence where available.
- The user can switch among five RAG architectures.
- Each architecture runs through the same common interface.
- The system records LangSmith traces.
- The user can run an evaluation dataset against all five architectures.
- The dashboard displays comparable metrics.
- Failed processing and failed RAG runs are visible and recoverable.
- The system does not fabricate evaluation numbers.
- The project has unit and integration tests for core retrieval and evaluation behavior.

---

## 21. Success Metrics

### Product metrics

- Corpus creation completion rate
- Average papers per corpus
- Processing success rate
- Chat questions per corpus
- Repeat usage
- User feedback score
- Evidence click-through rate

### Engineering metrics

- Retrieval latency
- End-to-end latency
- Processing throughput
- Failed job rate
- Evaluation reproducibility
- Test coverage of critical components

### Research metrics

- Faithfulness
- Correctness
- Retrieval recall
- Citation correctness
- Cost per answer
- Token efficiency
- Architecture-specific strengths and weaknesses

---

## 22. Risks and Mitigations

### Risk: ArXiv API rate limits

Mitigation:

- Cache metadata.
- Use respectful request rates.
- Add retries with backoff.
- Avoid unnecessary repeated searches.
- Make API configuration environment-based.

### Risk: PDF parsing quality

Mitigation:

- Preserve page boundaries.
- Detect malformed PDFs.
- Add OCR as a fallback later.
- Track extraction quality.
- Allow reprocessing.

### Risk: Unfair architecture comparison

Mitigation:

- Same corpus version.
- Same evaluation dataset.
- Same model where possible.
- Record all configuration.
- Clearly label non-comparable experiments.

### Risk: GraphRAG complexity

Mitigation:

- Start with a basic entity/relation graph.
- Link every graph fact to source chunks.
- Add advanced community detection later.

### Risk: Evaluation metrics can be misleading

Mitigation:

- Combine automated and human evaluation.
- Show metric definitions.
- Keep reference answers and source labels.
- Inspect failed examples.
- Never present a single score as universal truth.

### Risk: LLM hallucination

Mitigation:

- Evidence-first prompts.
- Citation validation.
- Retrieval sufficiency checks.
- Explicit abstention behavior.
- LangSmith traces and feedback.

---

## 23. Future Enhancements

- Support Semantic Scholar and OpenAlex.
- Add citation graph exploration.
- Add paper recommendation.
- Add automatic literature review generation.
- Add research timeline generation.
- Add multimodal PDF understanding.
- Add tables and figure extraction.
- Add collaborative workspaces.
- Add saved research notes.
- Add hypothesis generation with evidence tracking.
- Add benchmark sharing.
- Add custom user-uploaded papers.
- Add model comparison.
- Add reranker comparison.
- Add automated regression evaluation in CI/CD.

---

## 24. Final Product Positioning

### Short description

> ArXiv RAG Research Lab is a multi-paper research workspace that turns ArXiv searches into interactive, evidence-backed research corpora and lets users compare five RAG architectures through LangSmith-powered evaluation.

### Resume-oriented description

> Built a modular multi-paper RAG research platform with ArXiv corpus creation, Hybrid RAG, Hierarchical RAG, GraphRAG, Agentic RAG, and Adaptive RAG; implemented LangSmith tracing and evaluation workflows to compare retrieval quality, faithfulness, correctness, latency, and token efficiency on shared research datasets.

### Core differentiator

The product is not merely “chat with PDFs.”

It is:

> **Search → Build corpus → Research → Chat → Compare RAG architectures → Evaluate → Improve.**


