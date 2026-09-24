import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from apps.api.core.database import get_db
from apps.api.core.config import settings
from apps.api.core.langsmith import langsmith_tracker
from apps.api.models.evaluation import EvaluationDataset, EvaluationExample, EvaluationExperiment
from apps.api.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.get("/langsmith/stats")
async def get_langsmith_stats():
    return langsmith_tracker.get_stats()

@router.get("/datasets")
async def list_datasets(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(EvaluationDataset))
    datasets = res.scalars().all()
    if not datasets:
        # Seed default benchmark dataset
        default_ds = EvaluationDataset(
            name="ArXiv RAG Benchmark v1",
            description="Long-Context Positional Bias & Architecture Comparison Dataset",
            version="1.0.0",
            item_count=len(evaluation_service.DEFAULT_QUESTIONS)
        )
        db.add(default_ds)
        await db.flush()
        for q in evaluation_service.DEFAULT_QUESTIONS:
            ex = EvaluationExample(
                dataset_id=default_ds.id,
                question=q["question"],
                ground_truth=q.get("ground_truth"),
                difficulty=q.get("difficulty", "medium"),
                question_type=q.get("type", "factual")
            )
            db.add(ex)
        await db.commit()
        await db.refresh(default_ds)
        datasets = [default_ds]

    return datasets

@router.post("/experiments")
async def run_experiment(corpus_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # Ensure default dataset exists
    res = await db.execute(select(EvaluationDataset))
    dataset = res.scalars().first()
    if not dataset:
        dataset = EvaluationDataset(
            name="ArXiv RAG Benchmark v1",
            description="Long-Context Positional Bias & Architecture Comparison Dataset",
            version="1.0.0",
            item_count=len(evaluation_service.DEFAULT_QUESTIONS)
        )
        db.add(dataset)
        await db.flush()
        for q in evaluation_service.DEFAULT_QUESTIONS:
            ex = EvaluationExample(
                dataset_id=dataset.id,
                question=q["question"],
                ground_truth=q.get("ground_truth"),
                difficulty=q.get("difficulty", "medium"),
                question_type=q.get("type", "factual")
            )
            db.add(ex)
        await db.commit()
        await db.refresh(dataset)

    # Run benchmark evaluation
    exp: Any = EvaluationExperiment(
        dataset_id=dataset.id,
        corpus_id=corpus_id,
        name=f"Evaluation Run #{int(time.time()) % 10000}",
        status="running"
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)

    # Compute metrics across all 5 architectures
    results = await evaluation_service.run_benchmark(corpus_id)
    exp.results = results
    exp.status = "completed"
    exp.langsmith_project_url = f"https://smith.langchain.com/projects/{settings.LANGCHAIN_PROJECT}"
    await db.commit()
    await db.refresh(exp)

    return exp

@router.get("/latest")
async def get_latest_experiment(corpus_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(EvaluationExperiment)
        .where(EvaluationExperiment.corpus_id == corpus_id)
        .where(EvaluationExperiment.status == "completed")
        .order_by(EvaluationExperiment.created_at.desc())
    )
    exp = res.scalars().first()
    if not exp:
        return {"status": "none", "results": {}}
    return exp

@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(EvaluationExperiment).where(EvaluationExperiment.id == experiment_id))
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp
