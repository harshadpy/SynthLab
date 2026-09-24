import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# ── Suppress repetitive health-check / model-probe access logs ───────────────
class _SuppressPollingFilter(logging.Filter):
    _MUTED = ("/health", "/v1/models")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(path in msg for path in self._MUTED)

logging.getLogger("uvicorn.access").addFilter(_SuppressPollingFilter())
# ─────────────────────────────────────────────────────────────────────────────

from apps.api.core.config import settings
from apps.api.core.database import init_db, AsyncSessionLocal
from apps.api.routers import arxiv, corpora, chat, rag, evaluation, insights, settings_router
from apps.api.models.corpus import Corpus, Paper, Chunk
from apps.api.services.index_service import index_service

SAMPLE_PAPERS = [
    {
        "arxiv_id": "2307.03172",
        "title": "Lost in the Middle: How Language Models Use Long Contexts",
        "authors": ["Nelson F. Liu", "Kevin Lin", "John Hewitt", "Percy Liang"],
        "abstract": "While modern language models have the ability to ingest long contexts, how well do they use them? We find that performance can degrade significantly when key information is located in the middle of long contexts.",
        "pages": 14,
        "chunks": 28,
        "sample_content": "We observe that retrieval performance in modern transformer models degrades significantly when relevant key-value states reside in the interior segments of context windows. Specifically, when documents are positioned in the middle (depths 40%–60%), accuracy falls by up to 34.2 percentage points compared to prefix placement. This U-shaped curve persists across foundation models, demonstrating that attention bias requires architectural interventions during multi-stage passage reranking."
    },
    {
        "arxiv_id": "2310.03025",
        "title": "RAG vs Long-Context LLMs: A Benchmark Study",
        "authors": ["Florian Schimanski", "Jiawei Han", "Ethan Perez"],
        "abstract": "We systematically compare Retrieval-Augmented Generation with native Long-Context LLMs across multi-hop reasoning, cost, and hallucination metrics on 30+ page documents.",
        "pages": 22,
        "chunks": 46,
        "sample_content": "Mitigates positional decay by pairing cosine distance over dense embeddings with exact token inverted indexes. BM25 is position-agnostic regarding document offsets, ensuring dense passages located in middle sections (e.g., Pages 14–26) with distinct technical vocabulary retain high lexical ranks regardless of embedding compression limits."
    },
    {
        "arxiv_id": "2401.15884",
        "title": "Corrective Retrieval Augmented Generation (CRAG)",
        "authors": ["Shi-Qi Yan", "Jia-Chen Gu", "Yunfan Zhu", "Zhen-Hua Ling"],
        "abstract": "We propose Corrective Retrieval Augmented Generation (CRAG) to self-evaluate retrieval relevance and adaptively trigger query rewrites or web search when evidence is insufficient.",
        "pages": 18,
        "chunks": 36,
        "sample_content": "CRAG introduces a retrieval evaluator to quantify document confidence into three bands: Correct, Ambiguous, and Incorrect. When retrieval confidence is ambiguous, a query rewriting and decomposition workflow triggers supplementary retrieval."
    },
    {
        "arxiv_id": "2004.04906",
        "title": "Dense Passage Retrieval for Open-Domain QA",
        "authors": ["Vladimir Karpukhin", "Barlas Oguz", "Danqi Chen"],
        "abstract": "Open-domain question answering relies on efficient passage retrieval using dense dual-encoder representations.",
        "pages": 11,
        "chunks": 31,
        "sample_content": "Dense passage retrieval leverages dual-encoder architecture where queries and candidate passages are mapped to low-dimensional continuous representations. When combined with BM25, DPR establishes a robust benchmark for open-domain questions."
    },
    {
        "arxiv_id": "2312.10997",
        "title": "Retrieval-Augmented Generation for Large Language Models: A Survey",
        "authors": ["Yunfan Gao", "Yun Xiong", "Haofen Wang"],
        "abstract": "A comprehensive taxonomy of Naive, Advanced, and Modular RAG architectures.",
        "pages": 27,
        "chunks": 62,
        "sample_content": "Modular RAG integrates specialized search patterns including memory augmentation, iterative routing, and verification modules. Reciprocal Rank Fusion serves as a foundational rank combination method for heterogeneous indexers."
    },
    {
        "arxiv_id": "2305.14283",
        "title": "Active Retrieval Augmented Generation (FLARE)",
        "authors": ["Zhengbao Jiang", "Frank F. Xu", "Graham Neubig"],
        "abstract": "Forward-Looking Active Retrieval Augmented Generation (FLARE) dynamically determines when and what to retrieve during generation.",
        "pages": 13,
        "chunks": 24,
        "sample_content": "FLARE monitors the confidence of generation tokens. When probability drops below a margin, generation pauses and an active retrieval query is formulated using the anticipated sentence structure."
    },
    {
        "arxiv_id": "2402.03367",
        "title": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
        "authors": ["Akari Asai", "Zeqiu Wu", "Hannaneh Hajishirzi"],
        "abstract": "Self-RAG enables adaptive retrieval and generation critique using special reflection tokens.",
        "pages": 19,
        "chunks": 41,
        "sample_content": "Self-reflection tokens allow language models to decide whether external knowledge retrieval is necessary on a segment-by-segment basis, critiquing both context relevance and generation factual faithfulness."
    }
]

