from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apps.api.core.database import get_db
from apps.api.core.config import settings
from apps.api.models.chat import Conversation, Message, RAGRun, Feedback
from apps.api.schemas.rag import ChatQueryRequest, AnswerResult, FeedbackRequest
from apps.api.rag import get_rag_pipeline
from apps.api.core.langsmith import langsmith_tracker

router = APIRouter(tags=["chat"])

@router.post("/corpora/{corpus_id}/chat", response_model=AnswerResult)
async def chat_with_corpus(corpus_id: str, payload: ChatQueryRequest, db: AsyncSession = Depends(get_db)):
    pipeline = get_rag_pipeline(payload.strategy)

    config = {
        "top_k": payload.top_k,
        "reranker": payload.reranker,
        "scope": payload.scope,
        "paper_id": payload.paper_id,
        "model": settings.DEFAULT_CHAT_MODEL
    }

    # Execute RAG pipeline
    result = await pipeline.run(payload.query, corpus_id, config)

    # Manage or create conversation
    conv_id = payload.conversation_id
    if not conv_id:
        conv = Conversation(corpus_id=corpus_id, title=payload.query[:60])
        db.add(conv)
        await db.flush()
        conv_id = conv.id

    # Persist User Query Message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=payload.query
    )
    db.add(user_msg)

    # Persist RAG Run Telemetry
    citations_data = [c.dict() for c in result.citations]
    rag_run = RAGRun(
        corpus_id=corpus_id,
        strategy=result.strategy,
        query=payload.query,
        model=result.model,
        latency_ms=result.latency_ms,
        retrieval_latency_ms=result.retrieval_latency_ms,
        generation_latency_ms=result.generation_latency_ms,
        token_usage=result.token_usage,
        citations=citations_data,
        intermediate_steps=result.intermediate_steps,
        trace_id=result.trace_id,
        config=config
    )
    db.add(rag_run)
    await db.flush()

    # Persist Assistant Response Message
    assistant_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=result.answer,
        run_id=rag_run.id
    )
    db.add(assistant_msg)
    await db.commit()

    return result

@router.post("/runs/{run_id}/feedback")
async def submit_feedback(run_id: str, payload: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RAGRun).where(RAGRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    fb = Feedback(
        run_id=run_id,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(fb)
    await db.commit()

    # Log to LangSmith if trace is present
    if run.trace_id:
        score = 1.0 if payload.rating in ("helpful", "correct") else 0.0
        langsmith_tracker.record_feedback(run.trace_id, key="user_rating", score=score, comment=payload.comment)

    return {"status": "success", "run_id": run_id, "rating": payload.rating}
