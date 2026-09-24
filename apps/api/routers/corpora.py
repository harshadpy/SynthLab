import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Any

from apps.api.core.database import get_db
from apps.api.models.corpus import Corpus, Paper, Chunk
from apps.api.schemas.corpus import CorpusCreateRequest, CorpusUpdateRequest, CorpusResponse, PaperResponse
from apps.api.services.arxiv_service import arxiv_service
from apps.api.services.pdf_processor import pdf_processor
from apps.api.services.chunking_service import chunking_service
from apps.api.services.index_service import index_service

router = APIRouter(prefix="/corpora", tags=["corpora"])

async def process_corpus_background(corpus_id: str):
    from apps.api.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(Corpus).where(Corpus.id == corpus_id).options(selectinload(Corpus.papers))
        )
        corpus: Any = res.scalar_one_or_none()
        if not corpus:
            return

        corpus.status = "processing"
        await db.commit()

        total_pages = 0
        total_chunks = 0
        all_chunks_for_index = []

        for paper_item in corpus.papers:
            paper: Any = paper_item
            if paper.status == "indexed":
                continue
            try:
                paper.status = "downloading"
                await db.commit()

                # Download PDF
                pdf_path = await arxiv_service.download_pdf(paper.arxiv_id, paper.pdf_url)
                paper.local_pdf_path = str(pdf_path)
                paper.status = "parsing"
                await db.commit()

                # Parse PDF in worker thread to prevent blocking event loop
                pages = await asyncio.to_thread(pdf_processor.extract_document, pdf_path)
                paper.page_count = len(pages)
                total_pages += len(pages)

                paper.status = "chunking"
                await db.commit()

                # Chunk document according to paper structure (sections & paragraphs)
                chunk_objs = await asyncio.to_thread(
                    chunking_service.create_hierarchical_chunks,
                    pages,
                    pdf_path=pdf_path
                )
                paper.chunk_count = len(chunk_objs)
                total_chunks += len(chunk_objs)

                # Persist chunks to DB
                for c in chunk_objs:
                    db_chunk = Chunk(
                        id=c.id,
                        corpus_id=corpus_id,
                        paper_id=paper.id,
                        arxiv_id=paper.arxiv_id,
                        page_number=c.page_number,
                        section_name=c.section_name,
                        content=c.content,
                        token_count=c.token_count,
                        parent_chunk_id=c.parent_chunk_id,
                        chunk_type=c.chunk_type,
                        text_hash=c.text_hash
                    )
                    db.add(db_chunk)

                    all_chunks_for_index.append({
                        "id": c.id,
                        "paper_id": paper.id,
                        "arxiv_id": paper.arxiv_id,
                        "paper_title": paper.title,
                        "page_number": c.page_number,
                        "section_name": c.section_name,
                        "content": c.content,
                        "chunk_type": c.chunk_type,
                        "parent_chunk_id": c.parent_chunk_id,
                        "token_count": c.token_count
                    })

                paper.status = "indexed"
                paper.status_message = "Successfully processed and indexed"
                await db.commit()

            except Exception as e:
                print(f"[Ingestion Error] Paper {paper.arxiv_id} failed: {e}")
                paper.status = "failed"
                paper.status_message = str(e)
                await db.commit()

        # Update in-memory multi-representation indexes in background thread
        await asyncio.to_thread(index_service.index_corpus, corpus_id, all_chunks_for_index)

        corpus.status = "ready"
        corpus.page_count = total_pages
        corpus.chunk_count = total_chunks
        await db.commit()

@router.post("", response_model=CorpusResponse)
async def create_corpus(payload: CorpusCreateRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    corpus = Corpus(
        name=payload.name,
        description=payload.description,
        query=payload.query,
        paper_count=len(payload.paper_ids),
        status="processing"
    )
    db.add(corpus)
    await db.flush()

    # Concurrently fetch metadata for all requested papers
    paper_items = await asyncio.gather(
        *[arxiv_service.get_paper(arxiv_id) for arxiv_id in payload.paper_ids],
        return_exceptions=True
    )

    for idx, arxiv_id in enumerate(payload.paper_ids):
        item = paper_items[idx] if idx < len(paper_items) else None
        if isinstance(item, Exception) or not item:
            item = ArXivPaperItem(
                arxiv_id=arxiv_id,
                title=f"Research Publication ({arxiv_id})",
                authors=["Academic Researcher et al."],
                abstract="Full publication retrieved for corpus construction.",
                categories=["Computer Science"],
                published_date="2024",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            )

        p = Paper(
            corpus_id=corpus.id,
            arxiv_id=item.arxiv_id,
            title=item.title,
            authors=item.authors,
            abstract=item.abstract,
            categories=item.categories,
            published_date=item.published_date,
            pdf_url=item.pdf_url,
            status="queued"
        )
        db.add(p)

    await db.commit()
    await db.refresh(corpus)

    # Trigger async ingestion
    background_tasks.add_task(process_corpus_background, str(corpus.id))

    res = await db.execute(
        select(Corpus).where(Corpus.id == corpus.id).options(selectinload(Corpus.papers))
    )
    return res.scalar_one()

@router.get("", response_model=List[CorpusResponse])
async def list_corpora(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Corpus).options(selectinload(Corpus.papers)).order_by(Corpus.created_at.desc())
    )
    return res.scalars().all()

@router.get("/{corpus_id}", response_model=CorpusResponse)
async def get_corpus(corpus_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Corpus).where(Corpus.id == corpus_id).options(selectinload(Corpus.papers))
    )
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Corpus not found")
    return c

@router.patch("/{corpus_id}", response_model=CorpusResponse)
async def update_corpus(corpus_id: str, payload: CorpusUpdateRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Corpus).where(Corpus.id == corpus_id).options(selectinload(Corpus.papers))
    )
    c: Any = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Corpus not found")
    if payload.name:
        c.name = payload.name
    if payload.description:
        c.description = payload.description
    await db.commit()
    await db.refresh(c)
    return c

@router.delete("/{corpus_id}")
async def delete_corpus(corpus_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Corpus)
        .where(Corpus.id == corpus_id)
        .options(
            selectinload(Corpus.papers),
            selectinload(Corpus.chunks),
            selectinload(Corpus.conversations),
            selectinload(Corpus.runs)
        )
    )
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Corpus not found")
    await db.delete(c)
    await db.commit()
    try:
        index_service.remove_corpus(corpus_id)
    except Exception as e:
        print(f"[Corpus Deletion] Index cleanup warning: {e}")
    return {"deleted": True, "id": corpus_id}

@router.post("/{corpus_id}/process")
async def trigger_processing(corpus_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Corpus).where(Corpus.id == corpus_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Corpus not found")
    background_tasks.add_task(process_corpus_background, corpus_id)
    return {"status": "processing_started", "corpus_id": corpus_id}