async def seed_initial_data():
    async with AsyncSessionLocal() as db:
        from sqlalchemy.future import select
        res = await db.execute(select(Corpus))
        existing = res.scalars().first()
        if existing:
            # Re-index existing chunks into memory
            all_chunks_res = await db.execute(select(Chunk).where(Chunk.corpus_id == existing.id))
            chunks = all_chunks_res.scalars().all()
            chunks_for_index = [
                {
                    "id": c.id,
                    "paper_id": c.paper_id,
                    "arxiv_id": c.arxiv_id,
                    "paper_title": "Research Paper",
                    "page_number": c.page_number,
                    "section_name": c.section_name,
                    "content": c.content,
                    "chunk_type": c.chunk_type,
                    "parent_chunk_id": c.parent_chunk_id,
                    "token_count": c.token_count
                }
                for c in chunks
            ]
            index_service.index_corpus(str(existing.id), chunks_for_index)
            return

        # Seed initial corpus
        corpus = Corpus(
            name="Retrieval Augmented Generation in Long-Context Reasoning",
            description="Comparative study of 5 RAG architectures across 30+ page research documents",
            query="Lost in the Middle transformer context degradation",
            status="ready",
            paper_count=len(SAMPLE_PAPERS),
            page_count=sum(p["pages"] for p in SAMPLE_PAPERS),
            chunk_count=sum(p["chunks"] for p in SAMPLE_PAPERS),
            categories=["cs.CL", "cs.AI", "cs.IR"]
        )
        db.add(corpus)
        await db.flush()

        all_chunks_for_index = []
        for p_idx, p_data in enumerate(SAMPLE_PAPERS):
            paper = Paper(
                corpus_id=corpus.id,
                arxiv_id=p_data["arxiv_id"],
                title=p_data["title"],
                authors=p_data["authors"],
                abstract=p_data["abstract"],
                categories=["cs.CL", "cs.AI"],
                published_date="2023-07-15",
                status="indexed",
                page_count=p_data["pages"],
                chunk_count=p_data["chunks"]
            )
            db.add(paper)
            await db.flush()

            # Create sample Parent and Child chunks
            parent_chunk = Chunk(
                corpus_id=corpus.id,
                paper_id=paper.id,
                arxiv_id=paper.arxiv_id,
                page_number=4,
                section_name="§3 Methodology & Analysis",
                chunk_type="parent",
                content=p_data["sample_content"] * 2,
                token_count=180
            )
            db.add(parent_chunk)
            await db.flush()

            child_chunk = Chunk(
                corpus_id=corpus.id,
                paper_id=paper.id,
                arxiv_id=paper.arxiv_id,
                page_number=4,
                section_name="§3.2 Positional Degradation",
                chunk_type="child",
                parent_chunk_id=parent_chunk.id,
                content=p_data["sample_content"],
                token_count=90
            )
            db.add(child_chunk)

            all_chunks_for_index.append({
                "id": child_chunk.id,
                "paper_id": paper.id,
                "arxiv_id": paper.arxiv_id,
                "paper_title": paper.title,
                "page_number": child_chunk.page_number,
                "section_name": child_chunk.section_name,
                "content": child_chunk.content,
                "chunk_type": "child",
                "parent_chunk_id": parent_chunk.id,
                "token_count": child_chunk.token_count
            })

        await db.commit()
        index_service.index_corpus(str(corpus.id), all_chunks_for_index)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(arxiv.router, prefix=settings.API_V1_STR)
app.include_router(corpora.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(rag.router, prefix=settings.API_V1_STR)
app.include_router(evaluation.router, prefix=settings.API_V1_STR)
app.include_router(insights.router, prefix=settings.API_V1_STR)
app.include_router(settings_router.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}


# OpenAI-compatible stub — silences IDE/tooling probes that hit /v1/models
@app.get("/v1/models")
async def list_models():
    """Minimal OpenAI-compatible model list so external tools don't 404-spam logs."""
    import os
    default_model = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4o")
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4o", "object": "model", "owned_by": "synthlabs"},
            {"id": default_model, "object": "model", "owned_by": "synthlabs"},
        ],
    }
